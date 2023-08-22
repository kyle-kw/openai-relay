# -*- coding:utf-8 -*-

# @Time   : 2023/8/18 16:02
# @Author : huangkewei

from sqlalchemy import BigInteger, Column, Integer, String, text, Text, Float
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


class OpenaiRelayLogInfo(Base):
    __tablename__ = 'openai_relay_log_info'

    record_pk = Column(BigInteger, primary_key=True)
    forward_key = Column(String(100), nullable=False, comment='验证使用key')
    req_type = Column(String(100), server_default=text("''"), comment='请求类型')
    model_name = Column(String(100), server_default=text("''"), comment='请求model名字')
    req_prompt = Column(Text, comment='请求prompt')
    res_content = Column(Text, comment='返回内容')
    first_time = Column(Float, server_default=text("'0'"), comment='请求第一次返回内容用时')
    all_time = Column(Float, server_default=text("'0'"), comment='请求整体用时')
    return_rate = Column(Float, server_default=text("'0'"), comment='吐字/s')
    retry_times = Column(TINYINT, server_default=text("'0'"), comment='重试次数')
    req_token = Column(Integer, server_default=text("'0'"), comment='请求使用token数')
    res_token = Column(Integer, server_default=text("'0'"), comment='响应使用token数')
    log_info = Column(Text, nullable=False, comment='日志信息')
    create_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment='生成时间')


class OpenaiRelayLogInfoError(Base):
    __tablename__ = 'openai_relay_log_info_error'

    record_pk = Column(BigInteger, primary_key=True)
    forward_key = Column(String(100), nullable=False, comment='验证使用key')
    openai_key = Column(String(100), nullable=False, comment='请求使用key')
    req_type = Column(String(100), server_default=text("''"), comment='请求类型')
    model_name = Column(String(100), server_default=text("''"), comment='请求model名字')
    req_prompt = Column(Text, comment='请求prompt')
    log_info = Column(Text, nullable=False, comment='日志信息')
    error_info = Column(Text, nullable=False, comment='错误信息')
    create_time = Column(DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment='生成时间')


