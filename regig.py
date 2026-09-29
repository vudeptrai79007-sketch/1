import os
import time
import threading
import subprocess
import sys
import random
import re
from datetime import datetime
import uuid
import platform
import imaplib
import email
from email.header import decode_header
import json
import traceback

# BIẾN TOÀN CỤC ĐIỀU KHIỂN DỪNG TOOL & KHÓA LUỒNG
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock() # Tránh loạn màn hình khi nhiều thiết bị cùng hỏi OTP
CONFIG_FILE = "config_gmail.json"

# BIẾN TOÀN CỤC CHO THUẬT TOÁN TỊNH TIẾN NĂM SINH
BASE_YEAR = random.randint(1995, 2005)

# ========== BẢNG MÀU GIAO DIỆN TERMINAL (RGB) ==========
class Colors:
    PRIMARY = "\033[38;2;255;100;150m"
    SECONDARY = "\033[38;2;100;200;255m"
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
    
    BANNER1 = "\033[38;2;153;51;255m"
    BANNER2 = "\033[38;2;170;70;255m"
    BANNER3 = "\033[38;2;190;90;255m"
    BANNER4 = "\033[38;2;210;110;240m"
    BANNER5 = "\033[38;2;230;130;220m"
    
    DEVICE_INFO = "\033[38;2;255;200;140m"
    KEY = "\033[38;2;200;160;255m"
    VALUE = "\033[38;2;120;255;220m"
    LINE = "\033[38;2;190;235;210m"
    TITLE = "\033[38;2;255;215;0m"
    NUMBER = "\033[38;2;255;165;0m"
    EMAIL = "\033[38;2;100;200;255m"
    USERNAME = "\033[38;2;0;255;255m"
    PASSWORD = "\033[38;2;255;105;180m"
    RESET = "\033[0m"
    
    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"

# TỰ ĐỘNG CÀI ĐẶT THƯ VIỆN NẾU THIẾU
try:
    import requests
    import uiautomator2 as u2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt thư viện thiếu...', Colors.WARNING)}")
    os.system("pip install requests uiautomator2 numpy opencv-python")
    import requests
    import uiautomator2 as u2

