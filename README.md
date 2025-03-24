flask 
poetry run python insurance_crawler.py

python main.py





----
crawler/
├── __init__.py
├── core.py         # 크롤링 로직 (동기/비동기 함수 포함)
└── utils.py        # 공통 유틸리티 함수들 (예: 스레드 실행 관련)
web/
├── __init__.py
└── routes.py       # Flask 라우트; 여기서 crawler.core의 함수들을 호출
main.py             # Flask 앱 인스턴스 생성 (또는 create_app() 사용)# crawler_test_2_v1
