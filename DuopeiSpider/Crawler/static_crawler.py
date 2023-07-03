import asyncio
import time

from DuopeiSpider.Crawler.dynamic_crawler import Scraper
from DuopeiSpider.Utils.js_tools.js_script import *


class StaticScraper(Scraper):
    def __init__(self, headless):
        super().__init__(headless=headless)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def run(self, url):
        page = await self.browser.new_page()
        page.set_default_timeout(600 * 1000)  # 默认超时
        await self.block_img(page, url)

        # 导航到需要爬取的网站
        await page.goto(url)

        # 点击提示框
        banner_selector = WEBSITE_DICT[url].get('banner_selector', None)
        if banner_selector:
            await page.locator(banner_selector).click()

        # 2.滚动页面
        await self.scroll_page(page, url, page.locator(WEBSITE_DICT[url]['page_finished_selector']))

        # 定位到具有跳转链接的元素
        elements_locator = page.locator(WEBSITE_DICT[url]['user_card_selector'])

        # 获取元素的数量
        elements_count = await elements_locator.count()

        for i in range(elements_count):
            # 获取单个元素
            element = elements_locator.nth(i)
            await self.scroll_page(page, url, element)

            # 将元素滚动到视野中
            await element.scroll_into_view_if_needed()

            # 模拟点击元素
            await element.click()
            await page.wait_for_load_state('networkidle')

            # 获取并打印新页面的URL
            print(i, elements_count, page.url)

            # 回到原始页面
            await page.goto(url)

        await page.close()


async def main():
    async with StaticScraper(False) as scraper:
        await scraper.run('http://8mukjha763.duopei-m.99c99c.com')


if __name__ == '__main__':
    asyncio.run(main())
