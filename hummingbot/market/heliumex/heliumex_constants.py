import enum
HELIUMEX_EXCHANGE_ID = "HELIUMEX"

HELIUMEX_AUTH_URL = "https://authentication.cryptosrvc.com/api"

HELIUMEX_REST_URL = "https://trade.heliumex.shiftmarketsdev.com/api/v1"
HELIUMEX_WS_URL = "wss://trade.heliumex.shiftmarketsdev.com/websocket/v1"
HELIUMEX_WS_DATA_SERVICE_URL = "wss://exchange-data-service.cryptosrvc.com/"


HELIUMEX_API_ENDPOINT_EXCHANGE_TOKEN = "/user_authentication/exchangeToken"
HELIUMEX_API_ENDPOINT_REFRESH_TOKEN = "/user_authentication/refreshAccessToken"

# API Endpoints
HELIUMEX_API_ENDPOINT_ACCOUNTS = "/accounts"
HELIUMEX_API_ENDPOINT_CURRENCIES = "/currencies"
HELIUMEX_API_ENDPOINT_ORDER_BOOK_SNAPSHOT = "/books"
HELIUMEX_API_ENDPOINT_ORDERS = "/orders"
HELIUMEX_API_ENDPOINT_ORDERS_EVENTS = "/orders/events"
HELIUMEX_API_ENDPOINT_SECURITIES = "/securities"
HELIUMEX_API_ENDPOINT_SECURITIES_STATISTICS = "/securities/statistics"
HELIUMEX_API_ENDPOINT_TRANSACTIONS_COMPLETE = "/transactions/complete"

# Websocket SUBSCRIBE Endpoints
HELIUMEX_WS_ENDPOINT_ACCOUNTS = "/app/v1/accounts"
HELIUMEX_WS_ENDPOINT_ORDERS = "/user/v1/orders"
HELIUMEX_WS_ENDPOINT_ORDERS_LISTEN = "/v1/orders"
# ELIUMEX_WS_ENDPOINT_ORDER_EVENTS_SUBSCRIBE = "/user/v1/orders"
HELIUMEX_WS_ENDPOINT_USER_BALANCES = "/user/v1/balances"
HELIUMEX_WS_ENDPOINT_USER_BALANCES_LISTEN = "/v1/balances"

HELIUMEX_WS_ENDPOINT_USER_RESPONSES = "/user/v1/responses"
HELIUMEX_WS_ENDPOINT_RESPONSES_LISTEN_DESTINATION = "/v1/responses"
HELIUMEX_WS_ENDPOINT_ALL_SECURITIES_STATISTCS = "/user/v1/securities/statistics"

# Exchange Data Service SUBSCRIBE Endpoints
HELIUMEX_WS_ENDPOINT_QUOTES = "/topic/HELIUMEX/quotes"
HELIUMEX_WS_ENDPOINT_ORDER_BOOK = "/topic/HELIUMEX/orderbook"
HELIUMEX_WS_ENDPOINT_CURRENT_BARS = "/topic/HELIUMEX/current-bars"

# Websocket SEND Event Endpoints
HELIUMEX_WS_ENDPOINT_ACCOUNTS = "/app/v1/accounts"
HELIUMEX_WS_ENDPOINT_AVAILABLE_SECURITIES = "/app/v1/securities"
HELIUMEX_WS_EDNPOINT_CREATE_ORDER = "/app/v1/orders/create"
HELIUMEX_WS_ENDPOINT_CANCEL_ORDER = "/app/v1/orders/cancel"
HELIUMEX_WS_ENDPOINT_GLOBAL_SETTINGS = "/app/v1/global/settings"
HELIUMEX_WS_ENDPOINT_HISTORICAL_BARS = "/app/v1/historical-bars"
HELIUMEX_WS_ENDPOINT_ORDER_EVENTS_SEND = "/app/v1/orders/events"
HELIUMEX_WS_ENDPOINT_TRADES = "/app/v1/trades"
HELIUMEX_WS_ENDPOINT_USER_SETTINGS = "/app/v1/user/settings/get"

CRYPTO_PAIRS = [
    "HNTUSDC"
]

# Defaults
MESSAGE_TIMEOUT = 3.0
PING_TIMEOUT = 5.0
MAX_RETRIES = 20
WS_PING_TIMEOUT = 5.0
WS_MESSAGE_TIMEOUT = 10.0

# OrderBook
MESSAGE_TIMEOUT_ORDER_BOOK = 30.0
PING_TIMEOUT_ORDER_BOOK = 10.0

HELIUMEX_EXCHANGE_NAME = "heliumex"

# Fees
DEFAULT_MAKER_FEE = "0.0035"
DEFAULT_TAKER_FEE = "0.0035"


class HeliumExEventTypes(enum.Enum):
    OrderbookSnapshot = "OrderbookSnapshot",
    OrderbookUpdate = "OrderbookUpdate",
    TradesSnapshot = "TradesSnapshot",
    TradesUpdate = "TradesUpdate",
    ActiveOrdersSnapshot = "ActiveOrdersSnapshot",
    ActiveOrdersUpdate = "ActiveOrdersUpdate",
    BalanceSnapshot = "BalanceSnapshot",
    BalanceUpdate = "BalanceUpdate"


