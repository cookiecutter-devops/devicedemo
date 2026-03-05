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
import logging
import os
from wsgiref import simple_server

from oslo_config import cfg
from oslo_log import log
from paste import deploy
import pecan

from devicedemo.api import config as api_config
from devicedemo.api import hooks
from devicedemo.i18n import _LI


LOG = log.getLogger(__name__)

# 认证相关配置选项
auth_opts = [
    cfg.StrOpt('api_paste_config',
               default="api_paste.ini",  # 默认的API Paste配置文件
               help="Configuration file for WSGI definition of API."
               ),
    cfg.StrOpt('auth_strategy',
               choices=['noauth', 'keystone'],  # 支持的认证策略
               default='keystone', # 默认使用Keystone认证
               help=("The strategy to use for auth. Supports noauth and "
                     "keystone")),  # 认证策略选项，支持noauth和keystone
]

# API 服务相关配置选项
api_opts = [
    cfg.IPOpt('host_ip',
              default="0.0.0.0",# 默认绑定到所有网络接口
              help='Host serving the API.'),
    cfg.PortOpt('port',
                default=9009,   # 默认API端口号
                help='Host port serving the API.'),
    cfg.BoolOpt('pecan_debug',
                default=False,  # 默认不启用调试模式
                help='Toggle Pecan Debug Middleware.'),
]

CONF = cfg.CONF  # 全局配置对象
CONF.register_opts(auth_opts)  # 注册认证配置选项
CONF.register_opts(api_opts, group='api')  # 注册API配置选项到api组



def get_pecan_config():
    """获取Pecan框架配置

    Returns:
        pecan.configuration: Pecan配置对象
    """
    # 设置Pecan配置
    filename = api_config.__file__.replace('.pyc', '.py')  # 获取配置文件路径，排除.pyc编译文件
    return pecan.configuration.conf_from_file(filename)  # 从文件加载Pecan配置对象


def setup_app(pecan_config=None, extra_hooks=None):
    """
    设置Pecan应用

    Args:
        pecan_config: Pecan配置对象
        extra_hooks: 额外的Pecan钩子

    Returns:
        Pecan应用实例
    """
    app_conf = get_pecan_config()  # 获取Pecan配置
    app_hooks = [  # 定义应用钩子
        hooks.RPCHook(),  # RPC钩子，为请求注入RPC客户端
    ]


    # 如果使用Keystone认证策略，添加上下文钩子
    if CONF.auth_strategy == 'keystone':
        app_hooks.append(hooks.ContextHook())  # 上下文钩子，处理认证和请求上下文

    # 创建Pecan应用实例
    app = pecan.make_app(
        app_conf.app.root,  # 应用根目录
        static_root=app_conf.app.static_root,  # 静态文件目录
        template_path=app_conf.app.template_path,  # 模板文件目录
        debug=CONF.api.pecan_debug,  # 是否启用调试模式
        force_canonical=getattr(app_conf.app, 'force_canonical', True),  # 是否强制使用规范URL
        hooks=app_hooks,  # 应用钩子列表
        guess_content_type_from_ext=False  # 是否根据文件扩展名猜测内容类型
    )

    return app  # 返回Pecan应用实例


def load_app():
    """
    加载WSGI应用
    从Paste配置文件加载WSGI应用实例

    Returns:
        WSGI应用实例

    Raises:
        ConfigFilesNotFoundError: 当配置文件未找到时
    """
    cfg_file = None  # 配置文件路径变量
    cfg_path = cfg.CONF.api_paste_config  # 从全局配置获取Paste配置路径
    if not os.path.isabs(cfg_path):  # 如果不是绝对路径
        cfg_file = CONF.find_file(cfg_path)  # 在配置搜索路径中查找文件
    elif os.path.exists(cfg_path):  # 如果路径存在
        cfg_file = cfg_path  # 直接使用该路径

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([cfg.CONF.api_paste_config])
    LOG.info(_LI("Full WSGI config used: %s"), cfg_file) # 记录使用的完整WSGI配置
    return deploy.loadapp("config:" + cfg_file) # 使用PasteDeploy加载应用


def build_server():
    # 构建WSGI服务器实例， 创建并配置一个WSGI服务器，用于处理HTTP请求
    host = CONF.api.host_ip  # 获取API服务监听地址
    port = CONF.api.port  # 获取API服务监听端口
    LOG.info(_LI('Starting server in PID %s'), os.getpid())  # 记录服务器进程ID
    LOG.info(_LI("Configuration:"))  # 记录配置信息
    cfg.CONF.log_opt_values(LOG, logging.INFO)  # 记录配置信息

    if host == '0.0.0.0':  # 如果监听地址为0.0.0.0，则显示提示信息
        LOG.info(_LI('serving on 0.0.0.0:%(sport)s, view at '
                     'http://127.0.0.1:%(vport)s'),
                 {'sport': port, 'vport': port})
    else:
        LOG.info(_LI("serving on http://%(host)s:%(port)s"),
                 {'host': host, 'port': port})

    server_cls = simple_server.WSGIServer  # 定义WSGI服务器类
    handler_cls = simple_server.WSGIRequestHandler  # 定义WSGI请求处理类

    app = load_app()    # 加载WSGI应用

    # 创建服务器实例
    srv = simple_server.make_server(
        host,
        port,
        app,
        server_cls,
        handler_cls)

    return srv  # 返回WSGI服务器实例


def app_factory(global_config, **local_conf):
    # Pecan应用工厂函数，用于WSGI服务器初始化时调用
    return setup_app()  # 返回Pecan应用实例


"""
服务启动流程：
devicedemo-api 命令 -> cmd/api.py:main()
service.prepare_service() -> 准备配置、日志等环境
app.build_server() -> 构建 WSGI 服务器
server.serve_forever() -> 启动服务并处理请求

WSGI 服务器启动 -> wsgiref/simple_server.py:make_server()
"""
