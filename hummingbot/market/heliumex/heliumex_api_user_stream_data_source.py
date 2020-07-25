#!/usr/bin/env python
import asyncio
import logging
import time
from typing import (
    Optional,
    List,
)
import ujson

from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource

from hummingbot.logger import HummingbotLogger

from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_order_book import HeliumExOrderBook
import hummingbot.market.heliumex.heliumex_stomp as STOMP
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_websocket import HeliumExWebsocket


class HeliumExAPIUserStreamDataSource(UserStreamTrackerDataSource):
    _heliumex_usds_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._heliumex_usds_logger is None:
            cls._heliumex_usds_logger = logging.getLogger(__name__)
        return cls._heliumex_usds_logger

    def __init__(self, heliumex_auth: HeliumExAuth, trading_pairs: Optional[List[str]] = []):
        self._heliumex_auth: HeliumExAuth = heliumex_auth
        self._trading_pairs = trading_pairs
        self._last_recv_time: float = 0
        self._websocket: HeliumExWebsocket = HeliumExWebsocket(auth=self._heliumex_auth)
        super().__init__()

    @property
    def order_book_class(self):
        """
        *required
        Get relevant order book class to access class specific methods
        :returns: OrderBook class
        """
        return HeliumExOrderBook

    @property
    def last_recv_time(self) -> float:
        return self._last_recv_time

    async def listen_for_user_stream(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """
        *required
        Subscribe to user stream via web socket, and keep the connection open for incoming messages
        :param ev_loop: ev_loop to execute this function in
        :param output: an async queue where the incoming messages are stored
        """
        while True:
            try:
                await self._websocket.connect(self._heliumex_auth)
                # TODO? response_subscription = await self._websocket.subscribe(CONSTANTS.socket_send_responses())
                # register for order updates
                orders_update_subscription = await self._websocket.subscribe(CONSTANTS.orders_WS())
                # register for balance updates
                balance_update_subscription = await self._websocket.subscribe(CONSTANTS.balances_WS())

                async for message in self._websocket.on(
                    [CONSTANTS.HELIUMEX_WS_ENDPOINT_ORDERS_LISTEN, CONSTANTS.HELIUMEX_WS_ENDPOINT_USER_BALANCES_LISTEN],
                    [orders_update_subscription, balance_update_subscription]
                ):
                    self._last_recv_time = time.time()
                    stomp_msg: STOMP.StompFrame = message
                    parsed_message = ujson.loads(stomp_msg.body)
                    if CONSTANTS.HELIUMEX_WS_ENDPOINT_ORDERS_LISTEN in stomp_msg.headers["destination"]:
                        parsed_message["event_type"] = CONSTANTS.HeliumExEventTypes.ActiveOrdersUpdate
                        output.put_nowait(parsed_message)
                    elif CONSTANTS.HELIUMEX_WS_ENDPOINT_USER_BALANCES_LISTEN in stomp_msg.headers["destination"]:
                        for item in parsed_message:
                            item["event_type"] = CONSTANTS.HeliumExEventTypes.BalanceUpdate
                            output.put_nowait(item)
                    else:  # TODO: log an error?
                        pass

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Unexpected error with HeliumEx WebSocket connection. {str(e)}\n\n Retrying after 30 seconds...", exc_info=True)
                await asyncio.sleep(30.0)
