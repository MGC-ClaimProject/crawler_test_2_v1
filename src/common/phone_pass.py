from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time, os, json
from PIL import Image
from io import BytesIO

from config.base import Config

# -----------------------------------------
# 파일 및 API 설정
# -----------------------------------------
save_directory = Config.CAPTCHA_SAVE_DIR  # 원하는 저장 경로
BACKEND_BASE_URL = Config.BACKEND_BASE_URL
INSURANCES_BASE_URL = f"{BACKEND_BASE_URL}/v1/insurances"
CAPTCHA_URL = f"{INSURANCES_BASE_URL }/captcha/"


# 통합 인증 관련 파일 (JSON)
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
    AUTH_TEXT 파일에서 member_id에 해당하는 인증 데이터를 반환합니다.
    (데이터가 없으면 1초마다 재시도)
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
    """AUTH 데이터에서 길이가 6인 captcha_text를 반환합니다."""
    while True:
        auth_data = get_auth_data(member_id)
        captcha = auth_data.get("captcha_text", "")
        if len(captcha) == 6:
            return captcha

def get_sms_from_auth(member_id):
    """AUTH 데이터에서 길이가 6인 sms_text를 반환합니다."""
    while True:
        auth_data = get_auth_data(member_id)
        sms = auth_data.get("sms_text", "")
        if len(sms) == 6:
            return sms

def get_email_from_auth(member_id):
    """AUTH 데이터에서 길이가 6인 email_text를 반환합니다."""
    while True:
        auth_data = get_auth_data(member_id)
        email = auth_data.get("email_text", "")
        if len(email) == 6:
            return email

def save_auth_data(member_id, captcha_text="", sms_text="", email_text=""):
    """
    AUTH_TEXT 파일에 member_id의 인증 데이터를 저장합니다.
    형식:
    {
      "1": {
         "captcha_text": "123123",
         "sms_text": "321232",
         "email_text": "444444"
      }
    }
    """
    if os.path.exists(AUTH_TEXT):
        try:
            with open(AUTH_TEXT, "r", encoding="utf-8") as file:
                auth_data = json.load(file)
        except json.JSONDecodeError:
            auth_data = {}
    else:
        auth_data = {}

    auth_data[str(member_id)] = {
        "captcha_text": captcha_text,
        "sms_text": sms_text,
        "email_text": email_text
    }
    try:
        with open(AUTH_TEXT, "w", encoding="utf-8") as file:
            json.dump(auth_data, file, ensure_ascii=False, indent=4)
        print(f"✅ Auth data saved for member_id={member_id}: {auth_data[str(member_id)]}")
        return True
    except Exception as e:
        print(f"⚠️ Error saving auth data: {str(e)}")
        return False

# -----------------------------------------
# CAPTCHA 관련 함수
# -----------------------------------------
def capture_captcha(driver, member_id):
    """
    보안문자 이미지를 캡쳐하여 파일로 저장합니다.
    성공 시 status 200 반환, 실패 시 400 반환.
    """
    try:
        captcha_img = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "botDetectCaptcha_CaptchaImage"))
        )
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot))
        loc = captcha_img.location
        size = captcha_img.size
        captcha_image = image.crop((loc['x'], loc['y'], loc['x'] + size['width'], loc['y'] + size['height']))
        filename = f"captcha_{member_id}.png"
        save_path = os.path.join(save_directory, filename)
        captcha_image.save(save_path)
        print(f"✅ 보안문자 이미지 저장 완료: {save_path}")
        return {"filename": filename, "status": 200}
    except Exception as e:
        print(f"⚠️ CAPTCHA 이미지 저장 실패: {str(e)}")
        return {"status": 400}

