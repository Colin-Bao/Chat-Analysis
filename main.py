import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
import asyncio
from DuopeiSpider.Crawler.dynamic_crawler import Scraper
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT
from DuopeiSpider.Utils import setting as cf
import argparse
import time
import psutil


def parse_args():
    parser = argparse.ArgumentParser(description='Your web scraper.')
    # parser.add_argument('--websites', nargs='*', default=config.,
    #                     help='The list of websites to scrape.')
    parser.add_argument('--dsdir', default=cf.DS_PATH, help='数据存储根路径')
    parser.add_argument('--webcore', default=cf.WEB_CORE, help='浏览器内核')
    parser.add_argument('--timeout', default=cf.TIME_OUT, help='超时时间')
    parser.add_argument('--cpu_core', default=cf.CPU_CORE, help='使用CPU数量')
    return parser.parse_args()


async def main():
    # 程序运行参数
    args = parse_args()

    # 限制 CPU 核心数量
    if sys.platform.startswith('darwin'):
        pass
    else:
        p = psutil.Process()
        p.cpu_affinity(list(range(cf.CPU_CORE)))

    # 异步运行
    async with Scraper(browser_type=args.webcore, time_out=args.timeout) as scraper:
        while True:
            try:
                await scraper.log(f'\n\n---------------------------【开始爬取】{args.dsdir}---------------------------\n',
                                  {'class_name': 'main', 'url_name': 'all'})
                tasks = [scraper.run(website) for website, _ in WEBSITE_DICT.items()]
                await asyncio.gather(*tasks)
            except Exception as e:
                await scraper.log(f'Error occurred: {e}', {'class_name': 'main', 'url_name': 'all'}, 'error')
            time.sleep(cf.CRAWL_INTERVAL)
            # break


if __name__ == "__main__":
    asyncio.run(main())
