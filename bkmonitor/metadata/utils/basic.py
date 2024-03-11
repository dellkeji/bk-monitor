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
import logging
from functools import reduce
from typing import Any, Dict, List, Union


def getitems(obj: Dict, items: Union[List, str], default: Any = None) -> Any:
    """
    递归获取数据
    注意：使用字符串作为键路径时，须确保 Key 值均为字符串

    :param obj: Dict 类型数据
    :param items: 键列表：['foo', 'bar']，或者用 "." 连接的键路径： ".foo.bar" 或 "foo.bar"
    :param default: 默认值
    :return: 返回对应的value或者默认值
    """
    if not isinstance(obj, dict):
        raise TypeError("Dict object support only!")
    if isinstance(items, str):
        items = items.strip(".").split(".")
    try:
        return reduce(lambda x, i: x[i], items, obj)
    except (IndexError, KeyError, TypeError):
        return default


def log_format_record(logger: logging.Logger, task_name: str, operation: str, body: Any, resp_data: Any = None) -> None:
    """记录格式化日志"""
    try:
        body_str = json.dumps(body)
        resp_data_str = json.dumps(resp_data)
    except (ValueError, TypeError) as e:
        logger.error("task_name: %s, operator: %s json dumps error, error: %s", e)
        return

    # 忽略记录日志的异常
    try:
        logger.info(
            "diff content, task_name: %s, operator: %s, body: %s, resp_data: %s",
            task_name,
            operation,
            body_str,
            resp_data_str,
        )
    except Exception:
        pass
