This is just a utils library I have to share code with my discord bots. You are free to use it with an MIT license.


# Using the utils library in your project
Add it to your bot as a git submodule named `utils`, so your code can `import utils`.

```bash
# in your bot's repository
git submodule add https://github.com/Ken-Miles/utils utils
```

Your bot's repository records which utils commit it uses. That way every clone and every deploy runs the same utils
code until you choose to update it.

## Installing dependencies
Add this line to your bot's `requirements.txt`, so one command installs both your bot's and utils' dependencies:

```text
-r utils/requirements.txt
```

## Setting up a fresh clone of a bot

```bash
git clone --recurse-submodules <your-repository-url>
```
```bash
python -m venv .venv
```
```bash
.venv/bin/pip install -r requirements.txt
```

If you already cloned without `--recurse-submodules`, fetch utils at the commit your bot uses:
```bash
git submodule update --init --recursive
```

Optionally, make `git pull` also update the submodule to the commit your bot uses:
```bash
git config submodule.recurse true
```

## Updating utils in a bot
Move the submodule to the latest utils, then commit the new commit pointer in your bot's repository:
```bash
git submodule update --remote utils
```
```bash
git add utils && git commit -m "Update utils"
```

Don't use `--remote` in deploy scripts. It pulls the newest utils commit instead of the one your bot was tested with.

## Keeping pytest out of utils
utils has its own tests in `utils/tests`. If your bot uses pytest, running `pytest` from your bot's root finds and runs
them too. Pytest reads its settings from your bot's own config file, so the fix goes in your bot's `pyproject.toml`:

```toml
[tool.pytest.ini_options]
norecursedirs = ["utils", ".*", "build", "dist", "*.egg", "venv", "CVS", "_darcs", "node_modules", "{arch}"]
```

The list repeats pytest's default skip list, because setting this key replaces the defaults. Without `.*`, pytest also
searches hidden folders such as `.venv`.

`pytest utils/tests` still runs utils' tests when you name the path. Any folder named `utils` at any depth is skipped,
so if your bot has its own `utils/` package with tests, move those tests or narrow the pattern.

# Configuring utils for your bot
Never put files inside the `utils` folder. Anything you add there isn't tracked by your bot's repository or by this one.

Keep each kind of setting where it belongs:

| What | Where |
|---|---|
| Secrets (tokens, webhook URLs, API keys, passwords) | Environment variables, listed in your bot's `.env.example` |
| Your bot's own settings (support server, channel IDs, ...) | A `config.py` in your bot's repository |
| Logging setup | Your bot's `main.py` |
| Settings the utils library uses | `utils.configure(...)`, called once in `main.py` before loading cogs |

```python
import utils

import config  # your bot's own settings module

utils.configure(
    emojis=config.EMOJIS,  # merged into utils.emojidict
    guilds=config.GUILDS,  # used by is_support_server()
    trusted_users=config.TRUSTED_USERS,  # used by is_trusted() and Cooldown()
    use_defer_emoji=True,  # react with a loading emoji instead of typing on ctx.defer()
    footer_name='@you',  # "Made by ..." footer when no bot owner is found
)
```

Settings you leave out keep their defaults. The current values are on `utils.settings`.

## Migrating from custom_constants.py
`utils/src/custom_constants.py` still works, but it is deprecated and raises a `DeprecationWarning`. To move off it:

1. Move secrets into environment variables. Read them in your bot's `config.py`, for example with
   `environ.Env()` from django-environ.
2. Move the rest of your bot's settings into `config.py`. Then change `from utils import SENTRY_URL` to
   `from config import SENTRY_URL`.
3. Move the logging setup (handlers, formatters, `setLevel` calls) into `main.py`.
4. Pass `emojidict`, `GUILDS` and `TRUSTED_USERS` to `utils.configure(...)`.

   The old file only ever applied `emojidict`. Values it set for `GUILDS`, `TRUSTED_USERS` and `USE_DEFER_EMOJI` never
   reached the library's checks. Passing them to `configure()` does apply them, so check that they're the values you want.
5. Delete `utils/src/custom_constants.py` (and `utils/src/kens_utils/custom_constants.py` if you have one).

# Supported discord.py versions
utils needs discord.py 2.6 or newer, because it uses Components V2 when it's imported. It's tested on 2.6.0, the newest
2.6 and 2.7 releases, and master.

## Helpers that stand in for discord.py features
Some helpers provide a discord.py feature that your installed discord.py doesn't have yet. There are two kinds:

- **Backports** (`utils.compat`): features from a released discord.py, for bots on an older version.
- **Experimental features** (`utils.experimental`): features from discord.py pull requests that haven't been merged.
  Their docstrings start with an "Experimental" warning, and the pull request's API may still change before it's
  merged.

Every one of these helpers follows the same rules, so moving to discord.py's version later is easy:

