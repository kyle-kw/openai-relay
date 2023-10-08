# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 15:30
# @Author : huangkewei

import random
import orjson
from typing import List, Dict
from sqlalchemy import select
from data_stream_kit import AIOSessionManager, sqlalchemy_result_format

from app.utils.logs import logger
from app.utils.conf import SELECT_URL
from app.utils.sqlalchemy_models import AuthOpenaiApiKeysV2, AuthForwardApiKeysV2, \
    AuthForwardKeyModelMapping
from app.utils.exception import AuthException, RequestException, TokenLimitException
from app.utils.redis_tools import get_openai_key, add_key_to_openai_pool, get_forward_key, \
    add_key_to_forward_pool, limit_keys_token

Session = AIOSessionManager(url=SELECT_URL)


async def query_all_keys():
    m = AuthOpenaiApiKeysV2
    select_sql = (
        select([m]).
        where(m.status == 0)
    )

    async with Session() as session:
        res = await session.execute(select_sql)
        res = sqlalchemy_result_format(res)
        logger.debug('查询到所有可用的api key')

        return res


async def query_forward_all_keys():
    m = AuthForwardApiKeysV2
    select_sql = (
        select([m]).
        where(m.status == 0)
    )

    async with Session() as session:
        res = await session.execute(select_sql)
        res = sqlalchemy_result_format(res)
        logger.debug('查询到所有可用的forward key')

        return res


async def query_forward_all_model_mapping():
    m = AuthForwardKeyModelMapping
    select_sql = (
        select([m]).
        where(m.status == 0)
    )

    async with Session() as session:
        res = await session.execute(select_sql)
        res = sqlalchemy_result_format(res)
        logger.debug('查询所有可用的 forward model 映射。')

        return res


def keys_format(keys: List[Dict]):

    random.shuffle(keys)

    keys_f: List[str] = []
    for key in keys:
        tmp = {
            'api_key': key['api_key'],
            'key_type': key['key_type'],
            'key_used': key['key_used'],
            'api_base': key['api_base'],
            'api_type': key['api_type'],
            'api_version': key['api_version'],
            'model': key['model'],
            'engine': key['engine'],
            'limit_token': key['limit_token'],
        }
        tmp = orjson.dumps(tmp).decode()
        keys_f.append(tmp)

    return keys_f


async def get_one_key(role=None):

    if role is None:
        role = {'any'}
    if isinstance(role, str):
        role = {role}

    keys = await get_openai_key()
    if not keys:
        keys = await query_all_keys()
        keys_f = keys_format(keys)
        status = await add_key_to_openai_pool(keys_f)
        log_msg = '插入redis成功' if status else '插入redis失败'
        logger.debug(f'status: {status}. {log_msg}')
        keys = await get_openai_key()

    if not keys:
        logger.error('没有可用的openai keys!')
        raise RequestException(detail='没有可用的openai keys!')

    keys: List[Dict] = [orjson.loads(k) for k in keys]

    keys = [
        d for d in keys
        if set(d['key_used'].split(',')) & role
    ]

    return keys


def auth_forward_key_effective(key_lst, forward_key):
    for one in key_lst:
        key = one.get('forward_key')
        if key == forward_key:
            return one

    return -1


def forward_keys_format(keys: List[Dict], model_maps: List[Dict]):

    random.shuffle(keys)
    model_map_dict = {}
    for one_map in model_maps:
        forward_key = one_map['forward_key']
        old_model = one_map['old_model']
        new_model = one_map['new_model']

        model_map_dict.setdefault(forward_key, {})
        model_map_dict[forward_key][old_model] = new_model

    keys_f: List[str] = []
    for key in keys:
        model_map = model_map_dict.get(key['forward_key'], {})
        tmp = {
            'forward_key': key['forward_key'],
            'key_used': key['key_used'],
            'model_map': model_map,
        }
        tmp = orjson.dumps(tmp).decode()
        keys_f.append(tmp)

    return keys_f


async def auth_forward(forward_key):
    forward_keys = await get_forward_key()
    if not forward_keys:
        forward_keys = await query_forward_all_keys()
        forward_model_maps = await query_forward_all_model_mapping()
        forward_keys_f = forward_keys_format(forward_keys, forward_model_maps)
        status = await add_key_to_forward_pool(forward_keys_f)
        log_msg = '插入redis成功' if status else '插入redis失败'
        logger.debug(f'status: {status}. {log_msg}')

        forward_keys = await get_forward_key()

    if not forward_keys:
        logger.error('没有可用的forward keys!')
        raise AuthException(detail='没有可用的forward keys!')

    forward_keys: List[Dict] = [orjson.loads(k) for k in forward_keys]
    key = auth_forward_key_effective(forward_keys, forward_key)

    if key == -1:
        logger.error('验证forward key失败!')
        raise AuthException(detail='验证forward key失败!')

    return key


async def auth_openai_token_limit(key):
    # 验证key有没有限流

    api_key = key['api_key']
    limit_token = key['limit_token'] * 1000

    status = await limit_keys_token(api_key, limit_token)

    if status == 0:
        raise TokenLimitException()

