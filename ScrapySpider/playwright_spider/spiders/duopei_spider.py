import json
from scrapy import Spider
from scrapy.http import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sys

# 自定义模块
SCRAPY_ROOT_PATH = Path("~/PycharmProjects/Chat-Analysis").expanduser()
sys.path.extend([str(SCRAPY_ROOT_PATH), str(SCRAPY_ROOT_PATH / 'ScrapySpider')])

from ScrapySpider.playwright_spider.items import UserUpdate, UserAppend, UserItem, Company  # noqa
from ScrapySpider.playwright_spider.private_config.config import sqlalchemy_uri  # noqa


class DuopeiSpider(Spider):
    name = "duopei"
    custom_settings = {
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "CONCURRENT_REQUESTS": 1,
            "LOG_LEVEL": "INFO",
            "TELNETCONSOLE_ENABLED": False,
            "COOKIES_ENABLED": False,
            'ROBOTSTXT_OBEY': False,

    }

    def __init__(self, start_url: str, crawl_info: list, db_mode, **kwargs):
        super(DuopeiSpider, self).__init__(**kwargs)

        # 创建数据库会话
        engine = create_engine(sqlalchemy_uri)  # 使用你的数据库连接字符串
        Session = sessionmaker(bind=engine)
        session = Session()

        # 执行查询
        query_result = session.query(Company).all()

        # 初始化结果字典
        self.selector_dict = {}

        # 遍历查询结果并构造字典
        for obj in query_result:
            website = obj.website  # 假设url是CompanySelector类的一个属性
            other_attributes = {key: value for key, value in obj.__dict__.items() if key != 'website' and key != '_sa_instance_state'}
            self.selector_dict[website]: dict = other_attributes

        # 创建start_urls列表
        self.start_urls = [start_url]

        # Set default meta values
        self.meta_dict = {
                'PWDownloaderMiddleware': True,
                'Playwright_Headless': True,
                'db_mode': db_mode,
                'crawl_info': crawl_info
        }

        # Override default meta values
        self.meta_dict.update(kwargs)

    def start_requests(self):
        for url in self.start_urls:
            print('--------------------------------收到参数-------------------------------- \n', self.start_urls, self.meta_dict)
            meta = self.meta_dict
            meta.update({'locator_dict': self.selector_dict[url]})  # noqa
            yield Request(url=url, callback=self.parse, meta=meta, errback=self.handle_error)

    def parse(self, response, **kwargs):
        # 抓取数据
        # print('----------------开始抓取数据-----------------', json.loads(response.body))
        for user_data in json.loads(response.body)['res']:
            # 创建 User 对象
            match self.meta_dict['db_mode']:
                case 'append':
                    user = UserAppend(**user_data)
                    user.append_id = user.create_append_id()
                case 'update':
                    user = UserUpdate(**user_data)
                case _:
                    raise ValueError(f'Invalid db_mode: {self.meta_dict["db_mode"]}')

            # 生成 employee_id
            user.employee_id = user.create_employee_id()

            # 创建 Item 对象
            item = UserItem(user, self.meta_dict['db_mode'])

            # yield user 对象
            yield item

    def handle_error(self, failure):
        """
        handle_spider_error方法连接到spider_error信号。
        如果在parse方法或任何其他爬虫回调中引发异常，handle_spider_error将被调用，并传递一个failure对象，包含有关错误的详细信息。
        :param failure:
        :return:
        """
        # 处理请求错误
        self.logger.error(f'Error occurred while processing : {failure.value}')

        # 重新引发异常，使其向上抛出
        raise failure.value
