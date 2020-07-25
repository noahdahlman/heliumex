#!/usr/bin/env python

import asyncio
import aiohttp
import logging
import pandas as pd
from typing import (
    Any,
    Dict,
    List,
    Optional,
)
import time
import uuid

from hummingbot.logger import HummingbotLogger
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.order_book_tracker_entry import OrderBookTrackerEntry

from hummingbot.core.utils import async_ttl_cache


from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
import hummingbot.market.heliumex.heliumex_payloads as PAYLOADS
from hummingbot.market.heliumex.heliumex_websocket import HeliumExWebsocket
from hummingbot.market.heliumex.heliumex_order_book import HeliumExOrderBook


class HeliumExMarketData:
    pair: str
    baseAsset: str
    quoteAsset: str
    volume: str
    price: str


class HeliumExAPIOrderBookDataSource(OrderBookTrackerDataSource):

    _hxaobds_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._hxaobds_logger is None:
            cls._hxaobds_logger = logging.getLogger(__name__)
        return cls._hxaobds_logger

    def __init__(self, heliumex_auth: HeliumExAuth, trading_pairs: Optional[List[str]] = None):
        super().__init__()
        self._heliumex_auth: HeliumExAuth = heliumex_auth
        self._trading_pairs: Optional[List[str]] = trading_pairs
        self._websocket: HeliumExWebsocket = HeliumExWebsocket(CONSTANTS.HELIUMEX_WS_DATA_SERVICE_URL, use_stomp=False)
        self._snapshot_msg: Dict[str, any] = {}

    @classmethod
    @async_ttl_cache(ttl=60 * 30, maxsize=1)
    async def get_active_exchange_markets(cls, auth: HeliumExAuth) -> pd.DataFrame:
        """
        *required
        Returned data frame should have trading_pair as index and include usd volume, baseAsset and quoteAsset
        """
        async with aiohttp.ClientSession() as client:

            await auth.get_auth_token()
            auth_header = auth.get_auth_api_header()

            # Get the securities
            # TODO: this call includes other data like the trading commissions,
            # and order quantities, need to update that here?
            securities_response = await client.get(CONSTANTS.available_securities_API(), headers=auth_header)
            securities_response: aiohttp.ClientResponse = securities_response

            if securities_response.status != 200:
                raise IOError(f"Error fetching HeliumEx trading pairs. "
                              f"HTTP status is {securities_response.status} message: {securities_response.text}")

            securities_data = await securities_response.json()

            # Get the market data for all securities
            statistics_response = await client.get(CONSTANTS.all_securities_statistics_API(), headers=auth_header)
            statistics_response: aiohttp.ClientResponse = statistics_response

            if statistics_response.status != 200:
                raise IOError(f"Error fetching HeliumEx markets information. "
                              f"HTTP status is {statistics_response.status}.")

            statistics_data = await statistics_response.json()

            securities_data: Dict[str, Any] = {
                details["id"]: details for details in securities_data
            }

            statistics_data: Dict[str, Any] = {
                details["security_id"]: details for details in statistics_data
            }

            # build the data frame
            all_markets: pd.DataFrame = pd.DataFrame.from_records(data=list(securities_data.values()), index="id")
            all_markets.rename({"base_currency": "baseAsset", "term_currency": "quoteAsset"},
                               axis="columns", inplace=True)

            usd_volume: List[float] = [
                float(details["volume_24h_change"]) for _, details in statistics_data.items()
            ]

            all_markets.loc[:, "USDVolume"] = usd_volume

            await client.close()

            return all_markets.sort_values("USDVolume", ascending=False)

    async def get_trading_pairs(self) -> List[str]:
        """
        *required
        Get a list of active trading pairs
        (if the market class already specifies a list of trading pairs,
        returns that list instead of all active trading pairs)
        :returns: A list of trading pairs defined by the market class, or all active trading pairs from the rest API
        """
        if not self._trading_pairs:
            try:
                active_markets: pd.DataFrame = await self.get_active_exchange_markets()
                self._trading_pairs = active_markets.index.tolist()
            except Exception:
                self._trading_pairs = []
                self.logger().network(
                    "Error getting active exchange information.",
                    exc_info=True,
                    app_warning_msg="Error getting active exchange information. Check network connection."
                )
        return self._trading_pairs

    @staticmethod
    async def get_snapshot(auth: HeliumExAuth, trading_pair: str) -> Dict[str, any]:
        """
        Fetches order book snapshot for a particular trading pair from the rest API
        :returns: Response from the rest API
        """
        # TODO: use a centrralized api client that can amange auth & retry
        client = aiohttp.ClientSession()
        await auth.get_auth_token()
        auth_header = auth.get_auth_api_header()
        response = await client.get(CONSTANTS.order_book_API(trading_pair), headers=auth_header)
        if response.status == 401:
            await auth.refresh()

        if response.status != 200:
            await client.close()
            raise IOError(
                f"Error fetching OrderBook for {trading_pair}. " f"status: {response.status} message: {response.text}"
            )

        response_json = await response.json()
        await client.close()

        return PAYLOADS.exchange_order_book_api_message_to_order_book_message(trading_pair, response_json)

    async def get_tracking_pairs(self) -> Dict[str, OrderBookTrackerEntry]:
        """
        *required
        Initializes order books and order book trackers for the list of trading pairs
        returned by `self.get_trading_pairs`
        :returns: A dictionary of order book trackers for each trading pair
        """
        trading_pairs: List[str] = await self.get_trading_pairs()
        tracking_pairs: Dict[str, OrderBookTrackerEntry] = {}

        number_of_pairs: int = len(trading_pairs)
        for index, trading_pair in enumerate(trading_pairs):
            try:
                snapshot: Dict[str, any] = await self.get_snapshot(self._heliumex_auth, trading_pair)
                snapshot_timestamp: float = time.time_ns()
                snapshot_msg: OrderBookMessage = HeliumExOrderBook.snapshot_message_from_exchange(
                    snapshot,
                    snapshot_timestamp,
                    metadata={"trading_pair": trading_pair}
                )
                order_book: OrderBook = self.order_book_create_function()
                order_book.apply_snapshot(snapshot_msg.bids, snapshot_msg.asks, snapshot_msg.update_id)

                tracking_pairs[trading_pair] = OrderBookTrackerEntry(
                    trading_pair,
                    snapshot_timestamp,
                    order_book,
                )
                self.logger().info(f"Initialized order book for {trading_pair}. "
                                   f"{index+1}/{number_of_pairs} completed.")
                await asyncio.sleep(0.6)
            except IOError:
                self.logger().network(
                    f"Error getting snapshot for {trading_pair}.",
                    exc_info=True,
                    app_warning_msg=f"Error getting snapshot for {trading_pair}. Check network connection."
                )
            except Exception:
                self.logger().error(f"Error initializing order book for {trading_pair}. ", exc_info=True)

        return tracking_pairs

    async def listen_for_trades(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """
        Listen for trades using websocket  method
        """
        # TODO: there is a "trades" endpoint
        pass

    async def listen_for_order_book_diffs(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """
        *required
        Subscribe to diff channel via web socket, and keep the connection open for incoming messages
        :param ev_loop: ev_loop to execute this function in
        :param output: an async queue where the incoming messages are stored
        """
        # Diff messages are passed with the snapshots
        pass

    async def listen_for_order_book_snapshots(self, ev_loop: asyncio.BaseEventLoop, output: asyncio.Queue):
        """
        *required
        Fetches order book snapshots for each trading pair, and use them to update the local order book
        :param ev_loop: ev_loop to execute this function in
        :param output: an async queue where the incoming messages are stored
        """
        while True:
            try:
                await self._websocket.connect()

                trading_pairs: List[str] = await self.get_trading_pairs()

                for trading_pair in trading_pairs:
                    topic = CONSTANTS.order_book_WS(trading_pair)
                    subscription_id = await self._websocket.subscribe(
                        topic,
                        f"orderbook-{trading_pair}-{str(uuid.uuid1())[:8]}"
                    )

                    async for message in self._websocket.on([topic], [subscription_id]):
                        # TODO: error handling

                        if message["type"] == "update":
                            diff_timestamp: float = time.time_ns()
                            diff: Dict[str, Any] = PAYLOADS.exchange_order_book_socket_message_to_order_book_message(
                                trading_pair, diff_timestamp, message["payload"]
                            )
                            diff_msg: OrderBookMessage = HeliumExOrderBook.diff_message_from_exchange(
                                diff,
                                diff_timestamp,
                                metadata={"trading_pair": trading_pair}
                            )
                            output.put_nowait(diff_msg)
                            self.logger().debug(f"Saved order book diff for {trading_pair}")

                        elif message["type"] == "snapshot":
                            snapshot_timestamp: float = time.time_ns()
                            snapshot: Dict[str, Any] = PAYLOADS.exchange_order_book_socket_message_to_order_book_message(
                                trading_pair, snapshot_timestamp, message["payload"]
                            )
                            snapshot_msg: OrderBookMessage = HeliumExOrderBook.snapshot_message_from_exchange(
                                snapshot,
                                snapshot_timestamp,
                                metadata={"trading_pair": trading_pair}
                            )
                            output.put_nowait(snapshot_msg)
                            self.logger().debug(f"Saved order book snapshot for {trading_pair}")
                        else:
                            self.logger().error(f"unknown message type: {message}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger().error(f"Unexpected error listen_for_order_book_snapshots {str(e)}", exc_info=True)
                await asyncio.sleep(5.0)
            finally:
                await self._websocket.disconnect()
