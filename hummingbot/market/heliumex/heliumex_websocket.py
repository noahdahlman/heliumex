#!/usr/bin/env python
import asyncio
import logging
import websockets
import time
import ujson
import uuid

from typing import Dict, Optional, AsyncIterable, Union, List
from websockets.exceptions import ConnectionClosed
from hummingbot.logger import HummingbotLogger

from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
import hummingbot.market.heliumex.heliumex_stomp as STOMP
import hummingbot.market.heliumex.heliumex_topics as TOPICS
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS

StompFrameOrDict = Union[STOMP.StompFrame, Dict]


class HeliumExWebsocket:

    _hx_ws_logger: Optional[HummingbotLogger] = None

    # TODO: add a cache to help disambiguate messages that come in for specific subscriptions, etc.
    # and to also handle when messages come in that subscribers may have missed

    _url = None

    _heliumex_auth: Optional[HeliumExAuth] = None

    _client: Optional[websockets.WebSocketClientProtocol]
    _ev_loop = asyncio.BaseEventLoop

    _events: Dict[str, bool]

    _last_recv_time: float

    _subscriptions: Dict[str, str]

    _use_stomp: bool

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._hx_ws_logger is None:
            cls._hx_ws_logger = logging.getLogger(__name__)
        return cls._hx_ws_logger

    def __init__(self, url: str = CONSTANTS.HELIUMEX_WS_URL, auth: HeliumExAuth = None, use_stomp: bool = True):
        """
        Some topics use the stomp protocol while others do not
        """
        self._url = url
        self._client = None
        self._ev_loop = asyncio.get_event_loop()
        self._events: Dict[str, bool] = {}
        self._heliumex_auth = auth
        self._subscriptions = {}
        self._last_recv_time = 0
        self._use_stomp = use_stomp

    def _get_event(self, name: str) -> bool:
        return self._events.get(name, False)

    def _set_event(self, name: str):
        self._events[name] = True

    # connect to exchange
    async def connect(self, auth: HeliumExAuth = None) -> bool:
        if auth is not None:
            self._heliumex_auth = auth

        try:

            self._client = await websockets.connect(self._url)
            if self._heliumex_auth is not None:
                auth_token = await self._heliumex_auth.get_auth_token()
                await self._client.send(STOMP.connect(auth_token))

                # wait for one message to come back.
                # Should be the CONNECTED response but might not be.
                # we dont care so long as the connection is open.
                await asyncio.wait_for(self._client.recv(), timeout=CONSTANTS.WS_PING_TIMEOUT)

            return True
        except Exception as e:
            self.logger().error(f"Websocket connect error: '{str(e)}'", exc_info=True)
            return False

    # disconnect from exchange
    async def disconnect(self) -> None:
        if self._client is None:
            return

        # todo check is open/ready

        try:
            await self._client.send(STOMP.disconnect())
        except Exception:
            pass

        await self._client.close()
        self._subscriptions.clear()

    async def subscribe(self, destination: str, subscription_id: Optional[str] = None) -> Optional[str]:
        if subscription_id is None:
            subscription_id = f"{destination}-{str(uuid.uuid1())[:8]}"

        try:
            if self._use_stomp:
                await self._client.send(STOMP.subscribe(
                    subscription_id=subscription_id,
                    destination=destination
                ))
            else:
                await self._client.send(TOPICS.subscribe(destination))

            self._subscriptions[subscription_id] = destination
            return subscription_id
        except Exception as e:
            self.logger().error(f"Websocket subscribe error: '{str(e)}'", exc_info=True)
            return None

    async def unsubscribe(self, subscription_id: str) -> bool:
        if subscription_id not in self._subscriptions:
            return True
        # TODO: send unsubscribe
        return True

    async def request(self, destination: str, correlation_id: Optional[str] = None, body: Optional[str] = None) -> AsyncIterable[STOMP.StompFrame]:
        """
        Request data and return a result.  Note only certain API's actually respond directly.
        most respond on the /responses topic
        """
        if not self._use_stomp:
            self.logger().error("Websocket request error: must use STOMP")
            yield None
            return

        if correlation_id is None:
            correlation_id = uuid.uuid4()

        try:
            message = STOMP.send(
                destination=destination,
                correlation_id=correlation_id,
                body=body
            )
            await self._client.send(message)
        except Exception as e:
            self.logger().error(f"Websocket request error: '{str(e)}'", exc_info=True)
            yield e
            return

        async for message in self._messages():
            print(f"message: {message}")
            if "correlation-id" in message.headers and message.headers["correlation-id"] == correlation_id:
                yield message

    async def send(self, destination: str, correlation_id: Optional[str] = None, headers: Dict[str, str] = {}, body: Optional[str] = None) -> Optional[str]:
        """
        Fire a request but do not wait for a result.
        Generally this method is paried with a coroutine awaiting the `on` generator
        that listens for events specific to this request's `correlation_id`
        """
        if not self._use_stomp:
            self.logger().error("Websocket request error: must use STOMP")
            return None
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        try:
            message = STOMP.send(
                destination=destination,
                correlation_id=correlation_id,
                headers=headers,
                body=body
            )
            await self._client.send(message)
        except Exception as e:
            self.logger().error(f"Websocket request error: '{str(e)}'", exc_info=True)
            raise

        return correlation_id

    async def on(self, event_names: List[str], subscription_ids: List[str], correlation_ids: Optional[List[str]] = None) -> AsyncIterable[StompFrameOrDict]:
        """
        listen to messages by event_name and optionally, the correlation_id.

        """
        for event_name in event_names:
            self._set_event(event_name)

        async for message in self._messages():
            if self._use_stomp:
                # TODO: maybe we only want the body back?
                # if this is a STOMP response MESSAGE that includes a `destination`
                # meant for this event and a `subscription` meant for this subscription_id
                if "MESSAGE" in message.cmd and "destination" in message.headers:
                    for event_name in event_names:
                        # only emit if a subscription id is also relevant for the event
                        if event_name in message.headers["destination"] and "subscription" in message.headers:
                            for subscription_id in subscription_ids:
                                if subscription_id in message.headers["subscription"]:
                                    if correlation_ids is None and "correlation-id" not in message.headers:
                                        yield message
                                    # if there is a `correlation-id`
                                    elif correlation_ids is not None and "correlation-id" in message.headers:
                                        for correlation_id in correlation_ids:
                                            if correlation_id in message.headers["correlation-id"]:
                                                yield message
            else:
                if "source" in message and event_name in message["source"]:
                    yield message

    async def _messages(self) -> AsyncIterable[StompFrameOrDict]:
        try:
            while True:
                try:
                    message: str = await asyncio.wait_for(self._client.recv(), timeout=CONSTANTS.WS_MESSAGE_TIMEOUT)
                    if (("heartbeat" not in message and
                         "systemStatus" not in message and
                         "subscriptionStatus" not in message)):
                        self._last_recv_time = time.time()
                        if self._use_stomp:
                            frame = STOMP.unpack_frame(message)
                            yield frame
                        else:
                            yield ujson.loads(message)
                except asyncio.TimeoutError:
                    try:
                        pong_waiter = await self._client.ping()
                        await asyncio.wait_for(pong_waiter, timeout=CONSTANTS.WS_PING_TIMEOUT)
                    except asyncio.TimeoutError:
                        raise
        except asyncio.TimeoutError:
            self.logger().warning("WebSocket ping timed out. Reconnecting...")
            return
        except ConnectionClosed:
            return
        finally:
            await self.disconnect()
