# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 08:45
# @Author : huangkewei

import json
import time
import httpx
from httpx import Response
from fastapi import Request

from app.dependencies.context import OpenaiContext
from app.dependencies.distribute import distribute
from app.utils.helper import retry_decorator, send_error_msg
from app.utils.exception import OtherException, RequestException
from app.utils.redis_tools import add_key_to_cooldown_pool
from app.utils.logs import logger


@retry_decorator(retry_exception=RequestException)
async def chat_relay_server(request: Request, ctx: OpenaiContext) -> Response:
    """

    :param request:
    :param ctx:
    :return:
    """
    try:
        client = httpx.AsyncClient(http1=True, http2=False, timeout=10)
        req = client.build_request(**ctx.req_params)
        ctx.deal_time = time.perf_counter()

        r = await client.send(req, stream=True)
        logger.debug(f"forward_key: {ctx.forward_key}. 请求成功！")

        return r

    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"请求失败. {str(e)}")
        await send_error_msg(ctx, str(e))

        key = json.dumps(ctx.key)
        await add_key_to_cooldown_pool(key)
        await distribute(request, ctx)
        ctx.retry_times += 1

        raise RequestException(detail=e)

    except Exception as e:
        logger.error(f"请求失败. {str(e)}")
        await send_error_msg(ctx, str(e))

        raise OtherException(detail=e)

