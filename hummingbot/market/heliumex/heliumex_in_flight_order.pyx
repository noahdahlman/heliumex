from decimal import Decimal
from typing import (
    Any,
    Dict,
    Optional,
)

from hummingbot.core.event.events import (
    OrderType,
    TradeType
)
from hummingbot.market.heliumex.heliumex_market import HeliumExMarket
from hummingbot.market.in_flight_order_base import InFlightOrderBase

cdef class HeliumExInFlightOrder(InFlightOrderBase):
    def __init__(self,
                 client_order_id: str,
                 exchange_order_id: Optional[str],
                 trading_pair: str,
                 order_type: OrderType,
                 trade_type: TradeType,
                 price: Decimal,
                 amount: Decimal,
                 initial_state: str = "new"):
        super().__init__(
            HeliumExMarket,
            client_order_id,
            exchange_order_id,
            trading_pair,
            order_type,
            trade_type,
            price,
            amount,
            initial_state,
        )

    @property
    def is_done(self) -> bool:
        return self.last_state in [
            "suspended",
            "filled",
            "canceled",
            "expired",
            "rejected",
            "completely_filled"
        ]

    @property
    def is_failure(self) -> bool:
        return self.last_state in [
            "suspended",
            "canceled",
            "expired",
            "rejected"
        ]

    @property
    def is_cancelled(self) -> bool:
        return self.last_state == "canceled"

    @property
    def order_type_description(self) -> str:
        """
        :return: Order description string . One of ["limit buy" / "limit sell" / "market buy" / "market sell"]
        """
        order_type = "market" if self.order_type is OrderType.MARKET else "limit"
        side = "buy" if self.trade_type == TradeType.BUY else "sell"
        return f"{order_type} {side}"

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> InFlightOrderBase:
        """
        :param data: json data from API, or from the local cache
        :return: formatted InFlightOrder
        """
        # this method expects an active order, not an historical order
        cdef:
            HeliumExInFlightOrder retval = HeliumExInFlightOrder(
                data["exchange_order_id"] if "exchange_order_id" in data else data["id"],
                data["client_order_id"] if "client_order_id" in data else data["order_id"],
                data["trading_pair"] if "trading_pair" in data else data["security_id"],
                getattr(OrderType, data["order_type"] if "order_type" in data else data["type"]),
                getattr(TradeType, data["trade_type"] if "trade_type" in data else data["side"]),
                Decimal(data["price"]),
                Decimal(data["amount"] if "amount" in data else data["quantity"]),
                data["last_state"] if "last_state" in data else data["status"]
            )
        # TODO: determine if we need these by forcing a state transition on an open order
        # e.g. open an order for 20 and then buy only 5 to partially fill

        # and see if we can get a trade notification that include state relevant to these fields
        retval.executed_amount_base = Decimal(data["executed_amount_base"]) if "executed_amount_base" in data else Decimal(data["cumulative_quantity"])
        retval.executed_amount_quote = Decimal(data["executed_amount_quote"]) if "executed_amount_quote" in data else Decimal(data["cumulative_quantity"]) * Decimal(data["average_price"])
        retval.fee_asset = data["fee_asset"]
        retval.fee_paid = Decimal(data["fee_paid"])
        retval.last_state = data["last_state"]
        return retval

    def update_with_execution_report(self, execution_report: Dict[str, Any]):
        """
        Update the order with an execution report
        """
        inbound_order_id = execution_report["id"]
        if inbound_order_id != self.exchange_order_id:
            # this is not the right order
            return

        self.last_state = execution_report["status"]
        execute_price = Decimal(execution_report["average_price"])
        executed_amount = Decimal(execution_report["cumulative_quantity"])
        self.executed_amount_base = executed_amount
        self.executed_amount_quote = executed_amount * execute_price

        if "completely_filled" in execution_report["status"]:
            # TODO: verify twe only ever get one event
            first_event = execution_report["events"][0]
            self.fee_asset = first_event["commission_currency"]
            # TODO: verify we want the ABS
            self.fee_paid = Decimal(abs(first_event["commission"]))
