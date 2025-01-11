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
import time
import warnings
from typing import Union

from GBConstants import GBConstants
from GBUtilities import GBUtilities

class GBDataMachine:
    @property
    def ordered(self) -> Union[pd.DataFrame, gen.NDFrame]:
        """Returns the ordered data"""
        return self._ordered
    
    @ordered.setter
    def ordered(self, value: Union[pd.DataFrame, gen.NDFrame]):
        """Sets the ordered data"""
        self._ordered = value

    @property
    def bollingerGaps(self) -> Union[pd.DataFrame, gen.NDFrame]:
        """Returns the bollinger gaps data"""
        return self._bollingerGaps
    
    @bollingerGaps.setter
    def bollingerGaps(self, value: Union[pd.DataFrame, gen.NDFrame]):
        """Sets the bollinger gaps data"""
        self._bollingerGaps = value

    @classmethod
    def fromFilename(cls, fileName: str, interval: int = 15, movingAverageSize: int = 30):
        """Constructor starting from a filename.

        :param fileName: Name of the file containing the data.
        :type fileName: str
        :param interval: Time gap between each price (in min). (default is 15)
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average. (default is 30)
        :type movingAverageSize: int
        """
        csvData = pd.read_csv(fileName, parse_dates=True)
        return cls(csvData, interval, movingAverageSize)

    @classmethod
    def fromDataframe(cls, data: gen.NDFrame, interval: int = 15, movingAverageSize: int = 30):
        """Constructor starting from a filename.

        :param data: Structure containing prices and dates.
        :type data: gen.NDFrame
        :param interval: Time gap between each price (in min). (default is 15)
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average. (default is 30)
        :type movingAverageSize: int
        """
        return cls(data, interval, movingAverageSize)

    def __init__(self, data: gen.NDFrame = None, interval: int = 15, movingAverageSize: int = 30):
        """Constructs GBDataMachine with the given data formatted like a csv [epochTime, price].

        :param data: Structure containing prices and dates.
        :type data: gen.NDFrame
        :param interval: Time gap between each price (in min). (default is 15)
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average. (default is 30)
        :type movingAverageSize: int
        """
        self.interval = interval
        self.movingAverageSize = movingAverageSize
        self.intervalJustClosed = False
        self.roundTemp = {
            'Date': 0,
            'Open': 0,
            'High': 0,
            'Low': 0,
            'Close': 0,
            'MA': 0,
            'Std': 0,
            'LBand': 0,
            'HBand': 0,
            'EMA5': 0,
            'EMA10': 0,
            'EMA20': 0,
            'EMA40': 0,
            'EMA50': 0,
            'EMA100': 0,
            'EMA200': 0
        }
        self.bGapRoundTemp = {
            'Date': 0,
            'Value': 0
        }
        self.newRound = pd.DataFrame(self.roundTemp, index=[0])
        self.newGapRound = pd.DataFrame(self.bGapRoundTemp, index=[0])
        self._bollingerGaps = pd.DataFrame()
        if data is not None:
            if 'Low' not in data:
                self._ordered = pd.DataFrame()
                self.parseToInterval(data)
            else:
                self._ordered = data
        else:
            self._ordered = pd.DataFrame()
        return

    def parseToInterval(self, data: pd.DataFrame):
        """Parses the given dataframe to the data machine

        :param data: dataframe containing the dates and prices
        :type data: pandas.DataFrame
        """
        for i, row in data.iterrows():
            self.__append(row['epoch'], row['price'])
        self.update()

    def __append(self, epochTime: float, price: float):
        if not self.newRound['Date'].isnull().all() and (epochTime >= self.newRound['Date'] + 60 * self.interval).max():
            if (
                len(self.ordered) == 0 or
                ('Date' not in self.ordered.columns) or 
                (len(self.ordered) > 0 and (self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']).all())
            ):
                self.ordered = pd.concat([self.ordered, self.newRound], ignore_index=True)
                self.intervalJustClosed = True
            self.newRound = pd.DataFrame(self.roundTemp, index=[0])
        self.newRound['Close'] = price
        if (self.newRound['Date'] == 0).all():
            self.newRound['Date'] = epochTime - (epochTime % (self.interval * 60))
            self.newRound['Open'] = self.newRound['High'] = self.newRound['Low'] = price
        if (self.newRound['Low'] > price).all():
            self.newRound['Low'] = price
        elif (self.newRound['High'] < price).all():
            self.newRound['High'] = price

    def appendFormated(self, date: float, open: float, high: float, low: float, close: float):
        """Appends an already formated row to the data machine

        :param date: epoch time in seconds
        :type date: float
        :param open: open price
        :type open: float
        :param high: high price
        :type high: float
        :param low: low price
        :type low: float
        :param close: close price
        :type close: float
        """
        self.ordered = pd.concat([self.ordered, pd.DataFrame({
            'Date': date,
            'Open': float(open),
            'High': float(high),
            'Low': float(low),
            'Close': float(close),
            'MA': 0,
            'Std': 0,
            'LBand': 0,
            'HBand': 0
        }, index=[0])], ignore_index=True)

    def appendFilename(self, fileName: str):
        """Appends a file into the data machine.

        :param fileName: name of the file
        :type fileName: str
        """
        csvData = pd.read_csv(fileName, parse_dates=True)
        return self.appendDataframe(csvData)

    def appendDataframe(self, dataFrame: pd.DataFrame):
        """Same as parseToInterval but with a different name"""
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
        epochTime = float(epochTime)
        price = float(price)
        self.__append(epochTime, price)
        self.update(shouldPrint)

    def update(self, shouldPrint: bool = False):
        """Updates the GBDataMachine and computes bollinger bands, moving averages, ...

        :param shouldPrint: specify if the updates operations should be displayed or not
        :type shouldPrint: bool
        """

        warnings.filterwarnings("always", category=FutureWarning)

        # if (self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']).all():
        #     self.ordered = pd.concat([self.ordered, self.newRound], ignore_index=True)
        #     self.intervalJustClosed = True
        # else:
        #     self.ordered.at[len(self.ordered) - 1, 'High'] = self.newRound['High'].iloc[0]
        #     self.ordered.at[len(self.ordered) - 1, 'Low'] = self.newRound['Low'].iloc[0]
        #     self.ordered.at[len(self.ordered) - 1, 'Close'] = self.newRound['Close'].iloc[0]
        #     self.ordered.at[len(self.ordered) - 1, 'Open'] = self.newRound['Open'].iloc[0]

        if all(col in self.ordered.columns for col in ['Date', 'High', 'Low', 'Close', 'Open']):
            # Flatten `self.newRound` if it's multi-dimensional
            new_row = GBUtilities.ensureCorrectFormat(self.newRound, True, 'self.newRound')
        
            if self.ordered.empty or self.ordered.iloc[-1]['Date'] != new_row['Date']:
                # Ensure `self.newRound` is in the correct format for concatenation
                new_row_df = GBUtilities.createNewDataFrameRow(new_row, 'self.newRound')

                # Append the new row to `self.ordered`
                if self.ordered.empty:
                    self.ordered = new_row_df
                else:
                    self.ordered = pd.concat([self.ordered, new_row_df], ignore_index=True)
                self.intervalJustClosed = True
            else:
                # Update the last row with new values
                last_index = self.ordered.index[-1]
                self.ordered.loc[last_index, ['High', 'Low', 'Close', 'Open']] = (
                    new_row['High'], new_row['Low'], new_row['Close'], new_row['Open']
                )

            # Calculate Moving Averages and Bollinger Bands
            if (
                len(self.ordered) >= self.movingAverageSize and 
                all(col in self.ordered.columns for col in ['MA', 'Std'])
            ):
                self.ordered['MA'] = self.ordered['Close'].rolling(window=self.movingAverageSize).mean()
                self.ordered['Std'] = self.ordered['Close'].rolling(window=self.movingAverageSize).std()
                self.ordered['HBand'] = self.ordered['MA'] + (self.ordered['Std'] * 2)
                self.ordered['LBand'] = self.ordered['MA'] - (self.ordered['Std'] * 2)
            else:
                self.ordered['MA'] = None
                self.ordered['Std'] = None
                self.ordered['HBand'] = None
                self.ordered['LBand'] = None

            # Calculate Exponential Moving Averages (EMA)
            emaValues = GBConstants.getEMAValues()
            for emaValue in emaValues:
                self.ordered['EMA{0}'.format(emaValue)] = self.ordered['Close'].ewm(span=emaValue).mean()
            # self.ordered['EMA5'] = self.ordered['Close'].ewm(span=5).mean()
            # self.ordered['EMA10'] = self.ordered['Close'].ewm(span=10).mean()
            # self.ordered['EMA20'] = self.ordered['Close'].ewm(span=20).mean()
            # self.ordered['EMA50'] = self.ordered['Close'].ewm(span=50).mean()
            # self.ordered['EMA40'] = self.ordered['Close'].ewm(span=40).mean()
            # self.ordered['EMA100'] = self.ordered['Close'].ewm(span=100).mean()
            # self.ordered['EMA200'] = self.ordered['Close'].ewm(span=200).mean()

            # Calculate Bollinger Gaps
            if all(col in self.ordered.columns for col in ['HBand', 'LBand']):
                self.bollingerGaps = pd.DataFrame()
                self.bollingerGaps['Date'] = self.ordered['Date']
                self.bollingerGaps['Value'] = round(
                    (self.ordered['Close'] - self.ordered['LBand']) / 
                    (self.ordered['HBand'] - self.ordered['LBand']) * 100, 2
                )
            else:
                self.bollingerGaps = pd.DataFrame()

            # Print the last row if it exists
            if not self.ordered.empty and shouldPrint:
                last = self.ordered.iloc[-1]
                print(last)
        else:
            print("DataFrame is empty or missing required 'Close' column.")
        # self.ordered['MA'] = self.ordered['Close'].rolling(window=self.movingAverageSize).mean()
        # self.ordered['EMA20'] = self.ordered['Close'].ewm(span=20).mean()
        # self.ordered['EMA50'] = self.ordered['Close'].ewm(span=50).mean()
        # self.ordered['EMA40'] = self.ordered['Close'].ewm(span=40).mean()
        # self.ordered['EMA5'] = self.ordered['Close'].ewm(span=5).mean()
        # self.ordered['Std'] = self.ordered['Close'].rolling(window=self.movingAverageSize).std()
        # self.ordered['HBand'] = self.ordered['MA'] + (self.ordered['Std'] * 2)
        # self.ordered['LBand'] = self.ordered['MA'] - (self.ordered['Std'] * 2)
        # self.bollingerGaps = pd.DataFrame()
        # self.bollingerGaps['Date'] = self.ordered['Date']
        # self.bollingerGaps['Value'] = round(
        #     (self.ordered['Close'] - self.ordered['LBand']) / (self.ordered['HBand'] - self.ordered['LBand']) * 100
        # , 2)
        # last = self.ordered.iloc[-1]
        # if shouldPrint:
        #     print(self.ordered.iloc[[-1]])

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
        """Returns memory usage

        :returns: memory usage
        :rtype: int
        """
        return self.ordered.memory_usage(deep=True).sum() + self.bollingerGaps.memory_usage(deep=True).sum()

    def printPrices(self):
        """Prints prices data"""
        print(self.ordered.to_csv(index=False))

    def currentBollingerValue(self):
        """Prints the current/last bollinger value"""
        return self.bollingerGaps.iloc[[-1]].iloc[0]['Value']

    def lastPrice(self):
        """Returns the last close price"""
        return self.ordered.iloc[-1]["Close"] if len(self.ordered.index) != 0 else None

    def intervalClosed(self) -> bool:
        """Returns if an iteration has just been closed"""
        ret = self.intervalJustClosed
        self.intervalJustClosed = False
        return ret