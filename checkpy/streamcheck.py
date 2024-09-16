import websockets
import asyncio
import logging
import sys
import json

from .checkenum import *
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from typing import List, Tuple, Union


class StreamCheckpy(object):
    def __init__(self, user_id, user_key, initial_subscribes: List[Tuple[Union[MarketType, SubType, str]]]):
        self.__user_id = user_id
        self.__user_key = user_key
        self.__wss_uri = 'wss://newmobile.koscom.co.kr'
        self.__subscribes = {self.__generate_code(initial_subscribe[0], initial_subscribe[1], initial_subscribe[2]): SubscribeStatus.UNSUBSCRIBED for initial_subscribe in initial_subscribes}

        with open('checkpy/translate.json') as f:
            self.__translate = json.load(f)

    def __generate_subscribe_msg(self, code):
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'dtype': 'open_sise', 'scode': code}

        return json.dumps(payload)
    
    def __generate_unsubscribe_msg(self, code):
        payload = {'cust_id': self.__user_id, 'auth_key': self.__user_key, 'dtype': 'close_sise', 'scode': code}

        return json.dumps(payload)
    
    def generate_subscribe_msgs(self):
        return '|'.join([self.__generate_subscribe_msg(code) for code in self.__subscribes.keys()])

    @staticmethod
    def __generate_code(market_type: MarketType, sub_type: SubType, ticker) -> str:
        return f'{market_type}{sub_type}{ticker}'
    
    def __convert_keys(self, msg):
        return {self.__translate.get(key): value for key, value in msg.items() if key in self.__subscribes.keys()}

    def __process_msg(self, msg, callback):
        callback(self.__convert_keys(msg))

    async def __start_stream(self, callback):
        while True:
            try:
                async with websockets.connect(self.__wss_uri) as check_wss:
                    await check_wss.send(self.generate_subscribe_msgs())
                    self.__subscribes = {key: SubscribeStatus.SUBSCRIBED for key in self.__subscribes.keys()}
                
                while check_wss.open:
                    self.__process_msg(await check_wss.recv(), callback=callback)
            
            except (ConnectionClosedError, ConnectionClosedOK) as WebsocketError:
                logging.error(f'Wss error occurs reason: {WebsocketError}')
                self.__subscribes = {key: SubscribeStatus.UNSUBSCRIBED for key in self.__subscribes.keys()}
                await asyncio.sleep(1)

    def run(self, callback):
        task = asyncio.get_event_loop()

        try:
            task.run_until_complete(self.__start_stream(callback=callback))
        
        except KeyboardInterrupt:
            sys.exit()
