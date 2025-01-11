###
### GreedyBoyDecisionTester class
###
import datetime

from GreedyBoyDecisionMaker import GreedyBoyDecisionMaker
from ConfigManager import getConfig
from KrakenApi import get_kraken_token
import tempfile, time, csv, os
from typing import List
from github import Github
import pandas as pd
import requests
from GBConstants import GBConstants

# Testing with Dogecoin
currencyInitial = "ETH"

def getTestTimeList(greedyBoyRepo, branchName) -> List[float]:
    githubDataPath = "./price_history/" + currencyInitial + "/"

    tab = []
    try:
        dirContent = greedyBoyRepo.get_contents(os.path.dirname(githubDataPath), branchName)

        ## Checks if file already exists
        for file in dirContent:
            fileDate = os.path.splitext(os.path.basename(file.name))[0]
            fileDateTime = datetime.datetime.strptime(fileDate, GBConstants.DATE_FORMAT)
            tab += [(fileDateTime - datetime.datetime(1970, 1, 1)).total_seconds()]
    except:
        0

    return tab

def main():
    apiKey, apiPrivateKey, githubToken, repoName, dataBranchName = getConfig()
    ordersDataPath = tempfile.gettempdir() + "/reports" + currencyInitial + ".csv"
    githubOrdersPath = "./reports/" + currencyInitial + "-reports.csv"
    krakenToken = get_kraken_token(apiKey, apiPrivateKey)

    # Github repo
    g = Github(githubToken)
    repoName = repoName
    greedyBoyRepo = g.get_repo(repoName)

    # Loop
    testTimes = getTestTimeList(greedyBoyRepo, dataBranchName)
    testTimes.sort()

    # Log test
    testLog = open(tempfile.gettempdir() + "/testResults.csv", "w")
    testLogWriter = csv.DictWriter(
        testLog,
        fieldnames=['Date', 'Crypto', 'Fiat', 'OpeningPrice', 'ClosePrice', 'OverallBenefit', 'BotBenefit'],
        lineterminator="\n"
    )
    testLogWriter.writeheader()

    # Test Configurations
    cryptoBalance, fiatBalance = 0.0, GBConstants.FIAT_BALANCE_CHECK # 15000 XDG, 0 dollars

    # Loading test files
    testDatas = []
    for i, testTime in enumerate(testTimes):
        if i + 1 == len(testTimes): continue

        print("Loading", time.strftime(GBConstants.PRINT_DATE_FORMAT, time.gmtime(testTime)), "...")

        dataPath = tempfile.gettempdir() + "/data" + currencyInitial + str(testTime) + ".csv"

        if os.path.exists(dataPath):
            testDatas += [pd.read_csv(dataPath, parse_dates=False)]
            continue

        githubDataFilename = time.strftime(GBConstants.DATE_FORMAT, time.gmtime(testTime)) + ".csv"
        githubDataPath = "./price_history/" + currencyInitial + "/" + githubDataFilename

        try:
            githubFile = greedyBoyRepo.get_contents(githubDataPath, dataBranchName)

            if githubFile.content == '':
                githubResponse = requests.get(githubFile.download_url)
                githubResponse.raise_for_status()
                githubFileContent = githubResponse.text
                empty = not csv.Sniffer().has_header(githubFileContent)
                if not empty:
                    with open(dataPath, "w") as f:
                        f.write(githubFileContent)
                    testDatas += [pd.read_csv(dataPath, parse_dates=False)]
            else:
                githubFileContent = githubFile.decoded_content.decode('ascii')
                empty = not csv.Sniffer().has_header(githubFileContent)
                if not empty:
                    with open(dataPath, "w") as f:
                        f.write(githubFileContent)
                testDatas += [pd.read_csv(dataPath, parse_dates=False)]
        except Exception as e:
            print("Couldn't load file", githubDataPath, ":", e) 
            0


    print("Beginning tests...")
    for i, testTime in enumerate(testTimes):
        # Skip if not enough data for the last 5 days
        if len(testTimes) >= 5 and testTime < testTimes[-5]: 
            continue
        # Skip if i is 0 or the last test
        if i == 0 or i + 1 == len(testTimes): 
            continue
        # Skip if not the day after the previous test
        if testTimes[i - 1] != testTime - 86400: 
            continue

        print("Test " + time.strftime(GBConstants.PRINT_DATE_FORMAT, time.gmtime(testTime)) + ": ")
        dataPath = tempfile.gettempdir() + "/data" + currencyInitial + str(testTime) + ".csv"
        githubDataFilename = time.strftime(GBConstants.DATE_FORMAT, time.gmtime(testTime)) + ".csv"
        githubDataPath = "./price_history/" + currencyInitial + "/" + githubDataFilename
        ordersDataPath = tempfile.gettempdir() + "/reports" + currencyInitial + time.strftime(GBConstants.DATE_FORMAT, time.gmtime(testTime)) + ".csv"

        # Test decision maker
        gbDM = GreedyBoyDecisionMaker(
            apiKey, apiPrivateKey, githubToken, repoName,   # Api Key, Api Private Key, Github repo
            dataBranchName, currencyInitial, "dataPath",      # Branch name, trading initial, temp path of today's data
            ordersDataPath, githubOrdersPath, krakenToken,  # temp path containing orders, kraken token
            testTime=testTime                               # Test Time
        )
        if len(testDatas) > 0 and (0 <= i - 1 < len(testDatas)):
            gbDM.dataMachine.appendDataframe(testDatas[i - 1])
        else:
            continue

        # To get for comparisons
        beginningPrice = gbDM.dataMachine.lastPrice()

        gbDM.setCustomBalance(cryptoBalance, fiatBalance)
        if i < len(testDatas) and testDatas[i] is not None and not testDatas[i].empty:
            for j, row in testDatas[i].iterrows():
                gbDM.addData(row['epoch'], row['price'])
        else:
            continue

        # Log
        startingMoney = fiatBalance + cryptoBalance * beginningPrice

        # Benefits computed in percentage
        overallBenefit = (gbDM.fiatBalance + gbDM.cryptoBalance * gbDM.dataMachine.lastPrice()) / startingMoney
        botBenefit = (gbDM.fiatBalance + gbDM.cryptoBalance * gbDM.dataMachine.lastPrice()) / \
                     (fiatBalance + cryptoBalance * gbDM.dataMachine.lastPrice())

        overallBenefit = (overallBenefit - 1) * 100
        botBenefit = (botBenefit - 1) * 100

        row = {
            'Date': testTime,
            'Crypto': gbDM.cryptoBalance,
            'Fiat': gbDM.fiatBalance,
            'OpeningPrice': beginningPrice,
            'ClosePrice': gbDM.dataMachine.lastPrice(),
            'OverallBenefit': overallBenefit,
            'BotBenefit': botBenefit
        }
        testLogWriter.writerow(row)
        print("Results of " + time.strftime(GBConstants.PRINT_DATE_FORMAT, time.gmtime(testTime)) + ": " + str(row))

    # Close log
    testLog.close()

if __name__ == '__main__':
    main()