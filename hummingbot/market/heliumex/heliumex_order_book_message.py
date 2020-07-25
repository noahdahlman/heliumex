#!/usr/bin/env python

import pandas as pd
from typing import (
    Dict,
    List,
    Optional,
)

from hummingbot.core.data_type.order_book_row import OrderBookRow
from hummingbot.core.data_type.order_book_message import (
    OrderBookMessage,
    OrderBookMessageType,
)


class HeliumExOrderBookMessageEntry:
    timestamp: str
    level: int
    side: str
    quantity: str
    price: str
    action: str
    number_of_orders: int
    exchange_id: str

    def __init(self, *args, **kwargs):
        for arg in args:
            for key in arg:
                setattr(self, key, arg[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])


class HeliumExOrderBookMessage(OrderBookMessage):
    def __new__(
        cls,
        message_type: OrderBookMessageType,
        content: Dict[str, any],
        timestamp: Optional[float] = None,
        *args,
        **kwargs,
    ):
        if timestamp is None:
            if message_type is OrderBookMessageType.SNAPSHOT:
                raise ValueError("timestamp must not be None when initializing snapshot messages.")
            timestamp = pd.Timestamp(content["timestamp"], tz="UTC").timestamp()
        return super(HeliumExOrderBookMessage, cls).__new__(
            cls, message_type, content, timestamp=timestamp, *args, **kwargs
        )

    @property
    def update_id(self) -> int:
        if self.type in [OrderBookMessageType.DIFF, OrderBookMessageType.SNAPSHOT]:
            return int(self.content["sequence_number"])
        else:
            return -1

    @property
    def trade_id(self) -> int:
        if self.type is OrderBookMessageType.TRADE:
            return int(self.content["sequence"])
        return -1

    @property
    def trading_pair(self) -> str:
        return self.content["security_id"]

    @property
    def asks(self) -> List[OrderBookRow]:
        return [
            OrderBookRow(float(entry["price"]), float(entry["amount"]), self.update_id) for entry in self.content["asks"]
        ]

    @property
    def bids(self) -> List[OrderBookRow]:
        return [
            OrderBookRow(float(entry["price"]), float(entry["amount"]), self.update_id) for entry in self.content["bids"]
        ]

    # @property
    # def asks(self) -> List[OrderBookRow]:

    #     retval: List[OrderBookRow] = []
    #     for entry in self.content["entries"]:
    #         entry_ = HeliumExOrderBookMessageEntry(entry)
    #         if entry_.side == "sell":
    #             retval.append(OrderBookRow(float(entry_.price), float(entry_.quantity), self.update_id))

    #     return retval

    # @property
    # def bids(self) -> List[OrderBookRow]:
    #     retval: List[OrderBookRow] = []
    #     for entry in self.content["entries"]:
    #         entry_ = HeliumExOrderBookMessageEntry(entry)
    #         if entry_.side == "buy":
    #             retval.append(OrderBookRow(float(entry_.price), float(entry_.quantity), self.update_id))

    #     return retval

    def __eq__(self, other) -> bool:
        return self.type == other.type and self.timestamp == other.timestamp

    def __lt__(self, other) -> bool:
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        else:
            """
            If timestamp is the same, the ordering is snapshot < diff < trade
            """
            return self.type.value < other.type.value
