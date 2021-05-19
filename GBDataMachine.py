#!/usr/bin/env python
##
## GBDataMachine.py
##

__author__      = "Kevin Pruvost"
__copyright__   = "Copyright 2021, GreedyBoy"
__credits__     = ["Kevin Pruvost", "Hugo Mathieu-Steinbach"]
__license__     = "Proprietary"
__version__     = "1.0.0"
__maintainer__  = "Kevin Pruvost"
__email__       = "pruvostkevin0@gmail.com"
__status__      = "Test"

import pandas.core.generic as gen
import copy
import pandas as pd

class GBDataMachine:
    @classmethod
    def fromFilename(cls, fileName: str, interval: int = 15, movingAverageSize: int = 30):
        """Constructor starting from a filename.

        :param fileName: Name of the file containing the data.
        :type fileName: str
        :param interval: Time gap between each price (in min).
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average.
        :type movingAverageSize: int
        """
        csvData = pd.read_csv(fileName, parse_dates=True)
        return cls(csvData, interval, movingAverageSize)

    @classmethod
    def fromDataframe(cls, data: gen.NDFrame, interval: int = 15, movingAverageSize: int = 30):
        """Constructor starting from a filename.

        :param data: Structure containing prices and dates.
        :type data: gen.NDFrame
        :param interval: Time gap between each price (in min).
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average.
        :type movingAverageSize: int
        """
        return cls(data, interval, movingAverageSize)

    def __init__(self, data: gen.NDFrame = None, interval: int = 15, movingAverageSize: int = 30):
        """Constructs GBDataMachine with the given data formatted like a csv [epochTime, price].

        :param data: Structure containing prices and dates.
        :type data: gen.NDFrame
        :param interval: Time gap between each price (in min).
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average.
        :type movingAverageSize: int
        """
        self.interval = interval
        self.movingAverageSize = movingAverageSize
        self.roundTemp = {
            'Date': 0,
            'Open': 0,
            'High': 0,
            'Low': 0,
            'Close': 0,
            'MA': 0,
            'Std': 0,
            'LBand': 0,
            'HBand': 0
        }
        self.bGapRoundTemp = {
            'Date': 0,
            'Value': 0
        }
        self.newRound = copy.deepcopy(self.roundTemp)
        self.newGapRound = copy.deepcopy(self.bGapRoundTemp)
        self.bollingerGaps = pd.DataFrame()
        if data:
            if 'Low' not in data:
                self.ordered = pd.DataFrame()
                self.parseToInterval(data)
            else:
                self.ordered = data
        else:
            self.ordered = pd.DataFrame()
        return

    def parseToInterval(self, data):
        for i, row in data.iterrows():
            self.__append(row['epoch'], row['price'])
        self.update()

    def __append(self, epochTime: float, price: float):
        if self.newRound['Date'] != 0 and epochTime >= self.newRound['Date'] + 60 * self.interval:
            if len(self.ordered) == 0 or self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']:
                self.ordered = self.ordered.append(self.newRound, ignore_index=True)
            self.newRound = copy.deepcopy(self.roundTemp)
        self.newRound['Close'] = price
        if self.newRound['Date'] == 0:
            self.newRound['Date'] = epochTime - (epochTime % (self.interval * 60))
            self.newRound['Open'] = self.newRound['High'] = self.newRound['Low'] = price
        if self.newRound['Low'] > price:
            self.newRound['Low'] = price
        elif self.newRound['High'] < price:
            self.newRound['High'] = price

    def appendFormated(self, date: float, open: float, high: float, low: float, close: float):
        self.ordered = self.ordered.append({
            'Date': date,
            'Open': float(open),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
            'MA': 0,
            'Std': 0,
            'LBand': 0,
            'HBand': 0
        }, ignore_index=True)

    def appendDataframe(self, dataFrame: pd.DataFrame):
        for i, row in dataFrame.iterrows():
            self.__append(row['epoch'], row['price'])
        self.update()

    def append(self, epochTime: float, price: float, shouldPrint: bool = False):
        """Appends new (epochTime, price) into the Dataframes.

        :param epochTime: timestamp of the price
        :type epochTime: float
        :param price: price
        :type price: float
        """
        if type(epochTime) != float: epochTime = float(epochTime)
        if type(price) != float: price = float(price)
        self.__append(epochTime, price)
        self.update(shouldPrint)

    def update(self, shouldPrint: bool = False):
        """Updates the GBDataMachine and computes bollinger bands, moving averages, ..."""
        if self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']:
            self.ordered = self.ordered.append(self.newRound, ignore_index=True)
        else:
            self.ordered.at[len(self.ordered) - 1, 'High'] = self.newRound['High']
            self.ordered.at[len(self.ordered) - 1, 'Low'] = self.newRound['Low']
            self.ordered.at[len(self.ordered) - 1, 'Close'] = self.newRound['Close']
            self.ordered.at[len(self.ordered) - 1, 'Open'] = self.newRound['Open']
        self.ordered['MA'] = self.ordered['Close'].rolling(window=self.movingAverageSize).mean()
        self.ordered['Std'] = self.ordered['Close'].rolling(window=self.movingAverageSize).std()
        self.ordered['HBand'] = self.ordered['MA'] + (self.ordered['Std'] * 2)
        self.ordered['LBand'] = self.ordered['MA'] - (self.ordered['Std'] * 2)
        self.bollingerGaps = pd.DataFrame()
        self.bollingerGaps['Date'] = self.ordered['Date']
        self.bollingerGaps['Value'] = round(
            (self.ordered['Close'] - self.ordered['LBand']) / (self.ordered['HBand'] - self.ordered['LBand']) * 100
        , 2)
        if shouldPrint:
            print(self.ordered.iloc[[-1]])

    def convertForGraphicViews(self):
        """Convert data and format it for :ref:`GraphViewer<GraphViewer>`.

        :returns: (DataFrame containing data for Plot 1, Same for Plot 2)
        :rtype: (pandas.DataFrame, pandas.DataFrame)
        """
        data1, data2 = copy.deepcopy(self.ordered), copy.deepcopy(self.bollingerGaps)
        data1, data2 = data1.iloc[self.movingAverageSize:], data2.iloc[self.movingAverageSize:]
        data1["Date"], data2["Date"] = pd.to_datetime(data1["Date"], unit='s'), pd.to_datetime(data2["Date"], unit='s')
        data1, data2 = data1.set_index('Date'), data2.set_index('Date')
        return data1, data2

    def memoryUsage(self):
        return self.ordered.memory_usage(deep=True).sum() + self.bollingerGaps.memory_usage(deep=True).sum()

    def printPrices(self):
        print(self.ordered.to_csv(index=False))

    def currentBollingerValue(self):
        return self.bollingerGaps.iloc[[-1]].iloc[0]['Value']