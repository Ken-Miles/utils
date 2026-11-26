"""Experimental: features from discord.py pull requests that haven't been merged yet.

Their final API may change before they're merged. Each helper matches the call the pull request
adds (see :mod:`._library_features`): once discord.py includes it, the helper calls discord.py's
version and raises a DeprecationWarning naming that call, so you can replace the helper.
"""

from __future__ import annotations

import base64
import inspect
import json
import re
import secrets
import subprocess
from typing import TYPE_CHECKING, Any

import discord
from discord.http import Route

from ._library_features import redirects_to

if TYPE_CHECKING:
    import io
    import os

    from discord.abc import GuildChannel

# fmt: off
__all__ = (
    'fetch_permissions_for',
    'has_attachment_flag',
    'probe_codec',
    'VoiceFile',
    'voice_file',
    'generate_waveform',
    'send_voice_message',
)
# fmt: on

_HAS_FETCH_PERMISSIONS_FOR = hasattr(discord.Guild, 'fetch_permissions_for')  # PR #10545

# attachment flags from PR #10546, and their bit positions
_NEW_ATTACHMENT_FLAG_BITS = {
    'contains_gore_media': 6,
    'contains_self_harm_media': 7,
}


def _probe_is_fixed() -> bool:
    """Whether discord.py's codec probe caps the bitrate at 512 kbps instead of raising it to 512 (PR #10517)."""
    try:
        return 'max(' not in inspect.getsource(discord.FFmpegOpusAudio._probe_codec_native)
    except (OSError, TypeError):  # source unavailable, e.g. a compiled install
        return False


_HAS_PROBE_FIX = _probe_is_fixed()


def _target_kind(target: object) -> str:
    if isinstance(target, (discord.Member, discord.User)) or (
        isinstance(target, discord.Object) and target.type in (discord.Member, discord.User)
    ):
        return 'member'
    if isinstance(target, discord.Role) or (isinstance(target, discord.Object) and target.type is discord.Role):
        return 'role'
    raise TypeError(f'target must be a Member, User, Role, or Object with one of those types, not {target!r}')


def _upstream_fetch_permissions_for(scope, target, *, implicit: bool = True):
    _target_kind(target)  # same TypeError as the helper, before any request
    if isinstance(scope, discord.Guild):
        return scope.fetch_permissions_for(target)  # pyright: ignore[reportAttributeAccessIssue]
    return scope.fetch_permissions_for(target, implicit=implicit)  # pyright: ignore[reportAttributeAccessIssue]


# the availability checks are lambdas so they read the flags at call time (tests can change them)


@redirects_to(
    'await scope.fetch_permissions_for(target)  (channels: also implicit=implicit)',
    available=lambda *a, **k: _HAS_FETCH_PERMISSIONS_FOR,
    upstream=_upstream_fetch_permissions_for,
    pr=10545,
)
async def fetch_permissions_for(
    scope: discord.Guild | GuildChannel,
    target: discord.Member | discord.User | discord.Role | discord.Object,
    *,
    implicit: bool = True,
) -> discord.Permissions:
    """|coro|

    Asks Discord for a member's or role's permissions in a guild or channel.

    For a member, this is their permissions from all of their roles, plus the channel's overwrites when
    ``scope`` is a channel. For a role, it's the role's own permissions, plus the channel's overwrites.

    Parameters
    ----------
    scope: Union[:class:`discord.Guild`, :class:`discord.abc.GuildChannel`]
        Where to check the permissions.
    target: Union[:class:`discord.Member`, :class:`discord.User`, :class:`discord.Role`, :class:`discord.Object`]
        Who to check. A :class:`discord.Object` must have a ``type`` of Member, User or Role.
    implicit: :class:`bool`
        Channels only: whether to include implicit permissions, such as losing ``send_messages`` when
        ``view_channel`` is denied. Defaults to ``True``.

    Raises
    ------
    TypeError
        ``target`` isn't a member, user or role.
    discord.HTTPException
        Fetching the permissions failed.
    """
    kind = _target_kind(target)
    if isinstance(scope, discord.Guild):
        route = Route(
            'GET', f'/guilds/{{guild_id}}/permissions/{kind}/{{target_id}}', guild_id=scope.id, target_id=target.id
        )
        data = await scope._state.http.request(route)
    else:
        route = Route(
            'GET', f'/channels/{{channel_id}}/permissions/{kind}/{{target_id}}', channel_id=scope.id, target_id=target.id
        )
        data = await scope._state.http.request(route, params={'implicit': int(implicit)})
    return discord.Permissions(int(data['permissions']))


