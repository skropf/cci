import threading
from time import sleep

class Trader(threading.Thread):
    
    def __init__(self, krakenAPI, tick=10, runningTicks=60, currency=['XBT'], profitMargin=0.015, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)
        
        self._krakenAPI = krakenAPI
        self._tick = tick
        self._runningTicks = runningTicks
        self._currency = currency
        self._profitMargin = profitMargin
        
        self._trend = {}
        self._marketPriceList = {}
        self._currencyPairs = []
        self._orders = []
        
        for currency in self._currency:
            self._trend[currency] = []
            self._marketPriceList[currency] = []
            self._currencyPairs.append('X' + currency + 'ZUSD')

    def run(self):
        for time in range(self._runningTicks):
            print(str(time) + " of " + str(self._runningTicks) + ": ")
            sleep(self._tick)
        
            #getting market values from kraken for all currencies
            for currency in self._currency:
                result = self._krakenAPI.query_public('Ticker', {'pair': 'X' + currency + 'ZUSD'})['result']
                self._marketPriceList[currency].insert(0, format(float(result['X' + currency + 'ZUSD']['c'][0]), '.5f'))
                
            
            if time > 1:
                for currency in self._marketPriceList.keys():
                    marketPrice = float(self._marketPriceList[currency][0])
                    oldMarketPrice = float(self._marketPriceList[currency][1])
                    #limit = marketPrice * changeTrendLimit
                        
                    if marketPrice > oldMarketPrice:
                        #market value UP
                        self._trend[currency].insert(0, "U" + self._marketPriceList[currency][0])
                                    
                    elif marketPrice < oldMarketPrice:
                        #market value DOWN
                        self._trend[currency].insert(0, "D" + self._marketPriceList[currency][0])
                        
                        result = self._krakenAPI.query_public('Ticker', {'pair': 'X' + currency + 'ZUSD'})['result']['X' + currency + 'ZUSD']
                        buyMarginHalf = float(result['l'][1]) + ((float(result['h'][1]) - float(result['l'][1])) / 2)
                        buyMarginQuarter = float(result['l'][1]) + ((float(result['h'][1]) - float(result['l'][1])) / 4)
                        buyMarginTenth = float(result['l'][1]) + ((float(result['h'][1]) - float(result['l'][1])) / 8)
                        
                        #print("volume margin 1/2 " + currency + ": " + str(buyMarginHalf))
                        #print("volume margin 1/4 " + currency + ": " + str(buyMarginQuarter))
                        #print("volume margin 1/8 " + currency + ": " + str(buyMarginTenth))
                        

                        balance = float(self._krakenAPI.query_private('Balance', {}, None)['result']['ZUSD'])

                        if balance > 5:
                            if marketPrice < buyMarginTenth:
                                volume = 4 / marketPrice
                                buyResult = self._krakenAPI.query_private('AddOrder', {'pair': 'X' + currency + 'ZUSD', 'type': 'buy', 'ordertype': 'limit', 'price': marketPrice, 'volume': str(volume)}, None)
                                
                                print("---BOUGHT: " + str(buyResult))
                                txid = buyResult['result']['txid']
                                self._orders.append({'txid': txid, 'pair': 'X' + currency + 'ZUSD', 'marketPrice': marketPrice, 'volume': volume})
                                
                            elif marketPrice < buyMarginQuarter:
                                volume = 2 / marketPrice
                                buyResult = self._krakenAPI.query_private('AddOrder', {'pair': 'X' + currency + 'ZUSD', 'type': 'buy', 'ordertype': 'limit', 'price': marketPrice, 'volume': str(volume)}, None)
                                
                                print("---BOUGHT: " + str(buyResult))
                                txid = buyResult['result']['txid']
                                self._orders.append({'txid': txid, 'pair': 'X' + currency + 'ZUSD', 'marketPrice': marketPrice, 'volume': volume})
                            
                            elif marketPrice < buyMarginHalf:
                                volume = 1 / marketPrice
                                buyResult = self._krakenAPI.query_private('AddOrder', {'pair': 'X' + currency + 'ZUSD', 'type': 'buy', 'ordertype': 'limit', 'price': marketPrice, 'volume': str(volume)}, None)
                                
                                print("---BOUGHT: " + str(buyResult))
                                txid = buyResult['result']['txid'][0]
                                self._orders.append({'txid': txid, 'pair': 'X' + currency + 'ZUSD', 'marketPrice': marketPrice, 'volume': volume})
                            
                            
                            

                        else:
                            print("---NO FUNDS---\n---WAITING 5min---")
                            sleep(300)
                                
                            
                    else: self._trend[currency].insert(0, "S" + self._marketPriceList[currency][0])
                

                if len(self._orders) > 0:
                    closedOrders = list(self._krakenAPI.query_private('ClosedOrders', {}, None)['result']['closed'].keys())

                    ordersToDelete = []
                    for order in self._orders:
                        if closedOrders.count(order['txid']) > 0:
                            result = self._krakenAPI.query_private('AddOrder', {'pair': order['pair'], 'type': 'sell', 'ordertype': 'limit', 'price': str(float(order['marketPrice']) + float(order['marketPrice'])*0.015), 'volume': str(order['volume'])}, None)

                            ordersToDelete.append(order)
                            print("---SELLING: " + str(result))

                    for order in ordersToDelete:
                        self._orders.remove(order)
            
            #print("\n\n")
            #for currency in self._currency:
            #    print(currency + ": " + str(self._marketPriceList[currency][0:5]) + " - " + str(self._trend[currency][0:5]))
            #print("\n")
