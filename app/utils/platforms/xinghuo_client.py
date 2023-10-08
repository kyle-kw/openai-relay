# -*- coding:utf-8 -*-

# @Time   : 2023/9/6 13:27
# @Author : huangkewei

import asyncio
import websockets
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time


class WsParam(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.Spark_url + '?' + urlencode(v)

        return url


def gen_params(appid, domain, question, chat_param=None):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "random_threshold": 0.0,
                "max_tokens": 3000,
                "auditing": "default",
                "temperature": 0.1,
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    if chat_param is not None:
        data['parameter']['chat'].update(chat_param)

    return data


async def xunfei_chat(appid, api_key, api_secret, spark_url, domain, question, chat_param=None):

    wsParam = WsParam(appid, api_key, api_secret, spark_url)
    wsUrl = wsParam.create_url()

    async with websockets.connect(wsUrl) as websocket:
        data = json.dumps(gen_params(appid, domain, question, chat_param))

        await websocket.send(data)

        while True:
            try:
                message = await websocket.recv()

                yield message
            except websockets.ConnectionClosedOK:
                break
            except websockets.WebSocketException as e:
                raise e
            except Exception as e:
                raise e