class HeliumExPeriodicity(enum.Enum):
    MINUTE_1 = "minute1"
    MINUTE_5 = "minute5"
    MINUTE_15 = "minute15"
    MINUTE_30 = "minute30"
    DAY_1 = "day"


def accounts_API() -> str:
    """
    Returns an array of accounts for the currently authenticated user.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ACCOUNTS}"


def accounts_WS() -> str:
    """
    Returns an array of accounts for the currently authenticated user.
    This is the SEND equivalent of `balances_WS`
    """
    return f"{HELIUMEX_WS_ENDPOINT_ACCOUNTS}"


def available_currencies_API() -> str:
    """
    Gets all currencies available on the exchange.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_CURRENCIES}"


def available_securities_API() -> str:
    """
    Returns a list of securities available on the exchange.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_SECURITIES}"


def available_securities_WS() -> str:
    """
    Returns a list of securities available on the exchange.
    """
    return f"{HELIUMEX_WS_ENDPOINT_AVAILABLE_SECURITIES}"


def all_securities_statistics_API() -> str:
    """
    Gets current prices for all securities.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_SECURITIES_STATISTICS}"


def balances_WS() -> str:
    """
    Returns an array of accounts for the currently authenticated user.
    This is the SUBSCRIBE version of `accounts_WS`
    """
    return f"{HELIUMEX_WS_ENDPOINT_USER_BALANCES}"


def cancel_order_WS() -> str:
    """
    Sends a request to cancel an open order.
    """
    return f"{HELIUMEX_WS_ENDPOINT_CANCEL_ORDER}"


def cancel_order_API() -> str:
    """
    Creates a new order on the exchange.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ORDERS}"


def create_order_WS() -> str:
    """
    Creates a new order on the exchange.
    """
    return f"{HELIUMEX_WS_EDNPOINT_CREATE_ORDER}"


def create_order_API() -> str:
    """
    Creates a new order on the exchange.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ORDERS}"


def current_bars_WS(security_id: str = CRYPTO_PAIRS[0], periodicity: str = str(HeliumExPeriodicity.MINUTE_15)) -> str:
    """
    Gets an array of recent price data that can be used to populate a price chart.
    """
    return f"{HELIUMEX_WS_ENDPOINT_CURRENT_BARS}/{security_id}/{periodicity}"

# TODO: historical bars


def historical_bars_WS() -> str:
    """
    """
    return f"{HELIUMEX_WS_ENDPOINT_HISTORICAL_BARS}"


def order_book_API(security_id: str) -> str:
    """
    Gets a description of the complete order book for a particular instrument from the REST API.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ORDER_BOOK_SNAPSHOT}/{security_id}"


def order_book_WS(security_id: str = CRYPTO_PAIRS[0]) -> str:
    """
    Gets a description of the complete order book for a particular instrument.
    This endpoint subscribes to changes and will process both snapshots and diff messages.
    """
    return f"{HELIUMEX_WS_ENDPOINT_ORDER_BOOK}-{security_id}"


def order_events_API(start_time: int) -> str:
    """
    Gets a history of order events for the currencly authenticated user.
    This is the SEND equivalent of `orders_WS`
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ORDERS_EVENTS}?startTime={start_time}"


def order_events_send_WS() -> str:
    """
    Gets a history of order events for the currencly authenticated user.
    This is the SEND equivalent of `orders_WS`
    """
    return f"{HELIUMEX_WS_ENDPOINT_ORDER_EVENTS_SEND}"


def orders_API() -> str:
    """
    Gets the active orders for the authenticated user.
    """
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_ORDERS}"


def orders_WS() -> str:
    """
    Gets the active orders for the authenticated user
    This is the SUBSCRIBE equivalent of `order_events_send_WS`
    """
    return f"{HELIUMEX_WS_ENDPOINT_ORDERS}"


def quotes_WS(security_id: str = CRYPTO_PAIRS[0]) -> str:
    return f"{HELIUMEX_WS_ENDPOINT_QUOTES}-{security_id}"


def socket_send_responses() -> str:
    """
    use this SUBSCRIBE to listen to responses for SEND requests
    """
    return f"{HELIUMEX_WS_ENDPOINT_USER_RESPONSES}"


def socket_receive_responses() -> str:
    """
    When listening via `socket_send_responses` the destination returned strips the topic
    so you have to use this for disambiguation
    """
    return f"{HELIUMEX_WS_ENDPOINT_RESPONSES_LISTEN_DESTINATION}"


def settings_global_WS() -> str:
    return f"{HELIUMEX_WS_ENDPOINT_GLOBAL_SETTINGS}"


def settings_user_WS() -> str:
    """
    Returns things like wether or not 2FA is enabled for the account
    """
    return f"{HELIUMEX_WS_ENDPOINT_USER_SETTINGS}"


def trades_WS(security_id: str = CRYPTO_PAIRS[0]) -> str:
    return f"{HELIUMEX_WS_ENDPOINT_TRADES}/{security_id}"


def transactions_complete_API(self) -> str:
    return f"{HELIUMEX_REST_URL}{HELIUMEX_API_ENDPOINT_TRANSACTIONS_COMPLETE}"
