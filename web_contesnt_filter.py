import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class WebContentFilter:
    def __init__(self):
        # 필터링할 태그들
        self.blocked_tags = {
            'img', 'video', 'audio', 'source', 'picture',
            'iframe', 'embed', 'object', 'canvas', 'style', 'script'
        }
        
        # 허용할 속성들
        self.allowed_attributes = {'href', 'target', 'rel'}
        
        # 세션 생성
        self.session = requests.Session()
        
    def fetch_url(self, url):
        """웹 페이지 내용을 가져옵니다."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def filter_content(self, html_content, base_url=None):
        """HTML 콘텐트를 필터링합니다."""
        # BeautifulSoup 객체 생성
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 불필요한 태그 제거
        for tag in self.blocked_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # 모든 요소에서 style 속성과 불필요한 속성들 제거
        for element in soup.find_all(True):
            # 허용된 속성만 남기고 나머지 제거
            attrs = dict(element.attrs)
            for attr in attrs:
                if attr not in self.allowed_attributes:
                    del element[attr]
            
            # href 속성이 있는 경우 절대 경로로 변환
            if base_url and 'href' in element.attrs:
                element['href'] = urljoin(base_url, element['href'])

        return str(soup)

    def save_content(self, filtered_content, output_file):
        """필터링된 콘텐츠를 파일로 저장합니다."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(filtered_content)
            print(f"필터링된 콘텐츠가 {output_file}에 저장되었습니다.")
        except IOError as e:
            print(f"파일 저장 중 오류 발생: {e}")

def main():
    # 사용 예시
    url = input("필터링할 웹페이지 URL을 입력하세요: ")
    output_file = input("저장할 파일 이름을 입력하세요 (예: filtered.html): ")
    
    filter = WebContentFilter()
    
    # 웹페이지 가져오기
    html_content = filter.fetch_url(url)
    if html_content:
        # 콘텐츠 필터링
        filtered_content = filter.filter_content(html_content, url)
        
        # 결과 저장
        filter.save_content(filtered_content, output_file)

if __name__ == "__main__":
    main()