import ujson


def subscribe(destination: str) -> str:
    return ujson.dumps({"type": "subscribe", "destination": destination})
