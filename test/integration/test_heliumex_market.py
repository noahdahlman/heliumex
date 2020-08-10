#!/usr/bin/env python
import logging
from os.path import join, realpath
import sys; sys.path.insert(0, realpath(join(__file__, "../../../")))

from hummingbot.logger.struct_logger import METRICS_LOG_LEVEL

import asyncio
import contextlib
from decimal import Decimal
import os
import time
from typing import (
    List,
)
import unittest

import conf
from hummingbot.core.clock import (
    Clock,
    ClockMode
)
from hummingbot.core.event.event_logger import EventLogger
from hummingbot.core.event.events import (
    MarketEvent,
    OrderCancelledEvent,
    BuyOrderCreatedEvent,
    SellOrderCreatedEvent,
    TradeFee,
    TradeType,
)
from hummingbot.core.utils.async_utils import (
    safe_ensure_future,
    safe_gather,
)
import hummingbot.market.heliumex.heliumex_constants as CONSTANTS
from hummingbot.market.heliumex.heliumex_market import HeliumExMarket
from hummingbot.market.market_base import OrderType
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.client.config.fee_overrides_config_map import fee_overrides_config_map

logging.basicConfig(level=METRICS_LOG_LEVEL)


class TestHeliumExMarket(unittest.TestCase):
    events: List[MarketEvent] = [
        MarketEvent.ReceivedAsset,
        MarketEvent.BuyOrderCompleted,
        MarketEvent.SellOrderCompleted,
        MarketEvent.WithdrawAsset,
        MarketEvent.OrderFilled,
        MarketEvent.OrderCancelled,
        MarketEvent.TransactionFailure,
        MarketEvent.BuyOrderCreated,
        MarketEvent.SellOrderCreated,
        MarketEvent.OrderCancelled
    ]

    market: HeliumExMarket
    market_logger: EventLogger
    stack: contextlib.ExitStack

    default_test_timeout = 10

    @classmethod
    def setUpClass(cls):
        cls.ev_loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
        cls.clock: Clock = Clock(ClockMode.REALTIME)
        cls.market: HeliumExMarket = HeliumExMarket(
            heliumex_api_key=conf.heliumex_api_key,
            heliumex_secret_key=conf.heliumex_secret_key,
            heliumex_one_time_password=conf.heliumex_one_time_password,
            trading_pairs=CONSTANTS.CRYPTO_PAIRS
        )
        print("Initializing HeliumEx market... this will take about a minute.")
        cls.clock.add_iterator(cls.market)
        cls.stack = contextlib.ExitStack()
        cls._clock = cls.stack.enter_context(cls.clock)
        cls.ev_loop.run_until_complete(cls.wait_til_ready())

        print("Ready.")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.stack.close()

    @classmethod
    async def wait_til_ready(cls):
        while True:
            now = time.time()
            next_iteration = now // 1.0 + 1

            if cls.market.ready:
                break
            else:
                await cls._clock.run_til(next_iteration)
            await asyncio.sleep(1.0)

    def setUp(self):
        self.db_path: str = realpath(join(__file__, "../heliumex_test.sqlite"))
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

        self.market_logger = EventLogger()
        for event_tag in self.events:
            self.market.add_listener(event_tag, self.market_logger)

    def tearDown(self):
        for event_tag in self.events:
            self.market.remove_listener(event_tag, self.market_logger)
        self.market_logger = None

    async def run_parallel_async(self, *tasks):
        future: asyncio.Future = safe_ensure_future(safe_gather(*tasks))
        while not future.done():
            now = time.time()
            next_iteration = now // 1.0 + 1
            await self.clock.run_til(next_iteration)
        return future.result()

    def run_parallel(self, *tasks):
        return self.ev_loop.run_until_complete(self.run_parallel_async(*tasks))

    def test_get_fee(self):
        """
        Can retrieve fees from API
        """
        limit_fee: TradeFee = self.market.get_fee("HNT", "USDC", OrderType.LIMIT, TradeType.BUY, 1, 1)
        self.assertGreater(limit_fee.percent, 0)
        self.assertEqual(len(limit_fee.flat_fees), 0)
        market_fee: TradeFee = self.market.get_fee("HNT", "USDC", OrderType.MARKET, TradeType.BUY, 1)
        self.assertGreater(market_fee.percent, 0)
        self.assertEqual(len(market_fee.flat_fees), 0)

    def test_fee_overrides_config(self):
        """
        Can override trade fees
        """
        fee_overrides_config_map["heliumex_taker_fee"].value = None
        fee_overrides_config_map["heliumex_taker_fee"].value = Decimal('0.2')
        taker_fee: TradeFee = self.market.get_fee("HNT", "USDC", OrderType.MARKET, TradeType.BUY, Decimal(1),
                                                  Decimal('0.1'))
        self.assertAlmostEqual(Decimal("0.002"), taker_fee.percent)
        fee_overrides_config_map["heliumex_maker_fee"].value = Decimal('0.75')
        maker_fee: TradeFee = self.market.get_fee("HNT", "USDC", OrderType.LIMIT, TradeType.BUY, Decimal(1),
                                                  Decimal('0.1'))
        self.assertAlmostEqual(Decimal("0.0075"), maker_fee.percent)

    def test_order_book(self):
        BUY = True
        SELL = False

        order_book: OrderBook = self.market.order_books["HNTUSDC"]
        self.assertIsNotNone(order_book)

        current_buy_price = order_book.get_price(BUY)
        current_sell_price = order_book.get_price(SELL)

        self.assertTrue(current_buy_price > 0.000001)
        self.assertTrue(current_sell_price > 0.000001)

    def test_limit_buy(self):
        """
        Can execute a limit buy order
        """
        self.assertGreater(self.market.get_balance("USDC"), Decimal("0.01"))
        trading_pair = "HNTUSDC"
        BUY = True
        amount: Decimal = Decimal("1")

        quantized_amount: Decimal = self.market.quantize_order_amount(trading_pair, amount)
        current_bid_price: Decimal = self.market.get_price(trading_pair, BUY)

        self.assertTrue(quantized_amount > 0.01)
        self.assertTrue(current_bid_price > 0.00000001)

        # Creaate the order at the minimum price
        bid_price: Decimal = Decimal("0.00000002")
        quantize_bid_price: Decimal = self.market.quantize_order_price(trading_pair, bid_price)

        self.assertTrue(quantize_bid_price > 0.00000001)
        self.assertTrue(quantize_bid_price >= bid_price)

        # Create a Buy Limit - Good Til Cancelled order
        order_id = self.market.buy(trading_pair, quantized_amount, OrderType.LIMIT, quantize_bid_price)
        self.assertTrue(len(order_id) > 1)

        [order_created_event] = self.run_parallel(self.market_logger.wait_for(BuyOrderCreatedEvent))

        created_events: List[BuyOrderCreatedEvent] = [event for event in self.market_logger.event_log
                                                      if isinstance(event, BuyOrderCreatedEvent) and event.order_id == order_id]
        self.assertTrue(any(created_events))

        # Cancel the order
        cancelled_order_id = self.market.cancel(trading_pair, order_id)
        self.assertTrue(len(cancelled_order_id) > 1)

        [order_cancelled_event] = self.run_parallel(self.market_logger.wait_for(OrderCancelledEvent))

        cancelled_events: List[OrderCancelledEvent] = [event for event in self.market_logger.event_log
                                                       if isinstance(event, OrderCancelledEvent) and event.order_id == cancelled_order_id]
        self.assertTrue(any(cancelled_events))

        # Reset the logs
        self.market_logger.clear()

    def test_limit_sell(self):
        self.assertGreater(self.market.get_balance("HNT"), Decimal("1"))
        trading_pair = "HNTUSDC"
        SELL = False
        amount: Decimal = Decimal("1")

        quantized_amount: Decimal = self.market.quantize_order_amount(trading_pair, amount)
        current_ask_price: Decimal = self.market.get_price(trading_pair, SELL)

        self.assertTrue(quantized_amount > 0.01)
        self.assertTrue(current_ask_price > 0.00000001)

        # place an order that is arbitrarily larger than the best ask
        # TODO: use max order price
        ask_price: Decimal = current_ask_price * Decimal("1.5")
        quantize_ask_price: Decimal = self.market.quantize_order_price(trading_pair, ask_price)

        self.assertTrue(quantize_ask_price > 0.00000001)
        self.assertTrue(quantize_ask_price >= ask_price)

        # Create a Sell Limit - Good Til Cancelled order
        order_id = self.market.sell(trading_pair, quantized_amount, OrderType.LIMIT, quantize_ask_price)
        self.assertTrue(len(order_id) > 1)

        [order_created_event] = self.run_parallel(self.market_logger.wait_for(SellOrderCreatedEvent))

        created_events: List[SellOrderCreatedEvent] = [created_event for created_event in self.market_logger.event_log
                                                       if isinstance(created_event, SellOrderCreatedEvent) and created_event.order_id == order_id]
        self.assertTrue(any(created_events))

        # Cancel the order
        cancelled_order_id = self.market.cancel(trading_pair, order_id)
        self.assertTrue(len(cancelled_order_id) > 1)

        [order_cancelled_event] = self.run_parallel(self.market_logger.wait_for(OrderCancelledEvent))

        cancelled_events: List[OrderCancelledEvent] = [event for event in self.market_logger.event_log
                                                       if isinstance(event, OrderCancelledEvent) and event.order_id == cancelled_order_id]
        self.assertTrue(any(cancelled_events))

        # Reset the logs
        self.market_logger.clear()

    def test_cancel_all(self):

        self.market.cancel_all(30)

        self.assertTrue(True)
