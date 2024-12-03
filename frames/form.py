import streamlit as st


def params_selector_ui(params: dict) -> dict:
    params_parse = dict()
    with st.form("params"):
        for param in params:
            if param["type"] == "int":
                col1, col2 = st.columns(2)
                with col1:
                    min_number = st.number_input("min " + param["name"], value=param["min"])
                with col2:
                    max_number = st.number_input("max " + param["name"], value=param["max"])
                params_parse[param["name"]] = range(min_number, max_number, param["step"])
            else:
                pass
        submitted = st.form_submit_button("Submit")
    return submitted, params_parse

def params_selector_ui_new(params: dict) -> dict:
    params_parse = dict()
    with st.form("params"):
        for param in params:
            if param["type"] == "int":
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    ema1 = st.number_input("ema1 ", value=param["ema1"], step=1)
                with col2:
                    ema2 = st.number_input("ema2 ", value=param["ema2"], step=1)
                with col3:
                    ema3 = st.number_input("ema3 ", value=param["ema3"], step=1)
                with col4:
                    ema4 = st.number_input("ema4 ", value=param["ema4"], step=1)
                params_parse[param["name"]] = dict(ema1=ema1, ema2=ema2, ema3=ema3, ema4=ema4)
            elif param["type"] == "float" and param["name"] == "trade_config":
                trade_cash_per, trade_per_time = st.columns(2)
                with trade_cash_per:
                    trade_cash_per = st.number_input("交易资金占比",
                                                     value=param["trade_cash_per"],
                                                     step=0.1,
                                                     max_value=1.0)
                with trade_per_time:
                    trade_per_time = st.number_input("连续下单次数",
                                                     value=param["trade_times"],
                                                     step=1.0,
                                                     min_value=1.0
                                                     )

                params_parse[param["name"]] = dict(trade_cash_per=trade_cash_per,
                                                   trade_per_time=trade_per_time)
            else:
                pass

        submitted = st.form_submit_button("Submit")

    return  submitted, params_parse
