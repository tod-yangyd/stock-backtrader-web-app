import datetime

from jqdatasdk import auth,normalize_code,get_price
from jqdatasdk import get_dominant_future,finance,query,get_futures_info
import pandas as pd


class Future_Method():
    def __init__(self):
        auth('13061919845', 'Qh!@#456')




    def get_commissionandmargin(self,fut_code, date,market_type='单品种'):
        """
        获取品种的保证金和合约系数信息
        :param ft_code: 'fg2501' or 'fg'
        :param unit: '1m' or '60m' or 'daily'
        :param start_dt: '2024-01-01 00:00:00'
        :param end_dt: '2024-07-01 00:00:00'
        :return:
        """
        if market_type =="主力连续":
            jq_code = get_dominant_future(fut_code, date, date).values[0]
        else:
            jq_code = normalize_code(fut_code)

        fut_infos = finance.run_query(
            query(
                finance.FUT_MARGIN.day, finance.FUT_MARGIN.specul_buy_margin_rate,
                finance.FUT_MARGIN.specul_sell_margin_rate).filter(
                finance.FUT_MARGIN.code == jq_code
            ).limit(1)
        )

        comm_query = finance.run_query(
            query(
                finance.FUT_CHARGE.day,finance.FUT_CHARGE.unit, finance.FUT_CHARGE.clearance_charge,
                finance.FUT_CHARGE.opening_charge).filter(

                finance.FUT_CHARGE.code == jq_code
                                                  )

        )
        comm_info = {
            'comm_unit': comm_query['unit'][0],
            'comm_charge': comm_query['clearance_charge'][0]
        }

        margin_buy = fut_infos['specul_buy_margin_rate'][0]

        future_info = get_futures_info(jq_code)

        contract_multiplier = future_info[jq_code]['contract_multiplier']
        return (margin_buy, contract_multiplier,comm_info)




    def get_fut_data_single(self,ft_code='FG2501', unit='60m', start_dt='2024-01-01 00:00:00',
                     end_dt='2024-07-01 00:00:00') -> pd.DataFrame:
        """
        获取单品种bar级别数据
        :param ft_code:
        :param unit: '1m' or '60m' or 'daily'
        :param start_dt: '2024-01-01 00:00:00'
        :param end_dt: '2024-07-01 00:00:00'
        :return:
        """
        jq_code = normalize_code(ft_code)
        fut_df = get_price(jq_code, start_date=start_dt, end_date=end_dt, frequency=unit
                           , fields=['open', 'high', 'low', 'close', 'volume', 'open_interest'])
        fut_df.rename(columns={'open_interest': 'openinterest'}, inplace=True)
        fut_df['code'] = ft_code
        return fut_df




    def get_main(self,fut_code,start_date='2023-08-05',end_date='2024-08-11'):
        """
        获取品种的日期范围内的主力合约
        :param fut_code:
        :param start_date: '2024-01-01'
        :param end_date: '2024-07-01'
        :return:
        """
        return get_dominant_future(fut_code, date = start_date, end_date=end_date)

    def get_fut_data_main(self,ft_code='FG2501.XZCE', unit='60m', date='2024-01-01',
                    ) -> pd.DataFrame:
        """
        获取行情单日bar级别数据
        :param ft_code:
        :param unit: '1m' or '60m' or 'daily'
        :param date: '2024-01-01'
        :return:
        """
        start_dt = date + " 00:00:00"
        end_dt = date + " 23:00:00"
        fut_df = get_price(ft_code, start_date=start_dt, end_date=end_dt, frequency=unit
                           , fields=['open', 'high', 'low', 'close', 'volume', 'open_interest'])
        fut_df.rename(columns={'open_interest': 'openinterest'}, inplace=True)
        fut_df['code'] = ft_code.split('.')[0]
        return fut_df