import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_info_crawler import UserInfoScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT


# if WEBSITE_DICT[website]['name'] == '糖恋树洞'

async def main():
    async with UserInfoScraper(True) as scraper:
        semaphore = asyncio.Semaphore(1)
        print(end='')
        tasks = [asyncio.create_task(scraper.run_remote(semaphore, website)) for website in WEBSITE_DICT]
        await asyncio.gather(*tasks)
    #
    # async with UserInfoScraper(True) as scraper:
    #     _ = [await scraper.run_remote(website) for website, _ in WEBSITE_DICT.items()]


if __name__ == "__main__":
    while True:
        asyncio.run(main())
