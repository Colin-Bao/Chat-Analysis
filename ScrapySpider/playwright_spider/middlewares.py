# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os

from pathlib import Path

import logging

from datetime import datetime
import json
from scrapy import signals
# useful for handling different item types with a single interface
from scrapy.http import Response, Request, HtmlResponse
from playwright.async_api import async_playwright, Page, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from tqdm import tqdm


# noinspection PyMethodMayBeStatic
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

    async def remove_node_by_selector(self, page, remove_selector: str):
        if remove_selector:
            await page.evaluate('''
                    O => {
                        var elements = document.querySelectorAll(O);
                        if(elements.length > 0) {
                            elements.forEach((element) => {
                                element.parentNode.removeChild(element);
                            });
                        }
                    }
                    ''', remove_selector)

        # logging.getLogger('移除节点').info(f'移除节点：{remove_selector}')
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
                row['company'] = O.company;
                row['website'] = O.website;
                for (const [attr, classname] of Object.entries(O.itemDict)) {
                    const subElement = element.querySelector(classname);
                    if (subElement) {
                        let textContent;
                        if (attr === 'SexBg') {
                            textContent = subElement.getAttribute("style").trim();
                        } else if (attr === 'GradeImg') {
                            textContent = subElement.getAttribute("src").trim();
                        } else if (attr === 'SexImg') {
                            textContent = subElement.getAttribute("src").trim();
                        } else if (attr === 'AvatarImg') {
                            textContent = subElement.getAttribute("src").trim();
                        } else if (attr === 'TagSep') {
                            let texts = Array.from(subElement.querySelectorAll("span"), span => span.textContent.trim());
                            textContent = texts.join('|');
                        } else if (attr === 'ServiceSep') {
                            let texts = Array.from(subElement.querySelectorAll("span"), span => span.textContent.trim());
                            textContent = texts.join('|');
                        }  
                        else {
                            textContent = subElement.textContent.trim();
                        }
                        row[attr] = textContent;
                    }
                    else{
                        row[attr] = classname;
                    }
                }
                data.push(row);
                //if (Object.keys(O.itemDict).every(key => key in row)) {
                //    data.push(row);
                //}
            }
            return data;
        }
        '''

        # 定位器字典
        el_dict = request.meta.get('locator_dict')
        logging.getLogger('parse_clerk').info(f"店员信息解析：{request.url}, {el_dict['company']}")

        # JS提取
        user_dict_list = await page.evaluate(JS_USER_INFO,
                                             {"userSelector": el_dict['user_card_selector'],
                                              'itemDict': el_dict['user_info_selector'],
                                              'company': el_dict['company'],
                                              'website': request.url})  # 增加需要的信息
        return user_dict_list

    async def get_user_info(self, request, page: Page, debug_batch: int = 5) -> {}:
        """
        获取用户信息
        :param debug_batch: 用于小批量调试
        :param request:
        :param page:
        :return: 返回用户信息字典
        """

        # 定位器字典
        el_dict = request.meta.get('locator_dict')

        # 改变class
        change_body_selector = el_dict.get('change_body_selector', None)
        if change_body_selector:
            await page.evaluate("""O=>{document.querySelector(O).className ="";} """, el_dict.get('change_body_selector', None))

        # 删除元素
        await self.remove_node_by_selector(page, el_dict.get('remove_dialog_selector', None))

        # 滚动页面
        await self.scroll_page(page.locator(el_dict['user_card_selector']), page.locator(el_dict['page_finished_selector']))

        # 删除元素
        await self.remove_node_by_selector(page, el_dict.get('remove_dialog_selector', None))

        # 常规爬虫
        user_dict_list = await self.parse_clerk(request, page)

        # 截断
        user_dict_list = user_dict_list[:min(debug_batch, len(user_dict_list))]
        # logging.getLogger('常规爬虫').info(user_dict_list)

        # 按需调用url爬虫
        if request.meta.get('use_url_crawl', False):
            url_dict_list = await self.get_user_urls(request, page, debug_batch)
            assert len(url_dict_list) == len(user_dict_list)  # 保证数量一致
            return {'res': [{**d1, **d2} for d1, d2 in zip(url_dict_list, user_dict_list)]}
        else:
            return {'res': user_dict_list}

    async def get_user_urls(self, request, page: Page, debug_batch) -> [{}, ...]:
        """
        复杂的url爬虫，经常遇到网络响应问题
        :param request:
        :param page:
        :param debug_batch:调试数量
        """

        # 设置超时
        # page.set_default_timeout(2000)

        # 定位器字典
        el_dict = request.meta.get('locator_dict')

        # 定义截图路径
        screenshot_dir = Path(__file__).resolve().parent / 'screenshot' / f"{el_dict['company']}"
        os.makedirs(screenshot_dir, exist_ok=True)

        # 移除阻碍元素
        await self.remove_node_by_selector(page, el_dict.get('remove_other_selector', None))
        await self.remove_node_by_selector(page, el_dict.get('remove_dialog_selector', None))

        # 定位到具有跳转链接的元素
        click_locators = page.locator(el_dict['user_card_selector'])

        # 获取元素的数量
        elements_count = await click_locators.count()
        user_dict_list = []

        for i in tqdm(range(elements_count)[:min(debug_batch, elements_count)]):
            # 用于存储信息的字典
            user_dict = {'rank': i,
                         'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         'audio_url': None,
                         'homepage': None, }

            try:
                # ---------------------------------- 定位元素 ---------------------------------- #
                try:
                    # 移除阻碍元素
                    await self.remove_node_by_selector(page, el_dict.get('remove_dialog_selector', None))

                    # 定位当前元素
                    element = click_locators.nth(i)
                    await element.highlight()

                    # 将元素滚动到视野中
                    await element.scroll_into_view_if_needed()
                    # 记录
                    await page.screenshot(path=screenshot_dir / f'{i}.png')
                    await element.wait_for(state='visible', timeout=1000)  # 等待元素稳定


                except Exception as e:
                    # 捕获异常截图
                    await page.screenshot(path=screenshot_dir / f'{i}_locater.png', )
                    raise Exception(f"元素定位错误 {e}") from e

                # ---------------------------------- 解析音频 ---------------------------------- #
                try:
                    audio_locator = element.locator(el_dict['user_audio_selector'])
                    await audio_locator.highlight()
                    async with page.expect_response(lambda response: 'mp3' in response.url, timeout=1500) as response_info:
                        await audio_locator.click(timeout=1000)
                    user_dict['audio_url'] = (await response_info.value).url
                except Exception as e:
                    # 捕获异常截图
                    # await page.screenshot(path=screenshot_dir / f'{i}_audio.png')
                    raise Exception(f"解析音频错误 {e}") from e

                # ---------------------------------- 解析url跳转 ---------------------------------- #
                try:
                    await element.highlight()
                    await element.click()
                    await page.wait_for_url(url='**/detail/**', wait_until='domcontentloaded', timeout=1000)
                    user_dict['homepage'] = page.url
                    await page.go_back()  # 回到原始页面
                except Exception as e:
                    # 捕获异常截图
                    # await page.screenshot(path=screenshot_dir / f'{i}_url.png')
                    raise Exception(f"解析url跳转错误 {e}") from e


            except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
                logging.getLogger('get_user_urls').error(f"[{el_dict['company']} {e}")
                continue

            finally:
                # 任何失败都添加
                user_dict_list.append(user_dict)

        return user_dict_list

    async def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        if request.meta.get('PWDownloaderMiddleware') and not request.meta.get('handled'):
            # logging.getLogger('process_request').info(f"使用中间件：{request.url}")
            # 启动浏览器
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=request.meta.get('Playwright_Headless'),
                                                       args=[
                                                               '--disable-gpu',
                                                               # '--enable-gpu',  #
                                                               '--disable-software-rasterizer',
                                                       ]
                                                       )
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
