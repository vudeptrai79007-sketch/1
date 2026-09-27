import os
import time
import threading
import subprocess
import base64
import sys
import random
import re
from datetime import datetime
from xml.dom.minidom import parse
import json
import uuid
import platform

# ========== CÀI ĐẶT MÀU RGB TOÀN CỤC ==========
class Colors:
    PRIMARY = "\033[38;2;255;100;150m"
    SECONDARY = "\033[38;2;100;200;255m"
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
    DEBUG = "\033[38;2;150;150;255m"
    
    BANNER1 = "\033[38;2;153;51;255m"
    BANNER2 = "\033[38;2;170;70;255m"
    BANNER3 = "\033[38;2;190;90;255m"
    BANNER4 = "\033[38;2;210;110;240m"
    BANNER5 = "\033[38;2;230;130;220m"
    BANNER6 = "\033[38;2;240;150;200m"
    BANNER7 = "\033[38;2;200;200;255m"
    BANNER8 = "\033[38;2;150;230;255m"
    BANNER9 = "\033[38;2;120;255;230m"
    
    DEVICE_INFO = "\033[38;2;255;200;140m"
    KEY = "\033[38;2;200;160;255m"
    VALUE = "\033[38;2;120;255;220m"
    LINE = "\033[38;2;190;235;210m"
    TITLE = "\033[38;2;255;215;0m"
    NUMBER = "\033[38;2;255;165;0m"
    EMAIL = "\033[38;2;100;200;255m"
    USERNAME = "\033[38;2;0;255;255m"
    PASSWORD = "\033[38;2;255;105;180m"
    TIME = "\033[38;2;200;200;200m"
    
    RESET = "\033[0m"
    
    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"

# Cài đặt thư viện tự động
try:
    import requests
    import numpy as np
    import cv2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt thư viện thiếu...', Colors.WARNING)}")
    os.system("pip install numpy requests opencv-python")
    import requests
    import numpy as np
    import cv2

try:
    import uiautomator2 as u2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt uiautomator2...', Colors.WARNING)}")
    os.system("pip install uiautomator2")
    import uiautomator2 as u2

# ========== BANNER VÀ MÀU RGB ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.BANNER1}▄▄▄█████▓ █    ██   ██████    ▄▄▄█████▓ ▒█████   ▒█████   ██▓
{Colors.BANNER2}▓  ██▒ ▓▒ ██  ▓██▒▒██    ▒    ▓  ██▒ ▓▒▒██▒  ██▒▒██▒  ██▒▓██▒
{Colors.BANNER3}▒ ▓██░ ▒░▓██  ▒██░░ ▓██▄      ▒ ▓██░ ▒░▒██░  ██▒▒██░  ██▒▒██░
{Colors.BANNER4}░ ▓██▓ ░ ▓▓█  ░██░  ▒   ██▒   ░ ▓██▓ ░ ▒██   ██░▒██   ██░▒██░
{Colors.BANNER5}  ▒██▒ ░ ▒▒█████▓ ▒██████▒▒     ▒██▒ ░ ░ ████▓▒░░ ████▓▒░░██████▒
{Colors.BANNER6}  ▒ ░░   ░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░     ▒ ░░   ░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░▓  ░
{Colors.BANNER7}    ░    ░░▒░ ░ ░ ░ ░▒  ░ ░       ░      ░ ▒ ▒░   ░ ▒ ▒░ ░ ░ ▒  ░
{Colors.BANNER8}  ░        ░░░ ░ ░ ░  ░  ░        ░      ░ ░ ░ ▒  ░ ░ ░ ▒    ░ ░
{Colors.BANNER9}             ░            ░                  ░ ░      ░ ░      ░  ░
{Colors.RESET}""")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ADMIN: {Colors.VALUE}NHƯ ANH ĐÃ THẤY EM   {Colors.DEVICE_INFO}Phiên Bản: {Colors.VALUE}v6.1 (Nhập Tuần Tự Chuẩn){Colors.RESET}")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Nhóm Telegram: {Colors.VALUE}https://t.me/se_meo_bao_an{Colors.RESET}")
    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}")

    width = 70
    print(f"{Colors.TITLE}{' THÔNG TIN THIẾT BỊ '.center(width)}{Colors.RESET}")
    print(f"{Colors.LINE}{'─'*width}{Colors.RESET}")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Hệ điều hành: {Colors.VALUE}{platform.system()}{Colors.RESET}")

    try:
        info_ip = requests.get("http://ip-api.com/json", timeout=5)
        if info_ip.status_code == 200:
            data = info_ip.json()
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}IP: {Colors.VALUE}{data.get('query')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Khu Vực: {Colors.VALUE}{data.get('regionName')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ISP: {Colors.VALUE}{data.get('isp')}{Colors.RESET}")
            print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Nhà Mạng: {Colors.VALUE}{data.get('org')}{Colors.RESET}")
        else:
            raise Exception()
    except:
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}IP: {Colors.WARNING}Không xác định{Colors.RESET}")
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}Khu Vực: {Colors.WARNING}Không xác định{Colors.RESET}")

    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}")
    print()

def save_account(serial, email, password, username, full_name, mode="auto", cookie=""):
    folder_name = "Instagram_reg"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder_name}/account_{serial.replace(':', '_').replace('.', '_')}_{timestamp}.txt"
    
    content = f"""========================================
