import pandas as pd



def calculate_ema(day_count: int, close: pd.DataFrame):
    """
           计算ema指标
           :param day_count:
           :param close:
           :return:
    """
    result = close.ewm(span=day_count, adjust=False).mean()
    # result = ta.ema(df, length=day_count)
    # 移除前day_count行的不准确数据
    #result = result.iloc[day_count:]
    #print ("生成范围",day_count, " 生成成果： ",result.dropna(axis=0, how='any').round(2))
    return result.dropna(axis=0, how='any').round(2)


def merge_ema(future_df: pd.DataFrame, time_periods: dict):
    """
        将从行情商导出的行情数据拼接ema的数据列

    """
    close_df = future_df["close"]
    for (key,value) in time_periods.items():

        df = calculate_ema(close=close_df, day_count=value)
        df.rename(key, inplace=True)
        future_df = pd.concat([future_df, df], axis=1, ignore_index=False)

    return future_df