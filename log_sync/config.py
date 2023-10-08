# -*- coding:utf-8 -*-

# @Time   : 2023/8/18 16:01
# @Author : huangkewei

from os import getenv


def get_env(env_name, default=None, required=False, arg_formatter=None):
    rv = getenv(env_name)
    if required and rv is None and default is None:
        raise ValueError("'{}' environment variable is required.".format(env_name))
    elif rv is None:
        print("'{}' uses default value: {}".format(env_name, default))
        rv = default
    if arg_formatter is not None:
        rv = arg_formatter(rv)
    return rv


INSERT_URL = get_env("INSERT_URL", "mysql+pymysql://root:q1w2e3r4UMYSQL@130.252.27.39:3366/test")

KAFKA_URI = get_env("KAFKA_URI", "kafka-test:9092")
KAFKA_OPENAI_TOPIC = get_env("KAFKA_OPENAI_TOPIC", "openai-relay-v2-test")
KAFKA_GROUP_ID = get_env("KAFKA_GROUP_ID", "test1")

REDIS_URL = get_env("REDIS_URL", "redis://@130.252.27.39:6379/1")

