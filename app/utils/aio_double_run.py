# -*- coding:utf-8 -*-

# @Time   : 2023/8/25 13:06
# @Author : huangkewei

import asyncio
from functools import partial


async def aiter_bytes_new(first_value, aiter_iter):
    yield first_value
    async for chunk in aiter_iter:
        yield chunk


async def task1(aio_func, queue: asyncio.Queue):
    print('task1 init')

    message = await queue.get()
    if message == 'stop':
        print('task1 stop')
        return
    if message == 'start':
        print('task1 start')
        r = aio_func()
        first_value = await r.__anext__()
        r_new = aiter_bytes_new(
            first_value,
            r
        )
        print('task1 over')
        return 1, r_new


async def task2(aio_func, queue: asyncio.Queue):
    print('task2 init')

    message = await queue.get()
    if message == 'stop':
        print('task2 stop')
        return
    if message == 'start':
        print('task2 start')
        r = aio_func()
        first_value = await r.__anext__()
        r_new = aiter_bytes_new(
            first_value,
            r
        )
        print('task2 over')
        return 2, r_new


async def timeout_task(i):
    await asyncio.sleep(i)
    return -1, -1


async def double_run_task(aio_func1, aio_func2, timeout=10):
    """
    执行双发任务，当执行一个任务超时，会启动另外一个任务。

    :param aio_func1: 任务一
    :param aio_func2: 任务二
    :param timeout: 超时启动第二个任务
    :return:
    """

    q1 = asyncio.Queue()
    q2 = asyncio.Queue()
    t1 = asyncio.create_task(task1(aio_func1, q1))
    t2 = asyncio.create_task(task2(aio_func2, q2))
    t_timeout = asyncio.create_task(timeout_task(timeout))

    tasks = [t1, t2, t_timeout]
    await_tasks = asyncio.as_completed(tasks)

    await q1.put('start')

    coro = next(await_tasks)
    idx, result = await coro

    if idx != -1:
        await q2.put('stop')
        return idx, result

    await q2.put('start')

    coro = next(await_tasks)
    idx, result = await coro

    # 尝试关闭另一个任务
    if idx == 1:
        t2.cancel()
        cancel_task = t2
    else:
        t1.cancel()
        cancel_task = t1

    try:
        await cancel_task
    except asyncio.CancelledError:
        pass

    return idx, result


async def aio_func_test(i):
    await asyncio.sleep(i)
    return 'aio_func_test finish'


async def aio_double_test():
    # 测试双发
    t1 = partial(aio_func_test, i=3)
    t2 = partial(aio_func_test, i=3)
    s = await double_run_task(t1, t2, timeout=1)
    print(s)


async def main():
    await aio_double_test()
    await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
