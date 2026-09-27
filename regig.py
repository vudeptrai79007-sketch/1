import os
import time
import threading
import subprocess
import base64
import sys
import random
import re
from datetime import datetime
import json
import uuid
import platform
import imaplib
import email
from email.header import decode_header

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
    print(f"""{Colors.BANNER1} ██░ ██  █    ██  ▓██   ██▓   ██▒   █▓   ▄▀▄  
{Colors.BANNER2}▓██░ ██▒ ██  ▓██▒  ▒██  ██▒  ▓██░   █▒ █    ██ 
{Colors.BANNER3}▒██▀▀██░ ▓██  ▒██░  ▒██ ██░   ▓██  █▒░ ██  ▓██▒
{Colors.BANNER4}░▓█ ░██  ▓▓█  ░██░  ░ ▐██▓░    ▒██ █░░ ▓██  ▒██░
{Colors.BANNER5}░▓█▒░██▓ ▒▒█████▓   ░ ██▒▓░     ▒▀█░   ▓▓█  ░██░
{Colors.BANNER6} ▒ ░░▒░▒ ░▒▓▒ ▒ ▒    ██▒▒▒      ░ ▐░   ▒▒█████▓ 
{Colors.BANNER7} ▒ ░▒░ ░ ░░▒░ ░ ░  ▓██ ░▒░      ░ ░░   ░▒▓▒ ▒ ▒ 
{Colors.BANNER8} ░  ░░ ░  ░░░ ░ ░  ▒ ▒ ░░         ░░   ░░▒░ ░ ░ 
{Colors.BANNER9} ░  ░  ░    ░      ░ ░             ░    ░░░ ░ ░ 
{Colors.RESET}""")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ADMIN: {Colors.VALUE}HUY VŨ   {Colors.DEVICE_INFO}Phiên Bản: {Colors.VALUE}v7.0 (VIP IMAP GMAIL){Colors.RESET}")
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
        else:
            raise Exception()
    except:
        print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}IP: {Colors.WARNING}Không xác định{Colors.RESET}")

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

# ========== GMAIL IMAP SERVICE (Tích hợp code gốc của bạn) ==========
class GmailIMAPService:
    def __init__(self, base_email, app_password):
        self.base_email = base_email
        self.app_password = app_password
        self.mail = None
        self.seen_uids = set()

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.mail.login(self.base_email, self.app_password)
            return True
        except Exception as e:
            print(f"{Colors.color_text(f'Lỗi kết nối IMAP Gmail: {e}', Colors.ERROR)}")
            return False

    def decode_mime(self, value):
        if not value: return ""
        parts = decode_header(value)
        out = []
        for text, enc in parts:
            if isinstance(text, bytes):
                try: out.append(text.decode(enc or "utf-8", errors="replace"))
                except: out.append(text.decode("utf-8", errors="replace"))
            else:
                out.append(text)
        return "".join(out)

    def get_text(self, msg):
        plain, html = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment": continue
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)
                if not payload: continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/plain": plain.append(text)
                elif ctype == "text/html": html.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain": plain.append(text)
                else: html.append(text)

        if plain: return "\n".join(plain).strip()
        if html:
            text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", "\n".join(html))
            text = re.sub(r"(?i)<br\s*/?>", "\n", text)
            text = re.sub(r"(?i)</p\s*>", "\n\n", text)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"[ \t]+", " ", text)
            return text.strip()
        return ""

    def get_otp_code(self, target_email, timeout=120):
        if not self.mail:
            if not self.connect(): return None
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    # Quét 5 mail mới nhất
                    for uid in reversed(uids[-5:]):
                        if uid in self.seen_uids: continue
                        
                        status, fetch_data = self.mail.uid("fetch", uid, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple):
                                    raw = item[1]
                                    break
                            if raw:
                                msg = email.message_from_bytes(raw)
                                subject = self.decode_mime(msg.get("Subject", ""))
                                from_addr = self.decode_mime(msg.get("From", ""))
                                to_addr = self.decode_mime(msg.get("To", ""))
                                
                                # Lọc đúng mail Instagram gửi về biến thể hiện tại
                                if "instagram" in subject.lower() or "instagram" in from_addr.lower():
                                    self.seen_uids.add(uid) # Đánh dấu đã đọc
                                    body = self.get_text(msg)
                                    otp_match = re.search(r'\b(\d{6})\b', body)
                                    if otp_match:
                                        return otp_match.group(1)
            except: pass
            time.sleep(5)
        return None

