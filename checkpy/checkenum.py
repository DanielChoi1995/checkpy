from enum import StrEnum, IntEnum

class MarketType(StrEnum):
    KOSPI_STOCK = '00100'
    KOSPI_INDEX = '00200'
    KOSDAQ_STOCK = '00300'
    KOSDAQ_INDEX = '00400'
    K200_FUTURES = '00500'
    K200_OPTION = '00600'
    KQ150_FUTURES = '06700'
    STOCK_FUTURES = '09100'
    K200_MINI_F = '10300'
    K200_NIGHT_F_DELAYED = '20700'


class SubType(StrEnum):
    TRANSACTION = '2'
    ORDERBOOK = '5'


class SubscribeStatus(IntEnum):
    SUBSCRIBED = 0
    UNSUBSCRIBED = 1
