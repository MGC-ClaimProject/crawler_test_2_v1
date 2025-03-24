
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.common import TimeoutException
import requests
from config.base import Config

# 🔄 알럿 확인 및 닫기 함수
# def handle_alert(driver):
#     try:
#         WebDriverWait(driver, 1).until(EC.alert_is_present())  # 🔄 알럿이 뜰 때까지 대기 (최대 1초)
#         alert = driver.switch_to.alert
#         print(f"⚠️ 알럿 감지: {alert.text}")
#         alert.accept()  # 🔄 확인 버튼 클릭
#         print("✅ 알럿이 닫혔습니다.")
#     except NoAlertPresentException:
#         print("⚠️ 알럿이 존재하지 않습니다.")
#     except TimeoutException:
#         print("⚠️ 알럿 대기 시간 초과.")
#     except Exception as e:
#         print(f"⚠️ 알럿 처리 중 예외 발생: {str(e)}")
#


def update_task_status(task_id, status, result_data):
    """
    크롤러 상태 업데이트 요청을 보내는 함수
        # 📌 크롤러 status 필드의 값
            CRAWLER_STATUS = {
                "pending": "요청중",                        # 요청이 생성됨
                "in_progress": "진행중",                    # 크롤러 실행 중
                "waiting_for_verification": "인증 대기",    # 사용자의 휴대폰 인증을 기다리는 중
                "auth_pass": "인증 성공",                   # 인증에 성공함
                "saving_data": "최종 데이터 저장중",       # 크롤링이 완료되어 데이터를 저장하는 중
                "completed": "성공",                        # 크롤러 완료 및 데이터 저장 완료
                "failed": "실패"                            # 크롤러 실행 실패
            }

    """

    update_task_status_url = Config.UPDATE_TASK_STATUS_URL
    url = f"{update_task_status_url}/{task_id}/"
    payload = {
        "task_id": str(task_id),
        "status": status
    }
    # 상태가 completed이고 result_data가 존재하면 payload에 추가
    if status == "completed" and result_data is not None:
        payload["result_data"] = result_data

    try:
        response = requests.patch(url, json=payload, timeout=5)
        # 응답 본문이 비어 있으면 빈 dict로 처리
        try:
            resp_json = response.json()
        except ValueError:
            resp_json = {}
        print(f"✅ 상태 업데이트 응답: {response.status_code} - {resp_json}")
    except requests.RequestException as e:
        print(f"⚠️ 상태 업데이트 요청 실패: {str(e)}")