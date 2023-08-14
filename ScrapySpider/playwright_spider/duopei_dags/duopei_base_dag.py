# [START import_module]

from airflow.decorators import dag, task


# [END import_module]


@task.external_python(python='/home/nizai9a/miniconda3/envs/PlaySpider/bin/python')
def crawl_duopei(url, crawl_info, db_mode):
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
    scrapy_root_path = Path("~/PycharmProjects/Chat-Analysis").expanduser()
    sys.path.extend([str(scrapy_root_path), str(scrapy_root_path / 'ScrapySpider')])
    os.chdir(str(scrapy_root_path / 'ScrapySpider'))  # 更改工作目录到Scrapy项目

    # Scrapy项目路径
    from ScrapySpider.playwright_spider.spiders.duopei_spider import DuopeiSpider

    # 用来存储异常的列表
    errors = []

    # noinspection PyUnusedLocal
    def handle_spider_error(failure, response, spider):
        # 保存异常到列表
        errors.append(failure.value)

    # 新建一个爬虫项目
    process = CrawlerProcess(get_project_settings())
    crawler = process.create_crawler(DuopeiSpider)

    # 连接到 spider_error 信号以捕获异常
    dispatcher.connect(handle_spider_error, signal=signals.spider_error)

    process.crawl(crawler, start_url=url, crawl_info=crawl_info, db_mode=db_mode)
    process.start()

    # 在爬虫运行完成后检查是否有错误，并引发异常（如果有）
    if errors:
        print(f'----------------------{url}引发异常---------------------- \n')
        raise errors[0]


def get_company_list() -> list[(), ()]:
    from airflow.providers.mysql.hooks.mysql import MySqlHook  # noqa
    # 创建数据库会话
    conn = MySqlHook(mysql_conn_id='mysql_duopei').get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT company, website FROM duopei.company;")

    # 执行查询并获取结果列表
    start_urls = cursor.fetchall()

    # 关闭游标
    cursor.close()
    conn.close()
    return start_urls
