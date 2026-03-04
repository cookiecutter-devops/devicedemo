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
import os

from devicedemo.common.db.alembic import migration

ALEMBIC_REPO = os.path.join(os.path.dirname(__file__), 'alembic')


def upgrade(revision):
    """
     升级数据库到指定版本或最新版本
    :param revision: 版本号或'head'
    :return: 升级结果
    """
    config = migration.load_alembic_config(ALEMBIC_REPO)
    return migration.upgrade(config, revision)


def downgrade(revision):
    """
     降级数据库到指定版本
     :param revision: 版本号或'base'
     :return: 降级结果
    """
    config = migration.load_alembic_config(ALEMBIC_REPO)
    return migration.downgrade(config, revision)


def version():
    """
    查看当前数据库版本
    :return: 当前版本号
    """
    config = migration.load_alembic_config(ALEMBIC_REPO)
    return migration.version(config)


def revision(message, autogenerate):
    """
     生成新的迁移脚本（自动检测模型变化）
    :param message: 脚本描述信息
    :param autogenerate: 是否自动生成
    :return: 脚本文件名
    """
    config = migration.load_alembic_config(ALEMBIC_REPO)
    return migration.revision(config, message, autogenerate)


def stamp(revision):
    """
    为数据库打版本戳记
    :param revision: 版本号
    :return: 戳记结果
    """
    config = migration.load_alembic_config(ALEMBIC_REPO)
    return migration.stamp(config, revision)
