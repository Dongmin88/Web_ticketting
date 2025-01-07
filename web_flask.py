from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_links_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 링크 추출
        links = [a['href'] for a in soup.find_all('a', href=True)]
        
        # 텍스트 추출
        page_text = soup.get_text()
        
        return links, page_text.strip()
    except requests.RequestException as e:
        return [], f"Error: {e}"

@app.route('/')
def home():
    url = "https://www.interpark.com/"  # 여기에 원하는 URL 입력
    links, text = get_links_from_page(url)
    
    # HTML 템플릿
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webpage Links and Text</title>
    </head>
    <body>
        <h1>Links from the Page</h1>
        <ul>
            {% for link in links %}
                <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
            {% endfor %}
        </ul>
        <h1>Page Text</h1>
        <pre>{{ text }}</pre>
    </body>
    </html>
    """
    
    # HTML 렌더링
    return render_template_string(html_template, links=links, text=text[:1000])  # 텍스트는 처음 1000자만 표시

if __name__ == '__main__':
    app.run(debug=True)
