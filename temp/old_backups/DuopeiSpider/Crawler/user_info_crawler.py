"""
我需要使用playwright的异步方法爬取一个网站，该网站下面有一个用户列表。每个用户列表又对应一个链接，我需要对每个用户依次在新的链接上进行第二级的爬取，
我需要保存每个用户的头像，音频、地区、年龄等属性，既包含了结构化的数据又有非结构化的数据。帮我设计合适的程序结构，以及合适的文件储存架构。
"""
import asyncio

import time
import sys
import datetime

import pandas as pd
from tqdm import tqdm
import os
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from DuopeiSpider.Crawler.user_panel_crawler import Scraper
from DuopeiSpider.Utils.js_tools.js_script import *
from DuopeiSpider.Utils import setting as cf


class UserInfoScraper(Scraper):
    def __init__(self, headless):
        super().__init__(headless=headless)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

    # noinspection PyMethodMayBeStatic
    async def create_save_directories(self, name):
        img_dir = f"{cf.DS_PATH}/{name}/user_info/imgs"
        audio_dir = f"{cf.DS_PATH}/{name}/user_info/audios"
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

    # noinspection PyMethodMayBeStatic
    async def get_user_url(self, url) -> list[(str, int), ...] | None:
        # 读取用户URL列表
        user_url_path = f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/user_url.csv"
        if os.path.exists(user_url_path):
            df = pd.read_csv(user_url_path)
            user_list: [(str, int), ...] = list(zip(df['User_url'].tolist(), df['Rank'].tolist(), ))
        else: return None

        return user_list

    async def worker(self, page, web_site, queue, pbar, result_queue):
        while True:
            user_url = await queue.get()
            result = await self.process_user(page, web_site, user_url)
            await result_queue.put(result)
            queue.task_done()
            pbar.update(1)
            print(end='')

    # noinspection PyMethodMayBeStatic
    async def process_user(self, page, web_site, user_url):
        user_info_dict = {}
        user_url, user_rank = user_url
        print(end='')
        try:
            # 跳转页面
            await page.goto(user_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(1000)

            # # 定位照片墙
            # for k, v in enumerate(await page.locator(WEBSITE_DICT[web_site]['img_wall_selector']).all()):
            #     user_info_dict[f'img_{k}'] = await v.get_attribute('src')
            #
            # # 点击公告
            # await page.locator(WEBSITE_DICT[web_site]['dialog_button_selector']).click()
            # await page.wait_for_timeout(1000)

            # 解析音频
            # async with page.expect_response(lambda response: 'mp3' in response.url) as response_info:
            #     await page.locator(WEBSITE_DICT[web_site]['clerk_audio_selector']).click()
            #     await page.wait_for_timeout(1000)
            #     user_info_dict['audio_url'] = (await response_info.value).url

            # 解析个人资料
            user_info: [] = await page.locator(WEBSITE_DICT[web_site]['clerk_info_selector']).all_inner_texts()

            #
            # 解析礼物墙
            user_gift_wall: [str, ...] = await page.locator('div.row-item').all_inner_texts()

            # 生成信息字典
            for k, v in enumerate(user_info[0].split('\n')):
                user_info_dict[f'info_{k}'] = v
            for k, v in enumerate(user_gift_wall):
                user_info_dict[f'gift_{k}'] = v

            # 额外元数据
            user_info_dict['user_rank'] = user_rank
            user_info_dict['user_url'] = user_url
            user_info_dict['user_source'] = web_site
            user_info_dict['source_name'] = WEBSITE_DICT[web_site]['name']
            user_info_dict['update_time'] = datetime.datetime.now()

            # 处理成功
            return user_info_dict


        except (PlaywrightTimeoutError, PlaywrightError) as e:
            # failed_urls.append((user_url, user_rank))
            # print(f'Failed to process {user_url} with error: {e}')
            # await page.screenshot(path=f'{cf.DS_PATH}/{WEBSITE_DICT[web_site]["name"]}/screenshots/{user_rank}.png')
            # await asyncio.sleep(1)
            return user_info_dict

        finally:
            print(end='')
            await asyncio.sleep(1)

    async def process_urls(self, web_site, urls, failed_urls):
        """
        处理用户失败URL列表
        """
        tasks = []
        with tqdm(total=len(urls)) as pbar:
            for user_url, user_rank in urls:
                task = asyncio.create_task(self.process_user(web_site, user_url, user_rank, pbar, failed_urls))
                tasks.append(task)
            return await asyncio.gather(*tasks)

    async def run_remote_old(self, web_site):
        user_urls = await self.get_user_url(web_site)
        failed_urls = []
        user_info_list = await self.process_urls(web_site, user_urls, failed_urls)

        # keep processing failed URLs until there's none left
        while failed_urls:
            temp_failed_urls = failed_urls.copy()
            failed_urls = []  # reset the list for the next run
            failed_user_info_list = await self.process_urls(web_site, temp_failed_urls, failed_urls)
            user_info_list.extend(failed_user_info_list)  # combine the results

        # 保存结果
        pd.DataFrame(user_info_list).to_csv(f"{cf.DS_PATH}/{WEBSITE_DICT[web_site]['name']}/user_info/user_card.csv", escapechar='\\',
                                            index=False)

    async def run_remote(self, semaphore, web_site, coroutine_num=10):
        print(end='')
        async with semaphore:
            print(end='')
            print(web_site)
            # 1. 创建5个页面
            contexts = [await self.browser.new_context() for _ in range(coroutine_num)]
            pages = [await context.new_page() for context in contexts]

            # 2. 阻止在每个页面上加载图片
            for page in pages: await self.block_img(page, web_site)

            # 3. 获取用户URL列表并加入任务队列
            user_list = await self.get_user_url(web_site)
            task_queue = asyncio.Queue()
            for user_url in user_list: task_queue.put_nowait(user_url)

            # 4. 创建tqdm progress bar
            pbar = tqdm(total=task_queue.qsize())

            # 5. 创建并开启5个worker协程
            result_queue = asyncio.Queue()
            tasks = [asyncio.create_task(self.worker(pages[i], web_site, task_queue, pbar, result_queue)) for i in range(coroutine_num)]

            # 6. 等待所有任务完成
            await task_queue.join()
            for task in tasks: task.cancel()

            # Wait until all worker tasks are cancelled.
            await asyncio.gather(*tasks, return_exceptions=True)

            # 9. 关闭所有页面
            for page in pages: await page.close()

            # 10. 关闭tqdm progress bar
            pbar.close()

            #
            results = []
            while not result_queue.empty():
                item = await result_queue.get()
                if item:
                    results.append(item)

            # 保存结果
            pd.DataFrame(results).to_csv(f"{cf.DS_PATH}/{WEBSITE_DICT[web_site]['name']}/user_info/user_card.csv",
                                         escapechar='\\',
                                         index=False)

    async def run_local(self, url):
        # 创建目录
        await self.create_save_directories(WEBSITE_DICT[url]['name'])

        # 读取用户URL列表
        user_urls = await self.get_user_url(url)
        page = await self.browser.new_page()

        # 开始爬取
        user_info_list: [{}] = []
        for user_url, user_rank in tqdm(user_urls):
            try:
                while True:
                    # 导航到需要爬取的网站
                    await page.goto(user_url)
                    await page.wait_for_load_state('networkidle')

                    # 定义存储信息的字典
                    user_info_dict = {}

                    # 解析所有的照片墙
                    for k, v in enumerate(await page.locator(WEBSITE_DICT[url]['img_wall_selector']).all()):
                        user_info_dict[f'img_{k}'] = await v.get_attribute('src')

                    # 解析音频
                    await page.locator(WEBSITE_DICT[url]['dialog_button_selector']).click()  # 移除通知栏
                    async with page.expect_response(lambda response: 'mp3' in response.url) as response_info:
                        await page.locator(WEBSITE_DICT[url]['clerk_audio_selector']).click()
                    user_info_dict['audio_url'] = (await response_info.value).url

                    # 解析个人资料
                    user_info: [] = await page.locator(WEBSITE_DICT[url]['clerk_info_selector']).all_inner_texts()

                    # 解析礼物墙
                    user_gift_wall: [str, ...] = await page.locator('div.row-item').all_inner_texts()

                    # 生成信息字典
                    for k, v in enumerate(user_info[0].split('\n')):
                        user_info_dict[f'info_{k}'] = v
                    for k, v in enumerate(user_gift_wall):
                        user_info_dict[f'gift_{k}'] = v

                    # 额外元数据
                    user_info_dict['user_rank'] = user_rank
                    user_info_dict['user_url'] = user_url
                    user_info_dict['user_source'] = url
                    user_info_dict['source_name'] = WEBSITE_DICT[url]['name']
                    user_info_dict['update_time'] = datetime.datetime.now()

                    # 增加到列表
                    user_info_list.append(user_info_dict)
                    break
            except (PlaywrightTimeoutError, PlaywrightError, Exception):
                continue
            # 测试点
            # break
        await page.close()

        pd.DataFrame(user_info_list).to_csv(f"{cf.DS_PATH}/{WEBSITE_DICT[url]['name']}/user_info/user_card.csv", escapechar='\\',
                                            index=False)
