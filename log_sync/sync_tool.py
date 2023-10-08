# -*- coding:utf-8 -*-

# @Time   : 2023/7/19 16:02
# @Author : huangkewei

import logging
import base64
import orjson
import tiktoken
import numpy as np
from orjson import JSONDecodeError
from sqlalchemy import select
from httpx._decoders import LineDecoder
from data_stream_kit import SessionContextManager, sqlalchemy_data_commit, session, \
    sqlalchemy_result_format, sqlalchemy_update_data_by_case

from log_sync.models import AuthOpenaiApiKeysV2, AuthForwardApiKeysV2, OpenaiRelayLogInfo, \
    OpenaiRelayLogInfoError
from log_sync.config import INSERT_URL
from log_sync.redis_tools import add_all_redis_token
from collections import defaultdict

logger = logging.getLogger(__name__)
db_session = SessionContextManager(url=INSERT_URL, alias='insert')
decoder = LineDecoder()


def token_count(text, model_name='gpt-3.5-turbo'):
    """
    计算一段文本的使用的token数
    :param text:
    :param model_name:
    :return:
    """
    if not text:
        return 0

    enc = tiktoken.encoding_for_model(model_name)

    tokens = len(enc.encode(text))
    return tokens


def decode_embedding(embedding):
    p = np.frombuffer(
        base64.b64decode(embedding), dtype="float32"
    ).tolist()

    return p


@db_session
def query_openai_data_token(key_lst):
    if not key_lst:
        return

    m = AuthOpenaiApiKeysV2
    select_sql = (
        select([m.api_key, m.req_token_cnt, m.res_token_cnt]).
        where(m.api_key.in_(key_lst))
    )
    res = session.execute(select_sql)
    res = sqlalchemy_result_format(res)

    return res


@db_session
def update_openai_data_token(data_lst):
    if not data_lst:
        return

    key_lst = [d['api_key'] for d in data_lst]
    old_res = query_openai_data_token(key_lst)
    old_map = {
        d['api_key']: d
        for d in old_res
    }

    for data in data_lst:
        api_key = data['api_key']
        old_data = old_map.get(api_key)
        data['req_token_cnt'] += old_data['req_token_cnt']
        data['res_token_cnt'] += old_data['res_token_cnt']

    status = sqlalchemy_update_data_by_case(
        AuthOpenaiApiKeysV2,
        data_lst=data_lst,
        update_key='api_key',
        auto_commit=True
    )
    logger.info(f'{AuthOpenaiApiKeysV2.__tablename__} 更新token状态：{status}')


@db_session
def query_forward_data_token(key_lst):
    if not key_lst:
        return

    m = AuthForwardApiKeysV2
    select_sql = (
        select([m.forward_key, m.req_token_cnt, m.res_token_cnt]).
        where(m.forward_key.in_(key_lst))
    )
    res = session.execute(select_sql)
    res = sqlalchemy_result_format(res)

    return res


@db_session
def update_forward_data_token(data_lst):
    if not data_lst:
        return

    key_lst = [d['forward_key'] for d in data_lst]
    old_res = query_forward_data_token(key_lst)
    old_map = {
        d['forward_key']: d
        for d in old_res
    }

    for data in data_lst:
        api_key = data['forward_key']
        old_data = old_map.get(api_key)
        data['req_token_cnt'] += old_data['req_token_cnt']
        data['res_token_cnt'] += old_data['res_token_cnt']

    status = sqlalchemy_update_data_by_case(
        AuthForwardApiKeysV2,
        data_lst=data_lst,
        update_key='forward_key',
        auto_commit=True
    )
    logger.info(f'{AuthForwardApiKeysV2.__tablename__} 更新token状态：{status}')


@db_session
def insert_log_info(data_lst):
    if not data_lst:
        return

    stats = sqlalchemy_data_commit(
        OpenaiRelayLogInfo,
        data_lst=data_lst,
        auto_commit=True,
    )
    logger.info(f'添加日志数据状态：{stats}')


@db_session
def insert_error_log_info(error_data_lst):
    if not error_data_lst:
        return

    stats = sqlalchemy_data_commit(
        OpenaiRelayLogInfoError,
        data_lst=error_data_lst,
        auto_commit=True,
    )
    logger.info(f'添加错误日志数据状态：{stats}')


