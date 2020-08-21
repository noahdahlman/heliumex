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
        auth_token_1 = self.ev_loop.run_until_complete(self.auth.get_auth_token(force_refresh = False))
        assert auth_token_1 is not None and len(auth_token_1) > 0

        refresh_result = self.ev_loop.run_until_complete(self.auth.refresh())
        assert refresh_result

        auth_token_2 = self.ev_loop.run_until_complete(self.auth.get_auth_token(force_refresh = False))
        assert auth_token_2 is not None and len(auth_token_2) > 0

        assert auth_token_1 != auth_token_2


def main():
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()


if __name__ == "__main__":
    main()
