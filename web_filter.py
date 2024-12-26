from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox
import os
import webbrowser
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

class WebContentFilter:
    def __init__(self):
        self.blocked_tags = {
            'img', 'video', 'audio', 'source', 'picture',
            'iframe', 'embed', 'object', 'canvas', 'style', 'script'
        }
        self.allowed_attributes = {'href', 'target', 'rel'}
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return driver

    def fetch_url(self, url):
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(url)
            
            # 페이지가 완전히 로드될 때까지 대기 (최대 20초)
            wait = WebDriverWait(driver, 20)
            
            # 본문 콘텐츠가 로드될 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'container')))
            except TimeoutException:
                pass  # 특정 클래스가 없더라도 계속 진행
                
            # JavaScript가 실행될 시간을 추가로 기다림
            driver.implicitly_wait(5)
            
            # 페이지 끝까지 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.implicitly_wait(2)
            
            html_content = driver.page_source
            return html_content
            
        except Exception as e:
            messagebox.showerror("Error", f"URL을 가져오는 중 오류가 발생했습니다: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def filter_content(self, html_content, base_url=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 텍스트 콘텐츠 보존을 위해 
        for tag in self.blocked_tags:
            for element in soup.find_all(tag):
                # 텍스트 콘텐츠가 있다면 보존
                if element.string:
                    text_node = soup.new_tag('span')
                    text_node.string = element.string
                    element.replace_with(text_node)
                else:
                    element.decompose()
        
        # 허용된 속성만 남기기
        for element in soup.find_all(True):
            attrs = dict(element.attrs)
            for attr in attrs:
                if attr not in self.allowed_attributes:
                    del element[attr]
        
        # 기본 스타일 추가
        style_tag = soup.new_tag('style')
        style_tag.string = """
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 1200px; margin: 0 auto; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            h1, h2, h3 { color: #333; margin-top: 1.5em; }
            p { margin: 1em 0; }
        """
        if soup.head:
            soup.head.append(style_tag)
        else:
            head = soup.new_tag('head')
            head.append(style_tag)
            soup.html.insert(0, head)
            
        return str(soup)

    def save_and_open(self, filtered_content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(os.getcwd(), f'filtered_{timestamp}.html')
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(filtered_content)
            webbrowser.open('file://' + os.path.abspath(output_file))
            return output_file
        except IOError as e:
            messagebox.showerror("Error", f"파일 저장 중 오류가 발생했습니다: {e}")
            return None

class FilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Content Filter")
        self.root.geometry("500x180")
        
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="웹페이지 URL:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.url_entry = tk.Entry(frame, width=50)
        self.url_entry.pack(fill=tk.X, pady=(5, 10))
        
        self.status_label = tk.Label(frame, text="", fg="blue")
        self.status_label.pack(pady=(0, 10))
        
        tk.Button(frame, text="필터링 시작", command=self.process_url, 
                 bg='#0066cc', fg='white', padx=20, pady=5).pack()
        
        self.filter = WebContentFilter()

    def process_url(self):
        self.status_label.config(text="페이지 로딩 중...")
        self.root.update()
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "URL을 입력해주세요.")
            self.status_label.config(text="")
            return
            
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            
        html_content = self.filter.fetch_url(url)
        if html_content:
            self.status_label.config(text="필터링 중...")
            self.root.update()
            
            filtered_content = self.filter.filter_content(html_content, url)
            saved_file = self.filter.save_and_open(filtered_content)
            
            self.status_label.config(text="")
            if saved_file:
                messagebox.showinfo("Success", f"파일이 저장되었습니다:\n{saved_file}")

def main():
    root = tk.Tk()
    app = FilterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()