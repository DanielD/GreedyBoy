from KrakenBacktestGetter import KrakenBacktestGetter
import ConfigManager
import time, datetime

def getMillisecondsUntilTomorrow():
    # Record the current time using perf_counter
    start_time = time.perf_counter()
    # Calculate the time remaining until midnight
    now = datetime.datetime.now()
    next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    milliseconds_until_midnight = int((next_midnight - now).total_seconds() * 1000)
    # Record the end time using perf_counter and adjust for computation delay
    end_time = time.perf_counter()
    computation_delay_ms = (end_time - start_time) * 1000
    # Adjust the result for the computation time
    adjusted_milliseconds_until_midnight = milliseconds_until_midnight - computation_delay_ms
    return adjusted_milliseconds_until_midnight

def main():
    while True:
        apiKey, apiPrivateKey, githubToken, repoName, dataBranchName = ConfigManager.getConfig()
        kBacktestGetter = KrakenBacktestGetter(apiKey, apiPrivateKey, githubToken, repoName, dataBranchName)
        # Continue other (non WebSocket) tasks in the main thread

        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrowLimit = datetime.datetime.fromtimestamp(
            today.timestamp() + 86400 - 15
        )
        timer = getMillisecondsUntilTomorrow() - 15

        while True:
            try:
                print(time.strftime('Now: %H:%M:%S, ', time.localtime(time.time()))
                      + time.strftime('Limit : %d/%m/%Y %H:%M:%S, Time remaining: ', time.localtime(tomorrowLimit.timestamp()))
                      + str(getMillisecondsUntilTomorrow()))
                if time.time() > tomorrowLimit.timestamp():
                    print("Day finished !")
                    break
                time.sleep(3)
                if time.perf_counter() > timer:
                    print("Day finished !")
                    break
            except:
                break
        kBacktestGetter.close()

if __name__ == '__main__':
    main()