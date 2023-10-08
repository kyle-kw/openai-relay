# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 09:08
# @Author : huangkewei

import time
from fastapi import Request, Depends

from app.utils.logs import logger
from app.utils.cache import auth_forward
from app.utils.exception import AuthException
from app.dependencies.context import get_context, OpenaiContext


async def token_auth(
        request: Request,
        ctx: OpenaiContext = Depends(get_context, use_cache=False)
):
    ctx.start_time = time.time()

    key = request.headers.get('api-key') or request.headers.get('Authorization')
    if not key:
        logger.error('请求头缺少Authorization/api-key!')
        raise AuthException(detail='请求头缺少Authorization/api-key！')

    if key.startswith('Bearer '):
        key = key[7:]

    key_info = await auth_forward(key)

    key_used = key_info.get('key_used').split(',')
    ctx.key_used = {d.strip() for d in key_used if d.strip()}

    ctx.forward_key = key
    ctx.model_map = key_info.get('model_map', {})

    return ctx
