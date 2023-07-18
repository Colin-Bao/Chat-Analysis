from pathlib import Path

from scrapy import Spider, Request
from scrapy_playwright.page import PageMethod


class ScrollSpider(Spider):
    """Scroll down on an infinite-scroll page."""

    name = "scroll"
    custom_settings = {
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            # "DOWNLOAD_HANDLERS": {
            #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            # },
            "LOG_LEVEL": "INFO",

    }

    def start_requests(self):
        yield Request(
                url="http://tj5uhmrpeq.duopei-m.manongnet.cn", meta={'playwright': True}
        )

    def parse(self, response):
        return {"url": response.url, "count": response}
