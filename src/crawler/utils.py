# 공통 유틸리티 (예: 스레딩 관련 함수)
# crawler/crawler/utils.py
import threading

def run_in_background(func, *args, **kwargs):
    """
    주어진 함수를 별도의 스레드에서 실행합니다.
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread
