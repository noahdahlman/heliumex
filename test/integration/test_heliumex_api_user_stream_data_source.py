#!/usr/bin/env python
from os.path import (
    join,
    realpath
)
import sys; sys.path.insert(0, realpath(join(__file__, "../../../")))

import asyncio
import unittest
import conf

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_api_user_stream_data_source import HeliumExAPIUserStreamDataSource


class TestHeliumExApiUserStreamDataSource(unittest.TestCase):

    auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.data_source: HeliumExAPIUserStreamDataSource = HeliumExAPIUserStreamDataSource(
            heliumex_auth=cls.auth,
            trading_pairs=CONSTANTS.CRYPTO_PAIRS
        )

    def test_listen_for_user_stream(self):
        timeout = 6
        queue = asyncio.Queue()

        try:
            self.ev_loop.run_until_complete(
                # Force exit from event loop after set timeout seconds
                asyncio.wait_for(
                    self.data_source.listen_for_user_stream(ev_loop=self.ev_loop, output=queue),
                    timeout=timeout
                )
            )
        except asyncio.exceptions.TimeoutError as e:
            print(e)

        # Make sure that the number of items in the queue after certain seconds make sense
        # For instance, when the asyncio sleep time is set to 5 seconds in the method
        # If we configure timeout to be the same length, only 1 item has enough time to be received
        self.assertGreaterEqual(queue.qsize(), 1)

        try:
            while True:
                # Validate received response has correct data types
                item = queue.get_nowait()

                if item["event_type"] == CONSTANTS.HeliumExEventTypes.ActiveOrdersUpdate:
                    # TODO:
                    print(item)
                    self.assertIsNotNone(item["order"])
                    pass
                elif item["event_type"] == CONSTANTS.HeliumExEventTypes.BalanceUpdate:
                    # TODO:
                    print(item)
                    self.assertIsNotNone(item["account_id"])
                    pass
                else:
                    self.fail("wrong message type")

        except asyncio.QueueEmpty:
            pass
