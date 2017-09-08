import os
import threading
#from time import sleep
from datetime import datetime

import plotly as py
import plotly.graph_objs as go


class Indicator(threading.Thread):

    _currentTimeStamp = 0
    _intervalOHLC = 1
    _count = 100

    _dictOHLC = {}
    _dictQuotes = {}

    _dictAP = {}
    _dictVWAP = {}
    _dictGASP = {}

    _dictTenkanSen = {}
    _dictKijunSen = {}
    _dictChikouSpan = {}
    _dictSenkouSpanA = {}
    _dictSenkouSpanB = {}


    def __init__(self, krakenAPI, curPair="XXBTZUSD", interval=1, tick=30, pathToSaveGraph=os.environ['HOME'], group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)

        self._krakenAPI = krakenAPI
        self._curPair = curPair
        self._intervalOHLC = interval
        self._tick = tick
        self._pathToSaveGraph = pathToSaveGraph

    def change_interval(self, interval):
        self._intervalOHLC = interval
        self._clear()

    def change_count(self, count=100):
        self._count = count

    def _update_all(self, count=100):
        resultDepth = self._krakenAPI.query_public('Depth', {'pair': self._curPair, 'count': self._count})['result'][self._curPair]
        resultOHLC = self._krakenAPI.query_public('OHLC', {'pair': self._curPair, 'interval': self._intervalOHLC})['result'][self._curPair]

        timestamp = int(self._krakenAPI.query_public('Time', {})['result']['unixtime'])
        self._update_ap(resultDepth, timestamp)
        self._update_vwap(resultDepth, timestamp)
        self._update_gasp(resultDepth, timestamp)


        newTimeStampOHLC = int(resultOHLC[0][0])

        if newTimeStampOHLC != self._currentTimeStamp:
            self._currentTimeStamp = newTimeStampOHLC

            self._update_ichimoku_kinko_hyo(resultOHLC)
            self._update_ohlc_quotes(resultOHLC)

    def _update_ap(self, resultDepth, timestamp):
        asks = resultDepth['asks']
        bids = resultDepth['bids']

        self._dictAP[timestamp] = float("{:4.8f}".format((float(asks[0][0]) + float(bids[0][0])) / 2.0))

    def _update_vwap(self, resultDepth, timestamp):
        asks = resultDepth['asks']
        bids = resultDepth['bids']

        askSumList = [float(ask[0]) * float(ask[1]) for ask in asks]
        bidSumList = [float(bid[0]) * float(bid[1]) for bid in bids]
        askVolumeList = [float(x[1]) for x in asks]
        bidVolumeList = [float(x[1]) for x in bids]

        self._dictVWAP[timestamp] = float("{:4.8f}".format((sum(askSumList) + sum(bidSumList)) / (sum(askVolumeList) + sum(bidVolumeList))))

    def _update_gasp(self, resultDepth, timestamp):
        asks = resultDepth['asks']
        bids = resultDepth['bids']

        askSum = 0
        bidSum = 0
        askVolume = sum([float(x[1]) for x in asks])
        bidVolume = sum([float(x[1]) for x in bids])

        if askVolume > bidVolume:
            askVolume = bidVolume
            bidVolumeBuffer = bidVolume
            for i in range(0, len(bids), 1):
                bidSum = bidSum + float(bids[i][0]) * float(bids[i][1])
                bids[i][1] = 0

            for i in range(0, len(asks), 1):
                if bidVolumeBuffer - float(asks[i][1]) >= 0:
                    bidVolumeBuffer = bidVolumeBuffer - float(asks[i][1])
                    askSum = askSum + (float(asks[i][0]) * float(asks[i][1]))
                    asks[i][1] = 0
                else:
                    asks[i][1] = float(asks[i][1]) - bidVolumeBuffer
                    askSum = askSum + (float(asks[i][0]) * bidVolumeBuffer)
                    bidVolumeBuffer = 0
                    break;

        if askVolume < bidVolume:
            bidVolume = askVolume
            askVolumeBuffer = askVolume
            for i in range(0, len(asks), 1):
                askSum = askSum + float(asks[i][0]) * float(asks[i][1])
                asks[i][1] = 0

            for i in range(0, len(bids), 1):
                if askVolumeBuffer - float(bids[i][1]) >= 0:
                    askVolumeBuffer = askVolumeBuffer - float(bids[i][1])
                    bidSum = bidSum + (float(bids[i][0]) * float(bids[i][1]))
                    bids[i][1] = 0
                else:
                    bids[i][1] = float(bids[i][1]) - askVolumeBuffer
                    bidSum = bidSum + (float(bids[i][0]) * askVolumeBuffer)
                    askVolumeBuffer = 0
                    break;

        self._dictGASP[timestamp] = float("{:4.8f}".format((askSum + bidSum) / (askVolume + bidVolume)))

    def _update_ichimoku_kinko_hyo(self, resultOHLC):
        for i in range(0, len(resultOHLC)):
            sumTenkanSen = 0.0
            sumKijunSen = 0.0
            sumSenkouSpanB = 0.0

            if i + 9 < len(resultOHLC):
                for j in range(i + 9, i, -1):
                    sumTenkanSen = sumTenkanSen + float(resultOHLC[j][2]) + float(resultOHLC[j][3])
                self._dictTenkanSen[int(resultOHLC[i + 9][0])] = float("{:4.8f}".format(sumTenkanSen / 18))

            if i + 26 < len(resultOHLC):
                for j in range(i + 26, i, -1):
                    sumKijunSen = sumKijunSen + float(resultOHLC[j][2]) + float(resultOHLC[j][3])
                self._dictKijunSen[int(resultOHLC[i + 26][0])] = float("{:4.8f}".format(sumKijunSen / 52))
                self._dictSenkouSpanA[int(resultOHLC[i + 26][0]) + 26 * 60 * self._intervalOHLC] = float("{:4.8f}".format((sumTenkanSen / 18 + sumKijunSen / 52) / 2))

            if i + 52 < len(resultOHLC):
                for j in range(i + 52, i, -1):
                    sumSenkouSpanB = sumSenkouSpanB + float(resultOHLC[j][2]) + float(resultOHLC[j][3])
                self._dictSenkouSpanB[int(resultOHLC[i + 52][0]) + 26 * 60 * self._intervalOHLC] = float("{:4.8f}".format(sumSenkouSpanB / 104))

            self._dictChikouSpan[int(resultOHLC[i][0]) - 26 * 60 * self._intervalOHLC] = float("{:4.8f}".format(float(resultOHLC[i][4])))

    def _update_ohlc_quotes(self, resultOHLC):
        self._dictQuotes['date'] = []
        self._dictQuotes['open'] = []
        self._dictQuotes['high'] = []
        self._dictQuotes['low'] = []
        self._dictQuotes['close'] = []


        for item in resultOHLC:
            self._dictQuotes['date'].append(datetime.utcfromtimestamp(int(item[0])))
            self._dictQuotes['open'].append(float(item[1]))
            self._dictQuotes['high'].append(float(item[2]))
            self._dictQuotes['low'].append(float(item[3]))
            self._dictQuotes['close'].append(float(item[4]))

    def _clear(self):
        self._dictOHLC.clear()
        self._dictQuotes.clear()

        self._dictAP.clear()
        self._dictVWAP.clear()
        self._dictGASP.clear()

        self._dictTenkanSen.clear()
        self._dictKijunSen.clear()
        self._dictChikouSpan.clear()
        self._dictSenkouSpanA.clear()
        self._dictSenkouSpanB.clear()

    def _write_ichimoku_kinko_hyo(self):
        traceOHLC = go.Candlestick(x=self._dictQuotes['date'],
                open=self._dictQuotes['open'],
                high=self._dictQuotes['high'],
                low=self._dictQuotes['low'],
                close=self._dictQuotes['close'],
                increasing=dict(line=dict(color='#DBDBDB'), name='Increasing'),
                decreasing=dict(line=dict(color='#6D6D6D'), name='Decreasing'))

        listTenkanSenTimeStamp = [datetime.utcfromtimestamp(int(timestamp)) for timestamp in list(self._dictTenkanSen.keys())]
        listKijunSenTimeStamp = [datetime.utcfromtimestamp(int(timestamp)) for timestamp in list(self._dictKijunSen.keys())]
        listChikouSpanTimeStamp = [datetime.utcfromtimestamp(int(timestamp)) for timestamp in list(self._dictChikouSpan.keys())]
        listSenkouSpanATimeStamp = [datetime.utcfromtimestamp(int(timestamp)) for timestamp in list(self._dictSenkouSpanA.keys())]
        listSenkouSpanBTimeStamp = [datetime.utcfromtimestamp(int(timestamp)) for timestamp in list(self._dictSenkouSpanB.keys())]

        traceTenkanSen = go.Scatter(x=listTenkanSenTimeStamp,
                                    y=list(self._dictTenkanSen.values()),
                                    mode='lines',
                                    line=dict(color='#11B011'),
                                    name='Tenkan Sen')
        traceKijunSen = go.Scatter(x = listKijunSenTimeStamp,
                                   y = list(self._dictKijunSen.values()),
                                   mode='lines',
                                   line=dict(color='#DB542D'),
                                   name='Kijun Sen')
        traceChikouSpan = go.Scatter(x = listChikouSpanTimeStamp,
                                     y = list(self._dictChikouSpan.values()),
                                     mode='lines',
                                     line=dict(color='#793271'),
                                     name='Chikou Span')
        traceSenkouSpanA = go.Scatter(x = listSenkouSpanATimeStamp,
                                      y = list(self._dictSenkouSpanA.values()),
                                      mode='lines',
                                      line=dict(color='#FF00FF'),
                                      name='Senkou Span A')
        traceSenkouSpanB = go.Scatter(x = listSenkouSpanBTimeStamp,
                                      y = list(self._dictSenkouSpanB.values()),
                                      mode='lines',
                                      line=dict(color='#AB00FF'),
                                      name='Senkou Span B')

        data = [traceOHLC, traceTenkanSen, traceKijunSen, traceChikouSpan, traceSenkouSpanA, traceSenkouSpanB]

        path = self._pathToSaveGraph + '/indicator/ichimoku-kinko-hyo/' + str(self._intervalOHLC) + 'min/'
        file = path + self._curPair + '.html'

        layout = go.Layout(title=self._curPair + ": AP:" + str(list(self._dictAP.values())[0]) + " VWAP:" + str(list(self._dictVWAP.values())[0]) + " GASP:" + str(list(self._dictGASP.values())[0]))

        fig = go.Figure(data=data, layout=layout)

        graph = py.offline.plot(fig, filename=file, output_type='div')

        if not os.path.exists(path): os.makedirs(path)

        file = open(file, "w")
        file.flush()
        file.write(str(graph))
        file.close()

    def run(self):
        print(self._curPair + "-Indicator running: Tick: " + str(self._tick) + "s - Interval: " + str(self._intervalOHLC) + "min")

        self._update_all()
        self._write_ichimoku_kinko_hyo()
        self._clear()

        #sleep(self._tick)
        print(self._curPair + "-Indicator finished.")
