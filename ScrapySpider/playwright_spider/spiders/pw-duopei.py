import json

import logging
from pathlib import Path
from scrapy import Spider, Item, Field
from scrapy.http import Response, Request


class DuopeiSpider(Spider):
    name = "duopei"
    custom_settings = {
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            # "DOWNLOAD_HANDLERS": {
            #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            # },
            "CONCURRENT_REQUESTS": 2,
            "LOG_LEVEL": "INFO",
            "FEEDS": {
                    'data/%(name)s.jsonlines': {'format': 'jsonlines', 'overwrite': True, 'encoding': 'utf8'},
            }
    }

    # 读取定位器文件
    with open(
            '/Users/colin/Library/Mobile Documents/com~apple~CloudDocs/PycharmProjects/Chat-Analysis/DuopeiSpider/Utils/js_tools/user_selector.json',
            "r") as file:
        json_data = file.read()

    start_urls = list(json.loads(json_data).keys())

    # start_urls = ['http://8mukjha763.duopei-m.99c99c.com']
    # start_urls = ['http://oxxs5iqzqz.duopei-m.manongnet.cn'] # 最快的
    # start_urls = ['http://bisevslwz1.duopei-m.manongnet.cn']  # 新增

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse,
                          meta={'PWDownloaderMiddleware': True,
                                'Playwright_Headless': True,
                                'Playwright_Method': 'get_user_info',
                                'use_url_crawl': True,
                                'locator_dict': json.loads(self.json_data)[url],
                                })

    def parse(self, response):
        from ..items import UserItem
        for user in json.loads(response.body)['res']:
            item = UserItem()
            item = {field: user.get(field, None) for field in item.fields.keys()}
            yield item

    def handle_error(self, failure):
        # 处理请求错误
        self.log(failure.request.url + ' - ' + repr(failure))
