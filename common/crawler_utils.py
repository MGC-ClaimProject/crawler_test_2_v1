import os
import time
import json
from config.base import Config
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException



# -----------------------------------------
# 파일 및 API 설정
# -----------------------------------------
save_directory = Config.CAPTCHA_SAVE_DIR  # 원하는 저장 경로
BACKEND_BASE_URL = Config.BACKEND_BASE_URL
INSURANCES_BASE_URL = f"{BACKEND_BASE_URL}/v1/insurances"
CAPTCHA_URL = f"{INSURANCES_BASE_URL }/captcha/"

# 통합 인증 관련 파일
AUTH_TEXT = os.path.join(save_directory, "auth_text.json")

os.makedirs(save_directory, exist_ok=True)

# -----------------------------------------
# 공통 유틸리티 함수
# -----------------------------------------
def safe_find_element(driver, by, value, timeout=10):
    """요소를 최대 3회 재시도하여 찾습니다."""
    for _ in range(3):
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        except (StaleElementReferenceException, TimeoutException):
            time.sleep(1)
    return None

# -----------------------------------------
# 통합 인증 데이터 관련 함수
# -----------------------------------------
def get_auth_data(member_id):
    """
    통합 인증 JSON 파일(AUTH_TEXT)에서 member_id에 해당하는 인증 데이터를 기다리며 반환합니다.
    """
    print(f"⏳ member_id={member_id} auth data waiting... ({AUTH_TEXT})")
    time.sleep(3)
    while True:
        try:
            with open(AUTH_TEXT, "r", encoding="utf-8") as file:
                data = json.load(file)
            if str(member_id) in data:
                auth_data = data[str(member_id)]
                print(f"✅ Received auth data for member_id={member_id}: {auth_data}")
                return auth_data
        except (FileNotFoundError, json.JSONDecodeError):
            print("⚠️ AUTH JSON file not found or invalid.")
        print("⌛ Retrying in 1 sec...")
        time.sleep(1)

def get_captcha_from_auth(member_id):
    """통합 데이터에서 captcha_text 반환 (길이가 6이어야 함)"""
    auth_data = get_auth_data(member_id)
    captcha = auth_data.get("captcha_text", "")
    return captcha

def get_sms_from_auth(member_id):
    """통합 데이터에서 sms_text 반환 (길이가 6이어야 함)"""
    auth_data = get_auth_data(member_id)
    sms = auth_data.get("sms_text", "")
    return sms

def get_email_from_auth(member_id):
    """통합 데이터에서 email_text 반환 (길이가 6이어야 함)"""
    auth_data = get_auth_data(member_id)
    email = auth_data.get("email_text", "")
    return email

def save_auth_data(member_id, captcha_text="", sms_text="", email_text=""):
    """
    통합 인증 JSON 파일에 member_id에 해당하는 데이터를 저장합니다.
    만약 전달된 값이 빈 문자열이면, 해당 값은 기존 데이터에서 변경하지 않습니다.
    저장 형태:
    {
      "1": {
         "captcha_text": "123123",
         "sms_text": "321232",
         "email_text": "444444"
      }
    }
    """
    # 기존 JSON 파일 읽기 (없으면 빈 딕셔너리)
    if os.path.exists(AUTH_TEXT):
        with open(AUTH_TEXT, "r", encoding="utf-8") as file:
            try:
                auth_data = json.load(file)
            except json.JSONDecodeError:
                auth_data = {}
    else:
        auth_data = {}

    member_key = str(member_id)
    # 기존 데이터가 있으면 병합, 없으면 새로 생성
    if member_key in auth_data:
        existing = auth_data[member_key]
        # 전달된 값이 빈 문자열이 아니라면 업데이트, 빈 문자열이면 기존값 유지
        if captcha_text:
            existing["captcha_text"] = captcha_text
        if sms_text:
            existing["sms_text"] = sms_text
        if email_text:
            existing["email_text"] = email_text
        auth_data[member_key] = existing
    else:
        auth_data[member_key] = {
            "captcha_text": captcha_text,
            "sms_text": sms_text,
            "email_text": email_text
        }

    try:
        with open(AUTH_TEXT, "w", encoding="utf-8") as file:
            json.dump(auth_data, file, ensure_ascii=False, indent=4)
        print(f"✅ Auth data saved for member_id={member_id}: {auth_data[member_key]}")
        return True
    except Exception as e:
        print(f"⚠️ Error saving auth data: {str(e)}")
        return False

