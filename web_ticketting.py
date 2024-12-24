from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import logging
import json

class InterparkTicketing:
    def __init__(self, user_id, user_pw):
        """
        인터파크 티켓팅 자동화 클래스 초기화
        
        Args:
            user_id (str): 인터파크 아이디
            user_pw (str): 인터파크 비밀번호
        """
        self.user_id = user_id
        self.user_pw = user_pw
        self.driver = None
        self.setup_logging()

    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ticketing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """웹드라이버 설정"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.logger.info("웹드라이버 설정 완료")

    def login(self):
        """인터파크 로그인"""
        try:
            self.driver.get('https://ticket.interpark.com/Gate/TPLogin.asp')
            
            # iframe으로 전환
            iframe = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
            self.driver.switch_to.frame(iframe)
            
            # 로그인 정보 입력
            id_input = self.wait.until(EC.presence_of_element_located((By.ID, 'userId')))
            pw_input = self.driver.find_element(By.ID, 'userPwd')
            
            id_input.send_keys(self.user_id)
            pw_input.send_keys(self.user_pw)
            
            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.ID, 'btn_login')
            login_btn.click()
            
            self.logger.info("로그인 성공")
            return True
            
        except Exception as e:
            self.logger.error(f"로그인 실패: {str(e)}")
            return False

    def search_concert(self, concert_code):
        """
        공연 검색 및 예매 페이지 이동
        
        Args:
            concert_code (str): 공연 코드
        """
        try:
            url = f'http://ticket.interpark.com/Ticket/Goods/GoodsInfo.asp?GoodsCode={concert_code}'
            self.driver.get(url)
            self.logger.info(f"공연 페이지 접속: {concert_code}")
            return True
            
        except Exception as e:
            self.logger.error(f"공연 검색 실패: {str(e)}")
            return False

    def select_date(self, target_date):
        """
        공연 날짜 선택
        
        Args:
            target_date (str): 예매하려는 날짜 (YYYYMMDD 형식)
        """
        try:
            date_elements = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "calendar-date-selector")))
            
            for date_element in date_elements:
                if date_element.get_attribute("data-date") == target_date:
                    date_element.click()
                    self.logger.info(f"날짜 선택 완료: {target_date}")
                    return True
                    
            self.logger.warning(f"선택한 날짜를 찾을 수 없음: {target_date}")
            return False
            
        except Exception as e:
            self.logger.error(f"날짜 선택 실패: {str(e)}")
            return False

    def select_seats(self, seat_type):
        """
        좌석 선택
        
        Args:
            seat_type (str): 좌석 등급
        """
        try:
            # 좌석 등급 선택
            seat_buttons = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "seat-grade-button")))
            
            for button in seat_buttons:
                if seat_type in button.text:
                    button.click()
                    self.logger.info(f"좌석 등급 선택 완료: {seat_type}")
                    
                    # 빠른 예매 시도
                    available_seats = self.driver.find_elements(By.CSS_SELECTOR, "available-seat")
                    if available_seats:
                        available_seats[0].click()
                        self.logger.info("좌석 선택 완료")
                        return True
                        
            self.logger.warning("선택 가능한 좌석 없음")
            return False
            
        except Exception as e:
            self.logger.error(f"좌석 선택 실패: {str(e)}")
            return False

    def proceed_payment(self):
        """결제 진행"""
        try:
            # 예매하기 버튼 클릭
            reserve_btn = self.wait.until(EC.element_to_be_clickable((By.ID, 'reserve')))
            reserve_btn.click()
            
            # 결제 방법 선택 (예: 신용카드)
            payment_method = self.wait.until(EC.element_to_be_clickable((By.ID, 'card')))
            payment_method.click()
            
            self.logger.info("결제 페이지 진입 성공")
            return True
            
        except Exception as e:
            self.logger.error(f"결제 진행 실패: {str(e)}")
            return False

    def run_ticketing(self, concert_code, target_date, seat_type):
        """
        티켓팅 전체 프로세스 실행
        
        Args:
            concert_code (str): 공연 코드
            target_date (str): 예매하려는 날짜 (YYYYMMDD 형식)
            seat_type (str): 좌석 등급
        """
        try:
            self.setup_driver()
            
            if not self.login():
                raise Exception("로그인 실패")
                
            if not self.search_concert(concert_code):
                raise Exception("공연 검색 실패")
                
            if not self.select_date(target_date):
                raise Exception("날짜 선택 실패")
                
            if not self.select_seats(seat_type):
                raise Exception("좌석 선택 실패")
                
            if not self.proceed_payment():
                raise Exception("결제 진행 실패")
                
            self.logger.info("티켓팅 프로세스 완료")
            
        except Exception as e:
            self.logger.error(f"티켓팅 실패: {str(e)}")
            
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("웹드라이버 종료")

if __name__ == "__main__":
    # 설정 파일에서 계정 정보 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 티켓팅 봇 실행
    bot = InterparkTicketing(
        user_id=config['user_id'],
        user_pw=config['user_pw']
    )
    
    # 티켓팅 실행
    bot.run_ticketing(
        concert_code=config['concert_code'],
        target_date=config['target_date'],
        seat_type=config['seat_type']
    )