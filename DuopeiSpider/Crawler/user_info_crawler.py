"""
我需要使用playwright的异步方法爬取一个网站，该网站下面有一个用户列表。每个用户列表又对应一个链接，我需要对每个用户依次在新的链接上进行第二级的爬取，
我需要保存每个用户的头像，音频、地区、年龄等属性，既包含了结构化的数据又有非结构化的数据。帮我设计合适的程序结构，以及合适的文件储存架构。
"""
import datetime

import pandas as pd
from tqdm import tqdm
import os
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from DuopeiSpider.Crawler.user_panel_crawler import Scraper
from DuopeiSpider.Utils.js_tools.js_script import *
from DuopeiSpider.Utils import setting as cf


class UserInfoScraper(Scraper):
    def __init__(self, headless):
        super().__init__(headless=headless)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

    # noinspection PyMethodMayBeStatic
    async def create_save_directories(self, name):
        img_dir = f"{cf.DS_PATH}/{name}/user_info/imgs"
        audio_dir = f"{cf.DS_PATH}/{name}/user_info/audios"
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

    # noinspection PyMethodMayBeStatic
    async def get_user_url(self, url) -> list[str, ...] | None:
        # 读取用户URL列表
        user_url_path = f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/user_url.csv"
        if os.path.exists(user_url_path):
            user_urls = pd.read_csv(user_url_path)['User_url'].tolist()
        else: return None
        return user_urls

    async def run(self, url):
        # 创建目录
        await self.create_save_directories(WEBSITE_DICT[url]['name'])

        # 读取用户URL列表
        user_urls = await self.get_user_url(url)
        page = await self.browser.new_page()

        # 开始爬取
        user_info_list: [{}] = []
        for user_url in tqdm(user_urls):
            # 导航到需要爬取的网站
            await page.goto(user_url)
            await page.wait_for_load_state('networkidle')

            # 定义存储信息的字典
            user_info_dict = {}

            # 解析音频
            await page.locator(WEBSITE_DICT[url]['dialog_button_selector']).click()
            async with page.expect_response(lambda response: 'mp3' in response.url) as response_info:
                await page.locator(WEBSITE_DICT[url]['clerk_audio_selector']).click()
            user_info_dict['audio_url'] = (await response_info.value).url

            # 解析个人资料
            user_info: list = await page.locator(WEBSITE_DICT[url]['clerk_info_selector']).all_inner_texts()

            # 解析礼物墙
            user_gift_wall: [str, ...] = await page.locator('div.row-item').all_inner_texts()

            # 生成信息字典
            for k, v in enumerate(user_info[0].split('\n')):
                user_info_dict[f'info_{k}'] = v
            for k, v in enumerate(user_gift_wall):
                user_info_dict[f'gift_{k}'] = v

            # 额外元数据
            user_info_dict['user_url'] = user_url
            user_info_dict['user_source'] = url
            user_info_dict['source_name'] = WEBSITE_DICT[url]['name']
            user_info_dict['update_time'] = datetime.datetime.now()
            user_info_dict['img_dir'] = f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/imgs/"
            user_info_dict['audio_dir'] = f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/audios/"

            # 增加到列表
            user_info_list.append(user_info_dict)

        await page.close()
        pd.DataFrame(user_info_list).to_csv(f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/user_card.csv", escapechar='\\',
                                            index=True)
