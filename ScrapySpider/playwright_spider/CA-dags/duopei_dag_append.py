from __future__ import annotations

# [START import_module]

import pendulum

from airflow.decorators import dag, task
from datetime import timedelta


# [END import_module]


# [START instantiate_dag]
@dag(
        schedule="0 */2 * * *",
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei", "spider"],
        max_active_tasks=20,  # 限制并发数
        max_active_runs=1,  # 限制同时运行的实例数量
        dagrun_timeout=timedelta(minutes=2),
)
def duopei_append():
    @task()
    def query_urls():
        import json
        file_path = '/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider/data/user_selector.json'
        with open(file_path, "r", encoding='utf-8') as file:
            json_data = file.read()
        start_urls = list(json.loads(json_data).keys())
        return start_urls

    @task.external_python(task_id="crawl_duopei", python='/home/nizai9a/miniconda3/envs/PlaySpider/bin/python')
    def crawl_duopei(url):
        """
        Example function that will be performed in a virtual environment.

        Importing at the module level ensures that it will not attempt to import the
        library before it is installed.
        """

        import sys
        import os
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        from scrapy.signalmanager import dispatcher
        from scrapy import signals

        # 添加Scrapy项目路径到系统路径
        sys.path.append(os.path.abspath('/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider/playwright_spider'))
        from spiders.duopei_spider import DuopeiSpider  # noqa
        os.chdir('/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider')  # 更改工作目录到Scrapy项目

        # 用来存储异常的列表
        errors = []

        def handle_spider_error(failure, response, spider):
            # 保存异常到列表
            errors.append(failure.value)

        # 新建一个爬虫项目
        process = CrawlerProcess(get_project_settings())
        crawler = process.create_crawler(DuopeiSpider)

        # 连接到 spider_error 信号以捕获异常
        dispatcher.connect(handle_spider_error, signal=signals.spider_error)

        process.crawl(crawler, start_url=url)
        process.start()

        # 在爬虫运行完成后检查是否有错误，并引发异常（如果有）
        if errors:
            print(' # 在爬虫运行完成后检查是否有错误，并引发异常（如果有）')
            raise errors[0]

    # callable_external_python('http://tj5uhmrpeq.duopei-m.featnet.com')
    # crawl_duopei(url='http://tj5uhmrpeq.duopei-m.featnet.com')
    crawl_duopei.expand(url=query_urls())


# [START dag_invocation]
duopei_append()
