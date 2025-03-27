from flask import jsonify  # 🔄 Flask 추가
import time
# import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException  # 🔄 추가

from common.utils import update_task_status
from config.base import Config
from insurance_simple_crawler.data_extractor import save_crawler_data  # 🔄 추가된 부분
from insurance_simple_crawler.crawler import (
    click_button,
    select_kakao_auth,
    input_user_info,
    input_user_info_basic,
    agree_checkbox,
    All_checkbox,
    auth_request_button,
)


SELENIUM_REMOTE_URL=Config.SELENIUM_REMOTE_URL
CHROME_BINARY_PATH = Config.CHROME_BINARY_PATH
CHROMEDRIVER_PATH = Config.CHROMEDRIVER_PATH
INSURANCE_SIMPLE_SITE = Config.INSURANCE_SIMPLE_SITE

# 🔄 알럿 확인 및 닫기 함수
def handle_alert(driver):
    try:
        # 알럿이 뜰 때까지 최대 2초 대기
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to.alert

        # 알럿 텍스트 읽기
        alert_text = alert.text
        print(f"⚠️ 알럿 감지: {alert_text}")

        # 알럿 텍스트를 읽은 후 충분한 대기
        time.sleep(1)

        # 전처리: 개행 및 여분의 공백 제거
        cleaned_text = " ".join(alert_text.split())

        # "재신청" 포함 여부에 따라 처리
        if "재신청" in cleaned_text:
            print("✅ '재신청'이 포함된 알럿 감지! '확인' 클릭 후 30초 대기 중...")
            alert.accept()  # "확인" 클릭
            time.sleep(30)  # 30초 대기
        else:
            print("✅ 일반 알럿 감지! '확인' 클릭 후 즉시 진행")
            alert.accept()  # "확인" 클릭

        print("✅ 알럿 처리 완료.")

    except NoAlertPresentException:
        print("⚠️ 알럿이 존재하지 않습니다.")
    except TimeoutException:
        print("⚠️ 알럿 대기 시간 초과.")
    except UnexpectedAlertPresentException:
        print("⚠️ 알럿이 예기치 않게 발생했지만 처리 진행")
        driver.switch_to.alert.accept()  # 강제 확인 클릭
    except Exception as e:
        print(f"⚠️ 알럿 처리 중 예외 발생: {str(e)}")

# 🔄 미회신 보험사 팝업 확인 및 닫기 함수
def close_active_popup(driver):
    try:
        # display: none; 이 아닌 팝업 찾기
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[contains(@class, "popup_layer") and contains(@class, "rply_popup") and not(contains(@style, "display: none"))]'
            ))
        )

        # 해당 팝업 안에 있는 닫기 버튼 클릭
        close_button = popup.find_element(By.CSS_SELECTOR, 'button.btn_close_popup.btn_close_rply')
        close_button.click()
        print("✅ 팝업 닫기 버튼 클릭 완료")

    except Exception as e:
        print(f"❌ 팝업 닫기 실패: {e}")


