from playwright.sync_api import sync_playwright
import os
import requests
import time

# 发送 Telegram 消息
def send_telegram_message(message):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')  # 从环境变量中获取 bot token
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')  # 从环境变量中获取 chat ID
    if not bot_token or not chat_id:
        print("Telegram bot token 或 chat ID 未设置在环境变量中.")
        return None

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

# 登录 Webhost，并尝试多次登录
def login_koyeb(email, password, max_retries=5):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)  # 启动浏览器（无头模式）
        page = browser.new_page()

        # 访问登录页面
        page.goto("https://webhostmost.com/login")

        retries = 0
        while retries < max_retries:
            # 等待邮箱输入框并填写
            page.wait_for_selector('input[placeholder="Enter email"]')
            page.fill('input[placeholder="Enter email"]', email)

            # 等待密码输入框并填写
            page.wait_for_selector('input[placeholder="Password"]')
            page.fill('input[placeholder="Password"]', password)

            # 点击登录按钮
            page.wait_for_selector('button[type="submit"]')
            page.click('button[type="submit"]')

            # 等待错误信息或仪表板页面
            try:
                error_message = page.wait_for_selector('.MuiAlert-message', timeout=5000)
                if error_message:
                    error_text = error_message.inner_text()
                    print(f"第 {retries + 1} 次登录失败: {error_text}")
                    retries += 1
                    if retries < max_retries:
                        print("等待 1 秒后重试...")
                        time.sleep(1)  # 等待 5 秒后重试
                    continue
            except:
                # 如果没有错误，检查是否跳转到仪表板页面
                try:
                    page.wait_for_url("https://webhostmost.com/clientarea.php", timeout=5000)
                    print(f"账号 {email} 登录成功!")
                    browser.close()
                    return f"账号 {email} 登录成功!"
                except:
                    print(f"第 {retries + 1} 次登录失败: 未能跳转到仪表板页面")
                    retries += 1
                    if retries < max_retries:
                        print("等待 1 秒后重试...")
                        time.sleep(1)  # 等待 1 秒后重试
                    continue

        browser.close()
        return f"账号 {email} 登录失败: 尝试了 {max_retries} 次"

# 主程序
if __name__ == "__main__":
    # 从环境变量中获取账号信息（格式：email:password email:password ...）
    accounts = os.environ.get('WEBHOST', '').split(' ')
    login_statuses = []

    # 检查是否有配置账号
    if not accounts:
        print("没有配置任何账号")
        send_telegram_message("没有配置任何账号")
    else:
        # 遍历每个账号进行登录
        for account in accounts:
            email, password = account.split(':')
            status = login_koyeb(email, password)
            login_statuses.append(status)
            print(status)

        # 将所有登录状态发送到 Telegram
        if login_statuses:
            message = "WEBHOST登录状态:\n\n" + "\n".join(login_statuses)
            result = send_telegram_message(message)
            print("消息已发送到Telegram:", result)