THÔNG TIN TÀI KHOẢN INSTAGRAM (WEB)
========================================
Ngày tạo: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Thiết bị: {serial}
Chế độ: {mode}
----------------------------------------
Email:    {email}
Password: {password}
Username: {username}
Họ tên:   {full_name}
Cookie:   {cookie}
----------------------------------------
Định dạng nhanh: {email}|{password}|{username}|{cookie}
========================================
"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        summary_file = f"{folder_name}/ALL_ACCOUNTS.txt"
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"{email}|{password}|{username}|{full_name}|{cookie}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return filename
    except:
        return None

class MailService:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.email_address = None
        self.account_id = None
        self.domain = None
    
    def get_domain(self):
        try:
            response = requests.get(f"{self.base_url}/domains", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('hydra:totalItems', 0) > 0:
                    self.domain = data['hydra:member'][0]['domain']
                    return self.domain
        except:
            pass
        return None

    def create_account(self, address=None):
        if not self.domain:
            self.get_domain()
            if not self.domain:
                raise Exception("Không thể lấy domain từ Mail.tm")
        account_name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        password = "TempPass123!"
        payload = {"address": f"{account_name}@{self.domain}", "password": password}
        try:
            response = requests.post(f"{self.base_url}/accounts", json=payload, timeout=10)
            if response.status_code == 201:
                account_data = response.json()
                self.account_id = account_data['id']
                self.email_address = account_data['address']
                print(f"{Colors.color_text(f'Đã tạo tài khoản email: {self.email_address}', Colors.SUCCESS)}")
                return self.email_address
        except:
            pass
        return None

    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        if not self.email_address: raise Exception("Chưa có địa chỉ email.")
        payload = {"address": self.email_address, "password": password}
        try:
            response = requests.post(f"{self.base_url}/token", json=payload, timeout=10)
            if response.status_code == 200:
                auth_data = response.json()
                self.token = auth_data['token']
                return True
        except:
            pass
        return False

    def get_otp_code(self, timeout=120):
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_message_id = None
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10)
                if response.status_code == 200:
                    messages = response.json().get('hydra:member', [])
                    for msg in messages:
                        subject = msg.get('subject', '')
                        if ('Instagram' in subject or 'security' in subject.lower() or 'code' in subject.lower()):
                            if msg.get('id') != last_message_id:
                                last_message_id = msg['id']
                                detail_response = requests.get(f"{self.base_url}/messages/{msg['id']}", headers=headers, timeout=10)
                                if detail_response.status_code == 200:
                                    email_detail = detail_response.json()
                                    body_text = email_detail.get('text', '')
                                    if not body_text and email_detail.get('html'):
                                        body_text = re.sub('<[^<]+?>', '', email_detail['html'][0] if isinstance(email_detail['html'], list) else email_detail['html'])
                                    otp_match = re.search(r'\b(\d{6})\b', body_text)
                                    if otp_match: return otp_match.group(1)
            except:
                pass
            time.sleep(5)
        return None

