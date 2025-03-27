# import os
# import tempfile
# import time
# import uuid
# import logging
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from config.base import Config
#
# logging.basicConfig(level=logging.INFO)
#
# def setup_driver(task_id):
#     driver_path = "/usr/bin/chromedriver"
#
#     options = webdriver.ChromeOptions()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("--no-proxy-server")
#     options.add_argument("--ignore-certificate-errors")
#     options.add_argument("--disable-software-rasterizer")
#     options.add_argument("--single-process")
#     options.add_argument("--no-zygote")
#     options.add_argument("--incognito")  # 인코그니토 모드 추가
#     options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     )
#     options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
#
#     # 고유한 프로파일 디렉터리 생성: task_id, uuid, 타임스탬프 사용
#     unique_profile = f"chrome_profile_{task_id}_{uuid.uuid4()}_{int(time.time())}"
#     user_data_dir = tempfile.mkdtemp(prefix=unique_profile + "_")
#     options.add_argument(f"--user-data-dir={user_data_dir}")
#     logging.info("[setup_driver] Using Chrome user data directory: %s", user_data_dir)
#
#     service = Service(executable_path=driver_path)
#     driver = webdriver.Chrome(service=service, options=options)
#     logging.info("[setup_driver] Chrome session started.")
#
#     driver.get("chrome://net-internals/#dns")
#     driver.execute_script("chrome.send('clearHostResolverCache');")
#
#     return driver, user_data_dir


import os
import time
import uuid
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)

def setup_driver(task_id):
    driver_path = "/usr/bin/chromedriver"

    # 고유한 유저 프로필 경로 설정
    unique_profile_dir = f"/tmp/chrome_profile_{task_id}_{uuid.uuid4()}"

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
    # options.add_argument("--incognito")
    options.add_argument(f"--user-data-dir={unique_profile_dir}")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )
    options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")

    logging.info("[setup_driver] Using Chrome user data directory: %s", unique_profile_dir)

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    logging.info("[setup_driver] Chrome session started.")

    # driver.get("chrome://net-internals/#dns")
    # driver.execute_script("chrome.send('clearHostResolverCache');")

    return driver, unique_profile_dir

