import datetime

import akshare as ak
import backtrader  as bt


import backtrader.analyzers as btanalyzers
import pandas as pd
import streamlit as st
import yaml

from .schemas import StrategyBase
from utils import JQSDK
import time


@st.cache_data
def gen_stock_df(ak_params: dict) -> pd.DataFrame:
    """generate stock data

    Args:
        ak_params (dict): akshare kwargs

    Returns:
        pd.DataFrame: _description_
    """
    return ak.stock_zh_a_hist(**ak_params)



def gen_future_df(jq_params: dict) -> tuple:
    """generate stock data

    Args:
        jq_params (dict): jqshare kwargs

    Returns:
        pd.DataFrame: _description_
    """
    my_bar = st.progress(0, text='正在载入行情数据..')
    jqdata = JQSDK.Future_Method()


    (margin_buy, contract_multiplier,comm_info) = jqdata.get_commissionandmargin(fut_code=jq_params['symbol'], date=jq_params['end_date'],
                                                                       market_type=jq_params['market_type'])
    res = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'openinterest', 'code'])
    if jq_params['market_type'] =="主力连续":
        main_future_df = jqdata.get_main(jq_params['symbol'], start_date=jq_params['start_date'], end_date=jq_params['end_date'])


        time.sleep(0.01)
        for date, future in main_future_df.items():
            try:
                data = jqdata.get_fut_data_main(ft_code=future, unit=jq_params['period'], date=date)
                res = pd.concat([res if not res.empty else None, data])
            except Exception as e:
                print("日期： %s 获取主力合约行情数据失败,原因： %s" % (date, e))
    else:
        res = jqdata.get_fut_data_single(ft_code=jq_params['symbol'], unit=jq_params['period'],
                                   start_dt=jq_params['start_date'], end_dt=jq_params['end_date'])
    my_bar.progress(100, text='行情载入完成，开始载入策略指标')
    time.sleep(1)
    my_bar.empty()

    """
    df = jqdata.get_fut_data(ft_code=jq_params['symbol'], unit=jq_params['period'], start_dt=jq_params['start_date'],
                             end_dt=jq_params['end_date'])
    """
    return res,margin_buy/100,contract_multiplier,comm_info


@st.cache_data
def run_backtrader(
    stock_df: pd.DataFrame,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    start_cash: int,
    commission_fee: float,
    stake: int,
    _strategy: StrategyBase,
) -> pd.DataFrame:
    """run backtrader

    Args:
        stock_df (pd.DataFrame): stock data
        start_date (datetime.datetime): back trader from date
        end_date (datetime.datetime): back trader end date
        start_cash (int): back trader start cash
        commission_fee (float): commission fee
        stake (int): stake
        _strategy (StrategyBase): strategy name an params

    Returns:
        pd.DataFrame: back trader results
    """
    stock_df.columns = [
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
    ]
    stock_df.index = pd.to_datetime(stock_df["date"])
    data = bt.feeds.PandasData(dataname=stock_df, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=commission_fee)
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")

    strategy_cli = getattr(__import__(f"strategy"), f"{_strategy.name}Strategy")
    cerebro.optstrategy(strategy_cli, **_strategy.params)
    back = cerebro.run(optreturn=False)


    par_list = []
    for x in back:

        par = []
        for param in _strategy.params.keys():
            par.append(x[0].params._getkwargs()[param])
        par.extend(
            [
                x[0].analyzers.returns.get_analysis()["rnorm100"],
                x[0].analyzers.drawdown.get_analysis()["max"]["drawdown"],
                x[0].analyzers.sharpe.get_analysis()["sharperatio"],
            ]
        )
        par_list.append(par)
    columns = list(_strategy.params.keys())
    columns.extend(["return", "dd", "sharpe"])
    par_df = pd.DataFrame(par_list, columns=columns)
    return par_df


def load_strategy(yaml_file: str) -> dict:
    """load strategy

    Args:
        yaml_file (str): strategy config file path

    Returns:
        dict: strategy
    """
    with open(yaml_file, "r") as f:
        strategy = yaml.safe_load(f)
    return strategy


