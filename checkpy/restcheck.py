import json
import requests
import logging
import pandas as pd
from enum import IntEnum


class TimeSeriesType(IntEnum):
    NOT_TS = 0
    INTRA_DAY = 1
    OTHER = 2


class RestCheckpy(object):
    KLINE_INTERVAL = {'1d': 'daily', '1w': 'weekly', '1q': "quarterly", 'yoy': 'YTD', '1y': "yearly"}

    def __init__(self, user_id, user_key):
        self.__user_id = user_id
        self.__user_key = user_key
        self.__rest_base_uri = 'https://checkapi.koscom.co.kr'

        with open('checkpy/translate.json') as f:
            self.__translate = json.load(f)

    def __convert_columns(self, columns):
        return [self.__translate.get(column) for column in columns]

    def __fetch_data(self, end_point, payload, is_time_series: TimeSeriesType):
        resp = requests.post(f'{self.__rest_base_uri}{end_point}', data=payload).json()

        if resp.get('success') is True:
            df = pd.DataFrame(resp.get('results'))
            df.columns = self.__convert_columns(df.columns)

            if is_time_series == TimeSeriesType.INTRA_DAY:
                df['TIME'] = pd.to_datetime(df['INTRA_DATE'].astype(str) + df['INTRA_TIME'].astype(str).str.zfill(8), format='%Y%m%d%H%M%S%f')
                df.set_index(df['TIME'], inplace=True, drop=True)
                df.sort_index(inplace=True)
                df.drop(columns=['TIME', 'INTRA_DATE', 'INTRA_TIME'], errors='ignore', inplace=True)

            
            elif is_time_series == TimeSeriesType.OTHER:
                df['TIME'] = pd.to_datetime(df['DATE'].astype(str), format='%Y%m%d')
                df.set_index(df['TIME'], inplace=True, drop=True)
                df.sort_index(inplace=True)
                df.drop(columns=['TIME', 'DATE'], errors='ignore', inplace=True)

            else:
                pass

            return df.loc[:, df.columns.notna()].astype('float', errors='ignore')

        else:
            logging.debug(f"Fetch data failed. msg: {resp.get('message')}")
    
    def get_kospi_stocks_info(self):
        end_point = '/stock/m001/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kospi_stocks_basic_infos(self, tickers: list):
        end_point = '/stock/m001/basic_info_all_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kospi_investor_infos(self, tickers: list):
        end_point = '/stock/m001/invest_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kospi_orderbook_infos(self, tickers: list):
        end_point = '/stock/m001/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kospi_bbo_infos(self, tickers: list):
        end_point = '/stock/m001/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kospi_index_rank_infos(self, index_code: str, criteria_code: str):
        end_point = '/stock/m001/rank'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'up_code': index_code, 'criteria_code': criteria_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kospi_stock_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/stock/m001/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
    
    def get_kospi_stock_tick_data(self, ticker: str, date: str):
        end_point = '/stock/m001/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kospi_stock_kline_data_today_10s(self, ticker: str):
        end_point = '/stock/m001/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_kospi_stock_kline_data_intra_1m(self, ticker: str, date: str):
        end_point = '/stock/m001/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kospi_stock_kline_data(self, ticker: str, interval: str, start: str, end: str):
        end_point = '/stock/m001/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
        
    def get_kospi_index_infos(self):
        end_point = '/stock/m002/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kospi_index_basic_info(self, index_code: str):
        end_point = '/stock/m002/basic_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kospi_index_daily_info(self, index_code: str, start: str, end: str):
        end_point = '/stock/m002/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
    
    def get_kospi_index_tick_info(self, index_code: str):
        end_point = '/stock/m002/tick_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_kospi_index_kline_data_today_10s(self, index_code: str):
        end_point = '/stock/m002/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_kospi_index_kline_data_intra_1m(self, index_code: str, date: str):
        end_point = '/stock/m002/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kospi_index_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/stock/m002/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

    def get_kosdaq_stocks_info(self):
        end_point = '/stock/m003/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kosdaq_stocks_basic_infos(self, tickers: list):
        end_point = '/stock/m003/basic_info_all_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kosdaq_investor_infos(self, tickers: list):
        end_point = '/stock/m003/invest_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kosdaq_orderbook_infos(self, tickers: list):
        end_point = '/stock/m003/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kosdaq_bbo_infos(self, tickers: list):
        end_point = '/stock/m003/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kosdaq_index_rank_infos(self, index_code: str, criteria_code: str):
        end_point = '/stock/m003/rank'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'up_code': index_code, 'criteria_code': criteria_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kosdaq_stock_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/stock/m003/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
    
    def get_kosdaq_stock_tick_data(self, ticker: str, date: str):
        end_point = '/stock/m003/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kosdaq_stock_kline_data_today_10s(self, ticker: str):
        end_point = '/stock/m003/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kosdaq_stock_kline_data_intra_1m(self, ticker: str, date: str):
        end_point = '/stock/m003/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kosdaq_stock_kline_data(self, ticker: str, interval: str, start: str, end: str):
        end_point = '/stock/m003/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
        
    def get_kosdaq_index_infos(self):
        end_point = '/stock/m004/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kosdaq_index_basic_info(self, index_code):
        end_point = '/stock/m004/basic_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)

    def get_kosdaq_index_daily_info(self, index_code: str, start: str, end: str):
        end_point = '/stock/m004/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
    
    def get_kosdaq_index_tick_info(self, index_code: str):
        end_point = '/stock/m004/tick_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_kosdaq_index_kline_data_today_10s(self, index_code: str):
        end_point = '/stock/m004/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_kosdaq_index_kline_data_intra_1m(self, index_code: str, date: str):
        end_point = '/stock/m004/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType)
    
    def get_kosdaq_index_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/stock/m004/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
    
    def get_sector_index_infos(self):
        end_point = '/stock/m167/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_sector_index_basic_info(self, index_code: str):
        end_point = '/stock/m167/basic_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_sector_index_daily_info(self, index_code: str, start: str, end: str):
        end_point = '/stock/m167/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)

    def get_sector_index_tick_info(self, index_code: str):
        end_point = '/stock/m167/tick_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_sector_index_kline_data_today_10s(self, index_code: str):
        end_point = '/stock/m167/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_sector_index_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/stock/m167/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
    
    def get_other_index_infos(self):
        end_point = '/stock/m168/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_other_index_basic_info(self, index_code):
        end_point = '/stock/m168/basic_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_other_index_daily_info(self, index_code: str, start: str, end: str):
        end_point = '/stock/m168/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)

    def get_other_index_tick_info(self, index_code: str):
        end_point = '/stock/m168/tick_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_other_index_kline_data_today_10s(self, index_code: str):
        end_point = '/stock/m168/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_other_index_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/stock/m168/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
    
    def get_k200_futures_code_info(self):
        end_point = '/future/m005/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_futures_basic_infos(self, tickers: list):
        end_point = '/future/m005/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_futures_orderbook_infos(self, tickers: list):
        end_point = '/future/m005/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_futures_bbo_infos(self, tickers: list):
        end_point = '/future/m005/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_futures_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m005/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_k200_futures_tick_info(self, ticker: str, date: str):
        end_point = '/futures/m005/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_k200_futures_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m005/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_k200_futures_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m005/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_futures_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m005/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

    def get_kq150_futures_code_info(self):
        end_point = '/future/m067/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kq150_futures_basic_infos(self, tickers: list):
        end_point = '/future/m067/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_kq150_futures_orderbook_infos(self, tickers: list):
        end_point = '/future/m067/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kq150_futures_bbo_infos(self, tickers: list):
        end_point = '/future/m067/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kq150_futures_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m067/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_kq150_futures_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m067/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_kq150_futures_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m067/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_kq150_futures_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m067/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_kq150_futures_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m067/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')
    
    def get_stock_futures_code_info(self):
        end_point = '/future/m091/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_stock_futures_basic_infos(self, tickers: list):
        end_point = '/future/m091/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_stock_futures_orderbook_infos(self, tickers: list):
        end_point = '/future/m091/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_stock_futures_bbo_infos(self, tickers: list):
        end_point = '/future/m091/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_stock_futures_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m091/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_stock_futures_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m091/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_stock_futures_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m091/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_stock_futures_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m091/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_stock_futures_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m091/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')   

    def get_k200_mini_futures_code_info(self):
        end_point = '/future/m103/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_mini_futures_basic_infos(self, tickers: list):
        end_point = '/future/m103/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_mini_futures_orderbook_infos(self, tickers: list):
        end_point = '/future/m103/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_futures_bbo_infos(self, tickers: list):
        end_point = '/future/m103/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_futures_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m103/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_k200_mini_futures_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m103/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_k200_mini_futures_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m103/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_k200_mini_futures_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m103/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_futures_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m103/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

    def get_k200_option_code_info(self):
        end_point = '/future/m006/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_option_basic_infos(self, tickers: list):
        end_point = '/future/m006/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_option_orderbook_infos(self, tickers: list):
        end_point = '/future/m006/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_option_bbo_infos(self, tickers: list):
        end_point = '/future/m006/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_option_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m006/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_k200_option_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m006/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_k200_option_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m006/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_k200_option_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m006/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_option_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m006/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

    def get_k200_mini_option_code_info(self):
        end_point = '/future/m104/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_mini_option_basic_infos(self, tickers: list):
        end_point = '/future/m104/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_mini_option_orderbook_infos(self, tickers: list):
        end_point = '/future/m104/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_option_bbo_infos(self, tickers: list):
        end_point = '/future/m104/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_option_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m104/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_k200_mini_option_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m104/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_k200_mini_option_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m104/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_k200_mini_option_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m104/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_mini_option_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m104/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

    def get_k200_weekly_option_code_info(self):
        end_point = '/future/m182/code_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_weekly_option_basic_infos(self, tickers: list):
        end_point = '/future/m182/basic_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.NOT_TS)
    
    def get_k200_weekly_option_orderbook_infos(self, tickers: list):
        end_point = '/future/m182/hoga_info_port'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_weekly_option_bbo_infos(self, tickers: list):
        end_point = '/future/m182/hoga_info_port_top'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'codelist': ','.join(tickers)}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_weekly_option_daily_info(self, ticker: str, start: str, end: str):
        end_point = '/future/m182/hist_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'sdate': start, 'edate': end}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)  
    
    def get_k200_weekly_option_tick_info(self, ticker: str, date: str):
        end_point = 'futures/m182/tick_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': ticker, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)

    def get_k200_weekly_option_kline_data_today_10s(self, index_code: str):
        end_point = '/future/m182/intra_info'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
   
    def get_k200_weekly_option_kline_data_intra_10s(self, index_code: str, date: str):
        end_point = '/future/m182/intra_date'
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'edate': date}

        return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.INTRA_DAY)
    
    def get_k200_weekly_option_kline_data(self, index_code: str, interval: str, start: str, end: str):
        end_point = '/future/m182/term_hist_info'

        if interval in RestCheckpy.KLINE_INTERVAL.keys():
            payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'jcode': index_code, 'term': RestCheckpy.KLINE_INTERVAL.get(interval), 'sdate': start, 'edate': end}

            return self.__fetch_data(end_point=end_point, payload=payload, is_time_series=TimeSeriesType.OTHER)
        
        else:
            raise ValueError('Invalid interval')

