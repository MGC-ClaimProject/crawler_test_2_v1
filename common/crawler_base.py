import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from config.base import Config

logging.basicConfig(level=logging.INFO)

def setup_driver():
    driver_path = "/usr/bin/chromedriver"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-proxy-server")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")
    # 인코그니토 모드 추가: 매번 새 세션이 시작됨
    options.add_argument("--incognito")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )
    options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

    logging.info("[setup_driver] Starting Chrome session with driver at: %s", driver_path)

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    logging.info("[setup_driver] Chrome session started.")

    driver.get("chrome://net-internals/#dns")
    driver.execute_script("chrome.send('clearHostResolverCache');")

    return driver, None
