import sys

sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis')
sys.path.append('/home/ubuntu/PycharmProjects/Chat-Analysis/DuopeiSpider')

import asyncio
from DuopeiSpider.async_scraper import Scraper
from DuopeiSpider.js_script import website_dict
from DuopeiSpider import setting as cf
import argparse
import time


def parse_args():
    parser = argparse.ArgumentParser(description='Your web scraper.')
    # parser.add_argument('--websites', nargs='*', default=config.,
    #                     help='The list of websites to scrape.')
    parser.add_argument('--dsdir', default=cf.DS_PATH, help='数据存储根路径')
    parser.add_argument('--webcore', default=cf.WEB_CORE, help='浏览器内核')
    parser.add_argument('--timeout', default=cf.TIME_OUT, help='超时时间')
    return parser.parse_args()


async def main():
    # nohup python '/home/ubuntu/PycharmProjects/Chat-Analysis/DuopeiSpider/main.py' > /home/ubuntu/DataSets/2023-Escort/logs/main_log.log &
    # nohup /home/ubuntu/miniconda3/envs/PlaySpider/bin/python '/home/ubuntu/PycharmProjects/Chat-Analysis/DuopeiSpider/main.py' > /dev/null 2>&1 &

    # 程序运行参数
    args = parse_args()

    # 协程
    async with Scraper(browser_type=args.webcore, time_out=args.timeout) as scraper:
        while True:
            try:
                await scraper.log(f'\n\n---------------------------【开始爬取】{args.dsdir}---------------------------\n',
                                  {'class_name': 'main', 'url_name': 'all'})
                tasks = [scraper.run(website) for website, _ in website_dict.items()]
                await asyncio.gather(*tasks)
            except Exception as e:
                await scraper.log(f'Error occurred: {e}', {'class_name': 'main', 'url_name': 'all'}, 'error')
            time.sleep(cf.CRAWL_INTERVAL)
            break


if __name__ == "__main__":
    asyncio.run(main())
