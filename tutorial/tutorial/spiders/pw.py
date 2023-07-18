import json

import logging
from pathlib import Path
from scrapy import Spider, Item, Field
from scrapy.http import Response, Request


class BaseUserItem(Item):
    """
    基础用户信息：在首页能获取到的一级信息
    """
    rank, website, homepage, crawl_date, audio_url, Name, Age, SexImg, Online, Position, GradeImg, Grade, Service = Field(), Field(), Field(), \
        Field(), Field(), Field(), Field(), Field(), Field(), Field(), Field(), Field(), Field()


#
# "Name": ".name.text-ellipsis",
#       "Age": ".sex-age",
#       "SexImg": ".sex-age img",
#       "Online": ".switch-name",
#       "Position": ".position.align-center",
#       "GradeImg": ".clerk-item__body > div:nth-child(2) > img",
#       "Service":
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
                    'data/%(name)s.jsonlines': {'format': 'jsonlines', 'overwrite': True, 'encoding': 'utf8'},
            }

    }
    start_urls = ['http://tj5uhmrpeq.duopei-m.featnet.com', 'http://oxxs5iqzqz.duopei-m.manongnet.cn',
                  'http://8mukjha763.duopei-m.99c99c.com', 'http://9uybjxsbfh.duopei-m.manongnet.cn']
    # start_urls = ['http://tj5uhmrpeq.duopei-m.featnet.com']

    def start_requests(self):
        with open(
                '/Users/colin/Library/Mobile Documents/com~apple~CloudDocs/PycharmProjects/Chat-Analysis/DuopeiSpider/Utils/js_tools/user_selector.json',
                "r") as file:
            json_data = file.read()

        for url in self.start_urls:
            yield Request(url=url, callback=self.parse,
                          meta={'PlaywrightDownloaderMiddleware': True,
                                'Playwright_Headless': True,
                                'Playwright_Method': 'get_user_info',
                                'use_url_crawl': True,
                                'locator_dict': json.loads(json_data)[url],
                                })

    def parse(self, response):
        for user in json.loads(response.body)['res']:
            item = BaseUserItem()
            for i in list(item.fields.keys()):
                if i in user.keys():
                    item[i] = user[i]
            yield item

    def handle_error(self, failure):
        # 处理请求错误
        self.log(failure.request.url + ' - ' + repr(failure))
