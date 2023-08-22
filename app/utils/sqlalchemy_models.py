# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 15:32
# @Author : huangkewei

# sqlalchemy 相关model，用于数据库查询

from sqlalchemy import BigInteger, Column, Integer, String, text
from sqlalchemy.dialects.mysql import DATETIME, TINYINT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AuthOpenaiApiKeysV2(Base):
    __tablename__ = 'auth_openai_api_keys_v2'

    record_pk = Column(BigInteger, primary_key=True)
    api_key = Column(String(1000), nullable=False, unique=True, comment='key')
    key_type = Column(String(1000), nullable=False, comment='key 用处类型')
    key_used = Column(String(1000), server_default=text("'any'"), comment='key 允许使用的角色， any')
    api_base = Column(String(1000), server_default=text("''"), comment='api base 地址')
    api_type = Column(String(1000), server_default=text("''"), comment='api key 类型')
    api_version = Column(String(100), server_default=text("''"), comment='api 版本')
    model = Column(String(1000), server_default=text("''"), comment='模型类型')
    engine = Column(String(1000), server_default=text("''"), comment='引擎类型')
    limit_token = Column(Integer, server_default=text("'200'"), comment='每分钟最大使用token数。单位：k')
    req_token_cnt = Column(Integer, server_default=text("'0'"), comment='请求使用token数')
    res_token_cnt = Column(Integer, server_default=text("'0'"), comment='响应使用token数')
    status = Column(TINYINT, nullable=False, server_default=text("'0'"), comment='key状态')
    subscribe = Column(String(100), server_default=text("''"), comment='订阅类型')
    available_area = Column(String(100), server_default=text("''"), comment='可用区')
    create_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment='生成时间')
    update_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"), comment='更新时间')


class AuthForwardApiKeysV2(Base):
    __tablename__ = 'auth_forward_api_keys_v2'

    record_pk = Column(BigInteger, primary_key=True)
    forward_key = Column(String(1000), unique=True, comment='鉴权key')
    key_used = Column(VARCHAR(1000), server_default=text("'any'"), comment='key 用户')
    model = Column(VARCHAR(1000), server_default=text("'any'"), comment='key 用户')
    req_token_cnt = Column(Integer, server_default=text("'0'"), comment='请求使用的token数')
    res_token_cnt = Column(Integer, server_default=text("'0'"), comment='响应使用的token数')
    status = Column(TINYINT, nullable=False, server_default=text("'0'"))
    create_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment='生成时间')
    update_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"), comment='更新时间')


class AuthForwardKeyModelMapping(Base):
    __tablename__ = 'auth_forward_key_model_mapping'

    record_pk = Column(BigInteger, primary_key=True)
    forward_key = Column(String(100), nullable=False, comment='鉴权key')
    old_model = Column(VARCHAR(100), comment='源model')
    new_model = Column(VARCHAR(100), comment='新model')
    status = Column(TINYINT, nullable=False, server_default=text("'0'"))
    create_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment='生成时间')
    update_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"), comment='更新时间')

