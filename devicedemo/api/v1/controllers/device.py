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

import pecan  # Pecan Web框架
from pecan import rest  # Pecan REST支持
import six  # Python 2/3兼容性库
from wsme import types as wtypes  # WSME类型系统
import wsmeext.pecan as wsme_pecan  # WSME-Pecan集成

from devicedemo.api.v1 import types as dd_types  # API类型定义
from devicedemo.api.v1.datamodels import device as device_models  # 数据模型
from devicedemo.common import policy  # 权限策略
from devicedemo.db import api as db_api  # 数据库API


class DeviceController(rest.RestController):
    """设备资源的REST控制器 - 处理设备相关的HTTP请求"""

    @wsme_pecan.wsexpose(device_models.Device,
                         dd_types.UuidType(),  # 设备ID参数类型
                         status_code=200)  # HTTP状态码
    def get_one(self, device_id):
        """
        获取单个设备
        HTTP GET /v1/device/{id}
        :param device_id: 设备UUID
        :return: 设备对象
        """
        device = db_api.get_instance()  # 获取数据库实例
        try:
            device_db = device.get_device(device_id=device_id)   # 查询数据库
            return device_models.Device(
                **device_db.export_model())                      # 返回序列化结果
        except db_api.NoSuchDevice as e:
            pecan.abort(404, six.text_type(e))      # 设备不存在返回 404

    @wsme_pecan.wsexpose(device_models.DeviceCollection)  # 暴露WSME服务
    def get_all(self):
        """
        获取所有设备
        HTTP GET /v1/device
        :return: 设备集合
        """
        device = db_api.get_instance()  # 获取数据库实例
        device_list = []  # 设备列表
        devices_obj_list = device.list_devices()        # 从数据库获取所有设备
        for device_obj in devices_obj_list:
            device_db = device.get_device(device_id=device_obj.device_id)  # 获取每个设备
            device_list.append(device_models.Device(
                **device_db.export_model()))            # 转换为 API 模型
        res = device_models.DeviceCollection(devices=device_list)  # 创建集合对象
        return res

    @wsme_pecan.wsexpose(device_models.Device,
                         wtypes.text,  # 设备名称（必需）
                         wtypes.text,  # 设备类型（可选）
                         wtypes.text,  # 设备厂商（可选）
                         wtypes.text)  # 设备版本（可选）
    def post(self, name, dtype=None, vendor=None, version=None):
        """
        创建设备
        HTTP POST /v1/device
        :param name: 设备名称（必需）
        :param dtype: 设备类型（可选）
        :param vendor: 设备厂商（可选）
        :param version: 设备版本（可选）
        :return: 新创建的设备对象
        """
        device = db_api.get_instance()  # 获取数据库实例
        try:
            device_db = device.create_device(
                name=name,
                dtype=dtype,
                vendor=vendor,
                version=version)
            # 设置响应位置头，便于客户端定位新资源
            pecan.response.location = pecan.request.path_url
            if pecan.response.location[-1] != '/':
                pecan.response.location += '/'
            pecan.response.location += device_db.device_id
            return device_models.Device(
                **device_db.export_model())
        except db_api.DeviceAlreadyExists as e:
            pecan.abort(409, six.text_type(e))   # 冲突错误返回 409
        except db_api.ClientError as e:
            pecan.abort(400, six.text_type(e))   # 客户端错误返回 400

    @wsme_pecan.wsexpose(None,  # 不返回内容
                         dd_types.UuidType(),  # 设备ID
                         wtypes.text,  # 设备名称
                         wtypes.text,  # 设备类型
                         wtypes.text,  # 设备厂商
                         wtypes.text)  # 设备版本
    def put(self, device_id, name=None, dtype=None, vendor=None, version=None):
        """
        更新设备
        HTTP PUT /v1/device/{id}
        :param device_id: 设备ID
        :param name: 设备名称
        :param dtype: 设备类型
        :param vendor: 设备厂商
        :param version: 设备版本
        """
        device = db_api.get_instance()  # 获取数据库实例
        try:
            device_db = device.update_device(
                device_id=device_id,
                name=name,
                dtype=dtype,
                vendor=vendor,
                version=version)          # 更新数据库
            # 设置响应位置头
            pecan.response.headers['Location'] = pecan.request.path
        except db_api.NoSuchDevice as e:
            pecan.abort(409, six.text_type(e))  # 设备不存在返回 409
        except db_api.ClientError as e:
            pecan.abort(400, six.text_type(e))  # 客户端错误返回 400

    @wsme_pecan.wsexpose(None,  # 不返回内容
                         dd_types.UuidType(),  # 设备ID
                         status_code=204)  # HTTP 204 No Content
    def delete(self, device_id):
        """
        删除设备
        HTTP DELETE /v1/device/{id}
        :param device_id: 设备ID
        """
        device = db_api.get_instance()                    # 获取数据库实例
        try:
            device.delete_device(device_id=device_id)   # 从数据库删除设备
        except db_api.NoSuchDevice as e:
            pecan.abort(404, six.text_type(e))  # 设备不存在返回 404
