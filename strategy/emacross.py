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
        print("策略参数： ", self.p.emaperiod,self.p.trade_config["trade_cash_per"], " and ", self.p.trade_config["trade_per_time"])

        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        """
        # bt自带的ema计算逻辑有问题，用talib也一样，弃用
        # Add a MovingAverageSimple indicator
        bt.talib.CDLDOJI(self.data.open, self.data.high,
                         self.data.low, self.data.close)
        self.ema1 = bt.talib.EMA(timeperiod=self.p.emaperiod["ema1"])
        self.ema2 = bt.talib.EMA(timeperiod=self.p.emaperiod["ema2"])
        self.ema3 = bt.talib.EMA(timeperiod=self.p.emaperiod["ema3"])
        self.ema4 = bt.talib.EMA(timeperiod=self.p.emaperiod["ema4"])
        
        #print(self.p.emaperiod["ema1"],self.p.emaperiod["ema2"],self.p.emaperiod["ema3"],self.p.emaperiod["ema4"])
        #self.ema1 = bt.ind.EMA(self.dataclose, period=self.p.emaperiod["ema1"])
        #self.ema2 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema2"])
        #self.ema3 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema3"])
        #self.ema4 = bt.ind.EMA(self.dataclose,period=self.p.emaperiod["ema4"])
        """

        info = self.broker.getcommissioninfo(self.data0)
        print("MUL: ",info.p.mult)
        print("MARGIN: ", info.p.margin)
        contract_margin = info.p.margin
        self.contract_mult = info.p.mult

        trade_money = self.broker.get_cash() * self.p.trade_config["trade_cash_per"]
        margin = self.data0.lines.close[0] * contract_margin * self.contract_mult

        #self.ema_cross() = bt.ind.CrossOver(self.ema1, self.data0.ema4[0])

        # 单次下单比例
        self.trade_vol_per_time = self.p.trade_config["trade_per_time"]
        #最大持仓
        self.max_volume = int(trade_money/margin)
        #单次开仓额度
        self.trade_per_vol = int(self.max_volume * self.p.trade_config["trade_per_time"])

        print("回测系统设置：\n 单次下单比例：",self.trade_vol_per_time,"最大持仓：",self.max_volume,"单次开仓额度：",self.trade_per_vol)



        # 触发交易原因
        self.triger_reason = None
        self.position_code = None



    def ema_cross(self):
        """
         计算ema1是否穿ema4
        """
        if self.data0.ema1[0]>self.data0.ema4[0]  and self.data0.ema1[-1]<=self.data0.ema4[-1]:
            # 金叉
            return 1
        elif self.data0.ema1[0]<self.data0.ema4[0] and self.data0.ema1[-1]>=self.data0.ema4[-1]:
            # 死叉
            return -1
        else:
            return 0

    def order_target_size_yyd(self, type, target_size):
        if self.getposition().size == 0:
            if target_size>0:
                return self.buy(size=target_size,
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Market)
            else:
                return self.sell(size=target_size,
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Market)
        elif self.getposition().size > 0:
            if type == '加仓':
                return self.buy(size=target_size-self.getposition().size,
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Market)
            else:
                return self.sell(size=self.getposition().size-target_size,
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Market)
        else:
            if type == '加仓':
                return self.sell(size=abs(target_size-self.getposition().size),
                                 price=self.data0.lines.close[0],
                                 exectype=bt.Order.Market)
            else:
                return self.buy(size=abs(self.getposition().size-target_size),
                                price=self.data0.lines.close[0],
                                exectype=bt.Order.Market)


    def open_init(self):

        # 连续建仓信号初始化
        self.consecutive_open = True

        # 止盈损触发信号
        self.first_triger_limit = False
        # 建仓收盘价
        #self.last_opened_close = self.data0.lines.close[0]
        # 止盈后跳过第一个bar
        self.skip_nextbar = False
        # 止盈后最高价初始化
        self.next_greatest_price = 0
        # 是否允许补仓
        self.allow_cover = False

    def update_next_greatest_price(self):
        if self.getposition().size > 0:
            self.next_greatest_price = self.data0.lines.high[0]
        else:
            self.next_greatest_price = self.data0.lines.low[0]


    def next(self):
        # Simply log the closing price of the series from the reference
        self.log("Close, %.2f" % self.dataclose[0])
        time = datetime.datetime.combine(self.data0.lines.datetime.date(0), self.data0.lines.datetime.time())

        ema_data = [
            [datetime.datetime.combine(self.data0.lines.datetime.date(0), self.data0.lines.datetime.time()),
            self.data0.ema1[0],
            self.data0.ema2[0],
            self.data0.ema3[0],
            self.data0.ema4[0]
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
            if self.ema_cross() > 0:
                # 开仓信息初始化
                self.open_init()
                self.order = self.order_target_size_yyd(type='加仓',
                                                        target_size=self.trade_per_vol)
                self.triger_reason = "金叉，触发开仓"
                self.position_code = self.data[0]
                self.last_greatest_price =  self.data0.lines.high[0]
                # self.buy(size=self.trade_per_vol,price=self.data0.lines.close[0])
            elif self.ema_cross()  < 0:
                # 开仓信息初始化
                self.open_init()
                self.order = self.order_target_size_yyd(type='加仓',
                                                        target_size=-self.trade_per_vol)
                self.triger_reason ="死叉，触发开仓"
                self.last_greatest_price = self.data0.lines.low[0]

        # 如果有持仓，判断是反向开仓、继续开仓还是止盈还是回踩补仓
        else:

            # 仓位方向不变
            if ((self.getposition().size > 0 and self.ema_cross() >= 0) or
                    (self.getposition().size < 0 and self.ema_cross() <= 0)):

                # 是否满足连续建仓条件
                if  self.consecutive_open:
                    if abs(self.getposition().size) < self.max_volume:

                        if self.getposition().size > 0:
                            target_position = self.getposition().size + self.trade_per_vol
                            self.triger_reason = "符合连续建仓，准备补仓位至: %d" % (target_position)
                            self.order = self.order_target_size_yyd(
                                target_size=target_position, type='加仓')
                        else:
                            target_position = self.getposition().size - self.trade_per_vol
                            self.triger_reason = "符合连续建仓，准备补仓位至: %d" % (target_position)
                            self.order = self.order_target_size_yyd(
                                target_size=target_position, type='加仓')
                    else:
                        self.consecutive_open=False


                # 全部建仓完成以后，开始判断止盈or补仓
                else:

                    # 止盈条件采集
                    if self.getposition().size > 0:
                        # 记录交易后到止盈之间的最优价，以及止盈后下一次止盈区间内的最优价
                        if self.next_greatest_price == 0:
                            self.last_greatest_price = max(self.last_greatest_price, self.data0.lines.high[0])
                        else:
                            self.next_greatest_price = max(self.next_greatest_price, self.data0.lines.high[0])

                        # 补仓价格检查
                        if self.data0.lines.close[0] < self.data0.ema3[0]:
                            self.allow_cover = True
                    else:
                        if self.next_greatest_price == 0:
                            self.last_greatest_price = min(self.last_greatest_price, self.data0.lines.low[0])
                        else:
                            self.next_greatest_price = min(self.next_greatest_price, self.data0.lines.low[0])

                        if self.data0.lines.close[0] > self.data0.ema3[0]:
                            self.allow_cover = True
                    # 止盈行情趋势判断
                    if (
                        (self.getposition().size >0 and self.data0.ema1[0] > self.data0.ema2[0] and self.data0.ema2[0] > self.data0.ema3[0] and
                         self.data0.ema3[0] > self.data0.ema4[0])
                        or
                        (self.getposition().size < 0 and self.data0.ema1[0] < self.data0.ema2[0] and self.data0.ema2[0] < self.data0.ema3[0] and
                         self.data0.ema3[0] < self.data0.ema4[0])
                    ):

                        # 趋势行情下，收盘价穿过ema2，进入止盈判断逻辑
                        if (
                                (self.getposition().size >0 and self.data0.lines.close[0] < self.data0.ema2[0])
                                or
                                (self.getposition().size < 0 and self.data0.lines.close[0] > self.data0.ema2[0])
                        ):
                            # 检查触发过止盈，需要跳过这个bar
                            if not self.skip_nextbar:
                                # 如果本轮持仓第一次触发止盈
                                if not self.first_triger_limit:
                                    self.triger_reason = ("首次触发止盈,目标仓位：%d, 区间最优价格：%d" %
                                                          (
                                                            int(self.getposition().size * (1 - self.trade_vol_per_time)),
                                                            self.last_greatest_price
                                                          )
                                    )
                                    self.order = self.order_target_size_yyd(
                                        target_size=int(self.getposition().size * (1 - self.trade_vol_per_time)),
                                        type='平仓')
                                    self.first_triger_limit = True
                                    self.skip_nextbar = True
                                    # self.last_triger_limit_close = self.data0.lines.close[0]
                                    self.update_next_greatest_price()
                                # 如果满足基本止盈条件
                                else:
                                    # 检查是否满足AB之间的最高价关系
                                    if ((self.getposition().size > 0 and self.next_greatest_price > self.last_greatest_price) or
                                            (self.getposition().size < 0 and self.next_greatest_price < self.last_greatest_price)):
                                            self.triger_reason = ("触发追加止盈,目标仓位：%d, 上一个区间最优价格： %d, 本区间最优价格: %d" %
                                                (
                                                    int(self.getposition().size * (1 - self.trade_vol_per_time)),
                                                    self.last_greatest_price,
                                                    self.next_greatest_price
                                                )
                                            )
                                            self.order = self.order_target_size_yyd(
                                                target_size=int(self.getposition().size * (1 - self.trade_vol_per_time)),
                                                type='平仓')
                                            self.skip_nextbar = True
                                            self.last_greatest_price = self.next_greatest_price
                                            self.update_next_greatest_price()
                                    # 如果不满足，则不触发追加止盈
                                    else:
                                        self.skip_nextbar = False
                                        self.update_next_greatest_price()
                            else:
                                self.skip_nextbar = False
                    # 补仓行情趋势判断
                    elif self.allow_cover and self.first_triger_limit:
                        if (
                                (self.getposition().size > 0 and self.data0.lines.close[0] > self.data0.ema3[0])
                                or
                                (self.getposition().size < 0 and self.data0.lines.close[0] < self.data0.ema3[0])
                        ) and abs(self.getposition().size) < self.max_volume:
                            if self.getposition().size > 0:
                                self.order = self.order_target_size_yyd(target_size=self.max_volume, type='加仓')
                            else:
                                self.order = self.order_target_size_yyd(target_size=-self.max_volume, type='加仓')
                            # self.last_opened_close = self.data0.lines.close[0]
                            self.triger_reason = "触发补仓"
                            self.allow_cover = False
            # 反向开仓
            else:
                #print("************触发反向开仓")
                self.triger_reason = "触发反向开仓"
                if self.getposition().size > 0:
                    self.order = self.order_target_size(target= -self.trade_per_vol)
                    self.last_greatest_price = self.data0.lines.low[0]
                    self.open_init()
                elif self.getposition().size < 0:
                    self.order = self.order_target_size(target= self.trade_per_vol)
                    self.last_greatest_price = self.data0.lines.high[0]
                    self.open_init()





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

            pos = self.getposition()
            trade_data = [
                [
                    datetime.datetime.combine(self.data0.lines.datetime.date(0), self.data0.lines.datetime.time()),
                    # pos.adjbase
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
                                      columns=['datetime', '收盘价', '成交价', '持仓均价', '持仓数', '策略触发原因',
                                               '持仓浮盈',
                                               '总资金'])

            self.trade_log = pd.concat(
                [self.trade_log, data_frame],
                ignore_index=True)



        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None