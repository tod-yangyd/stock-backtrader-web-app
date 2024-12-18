import streamlit as st
st.set_page_config(page_title="回测平台",layout="wide")


import numpy as np
# 兼容新旧版本numpy
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool


from streamlit_echarts import st_pyecharts

from charts import draw_pro_kline, draw_result_bar,draw_pro_kline_fut
from frames import (kline_ema_selector_ui,akshare_selector_ui,jqshare_selector_ui, backtrader_selector_ui,
                    backtrader_selector_ui_new,params_selector_ui,params_selector_ui_new)
from utils.logs import LOGGER
from utils.processing import gen_stock_df, gen_future_df,load_strategy, run_backtrader,run_backtrader_new
from utils.schemas import StrategyBase
from utils.indicators import merge_ema
import pandas as pd

def main():
    ak_params = akshare_selector_ui()
    backtrader_params = backtrader_selector_ui()

    if ak_params["symbol"]:
        stock_df = gen_stock_df(ak_params)

        st.subheader("Kline")
        kline = draw_pro_kline(stock_df)
        st_pyecharts(kline,height="800px")

        st.subheader("Strategy")
        name = st.selectbox("strategy", list(strategy.keys()))
        submitted, params = params_selector_ui(strategy[name])

        if submitted:
            LOGGER.info(f"akshare: {ak_params}")
            LOGGER.info(f"backtrader: {backtrader_params}")
            backtrader_params.update(
                {
                    "stock_df": stock_df.iloc[:, :6],
                    "_strategy": StrategyBase(name=name, params=params),
                }
            )
            par_df = run_backtrader(**backtrader_params)
            st.dataframe(par_df.style.highlight_max(subset=par_df.columns[-3:]))
            bar = draw_result_bar(par_df)
            st_pyecharts(bar, height="500px")

def main_new():

    jq_params = jqshare_selector_ui()
    #ema_params = kline_ema_selector_ui()
    backtrader_params = backtrader_selector_ui_new()
    st.subheader("Strategy")
    col1,col2 = st.columns(2)
    with col1:
        name = st.selectbox("strategy", list(strategy.keys()))
        submitted, params = params_selector_ui_new(strategy[name])
    if jq_params["symbol"] and submitted:

        (future_df, margin_buy, contract_multiplier,comm_info) = gen_future_df(jq_params)

        #print(calculate_ema(day_count=120,close=close_df))
        last_close = future_df["close"][-1]
        margin = last_close*margin_buy*contract_multiplier
        call_per = int(backtrader_params["start_cash"] * params["trade_config"]["trade_cash_per"] / margin /  params["trade_config"]["trade_per_time"])

        with col2:
            st.text_area("策略的参数信息",
                         '初始交易资金: %(money)i \n单笔保证金大约： %(margins)i  \n单次下单手数（向下取整）： %(volume)i \n最大持仓数: %(max_volume)i' %
                         {"money": backtrader_params["start_cash"] * params["trade_config"]["trade_cash_per"],
                          "margins": margin,
                          "volume": call_per,
                          "max_volume": call_per * params["trade_config"]["trade_per_time"]},
                         height=150
                         )
        future_df=merge_ema(future_df,params["emaperiod"])
        LOGGER.info(f"jq_config: {jq_params}")
        LOGGER.info(f"backtrader_config: {backtrader_params}")
        backtrader_params.update(
            {
                "future_df": future_df.iloc[:, :11],
                "_strategy": StrategyBase(name=name, params=params),
                "margin_buy": margin_buy,
                "contract_multiplier": contract_multiplier,
                "comm_unit": comm_info["comm_unit"],
                "comm_charge": comm_info["comm_charge"]

            }
        )
        trade_df,ema_df,fund_res = run_backtrader_new(**backtrader_params)
        ema_df.set_index('datetime',inplace=True)
        trade_df.set_index('datetime',inplace=True)

        result = pd.concat([ema_df,trade_df],axis=1)

        st.subheader("Kline")
        (kline, positon) = draw_pro_kline_fut(period=jq_params["period"], ema_params=params["emaperiod"], future_df=future_df,result_df=result)
        st_pyecharts(kline, height="600px")
        if jq_params["market_type"] == "主力连续":
            st_pyecharts(positon)

        st.subheader("策略结果", divider=True)
        res1, res2 = st.columns(2)
        with res1:
            st.dataframe(result,width=1200, hide_index=False)
        with res2:
            st.text_area("策略运行结果",
                         '交易后总资金: %(money)i \n总手续费： %(comm)i' %
                         {"money": fund_res["总资金"],
                          "comm": fund_res["总手续费"]},
                         height=150
                         )






if __name__ == "__main__":
    strategy = load_strategy("./config/strategy_qh.yaml")
    main_new()
