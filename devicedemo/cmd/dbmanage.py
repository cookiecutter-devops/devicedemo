# zhangguoqing
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
# 数据库管理命令模块 - 提供命令行工具用于数据库迁移和管理
from oslo_config import cfg

from devicedemo.db import api as db_api # 数据库API
from devicedemo import service # 服务管理

CONF = cfg.CONF # 全局配置对象

class DBCommand(object):
    """
    数据库管理命令类 - 封装所有数据库操作命令
    支持升级、降级、版本戳记、生成新版本等操作
    """
    def get_migration(self):
        """
        获取数据库迁移管理器
        :return: 迁移管理器对象
        """
        migration = db_api.get_instance().get_migration()
        return migration


    def _version_change(self, cmd):
        """
        版本变更的通用方法
        :param cmd: 要执行的迁移命令(upgrade/downgrade)
        """
        revision = CONF.command.revision  # 从配置获取版本号
        migration = self.get_migration()  # 获取迁移管理器
        func = getattr(migration, cmd)    # 获取对应的方法
        func(revision)  # 执行迁移操作

    def upgrade(self):
        """
        升级数据库到指定版本或最新版本
        对应Alembic的upgrade命令
        """
        self._version_change('upgrade')

    def downgrade(self):
        """
        将数据库降级到指定版本
        对应Alembic的downgrade命令
        """
        self._version_change('downgrade')

    def revision(self):
        """
        生成新的数据库迁移脚本
        对应Alembic的revision命令
        """
        migration = self.get_migration()
        # 生成新的迁移脚本，可选择自动检测模型变化
        migration.revision(CONF.command.message, CONF.command.autogenerate)


    def stamp(self):
        """
        为数据库打上指定的版本戳记（不实际执行迁移）
        对应Alembic的stamp命令
        """
        migration = self.get_migration()
        migration.stamp(CONF.command.revision)

    def version(self):
        """
        显示当前数据库版本
        对应Alembic的version命令
        """
        migration = self.get_migration()
        migration.version()


def add_command_parsers(subparsers):
    """
    添加命令行解析器
    为每个数据库命令创建相应的命令行解析器
    :param subparsers: 子命令解析器容器
    """
    command_object = DBCommand()  # 创建命令对象实例

    # 升级命令解析器
    parser = subparsers.add_parser('upgrade')
    parser.set_defaults(func=command_object.upgrade)  # 设置执行函数
    parser.add_argument('--revision', nargs='?')  # 可选的版本参数


    # 降级命令解析器
    parser = subparsers.add_parser('downgrade')
    parser.set_defaults(func=command_object.downgrade)
    parser.add_argument('--revision', nargs='?')  # 可选的版本参数


    # 版本戳记命令解析器
    parser = subparsers.add_parser('stamp')
    parser.set_defaults(func=command_object.stamp)
    parser.add_argument('--revision', nargs='?')  # 必需的版本参数


    # 生成迁移脚本命令解析器
    parser = subparsers.add_parser('revision')
    parser.set_defaults(func=command_object.revision)
    parser.add_argument('-m', '--message')  # 迁移描述信息
    parser.add_argument('--autogenerate', action='store_true')  # 自动检测模型变化标志

    # 查看版本命令解析器
    parser = subparsers.add_parser('version')
    parser.set_defaults(func=command_object.version)


# 注册命令行选项，使用子命令形式
command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Available commands',
                                handler=add_command_parsers)

# 将命令行选项注册到全局配置
CONF.register_cli_opt(command_opt)


def main():
    """
    主函数 - 程序入口点
    初始化服务并执行指定的数据库命令
    """
    service.prepare_service()  # 准备服务环境（初始化配置、日志等）
    CONF.command.func()  # 执行通过命令行参数指定的函数


"""
# 查看当前数据库版本
devicedemo-dbmanage version

# 升级到最新版本
devicedemo-dbmanage upgrade

# 升级到指定版本
devicedemo-dbmanage upgrade --revision <版本号>

# 降级到指定版本
devicedemo-dbmanage downgrade --revision <版本号>

# 生成新的迁移脚本（自动检测模型变化）
devicedemo-dbmanage revision --autogenerate -m "描述信息"

# 为数据库打版本戳记
devicedemo-dbmanage stamp --revision <版本号>

这个文件实际上是对Alembic迁移工具的封装,通过 devicedemo.db.sqlalchemy.migration 模块与 Alembic 集成,提供了一个更符合OpenStack风格的命令行接口。
"""
