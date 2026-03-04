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
import signal
import threading

from oslo_config import cfg
from oslo_log import log
from paste import deploy
import pecan
import cotyledon

from devicedemo.api import config as api_config
from devicedemo.api import hooks
from devicedemo.i18n import _LI


LOG = log.getLogger(__name__)

auth_opts = [
    cfg.StrOpt('api_paste_config',
               default="api_paste.ini",
               help="Configuration file for WSGI definition of API."
               ),
    cfg.StrOpt('auth_strategy',
               choices=['noauth', 'keystone'],
               default='keystone',
               help=("The strategy to use for auth. Supports noauth and "
                     "keystone")),
]

api_opts = [
    cfg.IPOpt('host_ip',
              default="0.0.0.0",
              help='Host serving the API.'),
    cfg.PortOpt('port',
                default=9009,
                help='Host port serving the API.'),
    cfg.BoolOpt('pecan_debug',
                default=False,
                help='Toggle Pecan Debug Middleware.'),
    # 对于API服务，通常只使用单个工作进程，因为多个进程会导致端口冲突
    # 如果需要多进程，请使用外部负载均衡器（如nginx）配合单进程服务
    cfg.IntOpt('workers',
               default=1,
               min=1,
               max=1,  # 限制为1，避免端口冲突
               help='Number of API worker processes. '
                    'For API services, typically should be 1 to avoid port conflicts. '
                    'Use external load balancer for scaling.')
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)
CONF.register_opts(api_opts, group='api')


def get_pecan_config():
    # Set up the pecan configuration
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(pecan_config=None, extra_hooks=None):

    app_conf = get_pecan_config()
    app_hooks = [
        hooks.RPCHook(),
    ]

    if CONF.auth_strategy == 'keystone':
        app_hooks.append(hooks.ContextHook())

    app = pecan.make_app(
        app_conf.app.root,
        static_root=app_conf.app.static_root,
        template_path=app_conf.app.template_path,
        debug=CONF.api.pecan_debug,
        force_canonical=getattr(app_conf.app, 'force_canonical', True),
        hooks=app_hooks,
        guess_content_type_from_ext=False
    )

    return app


def load_app():
    cfg_file = None
    cfg_path = cfg.CONF.api_paste_config
    if not os.path.isabs(cfg_path):
        cfg_file = CONF.find_file(cfg_path)
    elif os.path.exists(cfg_path):
        cfg_file = cfg_path

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([cfg.CONF.api_paste_config])
    LOG.info(_LI("Full WSGI config used: %s"), cfg_file)
    return deploy.loadapp("config:" + cfg_file)


class APIService(cotyledon.Service):
    """API服务类 - 使用cotyledon框架管理服务生命周期"""

    def __init__(self, worker_id, conf=None):
        super(APIService, self).__init__(worker_id)
        self.conf = conf or CONF
        self.host = self.conf.api.host_ip
        self.port = self.conf.api.port
        self.server = None
        self.app = None
        self.running = True  # 添加运行标志
        self.server_thread = None  # 用于eventlet服务器线程管理
        self.shutdown_event = threading.Event()  # 用于优雅关闭

    def run(self):
        """启动服务"""
        LOG.info(_LI('Starting API server worker %d in PID %s'),
                self.worker_id, os.getpid())
        LOG.info(_LI("Configuration:"))
        self.conf.log_opt_values(LOG, logging.INFO)

        try:
            # 加载应用
            self.app = load_app()

            # 使用eventlet作为WSGI服务器，更适合生产环境
            try:
                import eventlet
                from eventlet import wsgi
                import socket

                # 创建监听套接字
                sock = eventlet.listen((self.host, self.port))

                LOG.info(_LI('serving on %(host)s:%(port)s'),
                        {'host': self.host, 'port': self.port})

                # 启动WSGI服务器，在单独线程中运行
                def serve():
                    wsgi.server(sock, self.app, log=LOG, debug=False)

                # 在后台线程运行服务器
                self.server_thread = threading.Thread(target=serve)
                self.server_thread.daemon = True
                self.server_thread.start()

                # 等待关闭信号
                self.shutdown_event.wait()

            except ImportError as e:
                LOG.warning(_LI('eventlet not available, falling back to wsgiref: %s'), e)
                # 如果 eventlet 不可用，则使用原生simple_server作为备选
                from wsgiref import simple_server
                server_cls = simple_server.WSGIServer
                handler_cls = simple_server.WSGIRequestHandler

                self.server = simple_server.make_server(
                    self.host,
                    self.port,
                    self.app,
                    server_cls,
                    handler_cls)

                LOG.info(_LI('serving on %(host)s:%(port)s'),
                        {'host': self.host, 'port': self.port})

                # 使用轮询检查运行状态
                while self.running:
                    self.server.handle_request()

        except Exception as e:
            LOG.exception(_LI('Error starting API server: %s'), e)
            os._exit(1)

    def terminate(self):
        """终止服务"""
        LOG.info(_LI('Terminating API server worker %d'), self.worker_id)

        # 设置关闭标志
        self.running = False
        self.shutdown_event.set()

        # 尝试优雅关闭eventlet服务器
        if self.server_thread and self.server_thread.is_alive():
            try:
                # eventlet服务器通常通过线程退出来停止
                self.server_thread.join(timeout=5.0)  # 等待最多5秒
            except Exception:
                pass  # 忽略关闭时的异常

        # 关闭wsgiref服务器
        if self.server:
            try:
                self.server.shutdown()
            except Exception:
                pass  # 忽略关闭时的异常

        LOG.info(_LI('API server worker %d terminated'), self.worker_id)


def create_service_manager():
    """创建服务管理器 - 使用cotyledon管理服务"""
    manager = cotyledon.ServiceManager()
    # 严格限制为1个worker，避免端口冲突
    manager.add(APIService, workers=CONF.api.workers)
    return manager


def run_server():
    """运行服务器 - 使用cotyledon服务管理"""
    manager = create_service_manager()

    # 注册信号处理
    def signal_handler(signum, frame):
        LOG.info(_LI('Received signal %d, initiating graceful shutdown'), signum)
        manager.stop()

    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 不捕获SIGUSR1等用于热重载的信号

    manager.run()
    return manager


def app_factory(global_config, **local_conf):
    return setup_app()
