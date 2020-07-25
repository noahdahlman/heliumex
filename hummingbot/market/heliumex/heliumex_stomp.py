
import copy
import time
from typing import Dict, Optional


class StompFrame(object):

    cmd: str
    headers: Dict[str, str]
    body: str

    @classmethod
    def unpack(cls, message: str) -> Dict[str, any]:
        body = []
        returned = dict(cmd='', headers={}, body='')

        breakdown = message.split('\n')

        # Get the message command:
        returned['cmd'] = breakdown[0]
        breakdown = breakdown[1:]

        def headD(field):
            # find the first ':' everything to the left of this is a
            # header, everything to the right is data:
            index = field.find(':')
            if index:
                header = field[:index].strip()
                data = field[index + 1:].strip()
                # print "header '%s' data '%s'" % (header, data)
                returned['headers'][header.strip()] = data.strip()

        def bodyD(field):
            field = field.strip()
            if field:
                body.append(field)

        # Recover the header fields and body data
        handler = headD
        for field in breakdown:
            # print "field:", field
            if field.strip() == '':
                # End of headers, it body data next.
                handler = bodyD
                continue

            handler(field)

        # Stich the body data together:
        # print "1. body: ", body
        body = "".join(body)
        returned['body'] = body.replace('\x00', '')

        # print "2. body: <%s>" % returned['body']

        return returned

    def __init__(self, cmd, headers: Optional[Dict[str, str]] = None, body: str = None):
        self.cmd = cmd
        self.headers = headers if headers is not None else None
        self.original_headers = copy.copy(self.headers)
        self.body = body

    def __repr__(self):
        return f'StompFrame=(cmd:{self.cmd}, headers:{self.headers}, original:{self.original_headers}, body:{self.body}'

    def pack(self) -> str:
        bits = [self.cmd, '\n']
        if self.body:
            bits.extend(('content-length:', str(len(self.body)), '\n'))

        for key, value in self.headers.items():
            bits.extend((key.replace('_', '-'), ':', str(value), '\n',))
        bits.extend((
            '\n',
            self.body or '',
            '\x00'
        ))
        return ''.join(bits)


def unpack_frame(message: str) -> StompFrame:
    frame = StompFrame.unpack(message)
    return StompFrame(
        frame['cmd'],
        frame['headers'],
        frame['body']
    )


def connect(exchange_access_token) -> str:
    headers: Dict[str, str] = {}
    headers['accept_version'] = '1.0,1.1,1.2'
    headers['Authorization'] = exchange_access_token
    headers['heart-beat'] = '10000,10000'
    return StompFrame('CONNECT', headers).pack()


def disconnect() -> str:
    ticks = str(time.time_ns())
    headers: Dict[str, str] = {}
    headers['X-Deltix-Nonce'] = ticks
    headers['receipt'] = ticks
    return StompFrame('DISCONNECT', headers).pack()


def send(destination: str, correlation_id: Optional[str] = None, headers = {}, body: Optional[str] = None) -> str:
    headers['X-Deltix-Nonce'] = str(time.time_ns())
    headers['destination'] = destination
    if correlation_id is not None:
        headers['correlation-id'] = correlation_id
    return StompFrame('SEND', headers, body).pack()


def subscribe(subscription_id: str, destination: str) -> str:
    headers: Dict[str, str] = {}
    headers['X-Deltix-Nonce'] = str(time.time_ns())
    headers['id'] = subscription_id
    headers['destination'] = destination
    return StompFrame('SUBSCRIBE', headers).pack()


def unsubscribe(subscription_id: str) -> str:
    headers: Dict[str, str] = {}
    headers['X-Deltix-Nonce'] = str(time.time_ns())
    headers['id'] = subscription_id
    return StompFrame('UNSUBSCRIBE', headers).pack()
