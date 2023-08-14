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
        dag_id='duopei_append',
        description='追加模式，面板数据',
        schedule="*/5 * * * *",
        # schedule=None,
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["多陪", "追加"],
        # max_active_tasks=2,
        max_active_runs=1,  # 限制同时运行的实例数量
        dagrun_timeout=timedelta(minutes=3),
        default_args={
                "owner": "colin",
        }
)
def duopei_dag():
    # 主流程
    def start_task():
        # 动态创建task
        # start_urls = (('http://exjomkwuav.duopei-m.manongnet.cn', '糖恋'),)
        for company, website in get_company_list():
            crawl_duopei.override(task_id='B_' + company)(website, ['basic'], 'append')

    start_task()


# [START dag_invocation]
duopei_dag()
