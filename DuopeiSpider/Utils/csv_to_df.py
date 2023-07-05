from DuopeiSpider.Utils.setting import DS_PATH
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT
import pandas as pd
import numpy as np


# 定义解析函数
def parse_csv_1(df: pd.DataFrame) -> pd.DataFrame:
    def shift_data(df_shift, mask, start, end):
        """
        # 定义一个函数用于移动数据
        """
        columns = [f'info_{i}' for i in range(start, end)]
        df_shift.loc[mask, columns] = df_shift.loc[mask, columns].shift(1, axis=1)

    shift_data(df, df['info_3'].str.contains('糖果'), 3, 10)
    shift_data(df, (df['info_5'] == '在线') | (df['info_5'] == '离线'), 5, 10)
    # 遗漏项
    df['user_position'] = '未获取'
    # 修改列名
    df = df.rename(
            columns={'info_1': 'user_name', 'info_2': 'user_age', 'info_3': 'user_service', 'info_4': 'user_grade',
                     'info_5': 'user_tag', 'info_6': 'user_status', 'info_9': 'user_profile', 'audio_url': 'user_audio_url'})

    return df


def parse_csv_2(df: pd.DataFrame) -> pd.DataFrame:
    # 解析
    df['user_status'] = df['info_4'].str[:2]
    df['user_service'] = df['info_4'].str[2:]
    df['user_sex'] = df['info_5'].str.extract(r'(男|女)')
    df['user_age'] = df['info_5'].str.extract(r'(\d+)岁')
    df['user_position'] = df['info_5'].str.extract(r'\d+岁(.+?)\d+元起')
    df['user_grade'] = df['info_5'].str.extract(r'(\d+)元起') + '元起'

    # 修改列名
    df = df.rename(
            columns={'info_0': 'user_grade', 'info_2': 'user_name', 'info_6': 'user_tag',
                     'info_7': 'user_profile', 'audio_url': 'user_audio_url'})

    return df


def parse_csv_3(df: pd.DataFrame) -> pd.DataFrame:
    # 解析
    columns = [f'info_{i}' for i in range(3, 11)]
    for i in range(3, 11):
        df.loc[df[f'info_{i}'].isna(), columns] = df.loc[df[f'info_{i}'].isna(), columns].shift(1, axis=1)
    df['user_sex'] = df['info_8'].str[:1]
    df['user_age'] = df['info_8'].str[1:]
    df['user_service'] = df['info_3'].astype('str') + df['info_4'].astype('str') + df['info_5'].astype('str') + df['info_6'].astype('str') + \
                         df['info_7'].astype('str')
    df['user_service'] = df['user_service'].str.replace('None', '')
    df['user_status'] = np.where(df['user_service'].str.contains('在线'), '在线', '离线')
    df['user_service'] = df['user_service'].str.replace('在线', '')
    df['user_service'] = df['user_service'].str.replace('离线', '')
    df['user_grade'] = '未获取'

    # 修改列名
    df = df.rename(columns={'info_1': 'user_name', 'info_2': 'user_position', 'info_9': 'user_tag',
                            'info_10': 'user_profile', 'audio_url': 'user_audio_url'})

    return df


def parse_csv_4(df: pd.DataFrame) -> pd.DataFrame:
    # 解析
    df['user_status'] = df['info_4'].str[:2]
    df['user_service'] = df['info_4'].str[2:]
    df['user_sex'] = df['info_5'].str.extract(r'(男|女)')
    df['user_age'] = df['info_5'].str.extract(r'(\d+)岁')
    df['user_position'] = df['info_5'].str.extract(r'\d+岁(.+?)\d+花瓣起')
    df['user_grade'] = df['info_5'].str.extract(r'(\d+)花瓣起') + '花瓣起'

    # 修改列名
    df = df.rename(
            columns={'info_0': 'user_grade', 'info_2': 'user_name', 'info_6': 'user_tag',
                     'info_7': 'user_profile', 'audio_url': 'user_audio_url'})

    return df


def parse_csv_gift(df: pd.DataFrame) -> pd.DataFrame:
    # 解析
    gift_columns = [i for i in df.columns if 'gift' in i]
    for i in gift_columns:
        df[i] = np.where(df[i].str.contains('x0'), '', df[i])
    df['user_gift'] = [' '.join(row) for row in df[gift_columns].values]
    df['user_gift'] = df['user_gift'].str.replace('\n', '')
    df['user_gift'] = df['user_gift'].str.replace('观看特效', '')
    return df


# 创建字典映射
function_mapping = {
        '糖恋树洞': parse_csv_1,
        '天空猫的树洞': parse_csv_2,
        '橘色灯罩': parse_csv_3,
        '清欢树洞': parse_csv_4
}


def run():
    df_merge = pd.DataFrame()
    for web in WEBSITE_DICT.keys():
        df_web_csv = pd.read_csv(f"{DS_PATH}/{WEBSITE_DICT[web]['name']}/user_info/user_card.csv")
        df_pharse = parse_csv_gift(function_mapping.get(WEBSITE_DICT[web]['name'], None)(df_web_csv)).rename(columns={'img_0': 'user_img'})
        df_pharse_use = df_pharse[
            ['user_rank', 'user_name', 'user_img', 'user_url', 'user_position', 'user_tag', 'user_profile', 'user_status', 'user_service',
             'user_audio_url', 'source_name', 'update_time']]
        df_merge = pd.concat([df_merge, df_pharse_use], axis=0, ignore_index=False)

    # 整合
    df_merge.to_csv(f"{DS_PATH}/dbs/user_card_all.csv", index=False)
