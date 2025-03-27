FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 기본 의존성 설치
RUN apt update && apt install -y \
    wget curl unzip gnupg \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcairo2 libcups2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxfixes3 libxkbcommon0 libxrandr2 libxrender1 libxss1 libxi6 \
    libdbus-1-3 libexpat1 libfontconfig1 libgconf-2-4 \
    xdg-utils libu2f-udev libvulkan1 xvfb \
 && apt clean && rm -rf /var/lib/apt/lists/*

# ✅ 크롬 설치 (정확한 버전)
RUN wget https://storage.googleapis.com/chrome-for-testing-public/121.0.6167.184/linux64/chrome-linux64.zip && \
    unzip chrome-linux64.zip && \
    mv chrome-linux64 /opt/chrome && \
    ln -s /opt/chrome/chrome /usr/bin/chromium

# ✅ 크롬드라이버 설치 (같은 버전)
RUN wget https://storage.googleapis.com/chrome-for-testing-public/121.0.6167.184/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

# 크롬 실행 경로 환경 변수 지정
ENV CHROME_BIN=/usr/bin/chromium

# chromedriver 존재 확인
RUN if [ -f /usr/bin/chromedriver ]; then \
         echo "✅ chromedriver exists at /usr/bin/chromedriver"; \
     else \
         echo "❌ chromedriver not found!"; exit 1; \
     fi

# 작업 디렉토리
WORKDIR /app/src

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 의존성 설치
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# 소스 코드 복사
COPY ./src /app/src
ENV PYTHONPATH=/app/src

EXPOSE 5001

CMD ["python", "main.py"]
