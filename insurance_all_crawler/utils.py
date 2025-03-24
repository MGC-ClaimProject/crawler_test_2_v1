from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.common import TimeoutException
import time

# 로그인, 회원가입 선택 (btnHeaderJoin, btnHeaderLogin)
def click_a_tag_inside_li(driver, li_id):
    """
    li 태그의 id 값을 이용해 내부 a 태그를 클릭하는 함수

    :param driver: Selenium WebDriver 객체
    :param li_id: 클릭할 li 태그의 id 값 (예: "btnHeaderLogin")

    사용 예시:
    click_a_tag_inside_li(driver, "btnHeaderLogin")  # 로그인 버튼 클릭
    click_a_tag_inside_li(driver, "btnHeaderJoin")  # 회원가입 버튼 클릭

    """
    try:
        # 1️⃣ li 태그 찾기 (최대 10초 대기)
        li_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, li_id))
        )

        # 2️⃣ 내부 a 태그 찾기
        a_element = li_element.find_element(By.TAG_NAME, "a")

        # 3️⃣ JavaScript를 이용해 클릭 (더 안정적)
        driver.execute_script("arguments[0].click();", a_element)
        print(f"✅ '{li_id}' 내부의 a 태그 클릭 완료!")

    except TimeoutException:
        print(f"⚠️ '{li_id}' 요소를 찾을 수 없습니다.")
    except Exception as e:
        print(f"⚠️ '{li_id}' 클릭 중 오류 발생: {str(e)}")


# 다음, 확인, 동의 등등
# click_text_button(driver, "동의")
# 현재페이지에서 text 라는 글씨가 써져있는 a 태그 찾아서 클릭하기
def click_text_button(driver, text:str):
    try:
        # 1️⃣ 현재 페이지에서 "동의"라는 글자가 포함된 <a> 태그 찾기
        agree_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(),{text})]"))
        )

        # 2️⃣ JavaScript로 클릭 (더 안정적)
        driver.execute_script("arguments[0].click();", agree_button)
        print(f"✅ '{text}' 버튼 클릭 완료!")

    except TimeoutException:
        print(f"⚠️ '{text}' 버튼을 찾을 수 없습니다.")
    except Exception as e:
        print(f"⚠️ '{text}' 버튼 클릭 중 오류 발생: {str(e)}")


# a태그의 id를 이용해 링크를 클릭하는 함수
def click_link_a_id(driver, id_text:str):
    try:
        # 1. <a> 태그 (id="confirmTermBase") 찾기 (최대 10초 대기)
        agree_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, id_text))
        )

        # 2. JavaScript로 강제 클릭 (더 안정적)
        driver.execute_script("arguments[0].click();", agree_button)
        print(f"✅{id_text} 버튼 클릭 완료!")

    except TimeoutException as e:
        print(f"⚠️ 시간 초과: {str(e)}")
    except Exception as e:
        print(f"⚠️ '동의' 버튼 클릭 중 오류 발생: {str(e)}")


# 모달의 "동의" 버튼을 직접 클릭하는 함수 (id 기준)
def focus_check_and_close_modal(driver, agree_button_id, modal_checkbox_ids):
    try:
        # 1. "동의" 버튼이 로드될 때까지 대기
        agree_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.ID, agree_button_id))
        )

        # 2. 체크박스 체크 (있을 경우)
        for modal_checkbox_id in modal_checkbox_ids:
            checkbox_elements = driver.find_elements(By.ID, modal_checkbox_id)
            if checkbox_elements:
                checkbox = checkbox_elements[0]
                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    print(f"✅ 체크박스 클릭 완료: {modal_checkbox_id}")

        # 3. "동의" 버튼 클릭하여 모달 닫기
        driver.execute_script("arguments[0].click();", agree_button)
        print(f"✅ '{agree_button_id}' 버튼 클릭 완료!")

    except TimeoutException:
        print(f"⚠️ '동의' 버튼({agree_button_id})을 찾을 수 없습니다.")
    except Exception as e:
        print(f"⚠️ 모달 처리 중 오류 발생: {str(e)}")

