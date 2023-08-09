import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_info_crawler import UserInfoScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT
from DuopeiSpider.Utils.csv_to_df import run as run_csv_to_df
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


async def main():
    while True:
        try:
            # 2.异步运行获取用户信息
            async with UserInfoScraper(True) as scraper:
                tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
                await asyncio.gather(*tasks)

            # 3.转换为df
            run_csv_to_df()
        except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
            print(e)
            continue


if __name__ == "__main__":
    asyncio.run(main())
