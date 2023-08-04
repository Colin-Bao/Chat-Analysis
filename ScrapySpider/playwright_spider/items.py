# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from sqlalchemy import Column, DateTime, String, Integer, func, Boolean, Unicode
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(String(200), primary_key=True)

    # 数据类型用于数据验证和数据库映射
    Name = Column(Unicode(100, collation='utf8mb4_unicode_ci'))
    online_status = Column(Boolean)
    company = Column(String(20))
    rank = Column(String(10))
    rank_2 = Column(String(10))
    website = Column(String(100))
    homepage = Column(String(200))
    crawl_date = Column(DateTime)
    crawl_date_2 = Column(DateTime)
    audio_url = Column(String(100))
    Age = Column(String(20))
    SexBg = Column(String(100))
    SexImg = Column(String(200))
    Online = Column(String(100))
    Position = Column(String(20))
    Grade = Column(String(20))
    GradePrice = Column(String(20))
    GradeImg = Column(String(200))
    Service = Column(String(100))
    ServiceSep = Column(String(100))
    Tag = Column(String(100))
    TagSep = Column(String(100))
    AvatarImg = Column(String(200))
    Profile = Column(String(200))

    #
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def create_id(self):
        hash_object = hashlib.sha256()
        combined_data = self.company + self.Name
        hash_object.update(combined_data.encode('utf-8'))
        return hash_object.hexdigest()


class UserItem(Item):
    """
    基础用户信息：在首页能获取到的一级信息
    """
    model = Field(serializer=User)

    def __init__(self, user):
        super().__init__()
        self['model'] = user
