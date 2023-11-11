# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - 监控平台 (BlueKing - Monitor) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
import logging
from typing import Dict, List, Optional

import kafka
from kafka.admin import KafkaAdminClient, NewPartitions

from metadata import config, models
from metadata.utils import consul_tools

logger = logging.getLogger("metadata")


def modify_transfer_cluster_id(bk_data_id: int, transfer_cluster_id: str) -> Dict:
    """更改数据源使用的transfer 集群 ID"""
    qs = models.DataSource.objects.filter(bk_data_id=bk_data_id)
    qs.update(transfer_cluster_id=transfer_cluster_id)
    record = qs.first()
    # 刷新consul
    record.refresh_consul_config()
    return {"bk_data_id": record.bk_data_id, "transfer_cluster_id": record.transfer_cluster_id}


def modify_kafka_cluster_id(bk_data_id: int, topic: Optional[str] = None, partition: Optional[int] = None):
    # 获取 kafka 集群信息
    record = models.DataSource.objects.filter(bk_data_id=bk_data_id).first()
    if not record:
        raise Exception("data id: %s not found", bk_data_id)
    mq_cluster = record.mq_cluster
    kafka_hosts = "{}:{}".format(mq_cluster.domain_name, mq_cluster.port)

    # 创建 topic 及 partition
    client = kafka.SimpleClient(hosts=kafka_hosts)
    client.ensure_topic_exists(topic, ignore_leadernotavailable=True)
    if partition:
        admin_client = KafkaAdminClient(bootstrap_servers=kafka_hosts)
        admin_client.create_partitions({topic: NewPartitions(partition)})

    # 然后更新相应记录
    qs = models.KafkaTopicInfo.objects.filter(bk_data_id=bk_data_id)
    qs.update(topic=topic)
    if partition:
        qs.update(partition=partition)
    # 更新 gse 写入的配置及consul信息
    models.DataSource.refresh_outer_config()


def get_transfer_cluster() -> List[str]:
    """通过 consul 路径获取 transfer 集群"""
    prefix_path = "%s/v1/" % config.CONSUL_PATH
    # 根据前缀，返回路径
    hash_consul = consul_tools.HashConsul()
    result_data = hash_consul.list(prefix_path)
    if not result_data[1]:
        return []

    # 解析并获取集群名称
    ret_data = []
    for data in result_data[1]:
        ret_data.append(data["Key"].split(prefix_path)[-1].split("/")[0])
    return list(set(ret_data))


def filter_data_id_and_transfer() -> Dict:
    records = models.DataSource.objects.values("bk_data_id", "transfer_cluster_id")
    data = {}
    for r in records:
        data.setdefault(r["transfer_cluster_id"], []).append(r["bk_data_id"])
    return data


def delete_datalink(bk_data_id: int):
    """通过数据源 ID 删除数据链路

    1. 数据源
        - 数据源记录
        - 数据源 option
        - 数据源和结果表关联关系
        - kafka topic
        - 删除写入 gse ds 的

    2. 结果表
        - 结果表记录
        - 结果表 option
        - 结果表指标
        - 结果表指标选择
        - CMDBLevel

    3. 存储
        - influxdb
        - vm
        - kafka
        - es
        - bkdata

    4. 数据依赖
        - consul -- transfer 依赖 ds
        - redis  -- unify query 依赖
    """
    pass
    pass
