from __future__ import annotations
from enum import Enum

from discord.ext.commands import Cog

from typing import Callable, Dict, Optional, Tuple, Union, Any, TYPE_CHECKING, Sequence, Union, Literal, ClassVar, TypeVar, Generic, overload
import discord
from discord import TextChannel, TextInput, Thread, Guild, User, Member, DMChannel, TextChannel, VoiceChannel, ForumChannel, CategoryChannel, StageChannel
from discord.abc import GuildChannel, PrivateChannel, Messageable
from discord.ext import commands
from discord.ext.commands import Bot, BucketType
from discord.app_commands import CommandTree, AppCommand, Command
import logging
import aiohttp
import datetime
import asyncio
from discord.utils import DISCORD_EPOCH
import yaml
from collections import defaultdict as emojidictionary
import re

if TYPE_CHECKING:
    from discord import Message, InteractionMessage, WebhookMessage

    Interaction = discord.Interaction[Any]
    #Context = commands.Context[Any]

TRUSTED_USERS = [
    #390583140311367682, # yannick6848 (jantjebloks)
    694535201925365841, # sccubmo
]

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
    'guest': '<:guest:1181644152388194314>',
    'td': '<:td:1181644208109539400>',
    'qd': '<:qd:1181644138047869038>',
    'ds': '<:ds:1181644142099566692>',
    'gd': '<:gd:1181644145555673188>',
    'sg': '<:sg:1181644149074706482>',
    'ld': '<:ld:1181644156137906286>',
    'sds': '<:sds:1181644172457955408>',
    'sgd': '<:sgd:1181644177671467090>',
    'ssg': '<:ssg:1181644204510810224>',
    'mos': '<:mos:1181644218825973810>',

    'at': '<:at:1181644321292816456>',

    'dm': '<:dm:1181644187028967466>',
    'pm': '<:pm:1181644192263438336>',
    'gm': '<:gm:1181644196118003803>',
    'sm': '<:sm:1181644200165527624>',
    'cm': '<:cm:1181644211943112745>',
    'em': '<:em:1181644339080855612>',
    'om': '<:om:1181644222227550208>',

    'pdv': '<:pdv:1181644215441178644>',
    'dv': '<:pdv:1181644215441178644>',
    'tld': '<:tld:1181644335272435823>',

    'cd': '<:cd:1181644332005064815>',
    'od': '<:the_od:1181644232981749860>',
    'id': '<:the_id:1181644225721401385>',
    'md': '<:the_md:1181644229571772476>',

    'the_cd': '<:the_cd:1181644332005064815>',
    'the_id': '<:the_id:1181644225721401385>',
    'the_od': '<:the_od:1181644232981749860>',
    'the_md': '<:the_md:1181644229571772476>',

    'scr': '<:scr:1181644279777603614>',

    'hbd': '<:hbd:1181644236710477986>',
    'hoo': '<:hoo:1181644240183378061>',


    'connect': '<:connect:1181644243996000299>',
    'express': '<:express:1181644249448595548>',
    'waterline': '<:waterline:1181644253546418188>',
    'airlink': '<:airlink:1181644257463910490>',

    'SCR': '<:SCR:1181644261188448337>',
    'SCR_Gradient': '<:SCR_Gradient:1181644264464191560>',
    'SCR_Pride': '<:SCR_Pride:1181644268557832334>',
    'SCR_White': '<:SCR_White:1181644272336896083>',
    'scr_logo': '<:scr_logo:1181644276040478822>',
    'admin': '<:admin:1181644283757985902>',
    'assistance': '<:assistance:1181644288208150629>',
    'bantech': '<:bantech:1181644292427628644>',
    'bts': '<:bts:1181644295837601854>',
    'charlie': '<:charlie:1181644299851542568>',
    'matty': '<:matty:1181644303353782445>',
    'tfs': '<:tfs:1181644307560677416>',
    'trainer': '<:trainer:1181644311213903882>',

    'discord': '<:discord:1181644315244642436>',
    'roblox': '<:roblox:1181644328444108873>',

    # global
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
    "x": '<a:X_:1046808381266067547>',
    'x2': "\U0000274c",
    True: '<a:check_:1046808377373769810>',
    'check': '<a:check_:1046808377373769810>',
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

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

