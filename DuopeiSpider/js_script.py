import re


def test():
    pass
    # type_config = {'Rank': 'uint16', 'Name': 'category', 'Sex': 'bool', 'Age': 'uint8',
    #                'Online': 'bool', 'Grade': 'uint8', 'Text': 'bool',
    #                'Call': 'bool', 'Video': 'bool', 'Game': 'bool'}

    # df['Grade'] = pd.to_numeric(df['Grade'].str[:2], errors='coerce')
    # df['Text'] = df['Service'].str.contains('文语', case=False)
    # df['Call'] = df['Service'].str.contains('连麦', case=False)
    # df['Video'] = df['Service'].str.contains('视频', case=False)
    # df['Game'] = df['Service'].str.contains('游戏', case=False)
    # df['Sex'] = df['Sex'].apply(lambda x: True if x == '255' else False)
    # df['Online'] = df['Online'].apply(lambda x: True if x == '在线' else False)


# 定义一些解析函数，每个函数处理一种URL模式
async def parse_url_pattern_1(gift_str: str) -> tuple[str,str,float]:
    # 处理方式1 糖恋
    name, rest = gift_str.split('被打赏了', 1)
    # 分别考虑2种模式
    if '礼物' in rest:
        gift, amount = re.search(r'\[ (.*) \] x (\d+)', rest).groups()
    else:
        gift = '颗'
        amount = rest.replace('糖果', '').strip()
    # 添加到列表
    return name.strip(), gift.strip(), float(amount)


async def parse_url_pattern_2(gift_str: str) -> tuple[str,str,float]:
    # 处理方式2 天空猫
    name = gift_str.split('】')[0].replace('【', '')
    amount = gift_str.split('打赏')[1].replace('元', '').strip()
    gift = '元'
    return name.strip(), gift.strip(), float(amount)


async def parse_url_pattern_3(gift_str: str) -> tuple[str,str,float]:
    # 处理方式3 橘色灯罩
    name, rest = gift_str.split('打赏给')[1].split('】', 1)
    name = name.replace('【', '')
    # 分别考虑2种模式
    if '礼物' in rest:
        gift = re.search(r'\[ (.*?) \]', rest).group(1)
        amount = 1.0
    else:
        gift = '颗'
        amount = re.findall(r'\d+\.?\d*', rest)[0]
    return name.strip(), gift.strip(), float(amount)


async def parse_url_pattern_4(gift_str: str) -> tuple[str,str,float]:
    # 处理方式4 清欢
    name, rest = gift_str.split('收到了客人打赏', 1)
    name = re.search(r'【(.*?)】', name).group(1)
    amount = rest.replace('花瓣', '').strip()
    gift = '花瓣'
    return name.strip(), gift.strip(), float(amount)


#
import json
with open("/home/ubuntu/PycharmProjects/Chat-Analysis/DuopeiSpider/js_scripts/user_selector.json", "r") as file:
    json_data = file.read()
WEBSITE_DICT = json.loads(json_data)

# 'http://tj5uhmrpeq.duopei-m.featnet.com' ok
# http://oxxs5iqzqz.duopei-m.manongnet.cn ok
# http://8mukjha763.duopei-m.99c99c.com 不一致
# http://fhpkn3rf85.duopei-m.manongnet.cn ok
# WEBSITE_DICT = {key: value for key, value in WEBSITE_DICT.items() if key == 'http://8mukjha763.duopei-m.99c99c.com'}


## 提取用户信息JS代码
JS_USER_INFO = '''(itemDict) => {
                        const elements = document.querySelectorAll('.van-cell__value.van-cell__value--alone');
                        const data = [];
                        for (const element of elements) {
                            const row = {};
                            for (const [attr, classname] of Object.entries(itemDict)) {
                                const subElement = element.querySelector(classname);
                                if (subElement) {
                                    let textContent;
                                    if (attr === 'Sex') {
                                        textContent = subElement.getAttribute("style").trim();
                                    } 
                                    else if (attr === 'GradeImg') {
                                        textContent = subElement.getAttribute("src").trim();
                                    }
                                    else if (attr === 'SexImg') {
                                        textContent = subElement.getAttribute("src").trim();
                                    }
                                    else {
                                        textContent = subElement.textContent.trim();
                                    }
                                    row[attr] = textContent;
                                }
                            }
                            if (Object.keys(row).length === Object.keys(itemDict).length) {
                                data.push(row);
                            }
                        }
                        return data;
                    }
                '''