def delete_captcha_file(member_id):
    """member_id에 해당하는 캡차 이미지 파일을 삭제합니다."""
    filename = f"captcha_{member_id}.png"
    file_path = os.path.join(save_directory, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ Captcha 파일 삭제 완료: {file_path}")
        except Exception as e:
            print(f"⚠️ Captcha 파일 삭제 중 오류 발생: {str(e)}")
    else:
        print(f"⚠️ 삭제할 Captcha 파일이 존재하지 않습니다: {file_path}")

# -----------------------------------------
# 입력 관련 함수
# -----------------------------------------
def enter_text(driver, element_id, value):
    """지정한 입력 필드에 값을 입력합니다."""
    element = safe_find_element(driver, By.ID, element_id)
    if element:
        element.clear()
        element.send_keys(value)
        print(f"✅ 입력 완료: {element_id} = {value}")
        time.sleep(0.5)
    else:
        print(f"❌ 입력 필드를 찾을 수 없음: {element_id}")

def enter_captcha_code(driver, captcha_text):
    """
    보안문자 입력 필드에 captcha_text 입력 후 확인 버튼 클릭.
    성공 시 True, 캡차 불일치 등 실패 시 False 반환.
    """
    try:
        captcha_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "captchaCode")))
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        print(f"✅ 보안문자 입력 완료: {captcha_text}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' 버튼 클릭 완료!")
        time.sleep(1)
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = Alert(driver)
            alert_text = alert.text
            print(f"⚠️ 알럿 발생: {alert_text}")
            alert.accept()
            print("✅ 알럿 확인 버튼 클릭 완료!")
            # 캡차 불일치 시 (실패 조건)
            if "그림문자가" in alert_text or "일치하지" in alert_text:
                print("🔄 캡차가 일치하지 않습니다.")
                return False
            else:
                return True
        except TimeoutException:
            print("✅ 모든 알럿 처리 완료.")
            return True
    except Exception as e:
        print(f"❌ 보안문자 입력 오류: {str(e)}")
        return False


def enter_sms_code(driver, sms_text):
    """
    SMS 인증 입력 필드에 sms_text 입력 후 확인 버튼을 클릭하는 함수.
    만약 모달창(즉, .layerPopupWrap .layer-pop.agreement가 display: block 상태)에서
    "인증 번호를 확인해 주세요." 메시지가 보이면, 해당 모달의 닫기 버튼을 클릭하고 False를 반환합니다.
    모달창이 완전히 닫혔다면(즉, invisibility가 확인되면) 성공으로 간주하여 True를 반환합니다.
    """
    try:
        # SMS 입력
        sms_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "usr_cert_no"))
        )
        sms_input.clear()
        sms_input.send_keys(sms_text)
        print(f"✅ SMS 입력 완료: {sms_text}")
        time.sleep(1)

        # 확인 버튼 클릭
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSubmit"))
        )
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' 버튼 클릭 완료!")
        time.sleep(1)

        # 3초 동안 모달창의 사라짐(invisibility)을 기다림.
        try:
            if WebDriverWait(driver, 3).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".layerPopupWrap .layer-pop.agreement"))
            ):
                print("✅ 팝업창이 완전히 닫혔습니다. SMS 인증 성공으로 간주.")
                return True
        except TimeoutException:
            try:
                # 모달 요소 찾기 (CSS 선택자는 페이지 구조에 맞게 조정)
                modal_dim = driver.find_element(By.CSS_SELECTOR, ".layerPopupWrap .dim")
                modal_popup = driver.find_element(By.CSS_SELECTOR, ".layerPopupWrap .layer-pop.agreement")
                if (modal_dim.value_of_css_property("display") == "block" and
                        modal_popup.value_of_css_property("display") == "block"):
                    # 모달 텍스트 확인
                    if "인증 번호를 확인해 주세요." in modal_popup.text:
                        print("❌ 인증번호 모달 확인됨: 인증 번호가 일치하지 않습니다.")
                        # 닫기 버튼 클릭
                        try:
                            close_button = modal_popup.find_element(By.CSS_SELECTOR, ".close")
                            driver.execute_script("arguments[0].click();", close_button)
                            print("✅ 모달 닫기 버튼 클릭 완료.")
                        except Exception as ce:
                            print(f"⚠️ 모달 닫기 버튼 클릭 오류: {ce}")
                        return False
            except Exception as e:
                # 모달이 더 이상 보이지 않으면 성공으로 간주
                print("✅ 모달이 닫힌 것으로 확인됨.")
            return False


    except Exception as e:
        print(f"❌ SMS 인증 입력 오류: {str(e)}")
        return False