class VietnameseNameGenerator:
    def __init__(self):
        self.FIRST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
        self.MIDDLE_NAMES = ["Văn", "Thị", "Minh", "Hoàng", "Anh", "Bảo", "Gia", "Khánh", "Ngọc", "Phương", "Quốc", "Thanh", "Thùy", "Xuân"]
        self.LAST_NAMES_MALE = ["An", "Bình", "Cường", "Dũng", "Đạt", "Đức", "Hải", "Hiếu", "Hùng", "Huy", "Khoa", "Lâm", "Long", "Minh", "Nam", "Phúc", "Quân", "Quang", "Sơn", "Thành", "Thắng", "Tuấn", "Việt", "Vinh"]
        self.LAST_NAMES_FEMALE = ["Anh", "Bích", "Chi", "Diệp", "Dung", "Giang", "Hà", "Hạnh", "Hiền", "Hoa", "Huyền", "Lan", "Linh", "Ly", "Mai", "My", "Nga", "Ngân", "Nhi", "Nhung", "Oanh", "Phương", "Quỳnh", "Thảo", "Trang", "Trinh", "Vân", "Vy"]
    
    def generate_name(self):
        first = random.choice(self.FIRST_NAMES)
        middle = random.choice(self.MIDDLE_NAMES)
        gender = random.choice(['male', 'female'])
        last = random.choice(self.LAST_NAMES_MALE) if gender == 'male' else random.choice(self.LAST_NAMES_FEMALE)
        full_name = f"{first} {middle} {last}".strip()
        cleaned_name = re.sub(r'[^a-zA-Z\s]', '', full_name.lower()).replace(' ', '')
        username = f"{cleaned_name}_{random.randint(10, 9999)}"
        return full_name, username

def generate_secure_password():
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(random.randint(10, 14)))

