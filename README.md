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
To run the tests for this utils library, you can use pytest. Make sure you have installed the testing dependencies first (see above).

```bash
# from your project root
cd utils # cd into the utils directory
pytest -vs tests
```