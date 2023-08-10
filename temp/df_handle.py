import re

user_orm = None


def clean_data_df(userobj):
    import numpy as np
    import pandas as pd
    # 将User对象的属性转换为字典
    user_dict = {column.name: getattr(user_orm, column.name) for column in userobj.__table__.columns}

    # 创建一个Dataframe，需要将字典转换为列表的形式，因为Dataframe期望的是一个二维的数据结构
    df = pd.DataFrame([user_dict])
    # df.to_csv(Path(__file__).resolve().parent / 'data' / 'user.csv', index=False, escapechar='\\')

    # 基础数据清洗
    df['name'] = df['Name'].str.strip()
    df['Tag'] = df['Tag'].replace('\s+|\n', '', regex=True)
    df['TagSep'] = df['TagSep'].replace('\s+|\n', '', regex=True)

    # 提取条件状态信息 全部转为了数字
    def extract_by_condition(df_con):
        df_con['online_status'] = np.where(df_con['Service'].str.contains('在线'), 1, 0)
        df_con['tag'] = np.where(df_con['Tag'] != 0, df_con['Tag'], df_con['TagSep'])
        return df_con

    # 提取等级信息
    def extract_grade(df_grade):
        def extract_grade_by_str(s, position):
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
                return int(grade[0]) if grade else 0  # 过滤 TODO 放到其他部分

        # Apply the function to the 'Grade' and 'GradeImg' columns
        df_grade['Grade_from_price'] = df_grade['GradePrice'].apply(extract_grade_by_str, position='before')
        df_grade['Grade_from_url'] = df_grade['GradeImg'].apply(extract_grade_by_str, position='after')

        return df_grade

    # 提取服务信息
    def extract_service(df_ser):
        df_ser['Service'] = np.where(pd.isnull(df_ser['Service']), df_ser['ServiceSep'], df_ser['Service'])
        df_ser['Service'] = df_ser['Service'].replace({r'●': '|', r'、': '|'}, regex=True).str.strip()
        services_df = df_ser['Service'].str.get_dummies(sep='|')
        services_df.columns = services_df.columns.str.strip()
        df_ser = df_ser.join(services_df)

        # 转化为数字列
        for i in ['Age', 'Grade_from_price', 'Grade_from_url']:
            df_ser[i] = pd.to_numeric(df_ser[i], errors='coerce').fillna(0).astype(int)

        # 映射重复列名
        column_mapping = {
                'grade': ['Grade_from_price', 'Grade_from_url'],
                '连麦': ['语音连麦', '可语音', '可连麦', '语音通话', ],
                '视频': ['视频聊天'],
                '游戏': ['游戏陪玩', '原神', 'csgo', '可游戏', '和平精英一局', '王者荣耀一局', '永劫无间', '金铲铲之战', '蛋仔派对',
                         '手游',
                         '端游', '陪玩'],
                '文语': ['文字语音条'],
                '学习辅导': ['教作业'],
                '点歌': ['点歌服务', '唱歌'],
                '离线': ['离线 + 客服预约'],
                '买断': ['买断专属'],
        }

        # 翻转字典，准备进行列名的映射
        reverse_mapping = {old: new for new, old_list in column_mapping.items() for old in old_list}

        # 映射列名
        for col in df_ser.columns:
            if col in reverse_mapping:
                df_ser.rename(columns={col: reverse_mapping[col]}, inplace=True)

        # 重复列相加
        df_ser = df_ser.groupby(level=0, axis=1).sum()
        return df_ser

    # 提取所有信息
    df = extract_by_condition(extract_service(extract_grade(df)))

    # 选择数据列
    # df = df[['Age', 'AvatarImg', 'grade', 'name', 'online_status',
    #          'Position', 'Profile', 'tag', 'audio_url', 'company', 'crawl_date', 'crawl_date_2',
    #          'grade', 'homepage', 'online_status', 'rank', 'rank_2', 'website', ]]

    return df
