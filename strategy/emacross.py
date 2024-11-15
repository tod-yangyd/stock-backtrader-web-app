import backtrader as bt
import pandas as pd
import datetime

from .base import BaseStrategy


class EMaCrossStrategy(BaseStrategy):

    params = (
        ("printlog", False),
        ("emaperiod", {"ema1": 13, "ema2": 13, "ema3": 13, "ema4": 13}),
        ("trade_config",{"trade_cash_per":0.2,"trade_per_time":0.2})
    )
    trade_log = pd.DataFrame(columns=['datetime', '收盘价', '成交价', '持仓均价', '持仓数', '策略触发原因', '持仓浮盈',
                                      '总资金'])
    ema_df = pd.DataFrame(columns=['datetime','EMA1', 'EMA2', 'EMA3', 'EMA4'])
    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        print("策略参数： ", self.p.trade_config["trade_cash_per"], " and ", self.p.trade_config["trade_per_time"])

        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.ema1 = bt.ind.ExponentialMovingAverage(self.dataclose, period=self.p.emaperiod["ema1"])
        self.ema2 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema2"])
        self.ema3 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema3"])
        self.ema4 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema4"])

        info = self.broker.getcommissioninfo(self.data0)
        print("MUL: ",info.p.mult)
        print("MARGIN: ", info.p.margin)
        contract_margin = info.p.margin
        self.contract_mult = info.p.mult

        trade_money = self.broker.get_cash() * self.p.trade_config["trade_cash_per"]

        margin = self.data0.lines.close[0] * contract_margin * self.contract_mult

        self.crossover_em4 = bt.ind.CrossOver(self.ema1, self.ema4)

        # 单次下单比例
        self.trade_vol_per_time = self.p.trade_config["trade_per_time"]
        #最大持仓
        self.max_volume = int(trade_money/margin)
        #单次开仓额度
        self.trade_per_vol = int(self.max_volume * self.p.trade_config["trade_per_time"])
        # 触发交易原因
        self.triger_reason = None
        self.position_code = None

    def order_target_size_yyd(self, type, target_size):
        if self.getposition().size == 0:
            if target_size>0:
                return self.buy(size=target_size,
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Limit)
            else:
                return self.sell(size=target_size,
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Limit)
        elif self.getposition().size > 0:
            if type == '加仓':
                return self.buy(size=target_size-self.getposition().size,
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Limit)
            else:
                return self.sell(size=self.getposition().size-target_size,
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Limit)
        else:
            if type == '加仓':
                return self.sell(size=abs(target_size-self.getposition().size),
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Limit)
            else:
                return self.buy(size=abs(self.getposition().size-target_size),
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Limit)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])
        #print("ema1: ",self.ema1[0])

        ema_data = [
            [datetime.datetime.combine(self.data0.lines.datetime.date(0), self.data0.lines.datetime.time()),
            self.ema1[0],
            self.ema2[0],
            self.ema3[0],
            self.ema4[0]
             ]
        ]
        ema_frame = pd.DataFrame(ema_data,
                                  columns=['datetime','EMA1', 'EMA2', 'EMA3', 'EMA4'])

        self.ema_df = pd.concat(
            [self.ema_df,ema_frame],
            ignore_index=True)
        """
        print("交易日期：%s  交易时段%s  该时段开盘价： %d 该时段收盘价： %d" %
                (
                 self.data0.lines.datetime.date(0),
                 self.data0.lines.datetime.time(),
                 self.data0.lines.open[0],
                 self.data0.lines.close[0]
                )
              )
        """

        # 如果没有持仓，则以em1和em4的金叉或者死叉作为开仓信号
        if not self.position:
            # 如果短线与最长线交叉，以收盘价开仓1/3
            if self.crossover_em4 > 0:
                self.order = self.order_target_size_yyd(type='加仓',
                                                        target_size=self.trade_per_vol)

                self.triger_reason = "金叉，触发开仓"
                self.position_code = self.data[0]
                # self.buy(size=self.trade_per_vol,price=self.data0.lines.close[0])

            elif self.crossover_em4 < 0:
                self.order = self.order_target_size_yyd(type='加仓',
                                                        target_size=-self.trade_per_vol)
                self.triger_reason ="死叉，触发开仓"
                #print("************em4和em1死叉，触发开仓")
                # self.buy(size=-self.trade_per_vol,price=self.data0.lines.close[0])

            # 连续建仓信号初始化
            self.start_signal = 1
            # 止盈损触发信号
            self.triger_ProfitOrLoss = False
            # 建仓收盘价
            self.last_opened_close = self.data0.lines.close[0]


        # 如果有持仓，判断是反向开仓、继续开仓还是止盈还是回踩补仓
        else:
            # 如果持仓方向与bar的收盘价方向不一致，反向开仓，否则持仓方向不变
            if ((self.getposition().size > 0 and self.data0.lines.close[0] > self.ema4 ) or
                        (self.getposition().size < 0 and self.data0.lines.close[0] < self.ema4 )) :
                #判断是继续开仓还是止盈还是补仓
                # 如果收盘价穿过ema2，且ema2和ema3、ema4的方向一致，则止盈1/3
                if ((self.getposition().size > 0 and self.data0.lines.close[0] < self.ema2 and self.ema2>self.ema3 and self.ema3>self.ema4) or
                        (self.getposition().size < 0 and self.data0.lines.close[0] > self.ema2 and self.ema2<self.ema3 and self.ema3<self.ema4)) :
                    if not self.triger_ProfitOrLoss:
                        #print("*******************触发止盈,目标仓位：%d" %  int(self.getposition().size * (1-self.trade_vol_per_time)))
                        self.triger_reason="触发止盈,目标仓位：%d" %  int(self.getposition().size * (1-self.trade_vol_per_time))
                        self.order = self.order_target_size_yyd(target_size=int(self.getposition().size * (1-self.trade_vol_per_time)),
                                                            type='平仓')
                        self.triger_ProfitOrLoss = True
                        self.last_triger_ProfitOrLoss_close = self.data0.lines.close[0]
                    # 如果多仓，判断是否继续止盈
                    elif self.triger_ProfitOrLoss and self.getposition().size > 0 :
                        a = max(self.last_triger_ProfitOrLoss_close,self.data0.lines.close[0])
                        b = max(self.last_opened_close,self.last_triger_ProfitOrLoss_close)
                        if a>b:
                            #print("*******************触发追加止盈")
                            self.triger_reason ="触发追加止盈"
                            self.order = self.order_target_size_yyd(
                                target_size= int(self.getposition().size * (1-self.trade_vol_per_time)),
                                type='平仓')
                            self.triger_ProfitOrLoss = True
                    # 如果空仓，判断是否继续止盈
                    elif self.triger_ProfitOrLoss and self.getposition().size < 0 :
                        a = min(self.last_triger_ProfitOrLoss_close, self.data0.lines.close[0])
                        b = min(self.last_opened_close, self.last_triger_ProfitOrLoss_close)
                        if a < b:
                            #print("*******************触发追加止盈")
                            self.triger_reason = "触发追加止盈"
                            self.order = self.order_target_size_yyd(
                                target_size=int(self.getposition().size * (1 - self.trade_vol_per_time)),
                                type='平仓')
                            self.triger_ProfitOrLoss = True
                # 如果有回落，并且行情回踩回EMA3，则触发补仓至满仓
                elif self.triger_ProfitOrLoss and ((self.getposition().size > 0 and self.data0.lines.close[0] > self.ema3) or
                                           (self.getposition().size < 0 and self.data0.lines.close[0] < self.ema3))\
                        and abs(self.getposition().size) < self.max_volume:
                    if self.getposition().size > 0:
                        self.order = self.order_target_size_yyd(target_size= int(self.trade_per_vol / self.trade_vol_per_time),type='加仓')
                    else:
                        self.order = self.order_target_size_yyd(target_size= - int(self.trade_per_vol / self.trade_vol_per_time),type='加仓')
                    self.last_opened_close = self.data0.lines.close[0]
                    self.triger_reason = "触发补仓"
                    #print("************触发补仓")
                # 如果还有连续建仓信号，根据信号值增加仓位
                elif self.start_signal< self.max_volume :
                    self.start_signal +=1
                    #print("**********符合连续建仓，准备补仓位至: %d" % (self.start_signal))
                    self.triger_reason = "符合连续建仓，准备补仓位至: %d" % (self.start_signal)
                    if self.getposition().size > 0:
                        self.order = self.order_target_size_yyd(target_size= self.start_signal * self.trade_per_vol,type='加仓')
                    else:
                        self.order = self.order_target_size_yyd(target_size= - self.start_signal * self.trade_per_vol,type='加仓')
                    self.last_opened_close = self.data0.lines.close[0]
            # 反向开仓
            else:
                #print("************触发反向开仓")
                self.triger_reason = "触发反向开仓"
                if self.getposition().size > 0:
                    self.order = self.order_target_size(target= -self.trade_per_vol)
                elif self.getposition().size < 0:
                    self.order = self.order_target_size(target= self.trade_per_vol)
                # 连续建仓信号初始化
                self.start_signal = 1
                # 止盈损触发信号
                self.triger_ProfitOrLoss = False
                # 建仓收盘价
                self.last_opened_close = self.data0.lines.close[0]

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


            #+self.self.data0.lines.datetime.time()
            pos = self.getposition()
            trade_data = [
                [datetime.datetime.combine(self.data0.lines.datetime.date(0),self.data0.lines.datetime.time()),
                #pos.adjbase
                self.data0.lines.close[0],
                order.executed.price,
                pos.price,
                pos.size,
                self.triger_reason,
                pos.size * (pos.adjbase - pos.price) * self.contract_mult,
                self.broker.getvalue()


                    ]
            ]
            data_frame = pd.DataFrame(trade_data,
                                      columns=['datetime', '收盘价', '成交价', '持仓均价', '持仓数', '策略触发原因', '持仓浮盈',
                                               '总资金'])

            self.trade_log=pd.concat(
                [self.trade_log,data_frame],
                                     ignore_index=True)


        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None