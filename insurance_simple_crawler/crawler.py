#crawler.py

import os
import time
import json
from selenium import webdriver  # 🔄 순수 selenium 사용
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service  # 🔄 추가

#
# SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub")
# CHROME_BINARY_PATH = "/usr/bin/chromium"
# CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
#
#
# def setup_driver():
#     # 📌 chromedriver 자동 설치 및 경로 반환
#     driver_path = chromedriver_autoinstaller.install()  # 🔄 설치 후 경로 반환
#
#     options = webdriver.ChromeOptions()
#     options.headless = True  # 🔄 도커에서는 반드시 headless 모드로!
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("--no-proxy-server")
#     options.add_argument("--ignore-certificate-errors")
#     options.add_argument("--disable-software-rasterizer")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
#
#     # 🔄 Service 객체로 드라이버 경로 지정 (자동 설치된 경로 사용)
#     service = Service(executable_path=driver_path)  # 🔄 변경된 부분
#
#     # 🔄 순수 Selenium으로 Chrome 드라이버 실행
#     driver = webdriver.Chrome(
#         service=service,  # 🔄 변경된 부분
#         options=options
#     )
#
#     # 🔄 DNS 캐시 초기화
#     driver.get("chrome://net-internals/#dns")
#     driver.execute_script("chrome.send('clearHostResolverCache');")
#
#     return driver


# ✅ 버튼 클릭 유틸
def click_button(driver, by, value, description):
    try:
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].click();", button)
        print(f"✅ {description} 클릭 완료")
        return True
    except Exception as e:
        print(f"⚠️ {description} 클릭 실패: {str(e)}")
        return False


# ✅ 카카오 인증 선택
def select_kakao_auth(driver):
    try:
        kakao_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//img[contains(@alt, 'KAKAO(카카오)')]"))
        )
        kakao_li = kakao_img.find_element(By.XPATH, "./ancestor::li")

        # ✅ 1. 스크롤로 위치 조정
        driver.execute_script("arguments[0].scrollIntoView(true);", kakao_li)
        print("✅ 스크롤 완료")

        # ✅ 2. 강제 클릭 (JavaScript)
        driver.execute_script("arguments[0].click();", kakao_li)
        print("✅ 카카오 인증 강제 클릭 완료")

    except Exception as e:
        print(f"⚠️ 카카오 인증 선택 실패: {str(e)}")


# ✅ 2차 - 간편인증 팝업창용 사용자 정보 입력 유틸 (8자리 생년월일 적용)
def input_user_info(driver, name, birth, phone1, phone2, phone3):
    phone = f"{phone1}{phone2}{phone3}"
    try:
        # ✅ 이름 입력
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-id='oacx_name']"))
        )
        name_input.clear()
        name_input.send_keys(name)
        time.sleep(.5)

        # ✅ 8자리 생년월일 입력 (YYYYMMDD 형식)
        birth_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-id='oacx_birth']"))
        )
        birth_input.clear()
        if len(birth) == 6:  # 만약 6자리라면 8자리로 변환 (예: 900101 -> 19900101)
            birth = f"19{birth}" if int(birth[:2]) > 30 else f"20{birth}"
        birth_input.send_keys(birth)
        time.sleep(.5)

        # ✅ 전화번호 입력 (연속적으로 입력)
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-id='oacx_phone2']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone)
        time.sleep(.5)

        print(f"✅ 본인 인증 정보 입력 완료: 이름={name}, 생년월일={birth}, 전화번호={phone}")

    except TimeoutException:
        print("⚠️ 본인 인증 입력 필드를 찾을 수 없습니다.")
    except Exception as e:
        print(f"⚠️ 본인 인증 정보 입력 중 오류 발생: {str(e)}")


# 📌 메인 페이지로 이동
def navigate_to_main_page(driver):
    try:
        # 현재 페이지 HTML 가져오기 및 텍스트 출력
        page_source = driver.page_source
        print("🔄 현재 페이지 텍스트:")
        print(page_source[:2000])  # 최대 2000자까지 출력

    except Exception as e:
        print(f"⚠️ 메인 페이지 이동 중 예외 발생: {str(e)}")



# ✅ 1차 - 본인 인증 정보 입력 유틸
def input_user_info_basic(driver, name, phone1, phone2, phone3, birth, id_back):
    try:
        print("📌 1차 본인 인증 정보 입력 시작...")

        # ✅ 이름 입력
        name_input = driver.find_element(By.ID, "applcntNm")
        driver.execute_script("arguments[0].click();", name_input)
        name_input.send_keys(name)

        # ✅ 전화번호 입력
        driver.find_element(By.ID, "telno1").clear()
        driver.find_element(By.ID, "telno1").send_keys(phone1)

        driver.find_element(By.ID, "telno2").clear()
        driver.find_element(By.ID, "telno2").send_keys(phone2)

        driver.find_element(By.ID, "telno3").clear()
        driver.find_element(By.ID, "telno3").send_keys(phone3)

        # ✅ 주민등록번호 입력
        driver.find_element(By.ID, "ssn1").clear()
        driver.find_element(By.ID, "ssn1").send_keys(birth)

        driver.find_element(By.ID, "ssn2").clear()
        driver.find_element(By.ID, "ssn2").send_keys(id_back)

        print(f"📌 입력된 본인 인증 정보: 이름={name}, 전화번호={phone1}-{phone2}-{phone3}, 생년월일={birth}, 주민등록번호 뒷자리={id_back}")

    except Exception as e:
        print(f"⚠️ 본인 인증 정보 입력 중 오류 발생: {str(e)}")



def agree_checkbox(driver):
    # ✅ 체크박스 자동 선택
    agree_checkboxes = ["checkAgree1_Y", "checkAgree2_Y", "checkAgree3_Y", "checkAgree4_Y", "checkAgree5_Y",
                        "checkAgree6_Y"]
    for checkbox_id in agree_checkboxes:
        checkbox = driver.find_element(By.ID, checkbox_id)
        if not checkbox.is_selected():
            checkbox.click()
def All_checkbox(driver):
    # ✅ 모든 체크박스 선택
    checkboxes = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='checkbox']"))
    )
    for checkbox in checkboxes:
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].scrollIntoView();", checkbox)
            driver.execute_script("arguments[0].click();", checkbox)
            print(f"✅ 체크박스 선택 완료: {checkbox.get_attribute('name') or checkbox.get_attribute('id')}")
def auth_request_button(driver):
    try:
        auth_request_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//button[contains(text(),'인증 요청')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", auth_request_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", auth_request_button)
        print("✅ '인증 요청' 버튼 강제 클릭 완료")
    except TimeoutException:
        print("⚠️ '인증 요청' 버튼을 찾을 수 없습니다.")
        return

