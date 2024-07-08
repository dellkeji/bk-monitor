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

from django.db import models

from monitor_web.models.collect.base import BaseResource


class PluginCollect(BaseResource):
    """插件采集"""

    kind = models.CharField("资源类型", max_length=32, default="plugin")
    scope = models.CharField("数据范围", max_length=16, default="host")
    task_id = models.CharField("任务ID", max_length=128, null=True, blank=True)

    class Meta:
        verbose_name = "插件采集"
        verbose_name_plural = "插件采集"
