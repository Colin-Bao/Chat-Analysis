from __future__ import annotations

from datetime import timedelta

# [START import_module]

import pendulum

from airflow.decorators import dag, task


# [END import_module]


# [START instantiate_dag]
@dag(
        schedule="0 */1 * * *",
        # dagrun_timeout=timedelta(minutes=2),
        start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei", "test"],
        max_active_tasks=4,  # 限制并发数
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

    @task
    def crawl_complate(url):
        print(url)
        # return url

    for i in range(1):
        crawl_duopei(i)
    # select_urls()
    # s = crawl_duopei.expand(url=select_urls())
    # crawl_complate(s)
    # crawl_duopei("sss")


# [START dag_invocation]
duopei_test()
