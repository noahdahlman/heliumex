#!/usr/bin/env python

import aiohttp
import logging
import time
from typing import Dict, Optional, Any

from hummingbot.logger import HummingbotLogger
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS


class HeliumExAuth:

    _heliumex_auth_logger: Optional[HummingbotLogger] = None

    __last_update_time: int

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._heliumex_auth_logger is None:
            cls._heliumex_auth_logger = logging.getLogger(__name__)
        return cls._heliumex_auth_logger

    def __init__(self, api_key: str, secret_key: str, one_time_password: Optional[str] = None):
        self._api_key: Optional[str] = api_key
        self._secret_key: Optional[str] = secret_key
        self._one_time_password: Optional[str] = one_time_password
        self._auth_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

        self._shared_client: aiohttp.ClientSession = None
        self.__last_update_time = 0

    async def get_auth_token(self, force_refresh = False) -> Optional[str]:
        """
        Get an auth token from the API
        """
        # refresh the token before it expires (e.g. after 45 mins)
        token_still_valid = time.time_ns() - self.__last_update_time <= 2700000000000
        if not force_refresh and self._auth_token is not None and token_still_valid:
            return self._auth_token
        elif not force_refresh and self._auth_token is not None and not token_still_valid:
            if await self.refresh():
                return self._auth_token

        url: str = CONSTANTS.HELIUMEX_AUTH_URL + CONSTANTS.HELIUMEX_API_ENDPOINT_EXCHANGE_TOKEN
        body = self._get_authorization_request_body()

        client: aiohttp.ClientSession = await self._http_client()

        response_coro = client.request(
            method="POST",
            url=url,
            headers={
                "Content-Type": "application/json"
            },
            json=body,
            timeout=100
        )

        async with response_coro as response:
            if response.status != 200:
                raise IOError(f"Error fetching HeliumEx exchange token. HTTP status is {response.status}.")

            try:
                response_json: Dict[str, Any] = await response.json()
            except Exception:
                raise IOError(f"Error parsing data from {url}.")

            try:
                result = response_json["result"]
                if "success" not in result:
                    message = response_json["message"]
                    self.logger().error(f"Error authorizing: {message}")
                    raise IOError({"error": response_json})
            except IOError:
                raise
            except Exception as e:
                self.logger().error(f"Error authorizing error: {e}")
                self._auth_token = None
                return None

            self._auth_token = response_json["exchange_access_token"]
            self._refresh_token = response_json["exchange_refresh_token"]

            self.__last_update_time = time.time_ns()

            # TODO given refresh token, clear out the sensitive values
            # from memory when we no longer need them
            return self._auth_token

    async def refresh(self) -> bool:

        url: str = CONSTANTS.HELIUMEX_AUTH_URL + CONSTANTS.HELIUMEX_API_ENDPOINT_REFRESH_TOKEN
        body = {
            "exchange": CONSTANTS.HELIUMEX_EXCHANGE_ID,
            "refreshToken": self._refresh_token
        }

        client: aiohttp.ClientSession = await self._http_client()

        response_coro = client.request(
            method="POST",
            url=url,
            headers={
                "Content-Type": "application/json"
            },
            json=body,
            timeout=100
        )

        async with response_coro as response:
            if response.status != 200:
                raise IOError(f"Error fetching HeliumEx exchange token. HTTP status is {response.status}.")

            try:
                response_json: Dict[str, Any] = await response.json()
            except Exception:
                raise IOError(f"Error parsing data from {url}.")

            try:
                result = response_json["result"]
                if "success" not in result:
                    message = response_json["message"]
                    self.logger().error(f"Error authorizing: {message}")
                    raise IOError({"error": response_json})
            except IOError:
                raise
            except Exception as e:
                self.logger().error(f"Error authorizing error: {e}")
                self._auth_token = None
                return False

            self._auth_token = response_json["exchange_access_token"]
            self._refresh_token = response_json["exchange_refresh_token"]

            self.__last_update_time = time.time_ns()

            return True

    def get_auth_api_header(self) -> Dict[str, str]:
        return self._generate_auth_api_dict(self._auth_token)

    def _get_authorization_request_body(self) -> Dict[str, any]:
        """
        Get the request body used for executing authorization
        """
        if self._one_time_password is None:
            return {
                "username": self._api_key,
                "password": self._secret_key,
                "exchange": CONSTANTS.HELIUMEX_EXCHANGE_ID
            }
        else:
            return {
                "username": self._api_key,
                "password": self._secret_key,
                "exchange": CONSTANTS.HELIUMEX_EXCHANGE_ID,
                "twoFACode": self._one_time_password
            }

    def _generate_auth_api_dict(self, exchange_access_token: str) -> Dict[str, str]:
        """
        Generates authentication signature and return it in a dictionary along with other inputs
        :return: a dictionary of request info including the request signature
        """

        timestamp = str(time.time_ns())

        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {exchange_access_token}",
            "x-deltix-nonce": timestamp
        }

    async def _http_client(self) -> aiohttp.ClientSession:
        if self._shared_client is None or self._shared_client.closed:
            self._shared_client = aiohttp.ClientSession()
        return self._shared_client

    async def stop(self):
        if self._shared_client is not None and not self._shared_client.closed:
            await self._shared_client.close()
