# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from datetime import datetime

import json

import time

import asyncio

from scrapy import signals
import logging
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import Response, Request, HtmlResponse
from playwright.async_api import async_playwright, Page, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from tqdm import tqdm


class TutorialSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


# noinspection PyMethodMayBeStatic
class PlaywrightDownloaderMiddleware:

    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    async def scroll_page(self, bottom_item_locator: Locator, finished_item_locator: Locator):
        """
        滚动页面
        :param bottom_item_locator: 底部元素定位器
        :param finished_item_locator: 完成元素定位器
        :return:
        """
        while True:
            await bottom_item_locator.last.scroll_into_view_if_needed()
            if await finished_item_locator.count():
                break

    async def get_user_urls(self, request, page: Page) -> {}:
        el_dict = request.meta.get('locator_dict')

        # 点击提示框
        # await page.click(el_dict['dialog_button_selector']) if el_dict.get('dialog_button_selector', None) else None

        # 2.滚动页面
        await self.scroll_page(page.locator(el_dict['user_card_selector']), page.locator(el_dict['page_finished_selector']))

        # 定位到具有跳转链接的元素
        click_locators = page.locator(el_dict['user_card_selector'])

        # 获取元素的数量
        elements_count = await click_locators.count()
        user_dict_list = []

        for i in tqdm(range(elements_count)):
            # 用于存储URL的字典
            user_dict = {}
            # 获取单个元素
            element = click_locators.nth(i)

            try:
                # 将元素滚动到视野中
                await element.scroll_into_view_if_needed()

                # 模拟点击元素
                # await self.remove_dialog(page, url)  # 移除通知框
                await element.click()
                await page.wait_for_load_state('networkidle')  # 等待点击事件

                # 获取并打印新页面的URL
                if 'detail' in page.url:
                    user_dict['user_url'] = page.url
                    user_dict['source'] = request.url
                    user_dict['rank'] = i
                    user_dict['crawl_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    user_dict_list.append(user_dict)
                    # 回到原始页面
                    await page.go_back()

                else:
                    pass
            except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
                await page.screenshot(path=f'{i}.png')
                continue

            # if i >= 5: break

        return {'res': user_dict_list}

    async def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        if request.meta.get('PlaywrightDownloaderMiddleware') and not request.meta.get('handled'):
            # 启动浏览器
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=request.meta.get('Playwright_Headless'))
            page = await browser.new_page()

            # 禁用图片
            await page.route('**/*', lambda route: route.abort() if route.request.resource_type == 'image' else route.continue_())
            await page.goto(request.url)

            # 根据传入的方法不同执行不同的逻辑
            res = await getattr(self, request.meta.get('Playwright_Method'))(request, page)

            # 标记已经处理过
            await page.close()
            request.meta['handled'] = True
            # logging.getLogger('detail').info(res)
            return HtmlResponse(url=request.url, body=json.dumps(res).encode('utf-8'), encoding='utf-8', request=request)
        else:
            return None
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

    async def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        # return response
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("中间件 Spider opened: %s" % spider.name)
