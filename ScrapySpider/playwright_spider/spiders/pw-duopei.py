import json
from pathlib import Path
from scrapy import Spider
from scrapy.http import Request
from ..items import User, UserItem


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
            # "FEEDS": {
            #         'data/%(name)s.jsonlines': {'format': 'jsonlines', 'overwrite': True, 'encoding': 'utf8'},
            # }
    }

    # 读取定位器文件
    file_path = Path(__file__).resolve().parent.parent / 'data' / 'user_selector.json'
    with open(file_path, "r", encoding='utf-8') as file:
        json_data = file.read()

    start_urls = list(json.loads(json_data).keys())

    # start_urls = ['http://8mukjha763.duopei-m.99c99c.com']
    # start_urls = ['http://exjomkwuav.duopei-m.manongnet.cn']  # 新增

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                    url=url, callback=self.parse,
                    meta={'PWDownloaderMiddleware': True,
                          'Playwright_Headless': True,
                          'Playwright_Method': 'get_user_info',
                          'use_url_crawl': True,
                          'locator_dict': json.loads(self.json_data)[url],
                          }
            )

    def parse(self, response, **kwargs):
        # 抓取数据
        for user_data in json.loads(response.body)['res']:
            # 创建 User 对象
            user = User(**user_data)
            user.id = user.create_id()
            # 创建 Item 对象
            item = UserItem(user)
            # yield user 对象
            yield item

    def handle_error(self, failure):
        # 处理请求错误
        self.log(failure.request.url + ' - ' + repr(failure))
