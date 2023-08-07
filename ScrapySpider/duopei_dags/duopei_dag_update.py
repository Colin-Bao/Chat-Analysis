#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

# [START tutorial]
# [START import_module]

import pendulum

from airflow.decorators import dag, task


# [END import_module]


# [START instantiate_dag]
@dag(
        schedule="0 */3 * * *",
        start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Shanghai"),
        catchup=False,
        tags=["duopei"],
)
def duopei_update():
    """
    ### TaskFlow API Tutorial Documentation
    This is a simple data pipeline example which demonstrates the use of
    the TaskFlow API using three simple tasks for Extract, Transform, and Load.
    Documentation that goes along with the Airflow TaskFlow API tutorial is
    located
    [here](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
    """

    # [END instantiate_dag]

    # [START extract]
    @task()
    def extract():
        """
        #### Extract task
        A simple Extract task to get data ready for the rest of the data
        pipeline. In this case, getting data is simulated by reading from a
        hardcoded JSON string.
        """
        import subprocess
        subprocess.run(['scrapy', 'crawl', 'duopei', '-a', 'use_url_crawl=true', '-a', 'crawl_mode_append=false'], cwd='/home/nizai9a/PycharmProjects/Chat-Analysis/ScrapySpider')
        return None

    extract()


# [START dag_invocation]
dag_instance = duopei_update()
# [END dag_invocation]
