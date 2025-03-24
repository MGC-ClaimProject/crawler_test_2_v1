FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 필요한 의존성 및 크로미움, 크로미움 드라이버 설치
RUN apt update && apt install -y \
    wget gnupg curl unzip \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcairo2 libcups2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxfixes3 libxkbcommon0 libxrandr2 libxrender1 libxss1 libxi6 \
    libdbus-1-3 libexpat1 libfontconfig1 libgconf-2-4 \
    xdg-utils libu2f-udev libvulkan1 xvfb \
    chromium chromium-driver \
 && apt clean && rm -rf /var/lib/apt/lists/*

# 크로미움 실행 파일 위치 지정 (보통 /usr/bin/chromium)
ENV CHROME_BIN=/usr/bin/chromium

# chromedriver가 /usr/bin/chromedriver에 존재하는지 확인
RUN if [ -f /usr/bin/chromedriver ]; then \
         echo "chromedriver exists at /usr/bin/chromedriver"; \
     else \
         echo "chromedriver not found in /usr/bin/chromedriver"; exit 1; \
     fi

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY . /app

EXPOSE 5001

CMD ["python", "main.py"]
