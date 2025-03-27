# crawler/web/routes.py
# Flask 라우트, 여기서 core.py의 함수들을 호출


import threading
import uuid

from flask import Blueprint, request, jsonify
from crawler.core import (
    run_insurance_simple_crawler_async,
    run_insurance_all_crawler_async,
)
# 필요에 따라 다른 모듈 임포트

web_bp = Blueprint("web", __name__)

@web_bp.route('/insurance_simple_crawler', methods=['POST'])
def insurance_simple_crawler():
    try:
        data = request.get_json()
        print(f"📩 받은 데이터: {data}")

        # ✅ Task ID 생성 (고유한 값)
        task_id = data.get("task_id")
        member_id = data.get("member_id")
        name = data.get("name")
        phone1 = data.get("phone1")
        phone2 = data.get("phone2")
        phone3 = data.get("phone3")
        birth = data.get("birth")  # 6자리
        id_back = data.get("id_back")  # 7자리
        carrier = data.get("carrier")
        # access_token = data.get("access_token")  # 백엔드에서 받은 액세스 토큰

        if not all([member_id, name, phone1, phone2, phone3, birth, id_back, carrier]):
            return jsonify({"error": "필수 데이터가 부족합니다!"}), 400

        # 비동기 실행 (백그라운드)
        run_insurance_simple_crawler_async(task_id, member_id, name, phone1, phone2, phone3, birth, id_back, carrier)

        # ✅ 성공적인 요청 응답 (Task ID 반환)
        return jsonify({
            "message": "크롤러가 실행되었습니다!",
            "task_id": task_id,  # ✅ task_id 반환
            "status": "in_progress"
        }), 202

    except Exception as e:
        print(f"⚠️ 에러 발생: {str(e)}")
        return jsonify({"error": "서버 오류가 발생했습니다."}), 500


@web_bp.route('/insurance_all_crawler', methods=['POST'])
def insurance_all_crawler():
    try:
        data = request.get_json()
        print(f"📩 받은 데이터: {data}")

        member_id = data.get("member_id")
        desired_id = data.get("desired_id")
        name = data.get("name")
        phone1 = data.get("phone1")
        phone2 = data.get("phone2")
        phone3 = data.get("phone3")
        birth = data.get("birth")  # 8자리
        gender = data.get("gender")  # male, female
        carrier = data.get("carrier")
        access_token = data.get("access_token")  # 백엔드에서 받은 액세스 토큰

        if not all([member_id, name, phone1, phone2, phone3, birth, gender, carrier, desired_id, access_token]):
            return jsonify({"error": "필수 데이터가 부족합니다!"}), 400

        # 비동기 실행 (백그라운드)
        run_insurance_all_crawler_async(member_id, name, phone1, phone2, phone3, birth, gender, carrier, desired_id)

        return jsonify({"message": "보험 전체 크롤러 실행이 시작되었습니다!"}), 200

    except Exception as e:
        print(f"⚠️ 에러 발생: {str(e)}")
        return jsonify({"error": "서버 오류가 발생했습니다."}), 500



