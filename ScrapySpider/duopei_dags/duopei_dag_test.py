from __future__ import annotations

# [START import_module]

import pendulum

from airflow.decorators import dag, task

from airflow.operators.python import PythonOperator


# [END import_module]


# [START instantiate_dag]
@dag(
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei", "tset"],
        max_active_tasks=10,  # 限制并发数
        max_active_runs=1  # 限制同时运行的实例数量
)
def duopei_test():
    @task()
    def select_urls():
        return ['1', '2', '3', '4', '5']

    @task
    def crawl_duopei(url):
        print(url)
        return url

    crawl_duopei.expand(url=select_urls())


load_tasks = []
# [START dag_invocation]
duopei_test()
