import os
import random
import time
from loguru import logger
from playwright.sync_api import sync_playwright
from tabulate import tabulate

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self) -> None:
        try:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(
                headless=True,  # GitHub Actions 环境下需要使用 headless 模式
                timeout=30000,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--start-maximized'
                ]
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.page = self.context.new_page()
            self.playwright = playwright  # 保存 playwright 实例以便后续清理
            
        except Exception as e:
            logger.error(f"初始化浏览器失败: {str(e)}")
            raise

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")

    def login(self):
        logger.info("开始登录流程")
        try:
            # 1. 访问首页
            logger.info("正在访问首页")
            self.page.goto(HOME_URL, wait_until="networkidle")
            self.page.screenshot(path="1_homepage.png")  # 保存截图用于调试
            time.sleep(3)
    
            # 2. 点击登录按钮
            logger.info("等待登录按钮出现")
            try:
                # 使用多个可能的选择器
                login_button = None
                for selector in ["button.login-button", "a.login-button", "[href='/login']"]:
                    try:
                        login_button = self.page.wait_for_selector(selector, timeout=5000)
                        if login_button:
                            logger.info(f"找到登录按钮: {selector}")
                            break
                    except:
                        continue
    
                if not login_button:
                    logger.error("未找到登录按钮")
                    return False
    
                login_button.click()
                logger.info("已点击登录按钮")
                self.page.screenshot(path="2_login_modal.png")
                time.sleep(3)
    
            except Exception as e:
                logger.error(f"点击登录按钮失败: {str(e)}")
                return False
    
            # 3. 等待登录表单加载
            logger.info("等待登录表单加载")
            try:
                self.page.wait_for_selector('div.login-modal', timeout=10000)
                logger.info("登录表单已加载")
                self.page.screenshot(path="3_login_form.png")
            except Exception as e:
                logger.error(f"等待登录表单超时: {str(e)}")
                return False
    
            # 4. 填写登录表单
            logger.info("开始填写登录表单")
            try:
                # 先尝试直接填写
                self.page.fill("#login-account-name", USERNAME)
                self.page.fill("#login-account-password", PASSWORD)
                
                # 如果直接填写失败，使用 JavaScript 注入
                self.page.evaluate(f'''
                    document.querySelector("#login-account-name").value = "{USERNAME}";
                    document.querySelector("#login-account-password").value = "{PASSWORD}";
                ''')
                
                logger.info("登录表单填写完成")
                self.page.screenshot(path="4_filled_form.png")
                time.sleep(2)
    
            except Exception as e:
                logger.error(f"填写登录表单失败: {str(e)}")
                return False
    
            # 5. 提交登录
            logger.info("准备提交登录")
            try:
                submit_button = self.page.wait_for_selector("#login-button", timeout=5000)
                if submit_button:
                    submit_button.click()
                    logger.info("已点击登录提交按钮")
                    self.page.screenshot(path="5_after_submit.png")
                else:
                    logger.error("未找到登录提交按钮")
                    return False
    
            except Exception as e:
                logger.error(f"提交登录失败: {str(e)}")
                return False
    
            # 6. 验证登录结果
            logger.info("验证登录结果")
            try:
                # 等待可能的错误消息
                error_message = self.page.query_selector(".alert-error")
                if error_message:
                    error_text = error_message.text_content()
                    logger.error(f"登录失败，错误信息: {error_text}")
                    return False
    
                # 检查登录成功标志
                success = False
                for selector in ["#current-user", ".user-menu", ".current-user"]:
                    try:
                        self.page.wait_for_selector(selector, timeout=5000)
                        success = True
                        break
                    except:
                        continue
    
                if success:
                    logger.info("登录成功！")
                    self.page.screenshot(path="6_login_success.png")
                    return True
                else:
                    logger.error("未检测到登录成功标志")
                    return False
    
            except Exception as e:
                logger.error(f"验证登录结果时出错: {str(e)}")
                return False
    
        except Exception as e:
            logger.error(f"登录过程出现未预期的错误: {str(e)}")
            return False
    
        return False

    def click_topic(self):
        topic_list = self.page.query_selector_all("#list-area .title")
        logger.info(f"Click {len(topic_list)} topics")
        for topic in topic_list:
            logger.info("Click topic: " + topic.get_attribute("href"))
            page = self.context.new_page()
            page.goto(HOME_URL + topic.get_attribute("href"))
            if random.random() < 0.3:  # 0.3 * 30 = 9
                self.click_like(page)
            self.browse_post(page)
            page.close()

    def browse_post(self, page):
        prev_url = None
        # 开始自动滚动，最多滚动10次
        for _ in range(10):
            # 随机滚动一段距离
            scroll_distance = random.randint(550, 650)  # 随机滚动 550-650 像素
            logger.info(f"Scrolling down by {scroll_distance} pixels...")
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            logger.info(f"Loaded: {page.url}")

            if random.random() < 0.03:  # 33 * 4 = 132
                logger.success("Randomly exit")
                break

            # 检查是否到达页面底部
            at_bottom = page.evaluate("window.scrollY + window.innerHeight >= document.body.scrollHeight")
            current_url = page.url
            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("Reached the bottom of the page. Exiting.")
                break

            # 动态随机等待
            wait_time = random.uniform(2, 4)  # 随机等待 2-4 秒
            logger.info(f"Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)

    def run(self):
        if not self.login():
            return
        self.click_topic()
        self.print_connect_info()

    def click_like(self, page):
        try:
            # 专门查找未点赞的按钮
            like_button = page.locator('.discourse-reactions-reaction-button[title="点赞此帖子"]').first
            if like_button:
                logger.info("找到未点赞的帖子，准备点赞")
                like_button.click()
                logger.info("点赞成功")
                time.sleep(random.uniform(1, 2))
            else:
                logger.info("帖子可能已经点过赞了")
        except Exception as e:
            logger.error(f"点赞失败: {str(e)}")

    def print_connect_info(self):
        logger.info("Print connect info")
        page = self.context.new_page()
        page.goto("https://connect.linux.do/")
        rows = page.query_selector_all("table tr")

        info = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        print("--------------Connect Info-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

        page.close()


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD")
        exit(1)
    l = LinuxDoBrowser()
    l.run()
