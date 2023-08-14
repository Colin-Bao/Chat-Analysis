# [START import_module]
import sys
from pathlib import Path
import pendulum
from airflow.decorators import dag, task
from datetime import timedelta

# 自定义包
scrapy_root_path = Path("~/PycharmProjects/Chat-Analysis").expanduser()
sys.path.extend([str(scrapy_root_path), str(scrapy_root_path / 'ScrapySpider')])
from ScrapySpider.playwright_spider.duopei_dags.duopei_base_dag import crawl_duopei, get_company_list  # noqa


# [END import_module]


# [START instantiate_dag]
@dag(
        dag_id='duopei_update',
        description='更新模式，主表',
        schedule="*/35 * * * *",
        # schedule=None,
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["多陪", "更新"],
        max_active_runs=1,  # 限制同时运行的实例数量
        max_active_tasks=10,  # 限制并发数
        dagrun_timeout=timedelta(minutes=35),
        default_args={
                "owner": "colin",
        }
)
def duopei_dag():
    # 主流程
    def start_task():
        # 动态创建task
        start_urls = get_company_list()
        # start_urls = (('糖恋', 'http://exjomkwuav.duopei-m.manongnet.cn',),)
        for company, website in start_urls:
            t1 = crawl_duopei.override(task_id='A_' + company)(website, ['basic', 'audio'], 'update')
            t2 = crawl_duopei.override(task_id='H_' + company)(t1, ['basic', 'homepage'], 'update')

    start_task()


# [START dag_invocation]
duopei_dag()
