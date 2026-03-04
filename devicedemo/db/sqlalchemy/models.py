# 数据库模型
from oslo_db.sqlalchemy import models  # Oslo SQLAlchemy基础模型
import sqlalchemy  # SQLAlchemy核心

from devicedemo.common.db import models as devicedemo_models  # 项目基础模型

Base = devicedemo_models.get_base()  # 获取SQLAlchemy基础类


class DeviceDemoBase(models.ModelBase):
    """设备模型的基础类，包含通用功能"""

    # 表配置：字符集和存储引擎
    __table_args__ = {'mysql_charset': "utf8",
                      'mysql_engine': "InnoDB"}
    fk_to_resolve = {}  # 外键解析映射

    def save(self, session=None):
        """保存模型到数据库"""
        from devicedemo import db

        if session is None:
            session = db.get_session()

        super(DeviceDemoBase, self).save(session=session)

    def as_dict(self):
        """将模型转换为字典格式"""
        d = {}
        for c in self.__table__.columns:
            if c.name == 'id':  # 跳过自增主键
                continue
            d[c.name] = self[c.name]
        return d

    def _recursive_resolve(self, path):
        """递归解析路径"""
        obj = self
        for attr in path.split('.'):
            if hasattr(obj, attr):
                obj = getattr(obj, attr)
            else:
                return None
        return obj

    def export_model(self):
        """导出模型数据为字典，包含外键解析"""
        res = self.as_dict()
        for fk, mapping in self.fk_to_resolve.items():
            res[fk] = self._recursive_resolve(mapping)
        return res


class Device(Base, DeviceDemoBase):
    """设备数据模型"""
    __tablename__ = 'device'  # 表名

    # 字段定义
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)  # 自增主键
    device_id = sqlalchemy.Column(sqlalchemy.String(36), nullable=False, unique=True)  # UUID，唯一约束
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, unique=True)  # 名称，非空且唯一
    dtype = sqlalchemy.Column(sqlalchemy.String(255), nullable=True, unique=False)  # 类型，可为空
    vendor = sqlalchemy.Column(sqlalchemy.String(255), nullable=True, unique=False)  # 厂商，可为空
    version = sqlalchemy.Column(sqlalchemy.String(255), nullable=True, unique=False)  # 版本，可为空

    def __repr__(self):
        # 字符串表示方法，用于调试
        return ('<Device[{uuid}]: '
                'device={device}>').format(
                    uuid=self.device_id,
                    device=self.name)

    def export_model(self):
        # 重写导出模型方法
        res = self.as_dict()
        for fk, mapping in self.fk_to_resolve.items():
            res[fk] = self._recursive_resolve(mapping)
        return res
