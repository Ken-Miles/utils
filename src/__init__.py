from .kens_utils import *  # Import all utilities

# check if custom_constants exists, if so import
try:
    from .custom_constants import *  # type: ignore

    emojidict = constants.emojidict
    emojidict.update(custom_constants.emojidict)
except (ImportError, NameError, ModuleNotFoundError):
    pass

if 'custom_constants' in globals():
    import warnings as _warnings

    _warnings.warn(
        'utils/src/custom_constants.py is deprecated. Keep secrets in environment variables, bot settings in '
        "your bot's own config module, and pass library settings to utils.configure(). See the utils README.",
        DeprecationWarning,
        stacklevel=2,
    )
