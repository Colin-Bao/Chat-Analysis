# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import pandas as pd
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
class PWDownloaderMiddleware:

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

    async def click_button_by_selector(self, page, button_selector: str):
        await page.evaluate('''
        var elements = document.querySelectorAll(".van-overlay, .van-dialog");
        if(elements.length > 0) {
            elements.forEach((element) => {
                element.parentNode.removeChild(element);
            });
        }
        ''')
        # if button_selector:
        #     button_locator = page.locator(button_selector)
        #     if await button_locator.count():
        #         text = await button_locator.all_inner_texts()
        #         logging.getLogger('').info(text)
        #         await button_locator.highlight()
        #         await page.evaluate('''
        #                     (selector) => {const element = document.querySelector(selector);
        #                     if (element) {element.parentNode.removeChild(element);}}''', button_selector)

        # await button_locator.click(timeout=1000)

        # await page.wait_for_timeout(1000)

    async def parse_clerk(self, request, page: Page) -> [{}, ...]:
        """
        店员信息解析
        :return:
        """

        # 提取用户信息JS代码
        JS_USER_INFO = '''
        O => {
            const elements = document.querySelectorAll(O.userSelector);
            const data = [];
            let index = 0;
        
            // Add the current time
            const now = new Date();
            const nowFormatted = now.toISOString().slice(0, 19).replace('T', ' ');
        
            for (const element of elements) {
                const row = {};
                row['rank_2'] = index;
                index = index + 1
                row['crawl_date_2'] = nowFormatted;
                for (const [attr, classname] of Object.entries(O.itemDict)) {
                    const subElement = element.querySelector(classname);
                    if (subElement) {
                        let textContent;
                        if (attr === 'Sex') {
                            textContent = subElement.getAttribute("style").trim();
                        } else if (attr === 'GradeImg') {
                            textContent = subElement.getAttribute("src").trim();
                        } else if (attr === 'SexImg') {
                            textContent = subElement.getAttribute("src").trim();
                        } else {
                            textContent = subElement.textContent.trim();
                        }
                        row[attr] = textContent;
                    }
                }
        
                if (Object.keys(O.itemDict).every(key => key in row)) {
                    data.push(row);
                }
            }
            return data;
        }
                        '''

        # 定位器字典
        el_dict = request.meta.get('locator_dict')
        # logging.getLogger('定位器字典').info(el_dict)

        # 提取
        user_dict_list = await page.evaluate(JS_USER_INFO,
                                             {"userSelector": el_dict['user_card_selector'],
                                              'itemDict': el_dict['user_info_selector']})

        return user_dict_list

    async def get_user_info(self, request, page: Page) -> {}:
        # 定位器字典
        el_dict = request.meta.get('locator_dict')

        # 滚动页面
        await self.scroll_page(page.locator(el_dict['user_card_selector']), page.locator(el_dict['page_finished_selector']))

        # 常规爬虫
        user_dict_list = await self.parse_clerk(request, page)
        # logging.getLogger('常规爬虫').info(user_dict_list)

        # 按需调用url爬虫
        if request.meta.get('use_url_crawl', False):
            url_dict_list = await self.get_user_urls(request, page)

            return {'res': [{**d1, **d2} for d1, d2 in zip(url_dict_list, user_dict_list)]}
        else:
            return {'res': user_dict_list}

    async def get_user_urls(self, request, page: Page) -> [{}, ...]:
        # 定位器字典
        el_dict = request.meta.get('locator_dict')

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
            # logging.getLogger('元素数量').info(element)

            try:
                # 将元素滚动到视野中
                await element.scroll_into_view_if_needed()
                await self.click_button_by_selector(page, el_dict.get('login_button_selector', None))  # 点击登录提示框

                # 解析音频
                audio_locator = element.locator(el_dict['user_audio_selector'])
                async with page.expect_response(lambda response: 'mp3' in response.url) as response_info:
                    await audio_locator.click()

                # 模拟点击元素
                await element.highlight()
                await element.click()
                await page.wait_for_url('**/detail/**')  # 等待页面跳转

                # 获取并打印新页面的URL
                if 'detail' in page.url:
                    user_dict['homepage'] = page.url
                    user_dict['website'] = request.url
                    user_dict['rank'] = i
                    user_dict['crawl_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    user_dict['audio_url'] = (await response_info.value).url
                    user_dict_list.append(user_dict)
                else:
                    pass

            except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
                # await page.screenshot(path=f'{i}.png')
                continue

            finally:
                # 回到原始页面
                if 'detail' in page.url:
                    await page.go_back()

        return user_dict_list

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
        spider.logger.info(f"{spider.name} Spider opened Use {__class__.__name__}")