def enter_email_code(driver, email_text):
    """
    이메일 인증 입력 필드에 email_text 입력 후 확인 버튼 클릭.
    성공 시 True, 실패 시 False를 반환합니다.
    """
    try:
        email_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtAuthNum")))
        email_input.clear()
        email_input.send_keys(email_text)
        print(f"✅ 이메일 입력 완료: {email_text}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnAuthConfirm")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '확인' 버튼 클릭 완료!")
        time.sleep(2)
        try:
            while True:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = Alert(driver)
                alert_text = alert.text
                print(f"⚠️ 알럿 발생: {alert_text}")
                alert.accept()
                print("✅ 알럿 확인 버튼 클릭 완료!")
                if "앞자리" in alert_text or "입력해주세요" in alert_text:
                    print("🔄 이메일 앞자리 오류 - 재입력 필요.")
                    return False
                if "인증이 완료되었습니다" in alert_text:
                    print("✅ 이메일 인증 완료.")
                    return True
        except TimeoutException:
            print("✅ 모든 알럿 처리 완료.")
            return True
    except Exception as e:
        print(f"❌ 이메일 인증 입력 오류: {str(e)}")
        return False

def enter_id_code(driver, user_id):
    """
    아이디 입력 필드에 user_id 입력 후 중복 확인 버튼 클릭.
    """
    try:
        id_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "userId")))
        id_input.clear()
        id_input.send_keys(user_id)
        print(f"✅ 아이디 입력 완료: {user_id}")
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnIdChk")))
        driver.execute_script("arguments[0].click();", confirm_button)
        print("✅ '중복 확인' 버튼 클릭 완료!")
        time.sleep(2)
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = Alert(driver)
            alert_text = alert.text
            print(f"⚠️ 알럿 발생: {alert_text}")
            alert.accept()
            print("✅ 알럿 확인 버튼 클릭 완료!")
            if "아이디" in alert_text or "다시 입력" in alert_text:
                print("🔄 아이디 다시 입력 필요.")
                return False
        except TimeoutException:
            print("✅ 알럿 없음 - 아이디 인증 성공!")
            return True
    except Exception as e:
        print(f"❌ 아이디 입력 오류: {str(e)}")
        return False
    return False

# -----------------------------------------
# 삭제 관련 함수 (AUTH_TEXT 초기화)
# -----------------------------------------
def delete_auth_field(member_id, field_name):
    """
    AUTH_TEXT 파일에서 member_id의 특정 필드(field_name)를 빈 문자열로 변경합니다.
    값이 이미 빈 문자열이면 작업하지 않습니다.
    """
    if os.path.exists(AUTH_TEXT):
        try:
            with open(AUTH_TEXT, "r+", encoding="utf-8") as file:
                data = json.load(file)
                key = str(member_id)
                if key in data and data[key].get(field_name, ""):
                    data[key][field_name] = ""
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, ensure_ascii=False, indent=4)
                    print(f"✅ {field_name} 삭제 완료 (member_id={member_id})")
        except Exception as e:
            print(f"⚠️ {field_name} 삭제 중 오류 발생: {str(e)}")

def delete_captcha_text(member_id):
    delete_auth_field(member_id, "captcha_text")

def delete_sms_text(member_id):
    delete_auth_field(member_id, "sms_text")

def delete_email_text(member_id):
    delete_auth_field(member_id, "email_text")

# -----------------------------------------
# 암호화 관련 함수
# -----------------------------------------
def disable_encryption(driver):
    """
    nppfs-1.13.0.js 스크립트를 제거하고 npkencrypt 속성을 삭제합니다.
    """
    try:
        driver.execute_script("""
            var script = document.querySelector('script[src*="nppfs-1.13.0.js"]');
            if (script) { script.parentNode.removeChild(script); }
        """)
        time.sleep(0.2)
        driver.execute_script("document.getElementById('edtPwd1').removeAttribute('npkencrypt');")
        driver.execute_script("document.getElementById('edtPwd2').removeAttribute('npkencrypt');")
        time.sleep(0.2)
        print("✅ 암호화 스크립트 및 npkencrypt 속성 제거 완료.")
    except Exception as e:
        print(f"⚠️ 암호화 스크립트 제거 오류: {str(e)}")

def replace_password_fields(driver):
    """
    기존 비밀번호 입력 필드를 삭제하고 새 필드로 교체합니다.
    """
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
    print("✅ 비밀번호 입력 필드 교체 완료.")

