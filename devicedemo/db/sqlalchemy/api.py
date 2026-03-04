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

from oslo_db import exception  # Oslo数据库异常处理
from oslo_db.sqlalchemy import utils  # Oslo SQLAlchemy工具
from oslo_utils import uuidutils  # UUID生成工具
import sqlalchemy  # SQLAlchemy ORM

from devicedemo import db  # 项目数据库模块
from devicedemo.db import api  # 数据库API抽象接口
from devicedemo.db.sqlalchemy import migration  # 数据库迁移模块
from devicedemo.db.sqlalchemy import models  # 数据库模型


def get_backend():
    """获取后端实现实例"""
    return DeviceManage()


class DeviceManage(api.Device):
    """数据库操作的具体实现类 - 继承自抽象接口"""

    def get_migration(self):
        """获取迁移管理器实现"""
        return migration

    def get_device(self, device_id=None, name=None):
        """
        查询设备方法
        :param device_id: 设备UUID
        :param name: 设备名称
        :return: 设备对象
        """
        session = db.get_session()  # 获取数据库会话
        try:
            q = utils.model_query(models.Device, session)  # 构建查询对象
            if device_id:
                q = q.filter(models.Device.device_id == device_id)  # 按ID过滤
            if name:
                q = q.filter(models.Device.name == name)  # 按名称过滤
            return q.one()   # 返回单条数据，如果找不到会抛出异常
        except sqlalchemy.orm.exc.NoResultFound:  # 处理未找到异常
            raise api.NoSuchDevice(device_id)

    def list_devices(self):
        """
        列出所有设备方法
        :return: 设备对象列表
        """
        session = db.get_session()  # 获取数据库会话
        q = utils.model_query(models.Device, session)  # 查询所有设备
        res = q.all()  # 返回所有数据
        return res

    def create_device(self, name, dtype=None, vendor=None, version=None):
        """
        创建设备方法
        :param name: 设备名称
        :param dtype: 设备类型
        :param vendor: 设备厂商
        :param version: 设备版本
        :return: 新创建的设备对象
        """
        session = db.get_session()  # 获取数据库会话
        try:
            with session.begin():   # 开启事务，确保操作的原子性
                device_db = models.Device(
                    device_id=uuidutils.generate_uuid(), # 自动生成UUID
                    name=name,
                    dtype=dtype,
                    vendor=vendor,
                    version=version)
                session.add(device_db)      # 添加到会话
            return device_db
        except exception.DBDuplicateEntry:  # 处理重复条目异常
            device_db = self.get_device(name=name)
            raise api.DeviceAlreadyExists(name, device_db.device_id)

    def update_device(self, device_id, name=None, dtype=None, vendor=None,
                      version=None):
        """
        更新设备方法
        :param device_id: 设备ID
        :param name: 设备名称
        :param dtype: 设备类型
        :param vendor: 设备厂商
        :param version: 设备版本
        :return: 更新后的设备对象
        """
        session = db.get_session()  # 获取数据库会话
        try:
            with session.begin():   # 开启事务
                q = session.query(models.Device)  # 查询设备
                q = q.filter(models.Device.device_id == device_id)  # 按ID过滤
                device_db = q.with_lockmode('update').one()  # 锁定行，防止并发冲突
                if name:
                    device_db.name = name  # 更新名称
                if dtype:
                    device_db.dtype = dtype  # 更新类型
                if vendor:
                    device_db.vendor = vendor
                if version:
                    device_db.version = version
            return device_db
        except sqlalchemy.orm.exc.NoResultFound:  # 处理未找到异常
            raise api.NoSuchDevice(device_id)
        except exception.DBDuplicateEntry:  # 处理重复条目异常
            device_db = self.get_device(name=name)
            raise api.DeviceAlreadyExists(name, device_db.device_id)

    def delete_device(self, device_id):
        """
        删除设备方法
        :param device_id: 设备ID
        """
        session = db.get_session()  # 获取会话
        q = utils.model_query(models.Device, session)  # 查询设备
        q = q.filter(models.Device.device_id == device_id)  # 按ID过滤
        r = q.delete()  # 删除设备
        if not r:  # 如果没有删除任何记录
            raise api.NoSuchDevice(device_id)  # 抛出设备不存在异常
