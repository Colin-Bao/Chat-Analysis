from __future__ import annotations

# [START import_module]

import pendulum

from airflow.decorators import dag, task


# [END import_module]


# [START instantiate_dag]
@dag(
        schedule="*/2 * * * *",
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei", "spider"],
        max_active_tasks=10,  # 限制并发数
        max_active_runs=1  # 限制同时运行的实例数量
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

    @task()
    def crawl_duopei(url):
        import subprocess
        subprocess.run(['/home/nizai9a/miniconda3/envs/PlaySpider/bin/python', '-m',
                        'scrapy', 'crawl', 'duopei', '-a', f'start_url={url}'],
                       cwd='/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider')

    # [START main_flow]
    urls = query_urls()
    crawl_duopei.expand(url=urls)


# [START dag_invocation]
duopei_append()
