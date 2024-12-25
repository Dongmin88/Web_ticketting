import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QCalendarWidget, QComboBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import QDate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import datetime
import logging
import requests
from bs4 import BeautifulSoup

class TicketingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_logging()
        self.concert_data = {}  # 콘서트 정보를 저장할 딕셔너리

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ticketing_gui.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle('인터파크 티켓팅 프로그램')
        self.setGeometry(100, 100, 800, 600)

        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # 로그인 정보 입력
        login_group = QWidget()
        login_layout = QHBoxLayout()
        
        # ID 입력
        id_label = QLabel('아이디:')
        self.id_input = QLineEdit()
        login_layout.addWidget(id_label)
        login_layout.addWidget(self.id_input)
        
        # 비밀번호 입력
        pw_label = QLabel('비밀번호:')
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        login_layout.addWidget(pw_label)
        login_layout.addWidget(self.pw_input)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)

        # 날짜 선택
        date_label = QLabel('공연 날짜 선택:')
        layout.addWidget(date_label)
        
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.clicked.connect(self.date_selected)
        layout.addWidget(self.calendar)

        # 콘서트 선택
        concert_label = QLabel('공연 선택:')
        layout.addWidget(concert_label)
        
        self.concert_combo = QComboBox()
        self.concert_combo.currentIndexChanged.connect(self.concert_selected)
        layout.addWidget(self.concert_combo)

        # 좌석 등급 선택
        seat_label = QLabel('좌석 등급:')
        layout.addWidget(seat_label)
        
        self.seat_combo = QComboBox()
        layout.addWidget(self.seat_combo)

        # 로그 표시 영역
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # 실행 버튼
        self.run_button = QPushButton('티켓팅 시작')
        self.run_button.clicked.connect(self.start_ticketing)
        layout.addWidget(self.run_button)

        main_widget.setLayout(layout)

    def date_selected(self):
        """날짜 선택 시 해당 날짜의 공연 정보 가져오기"""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyyMMdd")
        self.fetch_concerts(date_str)

    def fetch_concerts(self, date_str):
        """선택된 날짜의 공연 정보 크롤링"""
        try:
            # 인터파크 공연 검색 URL (웹페이지 직접 접근)
            url = f"https://ticket.interpark.com/TPGoodsList.asp?Ca=Con&Date={date_str}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
                'Referer': 'https://ticket.interpark.com/'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 공연 목록 찾기 (실제 HTML 구조에 맞게 선택자 수정)
            concert_list = soup.select('.Rk_gen2')
            
            self.concert_combo.clear()
            self.concert_data.clear()
            
            for concert in concert_list:
                try:
                    # 공연 제목과 링크 추출
                    title_elem = concert.select_one('.RKthumb > a')
                    if title_elem:
                        title = title_elem.get('title', '').strip()
                        href = title_elem.get('href', '')
                        
                        # 공연 코드 추출
                        if 'GoodsCode=' in href:
                            code = href.split('GoodsCode=')[1].split('&')[0]
                            
                            if title and code:
                                self.concert_data[title] = {
                                    'code': code,
                                    'seats': self.fetch_seat_grades(code)
                                }
                                self.concert_combo.addItem(title)
                                self.log_display.append(f"공연 추가: {title}")
                                
                except Exception as e:
                    self.logger.error(f"개별 공연 정보 파싱 실패: {str(e)}")
                    continue

            if not self.concert_data:
                self.log_display.append("해당 날짜에 등록된 공연이 없거나 정보를 가져오지 못했습니다.")
            else:
                self.log_display.append(f"{date_str} 날짜의 공연 정보를 불러왔습니다.")
                
        except Exception as e:
            self.log_display.append(f"공연 정보 로딩 실패: {str(e)}")
            self.logger.error(f"공연 정보 로딩 실패: {str(e)}")

    def fetch_seat_grades(self, concert_code):
        """공연의 좌석 등급 정보 가져오기"""
        try:
            url = f"https://ticket.interpark.com/Ticket/Goods/GoodsInfo.asp?GoodsCode={concert_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            seats = {}
            
            # 좌석 등급 정보 추출
            seat_info = soup.select('.SeatDetail')
            for seat in seat_info:
                try:
                    grade = seat.select_one('.GradeType').text.strip()
                    price = seat.select_one('.Price').text.strip()
                    if grade and price:
                        seats[grade] = price
                except Exception as e:
                    self.logger.error(f"좌석 정보 파싱 실패: {str(e)}")
                    continue
                    
            return seats
                
        except Exception as e:
            self.logger.error(f"좌석 정보 로딩 실패: {str(e)}")
            return {}

    def concert_selected(self):
        """콘서트 선택 시 좌석 등급 업데이트"""
        current_concert = self.concert_combo.currentText()
        if current_concert in self.concert_data:
            self.seat_combo.clear()
            for grade in self.concert_data[current_concert]['seats'].keys():
                self.seat_combo.addItem(grade)

    def start_ticketing(self):
        """티켓팅 시작"""
        if not self.validate_inputs():
            return

        try:
            # 브라우저 설정
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 10)

            # 로그인
            self.log_display.append("로그인 시도 중...")
            driver.get('https://ticket.interpark.com/Gate/TPLogin.asp')
            
            # iframe으로 전환
            iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
            driver.switch_to.frame(iframe)
            
            # 로그인 정보 입력
            id_input = wait.until(EC.presence_of_element_located((By.ID, 'userId')))
            pw_input = driver.find_element(By.ID, 'userPwd')
            
            id_input.send_keys(self.id_input.text())
            pw_input.send_keys(self.pw_input.text())
            
            # 로그인 버튼 클릭
            login_btn = driver.find_element(By.ID, 'btn_login')
            login_btn.click()
            
            # 선택된 공연 정보로 이동
            current_concert = self.concert_combo.currentText()
            concert_code = self.concert_data[current_concert]['code']
            
            url = f'http://ticket.interpark.com/Ticket/Goods/GoodsInfo.asp?GoodsCode={concert_code}'
            driver.get(url)
            
            # 여기서 예매 버튼 클릭 및 좌석 선택 로직 구현
            # (실제 구현 시에는 사이트의 구조에 맞게 수정 필요)
            
            self.log_display.append("티켓팅 프로세스 시작...")
            
        except Exception as e:
            self.log_display.append(f"티켓팅 실패: {str(e)}")
            self.logger.error(f"티켓팅 실패: {str(e)}")

    def validate_inputs(self):
        """입력값 검증"""
        if not self.id_input.text() or not self.pw_input.text():
            QMessageBox.warning(self, '경고', '아이디와 비밀번호를 입력해주세요.')
            return False
            
        if not self.concert_combo.currentText():
            QMessageBox.warning(self, '경고', '공연을 선택해주세요.')
            return False
            
        if not self.seat_combo.currentText():
            QMessageBox.warning(self, '경고', '좌석 등급을 선택해주세요.')
            return False
            
        return True

def main():
    app = QApplication(sys.argv)
    ex = TicketingApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()