import time
from common.phone_pass import fill_and_submit_auth_form, validate_user_id, enter_password, enter_email_and_send_auth, \
    replace_password_fields, get_email_from_auth, enter_email_code, check_user_duplicate
from common.virtual_keyboard import enter_password_via_virtual_keyboard, extract_combined_key_mapping
from src.insurance_all_crawler import click_checkbox, fill_input_field, select_gender, select_hp_certification, click_a_tag_inside_li, \
    focus_check_and_close_modal, click_link_a_id
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# 🔄 간편 인증 절차 수행
def signup_crawler(driver, name, phone1, phone2, phone3, birth, gender, carrier, member_id, desired_id):
    try:
        # 1. 사이트 접속
        driver.get("https://www.credit4u.or.kr/")
        print(f"⚠️ 사이트 접속완료!: 내보험 다보여 ")

        # 2. 회원가입 링크 클릭
        click_a_tag_inside_li(driver, "btnHeaderJoin")
        time.sleep(1)

        # 3. 체크박스 클릭 후 모달 처리
        checkbox_ids = ["tearm_item_base", "tearm_item01"]
        agree_button_data = {
            "tearm_item_base": "confirmTermBase",  # 첫 번째 모달
            "tearm_item01": "confirmTerm02"  # 두 번째 모달
        }
        modal_checkbox_ids = ["popupChk1", "popupChk2"]

        for checkbox_id in checkbox_ids:
            click_checkbox(driver, checkbox_id)
            agree_button_id = agree_button_data.get(checkbox_id)
            if agree_button_id:
                focus_check_and_close_modal(driver, agree_button_id, modal_checkbox_ids)

        # 4. 사용자 정보 입력
        user_info = {
            "userName": name,  # 이름
            "userBirth": birth,  # 생년월일 (YYYYMMDD)
        }
        for field_id, value in user_info.items():
            fill_input_field(driver, field_id, value, field_name=field_id)

        # 성별 선택
        select_gender(driver, gender)

        # 인증방식 선택 - 본인명의 핸드폰 인증
        select_hp_certification(driver)

        original_window = driver.current_window_handle

        # 5. "다음" 버튼 클릭
        click_link_a_id(driver, "a_next")
        time.sleep(1)

        # 6. 새 창이 열릴 때까지 대기
        try:
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in driver.window_handles if w != original_window]

            if new_window:
                new_window_handle = new_window[0]
                print("✅ 새 창 감지됨!")

                # 새 창으로 전환
                driver.switch_to.window(new_window_handle)
                print("✅ 새 창으로 전환 완료!")

                # 7. 본인 인증 페이지 감지
                WebDriverWait(driver, 5).until(
                    lambda d: "safe.ok-name.co.kr/CommonSvl" in d.current_url or
                              "nice.checkplus.co.kr/cert/main/menu" in d.current_url
                )

                popup_url = driver.current_url

                if "safe.ok-name.co.kr/CommonSvl" in popup_url:
                    print(f"✅ KCB 인증 창 확인됨: {popup_url}")
                    time.sleep(0.5)

                    # 통신사 선택
                    carrier_ids = {
                        "SKT": "agency-skt",
                        "KT": "agency-kt",
                        "LGU+": "agency-lgu"
                    }
                    carrier_id = carrier_ids.get(carrier)

                    if carrier_id:
                        carrier_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, carrier_id))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", carrier_button)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", carrier_button)
                        print(f"✅ 통신사 선택 완료: {carrier}")
                        time.sleep(1)

                    # 전체 동의 체크박스 클릭
                    agree_checkbox = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "agree_all"))
                    )
                    if not agree_checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", agree_checkbox)
                        print("✅ '전체 동의하기' 체크 완료!")

                    # 인증 버튼 클릭
                    auth_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "btnPass"))
                    )
                    driver.execute_script("arguments[0].click();", auth_button)
                    print("✅ '인증하기' 버튼 클릭 완료!")
                    time.sleep(1)

                    # SMS 인증 창 클릭
                    click_link_a_id(driver, "sms_auth")
                    time.sleep(1)

                    # 8. 본인 인증 정보 입력
                    phone = phone1 + phone2 + phone3

                    # ✅ 보안문자 생성 및 인증
                    fill_and_submit_auth_form(driver, name, birth, gender, phone, member_id)

                    # ✅ 인증 창 닫힘 감지 후 부모 창으로 이동
                    print("⏳ 인증 창이 자동으로 닫힐 때까지 대기 중...")
                    while len(driver.window_handles) > 1:
                        time.sleep(0.5)  # 창이 닫힐 시간을 기다림

                    # ✅ 부모 창으로 전환
                    driver.switch_to.window(original_window)
                    print("✅ 부모 창으로 복귀 완료!")

                    # 이미 가입된 회원이라는 모달이 뜨면

                    if check_user_duplicate(driver):
                        # 이미 가입된 회원임을 알리고 추가 로직을 실행 (예: 로그인 페이지로 이동)
                        print("회원 중복 확인: 이미 가입된 회원입니다.")

                    else:
                        print("중복된 회원이 아닙니다.")


                        # ✅ 아이디(중복확인)
                        while True:
                            value = validate_user_id(driver, member_id, desired_id)
                            if value:
                                break

                        # ✅ 비밀번호 입력(초기값 자동입력)-
                        # 크롤러 코드 내에서 비밀번호 입력 전에 필드 교체
                        replace_password_fields(driver)  # 기존 필드 제거 후 새 필드 생성

                        # 이후에 기존 방식으로 비밀번호를 입력합니다.
                        enter_password(driver, "1qaz2wsx!!")


                        # ✅ 이메일 인증
                        enter_email_and_send_auth(driver, email_id="idblackcat", domain="naver.com")
                        while True:
                            email_text = get_email_from_auth(member_id)
                            value = enter_email_code(driver, email_text)
                            if value:
                                break

                        time.sleep(1)

                        # ✅ 확인 버튼 클릭
                        confirm_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "btnConfirm"))
                        )
                        driver.execute_script("arguments[0].click();", confirm_button)
                        print("✅ '확인' 버튼 클릭 완료!")
                        time.sleep(2)


                    # ✅ 로그인 로직으로 바로 가기
                    # ✅ 다음 로직 대기
                    result = wait_for_main(member_id)

                    return result



                elif "nice.checkplus.co.kr/cert/main/menu" in popup_url:
                    print(f"✅ NICE 인증 창 확인됨: {popup_url}")

            else:
                print("⚠️ 새 창이 감지되지 않음.")

        except TimeoutException:
            print("⚠️ 새 창이 10초 내 감지되지 않음.")

    except TimeoutException as e:
        print(f"⚠️ 시간 초과: {str(e)}")

    print("✅ 인증 완료!")