def parse_chat_completions(bytes_):
    """
    解析chat接口返回的数据，兼容流式以及非流式

    :param bytes_:
    :return:
    """
    if isinstance(bytes_, bytes):
        txt_lines = decoder.decode(bytes_.decode("utf-8"))
    else:
        txt_lines = decoder.decode(bytes_)
    if not txt_lines:
        return {}
    line0 = txt_lines[0]
    target_info = dict()
    _start_token = "data: "
    if line0.startswith(_start_token):
        is_stream = True
        line0 = orjson.loads(line0[len(_start_token):])
        msg = line0["choices"][0]["delta"]
    else:
        is_stream = False
        line0 = orjson.loads("".join(txt_lines))
        msg = line0["choices"][0]["message"]

    target_info["created"] = line0.get("created", '')
    target_info["id"] = line0.get("id", '')
    target_info["model"] = line0.get("model", '')
    target_info["role"] = msg.get('role', '')
    target_info['usage'] = msg.get('usage', {})
    target_info["content"] = msg.get("content", "")
    if not is_stream:
        return target_info

    # loop for stream
    for line in txt_lines[1:]:
        if line in ("", "\n", "\n\n"):
            continue
        elif line.startswith(_start_token):
            target_info["content"] += parse_iter_line_content(
                line[len(_start_token):]
            )
        else:
            logger.warning(f"line not startswith data: {line}")

    return target_info


def parse_iter_line_content(line: str):
    """
    解析一行数据

    :param line:
    :return:
    """
    try:
        line_dict = orjson.loads(line)
        return line_dict["choices"][0]["delta"]["content"]
    except JSONDecodeError:
        return ""
    except KeyError:
        return ""


def parse_embeddings(bytes_: bytes):
    """
    解析embedding接口响应的数据

    :param bytes_:
    :return:
    """
    res = orjson.loads(bytes_)
    return res


def deal_error_log(one):
    error = one['error']

    ctx: dict = orjson.loads(one['ctx'])
    forward_key = ctx['forward_key']
    openai_key = ctx['openai_key']
    model_name = ctx['model_name']

    log_info = orjson.dumps(ctx).decode()

    req_params = ctx['req_params']

    req_type = ''
    req_text = ''

    if model_name in ['ERNIE-Bot', 'ERNIE-Bot-turbo', 'BLOOMZ-7B']:
        req_type = 'chat'

        req_data = req_params.get('json') or {}
        req_content = req_data.get('messages') or []
        req_text = '\n'.join([d['content'] for d in req_content])

    elif model_name in ['pangu-chat', 'pangu-text']:
        req_type = 'chat'
        prompt = req_params.get('prompt')
        if prompt is not None:
            req_text = prompt
        else:
            req_data = req_params.get('data') or '{}'
            req_data = orjson.loads(req_data)
            req_content = req_data.get('messages') or []
            req_text = '\n'.join([d['content'] for d in req_content])

    elif model_name in ['general', 'generalv2']:
        req_type = 'chat'
        question = req_params.get('question') or []
        req_text = '\n'.join([d['content'] for d in question])

    elif model_name in ['chatglm_pro', 'chatglm_std',
                        'chatglm_lite', 'chatglm_lite_32k']:
        req_type = 'chat'
        req_data = req_params.get('json') or {}
        req_content = req_data.get('prompt') or []
        req_text = '\n'.join([d['content'] for d in req_content])

    elif model_name in ['gpt-35-turbo', 'gpt-35-turbo-16k',
                        'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
                        'jfh-bot-32k-chat', 'jfh-coder-34b',
                        'jfh-bot-13b-chat', 'jfh-bot-7b']:
        req_type = 'chat'

        req_data = req_params.get('json')
        req_content = req_data.get('messages')
        req_text = '\n'.join([d['content'] for d in req_content])

    elif model_name in ['qwen-turbo', 'qwen-plus']:
        req_type = 'chat'
        question = req_params.get('input').get('messages') or []
        req_text = '\n'.join([d['content'] for d in question])

    elif model_name in ['text-embedding-ada-002']:
        req_type = 'embedding'

    else:
        req_type = 'chat'

        req_data = req_params.get('json')
        req_content = req_data.get('messages')
        req_text = '\n'.join([d['content'] for d in req_content])

    error_log = {
        'forward_key': forward_key,
        'openai_key': openai_key,
        'req_type': req_type,
        'model_name': model_name,
        'req_prompt': req_text,
        'log_info': log_info,
        'error': error,
    }

    return error_log


