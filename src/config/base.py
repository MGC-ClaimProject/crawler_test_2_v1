from dotenv import load_dotenv
import os

load_dotenv()



class Config:
    SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL")
    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")
    CAPTCHA_SAVE_DIR = os.getenv("CAPTCHA_SAVE_DIR")
    SIMPLE_JSON_SAVE_DIR = os.getenv("SIMPLE_JSON_SAVE_DIR")

    UPDATE_TASK_STATUS_URL = BACKEND_BASE_URL + "/v1/insurances/crawler_status"

    CHROME_BINARY_PATH = os.getenv("CHROME_BINARY_PATH")
    CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

    INSURANCE_SIMPLE_SITE=os.getenv("INSURANCE_SIMPLE_SITE")

