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
# API 数据模型 - 定义API层的数据结构
from wsme import types as wtypes  # WSME类型系统

from devicedemo.api.v1 import types as ck_types  # API类型定义



class Device(wtypes.Base):
    """Type describing a device.

    """

    device_id = wtypes.wsattr(ck_types.UuidType(), mandatory=False)  # UUID 类型
    """Uuid of the service."""

    name = wtypes.text  # 设备名称
    """Name of the device."""

    dtype = wtypes.text  # 设备类型
    """Type of the device."""

    vendor = wtypes.text  # 设备供应商
    """Vendor of the device."""

    version = wtypes.text  # 设备版本
    """Version of the device."""


    def to_json(self):
        # 转换为JSON格式的字典
        res_dict = {'deivce_id': self.device_id,
                    'name': self.name,
                    'dtype': self.dtype,
                    'vendor': self.vendor,
                    'version': self.version}
        return res_dict

    @classmethod
    def sample(cls):
        """创建示例数据"""
        sample = cls(device_id='faf7404e-1d9a-47d2-bc49-48569ad5ed6e',
                     name='device-001',
                     dtype='device-type-001',
                     vendor='tongfangcloud',
                     version='device-version-001')
        return sample


class DeviceCollection(wtypes.Base):
    """设备集合类型 - 描述设备列表的数据结构"""

    devices = [Device]  # 设备列表
    """设备列表"""

    @classmethod
    def sample(cls):
        """创建示例数据"""
        sample = Device.sample()
        return cls(devices=[sample])
