#!/usr/bin/env python

import asyncio
from collections import (
    defaultdict,
    deque
)
import logging
from typing import (
    Deque,
    Dict,
    List,
    Optional
)

from hummingbot.logger import HummingbotLogger

from hummingbot.core.data_type.order_book_tracker import OrderBookTracker, OrderBookTrackerDataSourceType
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource

from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_api_order_book_data_source import HeliumExAPIOrderBookDataSource
from hummingbot.market.heliumex.heliumex_order_book_message import HeliumExOrderBookMessage
from hummingbot.market.heliumex.heliumex_order_book import HeliumExOrderBook

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS


class HeliumExOrderBookTracker(OrderBookTracker):
    _heliumex_obt_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._heliumex_obt_logger is None:
            cls._heliumex_obt_logger = logging.getLogger(__name__)
        return cls._heliumex_obt_logger

    def __init__(self,
                 heliumex_auth: HeliumExAuth,
                 data_source_type: OrderBookTrackerDataSourceType = OrderBookTrackerDataSourceType.EXCHANGE_API,
                 trading_pairs: Optional[List[str]] = None):
        super().__init__(data_source_type=data_source_type)

        self._heliumex_auth: HeliumExAuth = heliumex_auth

        self._ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()

        self._data_source: Optional[OrderBookTrackerDataSource] = None
        self._order_book_snapshot_stream: asyncio.Queue = asyncio.Queue()
        self._order_book_diff_stream: asyncio.Queue = asyncio.Queue()

        self._process_msg_deque_task: Optional[asyncio.Task] = None
        self._past_diffs_windows: Dict[str, Deque] = {}

        self._order_books: Dict[str, HeliumExOrderBook] = {}
        self._saved_message_queues: Dict[str, Deque[HeliumExOrderBookMessage]] = defaultdict(lambda: deque(maxlen=1000))

        self._trading_pairs: Optional[List[str]] = trading_pairs

    @property
    def data_source(self) -> OrderBookTrackerDataSource:
        """
        *required
        Initializes an order book data source (Either from live API or from historical database)
        :return: OrderBookTrackerDataSource
        """
        if not self._data_source:
            if self._data_source_type is OrderBookTrackerDataSourceType.EXCHANGE_API:
                self._data_source = HeliumExAPIOrderBookDataSource(
                    self._heliumex_auth, trading_pairs=self._trading_pairs
                )
            else:
                raise ValueError(f"data_source_type {self._data_source_type} is not supported.")
        return self._data_source

    @property
    def exchange_name(self) -> str:
        """
        *required
        Name of the current exchange
        """
        return CONSTANTS.HELIUMEX_EXCHANGE_NAME