def generate_dot_variants(gmail):
    """Tạo biến thể dấu chấm (Dot trick) từ code gốc của bạn."""
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com":
        return [gmail]
    if "." in local:
        local = local.replace(".", "")
    
    variants = []
    if local:
        for mask in range(1 << max(0, len(local) - 1)):
            value = local[0]
            for i in range(1, len(local)):
                if mask & (1 << (i - 1)):
                    value += "."
                value += local[i]
            variants.append(value + "@" + domain)
    random.shuffle(variants)
    return variants

# ========== MODULE APP CLEANER VÀ CÁC HÀM CŨ GIỮ NGUYÊN ==========
class AppCleaner:
    def __init__(self, d, serial):
        self.d = d
        self.serial = serial
        self.package_name = "mark.via.gp"

    def close_recent_apps(self):
        print(f"{Colors.color_text(f'[{self.serial}] Đóng các ứng dụng chạy ngầm...', Colors.INFO)}")
        try:
            self.d.press("recent")
            time.sleep(1.5)
            size = self.d.window_size()
            for _ in range(3):
                self.d.swipe(size[0] * 0.5, size[1] * 0.6, size[0] * 0.5, size[1] * 0.1, duration=0.3)
                time.sleep(0.5)
            self.d.press("home")
            time.sleep(1)
        except: pass

    def clear_via_data(self):
        print(f"{Colors.color_text(f'[{self.serial}] ========== DỌN RÁC VIA BROWSER ==========', Colors.TITLE)}")
        self.close_recent_apps()
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
        except: return False

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
        except: pass

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
    def Back(self): subprocess.run(f"adb -s {self.handle} shell input keyevent 3", shell=True)

def ensure_atx_agent_health(d, serial):
    try: d.healthcheck()
    except:
        try:
            d = u2.connect(serial)
            d.healthcheck()
        except: pass

class MailService:
    # Class cũ dành cho Mail.tm (Giữ lại cho Mode 1)
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.email_address = None
        self.domain = None
    
    def get_domain(self):
        try:
            response = requests.get(f"{self.base_url}/domains", timeout=10)
            if response.status_code == 200:
                self.domain = response.json()['hydra:member'][0]['domain']
                return self.domain
        except: return None

    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): return None
        account_name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        payload = {"address": f"{account_name}@{self.domain}", "password": "TempPass123!"}
        try:
            response = requests.post(f"{self.base_url}/accounts", json=payload, timeout=10)
            if response.status_code == 201:
                self.email_address = response.json()['address']
                return self.email_address
        except: return None

    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        try:
            response = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10)
            if response.status_code == 200:
                self.token = response.json()['token']
                return True
        except: return False

    def get_otp_code(self, timeout=120):
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_id = None
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10)
                if response.status_code == 200:
                    messages = response.json().get('hydra:member', [])
                    for msg in messages:
                        if 'Instagram' in msg.get('subject', ''):
                            if msg.get('id') != last_id:
                                last_id = msg['id']
                                detail = requests.get(f"{self.base_url}/messages/{last_id}", headers=headers, timeout=10).json()
                                text = detail.get('text', '') or re.sub('<[^<]+?>', '', str(detail.get('html', '')))
                                match = re.search(r'\b(\d{6})\b', text)
                                if match: return match.group(1)
            except: pass
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
        return full_name, f"{cleaned_name}_{random.randint(10, 9999)}"

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
            if otp_input.isdigit() and len(otp_input) == 6: return otp_input
        except: return None
    return None

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
        except: pass

