import krakenex
from time import sleep
from indicator import Indicator

intervals = [1, 5, 15, 30, 60, 240]

krakenAPI = krakenex.API()
krakenAPI.load_key('../kraken.key')

currencyPairs = list((krakenAPI.query_public('AssetPairs', {})['result']).keys())
currencyPairs = [cur for cur in currencyPairs if cur.endswith('.d') is not True]
print(currencyPairs)

currencyPairs = [cur for cur in currencyPairs if "XRP" in cur]
print(currencyPairs)


while (1):
    for curPair, interval in zip(currencyPairs, intervals):
    	indicator = Indicator(krakenAPI, curPair=curPair, interval=interval)
    	indicator.start()
    	sleep(5)
