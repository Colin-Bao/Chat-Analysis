from DuopeiSpider.data_handler import DataHandler
from DuopeiSpider.logger import Logger
from DuopeiSpider.setting import *
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
        self.browser = None
        self.playwright = None

        # 数据处理
        self.data_handler = data_handler

        # 日志处理
        self.logger = Logger(f"{DS_PATH}/logs")
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
        :param url:
        :param page:
        :param parse_time:
        :return:
        """

        # 定义一些解析函数，每个函数处理一种URL模式
        async def parse_url_pattern_1(gift_str: str) -> tuple:
            # 处理方式1 糖恋
            name, rest = gift_str.split('被打赏了', 1)
            # 分别考虑2种模式
            if '礼物' in rest:
                gift, amount = re.search(r'\[ (.*) \] x (\d+)', rest).groups()
            else:
                gift = '颗'
                amount = rest.replace('糖果', '').strip()
            # 添加到列表
            return name.strip(), gift.strip(), float(amount)

        async def parse_url_pattern_2(gift_str: str) -> tuple:
            # 处理方式2 天空猫
            name = gift_str.split('】')[0].replace('【', '')
            amount = gift_str.split('打赏')[1].replace('元', '').strip()
            gift = '元'
            return name.strip(), gift.strip(), float(amount)

        async def parse_url_pattern_3(gift_str: str) -> tuple:
            # 处理方式3 橘色灯罩
            name, rest = gift_str.split('打赏给')[1].split('】', 1)
            name = name.replace('【', '')
            # 分别考虑2种模式
            if '礼物' in rest:
                gift = re.search(r'\[ (.*?) \]', rest).group(1)
                amount = 1.0
            else:
                gift = '颗'
                amount = re.findall(r'\d+\.?\d*', rest)[0]
            return name.strip(), gift.strip(), float(amount)

        async def parse_url_pattern_4(gift_str: str) -> tuple:
            # 处理方式4 清欢
            name, rest = gift_str.split('收到了客人打赏', 1)
            name = re.search(r'【(.*?)】', name).group(1)
            amount = rest.replace('花瓣', '').strip()
            gift = '花瓣'
            return name.strip(), gift.strip(), float(amount)

        # 创建一个字典映射从URL模式到相应的解析函数
        url_to_parser = {
                'http://tj5uhmrpeq.duopei-m.featnet.com': parse_url_pattern_1,
                'http://oxxs5iqzqz.duopei-m.manongnet.cn': parse_url_pattern_2,
                'http://8mukjha763.duopei-m.99c99c.com': parse_url_pattern_3,
                'http://fhpkn3rf85.duopei-m.manongnet.cn': parse_url_pattern_4,
        }

        # 发送JS
        async def parse_byjs() -> list[str]:
            """
            解析JS
            :return:一个包含所有选定元素文本内容的字符串列表
            """
            # 提取元素
            item_classname = '.swiper-slide:not(.swiper-slide-duplicate)'
            data_list = await page.evaluate(f'Array.from(document.querySelectorAll("{item_classname}")).map(e => e.textContent.trim())')
            return data_list

        async def trans_data(data: list[str]) -> pd.DataFrame:
            """
            解析礼物信息的字符串列表，并转为DataFrame
            :return:
            """

            # 根据URL选择相应的解析函数
            extracted_data = [await url_to_parser.get(url)(item) for item in data]

            # 转换
            df = pd.DataFrame(extracted_data, columns=['Name', 'Content', 'Num'])
            df['Date'] = parse_time
            df = df.astype(dtype={'Name': 'str', 'Content': 'str', 'Num': 'float'})

            # 返回
            await self.log('礼物数据解析成功', {'func_name': 'parse_gift', 'url_name': url})
            return df.reset_index(drop=True)  # 重置索引，add中为0则为新

        # 提取、转换礼物数据
        df_gift = await trans_data(await parse_byjs())
        return df_gift

    async def parse_clerk(self, page: Page, parse_time, url) -> pd.DataFrame:
        """
        店员信息解析
        :return:
        """

        async def parse_byjs() -> pd.DataFrame:
            """
            JS版解析
            """

            def get_selector() -> dict:
                """
                待获取字段的ClassName传递给JS
                :return:
                """
                # 店员信息属性列表
                item_dict = {'Name': '.name, .text-ellipsis',
                             'Age': '.sex-age',
                             }
                # 修改选择器
                match url:
                    case 'http://tj5uhmrpeq.duopei-m.featnet.com':  # 糖恋
                        item_dict.update({'Sex': '.sex-age',
                                          'Online': '.StatusEnum',
                                          'Grade': '.minPrice',
                                          'Service': '.status.text-ellipsis'})

                    case 'http://oxxs5iqzqz.duopei-m.manongnet.cn':  # 天空猫
                        item_dict.update({'Sex': '.sex-age',
                                          'Online': '.status.text-ellipsis',
                                          'GradeImg': '.grade img',
                                          'Service': '.status.text-ellipsis'})

                    case 'http://8mukjha763.duopei-m.99c99c.com':  # 橘色
                        item_dict.update({'SexImg': '.sex-age img',
                                          'Online': '.switch-name',
                                          'GradeImg': '.clerk-item__body img',
                                          'Service': '.switch-name'})

                    case 'http://fhpkn3rf85.duopei-m.manongnet.cn':  # 清欢
                        item_dict.update({'Name': '.name',
                                          'Online': '.status.text-ellipsis',
                                          'GradeImg': '.grade img',
                                          'Service': '.status.text-ellipsis'})
                    case _:
                        raise ValueError('No Support Url')
                return item_dict

            async def send_js() -> [{'': str}, ...]:
                """
                 # 执行一次浏览器交互，获取所有数据
                :return:
                """
                evaluate_js = '''(itemDict) => {
                        const elements = document.querySelectorAll('.van-cell__value, .van-cell__value--alone');
                        const data = [];
                        for (const element of elements) {
                            const row = {};
                            for (const [attr, classname] of Object.entries(itemDict)) {
                                const subElement = element.querySelector(classname);
                                if (subElement) {
                                    let textContent;
                                    if (attr === 'Sex') {
                                        textContent = subElement.getAttribute("style").trim();
                                    } 
                                    else if (attr === 'GradeImg') {
                                        textContent = subElement.getAttribute("src").trim();
                                    }
                                    else if (attr === 'SexImg') {
                                        textContent = subElement.getAttribute("src").trim();
                                    }
                                    else {
                                        textContent = subElement.textContent.trim();
                                    }
                                    row[attr] = textContent;
                                }
                            }
                            if (Object.keys(row).length === Object.keys(itemDict).length) {
                                data.push(row);
                            }
                        }
                        return data;
                    }
                '''
                data = await page.evaluate(evaluate_js, get_selector())
                return data

            # 将数据转换为 DataFrame
            df = pd.DataFrame(await send_js())

            # 返回供外部存储
            return df

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
        # df_user = await parse_byjs()
        df_user = await df_trans(await parse_byjs())
        await self.log(f'用户数据解析成功\n{df_user.columns.tolist()}', {'func_name': 'parse_clerk', 'url_name': url})
        return df_user

    async def run(self, url):
        """
        browser.new_context() 和 context.new_page(),
        在每次循环中创建新的上下文和页面可以有助于隔离每次迭代的状态，避免不同迭代之间的潜在冲突。
        """
        # 绑定日志类
        site_name = f"{url.replace('http://', '').split('.')[0]}"

        # 打开上下文
        async with await self.browser.new_context() as context:
            # 0.使用context创建页面
            page = await context.new_page()
            page.set_default_timeout(self.TIME_OUT * 1000)  # 默认超时

            # 1.访问页面
            await page.goto(url)

            # 2.滚动页面
            scroll_st = time.time()
            await self.log('页面开始滚动', {'func_name': 'run', 'url_name': url})
            while not await page.locator('.van-list__finished-text').count():
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                if time.time() - scroll_st > float(self.TIME_OUT):
                    raise PlaywrightTimeoutError(f'滚动超时：{self.TIME_OUT}')  # 10秒
            scroll_et = datetime.datetime.now()
            await self.log('页面滚动完毕', {'func_name': 'run', 'url_name': url})
            # 3.解析页面
            # -----------------绑定处理类 -----------------#
            self.data_handler = DataHandler(f'{DS_PATH}/{site_name}', (self.info_logger, self.warn_logger, self.error_logger), url)

            # -----------------对比礼物信息变更 -----------------#
            df_gift = await self.parse_gift(page, scroll_et, url)
            await self.data_handler.update_info_change(df_gift, 'gift', 'add')

            # -----------------对比用户信息变更 -----------------#
            df_user = await self.parse_clerk(page, scroll_et, url)
            await self.data_handler.save_append(df_user, self.data_handler.user_daily_dir + '/' + str(scroll_et.date()))  # 面板数据
            await self.data_handler.update_info_change(df_user, 'user', 'add')
            await self.data_handler.update_info_change(df_user, 'user', 'remove')