requests_handler = logging.FileHandler('requests.log','a')
requests_handler.setFormatter(formatter)
requests_logger = logging.getLogger('requests_commands')
requests_logger.setLevel(logging.INFO)
requests_logger.addHandler(requests_handler)

with open('apikeys.yml','r') as f:
    config = dict(yaml.safe_load(f))
    BLOXLINK_API_KEY = config.get('bloxlink_api')
    ROVER_API_KEY = config.get('rover_api')

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

async def _request(_method: Union[str, RequestType], /,  url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a GET request on the given URL."""
    method: RequestType
    if isinstance(_method, str):
        method = RequestType(_method.upper())
    else:
        method = _method

    rover = kwargs.pop('rover',False)
    bloxlink = kwargs.pop('bloxlink',False)

    SESSIONS = [aiohttp.ClientSession() for _ in range(3)]

    if rover:
        kwargs['headers'] = {'Authorization': f'Bearer {ROVER_API_KEY}'}
    
    if bloxlink:
        kwargs['headers'] = {'Authorization': f"{BLOXLINK_API_KEY}"}
    
    tr = 0

    for tr, session in enumerate(SESSIONS,1):
        request = method.get_method_callable(session)

        try: response = await request(url, **kwargs)
        except aiohttp.ServerDisconnectedError:
            requests_logger.warning(f"Server disconnected on session {tr}.")
            #await asyncio.sleep(5)
            continue

        status = response.status
        status_ = HTTPCode(status)
        requests_logger.info(f"[{method}] {status} {status_.name} from {response.url} (Session {tr})")

        if status_.is_200:
            return response
        
        if status_.is_100:
            requests_logger.info(f"Got a 1__ Continue, Retrying request...")
            continue
        elif status_.is_300:
            requests_logger.info(f"Got a 3__ Redirect. Retrying request...")
            continue
        elif status_.is_400:
            if status == 429:
                retry_after = response.headers.get('Retry-After',None)
                if not retry_after:
                    retry_after = response.headers.get('X-Ratelimit-Remaining',None)
                
                if retry_after:
                    requests_logger.info(f"We are being rate limited. Retrying in {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    requests_logger.info(f"We are being rate limited but no Retry-After header was found. Retrying in 5 seconds.")
                    await asyncio.sleep(5)
                    continue
        elif status_.is_500:
            requests_logger.info(f"Got a 5__ Server Error. Retrying request...")
            continue
    
    raise Exception(f"Failed to get a 2__ Success response after {tr} tries.")

async def _get(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a GET request on the given URL."""
    return await _request(RequestType.GET, url, **kwargs)

async def _post(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a POST request on the given URL."""
    return await _request(RequestType.POST, url, **kwargs)

async def _patch(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a PATCH request on the given URL."""
    return await _request(RequestType.PATCH, url, **kwargs)

async def _put(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a PUT request on the given URL."""
    return await _request(RequestType.PUT, url, **kwargs)

async def _delete(url: str, **kwargs) -> aiohttp.ClientResponse:
    """Performs a DELETE request on the given URL."""
    return await _request(RequestType.DELETE, url, **kwargs)

class CogU(Cog):
    """A subclass of Cog that includes a `hidden` attribute.
    Intended for use in Help commands where entire cogs shouldn't be shown by default."""
    hidden: ClassVar[bool]

    def __init_subclass__(cls, *, hidden: bool=False):
        cls.hidden = hidden
    
    async def _get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a GET request on the given URL."""
        return await _get(url, **kwargs)
    
    async def _post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a POST request on the given URL."""
        return await _post(url, **kwargs)
    
    async def _patch(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a PATCH request on the given URL."""
        return await _patch(url, **kwargs)
    
    async def _put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a PUT request on the given URL."""
        return await _put(url, **kwargs)
    
    async def _delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a DELETE request on the given URL."""
        return await _delete(url, **kwargs)

class GoToPageModal(discord.ui.Modal):

    def __init__(self, paginatior: BaseButtonPaginator, author_id: Optional[int]=None, title: str='Go to Page', **kwargs):
        if not title and kwargs.get('title',None): title = kwargs.pop('title')
        super().__init__(title='Go to Page', **kwargs)
        
        self.paginatior = paginatior

        self.author_id = author_id

        self.page_num = discord.ui.TextInput(label='Page Number', placeholder='Enter a page number',
         min_length=len(str(0)), max_length=len(str(self.paginatior.max_pages)), required=True, 
         custom_id='page_num', row=0)

        self.add_item(self.page_num)
    
    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        if self.author_id and interaction.user.id != self.author_id:
            return await interaction.followup.send('This modal is not for you.', ephemeral=True)
        try: page_num = int(self.page_num.value)
        except ValueError: return await interaction.followup.send('Page number must be an integer.', ephemeral=True)

        min_pages, max_pages = 0, self.paginatior.max_pages

        if not min_pages <= page_num <= max_pages:
            return await interaction.followup.send(f'Page number must be between {min_pages} and {max_pages}.', ephemeral=True)

        await self.paginatior._go_to_page(interaction, page_num)

class BaseButtonPaginator(discord.ui.View):
    """Made by @soheab on Discord, taken from the Discord.py Discord Server"""

    message: Optional[Message] = None

    def __init__(
        self,
        pages: Sequence[Any],
        *,
        author_id: Optional[int] = None,
        timeout: Optional[float] = 180.0,
        delete_message_after: bool = False,
        per_page: int = 1,
    ):
        super().__init__(timeout=timeout)
        self.author_id: Optional[int] = author_id
        self.delete_message_after: bool = delete_message_after

        self.current_page: int = 0
        self.per_page: int = per_page
        self.pages: Any = pages
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1

        self.max_pages: int = total_pages

    def stop(self) -> None:
        self.message = None
        self.ctx = None
        self.interaction = None

        super().stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self.author_id:
            return True

        if self.author_id != interaction.user.id:
            await interaction.response.send_message(
                "This menu is not for you.", ephemeral=True
            )
            return False

        return True

    def get_page(self, page_number: int) -> Any:
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def format_page(self, page: Any) -> Any:
        if isinstance(page, discord.Embed):
            if page.footer.text and ' | page' in page.footer.text.lower():
                new_footer = page.footer.text[:page.footer.text.lower().find(' | page')]
                page.set_footer(text=new_footer.strip())
        return page

    async def get_page_kwargs(self, page: Any) -> Dict[str, Any]:
        formatted_page = await discord.utils.maybe_coroutine(self.format_page, page)

        kwargs = {"content": None, "embeds": [], "view": self}
        if isinstance(formatted_page, str):
            kwargs["content"] = str(formatted_page)
        elif isinstance(formatted_page, discord.Embed):
            kwargs["embeds"] = [formatted_page]
        elif isinstance(formatted_page, list):
            if not all(isinstance(embed, discord.Embed) for embed in formatted_page):
                raise TypeError("All elements in the list must be of type Embed")

            kwargs["embeds"] = formatted_page
        elif isinstance(formatted_page, dict):
            return formatted_page
        else:
            raise TypeError(
                "Page content must be one of str, discord.Embed, list[discord.Embed], or dict"
            )

        return kwargs

    def update_buttons(self) -> None:
        self.previous_page.disabled = self.max_pages < 2 or self.current_page <= 0
        self.next_page.disabled = (
            self.max_pages < 2 or self.current_page >= self.max_pages - 1
        )

    async def update_page(self, interaction: Interaction) -> None:
        if self.message is None:
            self.message = interaction.message

        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        await interaction.response.edit_message(**kwargs)

    async def _stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        if self.delete_message_after:
            if self.message is not None:
                await self.message.delete()
        else:
            await interaction.response.send_message("Stopped the paginator.")
            
        self.stop()
    
    async def _previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page -= 1
        await self.update_page(interaction)
    
    async def _next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page += 1
        await self.update_page(interaction)

    async def _go_to_page(self, interaction: Interaction, page_num: int) -> None:
        if page_num < 0 or page_num >= self.max_pages:
            raise ValueError(f"Page number must be between 0 and {self.max_pages - 1}")
        self.current_page = page_num
        await self.update_page(interaction)

    async def start(
        self, obj: Union[Interaction, Messageable]
    ) -> Optional[Union[Message, InteractionMessage, WebhookMessage]]:
        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        if self.max_pages < 2:
            self.stop()
            del kwargs["view"]

        if isinstance(obj, discord.Interaction):
            if obj.response.is_done():
                self.message = await obj.followup.send(**kwargs)
            else:
                await obj.response.send_message(**kwargs)
                self.message = await obj.original_response()

        elif isinstance(obj, Messageable):
            self.message = await obj.send(**kwargs)
        else:
            raise TypeError(
                f"Expected Interaction or Messageable, got {obj.__class__.__name__}"
            )

        return self.message

class ButtonPaginator(BaseButtonPaginator):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('back'))
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._previous_page(interaction, _)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.red, emoji=emojidict.get('stop'))
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._stop_paginator(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('forward'))
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        return await self._next_page(interaction, _)
    
    @discord.ui.button(label="Go To Page", style=discord.ButtonStyle.gray)
    async def go_to_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        modal = GoToPageModal(self, author_id=self.author_id)
        await interaction.response.send_modal(modal)

ThreeButtonPaginator = ButtonPaginator

class FiveButtonPaginator(BaseButtonPaginator):
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def update_buttons(self) -> None:
        self.first_page.disabled = self.current_page <= 0
        super().update_buttons()
        self.last_page.disabled = self.current_page >= self.max_pages - 1
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('prev'))
    async def first_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page = 1
        await self.update_page(interaction)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('back'))
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._previous_page(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.red, emoji=emojidict.get('stop'))
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._stop_paginator(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('forward'))
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        return await self._next_page(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('next'))
    async def last_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page = self.max_pages - 1
        await self.update_page(interaction)
    
    @discord.ui.button(label="Go To Page", style=discord.ButtonStyle.gray)
    async def go_to_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        modal = GoToPageModal(self, author_id=self.author_id)
        await interaction.response.send_modal(modal)

class MentionableTree(CommandTree):
    """
    This was written by @leocx1000 on Discord   
    Copied from https://gist.github.com/LeoCx1000/021dc52981299b95ea7790416e4f5ca4
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_commands: dict[Optional[discord.abc.Snowflake], List[AppCommand]] = {}

    async def sync(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().sync(guild=guild)
        self.application_commands[guild] = ret
        return ret

    async def fetch_commands(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().fetch_commands(guild=guild)
        self.application_commands[guild] = ret
        return ret

    def get_mention_for(
        self,
        command: Command,
        *,
        guild: Optional[discord.abc.Snowflake] = None,
    ) -> Optional[str]:
        """Retrieves the mention of an AppCommand given a specific Command and optionally, a guild.
        Note that for this to work, the :meth:`.sync` or :meth:`.fetch_commands` must be called.
        Parameters
        ----------
        command: :class:`app_commands.Command`
            The command which it's mention we will attempt to retrieve.
        guild: Optional[:class:`discord.abc.Snowflake`]
            The scope (guild) from which to retrieve the commands from.
            If None is given or not passed, the global scope will be used.
        """
        try:
            found_commands = self.application_commands[guild]
            root_parent = command.root_parent or command
            command_id_found = discord.utils.get(found_commands, name=root_parent.name)
            if command_id_found:
                return f"</{command.qualified_name}:{command_id_found}>"
            return None
        except KeyError:
            return None

LOADING_EMOJI = emojidict.get('thinking')

class ConfirmationView(discord.ui.View):
    """
    Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/context.py#L280
    Written by @danny on Discord
    """

    def __init__(self, *, timeout: float, author_id: int, delete_after: bool, text: Optional[str]=None) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message('This button is not for you.', ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()


class ContextU(commands.Context):
    """Context Subclass to add some extra functionality."""
    defer_reaction: Optional[discord.Reaction] = None

    async def defer(self, *args, **kwargs):
        if not self.interaction and self.message:
            if (self.guild and self.guild.me.guild_permissions.add_reactions) or self.guild is None:
                self.defer_reaction = await self.message.add_reaction(LOADING_EMOJI)
        await super().defer(*args, **kwargs)

    async def _remove_reaction_if_present(self):
        if not self.interaction and self.message:
            if self.guild and LOADING_EMOJI in [str(x.emoji) for x in self.message.reactions]: ##discord.utils.get(self.message.reactions, emoji____str__=LOADING_EMOJI)
                if self.guild.me.guild_permissions.manage_messages:
                    await self.message.clear_reaction(LOADING_EMOJI)
                    self.defer_reaction = None

            if self.defer_reaction:
                await self.message.remove_reaction(LOADING_EMOJI,self.me)
                self.defer_reaction = None

    async def send(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().send(*args, **kwargs)

    async def reply(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().reply(*args, **kwargs)
    
    async def prompt(
        self,
        message: str,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.

        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        author_id = author_id or self.author.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
        )
        view.message = await self.send(message, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value


class BotU(Bot):
    tree_cls: MentionableTree
    tree: MentionableTree

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        if not self.owner_ids:
            assert self.application is not None
            if self.application.team:
                self.owner_ids = [x.id for x in self.application.team.members]
            else:
                self.owner_ids = [self.application.owner.id]
    
    async def get_context(self, message: Message, *, cls: type[commands.Context] = ContextU) -> commands.Context:
        return await super().get_context(message, cls=cls)

    async def getorfetch_channel(self, channelid: int, guild: Optional[Guild]=None) -> Union[GuildChannel, Thread, PrivateChannel]:
        """Gets a channel from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails."""
        channel: Optional[Union[GuildChannel, Thread, PrivateChannel]] = None
        if guild is not None:
            channel = guild.get_channel_or_thread(channelid)
            if channel is None:
                channel = await guild.fetch_channel(channelid)
        else:
            channel = self.get_channel(channelid)
            if channel is None:
                channel = await self.fetch_channel(channelid)
        return channel

    async def getorfetch_thread(self, threadid: int, guild: Guild) -> Thread:
        """Gets or fetches a Thread (Forum or TextChannel thread) from the provided guild.
        If None or a non-Thread is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(threadid, guild)
        if isinstance(ch, Thread):
            return ch
        raise Exception(f"Channel {threadid} is not a Thread")

    async def getorfetch_textchannel(self, channelid: int, guild: Guild) -> TextChannel:
        """Gets or fetches a TextChannel from the provided guild.
        If None or a non-TextChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, TextChannel):
            return ch
        raise Exception(f"Channel {channelid} is not a TextChannel")

    async def getorfetch_voicechannel(self, channelid: int, guild: Guild) -> VoiceChannel:
        """Gets or fetches a VoiceChannel from the provided guild.
        If None or a non-VoiceChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, VoiceChannel):
            return ch
        raise Exception(f"Channel {channelid} is not a VoiceChannel")
    
    async def getorfetch_categorychannel(self, channelid: int, guild: Guild) -> CategoryChannel:
        """Gets or fetches a CategoryChannel from the provided guild.
        If None or a non-CategoryChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, CategoryChannel):
            return ch
        raise Exception(f"Channel {channelid} is not a CategoryChannel")

    
    getorfetch_category = getorfetch_categorychannel
    
    async def getorfetch_stagechannel(self, channelid: int, guild: Guild) -> StageChannel:
        """Gets or fetches a StageChannel from the provided guild.
        If None or a non-StageChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, StageChannel):
            return ch
        raise Exception(f"Channel {channelid} is not a StageChannel")
    
    getorfetch_stage = getorfetch_stagechannel
    
    async def getorfetch_forumchannel(self, channelid: int, guild: Guild) -> ForumChannel:
        """Gets or fetches a StageChannel from the provided guild.
        If None or a non-StageChannel is returned, raises A"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, ForumChannel):
            return ch
        raise Exception(f"Channel {channelid} is not a ForumChannel")
    
    getorfetch_forum = getorfetch_forumchannel

    async def getorfetch_user(self, userid: int, guild: Optional[Guild]) -> Union[User, Member]:
        """Gets a user from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails."""
        user: Union[User, Member]
        if guild is not None:
            user = await self.getorfetch_member(userid, guild)
        else:
            user = self.get_user(userid) # type: ignore | fuck you pyright
            if user is None:
                user = await self.fetch_user(userid)
        return user

    async def getorfetch_member(self, userid: int, guild: Guild) -> Member:
        """Gets a Member from the guild's cache, else fetches it. Will error if fetch fails."""
        member = guild.get_member(userid)
        if member is None:
            member = await guild.fetch_member(userid)
        return member

    async def getorfetch_guild(self, guildid: int) -> Guild:
        """Gets a Guild from the cache, else fetches it. Will error if fetch fails."""
        guild = self.get_guild(guildid)
        if guild is None:
            guild = await self.fetch_guild(guildid)
        return guild 
    
    async def getorfetch_dmchannel(self, user: Union[User,Member]) -> DMChannel:
        """Gets a DM channel from the cache, else fetches it. Will error if fetch fails."""
        if user.dm_channel is None:
            return await user.create_dm()
        return user.dm_channel
    
    getorfetch_dm = getorfetch_dmchannel

    @staticmethod
    def makeembed(title: Optional[str]=None,timestamp: Optional[datetime.datetime]=None,
        color: Optional[discord.Colour]=None,description: Optional[str]=None, author: Optional[str]=None, 
        author_url: Optional[str]=None, author_icon_url: Optional[str]=None, footer: Optional[str]=None, 
        footer_icon_url: Optional[str]=None, url: Optional[str]=None,image: Optional[str]=None,
        thumbnail: Optional[str]=None,) -> discord.Embed:#embedtype: str='rich'):
        embed = discord.Embed()
        if title is not None:        embed.title = title
        if timestamp is not None:    embed.timestamp = timestamp
        if color is not None:        embed.color = color
        if description is not None:  embed.description = description
        if url is not None:          embed.url = url
        if author is not None:       embed.set_author(name=author,url=author_url,icon_url=author_icon_url)
        if footer is not None:       embed.set_footer(text=footer,icon_url=footer_icon_url)
        if image is not None:        embed.set_image(url=image)
        if thumbnail is not None:    embed.set_thumbnail(url=thumbnail)
        return embed

    def instance_makeembed(self, *args, **kwargs):
        return BotU.makeembed(*args, **kwargs)
    
    @staticmethod
    def makeembed_bot(title: Optional[str]=None,timestamp: Optional[datetime.datetime]=None,
        color: Optional[discord.Colour]=discord.Colour.green(),description: Optional[str]=None, 
        author: Optional[str]=None, author_url: Optional[str]=None, author_icon_url: Optional[str]=None,
        footer: str='Made by @aidenpearce3066', footer_icon_url: Optional[str]=None, url: Optional[str]=None,
        image: Optional[str]=None,thumbnail: Optional[str]=None,) -> discord.Embed:#embedtype: str='rich'):
        if not timestamp: timestamp = datetime.datetime.now()
        return BotU.makeembed(title=title,timestamp=timestamp,color=color,description=description,author=author,author_url=author_url,author_icon_url=author_icon_url,footer=footer,footer_icon_url=footer_icon_url,url=url,image=image,thumbnail=thumbnail)

    def instance_makeembed_bot(self, *args, **kwargs):
        return BotU.makeembed_bot(*args, **kwargs)

    @staticmethod
    def parsetime(date: str, time: Optional[str]=None) -> Optional[datetime.datetime]:
        """Parses a date and time string into a datetime.datetime object"""
        try:
            if date is not None and time is not None:
                return datetime.datetime.strptime(f"{date} {time}", "%Y.%m.%d %H:%M:%S")
            elif date is not None:
                return datetime.datetime.strptime(f"{date}", "%d.%m.%Y")
            elif time is not None:
                return datetime.datetime.strptime(f"{time}", "%H:%M:%S")
            #else:
            #    return parser.(date)
        except:
            return None

    timestamptype = Literal["t","T","d","D","f","F","R"]

    @staticmethod
    def dctimestamp(dt: Union[datetime.datetime, int, float], format: timestamptype="f") -> str:
        """
        Timestamp Styles
        STYLE     | EXAMPLE OUTPUT	              | DESCRIPTION
        t	  | 16:20	                      | Short Time
        T	  | 16:20:30	                      | Long Time
        d	  | 20/04/2021	                      | Short Date
        D	  | 20 April 2021	              | Long Date
        f  	  | 20 April 2021 16:20	              | Short Date/Time
        F	  | Tuesday, 20 April 2021 16:20      | Long Date/Time
        R	  | 2 months ago	              | Relative Time
        """
        if isinstance(dt, datetime.datetime): dt = int(dt.timestamp())
        if isinstance(dt, (int, float)): dt = int(dt)
        return f"<t:{int(dt)}:{format[:1]}>" 

    @staticmethod
    def dchyperlink(url: str, texttoclick: str, hovertext: Optional[str]=None, suppress_embed: bool=False) -> str:
        '''Formats a Discord Hyperlink so that it can be clicked on.
        "[Text To Click](https://www.youtube.com/ \"Hovertext\")"'''
        texttoclick, hovertext = f"[{texttoclick}]", f" \"{hovertext}\"" if hovertext is not None else ""
        return f"{texttoclick}({'<' if suppress_embed else ''}{url}{'>' if suppress_embed else ''}{hovertext})"

def is_owner(user: Union[discord.User, discord.Member], bot: BotU):
    assert bot.owner_ids is not None
    return user.id in bot.owner_ids

def check_is_trusted(user: Union[discord.User, discord.Member], bot: BotU):
    return is_owner(user, bot) or user.id in TRUSTED_USERS

def Cooldown(rate: int, per: int, bucket: BucketType):
    def actually_cool(ctx: commands.Context):
        #if await ctx.bot.is_owner(ctx.author): # bot owner gets no cooldown
        if is_owner(ctx.author, ctx.bot):
            return None
        return commands.Cooldown(rate, per)

    return commands.dynamic_cooldown(actually_cool, bucket)

def is_trusted():
    def predicate(ctx: commands.Context):
        return check_is_trusted(ctx.author, ctx.bot)

    return commands.check(predicate)

def is_support_server():
    def predicate(ctx: commands.Context):
        return ctx.guild is not None and ctx.guild.id in GUILDS

    return commands.check(predicate)

CodeblockLanguage = Literal["1c","4d","abnf","accesslog","ada","arduino","ino","armasm","arm","avrasm","actionscript","as","alan","ansi","i","log","ln","angelscript","asc","apache","apacheconf","applescript","osascript","arcade","asciidoc","adoc","aspectj","autohotkey","autoit","awk","mawk","nawk","gawk","bash","sh","zsh","basic","bbcode","blade","bnf","brainfuck","bf","csharp","cs","c","h","cpp","hpp","cc","hh","c++","h++","cxx","hxx","cal","cos","cls","cmake","cmake.in","coq","csp","css","csv","capnproto","capnp","chaos","kaos","chapel","chpl","cisco","clojure","clj","coffeescript","coffee","cson","iced","cpc","crmsh","crm","pcmk","crystal","cr","cypher","d","dns","zone","bind","dos","bat","cmd","dart","delphi","dpr","dfm","pas","pascal","freepascal","lazarus","lpr","lfm","diff","patch","django","jinja","dockerfile","docker","dsconfig","dts","dust","dst","dylan","ebnf","elixir","ex","elm","erlang","erl","extempore","xtlang","xtm","fsharp","fs","fix","fortran","f90","f95","gcode","nc","gams","gms","gauss","gss","godot","gdscript","gherkin","gn","gni","go","golang","gf","golo","gololang","gradle","groovy","xml","html","xhtml","rss","atom","xjb","xsd","xsl","plist","svg","http","https","haml","handlebars","hbs","html.hbs","html.handlebars","haskell","hs","haxe","hx","hy","hylang","ini","toml","inform7","i7","irpf90","json","java","jsp","javascript","js","jsx","jolie","iol","ol","julia","julia-repl","kotlin","kt","tex","leaf","lean","lasso","ls","lassoscript","less","ldif","lisp","livecodeserver","livescript","lock","ls","lua","makefile","mk","mak","make","markdown","md","mkdown","mkd","mathematica","mma","wl","matlab","maxima","mel","mercury","mirc","mrc","mizar","mojolicious","monkey","moonscript","moon","n1ql","nsis","never","nginx","nginxconf","nim","nimrod","nix","ocl","ocaml","ml","objectivec","mm","objc","obj-c","obj-c++","objective-c++","glsl","openscad","scad","ruleslanguage","oxygene","pf","pf.conf","php","php3","php4","php5","php6","php7","parser3","perl","pl","pm","plaintext","txt","text","pony","pgsql","postgres","postgresql","powershell","ps","ps1","processing","prolog","properties","protobuf","puppet","pp","python","py","gyp","profile","python-repl","pycon","k","kdb","qml","r","cshtml","razor","razor-cshtml","reasonml","re","redbol","rebol","red","red-system","rib","rsl","graph","instances","robot","rf","rpm-specfile","rpm","spec","rpm-spec","specfile","ruby","rb","gemspec","podspec","thor","irb","rust","rs","SAS","sas","scss","sql","p21","step","stp","scala","scheme","scilab","sci","shexc","shell","console","smali","smalltalk","st","sml","ml","solidity","sol","stan","stanfuncs","stata","iecst","scl","structured-text","stylus","styl","subunit","supercollider","sc","svelte","swift","tcl","tk","terraform","tf","hcl","tap","thrift","tp","tsql","twig","craftcms","typescript","ts","tsx","unicorn-rails-log","vbnet","vb","vba","vbscript","vbs","vhdl","vala","verilog","v","vim","axapta","x++","x86asm","xl","tao","xquery","xpath","xq","yml","yaml","zephir","zep"]

# only way to get a list of all the codeblock langs and create a type for it 
# is to use this hacky method -_-
CODEBLOCK_LANGUAGES = list(CodeblockLanguage.__args__) # type: ignore

async def create_codeblock(content: str, lang: CodeblockLanguage='py') -> str:
    if lang not in CODEBLOCK_LANGUAGES: raise ValueError(f"Invalid Language: {lang}")
    fmt: str = "```"
    return f"{fmt}{lang}\n{content}{fmt}"

async def create_paginator(ctx: ContextU, pages: Sequence[Any], author_id: Optional[int]=None, timeout: Optional[float]=180.0, delete_message_after: bool=False, per_page: int=1) -> BaseButtonPaginator:
    paginator = ThreeButtonPaginator(pages, author_id=author_id, timeout=timeout, delete_message_after=delete_message_after, per_page=per_page)
    await paginator.start(ctx)
    return paginator

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


class Snowflake:
    __binary: str
    __epoch: int

    def __init__(self, snowflake: Union[str, int], *, discord_snowflake: bool=False, custom_epoch: int=0):
        if isinstance(snowflake, str): snowflake = int(snowflake.strip())
        if discord_snowflake: self.__epoch = DISCORD_EPOCH
        else: self.__epoch = custom_epoch

        self.__binary = bin(snowflake)[2:]

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(__class__.binary_to_decimal(self.__binary[:-22]) + self.__epoch / 1000) # divide by 1000 to get seconds (from milliseconds)
    
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

makeembed_bot = BotU.makeembed_bot
makeembed = BotU.makeembed
parsetime = BotU.parsetime
dctimestamp = BotU.dctimestamp
dchyperlink = BotU.dchyperlink

SHIFT_ENTHUSIASTS = 1059402677601185853
GUILDS = [SHIFT_ENTHUSIASTS]

APATB = 1029151630215618600
APATB2 = 1078716884758831114
APATB3 = 1087156493746458674
APATB4 = 1134933747800735859

TESTING_GUILDS = [
    APATB,
    APATB2,
    APATB3,
    APATB4,
]

MY_GUILDS = TESTING_GUILDS + GUILDS