@redirects_to(
    'flags.{name}',
    available=lambda flags, name: name in _NEW_ATTACHMENT_FLAG_BITS and hasattr(discord.AttachmentFlags, name),
    upstream=lambda flags, name: getattr(flags, name),
    pr=10546,
    available_cases=tuple((None, name) for name in _NEW_ATTACHMENT_FLAG_BITS),
)
def has_attachment_flag(flags: discord.AttachmentFlags, name: str) -> bool:
    """Reads one attachment flag by name, including ``contains_gore_media`` and ``contains_self_harm_media``,
    which discord.py doesn't know yet.

    Use it as ``has_attachment_flag(attachment.flags, 'contains_gore_media')``.
    Raises AttributeError for names that aren't attachment flags.
    """
    if name in _NEW_ATTACHMENT_FLAG_BITS:
        return bool(flags.value >> _NEW_ATTACHMENT_FLAG_BITS[name] & 1)
    if name not in discord.AttachmentFlags.VALID_FLAGS:
        raise AttributeError(f'{name!r} is not an attachment flag.')
    return getattr(flags, name)


def _bitrate_kbps(kbps: float) -> int | None:
    # Cap at Discord's 512 kbps maximum. Streams that don't report a bitrate come out as 0: return
    # None so FFmpegOpusAudio uses its 128 kbps default instead of encoding at 0 kbps.
    return min(round(kbps), 512) or None


def _upstream_probe_codec(source: str, executable: str = 'ffmpeg') -> tuple[str | None, int | None]:
    # discord.py's own probes, with the same "no bitrate -> None" safety as the helper
    try:
        codec, bitrate = discord.FFmpegOpusAudio._probe_codec_native(source, executable)
    except Exception:
        codec, bitrate = discord.FFmpegOpusAudio._probe_codec_fallback(source, executable)
    return codec, bitrate or None


