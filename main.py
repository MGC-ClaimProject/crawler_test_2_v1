# Flask 앱 인스턴스 생성 (또는 create_app() 사용)
# crawler/main.py
from app_factory import create_app
from config.base import *

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
