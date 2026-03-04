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

import sys
import traceback

from devicedemo.api import app
from devicedemo import service


def main():
    """devicedemo-api入口函数"""
    try:
        service.prepare_service()  # 准备服务环境
        manager = app.run_server()  # 使用Cotyledon运行服务器
        return manager
    except KeyboardInterrupt:
        # 捕获键盘中断，确保优雅退出
        print("\nReceived interrupt signal, shutting down gracefully...", file=sys.stderr)
        return 1
    except Exception as e:
        # 记录完整异常信息
        print(f"Error starting devicedemo-api: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main() or 0)
