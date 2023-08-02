from playwright.async_api import async_playwright
import asyncio


async def run_login():
    # 启动浏览器
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    # 导航
    await page.goto('https://www.baidu.com')

    # 点击登录按钮
    await page.locator('#s-top-loginbtn').click()

    # 输入用户名
    await page.locator('#TANGRAM__PSP_11__userName').fill('111')
    await page.locator('#TANGRAM__PSP_11__password').fill('111')

    # 登录
    await page.locator('#TANGRAM__PSP_11__submit').click()


if __name__ == "__main__":
    asyncio.run(run_login())
