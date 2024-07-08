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

from bkmonitor.utils.db import JsonField


class BaseResource(models.Model):
    kind = models.CharField("资源类型", max_length=32)
    namespace = models.CharField("命名空间", max_length=32)
    name = models.CharField("资源名称", max_length=64)
    spec = JsonField("资源详情")
    status = models.CharField("资源状态", max_length=16, default="pending")
    updated_status_at = models.DateTimeField("修改时间", auto_now=True)

    creator = models.CharField("创建者", max_length=32)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updater = models.CharField("更新者", max_length=32)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True
