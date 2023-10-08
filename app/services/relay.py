# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 08:45
# @Author : huangkewei

import json
import time
import httpx
from fastapi import Request

from app.dependencies.context import OpenaiContext
from app.dependencies.distribute import distribute
from app.utils.helper import aio_retry_decorator, send_error_msg
from app.utils.exception import OtherException, RequestException, TokenLimitException
from app.utils.redis_tools import add_key_to_cooldown_pool
from app.utils.logs import logger
from app.utils.platforms import xunfei_chat
from app.utils.cache import auth_openai_token_limit
from app.utils.helper import copy_ctx
from app.utils.aio_double_run import double_run_task
from app.utils.helper import aiter_bytes
from functools import partial
from copy import deepcopy


async def chat_relay_server(request: Request, ctx: OpenaiContext):
    # 支持超时双发调用
    new_ctx = deepcopy(ctx)
    new_ctx.double_run_task = 1
    task1 = partial(chat_relay_server_, request=request, ctx=ctx)
    task2 = partial(chat_relay_server_, request=request, ctx=new_ctx)
    idx, r = await double_run_task(task1, task2, timeout=3)

    if idx == 2:
        # 将新的上下文保存下来
        copy_ctx(ctx, new_ctx)

    return r


@aio_retry_decorator(retry_exception=(RequestException, OtherException, TokenLimitException))
async def chat_relay_server_(request: Request, ctx: OpenaiContext):
    """

    :param request:
    :param ctx:
    :return:
    """
    try:
        if ctx.double_run_task == 1:
            ctx.double_run_task = 2
            await distribute(request, ctx)

        await auth_openai_token_limit(ctx.key)

        async with httpx.AsyncClient(http1=True, http2=False, timeout=ctx.timeout) as client:
            if ctx.key_type == 'xunfei':
                # 讯飞api是websocket请求
                ctx.deal_time = time.time()

                r = xunfei_chat(**ctx.req_params)

                logger.debug(f"forward_key: {ctx.forward_key}. 请求成功！")

                aiter_byte = aiter_bytes(r, ctx)

                async for chunk in aiter_byte:
                    yield chunk

            else:
                req = client.build_request(**ctx.req_params)
                ctx.deal_time = time.time()
                r = await client.send(req, stream=True)
                if r.status_code != 200:
                    raise RequestException(detail="请求失败！")

                logger.debug(f"forward_key: {ctx.forward_key}. 请求成功！")

                aiter_byte = aiter_bytes(r, ctx)

                async for chunk in aiter_byte:
                    yield chunk

                await r.aclose()

    except TokenLimitException as e:
        logger.error(f"key限流. {ctx.openai_key}")

        key = json.dumps(ctx.key)
        await add_key_to_cooldown_pool(key)
        await distribute(request, ctx)
        ctx.retry_times += 1

        raise TokenLimitException()

    except RequestException as e:
        logger.error(e.detail)
        await send_error_msg(ctx, e.detail)

        key = json.dumps(ctx.key)
        await add_key_to_cooldown_pool(key)
        await distribute(request, ctx)
        ctx.retry_times += 1

        raise e

    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"请求超时. {str(e)}")
        await send_error_msg(ctx, '请求超时')

        key = json.dumps(ctx.key)
        await add_key_to_cooldown_pool(key)
        await distribute(request, ctx)
        ctx.retry_times += 1
        ctx.timeout += 5

        raise RequestException(detail=e)

    except Exception as e:
        logger.error(f"请求失败. {str(e)}")
        await send_error_msg(ctx, str(e))

        key = json.dumps(ctx.key)
        await add_key_to_cooldown_pool(key)
        await distribute(request, ctx)
        ctx.retry_times += 1

        raise OtherException(detail=str(e))
