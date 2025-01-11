###
### GreedyBoyDecisionMaker class
###

import time
import tempfile
from typing import Any, Union
import pandas as pd
import pandas.core.generic as gen
import requests
import csv

#from pdoc import reset

from GBDataMachine import GBDataMachine
from GBUtilities import GBUtilities
from IGreedyBoyDecisionMaker_module import IGreedyBoyDecisionMaker
from KrakenApi import KrakenApi
from github import Github
from GBConstants import GBConstants
from TradingStrategies.EMACrossover import EMACrossover

class GreedyBoyDecisionMaker(IGreedyBoyDecisionMaker):
    # IGreedBoyDecisionMaker Implementation
    @property
    def buyOrSellPosition(self) -> Union[str, None]:
        return self._buyOrSellPosition
    
    @buyOrSellPosition.setter
    def buyOrSellPosition(self, value: str):
        assert value in ("buy", "sell"),\
            "buyOrSellPosition must be 'buy' or 'sell'"
        self._buyOrSellPosition = value

    @property
    def ordered(self) -> Union[pd.DataFrame, gen.NDFrame]:
        return self.dataMachine.ordered
    
    @property
    def bollingerGaps(self) -> Union[pd.DataFrame, gen.NDFrame]:
        return self.dataMachine.bollingerGaps

    def isIntervalClosed(self) -> bool:
        return self.dataMachine.intervalClosed()
    
    def AddOrderMax(self, buyOrSell: str):
        """
        Adds an order to the system with the maximum amount possible.
        :param buyOrSell: The type of order to add, which can be "buy" or "sell".
        """
        assert buyOrSell in ("buy", "sell"), "buyOrSell must be 'buy' or 'sell'"
        price = float(self.dataMachine.ordered.iloc[-1]["Close"])  # Gets Last price registered
        amount = self.fiatBalance / price if buyOrSell == "buy" else self.cryptoBalance
        self.AddOrder(buyOrSell, amount, price)

    # Private Methods

    def __writeRowToTemp(self, row):
        self.orderFile = open(self.ordersDataTempPath, "a")
        self.orderWriter = csv.DictWriter(self.orderFile, fieldnames=['Date', 'Price', 'Amount', 'Order'], lineterminator="\n")
        self.orderWriter.writerow(row)
        self.orderFile.close()

    def __readLastOrders(self):
        try:
            empty = True
            self.orders = None
            self.orderWriter = None
            githubFile = self.greedyBoyRepo.get_contents(self.ordersGithubPath, self.branchName)
            githubFileContent = githubFile.decoded_content.decode('ascii')
            empty = not csv.Sniffer().has_header(githubFileContent)
            if not empty:
                self.orderFile = open(self.ordersDataTempPath, "w")
                self.orderFile.write(githubFileContent)
                self.orderFile.close()
                self.dataMachine = GBDataMachine.fromFilename(self.ordersDataTempPath, interval=15)
        except:
            self.orderFile = open(self.ordersDataTempPath, "w")
            self.orderFile.write("")
            self.orderFile.close()
        self.orderFile = open(self.ordersDataTempPath, "a")
        self.orderWriter = csv.DictWriter(self.orderFile, fieldnames=['Date', 'Price', 'Amount', 'Order'], lineterminator="\n")
        if empty:
            self.orderWriter.writeheader()
        else: # Read Last Order
            orders = pd.read_csv(self.ordersDataTempPath, parse_dates=False)
            if len(orders.index) != 0:
                self.lastOrder = {
                    'Date': orders.iloc[-1]['Date'], 'Price': orders.iloc[-1]['Price'],
                    'Amount': orders.iloc[-1]['Amount'], 'Order': orders.iloc[-1]['Order']}

    def __setBuyOrSellPosition(self):
        price = self.dataMachine.lastPrice()  # Gets Last price registered
        if price:
            self.buyOrSellPosition = "buy" if self.fiatBalance > self.cryptoBalance * price else "sell"
        else:
            self.buyOrSellPosition = "buy" if self.fiatBalance >= 10 else "sell"

    def start(self):
        self.__readLastOrders()
        self.dataMachine = GBDataMachine(interval=15)

        ###################################
        # Getting data from the day before
        if not self.testTime:
            lastTime = time.time() - 86401
            resp = self.krakenApi.GetPrices(self.initial, 5, lastTime)
            if resp: # If request actually got useful information
                for result in resp:
                    self.dataMachine.appendFormated(result[0], result[1], result[2], result[3], result[4])
                lastTime = resp[-1][0] - 1
            resp = self.krakenApi.GetPrices(self.initial, 1, lastTime)
            if resp:
                for result in resp:
                    self.dataMachine.append(result[0], result[1])
                    self.dataMachine.append(result[0], result[2])
                    self.dataMachine.append(result[0], result[3])
                    self.dataMachine.append(result[0], result[4])
                    self.dataMachine.append(result[0], result[5])

        if self.dataMachine.ordered.size == 0:
            self.dataFiles = dict()
            try:
               self.dataFiles[self.initial] = None
               githubFile = self.greedyBoyRepo.get_contents(self.githubDataPath, self.branchName)
               githubFileContent = githubFile.decoded_content.decode('ascii')
               empty = not csv.Sniffer().has_header(githubFileContent)
               if not empty:
                   self.dataFile = open(self.dataPathWrite, "w")
                   self.dataFile.write(githubFileContent)
                   self.dataFile.close()
                   self.dataMachine = GBDataMachine.fromFilename(self.dataPathWrite)
            except: 0

        #################################
        # Trying to add data from today
        try:
            lastDate = self.dataMachine.ordered.iloc[-1]["Date"]
            #self.dataMachine = GBDataMachine.fromFilename(self.dataPathWrite if not empty else self.todayDataFilename)
            todayData = pd.read_csv(self.todayDataFilename, parse_dates=True)
            todayData = todayData.drop(todayData[todayData.epoch < lastDate].index)
            self.dataMachine.appendDataframe(todayData)
        except: 0

        print("Memory usage :", self.dataMachine.memoryUsage())
        self.getCryptoAndFiatBalance()
        print("Initial balance :")
        print("\t " + str(self.cryptoBalance) + " " + self.initial)
        print("\t$" + str(self.fiatBalance))
        #print(self.dataMachine.ordered.to_csv(index=False))

    def AddOrder(self, buyOrSell: str, amount, price = None):
        """
        Adds an order to the system.
        :param buyOrSell: The type of order to add, which can be "buy" or "sell".
        :param amount: The amount of the order.
        :param price: The price of the order. If None, the current price will be used.
        """
        assert buyOrSell in ("buy", "sell"), "buyOrSell must be 'buy' or 'sell'"

        if not price:
            price = self.dataMachine.ordered.iloc[-1]["Close"] # Gets Last price registered

        if self.buySellLimit != 0:
            maxAmount = self.buySellLimit / price # Gets max amount to buy or sell
            amount = min(amount, maxAmount)

        if buyOrSell == "buy":
            amount = min(amount, self.fiatBalance / price * 0.99975)
        elif buyOrSell == "sell":
            amount = min(amount, self.cryptoBalance * 0.99975)

        self.krakenApi.AddOrder(buyOrSell, "market", amount, self.initial)
        self.__writeRowToTemp({'Date': self.lastData, 'Price': str(price), 'Amount': str(amount), 'Order': buyOrSell})
        self.lastOrder = {'Date': self.lastData, 'Price': price, 'Amount': amount, 'Order': buyOrSell}
        if self.testTime:
            if self.buyOrSellPosition == "buy":
                self.cryptoBalance += amount * (0.9975)
                self.fiatBalance -= amount * price
            elif self.buyOrSellPosition == "sell":
                self.cryptoBalance -= amount
                self.fiatBalance += amount * price * (0.9975)
            self.__setBuyOrSellPosition()
        else:
            self.getCryptoAndFiatBalance()
        self.highest = self.lowest = 50

        print("Current balance :")
        print("\t " + str(self.cryptoBalance) + " " + self.initial)
        print("\t$" + str(self.fiatBalance))
        print("Added to reports : " + str(self.lastOrder))

    def addData(self, epoch, price):
        self.lastData = epoch
        self.dataMachine.append(epoch, price, False)
