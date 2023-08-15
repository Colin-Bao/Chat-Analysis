# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface

import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ScrapySpider.playwright_spider.private_config.config import sqlalchemy_uri
from ScrapySpider.playwright_spider.items import UserUpdate


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class UserPipeline:
    """
    收集所有用户的数据，并创建DataFrame
    """

    def __init__(self):
        self.engine = None
        self.Session = None

    def open_spider(self, spider):
        # 创建数据库连接
        self.engine = create_engine(sqlalchemy_uri)
        self.Session = sessionmaker(bind=self.engine)

    def process_item(self, item, spider):
        """
        在 process_item 方法中逐条处理数据可能更有效。这也可以让你更早地发现并处理潜在的数据问题。
        """

        def clean_data(date):
            # 去除换行、回车、空格
            date.Name = date.Name.strip()
            date.TagSep = re.sub('\s+|\n', '', date.TagSep) if date.TagSep else None
            date.Tag = re.sub('\s+|\n', '', date.Tag) if date.Tag else None
            date.Tag = date.Tag if date.Tag else date.TagSep

            # 提取在线信息
            date.online_status = True if ('在线' in (date.Online or '')) else False

            return date

        # 创建新的session
        session = self.Session()

        # 将item转换为User对象并添加到session
        user_orm = item['model']
        db_mode = item['db_mode']

        # 数据清洗
        user_orm = clean_data(user_orm)

        # 追加模式/更新模式
        if db_mode == 'append':
            session.add(user_orm)
        else:
            # 获取或创建用户对象
            existing_user = session.query(UserUpdate).filter(UserUpdate.employee_id == user_orm.employee_id).first() or user_orm

            # 更新所有非空字段
            for col_name in UserUpdate.__table__.columns.keys():
                new_value = getattr(user_orm, col_name)
                if new_value is not None:
                    setattr(existing_user, col_name, new_value)

            # 合并更新
            session.merge(existing_user)

        # 关闭session
        session.commit()
        session.close()

        return item

    def close_spider(self, spider):
        self.engine.dispose()
