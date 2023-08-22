# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 16:50
# @Author : huangkewei

# redis 缓存相关方法，异步。

import time
import orjson
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError
from app.utils.conf import REDIS_URL

r = aioredis.from_url(REDIS_URL)

add_keys_script = """  
local key = KEYS[1]
local current_time = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', key, '-inf', current_time)

local elements = cjson.decode(ARGV[1])
return redis.call('ZADD', key, unpack(elements))
"""
get_openai_key_script = """
local current_time = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', 'cooldown_pool', '-inf', current_time)
redis.call('ZREMRANGEBYSCORE', 'openai_key_pool', '-inf', current_time)

local keys = redis.call('ZDIFF', 2, 'openai_key_pool','cooldown_pool')
return keys
"""
auth_forward_key_script = """
local current_time = tonumber(redis.call('TIME')[1])
redis.call('ZREMRANGEBYSCORE', 'forward_key_pool', '-inf', current_time)

return redis.call('ZRANGE', 'forward_key_pool', 0, -1)
"""


class RedisConn:
    def __init__(self):
        self.r = None
        self.add_keys_sha = None
        self.get_openai_sha = None
        self.auth_forward_sha = None

    async def init_script_sha(self):
        self.add_keys_sha = await self.r.script_load(add_keys_script)
        self.get_openai_sha = await self.r.script_load(get_openai_key_script)
        self.auth_forward_sha = await self.r.script_load(auth_forward_key_script)

    async def init_redis(self):
        self.r = aioredis.from_url(REDIS_URL)
        await self.init_script_sha()

    def retry_decorator(self, retry_times=3, retry_exception=ConnectionError):
        """
        重试修饰器
        :param retry_times: 重试次数
        :param retry_exception: 重试异常, 单个异常或者元组
        :return:
        """

        def _decorator(func):
            async def _wrapper(*args, **kwargs):
                if not self.r:
                    await self.init_redis()

                for _ in range(retry_times):
                    try:
                        return await func(*args, **kwargs)
                    except retry_exception as e:
                        await self.init_redis()
                        continue
                raise e

            return _wrapper

        return _decorator

    async def add_key_to_redis_pool(self, pool_name, keys, timeout=60):
        @self.retry_decorator()
        async def _add_key_to_redis_pool(pool_name_, keys_, timeout_=60):
            """
            将keys添加到redis key池
            """
            if not keys_:
                return

            if isinstance(keys_, str):
                keys_ = [keys_]

            new_keys = []
            now_time = int(time.time() + timeout_)
            for key in keys_:
                new_keys.append(now_time)
                new_keys.append(key)
            keys_ = orjson.dumps(new_keys).decode()

            return await self.r.evalsha(self.add_keys_sha, 1, pool_name_, keys_)

        return await _add_key_to_redis_pool(pool_name, keys, timeout)

    async def add_key_to_cooldown_pool(self, keys, timeout=60):
        """
        将keys添加到冷却池
        """
        return await self.add_key_to_redis_pool(pool_name='cooldown_pool', keys=keys, timeout=timeout)

    async def add_key_to_openai_pool(self, keys, timeout=30):
        """
        将key添加openai api key缓存池
        """
        return await self.add_key_to_redis_pool(pool_name='openai_key_pool', keys=keys, timeout=timeout)

    async def add_key_to_forward_pool(self, keys, timeout=30):
        """
        将key添加openai api key缓存池
        """
        return await self.add_key_to_redis_pool(pool_name='forward_key_pool', keys=keys, timeout=timeout)

    async def get_openai_key(self):
        @self.retry_decorator()
        async def _get_openai_key():
            keys = await self.r.evalsha(self.get_openai_sha, 0)

            return keys

        return await _get_openai_key()

    async def get_forward_key(self):
        @self.retry_decorator()
        async def _get_forward_key():
            forward_key_lst = await self.r.evalsha(self.auth_forward_sha, 0)

            return forward_key_lst

        return await _get_forward_key()


redis_conn = RedisConn()

add_key_to_cooldown_pool = redis_conn.add_key_to_cooldown_pool
add_key_to_openai_pool = redis_conn.add_key_to_openai_pool
add_key_to_forward_pool = redis_conn.add_key_to_forward_pool
get_openai_key = redis_conn.get_openai_key
get_forward_key = redis_conn.get_forward_key


