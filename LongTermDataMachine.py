#!/usr/bin/env python
##
## LongTermDataMachine.py
##

__author__      = "Kevin Pruvost"
__copyright__   = "Copyright 2021, GreedyBoy"
__credits__     = ["Kevin Pruvost"]
__license__     = "Proprietary"
__version__     = "1.0.0"
__maintainer__  = "Kevin Pruvost"
__email__       = "pruvostkevin0@gmail.com"
__status__      = "Test"

import math

import pandas.core.generic as gen
import copy
import pandas as pd
import numpy as np

class LongTermDataMachine:
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

    def __init__(self, data: gen.NDFrame = None, interval: int = 1440, movingAverageSize: int = 30):
        """Constructs GBDataMachine with the given data formatted like a csv [epochTime, price].

        :param data: Structure containing prices and dates.
        :type data: gen.NDFrame
        :param interval: Time gap between each price (in min) (default is 1440, 1 day).
        :type interval: int
        :param movingAverageSize: Number of data taken into account to calculate a moving average. (default is 30)
        :type movingAverageSize: int
        """
        self.movingAverageSize = movingAverageSize
        self.interval = interval
        self.intervalJustClosed = False
        self.roundTemp = {
            'Date': 0,
            'Open': 0,
            'High': 0,
            'Low': 0,
            'Close': 0,
            'SMMA5': None,
            'SMMA40': None
        }
        self.newRound = pd.DataFrame(self.roundTemp, index=[0])
        if data is not None:
            if 'Low' not in data:
                self.ordered = pd.DataFrame()
                self.parseToInterval(data)
            else:
                self.ordered = data
        else:
            self.ordered = pd.DataFrame()
        return
    
    def parseToInterval(self, data: pd.DataFrame):
        """
        Parse data and append rows to the internal structure, then update the state.

        Args:
            data (pd.DataFrame): The data to parse, containing 'epoch' and 'price' columns.

        Returns:
            None
        """
        # Validate input data
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Error: The input `data` must be a pandas DataFrame.")
        
        # Check for required columns
        required_columns = {'epoch', 'price'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Error: DataFrame must contain the required columns: {required_columns}")

        # Process each row in the DataFrame
        for i, row in data.iterrows():
            # Ensure valid data in each row
            try:
                epoch_time = float(row['epoch'])
                price = float(row['price'])
                self._append(epoch_time, price)
            except (ValueError, TypeError) as e:
                print(f"Error processing row {i}: {e}")
                continue  # Skip invalid rows

        # Call the update method after processing
        self.update()

    # def parseToInterval(self, data: gen.NDFrame):
    #     for i, row in data.iterrows():
    #         self._append(row['epoch'], row['price'])
    #     self.update()

    def _append(self, epochTime: float, price: float):
        """
        Appends data to the internal structure based on the epoch time and price.

        Args:
            epochTime (float): The epoch time in seconds.
            price (float): The price value.

        Returns:
            None
        """
        # Validate inputs
        if not isinstance(epochTime, (float, int)) or epochTime <= 0:
            raise ValueError(f"Invalid `epochTime`: {epochTime}. Must be a positive number.")
        if not isinstance(price, (float, int)):
            raise ValueError(f"Invalid `price`: {price}. Must be a number.")

        # Ensure `self.newRound` is initialized properly
        if not hasattr(self, 'newRound') or self.newRound is None:
            raise AttributeError("`self.newRound` is not initialized.")
        if not hasattr(self, 'ordered'):
            raise AttributeError("`self.ordered` is not initialized.")
        if not hasattr(self, 'interval') or not isinstance(self.interval, (int, float)) or self.interval <= 0:
            raise ValueError("`self.interval` must be a positive number.")

        # Handle interval-based logic
        # Extract `Date` from `self.newRound` and ensure it's scalar
        if isinstance(self.newRound, dict):
            # Extract from a dictionary
            new_round_date = self.newRound.get('Date', 0)
        elif isinstance(self.newRound, pd.DataFrame):
            # Extract the first element from a DataFrame
            if 'Date' in self.newRound.columns and not self.newRound.empty:
                new_round_date = self.newRound.iloc[0]['Date']
            else:
                new_round_date = 0
        else:
            raise ValueError("Unsupported type for `self.newRound`.")

        # Ensure `new_round_date` is scalar
        if isinstance(new_round_date, pd.Series):
            new_round_date = new_round_date.iloc[0]

        # Perform the comparison safely
        if new_round_date != 0 and epochTime >= new_round_date + 60 * self.interval:
            # Ensure the last row of `self.ordered` has a scalar `Date`
            last_date = self.ordered.iloc[-1]['Date'] if not self.ordered.empty else None
            if last_date is None or last_date != new_round_date:
                # Append `self.newRound` to `self.ordered`
                try:
                    # Ensure `self.newRound` is in the correct format for concatenation
                    if isinstance(self.newRound, pd.DataFrame):
                        # If it's already a DataFrame, use the first row
                        new_row = self.newRound.iloc[0].to_dict()
                    elif isinstance(self.newRound, pd.Series):
                        # If it's a Series, convert it to a dictionary
                        new_row = self.newRound.to_dict()
                    elif isinstance(self.newRound, dict):
                        # If it's a dictionary, use it directly
                        new_row = self.newRound
                    else:
                        raise ValueError("`self.newRound` must be a dict, Series, or DataFrame.")

                    # Create a new DataFrame row and append it to `self.ordered`
                    self.ordered = pd.concat([self.ordered, pd.DataFrame([new_row])], ignore_index=True)
                    self.intervalJustClosed = True
                except Exception as e:
                    print(f"Error appending to `self.ordered`: {e}")
                    return

            # Reset `self.newRound` using `self.roundTemp`
            if hasattr(self, 'roundTemp') and isinstance(self.roundTemp, dict):
                self.newRound = self.roundTemp.copy()
            else:
                raise AttributeError("`self.roundTemp` is not properly initialized.")

        # Update `self.newRound` with the new price
        self.newRound['Close'] = price
        # Safely extract the 'Date' value from `self.newRound`
        new_round_date2 = self.newRound.get('Date', 0)

        # If `self.newRound` is a DataFrame or Series, ensure we extract the scalar
        if isinstance(new_round_date2, pd.Series) or isinstance(new_round_date2, pd.DataFrame):
            new_round_date2 = new_round_date2.iloc[0] if not new_round_date2.empty else 0

        # Perform the comparison with the scalar value
        if new_round_date2 == 0:
            self.newRound['Date'] = epochTime - (epochTime % (self.interval * 60))
            self.newRound['Open'] = self.newRound['High'] = self.newRound['Low'] = price

        # Update High and Low prices
        low = self.newRound['Low']
        high = self.newRound['High']

        # Handle cases where `low` or `high` are pandas Series
        if isinstance(low, pd.Series):
            low = low.iloc[0]
        if isinstance(high, pd.Series):
            high = high.iloc[0]

        # Perform comparisons with scalar values
        if low > price:
            self.newRound['Low'] = price
        elif high < price:
            self.newRound['High'] = price

    # def _append(self, epochTime: float, price: float):
    #     if self.newRound['Date'] != 0 and epochTime >= self.newRound['Date'] + 60 * self.interval:
    #         if len(self.ordered) == 0 or self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']:
    #             self.ordered = pd.concat([self.ordered, self.newRound], ignore_index=True)
    #             self.intervalJustClosed = True
    #         self.newRound = pd.DataFrame(self.roundTemp, index=[0])
    #     self.newRound['Close'] = price
    #     if self.newRound['Date'] == 0:
    #         self.newRound['Date'] = epochTime - (epochTime % (self.interval * 60))
    #         self.newRound['Open'] = self.newRound['High'] = self.newRound['Low'] = price
    #     if self.newRound['Low'] > price:
    #         self.newRound['Low'] = price
    #     elif self.newRound['High'] < price:
    #         self.newRound['High'] = price

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
            'SMMA5': None,
            'SMMA40': None
        }, index=[0])], ignore_index=True)

    def appendFilename(self, fileName):
        """Appends a file into the data machine.

        :param fileName: name of the file
        :type fileName: str
        """
        csvData = pd.read_csv(fileName, parse_dates=True)
        return self.appendDataframe(csvData)

    def appendDataframe(self, dataFrame: pd.DataFrame):
        """Same as parseToInterval but with a different name"""
        for i, row in dataFrame.iterrows():
            self._append(row['epoch'], row['price'])
        self.update()

    def appendFormatedDataframe(self, dataFrame: pd.DataFrame):
        for i, row in dataFrame.iterrows():
            self.appendFormated(row['Date'], row['Open'], row['High'], row['Low'], row['Close'])
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
        self._append(epochTime, price)
        self.update(shouldPrint)

    def update(self, shouldPrint: bool = False):
        """Updates the GBDataMachine and computes bollinger bands, moving averages, etc."""
        required_columns = ['Date', 'High', 'Low', 'Close', 'Open']
        
        # Ensure required columns exist in `self.ordered`
        if not all(col in self.ordered.columns for col in required_columns):
            print("Error: Required columns are missing in `self.ordered`.")
            return

        # Flatten `self.newRound` if it's multi-dimensional
        if isinstance(self.newRound, pd.DataFrame):
            if self.newRound.shape[0] == 1:  # Single row DataFrame
                new_row = self.newRound.iloc[0].to_dict()
            else:
                print("Error: `self.newRound` contains multiple rows.")
                return
        elif isinstance(self.newRound, dict):
            new_row = self.newRound
        else:
            print("Error: `self.newRound` must be a dictionary or a single-row DataFrame.")
            return

        # Check if `new_row` contains the required keys
        if not all(key in new_row for key in required_columns):
            print("Error: `self.newRound` is missing required keys.")
            return

        # Handle adding or updating rows
        if self.ordered.empty or self.ordered.iloc[-1]['Date'] != new_row['Date']:
            # Append the new row
            self.ordered = pd.concat([self.ordered, pd.DataFrame([new_row])], ignore_index=True)
            self.intervalJustClosed = True
        else:
            # Update the last row with new values
            last_index = self.ordered.index[-1]
            self.ordered.loc[last_index, ['High', 'Low', 'Close', 'Open']] = (
                new_row['High'], new_row['Low'], new_row['Close'], new_row['Open']
            )

        # Print the last row if required
        if shouldPrint and not self.ordered.empty:
            print(self.ordered.iloc[[-1]])

    # def update(self, shouldPrint: bool = False):
    #     """Updates the GBDataMachine and computes bollinger bands, moving averages, ..."""
    #     if all(col in self.ordered.columns for col in ['Date', 'High', 'Low', 'Close', 'Open']):
    #         if self.ordered.empty or self.ordered.iloc[-1]['Date'] != self.newRound['Date']:
    #             # Append the new row, ensuring it's in DataFrame format
    #             new_row = pd.DataFrame([self.newRound])
    #             self.ordered = pd.concat([self.ordered, new_row], ignore_index=True)
    #             self.intervalJustClosed = True
    #         else:
    #             # Update the last row with new values
    #             last_index = self.ordered.index[-1]
    #             self.ordered.at[last_index, 'High'] = self.newRound['High']
    #             self.ordered.at[last_index, 'Low'] = self.newRound['Low']
    #             self.ordered.at[last_index, 'Close'] = self.newRound['Close']
    #             self.ordered.at[last_index, 'Open'] = self.newRound['Open']
        # if self.newRound['Date'] != 0:
        #     if len(self.ordered.index) == 0 or self.ordered.at[len(self.ordered) - 1, 'Date'] != self.newRound['Date']:
        #         self.ordered = pd.concat([self.ordered, self.newRound], ignore_index=True)
        #         self.intervalJustClosed = True
        #     else:
        #         self.ordered.at[len(self.ordered) - 1, 'High'] = self.newRound['High']
        #         self.ordered.at[len(self.ordered) - 1, 'Low'] = self.newRound['Low']
        #         self.ordered.at[len(self.ordered) - 1, 'Close'] = self.newRound['Close']
        #         self.ordered.at[len(self.ordered) - 1, 'Open'] = self.newRound['Open']

        def calculate_sum(i: int, wSize: int):
            """Calculate the sum of 'Close' values over the given window size."""
            if i < wSize - 1:
                return 0  # Not enough data to calculate the sum
            return self.ordered.iloc[i - wSize + 1:i + 1]['Close'].sum()

        def smma(i: int, wSize: int):
            """
            Calculate the Smoothed Moving Average (SMMA) at index `i` with window size `wSize`.

            Args:
                i (int): The current index in the DataFrame.
                wSize (int): The window size for SMMA.

            Returns:
                float or None: The calculated SMMA value, or None if it cannot be calculated.
            """
            # Validate the window size
            if wSize <= 0:
                print("Error: Window size (wSize) must be a positive integer.")
                return None
            
            # Ensure there is enough data to calculate SMMA
            if i < wSize - 1:
                return None  # Not enough data to calculate SMMA

            if i == wSize - 1:
                # Initial SMMA calculation as the simple average
                sum_close = calculate_sum(i, wSize)
                if wSize == 0 or sum_close is None:  # Avoid division by zero
                    return None
                return np.round(sum_close / wSize, decimals=10)
            
            # Retrieve the previous SMMA value safely
            prev_smma = self.ordered.iloc[i - 1].get(f'SMMA{wSize}', 0)
            close_price = self.ordered.iloc[i]['Close']
            
            if prev_smma is None or close_price is None:  # Ensure valid numeric inputs
                return None
            
            # Calculate the SMMA and ensure no division by zero
            denominator = wSize + 1
            if denominator == 0:
                print("Error: Division by zero in SMMA calculation.")
                return None
            
            return np.round((prev_smma * wSize + close_price) / denominator, decimals=10)

        # Ensure there is enough data to calculate SMMA5
        if len(self.ordered) >= 5:
            new_smma5 = smma(len(self.ordered) - 1, 5)
            self.ordered.loc[self.ordered.index[-1], 'SMMA5'] = new_smma5

        # Ensure there is enough data to calculate SMMA40
        if len(self.ordered) >= 40:
            new_smma40 = smma(len(self.ordered) - 1, 40)
            self.ordered.loc[self.ordered.index[-1], 'SMMA40'] = new_smma40

        # def sum(i: int, wSize: int):
        #     s = 0
        #     for j in range(0, wSize): s += self.ordered.iloc[i - j]['Close']
        #     return s

        # def smma(i: int, wSize: int):
        #     if i == wSize:
        #         return np.round(sum(i, wSize) / wSize, decimals=10)
        #     return np.round((self.ordered.iloc[i - 1]['SMMA' + str(wSize + 1)] or 0 * wSize + self.ordered.iloc[i]['Close']) / (wSize + 1), decimals=10)

        # size = len(self.ordered.index)
        # if size < 5: return
        # newSm = smma(size - 1, 5 - 1)
        # self.ordered.loc[self.ordered.index[-1], 'SMMA5'] = newSm

        # if size < 40: return
        # newSm = smma(size - 1, 40 - 1)
        # self.ordered.loc[self.ordered.index[-1], 'SMMA40'] = newSm

        if shouldPrint:
            last = self.ordered.iloc[-1]
            print(last)

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
        return self.ordered.memory_usage(deep=True).sum()

    def printPrices(self):
        print(self.ordered.to_csv(index=False))

    def currentBollingerValue(self):
        return self.bollingerGaps.iloc[[-1]].iloc[0]['Value']

    def lastPrice(self):
        return self.ordered.iloc[-1]["Close"] if len(self.ordered.index) != 0 else None

    def intervalClosed(self):
        ret = self.intervalJustClosed
        self.intervalJustClosed = False
        return ret

import KrakenApi

def main():
    dataMachine = LongTermDataMachine()
    api = KrakenApi.KrakenApi("jN1hIQ7abFkjmn/ffco27/E2PC7/OfLatbX87vG5wa6vDlZP0GQTsoDa",
                    "Stha4yXDkHon3dnBBW8+nl7G+YVZvWC88OlltVKh5FhKuYJ0Z5sTgO9qe6a7bZKXfrapKMLgkNbJYuffnzvgtw==",
                    "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")
    prices = api.GetPrices("XDG", 1440, 1546214400)
    for priceBar in prices:
        dataMachine.appendFormated(priceBar[0], priceBar[1], priceBar[2], priceBar[3], priceBar[4])
    dataMachine.update()
    print(dataMachine.ordered.tail(50))

if __name__ == '__main__':
    main()