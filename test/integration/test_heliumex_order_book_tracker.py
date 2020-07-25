#!/usr/bin/env python
import sys
import asyncio
import logging
import unittest
import conf

import pandas as pd


from os.path import join, realpath
from typing import Dict, Optional, List, Tuple
from hummingbot.core.event.event_logger import EventLogger
from hummingbot.core.event.events import OrderBookEvent

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_order_book_tracker import HeliumExOrderBookTracker
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_tracker import (
    OrderBookTrackerDataSourceType
)


from hummingbot.core.utils.async_utils import safe_ensure_future

sys.path.insert(0, realpath(join(__file__, "../../../")))


class TestHeliumExOrderBookTracker(unittest.TestCase):
    auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)
    order_book_tracker: Optional[HeliumExOrderBookTracker] = None
    events: List[OrderBookEvent] = [
        OrderBookEvent.TradeEvent
    ]
    trading_pairs = CONSTANTS.CRYPTO_PAIRS

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.order_book_tracker: HeliumExOrderBookTracker = HeliumExOrderBookTracker(
            cls.auth,
            OrderBookTrackerDataSourceType.EXCHANGE_API,
            trading_pairs=cls.trading_pairs)
        cls.order_book_tracker_task: asyncio.Task = safe_ensure_future(cls.order_book_tracker.start())
        cls.ev_loop.run_until_complete(cls.wait_til_tracker_ready())

    @classmethod
    async def wait_til_tracker_ready(cls):
        while True:
            if cls.order_book_tracker.ready:
                print("Initialized real-time order books.")
                return
            await asyncio.sleep(1)

    def setUp(self):
        self.event_logger = EventLogger()
        for event_tag in self.events:
            for trading_pair, order_book in self.order_book_tracker.order_books.items():
                order_book.add_listener(event_tag, self.event_logger)

    def test_order_book_tracker_initializes(self):
        """
        Get and order book and a slice of prices
        """
        # This test assumes there is at least some volume on the exchange
        # which should be true for an integration test against a production environment
        BUY = True
        SELL = False

        order_books: Dict[str, OrderBook] = self.order_book_tracker.order_books
        book: OrderBook = order_books["HNTUSDC"]
        self.assertIsNotNone(book)

        current_buy_price = book.get_price(BUY)
        current_sell_price = book.get_price(SELL)

        self.assertTrue(current_buy_price > 0.000001)
        self.assertTrue(current_sell_price > 0.000001)

        # TODO: this needs fixed
        # self.assertGreaterEqual(book.get_price_for_volume(BUY, 10).result_price,
        #                         book.get_price(True))
        # self.assertLessEqual(book.get_price_for_volume(SELL, 10).result_price,
        #                      book.get_price(False))

    def test_order_book_tracker_snapshot(self):
        """
        Get a snapshot from the tracker
        """
        snapshots: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]] = self.order_book_tracker.snapshot
        self.assertIsNotNone(snapshots["HNTUSDC"])
        # TODO: imspect

    # def test_order_book_trade_event_omission(self):
    #     # TODO: see bitfinex

    # Test Event Omissions

    # TODO: def test_diff_msg_get_added_to_order_book(self):
    # It doesnt look like this one is reliable given how infrequently diff messages arrive
    # perhaps we need to issue an order in otder to force a diff


def main():
    logging.basicConfig(level=logging.INFO)
    unittest.main()


if __name__ == "__main__":
    main()
