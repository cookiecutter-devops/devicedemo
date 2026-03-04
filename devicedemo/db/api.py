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

## 抽象接口层 - 定义数据库操作的规范接口

import abc

from oslo_config import cfg
from oslo_db import api as db_api
import six

# 数据库后端映射：将字符串标识符映射到实际的实现类
_BACKEND_MAPPING = {'sqlalchemy': 'devicedemo.db.sqlalchemy.api'}

# 从配置中创建数据库API实例，支持懒加载
IMPL = db_api.DBAPI.from_config(cfg.CONF,
                                backend_mapping=_BACKEND_MAPPING,
                                lazy=True)



def get_instance():
    """
    Return a DB API instance.
    获取数据库API实例 - 这是访问数据库的主要入口点
    """
    return IMPL


class BaseError(Exception):
    """
    Base class errors.
    基础错误类 - 所有自定义异常的父类
    """


class ClientError(BaseError):
    """
    Base class for client side errors.
    客户端错误基类 - 用于处理客户端相关的错误
    """


class NoSuchDevice(ClientError):
    """
    Raised when the device doesn't exist.
     抛出设备不存在异常 - 当请求的设备不存在时抛出
    """

    def __init__(self, device_id=None, name=None):
        super(NoSuchDevice, self).__init__(
            "No such device: %s (UUID: %s)" % (name, device_id))
        self.devicd_id = device_id  # 设备ID
        self.name = name  # 设备名称


class DeviceAlreadyExists(ClientError):
    """
    Raised when the device already exists.
    抛出设备已存在异常 - 当创建设备但该设备已存在时抛出
    """

    def __init__(self, device_id, name):
        super(DeviceAlreadyExists, self).__init__(
            "Device %s already exists (UUID: %s)" % (name, device_id))
        self.device_id = device_id  # 设备ID
        self.name = name  # 设备名称


@six.add_metaclass(abc.ABCMeta)  # 使用ABC元类，确保子类必须实现抽象方法
class Device(object):
    """Base class for state tracking.
    设备数据库操作的抽象基类 - 定义了所有数据库操作的接口规范
    """

    @abc.abstractmethod
    def get_migration(self):
        """
        Return a migrate manager.
        获取迁移管理器 - 用于数据库迁移操作
        """

    @abc.abstractmethod
    def get_device(self, device_id=None, name=None):
        """
        Retrieve the device object.
        :param device_id: uuid of the device - 设备的UUID
        :param name: name of the device - 设备名称
        获取设备对象 - 根据ID或名称查询单个设备
        """

    @abc.abstractmethod
    def list_devices(self):
        """
        Return an list of every devices.
        获取所有设备列表 - 返回所有设备的列表
        """

    @abc.abstractmethod
    def create_device(self, name, dtype=None, vendor=None, version=None):
        """
        Create a new device.
        :param name: Name of the device to create. - 要创建的设备名称（必填）
        :param dtype: Type of the device to create. - 设备类型（可选）
        :param vendor: Vendor of the device to create. - 设备厂商（可选）
        :param version: Version of the device to create. - 设备版本（可选）
        创建设备 - 在数据库中创建新的设备记录
        """

    @abc.abstractmethod
    def update_device(self, device_id, name, dtype=None, vendor=None,
                      version=None):
        """
        Update a device.
        :param device_id: uuid UUID of the device to modify. - 要修改的设备UUID
        :param name: Name of the device to create. - 设备名称（可选）
        :param dtype: Type of the device to create. - 设备类型（可选）
        :param vendor: Vendor of the device to create. - 设备厂商（可选）
        :param version: Version of the device to create. - 设备版本（可选）
        更新设备 - 修改现有设备的信息
        """

    @abc.abstractmethod
    def delete_device(self, device_id):
        """
        Delete a device.

        :param device_id: uuid UUID of the device to delete.
        删除设备 - 从数据库中删除指定的设备
        """
