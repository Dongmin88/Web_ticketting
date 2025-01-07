from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_links_from_dynamic_page_without_media(url):
    # ChromeOptions 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 브라우저 창을 띄우지 않음
    chrome_options.add_argument("--disable-gpu")  # GPU 비활성화 (Windows에서 필요할 수 있음)
    
    # 이미지와 동영상 로드 차단
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    
    driver_path = "chromedriver"  # ChromeDriver 실행 파일 경로
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # URL 열기
        driver.get(url)
        
        # JavaScript 실행을 기다림
        time.sleep(5)  # 페이지 로드 시간을 조정

        # 완전히 로드된 HTML 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 링크 추출
        links = [a['href'] for a in soup.find_all('a', href=True)]
        
        # 페이지 텍스트 추출
        page_text = soup.get_text()
        
        return links, page_text.strip()
    
    finally:
        # WebDriver 종료
        driver.quit()

# 테스트
url = "https://example.com"
links, text = get_links_from_dynamic_page_without_media(url)

print("Links:")
for link in links:
    print(link)

print("\nPage Text:")
print(text[:500])  # 첫 500자만 출력
