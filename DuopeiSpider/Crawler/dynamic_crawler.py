import playwright.async_api
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from DuopeiSpider.Utils.js_tools.js_script import *
from DuopeiSpider.Utils.data_handler import DataHandler
from DuopeiSpider.Utils.logger import Logger
from DuopeiSpider.Utils import setting as cf

import pandas as pd
import time
import datetime


class Scraper:
    """
    数据爬取类
    """

    def __init__(self, browser_type: str = 'chromium', data_handler: DataHandler = None, time_out: int = 20, headless: bool = True):
        self.browser_type = browser_type
        self.browser: playwright.async_api.Browser = None
        self.playwright = None
        self.headless = headless

        # 数据处理
        self.data_handler = data_handler
        # self.json

        # 日志处理
        self.logger = Logger(f"{cf.DS_PATH}/logs")
        self.info_logger = self.logger.get_logger('info')
        self.warn_logger = self.logger.get_logger('warn')
        self.error_logger = self.logger.get_logger('error')

        # 参数
        self.TIME_OUT = time_out

    async def __aenter__(self):
        self.playwright = await async_playwright().__aenter__()
        match self.browser_type:
            case "webkit": self.browser = await self.playwright.webkit.launch(headless=self.headless)
            case "firefox": self.browser = await self.playwright.firefox.launch()
            case "chromium": self.browser = await self.playwright.chromium.launch(headless=self.headless)
            case _: raise ValueError("Invalid browser type. Choose from 'webkit', 'firefox', or 'chromium'.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()  # 关闭浏览器
        if self.playwright:
            await self.playwright.stop()  # 退出该类

    async def log(self, message: str, extra_dict: dict, level='info'):
        """
        日志记录
        :param extra_dict: 网站
        :param message:信息
        :param level:日志级别
        """
        extra = {'class_name': self.__class__.__name__, 'func_name': '', 'url_name': ''}
        extra.update(extra_dict)
        (getattr(self, f'{level}_logger').log(
                msg=message,
                level={'info': 20, 'warn': 30, 'error': 40}.get(level, 20),
                extra=extra
        ))

    async def click_banner(self, page: Page, url):
        banner_selector = WEBSITE_DICT[url].get('banner_selector', None)
        if banner_selector:
            await page.locator(banner_selector).click()
        await self.log('点击公告栏完成', {'func_name': 'click_banner', 'url_name': url})

    async def scroll_page(self, page: Page, url, locator_item: Locator):
        scroll_st = time.time()
        await self.log('页面开始滚动', {'func_name': 'scroll_page', 'url_name': url})
        while True:
            await page.locator(WEBSITE_DICT[url]['user_card_selector']).last.scroll_into_view_if_needed()
            if time.time() - scroll_st > float(self.TIME_OUT):
                raise PlaywrightTimeoutError(f'滚动超时：{self.TIME_OUT}')
            if await locator_item.count():
                break
        await self.log('页面滚动完毕', {'func_name': 'scroll_page', 'url_name': url})

    async def block_img(self, page: Page, url):
        await page.route('**/*', lambda route: route.abort() if route.request.resource_type == 'image' else route.continue_())
        await self.log('已关闭图像', {'func_name': 'block_img', 'url_name': url})

    async def parse_gift(self, page: Page, parse_time, url) -> pd.DataFrame:
        """
        礼物打赏解析
        :return:
        """

        # 发送JS
        item_classname = WEBSITE_DICT[url]['gift_info_selector']
        data_list = await page.evaluate(
                f'Array.from(document.querySelectorAll("{item_classname}")).map(e => e.textContent.trim())')  # 一个包含所有选定元素文本内容的字符串列表

        # 根据URL选择相应的解析函数
        # extracted_data =
        # extracted_data = [await WEBSITE_DICT[url]['url_to_parser'](item) for item in data_list]
        df_gift = pd.DataFrame([await (globals().get(WEBSITE_DICT[url]['url_to_parser']))(item) for item in data_list],
                               columns=['Name', 'Content', 'Num'])
        df_gift['Date'] = parse_time
        df_gift['Source'] = url
        df_gift = df_gift.astype(dtype={'Name': 'str', 'Content': 'str', 'Num': 'float', 'Source': 'str'})

        # 返回
        await self.log('礼物数据解析成功', {'func_name': 'parse_gift', 'url_name': url})
        return df_gift.reset_index(drop=True)  # 重置索引，add中为0则为新

    async def parse_clerk(self, page: Page, parse_time, url) -> pd.DataFrame:
        """
        店员信息解析
        :return:
        """

        async def func_version() -> [{}, ...]:
            # 从DOM中解析元素
            attribute_methods = {'Sex': 'style', 'GradeImg': 'src', 'SexImg': 'src'}
            user_list = []
            for element_user_card in await page.locator(WEBSITE_DICT[url]['user_card_selector']).all():
                # 在元素中定位子元素
                user_card_dict = {}
                for attr, selector in list(WEBSITE_DICT[url]['user_info_selector'].items()):
                    sub_element = element_user_card.locator(selector)

                    # 无数据跳出
                    if not await sub_element.count(): break

                    # 解析元素
                    if attr in attribute_methods: text_content = await sub_element.get_attribute(attribute_methods[attr])
                    else: text_content = (await sub_element.text_content()).strip()

                    # 增加属性
                    user_card_dict[attr] = text_content

                # 添加子元素
                if len(user_card_dict.keys()) == len(WEBSITE_DICT[url]['user_info_selector']): user_list.append(user_card_dict)
            return user_list

        # 增加和转换其他列
        df_user = pd.DataFrame(await page.evaluate(JS_USER_INFO, WEBSITE_DICT[url]['user_info_selector']))
        assert len(df_user.columns) == len(WEBSITE_DICT[url]['user_info_selector'])
        df_user['Age'] = df_user['Age'].replace('', 0)
        df_user['Date'] = parse_time
        df_user['Rank'] = range(len(df_user))
        df_user['Source'] = url

        # 类型转换
        await self.log('用户数据解析成功', {'func_name': 'parse_clerk', 'url_name': url})
        return df_user.astype(dtype=WEBSITE_DICT[url]['user_info_type'])

    async def run(self, url):
        """
        browser.new_context() 和 context.new_page(),
        在每次循环中创建新的上下文和页面可以有助于隔离每次迭代的状态，避免不同迭代之间的潜在冲突。
        # async with await self.browser.new_context() as context:
        """

        # 0.创建页面
        page = await self.browser.new_page()
        page.set_default_timeout(self.TIME_OUT * 1000)  # 默认超时
        await self.block_img(page, url)

        try:
            # 1.访问页面
            await page.goto(url)

            # 2.滚动页面
            await self.scroll_page(page, url, page.locator(WEBSITE_DICT[url]['page_finished_selector']))
            scroll_et = datetime.datetime.now()

            # 3.解析页面
            # -----------------绑定处理类 -----------------#
            self.data_handler = DataHandler(f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}",
                                            (self.info_logger, self.warn_logger, self.error_logger), url)

            # -----------------对比礼物信息变更 -----------------#
            df_gift = await self.parse_gift(page, scroll_et, url)
            await self.data_handler.update_info_change(df_gift, 'gift', 'add')

            # -----------------对比用户信息变更 -----------------#
            df_user = await self.parse_clerk(page, scroll_et, url)
            await self.data_handler.save_append(df_user, self.data_handler.user_daily_dir + '/' + str(scroll_et.date()))  # 面板数据
            await self.data_handler.update_info_change(df_user, 'user', 'add')
            await self.data_handler.update_info_change(df_user, 'user', 'remove')

        except PlaywrightTimeoutError as e:
            await self.log(f'Error occurred: {e}', {'class_name': 'run', 'url_name': url}, 'error')
        except PlaywrightError as e:
            await self.log(f'Error occurred: {e}', {'class_name': 'run', 'url_name': url}, 'error')
        except Exception as e:
            await self.log(f'Error occurred: {e}', {'class_name': 'run', 'url_name': url}, 'error')

        finally:
            # 4.关闭页面
            await page.close()