def wait_for_manual_otp(serial, email_address, timeout=300):
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    print(f"{Colors.color_text(f'[{serial}]  ĐANG CHỜ NHẬP OTP THỦ CÔNG', Colors.WARNING)}")
    print(f"{Colors.KEY} Email: {Colors.EMAIL}{email_address}{Colors.RESET}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            otp_input = input(f"\n{Colors.KEY}>> Nhập mã OTP (6 số) hoặc 'q' để thoát: {Colors.RESET}").strip()
            if otp_input.lower() == 'q': return None
            if otp_input.isdigit() and len(otp_input) == 6:
                return otp_input
        except:
            return None
    return None

def run_adb_command(serial, command, timeout=10):
    try:
        result = subprocess.run(f"adb -s {serial} {command}", shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except:
        return -1, "", "Error"

class ROMDetector:
    def __init__(self, serial):
        self.serial = serial
        self.manufacturer = self._getprop("ro.product.manufacturer")
        self.brand = self._getprop("ro.product.brand")
        self.display_id = self._getprop("ro.build.display.id")
        if not self.manufacturer: self.manufacturer = self.brand

    def _getprop(self, prop):
        try:
            res = subprocess.run(f"adb -s {self.serial} shell getprop {prop}", shell=True, capture_output=True, text=True, timeout=5)
            return res.stdout.strip().lower()
        except:
            return ""

    def is_match(self, *keywords):
        combined = f"{self.manufacturer} {self.brand} {self.display_id}"
        return any(kw.lower() in combined for kw in keywords)

    @property
    def is_xiaomi(self): return self.is_match("xiaomi", "redmi", "poco", "miui", "hyperos")
    @property
    def is_samsung(self): return self.is_match("samsung", "one ui")

# ========== MODULE APP CLEANER (VIA BROWSER) ==========
class AppCleaner:
    def __init__(self, d, serial):
        self.d = d
        self.serial = serial
        self.rom = ROMDetector(serial)
        self.package_name = "mark.via.gp"

    def clear_via_data(self):
        print(f"{Colors.color_text(f'[{self.serial}] ========== DỌN RÁC VIA BROWSER ==========', Colors.TITLE)}")
        self.d.app_stop(self.package_name)
        time.sleep(1.5)

        if not self._goto_app_info(self.package_name):
            self._open_settings_and_search("Via") 
        
        time.sleep(2.5)
        if not self._find_and_click_storage(): return False
        time.sleep(2)
        if not self._find_and_click_clear_data(): return False
        self._handle_confirm_popup()
        time.sleep(1.5)
        return True

    def _goto_app_info(self, package_name):
        try:
            subprocess.run(f"adb -s {self.serial} shell am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{package_name}", shell=True, timeout=8)
            return True
        except:
            return False

    def _open_settings_and_search(self, app_name):
        try:
            self.d.press("home")
            time.sleep(0.5)
            self.d.app_start("com.android.settings")
            time.sleep(2)
            for sel in [{"resourceId": "com.android.settings:id/search_action_bar"}, {"descriptionMatches": r"(?i).*search.*|.*tìm.*"}]:
                try:
                    elem = self.d(**sel)
                    if elem.exists(timeout=2):
                        elem.click()
                        break
                except: continue
            time.sleep(1)
            self.d.send_keys(app_name)
            time.sleep(2)
            for sel in [{"textContains": "Via"}, {"descriptionContains": "Via"}]:
                try:
                    elem = self.d(**sel)
                    if elem.exists(timeout=2):
                        elem.click()
                        time.sleep(2)
                        return
                except: continue
        except:
            pass

    def _find_and_click_storage(self):
        self._scroll_down()
        for sel in [{"textMatches": r"(?i).*(storage|dung lượng|bộ nhớ|storage & cache).*"}]:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=3):
                    elem.click()
                    return True
            except: continue
        self._click_relative(0.5, 0.6)
        return True

    def _find_and_click_clear_data(self):
        self._scroll_down()
        for sel in [{"textMatches": r"(?i).*(clear data|clear storage|xóa dữ liệu|xóa bộ nhớ).*"}]:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=3):
                    elem.click()
                    return True
            except: continue
        self._click_relative(0.5, 0.75)
        return True

    def _handle_confirm_popup(self):
        time.sleep(1.5)
        for sel in [{"textMatches": r"(?i)^(ok|yes|delete|xóa|clear|đồng ý|xác nhận)$"}, {"resourceId": "android:id/button1"}]:
            try:
                elem = self.d(**sel)
                if elem.exists(timeout=2):
                    elem.click()
                    return
            except: continue
        self.d.press("enter")

    def _scroll_down(self):
        try:
            size = self.d.window_size()
            self.d.swipe(size[0]*0.5, size[1]*0.8, size[0]*0.5, size[1]*0.3, duration=0.3)
            time.sleep(1)
        except: pass

    def _click_relative(self, x_percent, y_percent):
        try:
            size = self.d.window_size()
            self.d.click(int(size[0] * x_percent), int(size[1] * y_percent))
        except: pass

class Auto:
    def __init__(self, handle): self.handle = handle
    def Back(self): run_adb_command(self.handle, 'shell input keyevent 3')

def ensure_atx_agent_health(d, serial):
    try: d.healthcheck()
    except:
        try:
            d = u2.connect(serial)
            d.healthcheck()
        except: pass

def GetDevices():
    try:
        output = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        return [line.split("\t")[0] for line in output.strip().splitlines()[1:] if "\tdevice" in line]
    except: return []

def select_devices():
    devices = GetDevices()
    if not devices:
        print(f"{Colors.color_text('Không tìm thấy thiết bị nào đang kết nối!', Colors.ERROR)}")
        return []
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    for i, dev in enumerate(devices): print(f"{Colors.NUMBER}{i + 1}. {Colors.VALUE}{dev}{Colors.RESET}")
    print(f"{Colors.NUMBER}{len(devices) + 1}. {Colors.VALUE}Chạy tất cả thiết bị{Colors.RESET}")
    while True:
        try:
            choice = int(input(f"{Colors.KEY}Nhập lựa chọn: {Colors.RESET}"))
            if 1 <= choice <= len(devices): return [devices[choice-1]]
            elif choice == len(devices) + 1: return devices
        except: print(f"{Colors.color_text('Vui lòng nhập số hợp lệ.', Colors.ERROR)}")

