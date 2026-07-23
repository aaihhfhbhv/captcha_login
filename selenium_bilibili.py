import time
import cv2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from ocr_engine import mox

# 全局浏览器初始化函数
def init_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    service = Service(executable_path=r'driver/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 15)
    return driver, wait

# =====================通用验证码处理函数（一次/二次验证复用）=====================
def run_captcha_flow(driver, wait, max_retry=8):
    retry_count = 0
    captcha_pass = False
    while retry_count < max_retry and not captcha_pass:
        retry_count += 1
        print(f"\n========== 验证码第 {retry_count} 次尝试 ==========")

        # 关闭尝试过多弹窗
        try:
            error_btn = WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "geetest_panel_error_content"))
            )
            error_btn.click()
            print("⚠️ 检测到尝试过多弹窗，已点击关闭")
            time.sleep(1.2)
        except:
            pass

        try:
            # 截图验证码背景图
            captcha_wrap_elem = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "geetest_item_wrap")))
            captcha_path_part1 = "captcha_part1.jpg"
            captcha_wrap_elem.screenshot(captcha_path_part1)

            # 截图顶部提示文字
            captcha_tip_elem = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "geetest_tip_img")))
            captcha_path_part2 = "captcha_part2.jpg"
            captcha_tip_elem.screenshot(captcha_path_part2)

            # OCR识别
            results = mox(None, captcha_path_part1)
            results_order = mox(None, captcha_path_part2)
            print("背景图识别结果：", results)
            print("提示图识别结果：", results_order)

            # 识别为空，自动刷新验证码
            if not results or not results_order:
                print("❌ OCR识别为空，自动刷新验证码图片")
                refresh_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "geetest_refresh")))
                refresh_btn.click()
                time.sleep(1.5)
                continue

            # 拼接提示文字，获取点击顺序
            target_raw_text = ""
            for item in results_order:
                target_raw_text += item[1].strip()
            target_order = list(target_raw_text)
            click_count = len(target_order)
            sort_list = list(range(10))  # 用于处理不在序列内的文字，后置
            for txt in results:
                try:
                    sort_list.remove(target_order.index(txt[1]))
                except ValueError:
                    pass

            print(f"\n👉 OCR识别提示文本：{target_raw_text}")
            print(f"👉 拆分后点击顺序：{target_order}")
            print(f"👉 需要点击次数：{click_count}")

            # 按提示文字排序识别结果
            def sort_key(item):
                txt = item[1]
                try:
                    return target_order.index(txt)
                except ValueError:
                    print(f"⚠️ 文字【{txt}】不在序列内，后置")
                    return sort_list.pop(0)

            res = sorted(results, key=sort_key)
            print(f"👉 即将点击文字序列：{[i[1] for i in res]}")

            # 读取截图尺寸，计算文字中心点
            img = cv2.imread(captcha_path_part1)
            img_h, img_w = img.shape[:2]
            centers = []
            for (bbox, text, confidence) in res:
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                raw_cx = sum(x_coords) / 4
                raw_cy = sum(y_coords) / 4
                centers.append((raw_cx, raw_cy))

            # 绘制标记图保存
            draw_img = img.copy()
            for (bbox, text, confidence) in results:
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                center_x = int(sum(x_coords) / 4)
                center_y = int(sum(y_coords) / 4)
                cv2.circle(draw_img, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.imwrite('captcha.jpg', draw_img)
            print("✅ 标记图片已保存 captcha.jpg")

            # 按提示文字数量截取坐标循环点击
            click_targets = centers[:click_count]
            for raw_cx, raw_cy in click_targets:
                captcha_wrap_elem = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "geetest_item_wrap")))
                actions = ActionChains(driver)
                actions.move_to_element_with_offset(captcha_wrap_elem, -152, -152)
                actions.move_by_offset(raw_cx, raw_cy)
                actions.click().pause(0.7)
                actions.perform()
                actions.reset_actions()
                time.sleep(0.8)

            # 点击确认按钮提交验证码
            print("✅ 文字点击完成，准备点击确认按钮")
            confirm_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "geetest_commit_tip")))
            confirm_btn.click()
            time.sleep(2)

            # 再次关闭限制弹窗
            try:
                error_btn = WebDriverWait(driver, 1.5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "geetest_panel_error_content"))
                )
                error_btn.click()
                print("⚠️ 检测到尝试过多弹窗，已点击关闭")
                time.sleep(1.2)
            except:
                pass

            # 判断验证码弹窗是否消失，验证通过
            try:
                WebDriverWait(driver, 3).until_not(
                    EC.visibility_of_element_located((By.CLASS_NAME, "geetest_item_wrap"))
                )
                captcha_pass = True
                print("🎉 当前轮验证码验证通过！")
            except:
                print("❌ 验证失败，等待页面自动刷新验证码")
                time.sleep(1.8)

        except Exception as loop_err:
            print(f"单次验证码流程异常：{loop_err}，等待页面自动刷新")
            time.sleep(1.8)
    if not captcha_pass:
        print(f"❌ 达到最大重试次数 {max_retry}，本轮验证码验证失败")
    return captcha_pass

# B站登录主流程
def bilibili_login(driver, wait):
    driver.get("https://www.bilibili.com")
    # 点击登录入口
    login_entry = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "header-login-entry")))
    login_entry.click()
    time.sleep(1)

    # 输入账号密码
    username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='请输入账号']")))
    username_input.send_keys("your_username")  # 替换为实际账号

    password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='请输入密码']")))
    password_input.send_keys("your_password")  # 替换为实际密码

    # 点击登录按钮，弹出验证码
    login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_primary")))
    login_btn.click()
    time.sleep(2.2)

    # 第一轮主验证码验证
    print("===== 第一轮验证码验证 =====")
    first_pass = run_captcha_flow(driver, wait, max_retry=8)
    if not first_pass:
        print("❌ 第一轮验证码验证失败，终止登录")
        return

    # =====================检测二次验证弹窗=====================
    print("\n===== 检测是否存在二次风险验证 =====")
    try:
        # 检测二次验证激活div
        risk_confirm = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "risk-input-after-active"))
        )
        risk_confirm.click()
        print("✅ 检测到二次风险验证，已点击激活验证码弹窗")
        time.sleep(1.5)

        # 复用通用验证码流程执行二次验证
        print("===== 第二轮（二次）验证码验证 =====")
        second_pass = run_captcha_flow(driver, wait, max_retry=8)
        if not second_pass:
            print("❌ 二次验证码验证失败，登录终止")
            return
        print("🎉 二次验证全部通过，登录成功！")

    except:
        # 未找到二次验证元素，直接登录完成
        print("✅ 未触发二次风险验证，登录流程全部完成")

    time.sleep(500)