# -*- coding:utf-8 -*-

# @Time   : 2023/8/21 10:45
# @Author : huangkewei

import string
import random
from log_sync.models import AuthForwardApiKeysV2
from data_stream_kit import SessionContextManager, sqlalchemy_data_commit

url = 'mysql+pymysql://root:123456@localhost:3306/openai'
db_session = SessionContextManager(url=url)
letters = string.ascii_letters + string.digits


def generate_random_string(length):
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def gen_forward():
    """
    生成forward key
    """
    rand_str = generate_random_string(47)
    key = 'fd-' + rand_str

    return key


@db_session
def insert_forward_key(datas):
    stats = sqlalchemy_data_commit(
        AuthForwardApiKeysV2,
        data_lst=datas,
        auto_commit=True,
    )
    print(f"添加数据状态： {stats}")


def add_forward_key():
    forward_key = gen_forward()
    print(forward_key)
    datas = [{
        'forward_key': forward_key,
        'key_used': 'any',
        'model': 'any',
    }]
    insert_forward_key(datas)


if __name__ == '__main__':
    # k = gen_forward()
    # print(k)

    add_forward_key()
