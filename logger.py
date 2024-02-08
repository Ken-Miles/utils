import logging

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

requests_handler = logging.FileHandler('requests.log','a')
requests_handler.setFormatter(formatter)
requests_logger = logging.getLogger('requests_commands')
requests_logger.setLevel(logging.INFO)
requests_logger.addHandler(requests_handler)