1. **It mirrors a discord.py call.** `helper(obj, ...)` corresponds to `obj.method(...)`, with the same arguments,
   so replacing it is a mechanical edit. The tables below list each pair.
2. **It hands over to discord.py automatically.** When the installed discord.py has the feature, the helper calls
   discord.py's version instead of its own code. Your bot keeps working with no change.
3. **It tells you what to replace it with.** When it hands over, it raises a `DeprecationWarning` with the exact
   call to use, for example `Replace it with permissions.pin_messages`.
4. **You can check them all at once.** `utils.library_features()` lists every helper, whether it's experimental,
   whether the installed discord.py has it built in, and its replacement:

```python
for feature in utils.library_features():
    if feature.built_in:
        print(f'replace utils.{feature.helper}() with {feature.replacement}')
```

`DeprecationWarning`s are hidden by default outside tests. Run your bot with `python -W default::DeprecationWarning`
(or check `library_features()`) to see them.

### Backports for discord.py 2.6

| Helper | discord.py 2.7 equivalent |
|---|---|
| `partial_emoji_from_str(value, client=client)` | `discord.PartialEmoji.from_str(value, client=client)` |
| `message_call(message)` | `message.call` (raises `AttributeError` on 2.6 when there's no call) |
| `message_is_forwardable(message)` | `message.is_forwardable()` |
| `interaction_command_id(interaction)` | `interaction.command_id` |
| `interaction_custom_id(interaction)` | `interaction.custom_id` |
| `await role_member_counts(guild)` | `await guild.role_member_counts()` |
| `message_type_is_deletable(message.type)` | `message.type.is_deletable()` |
| `has_permission(perms, 'pin_messages')` | `perms.pin_messages` (also `bypass_slowmode`, `set_voice_channel_status`) |

`User.collectibles` and `Member.collectibles` can't be backported: discord.py 2.6 discards that data when it reads a
user.

### Experimental: open discord.py pull requests

| Helper | Becomes | Pull request |
|---|---|---|
| `await fetch_permissions_for(scope, target, implicit=True)` | `await scope.fetch_permissions_for(target)` (channels also take `implicit=`) | [#10545](https://github.com/Rapptz/discord.py/pull/10545): ask Discord for a member's or role's permissions |
| `has_attachment_flag(attachment.flags, 'contains_gore_media')` | `attachment.flags.contains_gore_media` | [#10546](https://github.com/Rapptz/discord.py/pull/10546): also `contains_self_harm_media` |
| `FFmpegOpusAudio.from_probe(source, method=probe_codec)` | `FFmpegOpusAudio.from_probe(source)` | [#10517](https://github.com/Rapptz/discord.py/pull/10517): discord.py raises every probed bitrate to at least 512 kbps instead of capping it there |
| `voice_file(fp, duration=12.5)` | `discord.File(fp, duration=12.5)` | [#10230](https://github.com/Rapptz/discord.py/pull/10230): send voice messages |
| `await send_voice_message(channel, file)` | `await channel.send(file=file)` | [#10230](https://github.com/Rapptz/discord.py/pull/10230) |

`probe_codec` also returns no bitrate for sources that don't report one, so `FFmpegOpusAudio` uses its 128 kbps
default. #10517 as written would encode those at 0 kbps.

Voice messages: `channel` can be a channel, a user, or a command context. Voice messages can't have text, embeds or
other files. The waveform (the bars Discord draws) is worked out from Ogg Opus audio, the format Discord's apps
record in, when libopus is loaded. Other formats get flat bars, or pass your own `waveform=`. On macOS with Homebrew,
discord.py doesn't find libopus by itself:

```python
discord.opus.load_opus('/opt/homebrew/lib/libopus.0.dylib')
```

#10230 as written fills in a random waveform when it can't read the audio, and its waveform code divides by zero on
very short or silent clips. These helpers use flat bars instead and handle both.

Below are just extras/misc installation options.

### Install extras (speedup, documentation, tests)

you may include any combination of the extras, below they are listed for your convenience
`docs`: documentation dependencies and files
`tests`: testing dependencies and files
`speed`: optional speedup dependencies (orjson, etc)

```bash
# from your project root
cd utils # cd into the utils directory

pip install .[docs,tests,speed]
```

## Running tests
The tests run on every supported Python version (3.10 to 3.15) and discord.py version (2.6.0, the newest 2.6 and 2.7
releases, and master). [nox](https://nox.thea.codes) sets up a separate environment for each combination. The versions
are listed in `noxfile.py`, and CI runs the same sessions on every push.

```bash
pip install nox
```
```bash
nox                # every combination (Pythons you don't have installed are skipped)
nox -p 3.12        # one Python, every discord.py version
nox -k "2.7.1"     # every Python, one discord.py version
nox -l             # list the sessions
```

Arguments after `--` go to pytest, for example `nox -p 3.12 -- -x -k layout`.

To run the tests once in your current environment instead:
```bash
pytest
```