#        if self.dataMachine.intervalClosed():
        self.makeDecision()
        #print(self.dataMachine.iloc[:5].to_csv(index=False))

    def getCryptoAndFiatBalance(self):
        self.cryptoBalance, self.fiatBalance = self.krakenApi.GetCryptoAndFiatBalance(self.initial, GBConstants.FIAT_CURRENCY)
        self.fiatBalance = GBUtilities.getMaxFiatBalance(self.fiatBalance, self.testTime) #self.fiatBalance / 2.0 if self.fiatBalance / 2.0 < 50.0 else 50.0
        self.__setBuyOrSellPosition()
        return self.cryptoBalance, self.fiatBalance

    def setBuySellLimit(self, fiatValue: float):
        """
        Sets the buy/sell limit.
        :param fiatValue: The buy/sell limit to set.
        """
        self.buySellLimit = fiatValue

    def setCustomBalance(self, cryptoBalance: float, fiatBalance: float):
        """
        Sets the custom balance.
        :param cryptoBalance: The custom crypto balance to set.
        :param fiatBalance: The custom fiat balance to set.
        """
        self.cryptoBalance, self.fiatBalance = cryptoBalance, fiatBalance
        self.__setBuyOrSellPosition()

    ######################################################################
    ## Decisions Making
    def makeDecision(self):
