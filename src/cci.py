import krakenex
from time import sleep
from indicator import Indicator

#for possible values (currency pairs, intervals, etc.) see https://www.kraken.com/help/api


#intervals = [1, 5, 15, 30, 60, 240]
intervals = [15]

krakenAPI = krakenex.API()
krakenAPI.load_key('../kraken.key')

#get all currency pairs that kraken supports
currencyPairs = list((krakenAPI.query_public('AssetPairs', {})['result']).keys())
currencyPairs = [cur for cur in currencyPairs if cur.endswith('.d') is not True]
print(currencyPairs)

#only use currency pairs with XRP
currencyPairs = [cur for cur in currencyPairs if "XRP" in cur]

print(intervals)
print(currencyPairs)


#run indicator for the selected currency pairs
for curPair in currencyPairs:
    for interval in intervals:
        indicator = Indicator(krakenAPI, curPair=curPair, interval=interval)
        indicator.start()
        sleep(5)
