# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface

import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.abspath('/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider'))
from items import UserUpdate, UserAppend  # noqa


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
        self.engine = create_engine('mysql+mysqlconnector://colin:^Q}spft2L0bmX^+=X=v0@140.250.51.124/duopei?charset=utf8mb4')
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
            date.online_status = True if ('在线' in (date.Online or '')) or ((date.Online or '') != '') else False

            return date

        # 创建新的session
        session = self.Session()

        # 将item转换为User对象并添加到session
        user_orm = item['model']
        crawl_mode_append = item['crawl_mode_append']

        # 数据清洗
        user_orm = clean_data(user_orm)

        # 追加模式
        if crawl_mode_append == 'true' or crawl_mode_append:
            session.add(user_orm)
            session.commit()

        # 更新模式
        else:
            existing_user = session.query(UserUpdate).filter_by(employee_id=user_orm.employee_id).one_or_none()
            # 存在employee_id 则更新
            if existing_user:
                existing_user.homepage = user_orm.homepage if user_orm.homepage else existing_user.homepage
                existing_user.audio_url = user_orm.audio_url if user_orm.audio_url else existing_user.homepage
                existing_user.crawl_date = user_orm.crawl_date
                existing_user.crawl_date_2 = user_orm.crawl_date_2
                session.commit()
            else:
                session.add(user_orm)
                session.commit()

        # 关闭session
        session.close()

        return item

    def close_spider(self, spider):
        self.engine.dispose()
