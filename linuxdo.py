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
            # 访问首页
            self.page.goto(HOME_URL, wait_until="networkidle", timeout=60000)
            logger.info("页面加载完成")
            time.sleep(3)
    
            # 点击登录按钮打开登录框
            login_button = self.page.wait_for_selector("button.login-button", timeout=10000)
            if login_button:
                login_button.click()
                logger.info("已点击登录按钮")
                time.sleep(3)
    
            # 使用 JavaScript 模拟真实的用户输入
            logger.info("开始填写登录表单")
            self.page.evaluate('''(username, password) => {
                // 模拟真实的用户输入事件
                function simulateUserInput(element, value) {
                    element.focus();
                    element.value = value;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('blur', { bubbles: true }));
                }
                
                const usernameInput = document.querySelector("#login-account-name");
                const passwordInput = document.querySelector("#login-account-password");
                
                simulateUserInput(usernameInput, username);
                simulateUserInput(passwordInput, password);
            }''', USERNAME, PASSWORD)
            
            logger.info("表单填写完成")
            time.sleep(2)
    
            # 模拟真实的点击行为
            logger.info("准备提交表单")
            self.page.evaluate('''() => {
                const button = document.querySelector("#login-button");
                
                // 模拟鼠标移动到按钮上
                button.dispatchEvent(new MouseEvent('mouseover', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                
                // 模拟鼠标按下
                button.dispatchEvent(new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                
                // 模拟点击
                button.dispatchEvent(new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                
                // 模拟鼠标释放
                button.dispatchEvent(new MouseEvent('mouseup', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
            }''')
            
            logger.info("已提交表单")
    
            # 等待页面加载完成
            self.page.wait_for_load_state("networkidle")
            time.sleep(5)
    
            # 验证登录状态
            login_status = self.page.evaluate('''() => {
                // 等待一段时间检查登录状态
                return new Promise((resolve) => {
                    let checkCount = 0;
                    const maxChecks = 10;
                    
                    function checkLoginStatus() {
                        const userElement = document.querySelector("#current-user");
                        if (userElement) {
                            resolve({ success: true, message: "找到用户元素" });
                            return;
                        }
                        
                        checkCount++;
                        if (checkCount >= maxChecks) {
                            resolve({ 
                                success: false, 
                                message: "未找到用户元素",
                                url: window.location.href,
                                html: document.documentElement.innerHTML
                            });
                            return;
                        }
                        
                        setTimeout(checkLoginStatus, 1000);
                    }
                    
                    checkLoginStatus();
                });
            }''')
            
            logger.info(f"登录状态检查结果: {login_status}")
            
            if login_status.get('success'):
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                # 保存页面内容用于调试
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(login_status.get('html', ''))
                return False
    
        except Exception as e:
            logger.error(f"登录过程出错: {str(e)}")
            self.page.screenshot(path="error.png")
            return False
    

    def click_topic(self):
        logger.info("获取话题列表")
        topic_list = self.page.query_selector("#list-area .title")
        logger.info(f"共获取到 {len(topic_list)} 条话题")
        for topic in topic_list:
            logger.info("点击话题: " + topic.get_attribute("href"))
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