# -------------

# checkbox의 id를 이용해서 체크박스를 체크하는 함수
def click_checkbox(driver, checkbox_id):
    try:
        # 1. 체크박스 요소 찾기 (최대 10초 대기)
        checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, checkbox_id))
        )

        # 2. 체크박스 현재 상태 확인
        if not checkbox.is_selected():  # 체크가 안 되어 있을 경우
            driver.execute_script("arguments[0].click();", checkbox)  # ✅ JavaScript로 강제 클릭
            print("✅ 체크박스 클릭 완료:", checkbox_id)
        else:
            print("⚠️ 이미 체크되어 있습니다.")

    except TimeoutException:
        print(f"⚠️ 체크박스를 찾을 수 없습니다. (ID:{checkbox_id})")
    except Exception as e:
        print(f"⚠️ 체크박스 클릭 중 오류 발생: {str(e)}")

# 이름, 생일등 정보 입력 필드 체우기
def fill_input_field(driver, field_id, value, field_name="입력 필드"):
    """
    특정 ID를 가진 input 필드에 값을 입력하는 함수.

    :param driver: Selenium WebDriver 인스턴스
    :param field_id: 입력할 input 태그의 ID
    :param value: 입력할 값
    :param field_name: 로그 출력용 필드명 (예: 이름, 생년월일, 전화번호 등)
    """
    try:
        input_field = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, field_id))
        )
        input_field.clear()  # 기존 값 삭제
        input_field.send_keys(value)  # 새 값 입력
        print(f"✅ {field_name} 입력 완료: {value}")

    except TimeoutException:
        print(f"⚠️ {field_name} 입력 필드를 찾을 수 없습니다. (ID: {field_id})")


# 성별 선택 radio 선택
def select_gender(driver, gender):
    """
    사용자의 성별을 선택하는 함수.

    :param driver: Selenium WebDriver 인스턴스
    :param gender: 선택할 성별 (예: "남" 또는 "여")
    """
    try:
        # 성별에 맞는 라디오 버튼 ID 매핑
        gender_radio_id = "rdoMale" if gender == "male" else "rdoFemale"

        # 해당 라디오 버튼이 나타날 때까지 대기
        gender_radio = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, gender_radio_id))
        )

        # 라디오 버튼 클릭 (이미 선택되지 않았다면)
        if not gender_radio.is_selected():
            driver.execute_script("arguments[0].click();", gender_radio)
            print(f"✅ 성별 선택 완료: {gender}")
        else:
            print(f"⚠️ 이미 선택된 성별: {gender}")

    except TimeoutException:
        print(f"⚠️ 성별 선택 필드를 찾을 수 없습니다. (ID: {gender_radio_id})")
    except Exception as e:
        print(f"⚠️ 성별 선택 중 오류 발생: {str(e)}")

# 인증방식 선택 (radio) - 무조건 본인명의 휴대폰인증으로 선택
def select_hp_certification(driver):
    """
    본인명의 휴대폰 인증 (rdoHp) 라디오 버튼을 강제 선택하는 함수.

    :param driver: Selenium WebDriver 인스턴스
    """
    try:
        # 라디오 버튼 요소 찾기
        radio_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "rdoHp"))
        )

        # 선택되지 않았다면 클릭
        if not radio_button.is_selected():
            driver.execute_script("arguments[0].click();", radio_button)
            print("✅ 본인명의 휴대폰 인증(rdoHp) 선택 완료!")
        else:
            print("⚠️ 이미 선택된 상태: 본인명의 휴대폰 인증")

    except TimeoutException:
        print("⚠️ 본인명의 휴대폰 인증(rdoHp) 필드를 찾을 수 없습니다.")
    except Exception as e:
        print(f"⚠️ 본인명의 휴대폰 인증 선택 중 오류 발생: {str(e)}")


