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

import json
import time
from typing import Dict, List

import requests
from django.core.management.base import BaseCommand

from metadata import models
from metadata.models.space.constants import SpaceTypes


class Command(BaseCommand):
    help = "query kafka topic by data_id"

    def add_arguments(self, parser):
        parser.add_argument(
            "--unify_query_host", default="http://bk-monitor-unify-query-http:10205", help="unify-query地址"
        )
        parser.add_argument("--platform_biz_id", default=2, help="查询指标数据所在的业务ID，默认是2")
        parser.add_argument("--bk_data_ids", type=str, help="数据源ID, 半角逗号分隔")

    def handle(self, *args, **options):
        unify_query_host, platform_biz_id = options.get("unify_query_host"), options.get("platform_biz_id")
        bk_data_ids = options.get("bk_data_ids")
        if not bk_data_ids:
            self.stderr.write("please input [bk_data_ids]")
            return

        self.stdout.write(json.dumps(self._compose_data(bk_data_ids, unify_query_host, platform_biz_id)))

    def _compose_data(self, bk_data_ids: str, unify_query_host: str, platform_biz_id: str) -> Dict:
        """组装数据"""
        data_id_str, data_id_list = [], []
        for data_id in bk_data_ids.split(","):
            data_id_str.append(str(data_id))
            data_id_list.append(int(data_id))
        data = self._query_topic_and_ds(data_id_list)
        topic_ds, data_ids_with_rt = data["topic_ds"], data["data_ids_with_rt"]
        # 过滤数据
        filter_q = "|".join(data_id_str)
        promql = (
            "sum by (id) (sum_over_time(bkmonitor:transfer_pipeline_frontend_handled_total{id=~\""
            + filter_q
            + "\"}[30d]))<=0"
        )
        filter_data_id_list = self._request_unify_query(
            unify_query_host, promql, {"X-Bk-Scope-Space-Uid": f"{SpaceTypes.BKCC.value}__{platform_biz_id}"}
        )

        ret_data = {}
        for data_id in data_id_list:
            # 组装数据源及对应的topic和host
            if (data_id not in data_ids_with_rt) or (data_id in filter_data_id_list):
                for tds in topic_ds:
                    if tds[1] == data_id:
                        ret_data.setdefault(data_id, []).append({"topic": tds[0], "host": topic_ds[tds]})
        return ret_data

    def _query_topic_and_ds(self, data_id_list: List) -> Dict:
        data = {
            k["topic"]: k["bk_data_id"]
            for k in models.KafkaTopicInfo.objects.filter(bk_data_id__in=data_id_list).values("bk_data_id", "topic")
        }

        kafka_info = self._query_kafka_host()
        storage = self._compose_storage_topic_ds(data_id_list, kafka_info)
        topic_ds_info, data_ids_with_rt = storage["topic_ds"], storage["data_ids_with_rt"]
        ds_kafka = self._query_data_source_mq_cluster_id(data_id_list)
        for topic, data_id in data.items():
            topic_ds_info[(topic, data_id)] = kafka_info.get(ds_kafka.get(data_id, 0))

        return {"topic_ds": topic_ds_info, "data_ids_with_rt": data_ids_with_rt}

    def _compose_storage_topic_ds(self, data_id_list: List, kafka_info: Dict) -> Dict:
        """组装存储topic和数据源"""
        rt_ds = self._get_table_id(data_id_list)
        storage_topic = self._get_storage_topic(list(rt_ds.keys()))
        # 返回数据{topic: {data_id: xxx, host: xxx}}
        data, data_ids_with_rt = {}, []
        for tid, data_id in rt_ds.items():
            data_ids_with_rt.append(data_id)
            topic_info = storage_topic.get(tid)
            if not topic_info:
                continue
            data[(topic_info["topic"], data_id)] = kafka_info.get(topic_info["storage_cluster_id"], "")
        return {"topic_ds": data, "data_ids_with_rt": data_ids_with_rt}

    def _query_no_rt_data_ids(self, bk_data_ids: List) -> List:
        """过滤无rt的数据源"""

    def _get_table_id(self, data_id_list: List) -> Dict:
        return {
            ds_rt["table_id"]: ds_rt["bk_data_id"]
            for ds_rt in models.DataSourceResultTable.objects.filter(bk_data_id__in=data_id_list).values(
                "bk_data_id", "table_id"
            )
        }

    def _get_storage_topic(self, table_id_list: List) -> Dict:
        return {
            k["table_id"]: {"topic": k["topic"], "storage_cluster_id": k["storage_cluster_id"]}
            for k in models.KafkaStorage.objects.filter(table_id__in=table_id_list).values(
                "table_id", "topic", "storage_cluster_id"
            )
        }

    def _query_kafka_host(self):
        """查询kafka地址"""
        return {
            cluster["cluster_id"]: f"{cluster['domain_name']}:{cluster['port']}"
            for cluster in models.ClusterInfo.objects.filter(cluster_type=models.ClusterInfo.TYPE_KAFKA).values(
                "cluster_id", "domain_name", "port"
            )
        }

    def _query_data_source_mq_cluster_id(self, data_id_list: List) -> Dict:
        """查询数据源对应的mq集群ID"""
        return {
            ds["bk_data_id"]: ds["mq_cluster_id"]
            for ds in models.DataSource.objects.filter(bk_data_id__in=data_id_list).values(
                "bk_data_id", "mq_cluster_id"
            )
        }

    def _request_unify_query(self, host: str, promql: str, headers: Dict) -> List:
        """请求unify-query接口"""
        url = f"{host}/query/ts/promql"
        now_sec = int(time.time())
        offset_sec = now_sec - 120
        req_params = {
            "promql": promql,
            "start": str(now_sec),
            "end": str(offset_sec),
            "step": "60s",
            "timezone": "Asia/Shanghai",
            "instant": False,
        }
        data = requests.post(url, json=req_params, headers=headers).json()
        # 判断是否为空
        if not data.get("series"):
            return []
        ret_data = set()
        # 组装数据
        for d in data["series"]:
            ret_data.add(int(d["group_values"][0]))

        return list(ret_data)
