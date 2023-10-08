# -*- coding:utf-8 -*-

# @Time   : 2023/9/8 14:48
# @Author : huangkewei

import logging
import redis
from log_sync.config import REDIS_URL


logger = logging.getLogger(__name__)
r = redis.from_url(REDIS_URL)


def redis_token_limit_set(key: str, mapping: dict):
    limit_key = 'limit_keys_token:' + key
    res = r.hset(limit_key, mapping=mapping)
    logger.info(f'数据添加redis完成，key:{key}, res: {res}')


def add_all_redis_token(token_datas: dict):
    if not token_datas:
        return

    for key, mapping in token_datas.items():
        try:
            redis_token_limit_set(key, mapping)
        except Exception as e:
            logger.error(f"添加redis使用token错误。{str(e)}")


def set_test():
    redis_token_limit_set(
        "bike:1",
        mapping={
            "model": "Deimos",
            "brand": "Ergonom",
            "type": "Enduro bikes",
            "price": 4972,
        },
    )


if __name__ == '__main__':
    set_test()
