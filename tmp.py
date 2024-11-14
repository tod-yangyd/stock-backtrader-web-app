from utils import JQSDK
import pandas as pd

t  =JQSDK.Joinquant_Method()




if __name__ =="__main__":

    main_future_df = t.get_main('FG', '2023-08-07', end_date='2024-08-10')

    res = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'openinterest', 'code'])
    # 2024-08-06 FG2409.XZCE
    for date, future in main_future_df.items():
        try:
            hah = t.get_fut_data_v2(ft_code=future, unit='15m', date=date)
            res = pd.concat([res if not res.empty else None, hah])
        except Exception as e:
            print("日期： %s 获取主力合约行情数据失败,原因： %s" % (date, e))

    # 索引重置并转为date格式，方便统计
    res = res.reset_index()
    res["index"] = pd.to_datetime(res["index"]).dt.date
    # 按日期和合约品种计数,并转为list输出
    count_df_tmp = res[['index','code']].value_counts(sort=False).sort_index()
    count_df =count_df_tmp.reset_index()
    target_list = count_df.values.tolist()

    print(target_list)
    hm_x_data = count_df['index'].tolist()
    hm_y_data = count_df['code'].tolist()

    print(1)

