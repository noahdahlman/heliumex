#!/usr/bin/env python
from os.path import join, realpath
import sys; sys.path.insert(0, realpath(join(__file__, "../../../")))
from typing import Optional

import logging
import asyncio
import unittest
import conf

from hummingbot.core.utils.async_utils import safe_ensure_future

from hummingbot.market.heliumex.heliumex_user_stream_tracker import HeliumExUserStreamTracker
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS


class HeliumExUserStreamTrackerUnitTest(unittest.TestCase):
    user_stream_tracker: Optional[HeliumExUserStreamTracker] = None

    # use all available pairs
    trading_pairs = CONSTANTS.CRYPTO_PAIRS

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.heliumex_auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)
        cls.user_stream_tracker = HeliumExUserStreamTracker(trading_pairs=CONSTANTS.CRYPTO_PAIRS)
        cls.user_stream_tracker_task: asyncio.Task = safe_ensure_future(cls.user_stream_tracker.start())
        cls.ev_loop.run_until_complete(cls.wait_til_tracker_ready())

    @classmethod
    async def wait_til_tracker_ready(cls):
        while True:
            if cls.user_stream_tracker.last_recv_time > 0:
                print("Initialized real-time order books.")
                return
            await asyncio.sleep(1)

    def run_async(self, task):
        return self.ev_loop.run_until_complete(task)

    # TODO:
    @unittest.skip
    def test_limit_order_cancelled(self):
        """
        This test should be run after the developer has implemented the limit buy and cancel
        in the corresponding market class
        """
        pass

    # TODO:
    @unittest.skip
    def test_limit_order_filled(self):
        """
        This test should be run after the developer has implemented the limit buy in the corresponding market class
        """
        pass

    def test_user_stream_manually(self):
        """
        This test should be run before market functions like buy and sell are implemented.
        Developer needs to manually trigger those actions in order for the messages to show up in the user stream.
        """
        item = self.user_stream_tracker.user_stream.get_no_wait()
        self.assertIsNotNone(item["event_type"])


def main():
    logging.basicConfig(level=logging.INFO)
    unittest.main()


if __name__ == "__main__":
    main()