def enter_password(driver, password):
    """
    비밀번호 입력 필드에 password를 강제로 설정합니다.
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
        print(f"✅ 비밀번호 입력 완료: {password} (edtPwd1: {entered_pwd1}, edtPwd2: {entered_pwd2})")
        return True
    except TimeoutException:
        print("❌ 비밀번호 입력 필드를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 비밀번호 입력 오류: {str(e)}")
    return False

def enter_email_and_send_auth(driver, email_id="idblackcat", domain="naver.com"):
    """
    이메일 입력 및 인증번호 발송 버튼 클릭 함수.
    """
    try:
        email_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "edtMail1")))
        email_input.clear()
        email_input.send_keys(email_id)
        print(f"✅ 이메일 아이디 입력 완료: {email_id}")
        select_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "selMail2")))
        select_box.click()
        time.sleep(0.5)
        domain_option = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//select[@id='selMail2']/option[@value='naver.com']"))
        )
        domain_option.click()
        print("✅ 이메일 도메인 선택 완료: naver.com")
        time.sleep(1)
        send_auth_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "btnSendAuthNum")))
        send_auth_button.click()
        print("✅ '인증번호 발송' 버튼 클릭 완료!")
        try:
            while True:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = Alert(driver)
                alert_text = alert.text
                print(f"⚠️ 알럿 발생: {alert_text}")
                alert.accept()
                print("✅ 알럿 확인 버튼 클릭 완료!")
                if "앞자리" in alert_text or "입력해주세요" in alert_text:
                    print("🔄 이메일 앞자리 오류 - 재입력 필요.")
                    return False
                if "인증이 완료되었습니다" in alert_text:
                    print("✅ 이메일 인증 완료.")
                    return True
        except TimeoutException:
            print("✅ 모든 알럿 처리 완료.")
            return True
    except TimeoutException:
        print("❌ 이메일 입력 또는 버튼을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 이메일 입력 오류: {str(e)}")

# -----------------------------------------
# 고객 정보 입력 + 인증 진행 함수
# -----------------------------------------
def fill_and_submit_auth_form(driver, name, birth, gender, phone, member_id):
    """
    본인인증 폼을 채우고 캡차, SMS 인증을 순차적으로 진행하는 함수.
    캡차 실패 시 재시도, SMS 실패 시 모달 닫기 후 재시도(최대 3회)하며,
    각 인증 단계별 결과를 AUTH_TEXT 파일에 업데이트합니다.
    """
    try:
        while True:
            # 캡차 초기화
            delete_captcha_text(member_id)

            # 캡차 이미지 캡쳐
            captcha_data = capture_captcha(driver, member_id)
            if captcha_data:
                print("⚠️ 보안문자 캡처 성공.")

            # 생년월일, 성별 등 추가 입력
            birth_trimmed = birth[2:]
            print(f"🎯 변환된 생년월일: {birth_trimmed}")
            birth_year = int(birth[:4])
            ssn1 = "1" if (birth_year < 2000 and gender.lower() == "male") else \
                   "2" if (birth_year < 2000 and gender.lower() != "male") else \
                   "3" if (birth_year >= 2000 and gender.lower() == "male") else "4"
            print(f"🎯 변환된 성별 코드: {ssn1}")

            def enter_text_local(element_id, value):
                elem = safe_find_element(driver, By.ID, element_id)
                if elem:
                    elem.clear()
                    elem.send_keys(value)
                    print(f"✅ 입력 완료: {element_id} = {value}")
                    time.sleep(0.5)
                else:
                    print(f"❌ 입력 필드 {element_id} 미발견.")

            enter_text_local("nm", name)
            enter_text_local("ssn6", birth_trimmed)
            enter_text_local("ssn1", ssn1)
            enter_text_local("mbphn_no", phone)

            # 백엔드에서 캡차 텍스트 읽기
            captcha_text = get_captcha_from_auth(member_id)

            # 캡차 입력 및 인증 시도
            captcha_success = enter_captcha_code(driver, captcha_text)
            # 캡차 이미지 파일 삭제
            delete_captcha_file(member_id)
            # 결과 업데이트 (성공: True→200, 실패: False→400)
            update_result_field(member_id, "captcha_result", captcha_success)

            if captcha_success:
                print("✅ 캡차 인증 성공!")
                # SMS 인증 단계 진행 (최대 3회 시도)
                sms_attempts = 0
                while sms_attempts < 3:
                    sms_text = get_sms_from_auth(member_id)
                    print(f"🔄 SMS 인증 시도 {sms_attempts+1}: {sms_text}")
                    sms_success = enter_sms_code(driver, sms_text)
                    update_result_field(member_id, "sms_result", sms_success)
                    if sms_success:
                        print("✅ SMS 인증 성공!")
                        delete_captcha_file(member_id)
                        delete_sms_text(member_id)
                        return  # 모든 인증 성공 후 함수 종료
                    else:
                        sms_attempts += 1
                        delete_sms_text(member_id)
                        print(f"❌ SMS 인증 실패. 남은 시도: {3 - sms_attempts}")
                        # (필요 시 SMS 입력 필드 초기화 등 추가 처리)
                # SMS 인증 최대 횟수 초과 시 캡차부터 재시도
                print("⚠️ SMS 인증 실패, 캡차부터 재시도합니다.")
                continue
            else:
                print("❌ 캡차 인증 실패, 다시 캡차 시도합니다.")
                continue

    except TimeoutException:
        print("⚠️ 요소 미발견.")
    except Exception as e:
        print(f"⚠️ 실행 오류: {str(e)}")

def validate_user_id(driver, member_id, desired_id):
    """
    회원가입 아이디 중복 체크.
    중복이면 desired_id 뒤에 숫자를 붙여 사용 가능한 아이디를 반환, 실패하면 False.
    """
    counter = 0
    candidate_id = desired_id
    max_attempts = 10
    while counter < max_attempts:
        enter_id_code(driver, candidate_id)
        print(f"⏳ 후보 아이디 '{candidate_id}' 중복 확인 대기...")
        try:
            WebDriverWait(driver, 5).until(
                lambda d: (safe_find_element(d, By.ID, "popInvalidId") and
                           safe_find_element(d, By.ID, "popInvalidId").value_of_css_property("display") == "block") or
                          (safe_find_element(d, By.ID, "popValidId") and
                           safe_find_element(d, By.ID, "popValidId").value_of_css_property("display") == "block")
            )
        except TimeoutException:
            print("⚠️ 중복 확인 시간 초과.")
            return False
        invalid_div = safe_find_element(driver, By.ID, "popInvalidId")
        if invalid_div and invalid_div.value_of_css_property("display") == "block":
            print(f"❌ 후보 아이디 '{candidate_id}' 중복됨.")
            confirm_button = safe_find_element(driver, By.CLASS_NAME, "a_pop_confirm")
            if confirm_button:
                driver.execute_script("arguments[0].click();", confirm_button)
                print("✅ 모달 닫기 버튼 클릭.")
            counter += 1
            candidate_id = desired_id + str(counter)
            print(f"🔄 새로운 후보 아이디: {candidate_id}")
        else:
            valid_div = safe_find_element(driver, By.ID, "popValidId")
            if valid_div and valid_div.value_of_css_property("display") == "block":
                print(f"✅ 후보 아이디 '{candidate_id}' 사용 가능!")
                use_id_button = safe_find_element(driver, By.CLASS_NAME, "btn_id_confirm")
                if use_id_button:
                    driver.execute_script("arguments[0].click();", use_id_button)
                    print("✅ '아이디 사용' 버튼 클릭 완료!")
                return candidate_id
    print("⚠️ 최대 시도 횟수 초과.")
    return False

def update_auth_field(member_id, field_name, new_value):
    """
    AUTH_TEXT 파일에서 member_id의 특정 필드를 new_value로 업데이트합니다.
    """
    if os.path.exists(AUTH_TEXT):
        try:
            with open(AUTH_TEXT, "r+", encoding="utf-8") as file:
                data = json.load(file)
                key = str(member_id)
                if key in data:
                    data[key][field_name] = new_value
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, ensure_ascii=False, indent=4)
                    print(f"✅ {field_name} 업데이트 완료 (member_id={member_id}): {new_value}")
                else:
                    print(f"⚠️ member_id {member_id} 데이터 없음.")
        except Exception as e:
            print(f"⚠️ {field_name} 업데이트 오류: {str(e)}")
    else:
        print("⚠️ AUTH_TEXT 파일 없음.")

def update_result_field(member_id, field_name, success=True):
    """
    AUTH_TEXT 파일에서 member_id의 field_name을
    성공 시 200, 실패 시 400으로 업데이트합니다.
    """
    result_value = 200 if success else 400
    update_auth_field(member_id, field_name, int(result_value))

# 이미 가입된 회원임을 알리는 모달을 찾아내는 함수
def check_user_duplicate(driver):
    try:
        pop_element = driver.find_element(By.ID, "pop_userDupl")
        if pop_element.value_of_css_property("display") == "block":
            print("이미 가입된 회원입니다.")
            return True
    except NoSuchElementException:
        # pop_userDupl 요소가 없으면 중복이 아님
        pass
    return False

