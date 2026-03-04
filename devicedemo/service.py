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
#
import socket  # Socket模块
import sys  # 系统模块

from oslo_config import cfg  # Oslo配置
import oslo_i18n  # Oslo国际化
from oslo_log import log  # Oslo日志

from devicedemo.common import defaults  # 默认设置
from devicedemo import messaging  # 消息传递
from devicedemo import version  # 版本信息


service_opts = [
    cfg.StrOpt('host',  # 主机名配置项
               default=socket.getfqdn(),  # 默认为主机名
               help='Name of this node. This can be an opaque identifier. '
               'It is not necessarily a hostname, FQDN, or IP address. '
               'However, the node name must be valid within an AMQP key, '
               'and if using ZeroMQ, a valid hostname, FQDN, or IP address.')
]

cfg.CONF.register_opts(service_opts)


def prepare_service(argv=None, config_files=None):
    """
    准备服务环境
    :param argv: 命令行参数
    :param config_files: 配置文件列表
    """
    oslo_i18n.enable_lazy()  # 启用懒加载国际化
    log.register_options(cfg.CONF)  # 注册日志选项
    log.set_defaults()  # 设置日志默认值
    defaults.set_cors_middleware_defaults()  # 设置CORS中间件默认值

    if argv is None:
        argv = sys.argv
    # 解析命令行参数并加载配置
    cfg.CONF(argv[1:], project='devicedemo', validate_default_values=True,
             version=version.version_info.version_string(),
             default_config_files=config_files)

    log.setup(cfg.CONF, 'devicedemo')  # 设置日志
    messaging.setup()  # 设置消息传递
