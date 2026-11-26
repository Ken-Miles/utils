"""Runs the tests on every supported Python and discord.py version.

nox                     # everything (skips Pythons that aren't installed)
nox -p 3.12             # one Python, every discord.py version
nox -k "2.7.1"          # every Python, one discord.py version
nox -l                  # list all sessions
"""

import nox

nox.options.default_venv_backend = 'uv|virtualenv'  # uv is much faster when it's installed

PYTHONS = ['3.10', '3.11', '3.12', '3.13', '3.14', '3.15']

# The oldest supported release, the newest patch of each minor version, and master (what the bots run).
# The library needs discord.py 2.6+: it uses Components V2 classes at import time.
DISCORD_PY = {
    '2.6.0': 'discord.py==2.6.0',
    '2.6.4': 'discord.py==2.6.4',
    '2.7.1': 'discord.py==2.7.1',
    'master': 'discord.py @ git+https://github.com/Rapptz/discord.py',
}

TEST_DEPS = ['pytest', 'pytest-asyncio', 'pytest-mock', 'pytest-order']


@nox.session(python=PYTHONS)
@nox.parametrize('discord', list(DISCORD_PY), ids=list(DISCORD_PY))
def tests(session: nox.Session, discord: str) -> None:
    session.install('-r', 'requirements.txt', DISCORD_PY[discord], *TEST_DEPS)
    session.run('python', '-c', 'import discord; print("discord.py", discord.__version__)')
    session.run('pytest', '-q', *session.posargs)
