import time
import uuid
from typing import Any, Dict, List
from decimal import Decimal

# TODO: historical bars send payload
# todo limit orders are gtc while market orders are gtd


def order_create(security_id: str, type: str, side: str, quantity: Decimal, price: Decimal, client_order_id: str = None) -> Dict[str, str]:

    order = {
        "client_order_id": client_order_id if client_order_id is not None else str(uuid.uuid4()).upper(),
        "security_id": security_id,
        "type": type,
        "side": side,
        "quantity": "{0:f}".format(quantity),
        "price": "{0:f}".format(price),
        "submission_time": time.time_ns(),
        "destination": "SHIFTFX"
    }
    if type == "market":
        return {
            **order,
            "time_in_force": "gtd",
            "expire_time": 0,
        }
    else:
        return {
            **order,
            "time_in_force": "gtc",
        }


def exchange_order_book_api_message_to_order_book_message(trading_pair: str, response_json: Dict[str, Any]) -> Dict[str, Any]:
    # bids
    bids: List[Dict[str, Any]] = [
        {
            "price": float(entry["price"]),
            "amount": float(entry["quantity"]),
            "level": entry["level"],
            "number_of_orders": entry["number_of_orders"]
        }
        for entry in response_json[0]["entries"]
        if entry["side"] == "buy"
    ]

    # asks
    asks: List[Dict[str, Any]] = [
        {
            "price": float(entry["price"]),
            "amount": float(entry["quantity"]),
            "level": entry["level"],
            "number_of_orders": entry["number_of_orders"]
        }
        for entry in response_json[0]["entries"]
        if entry["side"] == "sell"
    ]

    return {
        "type": "api",
        "security_id": trading_pair,
        "sequence_number": response_json[0]["sequence_number"],
        "timestamp": response_json[0]["timestamp"],
        "bids": bids,
        "asks": asks
    }


def exchange_order_book_socket_message_to_order_book_message(trading_pair: str, timestamp: float, payload: List[Dict[str, Any]]) -> Dict[str, Any]:

    # bids
    bids: List[Dict[str, Any]] = [
        {
            "price": float(entry["price"]),
            "amount": float(0) if entry["volume"] is None else float(entry["volume"]),
            "level": entry["level"],
            "volume_percent": entry["volume_percent"]
        }
        for entry in payload
        if entry["side"] == "BUY"
    ]

    # asks
    asks: List[Dict[str, Any]] = [
        {
            "price": float(entry["price"]),
            "amount": float(0) if entry["volume"] is None else float(entry["volume"]),
            "level": entry["level"],
            "volume_percent": entry["volume_percent"]
        }
        for entry in payload
        if entry["side"] == "SELL"
    ]

    return {
        "type": "websocket",
        "security_id": trading_pair,
        "sequence_number": timestamp,
        "timestamp": timestamp,
        "bids": bids,
        "asks": asks
    }