class PandasDataPlus(bt.feeds.PandasData):
    lines = ('ema1','ema2','ema3','ema4',)  # 要添加的列名
    # 设置 line 在数据源上新增的位置
    params = (
        #('turnover', -1),  # turnover对应传入数据的列名，这个-1会自动匹配backtrader的数据类与原有pandas文件的列名
        ('ema1', -1),
        ('ema2', -1),
        ('ema3', -1),
        ('ema4', -1),
        # 如果是个大于等于0的数，比如8，那么backtrader会将原始数据下标8(第9列，下标从0开始)的列认为是turnover这一列
    )



def run_backtrader_new(
    future_df: pd.DataFrame,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    start_cash: int,
    #commission_fee: float,
    slippage: float,
    coc: bool,
    margin_buy: int,
    contract_multiplier: int,
    comm_unit: str,
    comm_charge: float,
    _strategy: StrategyBase,
) -> pd.DataFrame:
    """run backtrader

    Args:
        future_df (pd.DataFrame): future data
        start_date (datetime.datetime): back trader from date
        end_date (datetime.datetime): back trader end date
        start_cash (int): back trader start cash

        slippage: 滑点设置
        coc: 作弊成交设置
        margin_buy: 保证金比例设置
        contract_multiplier: 合约系数设置
        comm_unit: 手续费单位设置
        comm_charge: 手续费比例设置
        _strategy (StrategyBase): strategy name  params

    Returns:
        pd.DataFrame: back trader results
    """
    future_df.columns = [

        "open",
        "high",
        "low",
        "close",
        "volume",
        'open_interest',
        'code',
        'ema1',
        'ema2',
        'ema3',
        'ema4'
    ]

    #print("backtrader导入期货数据：" ,future_df)

    data = PandasDataPlus(dataname=future_df, fromdate=start_date, todate=end_date)



    cerebro = bt.Cerebro()
    cerebro.broker.set_coc(coc)
    if comm_unit =="‱":
        cerebro.broker.setcommission(commission=comm_charge/10000, #交易手续费
                                     stocklike=False, #股票则填True
                                     commtype=bt.CommInfoBase.COMM_PERC,# 比例收手续费
                                     margin= margin_buy,    #保证金比例
                                     mult= contract_multiplier, #杠杆倍率
                                     automargin=True #按比例计算保证金
                                     )
    else:
        cerebro.broker.setcommission(commission=comm_charge,  # 交易手续费
                                     stocklike=False,  # 股票则填True
                                     commtype=bt.CommInfoBase.COMM_FIXED,  # 固定手续费
                                     margin=margin_buy,  # 保证金比例
                                     mult=contract_multiplier,  # 杠杆倍率
                                     automargin=True  # 按比例计算保证金
                                     )
    print("backtrader滑点设置：", slippage)
    # 是否滑点
    if slippage:
        cerebro.broker = bt.brokers.BackBroker(slip_perc=slippage)
    cerebro.adddata(data)
    cerebro.broker.setcash(start_cash)
    """
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
    #夏普比率分析器
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="sharpe")
    #回撤分析器
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    #年华收益率
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
    """
    strategy_cli = getattr(__import__(f"strategy"), f"{_strategy.name}Strategy")

    cerebro.addstrategy(strategy_cli, **_strategy.params)
    #如果希望多策略参数多次执行，用optstrategy
    #cerebro.optstrategy(strategy_cli, **_strategy.params)
    results = cerebro.run(optreturn=False)

    fund_res = {"总资金":cerebro.broker.get_value(),"总手续费":results[0].comm_all}






    back_df = results[0].trade_log
    ema_df = results[0].ema_df

    """
    par_list = []
    for x in back:
        par = []
        for param in _strategy.params.keys():
            par.append(x[0].params._getkwargs()[param])
        par.extend(
            [
                x[0].analyzers.returns.get_analysis()["rnorm100"],
                x[0].analyzers.drawdown.get_analysis()["max"]["drawdown"],
                x[0].analyzers.sharpe.get_analysis()["sharperatio"],
            ]
        )
        par_list.append(par)
    columns = list(_strategy.params.keys())
    columns.extend(["return", "dd", "sharpe"])
    par_df = pd.DataFrame(par_list, columns=columns)
    """
    return back_df,ema_df,fund_res