# ========== CÁC HÀM CƠ BẢN VÀ CẤU HÌNH ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.BANNER1} ██░ ██  █    ██  ▓██   ██▓   ██▒   █▓   ▄▀▄  
{Colors.BANNER2}▓██░ ██▒ ██  ▓██▒  ▒██  ██▒  ▓██░   █▒ █    ██ 
{Colors.BANNER3}▒██▀▀██░ ▓██  ▒██░  ▒██ ██░   ▓██  █▒░ ██  ▓██▒
{Colors.BANNER4}░▓█ ░██  ▓▓█  ░██░  ░ ▐██▓░    ▒██ █░░ ▓██  ▒██░
{Colors.BANNER5}░▓█▒░██▓ ▒▒█████▓   ░ ██▒▓░     ▒▀█░   ▓▓█  ░██░
{Colors.RESET}""")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ADMIN: {Colors.VALUE}HUY VŨ   {Colors.DEVICE_INFO}Phiên Bản: {Colors.VALUE}v10.5 (Fix Lỗi Trôi Tụt JS DatePicker){Colors.RESET}")
    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

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
Chế độ:   {mode}
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
            f.write(f"{email}|{password}|{username}|{full_name}|{cookie}\n")
    except Exception:
        pass

def toggle_airplane_mode(serial):
    if STOP_EVENT.is_set():
        return
        
    print(f"\n{Colors.color_text(f'[{serial}] [AUTO ĐẢO IP] Đang Bật/Tắt Chế độ máy bay...', Colors.WARNING)}")
    try:
        subprocess.run(f"adb -s {serial} shell cmd connectivity airplane-mode enable", shell=True)
        print(f"{Colors.color_text(f'[{serial}] Đã BẬT máy bay. Chờ 5s...', Colors.INFO)}")
        time.sleep(5)
        
        subprocess.run(f"adb -s {serial} shell cmd connectivity airplane-mode disable", shell=True)
        print(f"{Colors.color_text(f'[{serial}] Đã TẮT máy bay. Chờ 10s lấy lại sóng 4G...', Colors.INFO)}")
        time.sleep(10)
        
        print(f"{Colors.color_text(f'[{serial}] Đảo IP 4G thành công!', Colors.SUCCESS)}\n")
    except Exception as e:
        print(f"{Colors.color_text(f'[{serial}] Lỗi đổi IP: {e}', Colors.ERROR)}")

# ==================== HÀM INJECT JAVASCRIPT CHỌN NGÀY SINH (ĐÃ FIX LỖI TỤT TRANG) ====================
def inject_birthday_js(d, size, day, month, year):
    # Đã xoá toàn bộ lệnh scrollIntoView phía trong hàm s() để chống nhảy trang web.
    # Chỉ giữ lại đúng 1 nhịp scrollIntoView khung combobox ban đầu.
    js_payload = (
        f"(async function(){{"
        f"async function s(b,t){{"
        f"if(!b)return false;"
        f"b.click();"
        f"await new Promise(r=>setTimeout(r,400));"
        f"const l=Array.from(document.querySelectorAll('*')).filter(e=>e.children.length===0&&(e.innerText?.trim()===String(t)||e.innerText?.trim()==='Tháng '+t));"
        f"if(l.length>0){{"
        f"l[l.length-1].click();await new Promise(r=>setTimeout(r,400));return true;"
        f"}}"
        f"return false;"
        f"}}"
        f"const c=Array.from(document.querySelectorAll('[role=\"combobox\"]'));"
        f"if(c.length>=3){{"
        f"c[0].scrollIntoView({{block:'center'}});"
        f"await s(c[0],{day});await s(c[1],{month});await s(c[2],{year});"
        f"}}"
        f"}})();"
    )

    d.click(size[0] * 0.5, size[1] * 0.05)
    time.sleep(1)

    url_edit = d(className="android.widget.EditText")
    if url_edit.exists(timeout=2):
        url_edit.click()
        time.sleep(0.3)
        d.clear_text()
        time.sleep(0.3)
        d.send_keys("javascript:" + js_payload)
        time.sleep(0.5)
        d.press("enter")
        time.sleep(2)
        return True
    return False

# ==================== DỊCH VỤ MAIL.TM ====================
class MailService:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.domain = None
        self.email_address = None
        
    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10)
            if r.status_code == 200: 
                self.domain = r.json()['hydra:member'][0]['domain']
                return self.domain
        except Exception:
            return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain():
            return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        try:
            r = requests.post(
                f"{self.base_url}/accounts",
                json={"address": f"{name}@{self.domain}", "password": "TempPass123!"},
                timeout=10
            )
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except Exception:
            return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email:
            self.email_address = email
        try:
            r = requests.post(
                f"{self.base_url}/token",
                json={"address": self.email_address, "password": password},
                timeout=10
            )
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception:
            return False
            
    def get_otp_code(self, timeout=120):
        if not self.token:
            return None
        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_id = None
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        if 'Instagram' in msg.get('subject', ''):
                            if msg.get('id') != last_id:
                                last_id = msg['id']
                                detail = requests.get(f"{self.base_url}/messages/{last_id}", headers=headers, timeout=10).json()
                                text = detail.get('text', '') or re.sub('<[^<]+?>', '', str(detail.get('html', '')))
                                match = re.search(r'\b(\d{6})\b', text)
                                if match:
                                    return match.group(1)
            except Exception:
                pass
            time.sleep(5)
        return None

# ==================== DỊCH VỤ GMAIL IMAP ====================
class GmailIMAPService:
    def __init__(self, base_email, app_password):
        self.base_email = base_email
        self.app_password = app_password.replace(" ", "")
        self.mail = None
        self.seen_uids = set()

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.mail.login(self.base_email, self.app_password)
            return True
        except Exception as e:
            print(f"{Colors.color_text(f'Lỗi đăng nhập IMAP cho {self.base_email}: {e}', Colors.ERROR)}")
            return False

    def get_latest_uid(self):
        if not self.mail and not self.connect(): 
            return 0
        try:
            self.mail.select("INBOX", readonly=True)
            status, data = self.mail.uid("search", None, 'ALL')
            if status == "OK" and data[0]:
                uids = data[0].split()
                if uids:
                    return int(uids[-1]) 
        except Exception: 
            pass
        return 0

    def decode_mime(self, value):
        if not value:
            return ""
        parts = decode_header(value)
        out = []
        for text, enc in parts:
            if isinstance(text, bytes):
                try:
                    out.append(text.decode(enc or "utf-8", errors="replace"))
                except Exception:
                    out.append(text.decode("utf-8", errors="replace"))
            else:
                out.append(text)
        return "".join(out)

    def get_text(self, msg):
        plain, html = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    continue
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                
                if ctype == "text/plain":
                    plain.append(text)
                elif ctype == "text/html":
                    html.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain":
                    plain.append(text)
                else:
                    html.append(text)
                    
        if plain:
            return "\n".join(plain).strip()
        if html:
            return re.sub(r'<[^>]+>', ' ', "\n".join(html)).strip()
        return ""

    def get_otp_code(self, target_email, since_uid=0, timeout=120):
        if not self.mail:
            if not self.connect():
                return None
                
        start_time = time.time()
        print(f"{Colors.color_text(f'[HỆ THỐNG MAIL] Đang chờ mail OTP mới...', Colors.INFO)}")
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
                
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    
                    for uid_bytes in reversed(uids[-10:]):
                        try:
                            uid_int = int(uid_bytes)
                        except ValueError:
                            continue
                            
                        if uid_int <= since_uid:
                            continue
                        if uid_bytes in self.seen_uids:
                            continue
                            
                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple): 
                                    raw = item[1]
                                    break
                                    
                            if raw:
                                msg = email.message_from_bytes(raw)
                                subject = self.decode_mime(msg.get("Subject", "")).lower()
                                from_addr = self.decode_mime(msg.get("From", "")).lower()
                                to_addr = self.decode_mime(msg.get("To", "")).lower()
                                
                                if target_email.lower() not in to_addr:
                                    continue
                                    
                                if "instagram" in subject or "instagram" in from_addr:
                                    self.seen_uids.add(uid_bytes) 
                                    body = self.get_text(msg)
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match:
                                        return match.group(1)
            except Exception:
                pass
            time.sleep(5) 
        return None

def generate_dot_variants(gmail):
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

# ==================== DỌN RÁC VÀ TẠO INFO ====================
class AppCleaner:
    def __init__(self, d, serial):
        self.d = d
        self.serial = serial
        self.package_name = "mark.via.gp"

    def clear_via_data(self):
        if STOP_EVENT.is_set():
            return False
        print(f"{Colors.color_text(f'[{self.serial}] ========== DỌN RÁC VIA BROWSER ==========', Colors.TITLE)}")
        
        try:
            self.d.press("recent")
            time.sleep(1.5)
            size = self.d.window_size()
            for _ in range(3): 
                self.d.swipe(size[0]*0.5, size[1]*0.6, size[0]*0.5, size[1]*0.1, duration=0.3)
                time.sleep(0.5)
            self.d.press("home")
            time.sleep(1)
        except Exception:
            pass
        
        self.d.app_stop(self.package_name)
        time.sleep(1.5)
        
        try:
            subprocess.run(
                f"adb -s {self.serial} shell am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{self.package_name}",
                shell=True,
                timeout=8
            )
        except Exception:
            pass
        time.sleep(2.5)
        
        for _ in range(2): 
            self.d.swipe(size[0]*0.5, size[1]*0.8, size[0]*0.5, size[1]*0.3, duration=0.3)
            
        for sel in [{"textMatches": r"(?i).*(storage|dung lượng|bộ nhớ|storage & cache).*"}]:
            if self.d(**sel).exists(timeout=3): 
                self.d(**sel).click()
                break
        else:
            self.d.click(int(size[0]*0.5), int(size[1]*0.6))
        time.sleep(2)
        
        for sel in [{"textMatches": r"(?i).*(clear data|clear storage|xóa dữ liệu|xóa bộ nhớ).*"}]:
            if self.d(**sel).exists(timeout=3): 
                self.d(**sel).click()
                break
        else:
            self.d.click(int(size[0]*0.5), int(size[1]*0.75))
        time.sleep(1.5)
        
        for sel in [{"textMatches": r"(?i)^(ok|yes|delete|xóa|clear|đồng ý|xác nhận)$"}, {"resourceId": "android:id/button1"}]:
            if self.d(**sel).exists(timeout=2): 
                self.d(**sel).click()
                break
        else:
            self.d.press("enter")
        time.sleep(1.5)
        
        return True

def VietnameseNameGenerator():
    first = random.choice(["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Đặng", "Bùi", "Đỗ"])
    middle = random.choice(["Văn", "Thị", "Minh", "Hoàng", "Anh", "Bảo", "Gia", "Khánh", "Ngọc", "Phương"])
    last = random.choice(["An", "Bình", "Cường", "Dũng", "Anh", "Bích", "Chi", "Diệp", "Dung", "Hải", "Hùng"])
    full_name = f"{first} {middle} {last}"
    cleaned = re.sub(r'[^a-zA-Z\s]', '', full_name.lower()).replace(' ', '')
    return full_name, f"{cleaned}_{random.randint(100, 99999)}"

def select_devices():
    try:
        out = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        devices = []
        lines = out.strip().splitlines()[1:]
        for line in lines:
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])
    except Exception:
        devices = []
        
    if not devices:
        print(f"{Colors.color_text('Không tìm thấy thiết bị kết nối PC! Hãy cắm cáp và bật Gỡ lỗi USB.', Colors.ERROR)}")
        sys.exit()
        
    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
    for i, d in enumerate(devices): 
        print(f"{Colors.NUMBER}{i + 1}. {Colors.VALUE}{d}{Colors.RESET}")
    print(f"{Colors.NUMBER}{len(devices) + 1}. {Colors.VALUE}Chạy tất cả thiết bị{Colors.RESET}")
    
    while True:
        try:
            choice = input(f"{Colors.KEY}Chọn thiết bị: {Colors.RESET}")
            c = int(choice)
            if 1 <= c <= len(devices):
                return [devices[c-1]]
            elif c == len(devices) + 1:
                return devices
        except Exception:
            pass

def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm (Tự động lấy OTP) ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Dừng lại nhập PC | Nếu có Mail.tm thì Tự động) ]{Colors.RESET}")
    print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass (Tự động quét IMAP) ]{Colors.RESET}")
    print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể (Tự động quét IMAP) ]{Colors.RESET}")
    
    while True:
        choice = input(f"{Colors.KEY}Nhập lựa chọn [ 1, 2, 3 hoặc 4 ]: {Colors.RESET}").strip()
        if choice in ["1", "2", "3", "4"]:
            return choice

# ==================== MAIN THREAD THI CÔNG TÀI KHOẢN ====================
class starts(threading.Thread):
    def __init__(self, device, mode, account_count, ip_change_freq, data_source, manual_password=None, base_gmail=None, app_password=None):
        super().__init__()
        self.device = device
        self.mode = mode
        self.account_count = account_count
        self.ip_change_freq = ip_change_freq
        self.data_source = data_source
        self.manual_password = manual_password
        self.base_gmail = base_gmail
        self.app_password = app_password
    
    def run(self):
        global BASE_YEAR
        
        def create_one_account(serial, account_index):
            global BASE_YEAR
            
            if STOP_EVENT.is_set(): 
                return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{serial}]  BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email = ""
            imap_service = None
            mail_service = None
            full_name, username = VietnameseNameGenerator()
            
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
            secure_pass = "".join(random.choice(chars) for _ in range(12))

            if self.mode == "1":
                mail_service = MailService()
                used_email = mail_service.create_account(username)
                if not used_email:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Không tạo được Mail.tm!', Colors.ERROR)}")
                    return False
                mail_service.authenticate()
                
            elif self.mode == "2":
                if len(self.data_source) == 0:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết email trong danh sách!', Colors.ERROR)}")
                    return False
                used_email = self.data_source.pop(0)
                if "mail.tm" in used_email.lower():
                    mail_service = MailService()
                    pass_to_use = self.manual_password
                    if not pass_to_use: pass_to_use = "TempPass123!"
                    mail_service.authenticate(used_email, pass_to_use)
                    print(f"{Colors.color_text(f'[{serial}] Nhận diện đuôi Mail.tm, chuyển sang lấy OTP tự động!', Colors.SUCCESS)}")
                
            elif self.mode == "3":
                if len(self.data_source) == 0:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết danh sách Multi-Gmail!', Colors.ERROR)}")
                    return False
                used_email, app_pass = self.data_source.pop(0)
                imap_service = GmailIMAPService(used_email, app_pass)
                
            elif self.mode == "4":
                if len(self.data_source) == 0:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết biến thể Dot Trick!', Colors.ERROR)}")
                    return False
                used_email = self.data_source.pop(0)
                imap_service = GmailIMAPService(self.base_gmail, self.app_password)

            print(f"{Colors.color_text(f'[{serial}] Đang dùng Email: {used_email}', Colors.INFO)}")

            try:
                d = u2.connect(serial)
                try: d.healthcheck()
                except Exception: pass
                
                cleaner = AppCleaner(d, serial)
                if not cleaner.clear_via_data(): return False
                if STOP_EVENT.is_set(): return False
                
                print(f"{Colors.color_text(f'[{serial}] Đang mở Via Browser...', Colors.INFO)}")
                d.app_start("mark.via.gp", stop=True)
                time.sleep(4)
                
                btn_agree = d(textMatches=r"(?i)Đồng ý|Agree|Accept")
                if btn_agree.exists(timeout=2): btn_agree.click()
                    
                btn_skip = d(textMatches=r"(?i)Bỏ qua|Skip")
                if btn_skip.exists(timeout=2): btn_skip.click()

                print(f"{Colors.color_text(f'[{serial}] Đang bật chế độ Trang máy tính...', Colors.INFO)}")
                size = d.window_size()
                d.click(size[0]*0.90, size[1]*0.93)
                time.sleep(1.5)
                
                desktop_btn = d(textMatches=r"(?i).*Trang máy tính.*|.*Desktop.*")
                if desktop_btn.exists(timeout=2): desktop_btn.click()
                else: d.click(size[0]*0.5, size[1]*0.80)
                time.sleep(1.5)
                d.click(size[0]*0.5, size[1]*0.20)

                print(f"{Colors.color_text(f'[{serial}] Đang truy cập Instagram Web...', Colors.INFO)}")
                d.click(size[0]*0.5, size[1]*0.45)
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
                else: return False

                if STOP_EVENT.is_set(): return False

                print(f"{Colors.color_text(f'[{serial}] Đang điền form đăng ký...', Colors.INFO)}")
                time.sleep(3)
                
                email_field = d(textMatches=r"(?i).*email.*")
                if email_field.exists(timeout=2): email_field.click()
                else: 
                    edits = d(className="android.widget.EditText")
                    if edits.exists and edits.count > 0: edits[0].click()
                time.sleep(0.5)
                d.send_keys(used_email)
                time.sleep(1)
                d.press("back")
                time.sleep(1)

                pass_field = d(textMatches=r"(?i).*Mật khẩu.*|.*Password.*")
                if pass_field.exists(timeout=2): pass_field.click()
                else:
                    edits = d(className="android.widget.EditText")
                    if edits.exists and edits.count > 1: edits[1].click()
                    elif edits.exists and edits.count > 0: edits[0].click()
                time.sleep(0.5)
                d.send_keys(secure_pass)
                time.sleep(1)
                d.press("back")
                time.sleep(1.5)

                # ==================== INJECT JS CÓ HỖ TRỢ VUỐT CHỐNG LỖI ====================
                current_year = BASE_YEAR + random.randint(-3, 3)
                if current_year < 1990: current_year = 1990
                if current_year > 2007: current_year = 2007
                current_day = random.randint(2, 28)
                current_month = random.randint(1, 12)
                
                print(f"{Colors.color_text(f'[{serial}] Inject JS chọn Ngày {current_day}, Tháng {current_month}, Năm {current_year}...', Colors.INFO)}")
                js_success = inject_birthday_js(d, size, current_day, current_month, current_year)
                
                if not js_success:
                    print(f"{Colors.color_text(f'[{serial}] JS Inject bị từ chối, kích hoạt Vuốt thủ công dự phòng...', Colors.WARNING)}")
                    
                    d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.4, duration=0.5)
                    time.sleep(1.5)

                    day_btn = d(textMatches=r"(?i)^\s*Ngày\s*$|^\s*Day\s*$")
                    if day_btn.exists(timeout=2):
                        day_btn.click()
                        time.sleep(1.5)
                        target_day = str(current_day)
                        if d(text=target_day).exists(timeout=2): d(text=target_day).click()
                        else: d.click(size[0]*0.25, size[1]*0.4) 
                        time.sleep(1)

                    month_btn = d(textMatches=r"(?i)^\s*Tháng\s*$|^\s*Month\s*$")
                    if month_btn.exists(timeout=2):
                        month_btn.click()
                        time.sleep(1.5)
                        target_month = str(current_month)
                        target_month_text = f"Tháng {current_month}"
                        if d(text=target_month_text).exists(timeout=2): d(text=target_month_text).click()
                        elif d(text=target_month).exists(timeout=2): d(text=target_month).click()
                        else: d.click(size[0]*0.50, size[1]*0.4)
                        time.sleep(1)

                    year_btn = d(textMatches=r"(?i)^\s*Năm\s*$|^\s*Year\s*$")
                    if year_btn.exists(timeout=2):
                        year_btn.click()
                        time.sleep(1.5)
                        print(f"{Colors.color_text(f'[{serial}] Vuốt chậm 3 lần để lấy danh sách năm cũ...', Colors.INFO)}")
                        for _ in range(3):
                            d.swipe(size[0]*0.85, size[1]*0.75, size[0]*0.85, size[1]*0.25, duration=0.8)
                            time.sleep(0.4)
                        target_year_str = str(current_year)
                        if d(text=target_year_str).exists(timeout=2): d(text=target_year_str).click()
                        else: d.click(size[0]*0.85, size[1]*0.5)
                        time.sleep(1)
                
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)
                # ==============================================================================

                d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.5, duration=0.6)
                time.sleep(1.5)

                name_field = d(textMatches=r"(?i).*Tên đầy đủ.*")
                if name_field.exists(timeout=2): name_field.click()
                else: 
                    edits = d(className="android.widget.EditText")
                    if edits.exists and edits.count > 1: edits[-2].click()
                time.sleep(0.5)
                d.send_keys(full_name)
                time.sleep(1)
                d.press("back")
                time.sleep(1.5)

                user_field = d(textMatches=r"(?i).*Tên người dùng.*")
                if user_field.exists(timeout=2): user_field.click()
                else: 
                    edits = d(className="android.widget.EditText")
                    if edits.exists and edits.count > 0: edits[-1].click()
                time.sleep(0.5)
                d.clear_text()
                time.sleep(0.5)
                d.send_keys(username)
                time.sleep(1)
                d.press("back")
                
                print(f"{Colors.color_text(f'[{serial}] Đợi 3s để hệ thống xác nhận username...', Colors.INFO)}")
                time.sleep(3)

                uid_moc = 0
                if self.mode in ["3", "4"] and imap_service:
                    uid_moc = imap_service.get_latest_uid()

                print(f"{Colors.color_text(f'[{serial}] Bấm Gửi/Đăng ký...', Colors.INFO)}")
                d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.5, duration=0.5)
                time.sleep(1)

                submit_btn = d(className="android.widget.Button", textMatches=r"(?i).*Đăng ký.*|.*Sign up.*|.*Gửi.*")
                if submit_btn.exists(timeout=3): 
                    submit_btn.click()
                    print(f"{Colors.color_text(f'[{serial}] Đã click nút Gửi thành công!', Colors.SUCCESS)}")
                else: 
                    print(f"{Colors.color_text(f'[{serial}] Không thấy nút, click tọa độ dự phòng...', Colors.WARNING)}")
                    d.click(size[0]*0.5, size[1]*0.85)

                print(f"{Colors.color_text(f'[{serial}] Đợi 8s load trang xác nhận OTP...', Colors.INFO)}")
                time.sleep(8) 
                
                print(f"{Colors.color_text(f'[{serial}] Đang cuộn màn hình để lộ ô nhập OTP...', Colors.INFO)}")
                d.swipe(size[0]*0.5, size[1]*0.35, size[0]*0.5, size[1]*0.90, duration=0.25)
                time.sleep(1.5)

                otp_input = d(className="android.widget.EditText")
                if not otp_input.exists(timeout=3):
                    d.swipe(size[0]*0.5, size[1]*0.40, size[0]*0.5, size[1]*0.80, duration=0.3)
                    time.sleep(1.5)
                    otp_input = d(className="android.widget.EditText")

                if not otp_input.exists(timeout=5):
                    print(f"{Colors.color_text(f'[{serial}] LỖI: Không chuyển được sang trang OTP. Kẹt nút Gửi hoặc Username bị lỗi. Bỏ qua acc!', Colors.ERROR)}")
                    return False

                otp_code = None
                
                if self.mode == "2" and not (mail_service and mail_service.token):
                    with OTP_LOCK:
                        print(f"\n{Colors.color_text(f'[{serial}] >>> CHẾ ĐỘ 2: ĐÃ RA TRANG OTP! MỜI SẾP NHẬP MÃ TỪ PC <<<', Colors.SUCCESS)}")
                        user_otp = input(f"{Colors.KEY}Nhập mã OTP 6 số vừa gửi đến [{used_email}]: {Colors.RESET}").strip()
                        
                        if not user_otp or len(user_otp) != 6:
                            print(f"{Colors.color_text(f'[{serial}] Mã OTP không hợp lệ! Bỏ qua tài khoản này.', Colors.ERROR)}")
                            return False
                        otp_code = user_otp
                    
                else:
                    print(f"{Colors.color_text(f'[{serial}] Đang tự động quét mã OTP từ hòm thư...', Colors.INFO)}")
                    if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                        otp_code = mail_service.get_otp_code(timeout=120)
                    elif self.mode in ["3", "4"]:
                        otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=120)
                
                if not otp_code:
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Không lấy được mã OTP. Bỏ qua acc!', Colors.ERROR)}")
                    return False

                print(f"{Colors.color_text(f'[{serial}] Đã có mã OTP: {otp_code}. Đang điền vào điện thoại...', Colors.SUCCESS)}")
                otp_input.click()
                time.sleep(0.5)
                d.send_keys(otp_code)
                time.sleep(1.5)
                
                d.click(size[0]*0.1, size[1]*0.3)
                time.sleep(1.5)
                
                next_btn = d(className="android.widget.Button", textMatches=r"(?i).*Tiếp.*|.*Xác nhận.*")
                if next_btn.exists(timeout=3): 
                    next_btn.click()
                else: 
                    d.click(size[0]*0.5, size[1]*0.5)
                    
                soak_time = 20 if self.mode == "2" and not (mail_service and mail_service.token) else random.randint(15, 25)
                print(f"{Colors.color_text(f'[{serial}] Đang ngâm xác thực {soak_time}s...', Colors.WARNING)}")
                time.sleep(soak_time)
                
                print(f"{Colors.color_text(f'[{serial}] Đang chờ thêm 10s để load vào giao diện chính...', Colors.INFO)}")
                time.sleep(10)

                print(f"{Colors.color_text(f'[{serial}] Đang mở menu để lấy Cookie...', Colors.INFO)}")
                cookie = ""
                try:
                    d.click(size[0]*0.1, size[1]*0.08)
                    time.sleep(2)
                    
                    cookie_btn = d(textMatches=r"(?i).*Xem cookie.*")
                    if cookie_btn.exists(timeout=3):
                        cookie_btn.click()
                        time.sleep(2)
                        
                        text_views = d(className="android.widget.TextView")
                        for elem in text_views:
                            content_text = str(elem.get_text())
                            if "csrftoken=" in content_text: 
                                cookie = content_text
                                break
                        d.click(size[0]*0.5, size[1]*0.1)
                except Exception: pass

                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{serial}] DONE ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Mail: {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Pass: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie: {Colors.VALUE}{cookie if cookie else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(serial, used_email, secure_pass, username, full_name, f"mode_{self.mode}", cookie)
                return True
                
            except Exception as e:
                print(f"{Colors.color_text(f'[{serial}] Lỗi ngoại lệ hệ thống: {e}', Colors.ERROR)}")
                traceback.print_exc()
                return False
        
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set():
                print(f"{Colors.color_text(f'[{self.device}] Lệnh dừng được kích hoạt. Đang thoát luồng...', Colors.WARNING)}")
                break
            
            if create_one_account(self.device, i):
                success_count += 1
            
            if i < self.account_count and not STOP_EVENT.is_set():
                if self.ip_change_freq > 0 and i % self.ip_change_freq == 0: 
                    toggle_airplane_mode(self.device)
                else: 
                    time.sleep(random.uniform(5, 10))
        
        print(f"\n{Colors.color_text(f'[{self.device}] TỔNG KẾT: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    banner()
    print(f"{Colors.color_text('MẸO: Bạn có thể ấn tổ hợp phím Ctrl + C bất cứ lúc nào để DỪNG TOOL an toàn.', Colors.WARNING)}\n")
    
    config_data = load_config()
    mode = select_mode()
    
    data_source = []
    base_gmail = None
    app_password = None
    manual_password = None

    if mode == "1":
        print(f"{Colors.color_text('Đã chọn chế độ Tự động Mail.tm!', Colors.SUCCESS)}")
        
    elif mode == "2":
        print(f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}")
        email_input = input(">> ").strip().strip('"').strip("'")
        
        if os.path.isfile(email_input):
            with open(email_input, 'r', encoding='utf-8') as f: 
                for line in f:
                    if line.strip(): data_source.append(line.strip())
        else: 
            raw_emails = email_input.split(",")
            for e in raw_emails:
                if e.strip(): data_source.append(e.strip())
                
        is_mail_tm = False
        for e in data_source:
            if "mail.tm" in e.lower():
                is_mail_tm = True
                break
                
        if is_mail_tm: 
            print(f"{Colors.KEY}Nhận diện list có chứa Mail.tm! Nhập mật khẩu chung cho Mail.tm (Bỏ qua nếu mặc định TempPass123!): {Colors.RESET}")
            manual_password = input(">> ").strip()
            if not manual_password:
                manual_password = "TempPass123!"
                
        print(f"{Colors.color_text(f'Đã tải {len(data_source)} email thủ công.', Colors.SUCCESS)}")

    elif mode == "3":
        print(f"\n{Colors.TITLE}--- CẤU HÌNH NHIỀU GMAIL IMAP ---{Colors.RESET}")
        saved_path = config_data.get("multi_gmail_path", "")
        file_path = ""
        
        if saved_path and os.path.isfile(saved_path):
            print(f"{Colors.KEY}Đã tìm thấy file cũ: {Colors.VALUE}{saved_path}{Colors.RESET}")
            print(f"1. Dùng file cũ")
            print(f"2. Nhập file mới")
            choice = input(f"{Colors.KEY}>> {Colors.RESET}").strip()
            if choice == "1":
                file_path = saved_path
                
        if not file_path:
            print(f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}")
            file_path = input(">> ").strip().strip('"').strip("'")
            config_data["multi_gmail_path"] = file_path
            save_config(config_data)
            
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = re.split(r'[|:]', line.strip())
                    if len(parts) >= 2:
                        data_source.append((parts[0].strip(), parts[1].strip()))
            print(f"{Colors.color_text(f'Đã tải thành công {len(data_source)} Gmail IMAP!', Colors.SUCCESS)}")
        else:
            sys.exit()

    elif mode == "4":
        print(f"\n{Colors.TITLE}--- CẤU HÌNH GMAIL DOT TRICK ---{Colors.RESET}")
        saved_email = config_data.get("dot_trick_email", "")
        saved_pass = config_data.get("dot_trick_app_pass", "")
        
        if saved_email and saved_pass:
            print(f"{Colors.KEY}Đã lưu cấu hình cũ: {Colors.VALUE}{saved_email}{Colors.RESET}")
            print(f"1. Sử dụng file gmail cũ")
            print(f"2. Nhập mới")
            choice = input(f"{Colors.KEY}>> {Colors.RESET}").strip()
            if choice == "1":
                base_gmail = saved_email
                app_password = saved_pass
                
        if not base_gmail:
            print(f"{Colors.KEY}Nhập Gmail gốc (VD: huyvu@gmail.com): {Colors.RESET}")
            base_gmail = input(">> ").strip()
            print(f"{Colors.KEY}Nhập App Password (16 ký tự): {Colors.RESET}")
            app_password = input(">> ").strip()
            
            config_data["dot_trick_email"] = base_gmail
            config_data["dot_trick_app_pass"] = app_password
            save_config(config_data)
            
        data_source = generate_dot_variants(base_gmail)
        print(f"{Colors.color_text(f'Đã tạo ra {len(data_source)} biến thể Dot Trick.', Colors.SUCCESS)}")

    while True:
        try:
            print(f"\n{Colors.KEY}Nhập số lượng tài khoản cần tạo \033[97m[VD: 100]: {Colors.RESET}")
            account_count = int(input(">> ").strip())
            break
        except Exception:
            pass
        
    ip_change_freq = 4
    while True:
        try:
            print(f"{Colors.KEY}Sau bao nhiêu acc thành công thì Đổi IP? (Nhập 0 để Tắt) \033[97m[Mặc định: 4]: {Colors.RESET}")
            freq_str = input(">> ").strip()
            if not freq_str:
                break 
            ip_change_freq = int(freq_str)
            break
        except Exception:
            pass

    devices = select_devices()
    
    if devices:
        try:
            threads = []
            for serial in devices:
                t = starts(serial, mode, account_count, ip_change_freq, data_source.copy(), manual_password, base_gmail, app_password)
                threads.append(t)
                
            for t in threads:
                t.start()
                
            for t in threads:
                t.join()
                
            print(f"\n{Colors.color_text('  AUTO HOÀN THÀNH TOÀN BỘ!  ', Colors.SUCCESS)}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.color_text('!!! PHÁT HIỆN LỆNH DỪNG (CTRL+C) - ĐANG HỦY TIẾN TRÌNH !!!', Colors.ERROR)}")
            STOP_EVENT.set() 
            for t in threads:
                t.join() 
            print(f"{Colors.color_text('Tool đã dừng an toàn.', Colors.SUCCESS)}")
            sys.exit(0)