def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN  \033[97m[ Dùng email Mail.tm tự tạo ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY EMAIL & OTP \033[97m[ Dùng email của bạn ]{Colors.RESET}")
    while True:
        choice = input(f"{Colors.KEY}Nhập lựa chọn \033[97m[ 1 hoặc 2 ]: {Colors.RESET}").strip()
        if choice in ["1", "2"]: return "auto" if choice == "1" else "manual"

def select_account_count():
    while True:
        try:
            count = input(f"{Colors.KEY}Nhập số lượng tài khoản \033[97m[ 1-10 ]: {Colors.RESET}").strip()
            return int(count) if count and 1 <= int(count) <= 10 else 1
        except: pass

class starts(threading.Thread):
    def __init__(self, device, mode, manual_emails=None, manual_password=None, account_count=1):
        super().__init__()
        self.device = device
        self.mode = mode
        self.manual_emails = manual_emails if manual_emails else []
        self.manual_password = manual_password
        self.account_count = account_count
    
    def run(self):
        device = self.device
        mode = self.mode
        account_count = self.account_count

        def create_one_account(serial, account_index):
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{serial}]  BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            try:
                d = u2.connect(serial)
                ensure_atx_agent_health(d, serial)
                auto_obj = Auto(serial)

                cleaner = AppCleaner(d, serial)
                cleaner.clear_via_data()
                time.sleep(2)

                print(f"{Colors.color_text(f'[{serial}] Đang mở Via Browser...', Colors.INFO)}")
                d.app_start("mark.via.gp", stop=True)
                time.sleep(4)
                
                if d(textMatches=r"(?i)Đồng ý|Agree|Accept").exists(timeout=3):
                    d(textMatches=r"(?i)Đồng ý|Agree|Accept").click()
                    time.sleep(2)
                if d(textMatches=r"(?i)Bỏ qua|Skip").exists(timeout=2):
                    d(textMatches=r"(?i)Bỏ qua|Skip").click()
                    time.sleep(1)

                print(f"{Colors.color_text(f'[{serial}] Đang bật chế độ Trang máy tính...', Colors.INFO)}")
                try:
                    size = d.window_size()
                    d.click(size[0] * 0.90, size[1] * 0.93)
                    time.sleep(1.5)
                    desktop_btn = d(textMatches=r"(?i).*Trang máy tính.*|.*Desktop.*")
                    if desktop_btn.exists(timeout=2): desktop_btn.click()
                    else: d.click(size[0] * 0.5, size[1] * 0.80)
                    time.sleep(1.5)
                    d.click(size[0] * 0.5, size[1] * 0.20)
                    time.sleep(1)
                except Exception as e:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi khi bật Trang máy tính: {e}', Colors.WARNING)}")

                print(f"{Colors.color_text(f'[{serial}] Đang truy cập Instagram Web...', Colors.INFO)}")
                try:
                    size = d.window_size()
                    d.click(size[0] * 0.5, size[1] * 0.45)
                    time.sleep(1)
                    search_box = d(className="android.widget.EditText")
                    if search_box.exists(timeout=3):
                        search_box.click()
                        time.sleep(0.5)
                        d.clear_text()
                        time.sleep(0.5)
                        d.send_keys("https://www.instagram.com/accounts/emailsignup/")
                        time.sleep(1.5)
                        d.press("enter")
                        print(f"{Colors.color_text(f'[{serial}] Đang đợi tải trang web (10s)...', Colors.INFO)}")
                        time.sleep(10)
                    else:
                        print(f"{Colors.color_text(f'[{serial}] Lỗi: Không tìm thấy ô nhập link!', Colors.ERROR)}")
                        return None
                except Exception as e:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi khi nhập link: {e}', Colors.ERROR)}")
                    return None
                
                mail_service = MailService()
                if mode == "auto":
                    name_gen = VietnameseNameGenerator()
                    full_name, username = name_gen.generate_name()
                    if account_index > 1: username = f"{username}_{account_index}"
                    used_email = mail_service.create_account(address=username)
                    if not used_email: return None
                    mail_service.authenticate()
                else:
                    if self.manual_emails:
                        used_email = random.choice(self.manual_emails)
                        self.manual_emails.remove(used_email)
                    else:
                        print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết email ngẫu nhiên trong danh sách!', Colors.ERROR)}")
                        return None
                        
                    name_gen = VietnameseNameGenerator()
                    full_name, username = name_gen.generate_name()
                    if account_index > 1: username = f"{username}_{account_index}"
                    
                    if "mail.tm" in used_email.lower():
                        mail_service.authenticate(email=used_email, password=self.manual_password or "TempPass123!")

                secure_pass = generate_secure_password()
                print(f"{Colors.color_text(f'[{serial}] Đang điền form đăng ký Web...', Colors.INFO)}")

                # --- PHẦN 3.2: ĐIỀN FORM TRÊN WEB (TUẦN TỰ) ---
                try:
                    time.sleep(3)
                    size = d.window_size()

                    # 1. Điền Email (Ô Nhập Đầu Tiên)
                    print(f"{Colors.color_text(f'[{serial}] Nhập Email...', Colors.INFO)}")
                    email_field = d(textMatches=r"(?i).*di động hoặc email.*|.*email.*")
                    if email_field.exists(timeout=2):
                        email_field.click()
                    else:
                        d(className="android.widget.EditText")[0].click()
                    time.sleep(0.5)
                    d.send_keys(used_email)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1)

                    # 2. Điền Mật khẩu (Ô Nhập Thứ Hai)
                    print(f"{Colors.color_text(f'[{serial}] Nhập Mật khẩu...', Colors.INFO)}")
                    pass_field = d(textMatches=r"(?i).*Mật khẩu.*|.*Password.*")
                    if pass_field.exists(timeout=2):
                        pass_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count > 1: edits[1].click()
                        elif edits.count == 1: edits[0].click()
                    time.sleep(0.5)
                    d.send_keys(secure_pass)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1.5)

                    # Vuốt trang xuống NHẸ NHÀNG để khu vực Ngày Sinh vào giữa màn hình
                    d.swipe(size[0] * 0.5, size[1] * 0.7, size[0] * 0.5, size[1] * 0.4, duration=0.5)
                    time.sleep(1.5)
                    
                    # 3. Chọn Ngày, Tháng, Năm sinh BẰNG TỌA ĐỘ VẬT LÝ TUYỆT ĐỐI
                    print(f"{Colors.color_text(f'[{serial}] Chọn Ngày, Tháng, Năm sinh...', Colors.INFO)}")
                    
                    # === Chọn Ngày (ngẫu nhiên 1 - 5) ===
                    day_box = d(textMatches=r"(?i)^\s*Ngày\s*$|^\s*Day\s*$")
                    if day_box.exists(timeout=2):
                        day_box.click()
                        time.sleep(1.5)
                        d.click(size[0] * 0.25, size[1] * 0.65)
                        time.sleep(1)

                    # === Chọn Tháng (ngẫu nhiên 1 - 5) ===
                    month_box = d(textMatches=r"(?i)^\s*Tháng\s*$|^\s*Month\s*$")
                    if month_box.exists(timeout=2):
                        month_box.click()
                        time.sleep(1.5)
                        d.click(size[0] * 0.50, size[1] * 0.65)
                        time.sleep(1)

                    # === Chọn Năm (ngẫu nhiên 1996 - 2005) ===
                    year_box = d(textMatches=r"(?i)^\s*Năm\s*$|^\s*Year\s*$")
                    if year_box.exists(timeout=2):
                        year_box.click()
                        time.sleep(1.5)
                        for _ in range(4):
                            d.swipe(size[0] * 0.85, size[1] * 0.8, size[0] * 0.85, size[1] * 0.4, duration=1.0)
                            time.sleep(0.5)
                        d.click(size[0] * 0.85, size[1] * 0.65)
                        time.sleep(1)

                    # === VUỐT SIÊU NHẸ ĐỂ HIỆN RÕ 2 Ô TÊN VÀ USERNAME (KHÔNG TRƯỢT XUỐNG ĐÁY) ===
                    d.swipe(size[0] * 0.5, size[1] * 0.7, size[0] * 0.5, size[1] * 0.5, duration=0.6)
                    time.sleep(1.5)

                    # 4. Điền Tên đầy đủ (Ô Nhập Thứ Ba)
                    print(f"{Colors.color_text(f'[{serial}] Nhập Tên đầy đủ...', Colors.INFO)}")
                    name_field = d(textMatches=r"(?i).*Tên đầy đủ.*|.*Họ và tên.*|.*Full name.*")
                    if name_field.exists(timeout=2):
                        name_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count >= 3:
                            edits[2].click() # Ô nhập thứ 3 đếm từ trên xuống
                        elif edits.count > 0:
                            edits[edits.count - 2 if edits.count >= 2 else 0].click()
                    
                    time.sleep(0.5)
                    d.send_keys(full_name)
                    time.sleep(1)
                    d.press("back") # Gập bàn phím
                    time.sleep(1.5)

                    # 5. Điền Username (Ô Nhập Thứ Tư - Cuối cùng)
                    print(f"{Colors.color_text(f'[{serial}] Nhập Username...', Colors.INFO)}")
                    user_field = d(textMatches=r"(?i).*Tên người dùng.*|.*Username.*")
                    if user_field.exists(timeout=2):
                        user_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count >= 4:
                            edits[3].click() # Ô nhập thứ 4 đếm từ trên xuống
                        elif edits.count > 0:
                            edits[edits.count - 1].click() # Ưu tiên lấy ô dưới cùng nếu thiếu
                    
                    time.sleep(0.5)
                    d.clear_text()
                    time.sleep(0.5)
                    d.send_keys(username)
                    time.sleep(1)
                    d.press("back") # Gập bàn phím
                    time.sleep(1.5)

                    # 6. Bấm nút Gửi
                    print(f"{Colors.color_text(f'[{serial}] Bấm Gửi/Đăng ký...', Colors.INFO)}")
                    btn_signup = d(className="android.widget.Button", textMatches=r"(?i).*Đăng ký.*|.*Sign up.*|.*Gửi.*")
                    if btn_signup.exists(timeout=2): 
                        btn_signup.click()
                    else:
                        d.click(size[0] * 0.5, size[1] * 0.85)
                    time.sleep(8)
                except Exception as e:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi điền form: {e}', Colors.ERROR)}")
                    return None

                print(f"{Colors.color_text(f'[{serial}] Đang chờ lấy mã OTP...', Colors.INFO)}")
                otp_code = mail_service.get_otp_code(timeout=120) if mode == "auto" or mail_service.token else None
                if not otp_code: otp_code = wait_for_manual_otp(serial, used_email, timeout=300)
                
                if not otp_code or len(otp_code) != 6: return None
                
                try:
                    otp_input = d(className="android.widget.EditText")
                    if otp_input.exists(timeout=5):
                        otp_input.click()
                        time.sleep(0.5)
                        d.send_keys(otp_code)
                        time.sleep(1.5)
                        
                        d.press("back") 
                        time.sleep(1)
                        
                        btn_confirm = d(className="android.widget.Button", textMatches=r"(?i).*Tiếp.*|.*Next.*|.*Xác nhận.*|.*Confirm.*|.*Gửi.*")
                        if btn_confirm.exists(timeout=3): btn_confirm.click()
                        else:
                            d.swipe(size[0] * 0.5, size[1] * 0.7, size[0] * 0.5, size[1] * 0.5)
                            time.sleep(1)
                            d(className="android.widget.Button").click()
                            
                        print(f"{Colors.color_text(f'[{serial}] Đang chờ 120s (2 phút) để load vào nick...', Colors.WARNING)}")
                        time.sleep(120)
                except: return None

                # --- LẤY COOKIE TỪ VIA BROWSER ---
                print(f"{Colors.color_text(f'[{serial}] Đang mở menu để lấy Cookie...', Colors.INFO)}")
                extracted_cookie = ""
                try:
                    size = d.window_size()
                    d.click(size[0] * 0.1, size[1] * 0.08)
                    time.sleep(1.5)
                    
                    btn_view_cookie = d(text="Xem cookie")
                    if not btn_view_cookie.exists():
                        btn_view_cookie = d(textMatches=r"(?i).*Xem cookie.*")
                        
                    if btn_view_cookie.exists(timeout=3):
                        btn_view_cookie.click()
                        time.sleep(2) 
                        
                        for elem in d(className="android.widget.TextView"):
                            try:
                                text_content = elem.get_text()
                                if text_content and ("csrftoken=" in text_content or "ig_did=" in text_content or "mid=" in text_content):
                                    extracted_cookie = text_content
                                    break
                            except: continue
                                
                        if not extracted_cookie:
                             for elem in d(className="android.widget.EditText"):
                                try:
                                    text_content = elem.get_text()
                                    if text_content and ("csrftoken=" in text_content or "ig_did=" in text_content or "mid=" in text_content):
                                        extracted_cookie = text_content
                                        break
                                except: continue

                        d.press("back")
                        time.sleep(1)
                    else:
                        print(f"{Colors.color_text(f'[{serial}] Không thấy nút Xem cookie.', Colors.WARNING)}")
                except Exception as e:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi khi lấy cookie: {e}', Colors.WARNING)}")

                # --- HOÀN TẤT VÀ LƯU INFO ---
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{serial}]  HOÀN TẤT TÀI KHOẢN THỨ {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Email:    {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Password: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}Username: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie:   {Colors.VALUE}{'Đã lấy thành công' if extracted_cookie else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(serial, used_email, secure_pass, username, full_name, mode, extracted_cookie)
                
                return {"email": used_email, "username": username}
                
            except Exception as e:
                return None
        
        successful_accounts = []
        for i in range(1, account_count + 1):
            result = create_one_account(device, i)
            if result: successful_accounts.append(result)
            if i < account_count: time.sleep(random.uniform(10, 20))
        
        print(f"\n{Colors.color_text(f'[{device}]  TỔNG KẾT: {len(successful_accounts)}/{account_count} THÀNH CÔNG', Colors.TITLE)}")

if __name__ == "__main__":
    banner()
    mode = select_mode()
    manual_emails = []
    manual_password = None
    
    if mode == "manual":
        print(f"{Colors.KEY}Nhập danh sách email (cách nhau bằng dấu phẩy) HOẶC kéo thả file .txt chứa email vào đây:{Colors.RESET}")
        email_input = input(">> ").strip().strip('"').strip("'")
        
        if os.path.isfile(email_input):
            with open(email_input, 'r', encoding='utf-8') as f:
                manual_emails = [line.strip() for line in f if line.strip()]
            print(f"{Colors.color_text(f'Đã tải {len(manual_emails)} email từ file.', Colors.INFO)}")
        else:
            manual_emails = [e.strip() for e in email_input.split(",") if e.strip()]
            if manual_emails:
                with open("saved_emails.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(manual_emails))
                print(f"{Colors.color_text(f'Đã tự động lưu {len(manual_emails)} email này vào file saved_emails.txt', Colors.SUCCESS)}")
        
        if any("mail.tm" in e.lower() for e in manual_emails):
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu (dành cho mail.tm): {Colors.RESET}").strip() or "TempPass123!"
    
    account_count = select_account_count()
    selected_devices = select_devices()
    
    if selected_devices:
        threads = [starts(serial, mode, manual_emails, manual_password, account_count) for serial in selected_devices]
        for t in threads: t.start()
        for t in threads: t.join()
        print(f"\n{Colors.color_text('  HOÀN THÀNH TẤT CẢ!  ', Colors.SUCCESS)}")
