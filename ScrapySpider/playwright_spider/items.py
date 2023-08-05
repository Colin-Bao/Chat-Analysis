# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from sqlalchemy import Column, DateTime, String, Integer, func, Boolean, Unicode, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()


class UserUpdate(Base):
    #
    __tablename__ = 'user_update'

    #
    employee_id = Column(String(200), primary_key=True)

    # 数据类型用于数据验证和数据库映射
    Name = Column(Unicode(100, collation='utf8mb4_unicode_ci'), default=None)
    online_status = Column(Boolean, default=None)
    company = Column(String(20), default=None)
    rank = Column(String(10), default=None)
    rank_2 = Column(String(10), default=None)
    website = Column(String(100), default=None)
    homepage = Column(String(200), default=None)
    crawl_date = Column(DateTime, default=None)
    crawl_date_2 = Column(DateTime, default=None)
    audio_url = Column(String(100), default=None)
    Age = Column(String(20), default=None)
    SexBg = Column(String(100), default=None)
    SexImg = Column(String(200), default=None)
    Online = Column(String(100), default=None)
    Position = Column(String(20), default=None)
    Grade = Column(String(20), default=None)
    GradePrice = Column(String(20), default=None)
    GradeImg = Column(String(200), default=None)
    Service = Column(String(100), default=None)
    ServiceSep = Column(String(100), default=None)
    Tag = Column(String(100), default=None)
    TagSep = Column(String(100), default=None)
    AvatarImg = Column(String(200), default=None)
    Profile = Column(String(200), default=None)

    #
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def create_employee_id(self):
        hash_object = hashlib.sha256()
        combined_data = self.company + self.Name
        hash_object.update(combined_data.encode('utf-8'))
        return hash_object.hexdigest()


class UserAppend(UserUpdate):
    """
    新增用户信息
    """
    __tablename__ = 'user_append'

    # 主键和外键
    id = Column(String(200), primary_key=True)
    employee_id = Column(String(200), ForeignKey('user_update.employee_id'))

    def create_id(self):
        hash_object = hashlib.sha256()
        combined_data = str(self.created_at) + self.company + self.Name
        hash_object.update(combined_data.encode('utf-8'))
        return hash_object.hexdigest()


class UserItem(Item):
    """
    封装的ORM对象，用于传递给pipeline
    附加一些额外信息
    """
    model = Field()
    crawl_mode_append = Field()

    def __init__(self, user, crawl_mode_append):
        super().__init__()
        self['model'] = user
        self['crawl_mode_append'] = crawl_mode_append
