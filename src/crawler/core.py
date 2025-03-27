# 크롤링 로직 (동기/비동기 모두 포함 가능)
# crawler/crawler/core.py

import time


from crawler.utils import run_in_background
from common.utils import update_task_status
from insurance_simple_crawler.insurance_crawler import run_crawler as simple_run_crawler

def run_insurance_simple_crawler(task_id, member_id, name, phone1, phone2, phone3, birth, id_back, carrier):
    print(f"[SIMPLE] 크롤러 실행 시작: member_id={member_id}")

    # simple_run_crawler는 (result_data, status_code)를 반환한다고 가정합니다.
    result_data, status_code = simple_run_crawler(task_id, member_id, name, phone1, phone2, phone3, birth, id_back, carrier)

    # result_data가 Flask Response 객체이면 dict로 변환, 아니면 그대로 사용
    if hasattr(result_data, "get_json"):
        dict_result_data = result_data.get_json()
    else:
        dict_result_data = result_data

    result_status = dict_result_data.get("status")
    result_message = dict_result_data.get("message")
    # 상태 업데이트
    if status_code != 200:
        update_task_status(task_id, "failed", None)
    else:
        # insurance_data 추출 (이 값은 dict여야 함)
        insurance_data = dict_result_data.get("insurance_data")
        print("🔄 백엔드 상태 변경 : completed  - 데이터 DB 저장 완료!!")
        print(f"insurance_data : {insurance_data}")
        update_task_status(task_id, "completed", insurance_data)



    print(f"[SIMPLE] 크롤러 실행 완료 ->  result_status:{result_status}, message:{result_message}, status:{status_code}")
    


def run_insurance_all_crawler(member_id, name, phone1, phone2, phone3, birth, gender, carrier, desired_id):
    # 여기에 보험 전체 크롤러 로직을 작성하세요.
    print(f"[ALL] 크롤러 실행 시작: member_id={member_id}")
    # ... (크롤링 로직)
    time.sleep(5)  # 예시로 5초 대기
    print("[ALL] 크롤러 실행 완료")
    return {"status": 200}

# 동기/비동기 실행 함수 예시
def run_insurance_simple_crawler_async(*args, **kwargs):
    return run_in_background(run_insurance_simple_crawler, *args, **kwargs)

def run_insurance_all_crawler_async(*args, **kwargs):
    return run_in_background(run_insurance_all_crawler, *args, **kwargs)
