# -*- coding:utf-8 -*-

# @Time   : 2023/8/21 10:45
# @Author : huangkewei

from log_sync.models import AuthOpenaiApiKeysV2
from data_stream_kit import SessionContextManager, sqlalchemy_data_commit

url = 'mysql+pymysql://root:123456@localhost:3306/openai'
db_session = SessionContextManager(url=url)


@db_session
def insert_open_ai_key(data_lst):
    stats = sqlalchemy_data_commit(
        AuthOpenaiApiKeysV2,
        data_lst,
        auto_commit=True,
    )
    print(f"添加数据状态： {stats}")


def insert_openai_keys():
    keys = [
        {
            'api_key': 'sk-.....',  # # key
            'key_type': 'chat',  # key类型
            'key_used': 'any',  # key权限
            'api_base': '....',
            'api_type': 'eg. azure',
            'api_version': 'eg. 2023-05-15',
            'model': 'eg. gpt-35-turbo,gpt-35-turbo-16k',  # 可写多个支持的model，但是必须和engine一一对应。
            'engine': 'eg. test-gpt-35-turbo,test-gpt-35-turbo-16k',
        },
        # ....
    ]
    insert_open_ai_key(keys)


if __name__ == '__main__':
    insert_openai_keys()