def _deal_log_info(log_lst):
    """
    prompt_tokens
    completion_tokens
    total_tokens
    """
    if not log_lst:
        return

    update_openai = defaultdict(list)
    update_forward = defaultdict(list)
    log_data = []
    error_log_data = []

    for one in log_lst:
        try:
            if one.get('error') is not None:
                # 若存在error，错误日志
                error_log = deal_error_log(one)
                error_log_data.append(error_log)
                continue

            forward_key = one['forward_key']
            openai_key = one['openai_key']
            req_params = one['req_params']
            model_name = one['model_name']
            res_content = one['res_content'].encode()

            req_token_cnt = 0
            res_token_cnt = 0
            req_type = ''
            res_text = ''
            req_text = ''

            if model_name in ['ERNIE-Bot', 'ERNIE-Bot-turbo', 'BLOOMZ-7B']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                req_data = req_params.get('json') or {}
                req_content = req_data.get('messages') or []
                req_text = '\n'.join([d['content'] for d in req_content])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['pangu-chat', 'pangu-text']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                req_data = req_params.get('data') or '{}'
                req_data = orjson.loads(req_data)
                prompt = req_data.get('prompt')
                if prompt is not None:
                    req_text = prompt
                else:
                    req_content = req_data.get('messages') or []
                    req_text = '\n'.join([d['content'] for d in req_content])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['general', 'generalv2']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                question = req_params.get('question') or []
                req_text = '\n'.join([d['content'] for d in question])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['chatglm_pro', 'chatglm_std',
                                'chatglm_lite', 'chatglm_lite_32k']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                req_data = req_params.get('json') or {}
                req_content = req_data.get('prompt') or []
                req_text = '\n'.join([d['content'] for d in req_content])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['gpt-35-turbo', 'gpt-35-turbo-16k',
                                'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
                                'jfh-bot-32k-chat', 'jfh-coder-34b',
                                'jfh-bot-13b-chat', 'jfh-bot-7b']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                req_data = req_params.get('json')
                req_content = req_data.get('messages')
                req_text = '\n'.join([d['content'] for d in req_content])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['qwen-turbo', 'qwen-plus']:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                question = req_params.get('input').get('messages') or []
                req_text = '\n'.join([d['content'] for d in question])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            elif model_name in ['text-embedding-ada-002']:
                req_type = 'embedding'
                req_data = req_params.get('json')
                input_text = req_data.get('input')

                if isinstance(input_text, list) and isinstance(input_text[0], list):
                    req_token_cnt = sum([len(d) for d in input_text])
                elif isinstance(input_text, list) and isinstance(input_text[0], str):
                    input_text = ''.join(input_text)
                    req_token_cnt = token_count(input_text, model_name='text-embedding-ada-002')
                else:
                    req_token_cnt = token_count(input_text, model_name='text-embedding-ada-002')

                res_token_cnt = 0

            else:
                req_type = 'chat'
                res_content = parse_chat_completions(res_content)
                res_text = res_content.get('content', '')

                req_data = req_params.get('json')
                req_content = req_data.get('messages')
                req_text = '\n'.join([d['content'] for d in req_content])

                res_token_cnt = token_count(res_text)
                req_token_cnt = token_count(req_text)

            deal_time = one['deal_time']
            first_time = one['first_time']
            all_time = one['all_time']
            retry_times = one['retry_times']

            update_openai[openai_key].append((req_token_cnt, res_token_cnt, first_time))
            update_forward[forward_key].append((req_token_cnt, res_token_cnt, first_time))

            first_return_time = round(first_time - deal_time, 4)
            all_return_time = round(all_time - deal_time, 4)
            return_rate = 0.0

            if req_type == 'chat':
                return_rate = round(len(res_text) / all_return_time, 4)

            log_data.append({
                'forward_key': forward_key,
                'req_type': req_type,
                'model_name': model_name,
                'req_prompt': req_text,
                'res_content': res_text,
                'first_time': first_return_time,
                'all_time': all_return_time,
                'return_rate': return_rate,
                'retry_times': retry_times,
                'req_token': req_token_cnt,
                'res_token': res_token_cnt,
                'log_info': orjson.dumps(one).decode(),
            })
        except Exception as e:
            logger.exception(e)

    update_openai_all = []
    for openai_key, token_lst in update_openai.items():
        update_openai_all.append({
            'api_key': openai_key,
            'req_token_cnt': sum([d[0] for d in token_lst]),
            'res_token_cnt': sum([d[1] for d in token_lst]),
        })

    update_forward_all = []
    for forward_key, token_lst in update_forward.items():
        update_forward_all.append({
            'forward_key': forward_key,
            'req_token_cnt': sum([d[0] for d in token_lst]),
            'res_token_cnt': sum([d[1] for d in token_lst]),
        })

    set_token_limit = defaultdict(dict)
    for openai_key, token_lst in update_openai.items():
        for one_record in token_lst:
            set_token_limit[openai_key][str(int(one_record[2]))] = one_record[0] + one_record[1]
    for forward_key, token_lst in update_forward.items():
        for one_record in token_lst:
            set_token_limit[forward_key][str(int(one_record[2]))] = one_record[0] + one_record[1]

    add_all_redis_token(set_token_limit)
    insert_log_info(log_data)
    insert_error_log_info(error_log_data)
    update_openai_data_token(update_openai_all)
    update_forward_data_token(update_forward_all)

    logger.info('处理完成。')


def deal_log_info(log_lst):
    try:
        _deal_log_info(log_lst)
    except Exception as e:
        logger.exception(e)