# ----------------------------
# CAPTCHA 관련 함수
# ----------------------------
def capture_captcha(driver, member_id):
    """CAPTCHA 이미지를 캡처하여 지정된 경로에 저장합니다."""
    try:
        captcha_img = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "botDetectCaptcha_CaptchaImage")))
        screenshot = driver.get_screenshot_as_png()
        from PIL import Image
        from io import BytesIO
        image = Image.open(BytesIO(screenshot))
        loc = captcha_img.location
        size = captcha_img.size
        captcha_image = image.crop((loc['x'], loc['y'], loc['x'] + size['width'], loc['y'] + size['height']))
        filename = f"captcha_{member_id}.png"
        save_path = os.path.join(save_directory, filename)
        captcha_image.save(save_path)
        print(f"✅ Captcha image saved: {save_path}")
        return {"filename": filename, "status": 202}
    except Exception as e:
        print(f"⚠️ Captcha image saving failed: {str(e)}")
        return None

def monitor_captcha(driver, member_id):
    """백그라운드에서 주기적으로 CAPTCHA 이미지를 저장합니다."""
    print("🔄 Starting CAPTCHA monitor...")
    while True:
        success = capture_captcha(driver, member_id)
        if success:
            print("✅ Captcha refreshed.")
        else:
            print("⚠️ Captcha refresh failed.")
        time.sleep(2)

# ----------------------------
# 입력 관련 함수
# ----------------------------
def enter_text(driver, element_id, value):
    """지정된 입력 필드(element_id)에 value를 입력합니다."""
    element = safe_find_element(driver, By.ID, element_id)
    if element:
        element.clear()
        element.send_keys(value)
        print(f"✅ Entered text: {element_id} = {value}")
        time.sleep(0.5)
    else:
        print(f"❌ Input field not found: {element_id}")

def enter_captcha_code(driver, captcha_text):
    """CAPTCHA 입력 필드에 captcha_text를 입력하고 확인 버튼을 클릭합니다."""
    try:
        captcha_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "captchaCode")))
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        print(f"✅ Entered CAPTCHA: {captcha_text}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' button clicked.")
        time.sleep(2)
        try:
            while True:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = Alert(driver)
                alert_text = alert.text
                print(f"⚠️ Alert: {alert_text}")
                alert.accept()
                print("✅ Alert accepted.")
                if "앞자리" in alert_text or "입력해주세요" in alert_text:
                    print("🔄 Please re-enter the email prefix.")
                    return False
                if "인증이 완료되었습니다" in alert_text:
                    print("✅ Verification complete.")
                    return True
        except TimeoutException:
            print("✅ No more alerts; CAPTCHA verified.")
            return True
    except Exception as e:
        print(f"❌ Error entering CAPTCHA: {str(e)}")
        return False

def enter_sms_code(driver, sms_text):
    """SMS 인증 코드 입력 필드에 sms_text를 입력하고 확인 버튼을 클릭합니다."""
    try:
        sms_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "usr_cert_no")))
        sms_input.clear()
        sms_input.send_keys(sms_text)
        print(f"✅ Entered SMS code: {sms_text}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' button for SMS clicked.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Error entering SMS code: {str(e)}")
        return False

def enter_email_code(driver, email_text):
    """이메일 인증 코드 입력 필드에 email_text를 입력하고 확인 버튼을 클릭합니다."""
    try:
        email_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtAuthNum")))
        email_input.clear()
        email_input.send_keys(email_text)
        print(f"✅ Entered email verification code: {email_text}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnAuthConfirm")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' button for email clicked.")
        time.sleep(2)
        try:
            while True:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = Alert(driver)
                alert_text = alert.text
                print(f"⚠️ Alert: {alert_text}")
                alert.accept()
                print("✅ Alert accepted.")
                if "앞자리" in alert_text or "입력해주세요" in alert_text:
                    print("🔄 Please re-enter the email prefix.")
                    return False
                if "인증이 완료되었습니다" in alert_text:
                    print("✅ Email verification complete.")
                    return True
        except TimeoutException:
            print("✅ All alerts processed; email verified.")
            return True
    except Exception as e:
        print(f"❌ Error entering email verification code: {str(e)}")
        return False

def enter_id_code(driver, user_id):
    """아이디 입력 필드에 user_id를 입력하고, 중복 확인 버튼을 클릭합니다."""
    try:
        id_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "userId")))
        id_input.clear()
        id_input.send_keys(user_id)
        print(f"✅ Entered user ID: {user_id}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnIdChk")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '중복 확인' button clicked.")
        time.sleep(2)
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = Alert(driver)
            alert_text = alert.text
            print(f"⚠️ Alert for ID: {alert_text}")
            alert.accept()
            print("✅ Alert accepted.")
            if "아이디" in alert_text or "다시 입력" in alert_text:
                print("🔄 Please re-enter the user ID.")
                return False
        except TimeoutException:
            print("✅ No alert; ID verified.")
            return True
    except Exception as e:
        print(f"❌ Error entering user ID: {str(e)}")
        return False
    return False

