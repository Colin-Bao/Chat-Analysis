import os
import pandas as pd


class DataHandler:
    """
    数据操作类
    """

    def __init__(self, root_path: str, logger_tup: tuple, url: str):
        self.ROOT_PATH = root_path
        self.user_daily_dir = None
        self.snapshot_dir = None
        self.user_info_dir = None
        self.url = url

        # 创建目录
        self.prepare_directories()

        # 日志处理
        self.info_logger, self.warn_logger, self.error_logger = logger_tup

    async def log(self, message: str, extra_dict: dict, level='info'):
        """
        日志记录
        :param extra_dict: 网站
        :param message:信息
        :param level:日志级别
        """
        extra = {'class_name': self.__class__.__name__, 'func_name': '', 'url_name': self.url}
        extra.update(extra_dict)
        (getattr(self, f'{level}_logger').log(
                msg=message,
                level={'info': 20, 'warn': 30, 'error': 40}.get(level, 20),
                extra=extra
        ))

    def prepare_directories(self):
        """
        创建数据存储的目录
        """
        self.user_daily_dir = os.path.join(self.ROOT_PATH, 'user_daily_data')
        self.snapshot_dir = os.path.join(self.ROOT_PATH, 'snapshots')
        self.user_info_dir = os.path.join(self.ROOT_PATH, 'user_info')
        os.makedirs(self.user_daily_dir, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.user_info_dir, exist_ok=True)


    async def get_snapshot(self, df_parse: pd.DataFrame, table_name, table_type) -> pd.DataFrame:
        """
        读取和创建文件，包括user和gift的缓存文件，和状态记录表缓存文件。例如(df,user,['bk','add'])
        :param df_parse: 解析的即时数据
        :param table_name:缓存文件名，user,gift
        :param table_type: 快照缓存表bk、状态记录表add,remove
        :return:返回缓存数据
        """
        try:
            df_bk = pd.read_parquet(f'{self.snapshot_dir}/{table_name}-{table_type}')
        except FileNotFoundError:
            df_parse.to_parquet(f'{self.snapshot_dir}/{table_name}-{table_type}', engine='fastparquet')
            df_bk = df_parse
        return df_bk

    async def update_info_change(self, df_new: pd.DataFrame, bk_name, copmare_method):
        """
        信息变更记录，与旧缓存对照
        :param df_new: 解析的即时数据
        :param bk_name: 缓存文件名
        :param copmare_method: 变更方式
        """
        assert copmare_method in ['add', 'remove'], 'update_type should be either "add" or "remove"'
        await self.log(f'开始差异对比{bk_name}-{copmare_method}', {'func_name': 'update_info_change'})

        # ------------- 0.读取旧缓存与状态记录表 -------------#
        df_old = await self.get_snapshot(df_new, bk_name, 'bk')  # 旧缓存
        existing_changed_users = await self.get_snapshot(df_new, bk_name, copmare_method)  # 状态记录表

        # ------------- 1.与旧缓存对比 -------------#
        if copmare_method == 'add':
            changed_users = df_new[~df_new['Name'].isin(df_old['Name'])]
            log_message = f"{bk_name}增加：\n"
        else:
            changed_users = df_old[~df_old['Name'].isin(df_new['Name'])]
            log_message = f"{bk_name}减少：\n"
        if changed_users.empty: return

        # ------------- 2.与状态记录表对比 -------------#
        unique_changed_users = changed_users[~changed_users['Name'].isin(existing_changed_users['Name'])]
        if unique_changed_users.empty: return
        # 保存
        unique_changed_users.to_parquet(f'{self.snapshot_dir}/{bk_name}-{copmare_method}', engine='fastparquet', append=True)
        await self.log(f"{log_message}{unique_changed_users.to_string()}", {'func_name': 'update_info_change'}, 'warn')

        # ------------- 3.更新缓存 -------------#
        df_new.to_parquet(f'{self.snapshot_dir}/{bk_name}-bk', engine='fastparquet')
        await self.log(f'{bk_name}缓存数据更新', {'func_name': 'update_info_change'})

    async def save_append(self, df: pd.DataFrame, file_path: str):
        """
        追加保存
        :param df: 要保存的数据
        :param file_path: 要存储的位置
        """

        if not os.path.isfile(file_path):
            df.to_parquet(file_path, engine='fastparquet')
        else:
            assert len(df.columns) == len(pd.read_parquet(file_path).columns)
            df.to_parquet(file_path, engine='fastparquet', append=True)
        await self.log(f'面板数据保存成功', {'func_name': 'save_append'})
