# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 15:10
# @Author : huangkewei

from fastapi import Request, Depends

from app.utils.logs import logger
from app.utils.cache import get_one_key
from app.utils.distribute import main_distribute
from app.utils.helper import parse_request, choose_one_key
from app.dependencies.context import OpenaiContext
from app.dependencies.token_auth import token_auth


async def distribute(
    request: Request,
    ctx: OpenaiContext = Depends(token_auth, use_cache=False),
) -> OpenaiContext:
    """
    从缓存中读取可用key
    :param request:
    :param ctx:

    :return:
    """
    params = await parse_request(request)
    keys = await get_one_key(ctx.key_used)

    key = choose_one_key(keys, params, ctx.model_map)

    # 记录key相关信息，保持上下文。
    api_key = key.get('api_key')
    for one in keys:
        if one['api_key'] == api_key:
            ctx.key = one
            break
    ctx.openai_key = api_key
    ctx.key_type = key.get('api_type', '')
    ctx.model_name = key.get('model', '')
    if '16k' in ctx.model_name:
        ctx.timeout += 5

    logger.info('获取到可用的key。')
    ctx.req_params = main_distribute(key, params)

    return ctx

