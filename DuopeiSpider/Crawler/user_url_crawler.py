"""
根据点击后的url跳转，获取用户url列表
"""

import pandas as pd
from tqdm import tqdm
import os
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from DuopeiSpider.Crawler.user_panel_crawler import Scraper
from DuopeiSpider.Utils.js_tools.js_script import *
from DuopeiSpider.Utils import setting as cf


class StaticScraper(Scraper):
    def __init__(self, time_out, headless=True):
        super().__init__(headless=headless, time_out=time_out)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def run(self, url):
        save_path = f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/user_url.csv"
        # if os.path.exists(save_path):
        #     return

        page = await self.browser.new_page()
        page.set_default_timeout(self.TIME_OUT * 1000)  # 默认超时

        # 导航到需要爬取的网站
        await page.goto(url)

        # 点击提示框
        await self.click_banner(page, url)

        # 2.滚动页面
        await self.scroll_page(page, url, page.locator(WEBSITE_DICT[url]['page_finished_selector']))

        # 定位到具有跳转链接的元素
        elements_locator = page.locator(WEBSITE_DICT[url]['user_card_selector'])

        # 获取元素的数量
        elements_count = await elements_locator.count()
        url_list = []
        for i in tqdm(range(elements_count)):
            url_dict = {}
            # 获取单个元素
            element = elements_locator.nth(i)

            while 1:
                try:
                    # 将元素滚动到视野中
                    await element.scroll_into_view_if_needed()

                    # 模拟点击元素
                    await self.remove_dialog(page, url)  # 移除通知框
                    await element.click()
                    await page.wait_for_load_state('networkidle')  # 等待点击事件

                    # 获取并打印新页面的URL
                    if 'detail' in page.url:
                        url_dict['User_url'] = page.url
                        url_dict['Source'] = url
                        url_dict['Rank'] = i
                        url_list.append(url_dict)
                        # 回到原始页面
                        await page.go_back()
                        break
                except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
                    await page.screenshot(path=f'{ROOT_PATH}/DataSets/screenshots/e_{i}.png')
                    continue

        await page.close()
        pd.DataFrame(url_list).to_csv(save_path, index=False)
