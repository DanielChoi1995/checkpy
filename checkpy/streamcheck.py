import websockets
import asyncio
import logging
import json

from .ckeckenum import *
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

class StreamCheckpy(object):
    def __init__(self, user_id, user_key):
        self.__user_id = user_id
        self.__user_key = user_key
        self.__wss_uri = 'wss://newmobile.koscom.co.kr'
        self.__subscribes = {}

        with open('checkpy/translate.json') as f:
            self.__translate = json.load(f)

    def generate_subscribe_msg(self, market_type, sub_type, ticker):
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'dtype': 'open_sise', 'scode': self.__generate_code(market_type=market_type, sub_type=sub_type, ticker=ticker)}

        return json.dumps(payload) + '|'
    
    @staticmethod
    def __generate_code(market_type: MarketType, sub_type: SubType, ticker) -> str:
        return f'{market_type}{sub_type}{ticker}'
    
    def __convert_keys(self, msg):
        return {self.__translate.get(key): value for key, value in msg.items() if key in self.__subscribes.keys()}

    def __process_msg(self, msg, callback):
        callback(self.__convert_keys(msg))

    async def get_stream(self, callback):
        while True:
            try:
                async with websockets.connect(self.__wss_uri) as check_wss:
                    await check_wss.send(self.generate_subscribe_msg())
                
                while check_wss.open:
                    self.__process_msg(await check_wss.recv(), callback=callback)
            
            except (ConnectionClosedError, ConnectionClosedOK) as WebsocketError:
                logging.error(f'Wss error occurs reason: {WebsocketError}')
                await asyncio.sleep(1)