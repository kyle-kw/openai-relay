# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 08:45
# @Author : huangkewei

from fastapi import APIRouter, Depends, Request, Path
from fastapi.responses import StreamingResponse

from app.dependencies.distribute import distribute
from app.dependencies.context import OpenaiContext
from app.services.relay import chat_relay_server
from app.utils.logs import logger

router = APIRouter()


@router.post("/{prefix:path}/completions")
async def chat_relay(request: Request,
                     prefix: str = Path(...),
                     ctx: OpenaiContext = Depends(distribute, use_cache=False)):

    logger.info('chat: 开始转发请求服务。')
    r = await chat_relay_server(request, ctx)

    return StreamingResponse(
        r,
        status_code=200,
        media_type='text/event-stream',
    )


@router.post("/{prefix:path}/embeddings")
async def embedding_relay(request: Request,
                          prefix: str = Path(...),
                          ctx: OpenaiContext = Depends(distribute, use_cache=False)):
    logger.info('embeddings: 开始转发请求服务。')
    r = await chat_relay_server(request, ctx)

    return StreamingResponse(
        r,
        status_code=200,
        media_type='text/event-stream',
    )

