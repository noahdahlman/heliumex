#!/usr/bin/env python

import asyncio
import logging
from typing import (
    Optional,
    List,
)
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.logger import HummingbotLogger
from hummingbot.core.data_type.user_stream_tracker import (
    UserStreamTrackerDataSourceType,
    UserStreamTracker
)
from hummingbot.core.utils.async_utils import (
    safe_ensure_future,
    safe_gather,
)

from hummingbot.market.heliumex.heliumex_auth import HeliumExAuth
from hummingbot.market.heliumex.heliumex_api_user_stream_data_source import HeliumExAPIUserStreamDataSource

import hummingbot.market.heliumex.heliumex_constants as CONSTANTS


class HeliumExUserStreamTracker(UserStreamTracker):
    _heliumex_ust_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._heliumex_ust_logger is None:
            cls._heliumex_ust_logger = logging.getLogger(__name__)
        return cls._heliumex_ust_logger

    def __init__(self,
                 data_source_type: UserStreamTrackerDataSourceType = UserStreamTrackerDataSourceType.EXCHANGE_API,
                 heliumex_auth: Optional[HeliumExAuth] = None,
                 trading_pairs: Optional[List[str]] = []):
        super().__init__(data_source_type=data_source_type)
        self._heliumex_auth: HeliumExAuth = heliumex_auth
        self._trading_pairs: List[str] = trading_pairs
        self._ev_loop: asyncio.events.AbstractEventLoop = asyncio.get_event_loop()
        self._data_source: Optional[UserStreamTrackerDataSource] = None
        self._user_stream_tracking_task: Optional[asyncio.Task] = None

    @property
    def data_source(self) -> UserStreamTrackerDataSource:
        """
        *required
        Initializes a user stream data source (user specific order diffs from live socket stream)
        :return: OrderBookTrackerDataSource
        """
        if not self._data_source:
            if self._data_source_type is UserStreamTrackerDataSourceType.EXCHANGE_API:
                self._data_source = HeliumExAPIUserStreamDataSource(
                    heliumex_auth=self._heliumex_auth,
                    trading_pairs=self._trading_pairs
                )
            else:
                raise ValueError(f"data_source_type {self._data_source_type} is not supported.")
        return self._data_source

    @property
    def exchange_name(self) -> str:
        """
        *required
        Name of the current exchange
        """
        return CONSTANTS.HELIUMEX_EXCHANGE_NAME

    async def start(self):
        """
        *required
        Start all listeners and tasks
        """
        self._user_stream_tracking_task = safe_ensure_future(
            self.data_source.listen_for_user_stream(self._ev_loop, self._user_stream)
        )
        await safe_gather(self._user_stream_tracking_task)
