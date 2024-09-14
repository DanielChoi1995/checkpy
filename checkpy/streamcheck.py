import websockets
import json


class StreamCheckpy(object):
    def __init__(self, user_id, user_key):
        self.__user_id = user_id
        self.__user_key = user_key
        self.__wss_uri = 'wss://newmobile.koscom.co.kr'

        with open('checkpy/translate.json') as f:
            self.__translate = json.load(f)
