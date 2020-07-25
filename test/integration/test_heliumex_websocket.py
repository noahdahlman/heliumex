#!/usr/bin/env python
import asyncio
import sys
import logging
import unittest
import conf


from os.path import join, realpath

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_websocket import HeliumExWebsocket
from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth

sys.path.insert(0, realpath(join(__file__, "../../../")))


class TestHeliumExWebsocket(unittest.TestCase):

    default_test_timeout = 10

    auth = HeliumExAuth(conf.heliumex_api_key, conf.heliumex_secret_key)
    websocket = HeliumExWebsocket()
    data_services_websocket = HeliumExWebsocket(CONSTANTS.HELIUMEX_WS_DATA_SERVICE_URL, use_stomp=False)

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()

    # Authenticated Tests

    def test_websocket_connect_can_authorize(self):
        result = self.ev_loop.run_until_complete(self._login())
        self.assertTrue(result)

    # SUBSCRIBE Tests

    def test_websocket_subscribe_user_orders(self):
        """
        Retrieve a stream of open orders
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.orders_WS())

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.HELIUMEX_WS_ENDPOINT_ORDERS_LISTEN], [subscription_id]):
                ret_val = message
                break
            return ret_val

        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        # TODO: verify the data
        self.assertIsNotNone(result)

    def test_websocket_subscribe_account_balances(self):
        """
        Retrieve a stream of account balance changes
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.HELIUMEX_WS_ENDPOINT_USER_BALANCES)

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.HELIUMEX_WS_ENDPOINT_USER_BALANCES_LISTEN], [subscription_id]):
                ret_val = message
                break
            return ret_val

        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        # TODO: verify the data
        self.assertIsNotNone(result)

    # Data Services SUBSCRIBE Tests

    def test_data_services_websocket_subscribe_quotes(self):
        """
        Retrieve the current price quotes
        """
        async def coroutine():
            connected = await self.data_services_websocket.connect()
            self.assertTrue(connected)

            subscription_id = await self.data_services_websocket.subscribe(CONSTANTS.quotes_WS())

            ret_val = None
            async for message in self.data_services_websocket.on([CONSTANTS.quotes_WS()], [subscription_id]):
                ret_val = message
                break
            return ret_val

        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], CONSTANTS.quotes_WS())

    def test_data_services_websocket_subscribe_order_book(self):
        """
        Retrieve the order book snapshot
        """
        async def coroutine():
            connected = await self.data_services_websocket.connect()
            self.assertTrue(connected)

            subscription_id = await self.data_services_websocket.subscribe(CONSTANTS.order_book_WS())

            ret_val = None
            async for message in self.data_services_websocket.on([CONSTANTS.order_book_WS()], [subscription_id]):
                ret_val = message
                break
            return ret_val

        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], CONSTANTS.order_book_WS())

    # SEND Tests

    def test_websocket_get_global_settings(self):
        """
        Retrieve global settings
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
            correlation_id = await self.websocket.send(CONSTANTS.settings_global_WS())

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
                ret_val = message
                break
            return ret_val
        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)

    def test_websocket_get_user_settings(self):
        """
        Retrieve user settings
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
            correlation_id = await self.websocket.send(CONSTANTS.settings_user_WS())

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
                ret_val = message
                break
            return ret_val
        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)

    def test_websocket_get_accounts(self):
        """
        Retrieve accounts with a SEND request
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
            correlation_id = await self.websocket.send(CONSTANTS.accounts_WS())

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
                ret_val = message
                break
            return ret_val
        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)

    def test_websocket_get_order_events(self):
        """
        Retrieve historical orders for the user from a specific point in time
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
            correlation_id = await self.websocket.send(CONSTANTS.order_events_send_WS(), body = '{"start_time":0}')

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
                ret_val = message
                break
            return ret_val
        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)

    def test_websocket_get_trades(self):
        """
        Retrieve recent trades with a SEND request
        """
        async def coroutine():
            connected = await self._login()
            self.assertTrue(connected)

            subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
            correlation_id = await self.websocket.send(CONSTANTS.trades_WS())

            ret_val = None
            async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
                ret_val = message
                break
            return ret_val
        result = self.ev_loop.run_until_complete(asyncio.wait_for(
            coroutine(),
            timeout=self.default_test_timeout
        ))
        self.assertIsNotNone(result)

    # THE ONES ABOVE ACTUALLY WORK

    # TODO: need to verify trade fees

    # def test_order_creation_workflow(self):
    #     """
    #     Try to place and then cancel an order
    #     """
    #     async def coroutine():
    #         await self._login()

    #         subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())

    #         # Create an order
    #         payload = PAYLOADS.order_create("HNTUSDC", "limit", "buy", 1, 0.00000001)
    #         correlation_id = await self.websocket.send(CONSTANTS.create_order_WS(), body=ujson.dumps(payload))

    #         client_order_id = payload["client_order_id"]

    #         # wait for the order created message
    #         async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id]):
    #             response = ujson.loads(message.body)
    #             if response["client_order_id"] == client_order_id:
    #                 self.assertTrue(response["status"] == "pending_new")
    #                 break

    #         # TODO: fix cancel orders since it appears to not be working

    #         correlation_id2 = await self.websocket.send(
    #             CONSTANTS.cancel_order_WS(),
    #             headers={
    #                 "X-Deltix-Order-ID": client_order_id.upper(),
    #                 "X-Deltix-Client-Order-ID": "undefined"
    #             })

    #         ret_val = None
    #         # wait for the order cancelled message
    #         async for message in self.websocket.on([CONSTANTS.socket_receive_responses()], [subscription_id], [correlation_id2]):
    #             response = ujson.loads(message.body)
    #             if response["client_order_id"] == client_order_id:
    #                 print(response)
    #                 self.assertTrue(response["status"] == "canceled")
    #                 ret_val = response
    #                 break
    #         return ret_val

    #     result = self.ev_loop.run_until_complete(asyncio.wait_for(
    #         coroutine(),
    #         timeout=self.default_test_timeout
    #     ))
    #     self.assertIsNotNone(result)

    # def test_order_execution_workflow(self):
    #     # retrieve balances
    #     # if there is an available balance
    #     # place a limit sell order arbitrarily high
    #     # verify we receive notification of the order being created
    #     # verify we receive a book update notification
    #     # cancel the sell order
    #     # verify we receive a book update notification
    #     # place a limit buy order arbitrarily low
    #     # verify we receive a notification of the order being created
    #     # verify we receive a book update notification
    #     # cancel the buy order
    #     # verify we receive a book update notification

    #     # place an arbitrarily small market order
    #     # verify we receive a book update notification
    #     # verify that we receive a trade result
    #     # verify that we receive an order update that the order was filled
    #     ...

    # def test_data_services_websocket_subscribe_current_bars(self):
    #     async def get_current_bars():
    #         connected = await self.data_services_websocket.connect()
    #         self.assertTrue(connected)

    #         subscribed = await self.data_services_websocket.subscribe(CONSTANTS.current_bars_WS())

    #         ret_val = None
    #         async for message in self.data_services_websocket.on(CONSTANTS.current_bars_WS()):
    #             ret_val = message
    #             break
    #         return ret_val

    #     result = self.ev_loop.run_until_complete(get_current_bars())
    #     print(f"RESULT: {result}")
    #     self.assertIsNotNone(result)
    #     self.assertEqual(result["source"], CONSTANTS.current_bars_WS())

    # TODO: def test_websocket_get_historical_bars(self):
    #     """
    #     Gets historical bars
    #     """
    #     async def coroutine():
    #         connected = await self._login()
    #         self.assertTrue(connected)

    #         subscription_id = await self.websocket.subscribe(CONSTANTS.socket_send_responses())
    #         correlation_id = await self.websocket.send(CONSTANTS.trades_WS())

    #         ret_val = None
    #         async for message in self.websocket.on(CONSTANTS.socket_receive_responses(), subscription_id, correlation_id):
    #             ret_val = message
    #             break
    #         return ret_val
    #     result = self.ev_loop.run_until_complete(asyncio.wait_for(
    #         coroutine(),
    #         timeout=self.default_test_timeout
    #     ))
    #     self.assertIsNotNone(result)

    # def test_websocket_get_securities(self):

    #     async def get_securities():
    #         connected = await self._login()
    #         self.assertTrue(connected)

    #         ret_val = None
    #         async for response in self.websocket.request(CONSTANTS.available_securities_WS()):
    #             print(f"RESPONSE: {response}")
    #             ret_val = response
    #             break
    #         return ret_val

    #     result = self.ev_loop.run_until_complete(get_securities())
    #     print(f"RESULT: {result}")
    #     self.assertTrue(result)
    #     self.assertTrue(False)

    async def _login(self):
        connected = await self.websocket.connect(self.auth)
        return connected


def main():
    logging.basicConfig(level = logging.INFO)
    unittest.main()


if __name__ == "__main__":
    main()
