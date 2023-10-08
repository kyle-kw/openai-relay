# -*- coding:utf-8 -*-

# @Time   : 2023/7/19 15:57
# @Author : huangkewei

import orjson
import logging
import warnings

from data_stream_kit import KafkaConsumer
from log_sync.sync_tool import deal_log_info

from log_sync.config import KAFKA_URI, KAFKA_OPENAI_TOPIC, KAFKA_GROUP_ID

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(filename)s func:%(funcName)s line: %(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

"""
消费代理请求的日志信息
"""


class KafkaConsumerLog:
    def __init__(self) -> None:
        super().__init__()
        self._batch_size = 100

    def process_call_batch(self, consumer, msgs, **kwargs):
        """
        消费者，批量消息处理
        """
        if not msgs:
            logger.info("topic暂无消息")
            return

        logger.info('批量消息获取成功 len:{} topic:{}'.format(len(msgs), consumer._topic))

        # 消息解析
        _datas_lst = []
        for msg in msgs:
            try:
                _data = orjson.loads(msg.value())
                _datas_lst.append(_data)

            except Exception as e:
                logger.error(f'the last error offset is {msg.offset()}. Exception:{e}')
                continue

        # 处理日志信息
        deal_log_info(_datas_lst)

    def run(self, kafka_uri=None, topic=None, group_id=None):
        """主函数入口"""

        logger.info('消费 topic:{}'.format(topic))

        with KafkaConsumer(bootstrap_servers=kafka_uri,
                           group_id=group_id,
                           callback_auto_commit=True,
                           callback=self.process_call_batch,
                           topic=topic,
                           ) as consumer:
            consumer.start(batch_size=self._batch_size)


def run():
    kafka_uri = KAFKA_URI
    topic = KAFKA_OPENAI_TOPIC
    group_id = KAFKA_GROUP_ID

    k = KafkaConsumerLog()
    k.run(
        kafka_uri=kafka_uri,
        topic=topic,
        group_id=group_id
    )


if __name__ == '__main__':
    run()
