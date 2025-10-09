from .kens_utils import *  # Import all utilities

# check if custom_constants exists, if so import
try:
    from .custom_constants import * # type: ignore
    emojidict = constants.emojidict
except (ImportError, NameError, ModuleNotFoundError):
    pass
