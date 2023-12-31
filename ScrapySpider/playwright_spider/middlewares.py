# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


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
            await bottom_item_locator.last.scroll_into_view_if_needed(timeout=10000)
            if await finished_item_locator.count():
                break

    async def remove_node_by_selector(self, page, remove_selector: str):
        """
        通过选择器移除节点
        :param page:
        :param remove_selector:
        :return:
        """
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

    async def parse_clerk_basic(self, request, page: Page) -> [{}, ...]:
        """
        店员信息解析
        :return:
        """

        # 提取用户信息JS代码
        js_user_info = '''
        O => {
            const elements = document.querySelectorAll(O.user_card_selector);
            const data = [];
            let index = 0;
        
            // Add the current time
            const now = new Date();
            const nowFormatted = now.toISOString().slice(0, 19).replace('T', ' ');
        
            for (const element of elements) {
                
                // 额外元数据
                const row = {};
                row['rank_2'] = index;
                index = index + 1
                row['crawl_date_2'] = nowFormatted;
                
                // 基本信息解析
                for (let [attr, classname] of Object.entries(O)) {
                    if (['user_card_selector','remove_dialog_selector', 'remove_other_selector', 'page_finished_selector', 'user_audio_selector'].includes(attr)) {
                        continue;
                    }
                    attr = attr.replace('_selector', '');
                    const subElement = element.querySelector(classname);
                    
                    // 定位成功
                    if (subElement) {
                        let textContent;
                        switch (attr) {
                              case 'SexBg':
                                textContent = subElement.getAttribute("style").trim();
                                break;
                              case 'GradeImg':
                              case 'SexImg':
                              case 'AvatarImg':
                                textContent = subElement.getAttribute("src").trim();
                                break;
                              case 'TagSep':
                              case 'ServiceSep':
                                let texts = Array.from(subElement.querySelectorAll("span"), span => span.textContent.trim());
                                textContent = texts.join('|');
                                break;
                              default:
                                textContent = subElement.textContent.trim();
                        }
                        row[attr] = textContent;
                    }
                    // 定位失败
                    else{
                        row[attr] = classname;
                    }
                }
                
                // 合并数据
                data.push(row);
            }
            return data;
        }
        '''

        # 定位器字典
        locator_dict = {k: v for k, v in request.meta['locator_dict'].items() if k not in
                        ['remove_dialog_selector', 'remove_other_selector', 'page_finished_selector', 'user_audio_selector']}

        logging.getLogger('parse_clerk').info(f"店员信息解析：{request.url}, {locator_dict['company']}")

        # JS提取
        user_dict_list = await page.evaluate(js_user_info, locator_dict)
        return user_dict_list

    async def parse_clerk_audio_homepage(self, request, page: Page, crawl_info: str, debug_batch) -> [{}, ...]:
        """
        复杂的url爬虫，经常遇到网络响应问题
        :param crawl_info:
        :param request:
        :param page:
        :param debug_batch:调试数量
        """

        # 设置超时
        # page.set_default_timeout(2000)

        # 定位器字典
        locator_dict = request.meta['locator_dict']

        # 定义截图路径
        # screenshot_dir = Path(__file__).resolve().parent / 'screenshot' / f"{el_dict['company']}"
        # os.makedirs(screenshot_dir, exist_ok=True)

        # 移除阻碍元素
        await self.remove_node_by_selector(page, locator_dict['remove_other_selector'])
        await self.remove_node_by_selector(page, locator_dict['remove_dialog_selector'])

        # 定位到具有跳转链接的元素
        click_locators = page.locator(locator_dict['user_card_selector'])

        # 获取元素的数量
        elements_count = await click_locators.count()
        user_dict_list = []

        for i in tqdm(range(elements_count)[:min(debug_batch, elements_count)]):
            # ---------------------------------- 用于存储信息的字典 ---------------------------------- #
            user_dict = {'rank': i,
                         'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         'audio_url': None,
                         'homepage': None, }

            try:
                # ---------------------------------- 定位元素 ---------------------------------- #
                try:
                    # 移除阻碍元素
                    await self.remove_node_by_selector(page, locator_dict['remove_dialog_selector'])

                    # 定位当前元素
                    element = click_locators.nth(i)
                    await element.highlight()

                    # 将元素滚动到视野中
                    await element.scroll_into_view_if_needed()

                    # 移除阻碍元素
                    await self.remove_node_by_selector(page, locator_dict['remove_dialog_selector'])

                    # 记录
                    # await page.screenshot(path=screenshot_dir / f'{i}.png')
                    await element.wait_for(state='visible', timeout=1000)  # 等待元素稳定

                except Exception as e:
                    # 捕获异常截图
                    # await page.screenshot(path=screenshot_dir / f'{i}_locater.png', )
                    raise Exception(f"元素定位错误 {e}") from e

                match crawl_info:

                    # ---------------------------------- 解析音频 ---------------------------------- #
                    case 'audio':
                        try:
                            audio_locator = element.locator(locator_dict['user_audio_selector'])
                            await audio_locator.highlight()
                            async with page.expect_response(lambda response: 'mp3' in response.url, timeout=1500) as response_info:
                                await audio_locator.click(timeout=1500)
                            user_dict['audio_url'] = (await response_info.value).url
                        except Exception as e:
                            # 捕获异常截图
                            # await page.screenshot(path=screenshot_dir / f'{i}_audio.png')
                            raise Exception(f"解析音频错误 {e}") from e

                    # ---------------------------------- 解析url跳转---------------------------------- #
                    case 'homepage':
                        try:
                            await element.highlight()
                            await element.click(click_count=1)
                            await page.wait_for_url(url='**/detail/**', wait_until='domcontentloaded', timeout=1000)
                            user_dict['homepage'] = page.url
                            await page.go_back()  # 回到原始页面
                        except Exception as e:
                            # 捕获异常截图
                            # await page.screenshot(path=screenshot_dir / f'{i}_url.png')
                            raise Exception(f"解析url跳转错误 {e}") from e
                    case _:
                        raise ValueError(f'Invalid crawl_info: {crawl_info}')

            except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
                logging.getLogger('get_user_urls').error(f"[{locator_dict['company']} {e}")
                continue

            finally:
                # 任何失败都添加
                user_dict_list.append(user_dict)

        return user_dict_list

    async def get_clerk_info(self, request, page: Page, debug_batch: int = 1000) -> {}:
        """
        获取用户信息
        :param debug_batch: 用于小批量调试
        :param request:
        :param page:
        :return: 返回用户信息字典
        """

        # 定位器字典
        locator_dict = request.meta['locator_dict']

        # 改变class
        # change_body_selector = locator_dict.get('change_body_selector', None)
        # if change_body_selector:
        #     await page.evaluate("""O=>{document.querySelector(O).className ="";} """, locator_dict.get('change_body_selector', None))

        # 删除元素
        await self.remove_node_by_selector(page, locator_dict['remove_dialog_selector'])

        # 滚动页面
        await self.scroll_page(page.locator(locator_dict['user_card_selector']), page.locator(locator_dict['page_finished_selector']))

        # 删除元素
        await self.remove_node_by_selector(page, locator_dict['remove_dialog_selector'])

        # 常规爬虫
        basic_dict_list = await self.parse_clerk_basic(request, page)

        # 截断
        basic_dict_list = basic_dict_list[:min(debug_batch, len(basic_dict_list))]
        # logging.getLogger('常规爬虫').info(basic_dict_list)

        # 基本数据
        res = {'res': basic_dict_list}

        # 按需解析数据 rank
        if len(request.meta['crawl_info']) > 1:
            extra_dict_list = await self.parse_clerk_audio_homepage(request, page, request.meta['crawl_info'][1], debug_batch)
            assert len(extra_dict_list) == len(basic_dict_list)  # 保证数量一致
            res.update({'res': [{**d1, **d2} for d1, d2 in zip(extra_dict_list, basic_dict_list)]})

        return res

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
            try:
                res = await self.get_clerk_info(request, page)
            except Exception as e:
                logging.getLogger('detail').error(f"获取用户信息错误 {e}")
                raise e
            finally:
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
        raise exception

    def spider_opened(self, spider):
        spider.logger.info(f"{spider.name} Spider opened Use {__class__.__name__}")