##############################################
# 로그인 크롤러 메인 함수
##############################################
def login_crawler(driver, member_id, nickname, password):
    try:
        driver.get("https://www.credit4u.or.kr/")
        print("⚠️ 사이트 접속완료!: 내보험 다보여")

        click_a_tag_inside_li(driver, "btnHeaderLogin")
        time.sleep(1)

        user_info = {"userId": nickname}
        for field_id, value in user_info.items():
            fill_input_field(driver, field_id, value, field_name=field_id)

        # 숫자는 OCR 결과를 사용하고, 소문자와 특수문자는 HTML상 DOM 순서대로 추출하여 매핑합니다.
        combined_mapping = extract_combined_key_mapping(driver)
        print("자동 추출된 최종 키 매핑:", combined_mapping)

        # 예시 비밀번호: "1qazwsxedc!!"
        enter_password_via_virtual_keyboard(driver, password, combined_mapping)

        wait_for_main(member_id)
    except TimeoutException as e:
        print(f"⚠️ 시간 초과: {str(e)}")
    print("✅ 인증 완료!")




def wait_for_main(member_id):
    """프론트엔드에서 사용자의 보안문자 입력을 기다리는 함수"""
    print("⏳ 메인창 대기중.... ")
    while True:
        continue


def run_crawler(member_id, name, phone1, phone2, phone3, birth, gender, carrier, desired_id):
    """ 크롤링 실행 """
    from common.crawler_base import setup_driver
    driver = setup_driver()
    try:
        # signup_crawler(driver, name, phone1, phone2, phone3, birth, gender, carrier, member_id, desired_id)
        result = login_crawler(driver,member_id,"idblackcat2","qazwsx")
        return result
    except Exception as e:
        print(f"⚠️ 크롤러 실행 중 예외 발생: {str(e)}")
        return None
    finally:
        driver.quit()