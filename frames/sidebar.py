import datetime

import streamlit as st


def kline_ema_selector_ui() -> dict:
    """akshare params

    :return: dict
    """
    st.sidebar.markdown("# EMA Config")
    ema1 = st.sidebar.number_input("ema1", min_value=5, max_value=120, step=1, value=13)
    ema2 = st.sidebar.number_input("ema2", min_value=5, max_value=120, step=1, value=30)
    ema3 = st.sidebar.number_input("ema3", min_value=5, max_value=120, step=1, value=60)
    ema4 = st.sidebar.number_input("ema4", min_value=5, max_value=120, step=1, value=120)


    return {
        "ema1": ema1,
        "ema2": ema2,
        "ema3": ema3,
        "ema4": ema4
    }



def akshare_selector_ui() -> dict:
    """akshare params

    :return: dict
    """
    st.sidebar.markdown("# Akshare Config")
    symbol = st.sidebar.text_input("symbol")
    period = st.sidebar.selectbox("period", ("daily", "weekly", "monthly"))
    start_date = st.sidebar.date_input("start date", datetime.date(1970, 1, 1))
    start_date = start_date.strftime("%Y%m%d")
    end_date = st.sidebar.date_input("end date", datetime.datetime.today())
    end_date = end_date.strftime("%Y%m%d")
    adjust = st.sidebar.selectbox("adjust", ("qfq", "hfq", ""))
    return {
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust,
    }

def jqshare_selector_ui() -> dict:
    """akshare params

    :return: dict
    """
    st.sidebar.markdown("# JQshare Config")
    market_type = st.sidebar.selectbox("行情类型",("单品种","主力连续"))
    if market_type == "主力连续":
        symbol = st.sidebar.text_input("合约名称（ex. FG）")
    else:
        symbol = st.sidebar.text_input("合约名称（ex. fg2501）")
    period = st.sidebar.selectbox("行情数据间隔", ("15m","1m","5m"))
    start_date = st.sidebar.date_input("start date(试用版最早获取15个月以来的数据)",datetime.date.today() -datetime.timedelta(days=15*31),
                                       min_value=datetime.date.today() -datetime.timedelta(days=15*31))
    end_date = st.sidebar.date_input("end date(试用版最多获取3个月前的数据)",datetime.date.today() -datetime.timedelta(days=3*31),
                                     max_value=datetime.date.today() -datetime.timedelta(days=3*31))
    #start_date = st.sidebar.date_input("start date", datetime.date(1970, 1, 1))
    #start_date = start_date.strftime("%Y%m%d")
    #end_date = st.sidebar.date_input("end date", datetime.datetime.today())
    #end_date = end_date.strftime("%Y%m%d")
    #adjust = st.sidebar.selectbox("adjust", ("qfq", "hfq", ""))
    return {
        "market_type": market_type,
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date

    }


def backtrader_selector_ui() -> dict:
    """backtrader params

    :return: dict
    """
    st.sidebar.markdown("# BackTrader Config")
    start_date = st.sidebar.date_input(
        "backtrader start date", datetime.date(2000, 1, 1)
    )
    end_date = st.sidebar.date_input("backtrader end date", datetime.datetime.today())
    start_cash = st.sidebar.number_input(
        "start cash", min_value=0, value=100000, step=10000
    )
    commission_fee = st.sidebar.number_input(
        "commission fee", min_value=0.0, max_value=1.0, value=0.001, step=0.0001
    )
    stake = st.sidebar.number_input("stake", min_value=0, value=100, step=10)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "start_cash": start_cash,
        "commission_fee": commission_fee,
        "stake": stake,
    }

def backtrader_selector_ui_new() -> dict:
    """backtrader params

    :return: dict
    """
    st.sidebar.markdown("# BackTrader Config")
    start_date = st.sidebar.date_input(
        "回测开始时间", datetime.date.today() -datetime.timedelta(days=15*31)
    )
    end_date = st.sidebar.date_input("回测结束时间", datetime.date.today() -datetime.timedelta(days=3*31))
    start_cash = st.sidebar.number_input(
        "起始资金", min_value=0, value=50000, step=50000
    )
    """
    trade_cash_per = st.sidebar.number_input(
        "实际交易资金占比", min_value=0.1, value=0.3, step=0.1,max_value=1.0
    )
    trade_per_time = st.sidebar.number_input(
        "单次下单资金占比", min_value=0.1, value=0.3, step=0.1,max_value=1.0
    )
    """
    commission_fee = st.sidebar.number_input("手续费点数", value=2, disabled=True)/100
    checkbox = st.sidebar.checkbox("是否启用滑点")
    slippage = None
    if checkbox:
        slippage = st.sidebar.number_input("滑点点数: ", value=5, disabled=True)/100

        #slippage = st.sidebar.number_input("滑点",value=0.005,on_change=False,disabled=True)
    """
    # 单次下单手数
    stake = st.sidebar.number_input("stake", min_value=0, value=100, step=10)
    """
    return {
        "start_date": start_date,
        "end_date": end_date,
        "start_cash": start_cash,
        #"trade_cash_per": trade_cash_per,
        #"trade_per_time": trade_per_time,
        "commission_fee": commission_fee,
        "slippage": slippage
    }