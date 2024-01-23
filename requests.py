from __future__ import annotations

from typing import Union

import aiohttp
import asyncio

from logger import requests_logger
from constants import RequestType, HTTPCode, BLOXLINK_API_KEY, ROVER_API_KEY

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

    async def close_sessions():
        for session in SESSIONS:
            await session.close()

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
            await close_sessions()
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
        else:
            requests_logger.warning(f"Got an unknown status code {status}. Retrying request...")
            continue
    
    await close_sessions()
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