def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm tự tạo ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY EMAIL & OTP  \033[97m[ Dùng email/list txt của bạn ]{Colors.RESET}")
    print(f"{Colors.NUMBER}3. {Colors.VALUE}GMAIL IMAP & DOT TRICK\033[97m[ Tự động quét OTP từ Gmail gốc ]{Colors.RESET}")
    while True:
        choice = input(f"{Colors.KEY}Nhập lựa chọn \033[97m[ 1, 2 hoặc 3 ]: {Colors.RESET}").strip()
        if choice == "1": return "auto"
        elif choice == "2": return "manual"
        elif choice == "3": return "gmail_imap"

class starts(threading.Thread):
    def __init__(self, device, mode, manual_emails=None, manual_password=None, account_count=1, base_gmail=None, app_password=None):
        super().__init__()
        self.device = device
        self.mode = mode
        self.manual_emails = manual_emails if manual_emails else []
        self.manual_password = manual_password
        self.account_count = account_count
        self.base_gmail = base_gmail
        self.app_password = app_password
    
    def run(self):
        device = self.device
        mode = self.mode
        account_count = self.account_count
        
        # Khởi tạo dịch vụ Gmail IMAP sẵn cho Thread này nếu đang ở Mode 3
        imap_service = None
        if mode == "gmail_imap":
            imap_service = GmailIMAPService(self.base_gmail, self.app_password)

        def create_one_account(serial, account_index):
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{serial}]  BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            try:
                d = u2.connect(serial)
                ensure_atx_agent_health(d, serial)
                
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
                except: pass

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
                    else: return None
                except: return None
                
                # --- PHÂN LẠI LUỒNG LẤY EMAIL CHO CẢ 3 CHẾ ĐỘ ---
                used_email = ""
                mail_service = None
                
                name_gen = VietnameseNameGenerator()
                full_name, username = name_gen.generate_name()
                if account_index > 1: username = f"{username}_{account_index}"

                if mode == "auto":
                    mail_service = MailService()
                    used_email = mail_service.create_account(address=username)
                    if not used_email: return None
                    mail_service.authenticate()
                
                elif mode == "manual":
                    if not self.manual_emails:
                        print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết email trong danh sách!', Colors.ERROR)}")
                        return None
                    used_email = random.choice(self.manual_emails)
                    self.manual_emails.remove(used_email)
                    if "mail.tm" in used_email.lower():
                        mail_service = MailService()
                        mail_service.authenticate(email=used_email, password=self.manual_password or "TempPass123!")
                
                elif mode == "gmail_imap":
                    if not self.manual_emails:
                        print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã dùng hết biến thể Gmail!', Colors.ERROR)}")
                        return None
                    used_email = self.manual_emails.pop() # Lấy 1 biến thể từ danh sách đã tạo
                    print(f"{Colors.color_text(f'[{serial}] Đang sử dụng biến thể: {used_email}', Colors.SUCCESS)}")

                secure_pass = generate_secure_password()
                print(f"{Colors.color_text(f'[{serial}] Đang điền form đăng ký Web...', Colors.INFO)}")

                # --- ĐIỀN FORM V6.11 CHUẨN ---
                try:
                    time.sleep(3)
                    size = d.window_size()

                    # 1. Email
                    email_field = d(textMatches=r"(?i).*di động hoặc email.*|.*email.*")
                    if email_field.exists(timeout=2): email_field.click()
                    else: d(className="android.widget.EditText")[0].click()
                    time.sleep(0.5)
                    d.send_keys(used_email)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1)

                    # 2. Mật khẩu
                    pass_field = d(textMatches=r"(?i).*Mật khẩu.*|.*Password.*")
                    if pass_field.exists(timeout=2): pass_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count > 1: edits[1].click()
                        elif edits.count == 1: edits[0].click()
                    time.sleep(0.5)
                    d.send_keys(secure_pass)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1.5)

                    d.swipe(size[0] * 0.5, size[1] * 0.7, size[0] * 0.5, size[1] * 0.4, duration=0.5)
                    time.sleep(1.5)
                    
                    # 3. Ngày, Tháng, Năm
                    day_box = d(textMatches=r"(?i)^\s*Ngày\s*$|^\s*Day\s*$")
                    if day_box.exists(timeout=2):
                        day_box.click()
                        time.sleep(1.5)
                        target_day = d(classNameMatches=".*(?:CheckedTextView|TextView).*", text=str(random.randint(2, 7)))
                        if target_day.exists(timeout=2): target_day.click()
                        else: d.click(size[0] * 0.25, size[1] * 0.4) 
                        time.sleep(1)

                    month_box = d(textMatches=r"(?i)^\s*Tháng\s*$|^\s*Month\s*$")
                    if month_box.exists(timeout=2):
                        month_box.click()
                        time.sleep(1.5)
                        random_m = str(random.randint(2, 7))
                        t1 = d(classNameMatches=".*(?:CheckedTextView|TextView).*", text=f"Tháng {random_m}")
                        t2 = d(classNameMatches=".*(?:CheckedTextView|TextView).*", text=random_m)
                        if t1.exists(timeout=2): t1.click()
                        elif t2.exists(timeout=2): t2.click()
                        else: d.click(size[0] * 0.50, size[1] * 0.4)
                        time.sleep(1)

                    year_box = d(textMatches=r"(?i)^\s*Năm\s*$|^\s*Year\s*$")
                    if year_box.exists(timeout=2):
                        year_box.click()
                        time.sleep(1.5)
                        for _ in range(random.randint(4, 7)):
                            d.swipe(size[0] * 0.85, size[1] * 0.8, size[0] * 0.85, size[1] * 0.4, duration=0.5)
                            time.sleep(0.3)
                        d.click(size[0] * 0.85, size[1] * 0.5)
                        time.sleep(1)

                    d.swipe(size[0] * 0.5, size[1] * 0.7, size[0] * 0.5, size[1] * 0.5, duration=0.6)
                    time.sleep(1.5)

                    # 4. Tên
                    name_field = d(textMatches=r"(?i).*Tên đầy đủ.*|.*Họ và tên.*|.*Full name.*")
                    if name_field.exists(timeout=2): name_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count >= 3: edits[2].click() 
                        elif edits.count > 0: edits[-2 if edits.count >= 2 else 0].click()
                    time.sleep(0.5)
                    d.send_keys(full_name)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1.5)

                    # 5. Username
                    user_field = d(textMatches=r"(?i).*Tên người dùng.*|.*Username.*")
                    if user_field.exists(timeout=2): user_field.click()
                    else:
                        edits = d(className="android.widget.EditText")
                        if edits.count >= 4: edits[3].click() 
                        elif edits.count > 0: edits[-1].click() 
                    time.sleep(0.5)
                    d.clear_text()
                    time.sleep(0.5)
                    d.send_keys(username)
                    time.sleep(1)
                    d.press("back") 
                    time.sleep(1.5)

                    # 6. Gửi
                    print(f"{Colors.color_text(f'[{serial}] Bấm Gửi/Đăng ký...', Colors.INFO)}")
                    btn_signup = d(className="android.widget.Button", textMatches=r"(?i).*Đăng ký.*|.*Sign up.*|.*Gửi.*")
                    if btn_signup.exists(timeout=2): btn_signup.click()
                    else: d.click(size[0] * 0.5, size[1] * 0.85)
                    
                except Exception as e: return None

                # --- ĐỢI VÀ VUỐT TỪ TRÊN XUỐNG DƯỚI LỘ FORM OTP ---
                print(f"{Colors.color_text(f'[{serial}] Đợi 5s load trang, sau đó vuốt từ trên xuống dưới...', Colors.INFO)}")
                time.sleep(5) 
                d.swipe(size[0] * 0.5, size[1] * 0.3, size[0] * 0.5, size[1] * 0.8, duration=0.6)
                time.sleep(1.5)

                # --- XỬ LÝ OTP TÙY THEO CHẾ ĐỘ ---
                print(f"{Colors.color_text(f'[{serial}] Đang chờ lấy mã OTP...', Colors.INFO)}")
                otp_code = None
                
                if mode == "gmail_imap":
                    otp_code = imap_service.get_otp_code(target_email=used_email, timeout=120)
                elif mode == "auto" or (mode == "manual" and mail_service and mail_service.token):
                    otp_code = mail_service.get_otp_code(timeout=120)
                else:
                    otp_code = wait_for_manual_otp(serial, used_email, timeout=300)
                
                if not otp_code or len(otp_code) != 6: 
                    print(f"{Colors.color_text(f'[{serial}] Không tìm thấy OTP. Bỏ qua nick.', Colors.ERROR)}")
                    return None
                
                try:
                    otp_input = d(className="android.widget.EditText")
                    if otp_input.exists(timeout=5):
                        otp_input.click()
                        time.sleep(0.5)
                        d.send_keys(otp_code)
                        time.sleep(1.5)
                        
                        d.click(size[0] * 0.1, size[1] * 0.3) 
                        time.sleep(1.5)
                        
                        btn_confirm = d(className="android.widget.Button", textMatches=r"(?i).*Tiếp.*|.*Next.*|.*Xác nhận.*|.*Confirm.*|.*Gửi.*")
                        if btn_confirm.exists(timeout=3): btn_confirm.click()
                        else: d.click(size[0] * 0.5, size[1] * 0.5)
                        
                        print(f"{Colors.color_text(f'[{serial}] Đang chờ đúng 30s để load vào nick...', Colors.WARNING)}")
                        time.sleep(30)
                except: return None

                # --- LẤY COOKIE ---
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
                                if text_content and ("csrftoken=" in text_content or "ig_did=" in text_content):
                                    extracted_cookie = text_content
                                    break
                            except: continue
                                
                        if not extracted_cookie:
                             for elem in d(className="android.widget.EditText"):
                                try:
                                    text_content = elem.get_text()
                                    if text_content and ("csrftoken=" in text_content or "ig_did=" in text_content):
                                        extracted_cookie = text_content
                                        break
                                except: continue

                        d.click(size[0] * 0.5, size[1] * 0.1)
                        time.sleep(1)
                except: pass

                # --- HOÀN TẤT ---
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{serial}]  HOÀN TẤT TÀI KHOẢN THỨ {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Email:    {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Password: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}Username: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie:   {Colors.VALUE}{extracted_cookie if extracted_cookie else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(serial, used_email, secure_pass, username, full_name, mode, extracted_cookie)
                return {"email": used_email, "username": username}
                
            except Exception: return None
        
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
    base_gmail = None
    app_password = None
    
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
        
        if any("mail.tm" in e.lower() for e in manual_emails):
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu (dành cho mail.tm): {Colors.RESET}").strip() or "TempPass123!"
            
    elif mode == "gmail_imap":
        print(f"\n{Colors.TITLE}--- CẤU HÌNH GMAIL GỐC ---{Colors.RESET}")
        base_gmail = input(f"{Colors.KEY}Nhập Gmail gốc (VD: huyvu@gmail.com): {Colors.RESET}").strip()
        app_password = input(f"{Colors.KEY}Nhập App Password (16 ký tự): {Colors.RESET}").strip().replace(" ", "")
        
        # Gọi hàm tạo biến thể dấu chấm
        manual_emails = generate_dot_variants(base_gmail)
        print(f"{Colors.color_text(f'Đã tự động tạo {len(manual_emails)} biến thể dấu chấm từ {base_gmail}.', Colors.SUCCESS)}")
    
    account_count = select_account_count()
    selected_devices = select_devices()
    
    if selected_devices:
        threads = [starts(serial, mode, manual_emails, manual_password, account_count, base_gmail, app_password) for serial in selected_devices]
        for t in threads: t.start()
        for t in threads: t.join()
        print(f"\n{Colors.color_text('  HOÀN THÀNH TẤT CẢ!  ', Colors.SUCCESS)}")
