# -*- coding:utf-8 -*-

# @Time   : 2023/8/22 09:11
# @Author : huangkewei

import asyncio
import httpx
import orjson
import cachetools.func
API_TOKEN_TTL_SECONDS = 24 * 60 * 60

CACHE_TTL_SECONDS = API_TOKEN_TTL_SECONDS - 30


@cachetools.func.ttl_cache(maxsize=10, ttl=CACHE_TTL_SECONDS)
def get_api_token(ak, sk):
    auth_data = {
        "auth": {
            "identity": {
                "methods": [
                    "hw_ak_sk"
                ],
                "hw_ak_sk": {
                    "access": {
                        "key": ak
                    },
                    "secret": {
                        "key": sk
                    }
                }
            },
            "scope": {
                "project": {
                    "name": "cn-southwest-2"
                }
            }
        }
    }
    AUTH_URL = r'https://iam.myhuaweicloud.com/v3/auth/tokens'
    resp = httpx.post(AUTH_URL, json=auth_data, headers={"Content-Type": "application/json"})
    token = resp.headers.get('X-Subject-Token')
    if token:
        return token
    else:
        raise Exception(f"huawei Auth failed: {resp.status_code}")


def pangu_distribute(ak, sk, url, body):
    pangu_token = get_api_token(ak, sk)

    req_new = {
        'method': "POST",
        'url': url,
        'headers': {
            "Content-Type": "application/json",
            "X-Auth-Token": pangu_token
        },
        'data': orjson.dumps(body).decode(),
    }

    return req_new



