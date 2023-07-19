# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import logging
import pandas as pd
from .items import UserItem


# noinspection PyMethodMayBeStatic
class UserPipeline:
    """
    收集所有用户的数据，并创建DataFrame
    """

    def __init__(self):
        self.items = []

    def process_item(self, item: list[UserItem], spider):
        """
        在 process_item 方法中逐条处理数据可能更有效。这也可以让你更早地发现并处理潜在的数据问题。
        """
        self.items.append(item)
        return item

    def close_spider(self, spider):
        df = pd.DataFrame(self.items)
        df.to_csv('data/user.csv', index=False)

        # 基础数据清洗
        df['Name'] = df['Name'].apply(lambda x: x.strip())
        df['online_status'] = df['Online'].apply(lambda x: '在线' in x)

        # Function to extract grade from the string or url
        def extract_grade(s, position):
            if pd.isnull(s):  # Check if the string is NaN
                return 0
            else:
                if position == 'before':
                    target_part = s.rsplit('/', 1)[0]  # Split the string by '/' and take the first part
                elif position == 'after':
                    target_part = s.rsplit('/', 1)[-1]  # Split the string by '/' and take the last part
                else:
                    raise ValueError("Position must be either 'before' or 'after'")

                grade = re.findall(r'\d+', target_part)  # Find all digit sequences in the target part
                return grade[0] if grade else 0

        # Apply the function to the 'Grade' and 'GradeImg' columns
        df['Grade_from_price'] = df['GradePrice'].apply(extract_grade, position='before')
        df['Grade_from_url'] = df['GradeImg'].apply(extract_grade, position='after')

        # 分列提取服务信息
        df['Service'] = df['Service'].replace({r'●': '|', r'、': '|'}, regex=True).str.strip()
        services_df = df['Service'].str.get_dummies(sep='|')
        services_df.columns = services_df.columns.str.strip()
        df = df.join(services_df)

        # 转化为数字列
        for i in ['Age', 'Grade_from_price', 'Grade_from_url']:
            df[i] = pd.to_numeric(df[i], errors='coerce').fillna(0).astype(int)

        # 映射重复列名
        column_mapping = {'Grade_from_price': 'grade', 'Grade_from_url': 'grade',
                          '语音连麦': '连麦', '游戏陪玩': '游戏', '离线 + 客服预约': '离线', '买断专属': '买断'}
        df.rename(columns=column_mapping, inplace=True)

        # 重复列相加
        df = df.groupby(level=0, axis=1).sum()

        # 数据验证

        # 保存数据到数据库或其他地方
        df.to_csv('data/user_clean.csv', index=False)
        # df = pd.DataFrame(self.items)
        # print(df)