#         ########################################################################
#         ## Bollinger Strategy
#         def bollingerStrategy():
#             curBolVal = self.dataMachine.currentBollingerValue()

#             if not self.buyOrSellPosition: return
#             if curBolVal <= 100 - self.bollingerTolerance and curBolVal >= self.bollingerTolerance: return

#             if curBolVal > self.highest: self.highest = curBolVal
#             elif curBolVal < self.lowest: self.lowest = curBolVal

#             if self.lastOrder and self.lastOrder['Date'] + self.dataMachine.interval * 60 < self.lastData:
#                 lastPrice = self.dataMachine.lastPrice()
#                 if self.lastOrder['Order'] == "buy":
#                     if lastPrice < self.lastOrder['Price']:
#                         print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                         print("Current bollinger value :", curBolVal)
#                         return self.AddOrderMax("sell")
#                 elif self.lastOrder['Order'] == "sell":
#                     if lastPrice > self.lastOrder['Price']:
#                         print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                         print("Current bollinger value :", curBolVal)
#                         return self.AddOrderMax("buy")

#             if self.buyOrSellPosition == "buy":
#                 if self.lowest < 0 and \
#                         curBolVal - self.lowest >= self.bollingerTolerance:
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                     print("Current bollinger value :", curBolVal)
#                     self.AddOrderMax("buy")
#             elif self.buyOrSellPosition == "sell":
#                 if self.highest > 100 and \
#                         self.highest - curBolVal >= self.bollingerTolerance:
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                     print("Current bollinger value :", curBolVal)
#                     self.AddOrderMax("sell")

#         ########################################################################
#         ## Scalping Strategy
#         def scalpingStrategy(): # Begins by selling, so you need the crypto first
#             if not self.buyOrSellPosition: return

