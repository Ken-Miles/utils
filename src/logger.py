import logging

from .constants import formatter

requests_handler = logging.FileHandler("requests.log", "a")
requests_handler.setFormatter(formatter)
requests_logger = logging.getLogger("requests_commands")
requests_logger.setLevel(logging.INFO)
requests_logger.addHandler(requests_handler)
