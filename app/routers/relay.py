# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 08:45
# @Author : huangkewei

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.dependencies.distribute import distribute, azure_distribute
from app.dependencies.context import OpenaiContext
from app.services.relay import chat_relay_server
from app.utils.helper import aiter_bytes
from app.utils.logs import logger

router = APIRouter()


@router.post('/chat/completions')
@router.post('/v1/chat/completions')
async def chat_relay(request: Request, ctx: OpenaiContext = Depends(distribute, use_cache=False)):
    logger.info('chat: 开始转发请求服务。')
    r: httpx.Response = await chat_relay_server(request, ctx)
    aiter_byte = aiter_bytes(r, ctx)

    return StreamingResponse(
        aiter_byte,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )


@router.post('/embeddings')
@router.post('/v1/embeddings')
async def embedding_relay(request: Request, ctx: OpenaiContext = Depends(distribute, use_cache=False)):
    logger.info('embeddings: 开始转发请求服务。')
    r: httpx.Response = await chat_relay_server(request, ctx)
    aiter_byte = aiter_bytes(r, ctx)

    return StreamingResponse(
        aiter_byte,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )


@router.post('/openai/deployments/{deployment_id}/chat/completions')
@router.post('/v1/openai/deployments/{deployment_id}/chat/completions')
async def chat_azure_relay(
    deployment_id: str,
    request: Request,
    ctx: OpenaiContext = Depends(azure_distribute, use_cache=False)
):
    logger.info('azure chat: 开始转发请求服务。')
    r: httpx.Response = await chat_relay_server(request, ctx)
    aiter_byte = aiter_bytes(r, ctx)

    return StreamingResponse(
        aiter_byte,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )


@router.post('/openai/deployments/{deployment_id}/embeddings')
@router.post('/v1/openai/deployments/{deployment_id}/embeddings')
async def embedding_azure_relay(
    deployment_id: str,
    request: Request,
    ctx: OpenaiContext = Depends(azure_distribute, use_cache=False)
):
    logger.info('azure embeddings: 开始转发请求服务。')
    r: httpx.Response = await chat_relay_server(request, ctx)
    aiter_byte = aiter_bytes(r, ctx)

    return StreamingResponse(
        aiter_byte,
        status_code=r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(r.aclose),
    )