#             if self.scalping is not None: # Sold
#                 last = self.dataMachine.ordered.iloc[-1]
#                 closePrice = last['Close']
#                 if closePrice >= self.scalping['Min'] * self.scalping['MaxPercentage'] or\
#                     closePrice <= self.scalping['SellPrice'] / ((self.scalping['MaxPercentage'] - 1) * 1.2 + 1):
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                     print("Close: {0:6.5f}, EMA20: {1:6.5f}, EMA50: {2:6.5f}, Percentage : {3:6.3f}".format(
#                         closePrice, last['EMA20'], last['EMA50'], (self.scalping['SellPrice'] / closePrice - 1) * 100 - 0.2))
#                     self.AddOrderMax("buy")
#                     self.scalping = None
# #                elif closePrice < self.scalping['Min']:
#  #                   self.scalping['Min'] = closePrice
#             elif self.dataMachine.intervalClosed():
#                 last = self.dataMachine.ordered.iloc[-2]
#                 ema20, ema50 = last['EMA20'], last['EMA50']
#                 closePrice = last['Close']
#                 if last['Open'] < closePrice \
#                     and last['Low'] <= ema20 and last['Open'] <= ema20 \
#                     and last['High'] >= ema20 and last['High'] < ema50 \
#                     and ema50 / closePrice >= 1.008:
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])))
#                     print("Close: {0:6.5f}, EMA20: {1:6.5f}, EMA50: {2:6.5f}, Percentage : {3:6.3f}".format(closePrice, ema20, ema50, (ema50 / closePrice - 1) * 100))
#                     self.AddOrderMax("sell")
#                     self.scalping = {
#                         'MaxPercentage': ema50 / closePrice,
#                         'SellPrice': max(closePrice, ema20),
#                         'Min': closePrice
#                     }

#         ####################################
#         ## EMA Crossover
#         def emaCrossover():
#             if not self.buyOrSellPosition: return

#             if not self.dataMachine.intervalClosed():
#                 return

#             last = self.dataMachine.ordered.iloc[-2]
#             closePrice, ema5, ema40 = last['Close'], last['EMA5'], last['EMA40']
#             # print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])) +
#             #       " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
#             if self.buyOrSellPosition == "buy":
#                 if ema5 > ema40 and ema5 / ema40 >= 1.000:
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])) +
#                          " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
#                     self.AddOrderMax("buy")
#             elif self.buyOrSellPosition == "sell":
#                 if ema5 < ema40 and ema40 / ema5 >= 1.000:
#                     print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])) +
#                          " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
#                     self.AddOrderMax("sell")
#                     print("")

        #return bollingerStrategy()
        #return scalpingStrategy()
        #return emaCrossover()
        #return self.emaCrossover.run5_40()
        return self.emaCrossover.run(5, 40)

    def __init__(self, apiKey, apiPrivateKey, githubToken, repoName, dataBranchName, initial, todayDataFilename,
                 ordersTempPath, ordersGithubPath, krakenToken = None, bollingerTolerance: float = 20, testTime: float = None):
        self.initial = initial
        self.dataPathWrite = tempfile.gettempdir() + "/data" + initial + "_old.csv"
        self.githubDataFilename = time.strftime(GBConstants.DATE_FORMAT, time.localtime(time.time() - 86400)) + ".csv"
        self.githubDataPath = "./price_history/" + initial + "/" + self.githubDataFilename

        self.ordersDataTempPath, self.ordersGithubPath = ordersTempPath, ordersGithubPath

        self.apiKey, self.apiPrivateKey = apiKey, apiPrivateKey
        self.branchName = dataBranchName

        self.todayDataFilename = todayDataFilename

        # For testing purposes
        self.testTime = testTime

        # Github repo
        g = Github(githubToken)
        self.greedyBoyRepo = g.get_repo(repoName)

        # Kraken API
        self.krakenApi = KrakenApi(apiKey, apiPrivateKey, krakenToken)

        # Decision making
        self.lastOrder, self.lastData = None, None
        self._buyOrSellPosition = None  # "buy" / "sell"
        self.cryptoBalance = self.fiatBalance = 0
            ## Bollinger Strat
        self.bollingerTolerance = bollingerTolerance
        self.lowest = self.highest = 50
        self.buySellLimit = 0 # 0 if no limit
            ## Scalping Start
        self.scalping = None
        # EMA Crossover
        self.emaCrossover = EMACrossover(self)

        self.start()