@redirects_to(
    'discord.FFmpegOpusAudio.from_probe(source)  (drop method=probe_codec)',
    available=lambda *a, **k: _HAS_PROBE_FIX,
    upstream=_upstream_probe_codec,
    pr=10517,
)
def probe_codec(source: str, executable: str = 'ffmpeg') -> tuple[str | None, int | None]:
    """Finds an audio source's codec and bitrate, for ``discord.FFmpegOpusAudio.from_probe(source, method=probe_codec)``.

    discord.py's own probe raises every bitrate to at least 512 kbps, when 512 is meant to be the maximum.
    This caps it instead, and returns None for sources that don't report a bitrate, so FFmpegOpusAudio
    uses its default rather than 0 kbps.

    Uses ffprobe, and falls back to reading ffmpeg's output like discord.py does.
    """
    try:
        exe = executable[:2] + 'probe' if executable in ('ffmpeg', 'avconv') else executable
        args = [exe, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a:0', source]
        output = subprocess.check_output(args, timeout=20)
        if not output:
            return None, None
        stream = json.loads(output)['streams'][0]
        return stream.get('codec_name'), _bitrate_kbps(int(stream.get('bit_rate', 0)) / 1000)
    except Exception:  # same as discord.py: any ffprobe failure falls back to parsing ffmpeg's output
        pass

    proc = subprocess.Popen(
        [executable, '-hide_banner', '-i', source],
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    out, _ = proc.communicate(timeout=20)
    output = out.decode('utf8')
    codec_match = re.search(r'Stream #0.*?Audio: (\w+)', output)
    bitrate_match = re.search(r'(\d+) [kK]b/s', output)
    return (
        codec_match.group(1) if codec_match else None,
        _bitrate_kbps(int(bitrate_match.group(1))) if bitrate_match else None,
    )


# Voice messages: discord.py pull request #10230 adds duration= and waveform= to discord.File,
# and sets the voice message flag when such a file is sent.

_HAS_VOICE_FILES = 'duration' in inspect.signature(discord.File.__init__).parameters

_MAX_WAVEFORM_POINTS = 256


def generate_waveform(fp: io.BufferedIOBase, duration: float) -> list[int]:
    """Builds a voice message waveform (0-255 values, one per 100 ms, at most 256) from Ogg Opus audio.

    This is the format Discord's clients record voice messages in. Needs libopus loaded (see
    :func:`discord.opus.load_opus`). Reads ``fp`` from its current position; seek it back afterwards.

    Raises
    ------
    discord.opus.OpusNotLoaded
        libopus isn't loaded.
    discord.oggparse.OggError, ValueError
        The audio isn't Ogg Opus.
    """
    from array import array

    from discord.oggparse import OggStream
    from discord.opus import Decoder

    decoder = Decoder()
    pcm = array('h')  # 16-bit signed samples, both channels interleaved
    for packet in OggStream(fp).iter_packets():  # pyright: ignore[reportArgumentType]
        if packet[:8] in (b'OpusHead', b'OpusTags'):
            continue
        pcm.frombytes(decoder.decode(packet, fec=False))
    if not pcm:
        raise ValueError('No Opus audio found.')

    points = max(1, min(_MAX_WAVEFORM_POINTS, round(duration * 10)))
    size = len(pcm) / points
    # the loudest sample in each slice; max/min run in C, so this is fast even for long messages
    peaks = [
        max(max(chunk), -min(chunk)) if (chunk := pcm[int(i * size) : int((i + 1) * size)]) else 0 for i in range(points)
    ]
    loudest = max(peaks)
    if not loudest:
        return [0] * points
    return [min(255, peak * 255 // loudest) for peak in peaks]


class VoiceFile(discord.File):
    """A :class:`discord.File` that Discord shows as a voice message. Make one with :func:`voice_file`."""

    __slots__ = ('duration', 'waveform', 'voice')

    def __init__(
        self,
        fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase,
        *,
        duration: float,
        waveform: list[int] | None = None,
        filename: str | None = None,
        spoiler: bool = False,
        description: str | None = None,
    ) -> None:
        super().__init__(fp, filename=filename, spoiler=spoiler, description=description)
        if waveform is not None:
            if len(waveform) > _MAX_WAVEFORM_POINTS:
                raise ValueError(f'Waveforms have at most {_MAX_WAVEFORM_POINTS} values.')
            if any(not 0 <= value <= 255 for value in waveform):
                raise ValueError('Waveform values must be between 0 and 255.')
        else:
            try:
                waveform = generate_waveform(self.fp, duration)
            except Exception:
                # Not Ogg Opus, or libopus isn't loaded: show flat bars rather than a made-up shape.
                waveform = [128] * max(1, min(_MAX_WAVEFORM_POINTS, round(duration * 10)))
            self.reset()
        self.duration = duration
        self.waveform = waveform
        self.voice = True

    def to_dict(self, index: int) -> dict[str, Any]:
        payload = super().to_dict(index)
        payload['duration_secs'] = self.duration
        payload['waveform'] = base64.b64encode(bytes(self.waveform)).decode('ascii')
        return payload


@redirects_to(
    'discord.File(fp, duration=duration, waveform=waveform, filename=filename, spoiler=spoiler, description=description)',
    available=lambda *a, **k: _HAS_VOICE_FILES,
    upstream=lambda fp, **kwargs: discord.File(fp, **kwargs),
    pr=10230,
)
def voice_file(
    fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase,
    *,
    duration: float,
    waveform: list[int] | None = None,
    filename: str | None = None,
    spoiler: bool = False,
    description: str | None = None,
) -> discord.File:
    """Makes a file that Discord shows as a voice message. Send it with :func:`send_voice_message`.

    Parameters
    ----------
    fp
        The audio, like :class:`discord.File`. Discord accepts ``ogg``, ``mp3``, ``wav``, ``aac``, ``flac`` and more.
    duration: :class:`float`
        The length of the audio in seconds. Discord shows it on the message, and doesn't check it.
    waveform: Optional[List[:class:`int`]]
        Up to 256 values from 0 to 255, drawn as the message's bars. If left out, it's worked out from the audio
        for Ogg Opus files when libopus is loaded, and is flat for anything else.

    Working out the waveform decodes the whole file, which takes about a third of a second for a minute of
    audio. For long clips, call this with ``await asyncio.to_thread(voice_file, ...)`` so the bot isn't blocked.
    """
    return VoiceFile(fp, duration=duration, waveform=waveform, filename=filename, spoiler=spoiler, description=description)


def _upstream_send_voice_message(channel, file, *, reference=None, silent=False, delete_after=None):
    return channel.send(file=file, reference=reference, silent=silent, delete_after=delete_after)


@redirects_to(
    'await channel.send(file=file)',
    available=lambda *a, **k: _HAS_VOICE_FILES,
    upstream=_upstream_send_voice_message,
    pr=10230,
)
async def send_voice_message(
    channel: discord.abc.Messageable,
    file: discord.File,
    *,
    reference: discord.Message | discord.MessageReference | discord.PartialMessage | None = None,
    silent: bool = False,
    delete_after: float | None = None,
) -> discord.Message:
    """|coro|

    Sends a file from :func:`voice_file` as a voice message. Works with channels, users, and command contexts.

    Voice messages can't have text, embeds or other files, so this only takes the file.

    Parameters
    ----------
    reference
        A message to reply to, like :meth:`discord.abc.Messageable.send`.
    silent: :class:`bool`
        Don't send a push or desktop notification.
    delete_after: Optional[:class:`float`]
        Delete the message after this many seconds.

    Raises
    ------
    TypeError
        ``file`` isn't from :func:`voice_file`.
    discord.HTTPException
        Sending failed, for example because the channel doesn't allow voice messages.
    """
    from discord.http import handle_message_parameters
    from discord.utils import MISSING

    if not getattr(file, 'voice', False):
        raise TypeError('file must come from utils.voice_file().')

    channel_obj = await channel._get_channel()
    state = channel._state
    flags = discord.MessageFlags._from_value(0)
    flags.voice = True
    flags.suppress_notifications = silent
    reference_dict = reference.to_message_reference_dict() if reference is not None else MISSING

    with handle_message_parameters(
        file=file,
        flags=flags,
        nonce=secrets.randbits(64),
        message_reference=reference_dict,
        previous_allowed_mentions=state.allowed_mentions,
    ) as params:
        data = await state.http.send_message(channel_obj.id, params=params)
    message = state.create_message(channel=channel_obj, data=data)
    if delete_after is not None:
        await message.delete(delay=delete_after)
    return message
