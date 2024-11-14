import backtrader as bt

from .base import BaseStrategy

import pandas as pd
import datetime

class MaStrategy(BaseStrategy):
    """Ma strategy"""

    _name = "Ma"
    params = (
        ("maperiod", 15),
        ("printlog", False),
    )
    trade_log = pd.DataFrame(columns=['datetime', 'close', 'trade', 'price', 'position', 'profit', 'fund'])
    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None


        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )


    def next(self):
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log("BUY CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log("SELL CREATE, %.2f" % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )


            self.bar_executed = len(self)


            #+self.self.data0.lines.datetime.time()
            pos = self.getposition()
            trade_data = [
                    [datetime.datetime.combine(self.data0.lines.datetime.date(0),self.data0.lines.datetime.time()),
                    #pos.adjbase
                    self.data0.lines.close[0],
                    order.executed.price,
                    pos.price,
                    pos.size,
                    pos.size * (pos.adjbase - pos.price),
                    self.broker.getvalue()
                    ]
            ]
            data_frame = pd.DataFrame(trade_data,
                                      columns=['datetime', 'close', 'trade', 'price', 'position', 'profit', 'fund'])

            self.trade_log=pd.concat(
                [self.trade_log,data_frame],
                                     ignore_index=True)


        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None