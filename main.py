# 全局环境变量放在最顶部
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# 导入拆分后的模块
from selenium_bilibili import init_chrome_driver, bilibili_login

if __name__ == "__main__":
    # 初始化浏览器
    driver, wait = init_chrome_driver()
    try:
        # 执行B站登录逻辑
        bilibili_login(driver, wait)
    except Exception as e:
        print("程序顶层异常：", e)
    finally:
        # 程序结束关闭浏览器
        driver.quit()