import pandas as pd
import time
from GBConstants import GBConstants
from IGreedyBoyDecisionMaker_module import IGreedyBoyDecisionMaker

class EMACrossover:
    def __init__(self, decisionMaker: IGreedyBoyDecisionMaker):
        self.decisionMaker = decisionMaker
        self.emaValues = GBConstants.getEMAValues()

    def run(self, low: int, high: int):
        """
        Runs the EMA crossover strategy with the given low and high EMA values.
        :param low: The low EMA value.
        :param high: The high EMA value.
        :return: None
        :exception: AssertionError if low is not in self.emaValues or high is not in self.emaValues or low >= high
        """
        assert low in self.emaValues, "Low EMA value not found in GBConstants"
        assert high in self.emaValues, "High EMA value not found in GBConstants"
        assert low < high, "Low EMA value must be lower than high EMA value"

        if not self.decisionMaker.buyOrSellPosition:
            return
        
        if not self.decisionMaker.isIntervalClosed():
            return
        
        last = float(self.decisionMaker.ordered.iloc[-2])
        closePrice = float(last['Close'])
        emaLow = float(last['EMA' + str(low)])
        emaHigh = float(last['EMA' + str(high)])

        if self.decisionMaker.buyOrSellPosition == "buy":
            if emaLow > emaHigh and emaLow / emaHigh >= 1.000:
                print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.decisionMaker.bollingerGaps.iloc[-1]['Date'])) +
                        " || Close: {0:6.5f}, EMA{1}: {2:6.5f}, EMA{3}: {4:6.5f}".format(closePrice, low, emaLow, high, emaHigh))
                self.decisionMaker.AddOrderMax("buy")
        elif self.decisionMaker.buyOrSellPosition == "sell":
            if emaLow < emaHigh and emaHigh / emaLow >= 1.000:
                print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.decisionMaker.bollingerGaps.iloc[-1]['Date'])) +
                        " || Close: {0:6.5f}, EMA{1}: {2:6.5f}, EMA{3}: {4:6.5f}".format(closePrice, low, emaLow, high, emaHigh))
                self.decisionMaker.AddOrderMax("sell")
                print("")
    
    def run5_40(self):
        """
        Runs the EMA crossover strategy with the 5 and 40 EMAs.
        """
        if not self.decisionMaker.buyOrSellPosition: 
            return

        if not self.decisionMaker.isIntervalClosed():
            return

        last = self.decisionMaker.ordered.iloc[-2]
        closePrice, ema5, ema40 = float(last['Close']), float(last['EMA5']), float(last['EMA40'])
        # print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.dataMachine.bollingerGaps.iloc[-1]['Date'])) +
        #       " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
        if self.decisionMaker.buyOrSellPosition == "buy":
            if ema5 > ema40 and ema5 / ema40 >= 1.000:
                print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.decisionMaker.bollingerGaps.iloc[-1]['Date'])) +
                        " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
                self.decisionMaker.AddOrderMax("buy")
        elif self.decisionMaker.buyOrSellPosition == "sell":
            if ema5 < ema40 and ema40 / ema5 >= 1.000:
                print(time.strftime(GBConstants.PRINT_DATE_TIME_FORMAT, time.gmtime(self.decisionMaker.bollingerGaps.iloc[-1]['Date'])) +
                        " || Close: {0:6.5f}, EMA5: {1:6.5f}, EMA40: {2:6.5f}".format(closePrice, ema5, ema40))
                self.decisionMaker.AddOrderMax("sell")
                print("")