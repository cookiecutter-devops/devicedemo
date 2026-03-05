# -*- coding: utf-8 -*-
# Copyright 2013 - Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# API服务启动命令 - devicedemo服务的主入口点
from devicedemo.api import app      # 导入API应用模块
from devicedemo import service     # 导入服务管理模块


def main():
    """
    主函数 - devicedemo API服务的入口点

    该函数执行以下步骤：
    1. 准备服务环境（配置、日志等）
    2. 构建WSGI服务器实例
    3. 启动服务器并持续监听请求
    4. 处理中断信号
    """
    service.prepare_service()  # 准备服务环境，包括配置加载、日志设置等
    server = app.build_server()  # 构建WSGI服务器实例
    try:
        server.serve_forever()  # 启动服务器并持续处理请求
    except KeyboardInterrupt:  # 捕获Ctrl+C中断信号
        pass  # 退出程序


if __name__ == '__main__':  # 当作为主脚本运行时
    main()  # 调用主函数
