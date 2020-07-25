#!/usr/bin/env python

import sys
import asyncio
import logging
import unittest
import conf

from os.path import join, realpath
from typing import (
    Optional
)
from hummingbot.core.clock import (
    Clock,
    ClockMode
)

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_user_stream_tracker import HeliumExUserStreamTracker
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.core.utils.async_utils import safe_ensure_future

sys.path.insert(0, realpath(join(__file__, "../../../")))


class TestTeliumExUserStreamTracker(unittest.TestCase):
    user_stream_tracker: Optional[HeliumExUserStreamTracker] = None

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)
        cls.trading_pairs = CONSTANTS.CRYPTO_PAIRS
        cls.user_stream_tracker: HeliumExUserStreamTracker = HeliumExUserStreamTracker(
            heliumex_auth=cls.auth, trading_pairs=cls.trading_pairs)
        cls.user_stream_tracker_task: asyncio.Task = safe_ensure_future(cls.user_stream_tracker.start())

    def test_user_stream(self):
        # Wait process some msgs.
        self.ev_loop.run_until_complete(asyncio.sleep(120.0))
        print(self.user_stream_tracker.user_stream)


def main():
    logging.basicConfig(level=logging.INFO)
    unittest.main()


if __name__ == "__main__":
    main()
