import os

# 获取当前文件所在的目录
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))

# 参数设置
DS_PATH = f'{ROOT_PATH}/DataSets/2023-Escort'  # 路径
WEB_CORE = 'chromium'  # webkit chromium firefox
TIME_OUT = 40
CPU_CORE = 4
CRAWL_INTERVAL = 1  # 爬取间隔
