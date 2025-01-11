from abc import ABC, abstractmethod
from typing import Union

import pandas as pd
import pandas.core.generic as gen

class IGreedyBoyDecisionMaker(ABC):
    # Properties
    @property
    @abstractmethod
    def buyOrSellPosition(self) -> Union[str, None]:
        """
        The buy or sell position of the bot.
        :return: The buy or sell position of the bot.
        """
        pass

    @buyOrSellPosition.setter
    @abstractmethod
    def buyOrSellPosition(self, value: str):
        """
        Sets the buy or sell position of the bot.
        :param value: The value to set ("buy" or "sell").
        """
        pass

    @property
    @abstractmethod
    def ordered(self) -> Union[pd.DataFrame, gen.NDFrame]:
        """
        The ordered data.
        :return: The ordered data.
        """
        pass

    @property
    @abstractmethod
    def bollingerGaps(self) -> Union[pd.DataFrame, gen.NDFrame]:
        """
        The bollinger gaps data.
        :return: The bollinger gaps data.
        """
        pass

    @abstractmethod
    def isIntervalClosed(self) -> bool:
        """
        Returns whether the data machine interval is closed.
        :return: Whether the data machine interval is closed.
        """
        pass

    @abstractmethod
    def AddOrderMax(self, orderType: str):
        """
        Adds an order to the system with the maximum amount possible.
        :param orderType: The order type ("buy" or "sell").
        """
        pass