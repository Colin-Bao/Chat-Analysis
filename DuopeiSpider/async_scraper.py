import playwright.async_api

from DuopeiSpider.data_handler import DataHandler
from DuopeiSpider.logger import Logger
from DuopeiSpider import setting as cf
from DuopeiSpider.js_script import website_dict, extract_user_info_js

import re
import asyncio
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import pandas as pd
import time
import datetime
import sys


class Scraper:
    """
    数据爬取类
    """

    def __init__(self, browser_type, data_handler: DataHandler = None, time_out: int = 20, ):
        self.browser_type = browser_type
        self.browser: playwright.async_api.Browser = None
        self.playwright = None

        # 数据处理
        self.data_handler = data_handler

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
            case "webkit": self.browser = await self.playwright.webkit.launch(headless=True)
            case "firefox": self.browser = await self.playwright.firefox.launch()
            case "chromium": self.browser = await self.playwright.chromium.launch()
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

    async def parse_gift(self, page: Page, parse_time, url) -> pd.DataFrame:
        """
        礼物打赏解析
        :return:
        """

        # 发送JS
        item_classname = website_dict[url]['gift_info_selector']
        data_list = await page.evaluate(
            f'Array.from(document.querySelectorAll("{item_classname}")).map(e => e.textContent.trim())')  # 一个包含所有选定元素文本内容的字符串列表

        # 根据URL选择相应的解析函数
        extracted_data = [await website_dict[url]['url_to_parser'](item) for item in data_list]
        df_gift = pd.DataFrame(extracted_data, columns=['Name', 'Content', 'Num'])
        df_gift['Date'] = parse_time
        df_gift = df_gift.astype(dtype={'Name': 'str', 'Content': 'str', 'Num': 'float'})

        # 返回
        await self.log('礼物数据解析成功', {'func_name': 'parse_gift', 'url_name': url})
        return df_gift.reset_index(drop=True)  # 重置索引，add中为0则为新

    async def parse_clerk(self, page: Page, parse_time, url) -> pd.DataFrame:
        """
        店员信息解析
        :return:
        """

        async def df_trans(df) -> pd.DataFrame:
            """
            处理Dataframe
            :return:
            """
            # type_config = {'Rank': 'uint16', 'Name': 'category', 'Sex': 'bool', 'Age': 'uint8',
            #                'Online': 'bool', 'Grade': 'uint8', 'Text': 'bool',
            #                'Call': 'bool', 'Video': 'bool', 'Game': 'bool'}

            # df['Grade'] = pd.to_numeric(df['Grade'].str[:2], errors='coerce')
            # df['Text'] = df['Service'].str.contains('文语', case=False)
            # df['Call'] = df['Service'].str.contains('连麦', case=False)
            # df['Video'] = df['Service'].str.contains('视频', case=False)
            # df['Game'] = df['Service'].str.contains('游戏', case=False)
            # df['Sex'] = df['Sex'].apply(lambda x: True if x == '255' else False)
            # df['Online'] = df['Online'].apply(lambda x: True if x == '在线' else False)

            # 返回供外部调用
            # df = df.drop(columns=['Service']).astype(type_config)
            # 全部处理成str
            df = df.astype('str')
            df['Date'] = parse_time
            df['Rank'] = range(len(df))
            return df

        # 提取、转换和保存用户面板数据
        df_user = await df_trans(pd.DataFrame(await page.evaluate(extract_user_info_js, website_dict[url]['user_info_selector'])))
        await self.log(f'用户数据解析成功\n{df_user.columns.tolist()}', {'func_name': 'parse_clerk', 'url_name': url})
        return df_user

    async def run(self, url):
        """
        browser.new_context() 和 context.new_page(),
        在每次循环中创建新的上下文和页面可以有助于隔离每次迭代的状态，避免不同迭代之间的潜在冲突。
        """

        # 打开上下文
        # self.browser.new_page()
        # async with await self.browser.new_context() as context:
        # 0.创建页面
        page = await self.browser.new_page()
        page.set_default_timeout(self.TIME_OUT * 1000)  # 默认超时

        # 1.访问页面
        await page.goto(url)

        # 2.滚动页面
        scroll_st = time.time()
        await self.log('页面开始滚动', {'func_name': 'run', 'url_name': url})
        while not await page.locator(website_dict[url]['page_finished_selector']).count():
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            if time.time() - scroll_st > float(self.TIME_OUT):
                raise PlaywrightTimeoutError(f'滚动超时：{self.TIME_OUT}')
        scroll_et = datetime.datetime.now()
        await self.log('页面滚动完毕', {'func_name': 'run', 'url_name': url})

        # 3.解析页面
        # -----------------绑定处理类 -----------------#
        self.data_handler = DataHandler(f"{cf.DS_PATH}/{website_dict[url]['name']}",
                                        (self.info_logger, self.warn_logger, self.error_logger), url)

        # -----------------对比礼物信息变更 -----------------#
        df_gift = await self.parse_gift(page, scroll_et, url)
        print(df_gift)
        # await self.data_handler.update_info_change(df_gift, 'gift', 'add')

        # -----------------对比用户信息变更 -----------------#
        # df_user = await self.parse_clerk(page, scroll_et, url)
        # await self.data_handler.save_append(df_user, self.data_handler.user_daily_dir + '/' + str(scroll_et.date()))  # 面板数据
        # await self.data_handler.update_info_change(df_user, 'user', 'add')
        # await self.data_handler.update_info_change(df_user, 'user', 'remove')
