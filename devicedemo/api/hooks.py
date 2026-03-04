# -*- coding: utf-8 -*-
# Copyright 2014 Objectif Libre
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Stéphane Albert

# Pecan 钩子机制 - 在请求处理过程中插入自定义逻辑
from oslo_context import context  # Oslo上下文
from pecan import hooks  # Pecan钩子

from devicedemo.common import policy  # 权限策略
from devicedemo import messaging  # 消息传递


class RPCHook(hooks.PecanHook):
    """RPC钩子 - 为每个请求注入RPC客户端"""

    def __init__(self):
        self._rpc_client = messaging.get_client()  # 获取RPC客户端

    def before(self, state):
        # 在请求处理前执行
        state.request.rpc_client = self._rpc_client  # 将RPC客户端注入请求对象


class ContextHook(hooks.PecanHook):
    """上下文钩子 - 处理认证和请求上下文"""

    def on_route(self, state):
        """在路由阶段执行"""
        headers = state.request.headers  # 获取请求头

        # 从HTTP头中提取认证信息
        roles = headers.get('X-Roles', '').split(',')  # 角色列表
        is_admin = policy.check_is_admin(roles)  # 检查是否为管理员

        creds = {
            'user': headers.get('X-User') or headers.get('X-User-Id'),  # 用户ID
            'tenant': headers.get('X-Tenant') or headers.get('X-Tenant-Id'),  # 租户ID
            'auth_token': headers.get('X-Auth-Token'),  # 认证令牌
            'is_admin': is_admin,  # 是否为管理员
            'roles': roles,  # 角色列表
        }
        # 将认证上下文存入请求对象
        state.request.context = context.RequestContext(**creds)
