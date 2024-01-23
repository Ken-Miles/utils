from __future__ import annotations

from typing import Callable, Union
from enum import Enum
from collections import defaultdict as emojidictionary
import logging
import re
import datetime

import aiohttp  
import yaml

# K = TypeVar('K')
# V = TypeVar('V')

# class emojidictionary(Generic[K, V], dict):
#     def __init__(self, *args: Any, **kwargs: Any) -> None:
#         if args and isinstance(args[0], dict):
#             super().__init__(args[0].items()) 
#         else:
#             super().__init__(*args, **kwargs)

#     # Overloading get method for different types of keys
#     @overload
#     def get(self, key: K) -> V | None: ...
    
#     @overload
#     def get(self, key: K, default: V) -> V: ...

#     def get(self, key: K, default: Optional[V] = None) -> V | None:
#         if r := super().get(key):
#             return r
#         return super().get(default, None)

def constant_factory(value):
    return lambda: value

emojidict: emojidictionary = emojidictionary(constant_factory("\U00002753"), {

    "x": '<a:X_:1046808381266067547>',
    "check": '<a:check_:1046808377373769810>',
    'L': "\U0001f1f1",
    'l': "\U0001f1f1",
    "salute": "\U0001fae1",

    'clipboard': "\U0001f4cb",

    "calendar": "\U0001f4c6",
    "notepad": "\U0001f5d2",
    "alarmclock": "\U000023f0",
    "timer": "\U000023f2",

    'bot': "\U0001f916",

    'caution': "\U000026a0\U0000fe0f",

    'person': "\U0001f464",

    '1st': "\U0001f947",
    '2nd': "\U0001f948",
    '3rd': "\U0001f949",
    '1': "\U00000031\U0000fe0f\U000020e3",
    '2': "\U00000032\U0000fe0f\U000020e3",
    '3': "\U00000033\U0000fe0f\U000020e3",
    '4': "\U00000034\U0000fe0f\U000020e3",
    '5': "\U00000035\U0000fe0f\U000020e3",
    '6': "\U00000036\U0000fe0f\U000020e3",
    '7': "\U00000037\U0000fe0f\U000020e3",
    '8': "\U00000038\U0000fe0f\U000020e3",
    '9': "\U00000039\U0000fe0f\U000020e3",
    '10': "\U0001f51f",

    'game': '\U0001f3ae',

    'lock': "\U0001f512",

    'star': '\U00002b50',

    'thumbsup_': '<:upvote:1176051534950322246>',
    'thumbsdown_': '<:downvote:1176051583381942342>',

    'star_': '<:star:1176051612234555432>',

    'computer': '\U0001f5a5',

    'notepad': '\U0001f4dd',

    'i': '\U00002139\U0000fe0f',

    #'left': '\U00002b05\U0000fe0f',
    #'right': '\U000027a1\U0000fe0f',

    'vote': '\U0001f5f3',

    # global
    'x2': "\U0000274c",
    True: '<a:check_:1046808377373769810>',
    "check2": '\U00002705',
    'L': "\U0001f1f1",
    'l': "\U0001f1f1",
    "salute": "\U0001fae1",
    'no': "\U0001f6ab",
    'numbers': '\U0001f522',
    "calendar": "\U0001f4c6",
    "notepad": "\U0001f5d2",
    "alarmclock": "\U000023f0",
    "timer": "\U000023f2",
    "maybe": "\U0001f937",
    False: "<a:X_:1046808381266067547>",
    "pong": "\U0001f3d3",
    'pencilpaper': '\U0001f4dd',
    'red': "\U0001f534",
    "yellow": "\U0001f7e1",
    "green": "\U0001f7e2",
    "blue": "\U0001f535",
    'purple': "\U0001f7e3",
    'gray': "",

    'thinking': '<a:loading:1181644325445193778>',
    'loading': "<a:loading:1191255723850596422>",
    'postgres': "<:postgresql:1191255667575623780>",

    'mail': '\U0001f4ea',

    "headphones": "\U0001f3a7",

    "hamburger": '\U0001f354',
    "building": '\U0001f3db',
    "click": '\U0001f5b1',
    "newspaper": '\U0001f5de',
    "pick": '\U000026cf',
    "restart": '\U0001f504',

    "skull": "\U0001f480",
    "laughing": "\U0001f923",
    "notfunny": "\U0001f610",

    #1: "\U00000031"+"\U0000fe0f"+"\U000020e3",
    2: "\U00000032"+"\U0000fe0f"+"\U000020e3",
    3: "\U00000033"+"\U0000fe0f"+"\U000020e3",
    4: "\U00000034"+"\U0000fe0f"+"\U000020e3",
    5: "\U00000035"+"\U0000fe0f"+"\U000020e3",

    "stop": "\U000023f9",
    "playpause": "\U000023ef",
    "eject": "\U000023cf",
    "play": "\U000025b6\U0000fe0f",
    "pause": "\U000023f8",
    "record": "\U000023fa",
    "next": "\U000023ed\U0000fe0f",
    "prev": "\U000023ee\U0000fe0f",
    "fastforward": "\U000023e9\U0000fe0f",
    "rewind": "\U000023ea",
    "repeat": "\U0001f501",
    "back": "\U000025c0\U0000fe0f",
    "forward": "\U000025b6\U0000fe0f", # same as play
    "shuffle": "\U0001f500",

    "filmframes": "\U0001f39e",

    'badge': "<:badge:1188704607761858560>",
    
    'default': "\U00002753",
})

