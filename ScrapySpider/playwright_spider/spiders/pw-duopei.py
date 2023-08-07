import logging

import json
from pathlib import Path
from scrapy import Spider
from scrapy.http import Request
from ..items import UserUpdate, UserAppend, UserItem


class DuopeiSpider(Spider):
    name = "duopei"
    custom_settings = {
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "CONCURRENT_REQUESTS": 1,
            "LOG_LEVEL": "INFO",
            "TELNETCONSOLE_ENABLED": False,
            "COOKIES_ENABLED": False,
    }

    def __init__(self, start_url: str = None, **kwargs):
        super(DuopeiSpider, self).__init__(**kwargs)

        # 读取定位器文件并创建start_urls列表
        file_path = '/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider/data/user_selector.json'
        with open(file_path, "r", encoding='utf-8') as file:
            self.json_data = file.read()
        self.start_urls = [start_url]
        # logging.getLogger('log').error(f'读取定位器文件并创建start_urls列表 {self.start_urls}')

        # Set default meta values
        self.meta_dict = {
                'PWDownloaderMiddleware': True,
                'Playwright_Headless': True,
                'Playwright_Method': 'get_user_info',
                'use_url_crawl': False,
                'crawl_mode_append': True
        }

        # Override default meta values with any parameters passed from the command line
        self.meta_dict.update(kwargs)

    def start_requests(self):
        for url in self.start_urls:
            meta = {'locator_dict': json.loads(self.json_data)[url]}
            meta.update(self.meta_dict)
            yield Request(url=url, callback=self.parse, meta=meta)

    def parse(self, response, **kwargs):
        # 抓取数据
        for user_data in json.loads(response.body)['res']:
            # 创建 User 对象
            if self.meta_dict['crawl_mode_append'] == 'true' or self.meta_dict['crawl_mode_append']:
                user = UserAppend(**user_data)
                user.append_id = user.create_append_id()
            else:
                user = UserUpdate(**user_data)

            # 生成 employee_id
            user.employee_id = user.create_employee_id()

            # 创建 Item 对象
            item = UserItem(user, self.meta_dict['crawl_mode_append'])

            # yield user 对象
            yield item

    def handle_error(self, failure):
        # 处理请求错误
        self.log(failure.request.url + ' - ' + repr(failure))