# 🔄 간편 인증 절차 수행
def perform_auth(driver, task_id, name, phone1, phone2, phone3, birth, id_back):
    try:
        # 1. 사이트 접속
        driver.get(INSURANCE_SIMPLE_SITE)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//p[contains(text(), '내 보험 찾아줌 조회하기')]"))
        )

        # 2. "내 보험 찾아줌 조회하기" 클릭
        click_button(driver, By.XPATH, "//p[contains(text(), '내 보험 찾아줌 조회하기')]", "내 보험 찾아줌 조회하기")
        time.sleep(2)

        # 3. 동의 체크 및 다음 클릭
        agree_checkbox(driver)
        time.sleep(1)
        click_button(driver, By.CLASS_NAME, "btn_next_go", "동의하기")
        time.sleep(2)

        # 4. 1차 인증 정보 입력
        input_user_info_basic(driver, name, phone1, phone2, phone3, birth, id_back)

        # 5. 간편 인증 클릭
        click_button(driver, By.ID, "simple", "간편 인증")
        time.sleep(2)

        # 6. 팝업 전환
        main_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])

        # 7. 카카오 간편인증 선택
        select_kakao_auth(driver)

        # 8. 2차 개인정보 입력
        input_user_info(driver, name, birth, phone1, phone2, phone3)
        time.sleep(1)

        # 9. 모든 체크박스 체크
        All_checkbox(driver)
        time.sleep(1)

        # 10. 인증 요청 클릭
        auth_request_button(driver)

        # 상태 업데이트 - # 인증 문자,톡 발송 완료, 사용자 인증 대기 중
        status = "waiting_for_verification"
        update_task_status(task_id, status, None)


        # 11. 인증 완료 버튼 클릭 (2분간 -5초마다 24번)
        attempt = 0
        max_attempts = 24
        while attempt < max_attempts:
            try:
                # 🔄 '인증 완료' 버튼 탐지 및 클릭
                auth_complete_button = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//button[contains(text(),'인증 완료')]"))
                )
                if auth_complete_button is not None and auth_complete_button.is_enabled() and auth_complete_button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView();", auth_complete_button)
                    driver.execute_script("arguments[0].click();", auth_complete_button)
                    print(f"✅ [시도 {attempt + 1}/{max_attempts}] '인증 완료' 버튼 클릭 완료")
                else:
                    print(f"⚠️ [시도 {attempt + 1}/{max_attempts}] '인증 완료' 버튼이 비활성화 상태입니다.")
            except TimeoutException:
                print(f"⚠️ [시도 {attempt + 1}/{max_attempts}] '인증 완료' 버튼을 찾을 수 없습니다.")

            time.sleep(1)
            # 🔄 팝업 닫힘 확인
            if len(driver.window_handles) == 1:
                print("✅ 팝업이 닫혔습니다. 부모 화면으로 이동합니다.")
                driver.switch_to.window(main_window)
                time.sleep(1)
                update_task_status(task_id, "auth_pass", None)
                # 재신청 알렛 확인
                handle_alert(driver)
                # 미회신 보험사 팝업 확인
                close_active_popup(driver)

                break  # 🔄 반복 중단

            # 🔄 '확인' 버튼 찾기 및 클릭 (팝업이 안 닫혔다면)
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//button[contains(text(),'확인')]"))
                )
                if confirm_button is not None and confirm_button.is_enabled() and confirm_button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView();", confirm_button)
                    driver.execute_script("arguments[0].click();", confirm_button)
                    print("✅ '확인' 버튼 클릭 완료")
                else:
                    print("⚠️ '확인' 버튼이 비활성화 상태입니다.")
            except TimeoutException:
                print("⚠️ '확인' 버튼을 찾을 수 없습니다.")
            except Exception as e:
                print(f"⚠️ '확인' 버튼 클릭 중 예외 발생: {str(e)}")

            # 5초 대기 후 재시도
            time.sleep(4)
            attempt += 1


    except TimeoutException as e:
        print(f"⚠️ 시간 초과: {str(e)}")
        return jsonify({"status": "error", "message": "시간 초과중 에러 발생 "}), 408

    result_json = {"status": "success", "message": "인증 절차 모두 성공!! - 데이터 저장 준비중..."}
    print("✅ 인증 완료!")
    return jsonify(result_json), 200


# 🔄 메인 실행 함수
def run_crawler(task_id, member_id, name, phone1, phone2, phone3, birth, id_back, carrier):
    """
    크롤러 실행 함수 – 백그라운드 스레드에서 Flask 응답을 반환할 때
    반드시 애플리케이션 컨텍스트 내에서 jsonify를 호출하도록 함.
    """
    from common.crawler_base import setup_driver
    from app_factory import create_app  # Flask 앱 인스턴스 생성 함수
    app = create_app()  # 앱 인스턴스를 가져옴
    # driver, user_data_dir = setup_driver(task_id)
    driver, user_data_dir = setup_driver(task_id)

    try:
        with app.app_context():
            # 1. 간편 인증 수행
            auth_result_json, auth_status_code = perform_auth(
                driver, task_id, name, phone1, phone2, phone3, birth, id_back
            )

            # 1번 실패시
            if auth_status_code != 200:
                driver.quit()
                return jsonify(auth_result_json), auth_status_code

            time.sleep(2)

            update_task_status(task_id, "saving_data", None)
            print("🔄 백엔드 상태변경 : saving_data ")

            # 2. 데이터 추출
            result_data, status_code = save_crawler_data(driver, name, birth)

            if status_code != 200:
                driver.quit()
                return jsonify(result_data), status_code

            time.sleep(1)
            driver.quit()
            return jsonify(result_data), status_code

    except Exception as e:
        print(f"⚠️ 크롤러 실행 중 예외 발생: {str(e)}")
        with app.app_context():
            return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️ 드라이버 종료 중 예외: {str(e)}")
        # shutil.rmtree(user_data_dir, ignore_errors=True)
