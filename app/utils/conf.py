# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 16:35
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


# SELECT_URL = get_env("SELECT_URL", "mysql+aiomysql://root:q1w2e3r4UMYSQL@130.252.27.39:3366/test")
# REDIS_URL = get_env("REDIS_URL", "redis://@130.252.27.39:6379/1")

SELECT_URL = get_env("SELECT_URL", "mysql+aiomysql://dev_user:6e7%40003%5E%25168acE@172.21.0.76:3306/jointpilot")
REDIS_URL = get_env("REDIS_URL", "redis://:Pwd_dDV6FqyxQ6q@172.21.16.15:6380/6")

KAFKA_URI = get_env("KAFKA_URI", "kafka-test:9092")
KAFKA_OPENAI_TOPIC = get_env("KAFKA_OPENAI_TOPIC", "openai-relay-v2-test")

LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
LOG_PATH = get_env("LOG_PATH", "logs")

OPEN_SENTRY = get_env("OPEN_SENTRY", "false")
SENTRY_NSD = get_env("SENTRY_NSD", "http://56ea72c9768c4528ba32a017a75ae207@172.21.0.33:9000/27")
if OPEN_SENTRY.lower() == 'true':
    OPEN_SENTRY = True
else:
    OPEN_SENTRY = False


SAVE_LOG = get_env("SAVE_LOG", "true")
if SAVE_LOG.lower() == 'true':
    SAVE_LOG = True
else:
    SAVE_LOG = False

