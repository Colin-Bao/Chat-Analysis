import sys

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加Scrapy项目路径到系统路径
sys.path.extend(map(str, [Path("~/PycharmProjects/Chat-Analysis").expanduser(),
                          Path("~/PycharmProjects/Chat-Analysis/ScrapySpider").expanduser()]))

# 创建数据库会话
from ScrapySpider.playwright_spider.items import Company
from ScrapySpider.playwright_spider.private_config.config import sqlalchemy_uri

session = sessionmaker(bind=create_engine(sqlalchemy_uri))()

# 执行查询并获取结果列表
urls_list = [(url[0], url[1]) for url in session.query(Company.website, Company.company).all()]
print(urls_list)
