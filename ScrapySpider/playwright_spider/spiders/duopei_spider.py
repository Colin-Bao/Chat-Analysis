import logging

import json
from pathlib import Path
from scrapy import Spider
from scrapy.http import Request
import sys
import os

sys.path.append(os.path.abspath('/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider'))
from items import UserUpdate, UserAppend, UserItem  # noqa


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
            print('----------------收到参数-----------------', self.start_urls)
            meta = {'locator_dict': json.loads(self.json_data)[url]}
            meta.update(self.meta_dict)
            yield Request(url=url, callback=self.parse, meta=meta, errback=self.handle_error)

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
