import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_url_crawler import StaticScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT


async def main():
    # 异步运行
    async with StaticScraper(30, True) as scraper:
        tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items() if WEBSITE_DICT[website]['USE']]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