# ----------------------------
# 암호화/보안 관련 함수
# ----------------------------
def disable_encryption(driver):
    """암호화 스크립트(nppfs-1.13.0.js) 제거 및 npkencrypt 속성 삭제"""
    try:
        driver.execute_script("""
            var script = document.querySelector('script[src*="nppfs-1.13.0.js"]');
            if(script) { script.parentNode.removeChild(script); }
        """)
        time.sleep(0.2)
        driver.execute_script("document.getElementById('edtPwd1').removeAttribute('npkencrypt');")
        driver.execute_script("document.getElementById('edtPwd2').removeAttribute('npkencrypt');")
        time.sleep(0.2)
        print("✅ Encryption script and npkencrypt attribute removed.")
    except Exception as e:
        print(f"⚠️ Error disabling encryption: {str(e)}")

def replace_password_fields(driver):
    """기존 비밀번호 필드를 제거하고 새 <input type='password'> 요소로 교체합니다."""
    script = """
    var oldPwd1 = document.getElementById('edtPwd1');
    if(oldPwd1){
         var newPwd1 = document.createElement('input');
         newPwd1.type = 'password';
         newPwd1.id = 'edtPwd1';
         newPwd1.name = oldPwd1.getAttribute('name') || 'edtPwd1';
         newPwd1.placeholder = oldPwd1.getAttribute('placeholder') || '';
         newPwd1.className = oldPwd1.className || '';
         oldPwd1.parentNode.replaceChild(newPwd1, oldPwd1);
    }
    var oldPwd2 = document.getElementById('edtPwd2');
    if(oldPwd2){
         var newPwd2 = document.createElement('input');
         newPwd2.type = 'password';
         newPwd2.id = 'edtPwd2';
         newPwd2.name = oldPwd2.getAttribute('name') || 'edtPwd2';
         newPwd2.placeholder = oldPwd2.getAttribute('placeholder') || '';
         newPwd2.className = oldPwd2.className || '';
         oldPwd2.parentNode.replaceChild(newPwd2, oldPwd2);
    }
    """
    driver.execute_script(script)
    time.sleep(0.5)
    print("✅ Password fields replaced.")

def enter_password(driver, password):
    """
    암호화 스크립트를 제거한 후, 비밀번호 필드에 password를 강제 입력합니다.
    """
    try:
        password = str(password)
        disable_encryption(driver)
        pwd1 = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtPwd1")))
        pwd2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtPwd2")))
        driver.execute_script("arguments[0].value = '';", pwd1)
        driver.execute_script("arguments[0].value = '';", pwd2)
        time.sleep(0.2)
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, pwd1, password)
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, pwd2, password)
        entered_pwd1 = driver.execute_script("return document.getElementById('edtPwd1').value;")
        entered_pwd2 = driver.execute_script("return document.getElementById('edtPwd2').value;")
        print(f"✅ Password set: edtPwd1 = {password}")
        print(f"✅ Password set: edtPwd2 = {password}")
        print(f"🔍 Entered password1: {entered_pwd1}")
        print(f"🔍 Entered password2: {entered_pwd2}")
        return True
    except TimeoutException:
        print("❌ Password fields not found.")
    except Exception as e:
        print(f"❌ Error setting password: {str(e)}")
    return False

def enter_email_and_send_auth(driver, email_id="idblackcat", domain="naver.com"):
    """
    이메일 입력 필드에 'idblackcat@naver.com'을 입력하고, 인증번호 발송 버튼을 클릭합니다.
    """
    try:
        email_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtMail1")))
        email_input.clear()
        email_input.send_keys(email_id)
        print(f"✅ Email ID entered: {email_id}")
        select_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "selMail2")))
        select_box.click()
        time.sleep(0.5)
        domain_option = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//select[@id='selMail2']/option[@value='naver.com']"))
        )
        domain_option.click()
        print("✅ Email domain selected: naver.com")
        time.sleep(1)
        send_auth_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "btnSendAuthNum")))
        send_auth_button.click()
        print("✅ '인증번호 발송' button clicked!")
        try:
            while True:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = Alert(driver)
                alert_text = alert.text
                print(f"⚠️ Alert: {alert_text}")
                alert.accept()
                print("✅ Alert accepted!")
                if "앞자리" in alert_text or "입력해주세요" in alert_text:
                    print("🔄 Please re-enter the email prefix.")
                    return False
                if "인증이 완료되었습니다" in alert_text:
                    print("✅ Email verification complete.")
                    return True
        except TimeoutException:
            print("✅ All alerts processed; email verified.")
            return True
    except TimeoutException:
        print("❌ Email input or button not found.")
    except Exception as e:
        print(f"❌ Error in email input: {str(e)}")

# ----------------------------
# End of crawler_utils.py
