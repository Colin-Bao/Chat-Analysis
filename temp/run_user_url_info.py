import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_url_crawler import StaticScraper
from DuopeiSpider.Crawler.user_info_crawler import UserInfoScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT
from DuopeiSpider.Utils.csv_to_df import run as run_csv_to_df


async def main():
    # 1.异步运行获取url列表
    # async with StaticScraper(30, True) as scraper:
    #     tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
    #     await asyncio.gather(*tasks)

    # 2.异步运行获取用户信息
    async with UserInfoScraper(True) as scraper:
        tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
        await asyncio.gather(*tasks)

    # 3.转换为df
    # run_csv_to_df()


if __name__ == "__main__":
    asyncio.run(main())
