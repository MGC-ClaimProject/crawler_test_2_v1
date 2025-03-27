# crawler/app_factory.py

from flask import Flask
from config.base import Config


def create_app():
    app = Flask(__name__)

    # 앱 설정 (예: config 파일 로드 등)
    app.config.from_object(Config)

    # 블루프린트 등록
    from web.routes import web_bp
    app.register_blueprint(web_bp)

    return app
