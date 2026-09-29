import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

# Bảng màu cho CMD
class Colors:
    SUCCESS = "\033[92m"
    ERROR = "\033[91m"
    INFO = "\033[96m"
    WARNING = "\033[93m"
    RESET = "\033[0m"

def type_like_human(element, text):
    """Hàm gõ chữ chậm rãi như người thật để chống Bot"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def start_reg_chrome():
    print(f"{Colors.INFO}Đang khởi tạo Trình duyệt Chrome Ẩn danh (Anti-Detect)...{Colors.RESET}")
    
    # Cấu hình Chrome để lách Bot
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1280,800")
    # Nếu sếp có Proxy, thêm dòng này: options.add_argument('--proxy-server=http://ip:port')
    
    try:
        # Khởi động Chrome
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 15) # Thời gian chờ tối đa 15s cho mỗi hành động
        
        print(f"{Colors.INFO}Truy cập trang đăng ký Instagram...{Colors.RESET}")
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(5)
        
        # Tạo data ảo
        email = f"test_ig_{random.randint(1000, 99999)}@gmail.com"
        full_name = "Huy Vu"
        username = f"huyvu.auto.{random.randint(1000, 99999)}"
        password = "SuperPassword123!@"

        print(f"{Colors.WARNING}Đang điền form đăng ký...{Colors.RESET}")
        
        # Đợi và điền ô Email
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
        type_like_human(email_input, email)
        time.sleep(1)
        
        # Đợi và điền ô Full Name
        name_input = driver.find_element(By.NAME, "fullName")
        type_like_human(name_input, full_name)
        time.sleep(1)
        
        # Đợi và điền ô Username
        user_input = driver.find_element(By.NAME, "username")
        type_like_human(user_input, username)
        time.sleep(2) # Chờ IG check trùng username
        
        # Đợi và điền ô Password
        pass_input = driver.find_element(By.NAME, "password")
        type_like_human(pass_input, password)
        time.sleep(2)

        # Bấm nút Đăng ký (Sign up)
        print(f"{Colors.INFO}Bấm nút Đăng ký...{Colors.RESET}")
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        
        print(f"{Colors.SUCCESS}Đã gửi form! (Đang chờ load sang trang Ngày Sinh / OTP){Colors.RESET}")
        
        # Ngâm trình duyệt 30 giây để sếp xem kết quả trước khi tự đóng
        time.sleep(30)
        
    except Exception as e:
        print(f"{Colors.ERROR}Lỗi hoặc kẹt Checkpoint: {e}{Colors.RESET}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    start_reg_chrome()
