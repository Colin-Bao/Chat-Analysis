import re

# 定义一些解析函数，每个函数处理一种URL模式
async def parse_url_pattern_1(gift_str: str) -> tuple:
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


async def parse_url_pattern_2(gift_str: str) -> tuple:
    # 处理方式2 天空猫
    name = gift_str.split('】')[0].replace('【', '')
    amount = gift_str.split('打赏')[1].replace('元', '').strip()
    gift = '元'
    return name.strip(), gift.strip(), float(amount)


async def parse_url_pattern_3(gift_str: str) -> tuple:
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


async def parse_url_pattern_4(gift_str: str) -> tuple:
    # 处理方式4 清欢
    name, rest = gift_str.split('收到了客人打赏', 1)
    name = re.search(r'【(.*?)】', name).group(1)
    amount = rest.replace('花瓣', '').strip()
    gift = '花瓣'
    return name.strip(), gift.strip(), float(amount)


#
website_dict = {
        'http://tj5uhmrpeq.duopei-m.featnet.com':
            {
                    'url': 'http://tj5uhmrpeq.duopei-m.featnet.com',
                    'name': '糖恋树洞',
                    'page_finished_selector': '.van-list__finished-text',
                    'user_info_selector':
                        {
                                'Name': '.name.text-ellipsis', 'Age': '.sex-age',
                                'Sex': '.sex-age',
                                'Online': '.StatusEnum',
                                'Grade': '.minPrice',
                                'Service': '.status.text-ellipsis'
                        },
                    'gift_info_selector': '.swiper-slide:not(.swiper-slide-duplicate)',
                    'url_to_parser': parse_url_pattern_1,
            },
        'http://oxxs5iqzqz.duopei-m.manongnet.cn':
            {
                    'url': 'http://oxxs5iqzqz.duopei-m.manongnet.cn',
                    'name': '天空猫的树洞',
                    'page_finished_selector': '.van-list__finished-text',
                    'user_info_selector':
                        {
                                'Name': '.name', 'Age': '.sex-age',
                                'Sex': '.sex-age',
                                'Online': '.status.text-ellipsis',
                                'GradeImg': '.grade img',
                                'Service': '.status.text-ellipsis'
                        },
                    'gift_info_selector': '.swiper-slide:not(.swiper-slide-duplicate)',
                    'url_to_parser': parse_url_pattern_2,
            },
        'http://8mukjha763.duopei-m.99c99c.com':
            {
                    'url': 'http://8mukjha763.duopei-m.99c99c.com',
                    'name': '橘色灯罩',
                    'page_finished_selector': '.van-list__finished-text',
                    'user_info_selector':
                        {
                                'Name': '.name.text-ellipsis', 'Age': '.sex-age',
                                'SexImg': '.sex-age img',
                                'Online': '.switch-name',
                                'Position': '.position.align-center',
                                'GradeImg': '.clerk-item__body > div:nth-child(2) > img',
                                'Service': '.switch-name'
                        },
                    'gift_info_selector': '.swiper-slide:not(.swiper-slide-duplicate)',
                    'url_to_parser': parse_url_pattern_3,
            },
        'http://fhpkn3rf85.duopei-m.manongnet.cn':
            {
                    'url': 'http://fhpkn3rf85.duopei-m.manongnet.cn',
                    'name': '清欢树洞',
                    'page_finished_selector': '.van-list__finished-text',
                    'user_info_selector':
                        {
                                'Name': '.name', 'Age': '.sex-age',
                                'SexImg': '.sex-age img',
                                'Online': '.status.text-ellipsis',
                                'GradeImg': '.grade img',
                                'Service': '.status.text-ellipsis'
                        },
                    'gift_info_selector': '.swiper-slide:not(.swiper-slide-duplicate)',
                    'url_to_parser': parse_url_pattern_4,
            },
}

## 提取用户信息JS代码
extract_user_info_js = '''(itemDict) => {
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

# async def ex_js():
#     from playwright.async_api import async_playwright
#     import time
#
#     async with async_playwright() as playwright:
#         # 启动浏览器
#         browser = await playwright.chromium.launch()
#
#         # 测试
#         for website in website_dict:
#             st = time.time()
#
#             # 在浏览器中创建新的页面
#             page = await browser.new_page()
#
#             # 打开网页
#             await page.goto(website['url'])
#             while not await page.locator('.van-list__finished-text').count():
#                 await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
#             data = await page.evaluate(extract_user_info_js, website['user_info_selector'])
#             print(data[:5])
#
#         # 关闭浏览器
#         await browser.close()

#
# if __name__ == '__main__':
#     import asyncio
#
#     asyncio.run(ex_js())
