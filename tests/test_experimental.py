"""Experimental helpers in experimental.py. Each test forces the helper's own path, so it runs the same
on every discord.py version; the redirect to discord.py is covered in test_library_features.py."""

import base64
import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from ..src.kens_utils import experimental


def fake_scope(cls, response):
    scope = cls.__new__(cls)
    scope.id = 99
    scope._state = SimpleNamespace(http=SimpleNamespace(request=AsyncMock(return_value=response)))
    return scope


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'target, kind',
    [
        (discord.Object(id=5, type=discord.Member), 'member'),
        (discord.Object(id=5, type=discord.User), 'member'),
        (discord.Object(id=5, type=discord.Role), 'role'),
    ],
)
async def test_fetch_permissions_for(monkeypatch, target, kind):
    monkeypatch.setattr(experimental, '_HAS_FETCH_PERMISSIONS_FOR', False)

    guild = fake_scope(discord.Guild, {'permissions': '2048'})
    perms = await experimental.fetch_permissions_for(guild, target)
    route = guild._state.http.request.await_args.args[0]
    assert perms == discord.Permissions(2048) and perms.send_messages
    assert route.path == f'/guilds/{{guild_id}}/permissions/{kind}/{{target_id}}'
    assert route.url.endswith(f'/guilds/99/permissions/{kind}/5')

    channel = fake_scope(discord.TextChannel, {'permissions': '0'})
    assert await experimental.fetch_permissions_for(channel, target, implicit=False) == discord.Permissions.none()
    call = channel._state.http.request.await_args
    assert call.args[0].url.endswith(f'/channels/99/permissions/{kind}/5') and call.kwargs['params'] == {'implicit': 0}


@pytest.mark.asyncio
async def test_fetch_permissions_for_rejects_other_targets(monkeypatch):
    monkeypatch.setattr(experimental, '_HAS_FETCH_PERMISSIONS_FOR', False)
    with pytest.raises(TypeError):
        await experimental.fetch_permissions_for(fake_scope(discord.Guild, {}), discord.Object(id=1))


@pytest.mark.parametrize('name, bit', list(experimental._NEW_ATTACHMENT_FLAG_BITS.items()))
def test_has_attachment_flag_new_flags(name, bit):
    built_in = hasattr(discord.AttachmentFlags, name)
    with pytest.warns(DeprecationWarning) if built_in else contextlib.nullcontext():
        assert experimental.has_attachment_flag(discord.AttachmentFlags._from_value(1 << bit), name)
    with pytest.warns(DeprecationWarning) if built_in else contextlib.nullcontext():
        assert not experimental.has_attachment_flag(discord.AttachmentFlags._from_value(0), name)


def test_has_attachment_flag_existing_and_unknown():
    assert experimental.has_attachment_flag(discord.AttachmentFlags(clip=True), 'clip')
    with pytest.raises(AttributeError):
        experimental.has_attachment_flag(discord.AttachmentFlags._from_value(0), 'not_a_flag')


@pytest.mark.parametrize(
    'bit_rate, expected',
    [('128000', 128), ('96500', 96), ('900000', 512), ('512000', 512), (None, None), ('0', None)],
)
def test_probe_codec_ffprobe(monkeypatch, bit_rate, expected):
    monkeypatch.setattr(experimental, '_HAS_PROBE_FIX', False)
    stream = {'codec_name': 'opus', **({'bit_rate': bit_rate} if bit_rate else {})}
    calls = []
    monkeypatch.setattr(
        experimental.subprocess,
        'check_output',
        lambda args, timeout: calls.append(args) or json.dumps({'streams': [stream]}).encode(),
    )
    assert experimental.probe_codec('song.webm') == ('opus', expected)
    assert calls[0][0] == 'ffprobe' and calls[0][-1] == 'song.webm'


@pytest.mark.parametrize('output, expected', [('96 kb/s', ('opus', 96)), ('1411 kb/s', ('opus', 512)), ('', ('opus', None))])
def test_probe_codec_falls_back_to_ffmpeg(monkeypatch, output, expected):
    monkeypatch.setattr(experimental, '_HAS_PROBE_FIX', False)

    def no_ffprobe(*args, **kwargs):
        raise FileNotFoundError('ffprobe')

    class FakeProc:
        def __init__(self, args, **kwargs):
            assert args[0] == 'ffmpeg'

        def communicate(self, timeout):
            return f'Stream #0:0: Audio: opus, 48000 Hz, stereo, fltp, {output}'.encode(), None

    monkeypatch.setattr(experimental.subprocess, 'check_output', no_ffprobe)
    monkeypatch.setattr(experimental.subprocess, 'Popen', FakeProc)
    assert experimental.probe_codec('song.webm') == expected


