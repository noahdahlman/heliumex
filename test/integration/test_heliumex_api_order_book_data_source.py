#!/usr/bin/env python
from os.path import (
    join,
    realpath
)
import sys; sys.path.insert(0, realpath(join(__file__, "../../../")))

import asyncio
import unittest
from typing import List, Dict, Any
import conf

from hummingbot.core.data_type.order_book_tracker_entry import OrderBookTrackerEntry
from hummingbot.core.data_type.order_book_message import OrderBookMessageType

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_order_book_message import HeliumExOrderBookMessage
from hummingbot.market.heliumex.heliumex_api_order_book_data_source import HeliumExAPIOrderBookDataSource

# TODO: execute a test to verify the case where an order book snapshot is received,
# then a diff is received and the diff is applied
# since we do not have timestamps on these responses, we have to assume the orders are coming in order
# which means we should probably periodically refresh using snapshots from the API as well


class TestHeliumExApiOrderBookDataSource(unittest.TestCase):
    auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.data_source: HeliumExAPIOrderBookDataSource = HeliumExAPIOrderBookDataSource(
            heliumex_auth=cls.auth,
            trading_pairs=CONSTANTS.CRYPTO_PAIRS
        )

    def test_get_active_exchange_markets(self):
        async def run_get_active_exchange_markets():

            result = await self.data_source.get_active_exchange_markets(self.auth)
            self.assertGreater(result.size, 0)
            self.assertTrue("baseAsset" in result)
            self.assertTrue("quoteAsset" in result)
            self.assertTrue("USDVolume" in result)

        self.ev_loop.run_until_complete(run_get_active_exchange_markets())

    def test_get_trading_pairs(self):
        result: List[str] = self.ev_loop.run_until_complete(
            self.data_source.get_trading_pairs())

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIsInstance(result[0], str)
        self.assertEqual(result[0], "HNTUSDC")

    def test_get_snapshot_from_api(self):
        result: Dict[str, Any] = self.ev_loop.run_until_complete(
            self.data_source.get_snapshot(self.auth, "HNTUSDC"))

        self.assertEqual(result["security_id"], "HNTUSDC")

    def test_get_tracking_pairs(self):
        async def run_get_tracking_pairs():
            tracking_pairs: Dict[str, OrderBookTrackerEntry] = await self.data_source.get_tracking_pairs()
            assert any(tracking_pairs)

            self.assertTrue(tracking_pairs["HNTUSDC"].trading_pair == "HNTUSDC")

        self.ev_loop.run_until_complete(run_get_tracking_pairs())

    def test_listen_for_order_book_snapshot(self):
        timeout = 6  # should be long enough to get a response back
        queue = asyncio.Queue()

        try:
            self.ev_loop.run_until_complete(
                # Force exit from event loop after set timeout seconds
                asyncio.wait_for(
                    self.data_source.listen_for_order_book_snapshots(ev_loop=self.ev_loop, output=queue),
                    timeout=timeout
                )
            )
        except asyncio.exceptions.TimeoutError as e:
            print(e)

        # Make sure that the number of items in the queue after certain seconds make sense
        # For instance, when the asyncio sleep time is set to 5 seconds in the method
        # If we configure timeout to be the same length, only 1 item has enough time to be received
        self.assertGreaterEqual(queue.qsize(), 1)

        # Validate received response has correct data types
        first_item = queue.get_nowait()
        self.assertIsInstance(first_item, HeliumExOrderBookMessage)
        self.assertIsInstance(first_item.type, OrderBookMessageType)

        # Validate order book message type
        self.assertEqual(first_item.type, OrderBookMessageType.SNAPSHOT)

        # TODO: Validate snapshot received matches with the original snapshot received from API
        # self.assertEqual(first_item.content['bids'], FixtureLiquid.SNAPSHOT_2['buy_price_levels'])
        # self.assertEqual(first_item.content['asks'], FixtureLiquid.SNAPSHOT_2['sell_price_levels'])

        # Validate the rest of the content
        self.assertEqual(first_item.content['trading_pair'], "HNTUSDC")
        # self.assertEqual(first_item.content['product_id'], 27)
