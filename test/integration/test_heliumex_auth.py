#!/usr/bin/env python

import asyncio
import logging
import unittest

import conf
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth


class TestHeliumExAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()

        def handler(loop, context):
            print(context)
        cls.ev_loop.set_exception_handler(handler)

        api_key = conf.heliumex_api_key
        secret_key = conf.heliumex_secret_key
        # TODO: TOTP seed
        cls.auth: HeliumExAuth = HeliumExAuth(api_key, secret_key)

    def test_auth_succeeds(self):
        result = self.ev_loop.run_until_complete(self.auth.get_auth_token())
        assert result is not None and len(result) > 0


def main():
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()


if __name__ == "__main__":
    main()