def test_probe_fix_detection_matches_installed_discord_py():
    import inspect

    source = inspect.getsource(discord.FFmpegOpusAudio._probe_codec_native)
    assert experimental._HAS_PROBE_FIX is ('min(round(bitrate / 1000), 512)' in source)


# voice messages (PR #10230)

VOICE_OGG = Path(__file__).parent / 'fixtures' / 'voice.ogg'  # 1 s loud, 1 s quiet, 1 s silent


def load_opus() -> bool:
    if discord.opus.is_loaded():
        return True
    for path in ('/opt/homebrew/lib/libopus.0.dylib', '/usr/local/lib/libopus.0.dylib'):
        if Path(path).exists():
            discord.opus.load_opus(path)
            return True
    return discord.opus._load_default()


@pytest.fixture
def no_built_in_voice(monkeypatch):
    monkeypatch.setattr(experimental, '_HAS_VOICE_FILES', False)


def test_generate_waveform_follows_the_audio():
    if not load_opus():
        pytest.skip('libopus is not installed')
    with open(VOICE_OGG, 'rb') as fp:
        waveform = experimental.generate_waveform(fp, duration=3.0)
    assert len(waveform) == 30 and all(0 <= v <= 255 for v in waveform)
    loud, quiet, silent = waveform[1:9], waveform[11:19], waveform[21:29]
    assert min(loud) > 200 and max(quiet) < 60 and max(silent) < 5


def test_generate_waveform_rejects_non_opus():
    if not load_opus():
        pytest.skip('libopus is not installed')
    with pytest.raises(Exception):
        experimental.generate_waveform(io.BytesIO(b'ID3 not an ogg file'), duration=1.0)


def test_voice_file_payload(no_built_in_voice):
    file = experimental.voice_file(io.BytesIO(b'audio'), duration=2.5, waveform=[0, 128, 255], filename='voice.mp3')
    assert isinstance(file, experimental.VoiceFile) and file.voice
    payload = file.to_dict(0)
    assert payload['duration_secs'] == 2.5
    assert base64.b64decode(payload['waveform']) == bytes([0, 128, 255])
    assert payload['filename'] == 'voice.mp3'


def test_voice_file_waveform_is_flat_for_other_formats(no_built_in_voice):
    file = experimental.voice_file(io.BytesIO(b'not opus'), duration=1.2, filename='voice.mp3')
    assert file.waveform == [128] * 12  # pyright: ignore[reportAttributeAccessIssue]
    assert file.fp.read() == b'not opus'  # rewound after the failed generation


def test_voice_file_generates_waveform_for_opus(no_built_in_voice):
    if not load_opus():
        pytest.skip('libopus is not installed')
    file = experimental.voice_file(str(VOICE_OGG), duration=3.0)
    assert len(file.waveform) == 30 and max(file.waveform) == 255  # pyright: ignore[reportAttributeAccessIssue]
    assert file.fp.read(4) == b'OggS'


@pytest.mark.parametrize('waveform', [[256], [-1], [0] * 257])
def test_voice_file_validates_waveform(no_built_in_voice, waveform):
    with pytest.raises(ValueError):
        experimental.voice_file(io.BytesIO(b'a'), duration=1, waveform=waveform)


def sent_payload(params) -> dict:
    form = {part['name']: part['value'] for part in params.multipart}
    return json.loads(form['payload_json'])


@pytest.mark.asyncio
async def test_send_voice_message_sets_the_voice_flag(no_built_in_voice):
    sent = {}

    async def send_message(channel_id, *, params):
        sent['channel_id'], sent['payload'] = channel_id, sent_payload(params)
        return {'id': '1'}

    state = SimpleNamespace(
        allowed_mentions=None,
        http=SimpleNamespace(send_message=send_message),
        create_message=lambda channel, data: ('message', data['id']),
    )
    channel = SimpleNamespace(_state=state, _get_channel=AsyncMock(return_value=SimpleNamespace(id=42)))
    file = experimental.voice_file(io.BytesIO(b'audio'), duration=1.0, waveform=[1, 2], filename='v.ogg')

    assert await experimental.send_voice_message(channel, file, silent=True) == ('message', '1')  # pyright: ignore[reportArgumentType]
    flags = discord.MessageFlags._from_value(sent['payload']['flags'])
    assert sent['channel_id'] == 42 and flags.voice and flags.suppress_notifications
    assert sent['payload']['attachments'][0]['duration_secs'] == 1.0
    assert 'content' not in sent['payload'] and 'embeds' not in sent['payload']


@pytest.mark.asyncio
async def test_send_voice_message_rejects_plain_files(no_built_in_voice):
    with pytest.raises(TypeError):
        await experimental.send_voice_message(SimpleNamespace(), discord.File(io.BytesIO(b'a')))  # pyright: ignore[reportArgumentType]
