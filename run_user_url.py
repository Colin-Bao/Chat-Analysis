import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.user_url_crawler import StaticScraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT


async def main():
    # 我需要使用playwright的异步方法爬取一个网站，该网站下面有一个用户列表。每个用户列表又对应一个链接，我需要对每个用户依次在新的链接上进行第二级的爬取，我需要保存每个用户的头像，音频、地区、年龄等属性，既包含了结构化的数据又有非结构化的数据。帮我设计合适的程序结构，以及合适的文件储存架构。
    # 限制 CPU 核心数量
    # if sys.platform.startswith('darwin'):
    #     pass
    # else:
    #     p = psutil.Process()
    #     p.cpu_affinity(list(range(4, 8)))

    # 异步运行
    async with StaticScraper(30, True) as scraper:
        tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
