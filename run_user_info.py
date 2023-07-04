import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_info_crawler import UserInfoScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT


# if WEBSITE_DICT[website]['name'] == '糖恋树洞'

async def main():
    # 异步运行
    async with UserInfoScraper(True) as scraper:
        tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
