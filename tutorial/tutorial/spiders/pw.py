import json

import logging

from pathlib import Path
from scrapy import Spider
from scrapy.http import Response, Request


class ScrollSpider(Spider):
    name = "duopei-spider"
    custom_settings = {
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            # "DOWNLOAD_HANDLERS": {
            #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            # },
            "CONCURRENT_REQUESTS": 5,
            "LOG_LEVEL": "INFO",
            "FEEDS": {
                    '%(name)s-output.jsonlines': {'format': 'jsonlines', 'overwrite': False},
            }

    }
    start_urls = ['http://tj5uhmrpeq.duopei-m.featnet.com', 'http://oxxs5iqzqz.duopei-m.manongnet.cn',
                  'http://8mukjha763.duopei-m.99c99c.com']
    start_urls = ['http://tj5uhmrpeq.duopei-m.featnet.com']

    def start_requests(self):
        with open(
                '/Users/colin/Library/Mobile Documents/com~apple~CloudDocs/PycharmProjects/Chat-Analysis/DuopeiSpider/Utils/js_tools/user_selector.json',
                "r") as file:
            json_data = file.read()

        for url in self.start_urls:
            yield Request(url=url, callback=self.parse,
                          meta={'PlaywrightDownloaderMiddleware': True,
                                'Playwright_Headless': True,
                                'Playwright_Method': 'get_user_urls',
                                'locator_dict': json.loads(json_data)[url],
                                })

    def parse(self, response):
        logging.getLogger('sasaas').info('saaaaaaaaaaaaaaa')
        return {"url": response.url, 'body': json.loads(response.text)}

    # def handle_error(self, failure):
    #     # 处理请求错误
    #     self.log(failure.request.url + ' - ' + repr(failure))