try:
    from custom_constants import emoijdict
    for k,v in emoijdict.items():
        emojidict[k] = v
except: pass

LOADING_EMOJI = emojidict.get('thinking')


http_codes = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",

    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    218: "This is fine", # apache servers... https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    226: "IM Used",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy", # depricated
    306: "Unused", # depricated
    307: "Temporary Redirect",
    308: "Permanent Redirect",

    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot", # this is real btw
    420: "Enhance Your Calm", # unofficial twitter response code??? https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    421: "Misdirected Request",
    422: "Unprocessable Content",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    430: "Shopify Security Rejection", # unofficial shopify servers... https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    431: "Request Header Fields Too Large",
    444: "No Response", # unofficial nginx  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    449: "Retry With", # unofficial
    450: "Blocked by Windows Parental Controls", # bro what https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Unofficial_codes
    451: "Unavailable For Legal Reasons",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
    520: "Web Server Returned an Unknown Error", # unoffical code cloudflare
    521: "Web Server is Down", # unoffical code cloudflare
    522: "Connection Timed Out", # unoffical code cloudflare
    523: "Origin is Unreachable", # unoffical code cloudflare
    524: "A Timeout Occurred", # unoffical code cloudflare
    525: "SSL Handshake Failed", # unoffical code cloudflare
    526: "Invalid SSL Certificate", # unoffical code cloudflare
    527: "Railgun Error", # unoffical code cloudflare
    530: "Site is Frozen", # unoffical code cloudflare

    598: "Network Read Timeout Error", # unoffical code
    599: "Network Connect Timeout Error", # unoffical code
}


class HTTPCode:
    status: int
    def __init__(self, status: int):
        self.status = status
        assert status in http_codes.keys(), f"Invalid HTTP status code {status}"
    
    @property
    def name(self) -> str:
        return http_codes.get(self.status, "Unknown")

    @property
    def is_100(self) -> bool:
        return 100 <= self.status < 200
    
    @property
    def is_200(self) -> bool:
        return 200 <= self.status < 300
    
    @property
    def is_300(self) -> bool:
        return 300 <= self.status < 400
    
    @property
    def is_400(self) -> bool:
        return 400 <= self.status < 500
    
    @property
    def is_500(self) -> bool:
        return 500 <= self.status < 600

    def __str__(self) -> str:
        return f"{self.status} {self.name}"
    
    def __int__(self) -> int:
        return self.status

class RequestType(Enum):
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    PUT = 'PUT'
    DELETE = 'DELETE'

    def get_method_callable(self, session: aiohttp.ClientSession) -> Callable:
        if self is RequestType.GET:
            return session.get
        elif self is RequestType.POST:
            return session.post
        elif self is RequestType.PATCH:
            return session.patch
        elif self is RequestType.PUT:
            return session.put
        elif self is RequestType.DELETE:
            return session.delete
        raise ValueError(f"Invalid request type {self}")

    def __str__(self):
        return self.value.upper()

CURRENCY_SYMBOL = "$"
CURRENCY_NAME = "Money"

# regexes

RE_EMOJI = re.compile(r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>")
RE_URL = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
RE_INVITE = re.compile(r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?")
RE_GIFT = re.compile(r"(https?://)?discord((app)?.com/gifts|.gifts)/[a-zA-Z0-9-]+/?")
RE_HEX = re.compile(r"^(#|0x)[A-Fa-f0-9]{6}$")
RE_SNOWFLAKE = re.compile(r"^[0-9]{15,19}$")

DISCORD_EPOCH = 1420070400000

TRUSTED_USERS = [

]

GUILDS = [

]

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

with open('apikeys.yml','r') as f:
    config = dict(yaml.safe_load(f))
    BLOXLINK_API_KEY = config.get('bloxlink_api')
    ROVER_API_KEY = config.get('rover_api')



class Snowflake:
    __binary: str
    __epoch: int

    @staticmethod
    def from_binary(binary: str):
        return Snowflake(__class__.binary_to_decimal(binary))

    def __init__(self, snowflake: Union[str, int], *, discord_snowflake: bool=False, custom_epoch: int=0):
        if isinstance(snowflake, str): snowflake = int(snowflake.strip())
        if discord_snowflake: self.__epoch = DISCORD_EPOCH
        else: self.__epoch = custom_epoch

        self.__binary = bin(snowflake)[2:]
    
    def __int__(self) -> int:
        return int(self.__binary)

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(__class__.binary_to_decimal(self.__binary) + self.__epoch / 1000) # divide by 1000 to get seconds (from milliseconds)
    
    @property
    def worker_id(self) -> int:
        return int(self.__binary[-22:-17], 2)
    
    @property
    def process_id(self) -> int:
        return int(self.__binary[-17:-12], 2)
    
    @property
    def increment(self) -> int:
        return int(self.__binary[-12:])
    
    @property
    def binary(self) -> str:
        return self.__binary
    
    @property
    def epoch(self) -> int:
        return self.__epoch
    
    @staticmethod
    def binary_to_decimal(n: str):
        return int(n,2)

def parse_discord_snowflake(snowflake: Union[str, int]) -> Snowflake:
    """Returns a tuple of (datetime, worker_id, process_id, increment).
    See [this](https://i.imgur.com/UxWvdYD.png) image for more information."""
    return Snowflake(snowflake=snowflake, discord_snowflake=True)

def snowflake_timestamp(snowflake: Union[int, str]) -> datetime.datetime:
    return parse_discord_snowflake(snowflake).datetime
