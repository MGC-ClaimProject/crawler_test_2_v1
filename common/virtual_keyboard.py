import re
from bs4 import BeautifulSoup
import cv2
import numpy as np
import pytesseract
import requests
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time


# 1. 디버깅용: 현재 페이지에서 모든 키 요소의 data-coords 값을 출력
def data_coords(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    keys = soup.find_all("img", class_="kpd-data")
    for key in keys:
        coords_str = key.get("data-coords", "")
        if coords_str:
            try:
                left, top, right, bottom = map(int, coords_str.split(","))
                width = right - left
                height = bottom - top
                print(f"키 좌표: {coords_str} -> 위치: ({left}, {top}), 크기: ({width} x {height})")
            except Exception as e:
                print("좌표 파싱 오류:", e)


# 2. 키보드 미리보기 이미지 URL 추출 함수
def keyboard_preview_url(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    div_preview = soup.find("div", class_="preview keyboard")
    if div_preview:
        style_attr = div_preview.get("style", "")
        match = re.search(r'background-image:\s*url\("([^"]+)"\)', style_attr)
        if match:
            url = match.group(1)
            print("추출된 URL:", url)
            return url
        else:
            print("URL을 추출할 수 없습니다.")
    else:
        print("preview.keyboard 요소를 찾을 수 없습니다.")
    return None


# 3. URL에서 이미지를 다운로드하여 OpenCV 이미지 객체로 반환
def get_keyboard_image(driver):
    url = keyboard_preview_url(driver)
    if url:
        response = requests.get(url)
        if response.status_code == 200:
            img_data = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            if img is None:
                raise Exception("이미지 디코딩에 실패했습니다.")
            # 전처리 단계: 그레이스케일, 블러, 히스토그램 평활화, AdaptiveThreshold 등
            processed_img = preprocess_image_for_ocr(img)
            return processed_img
        else:
            raise Exception("이미지 다운로드 실패, 상태 코드: " + str(response.status_code))
    else:
        raise Exception("키보드 미리보기 URL을 가져올 수 없습니다.")


# 4. 이미지 전처리 함수 (OCR 정확도 향상을 위해)
def preprocess_image_for_ocr(img):
    # 1. 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 2. 노이즈 제거: GaussianBlur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # 3. 대비 향상을 위해 히스토그램 평활화
    equalized = cv2.equalizeHist(blurred)
    # 4. Adaptive thresholding (이진화); 가끔 배경 색상이 다를 때 유용함
    thresh = cv2.adaptiveThreshold(equalized, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    return thresh


# 5. OCR을 사용해 숫자 키 매핑(사진상 순서대로)을 추출하는 함수
def extract_numeric_key_mappings(driver):
    """
    OCR 결과에서 상단 행(가장 y값이 낮은 결과들)에서
    인식된 숫자 키 중, 정확히 한 글자인 숫자(0~9)만 사용하여
    OCR 데이터 순서대로(인덱스 순서) 매핑합니다.
    """
    img = get_keyboard_image(driver)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n_boxes = len(data['level'])
    numeric_keys = []  # (text, center_x, center_y, x) 튜플 리스트

    for i in range(n_boxes):
        text = data['text'][i].strip()
        # 텍스트가 정확히 1글자이고 숫자인 경우만 사용
        if text and len(text) == 1 and text.isdigit():
            try:
                x = int(data['left'][i])
                y = int(data['top'][i])
                w = int(data['width'][i])
                h = int(data['height'][i])
            except Exception as e:
                print("좌표 데이터 파싱 오류:", e)
                continue
            center_x = x + w // 2
            center_y = y + h // 2
            numeric_keys.append((text, center_x, center_y, x))

    # 만약 OCR 결과가 여러 줄이라면, 상단행(예: y값이 작은 행)만 선택하는 로직 추가 가능
    # 여기서는 OCR 데이터 순서(리스트 순서)를 그대로 사용합니다.

    # x 좌표 기준 정렬(사진상 순서대로 좌우 정렬)
    sorted_numeric_keys = sorted(numeric_keys, key=lambda k: k[3])
    numeric_mapping = {k[0]: (k[1], k[2]) for k in sorted_numeric_keys}
    print("자동 추출된 숫자 키 매핑:", numeric_mapping)
    return numeric_mapping


# 6. HTML에서 소문자 키 매핑(예: qwertyuiopasdfghjklzxcvbnm)을 순서대로 추출하는 함수
def extract_lower_layout_map(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", class_="kpd-group lower")
    if container is None:
        print("Lower keys container를 찾을 수 없습니다.")
        return {}
    key_elements = container.find_all("img", class_="kpd-data")
    # OCR 순서와 달리 HTML DOM 순서대로라면, 화면상의 순서를 따르도록 가정
    lower_keys_order = list("qwertyuiopasdfghjklzxcvbnm")
    if len(key_elements) < len(lower_keys_order):
        print("예상보다 소문자 키 이미지 개수가 적습니다.")
    layout_map = {}
    for i, elem in enumerate(key_elements):
        if i >= len(lower_keys_order):
            break
        coords_str = elem.get("data-coords")
        if coords_str:
            try:
                left, top, right, bottom = map(int, coords_str.split(","))
            except Exception as e:
                print("소문자 키 좌표 파싱 오류:", e)
                continue
            cx = (left + right) // 2
            cy = (top + bottom) // 2
            char = lower_keys_order[i]
            layout_map[char] = (cx, cy)
    print("소문자 키 매핑:", layout_map)
    return layout_map


# 7. HTML에서 특수문자 키 매핑(예: !@#$%^&*())를 순서대로 추출하는 함수
def extract_special_layout_map(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", class_="kpd-group special")
    if container is None:
        print("Special keys container를 찾을 수 없습니다.")
        return {}
    key_elements = container.find_all("img", class_="kpd-data")
    special_keys_order = list("!@#$%^&*()")
    if len(key_elements) < len(special_keys_order):
        print("예상보다 특수문자 키 이미지 개수가 적습니다.")
    layout_map = {}
    for i, elem in enumerate(key_elements):
        if i >= len(special_keys_order):
            break
        coords_str = elem.get("data-coords")
        if coords_str:
            try:
                left, top, right, bottom = map(int, coords_str.split(","))
            except Exception as e:
                print("특수문자 키 좌표 파싱 오류:", e)
                continue
            cx = (left + right) // 2
            cy = (top + bottom) // 2
            key_char = special_keys_order[i]
            layout_map[key_char] = (cx, cy)
    print("특수문자 키 매핑:", layout_map)
    return layout_map



def get_bounding_rect(driver, element):
    # 요소의 getBoundingClientRect()를 실행하여 {x, y, width, height} 딕셔너리를 반환합니다.
    rect = driver.execute_script(
        "var rect = arguments[0].getBoundingClientRect(); "
        "return {x: rect.left, y: rect.top, width: rect.width, height: rect.height};",
        element
    )
    return rect
# 8. Selenium ActionChains를 이용해 특정 오프셋 위치를 클릭하는 함수
def click_key(driver, container_element, offset):
    """
    container_element: 클릭 기준이 되는 가상키보드 컨테이너 (예: id="nppfs-keypad-passwd")
    offset: 컨테이너 내에서 클릭할 좌표 (x, y)
    """
    # 컨테이너의 화면상의 위치를 가져옵니다.
    rect = get_bounding_rect(driver, container_element)
    click_x = rect['x'] + offset[0]
    click_y = rect['y'] + offset[1]
    print(f"컨테이너 좌표: ({rect['x']}, {rect['y']}) / 클릭 오프셋: {offset} -> 최종 클릭 좌표: ({click_x}, {click_y})")
    # document.elementFromPoint를 사용하여 해당 좌표의 요소를 클릭합니다.
    driver.execute_script("document.elementFromPoint(arguments[0], arguments[1]).click();", click_x, click_y)
    time.sleep(0.5)


# 9. 최종 키 매핑(숫자, 소문자, 특수문자) 합치기
def extract_combined_key_mapping(driver):
    numeric_map = extract_numeric_key_mappings(driver)
    lower_map = extract_lower_layout_map(driver)
    special_map = extract_special_layout_map(driver)
    combined = {}
    combined.update(numeric_map)
    combined.update(lower_map)
    combined.update(special_map)
    print("최종 키 매핑:", combined)
    return combined


# 10. 추출된 키 매핑을 이용해 가상 키보드에서 비밀번호를 입력하는 함수
def enter_password_via_virtual_keyboard(driver, password, key_mapping):
    # 먼저 비밀번호 입력창(input id="passwd")을 클릭하여 가상키보드가 나타나도록 합니다.
    passwd_input = driver.find_element(By.ID, "passwd")
    passwd_input.click()
    time.sleep(1)

    # 가상키보드 컨테이너 요소 (예: id="nppfs-keypad-passwd")를 찾습니다.
    keyboard_container = driver.find_element(By.ID, "nppfs-keypad-passwd")
    for char in password:
        if char in key_mapping:
            offset = key_mapping[char]
            print(f"키 '{char}' 클릭: offset {offset}")
            click_key(driver, keyboard_container, offset)
        else:
            print(f"키 '{char}'의 매핑값이 없습니다.")


