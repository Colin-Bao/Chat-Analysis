
# [START import_module]

import pendulum
from airflow.decorators import dag, task
from datetime import timedelta

# [END import_module]


# [START instantiate_dag]
@dag(
        # schedule="*/2 * * * *",
        schedule=None,
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei", "spider"],
        # max_active_tasks=16,  # 限制并发数
        max_active_runs=1,  # 限制同时运行的实例数量
        dagrun_timeout=timedelta(minutes=2),
)
def duopei_append():

    @task.external_python(python='/home/nizai9a/miniconda3/envs/PlaySpider/bin/python')
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
        from pathlib import Path

        # 添加Scrapy项目路径到系统路径
        SCRAPY_ROOT_PATH = Path("~/PycharmProjects/Chat-Analysis").expanduser()
        sys.path.extend([str(SCRAPY_ROOT_PATH), str(SCRAPY_ROOT_PATH / 'ScrapySpider')])
        os.chdir(SCRAPY_ROOT_PATH)  # 更改工作目录到Scrapy项目

        # Scrapy项目路径
        from ScrapySpider.playwright_spider.spiders.duopei_spider import DuopeiSpider

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

    # 主流程
    def start_task():
        from airflow.providers.mysql.hooks.mysql import MySqlHook  # noqa
        # 创建数据库会话
        conn = MySqlHook(mysql_conn_id='mysql_duopei').get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT company, website FROM company;")

        # 执行查询并获取结果列表
        start_urls = cursor.fetchall()
        start_urls = (('http://exjomkwuav.duopei-m.manongnet.cn', '糖恋'),)

        # 动态创建task
        for website, company in start_urls:
            crawl_duopei.override(task_id='C_' + company)(website)

        # 关闭游标
        cursor.close()
        conn.close()

    start_task()
    # crawl_duopei(url='http://tj5uhmrpeq.duopei-m.featnet.com')
    # crawl_duopei.expand(url=query_urls())


# [START dag_invocation]
duopei_append()
