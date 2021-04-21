###
### MAIN
###

import KrakenApi
from KrakenBacktestGetter import KrakenBacktestGetter
import csv, time, datetime, json
import timeit

def lambda_handler(event, context):
    main()
    return {
        'statusCode': 200,
        'body': json.dumps("Hello coomers !")
    }

def getConfig():
    with open("config.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            return row['apiKey'], row['apiPrivateKey'], row['githubToken'], row['repoName'], row['dataBranchName']

def main():
    timer = time.perf_counter() + 60 * 15 - 15
    apiKey, apiPrivateKey, githubToken, repoName, dataBranchName = getConfig()
    kBacktestGetter = KrakenBacktestGetter(apiKey, apiPrivateKey, githubToken, repoName, dataBranchName)
#    kApi = KrakenApi.KrakenApi(apiKey, apiPrivateKey)
    # Continue other (non WebSocket) tasks in the main thread

    today = datetime.datetime.today()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrowLimit = datetime.datetime.fromtimestamp(
        today.timestamp() + 86400 - 10
    )

    while True:
        try:
            print(time.strftime('Now   : %d/%m/%Y %H:%M:%S', time.localtime(time.time())))
            print(time.strftime('Limit : %d/%m/%Y %H:%M:%S', time.localtime(tomorrowLimit.timestamp())))
            if time.time() > tomorrowLimit.timestamp():
                print("Day finished !")
                break
            time.sleep(3)
            print(str(time.perf_counter()) + " | " + str(timer))
            if time.perf_counter() > timer:
                break
        except:
            break
    kBacktestGetter.close()

if __name__ == '__main__':
    main()