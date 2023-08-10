# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from sqlalchemy import Column, DateTime, String, Integer, func, Boolean, Unicode, ForeignKey, create_engine, event
from sqlalchemy.orm import declarative_base, declared_attr, relationship, validates, object_session, sessionmaker
import hashlib

Base = declarative_base()


class UserBase(Base):
    __abstract__ = True  # Declare this class as abstract

    # 表名
    # @declared_attr
    # def __tablename__(self):
    #     return self.__name__.lower()  # Use the class name as table name

    # 用户ID
    employee_id = Column(String(200), primary_key=True, nullable=False)

    # 数据类型用于数据验证和数据库映射
    Name = Column(Unicode(100, collation='utf8mb4_unicode_ci'))
    online_status = Column(Boolean, default=None)
    company = Column(String(20))
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
    Online = Column(String(200), default=None)
    Position = Column(String(20), default=None)
    Grade = Column(String(20), default=None)
    GradePrice = Column(String(20), default=None)
    GradeImg = Column(String(200), default=None)
    Service = Column(String(200), default=None)
    ServiceSep = Column(String(200), default=None)
    Tag = Column(String(100), default=None)
    TagSep = Column(String(100), default=None)
    AvatarImg = Column(String(200), default=None)
    Profile = Column(String(200), default=None)

    # 数据库记录
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def create_employee_id(self):
        hash_object = hashlib.sha256()
        combined_data = self.company + self.Name
        hash_object.update(combined_data.encode('utf-8'))
        return hash_object.hexdigest()


class UserUpdate(UserBase):
    #
    __tablename__ = 'user_update'

    # 依赖关系
    children = relationship("UserAppend", back_populates="parent")


class UserAppend(UserBase):
    """
    新增用户信息
    """
    __tablename__ = 'user_append'

    # 依赖关系
    parent = relationship("UserUpdate", back_populates="children")

    # 主键和外键
    append_id = Column(String(200), primary_key=True)
    employee_id = Column(String(200), ForeignKey('user_update.employee_id'))

    def create_append_id(self):
        hash_object = hashlib.sha256()
        combined_data = str(self.crawl_date_2) + self.company + self.Name
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


# 外键约束
def before_insert_listener(mapper, connection, target):
    # Check if the employee_id exists in the UserUpdate table
    user_update_record = connection.scalar(
            UserUpdate.__table__.select().where(UserUpdate.employee_id == target.employee_id)
    )

    # 新记录
    data_to_insert = {key: value for key, value in target.__dict__.items() if key not in ('id', 'append_id', '_sa_instance_state')}

    # If not, insert a new record into UserUpdate
    if not user_update_record:
        # Create a dictionary with all the fields from UserAppend, except the id
        # Insert the new record into UserUpdate
        connection.execute(UserUpdate.__table__.insert().values(**data_to_insert))

    else:
        # If exists, update the UserUpdate record with new data from UserAppend
        connection.execute(
                UserUpdate.__table__.update().where(UserUpdate.employee_id == target.employee_id).values(**data_to_insert)
        )


event.listen(UserAppend, 'before_insert', before_insert_listener)
engine = create_engine('mysql+mysqlconnector://colin:^Q}spft2L0bmX^+=X=v0@140.250.51.124/duopei?charset=utf8mb4')  # Adjust the connection string
Session = sessionmaker(bind=engine)
session = Session()

# Create tables
Base.metadata.create_all(engine)
