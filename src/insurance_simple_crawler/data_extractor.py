import os
from bs4 import BeautifulSoup  # 🔄 HTML 파싱 라이브러리
import json

from flask import jsonify

from config.base import Config

# 🔄 저장할 디렉토리 설정
save_directory = Config.SIMPLE_JSON_SAVE_DIR  # ✅ 원하는 저장 경로 설정 (예: "C:/my_data/saved_pages")

# 🔄 저장 디렉토리 생성 (없으면 생성)
os.makedirs(save_directory, exist_ok=True)

STATUS_MAPPING = {
    "유지(정상)": "active",
    "소멸(해약포함)": "terminated",
    "휴면": "dormant",
    "만기": "matured",
    "실효": "lapsed",
    "해지": "cancelled"
}

def save_crawler_data(driver, name, birth):
    try:
        current_url = driver.current_url
        print(f"🔄 현재 페이지 URL: {current_url}")
        page_source = driver.page_source

        soup = BeautifulSoup(page_source, "html.parser")
        insurance_data = []

        filename = f"{birth}_{name}"

        # ✅ 보험 정보 추출
        tlist_tables = soup.find_all("table", {"class": "tList pc_view"})
        if len(tlist_tables) < 2:
            print("⚠️ 보험 정보 테이블을 찾을 수 없습니다.")
            return None

        main_table = tlist_tables[1]
        rows = main_table.find_all("tr")[2:]

        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 10:
                insurance_company = columns[0].get_text(strip=True)
                contract_status = columns[4].get_text(strip=True)
                mapped_status = STATUS_MAPPING.get(contract_status, "pending")

                data = {
                    "company": insurance_company,
                    "contract_type": columns[1].get_text(strip=True),
                    "policy_name": columns[2].get_text(strip=True),
                    "policy_number": columns[3].get_text(strip=True),
                    "status": mapped_status,
                    "contract_relation": columns[5].get_text(strip=True),
                    "start_date": columns[6].get_text(strip=True),
                    "end_date": columns[7].get_text(strip=True),
                    "branch": columns[8].get_text(strip=True),
                    "phone_number": columns[9].get_text(strip=True)
                }
                insurance_data.append(data)

        # # ✅ 미회신 생명보험사 정보 수집
        # unresponded_life = [
        #     a.get_text(strip=True)
        #     for a in soup.select("#unLList a")
        # ]
        #
        # # ✅ 미회신 손해보험사 정보 수집
        # unresponded_nonlife = [
        #     a.get_text(strip=True)
        #     for a in soup.select("#unNList a")
        # ]


        return {
            "status": "success",
            "message": "보험 추출 완료!",
            "insurance_data": insurance_data
        }, 200

    except Exception as e:
        print(f"❌ 보험 데이터 저장 중 오류 발생: {e}")
        return {
            "status": "fail",
            "message": str(e)
        }, 500

# 🔄 페이지 소스 저장 함수
def save_page_source(driver, name, birth):
    try:
        current_url = driver.current_url
        print(f"🔄 현재 페이지 URL: {current_url}")

        if "insuranceStep02.do" in current_url:
            print("✅ 저장할 페이지를 찾았습니다.")

            filename = os.path.join(save_directory, f"{birth}_{name}.html")
            page_source = driver.page_source

            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_source)

            print(f"✅ HTML 저장 완료: {filename}")

            return filename  # 저장된 파일 경로 반환
        else:
            print("⚠️ 저장할 페이지를 찾지 못했습니다.")
            return None

    except Exception as e:
        print(f"⚠️ HTML 저장 중 오류 발생: {str(e)}")
        return None

# 🔄 HTML 파일에서 데이터 추출 함수
def extract_data_from_html(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        insurance_data = []

        # ✅ 모든 `tList pc_view` 테이블 찾기
        tlist_tables = soup.find_all("table", {"class": "tList pc_view"})

        # ✅ 보험 정보가 있는 두 번째 `tList pc_view` 테이블 선택
        if len(tlist_tables) < 2:
            print("⚠️ 보험 정보 테이블을 찾을 수 없습니다.")
            return None

        main_table = tlist_tables[1]  # ✅ 두 번째 테이블이 보험 내역

        rows = main_table.find_all("tr")[2:]  # ✅ 헤더 제외하고 데이터 행만 추출

        for row in rows:
            columns = row.find_all("td")

            if len(columns) >= 10:
                # ✅ 보험사 정보 title 속성이 아닌 텍스트 내용 가져오기
                insurance_company = columns[0].get_text(strip=True)

                # ✅ 상태 매핑 적용
                contract_status = columns[4].get_text(strip=True)
                mapped_status = STATUS_MAPPING.get(contract_status, "pending")

                data = {
                    "company": insurance_company,
                    "contract_type": columns[1].get_text(strip=True),
                    "policy_name": columns[2].get_text(strip=True),
                    "policy_number": columns[3].get_text(strip=True),
                    "status": mapped_status,
                    "contract_relation": columns[5].get_text(strip=True),
                    "start_date": columns[6].get_text(strip=True),
                    "end_date": columns[7].get_text(strip=True),
                    "branch": columns[8].get_text(strip=True),
                    "phone_number": columns[9].get_text(strip=True)
                }
                insurance_data.append(data)

        json_filename = f"extracted_{os.path.basename(filename).split('.')[0]}.json"
        json_filepath = os.path.join(os.path.dirname(filename), json_filename)

        with open(json_filepath, "w", encoding="utf-8") as json_file:
            json.dump(insurance_data, json_file, ensure_ascii=False, indent=4)

        print(f"✅ 보험 데이터가 {json_filepath} 파일에 저장되었습니다.")
        os.remove(filename)
        print(f"🗑️ HTML 파일 삭제 완료: {filename}")

        return json_filename

    except Exception as e:
        print(f"⚠️ HTML에서 데이터 추출 중 오류 발생: {str(e)}")
        return None


def extract_and_log_data(driver, name, birth):
    # 🔄 HTML 저장 후 파일명 반환
    filename = save_page_source(driver, name, birth)
    if filename:
        json_filename = extract_data_from_html(filename)  # 🔄 저장된 HTML에서 데이터 추출
        return json_filename