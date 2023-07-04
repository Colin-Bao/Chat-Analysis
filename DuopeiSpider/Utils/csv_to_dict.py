from DuopeiSpider.Utils.setting import DS_PATH
from DuopeiSpider.Utils.js_tools.js_script import WEBSITE_DICT
# Replace with your actual data
import pandas as pd

df = pd.read_csv(f'{DS_PATH}/天空猫的树洞/user_info/user_card.csv')
df = df.rename(
        columns={'info_0': 'user_grade', 'info_2': 'user_name', 'info_4': 'user_service', 'info_5': 'user_position',
                 'info_6': 'user_tag',
                 'info_7': 'user_profile', 'audio_url': 'user_audio_url'})
df = df.filter(regex=r'^(?!gift_|info_)', axis=1)
