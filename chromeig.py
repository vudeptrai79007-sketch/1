# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import types
import re
if 'distutils' not in sys.modules:
    distutils_mod = types.ModuleType('distutils')
    distutils_version_mod = types.ModuleType('distutils.version')
    class LooseVersion:
        def __init__(self, vstring=None):
            if vstring:
                self.parse(vstring)
        def parse(self, vstring):
            self.vstring = vstring
            component_re = re.compile(r'(\d+)')
            components = [int(x) if x.isdigit() else x for x in component_re.split(vstring) if x and x != '.']
            self.version = components
        def __lt__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version < other_v
        def __le__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version <= other_v
        def __eq__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version == other_v
        def __ne__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version != other_v
        def __gt__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version > other_v
        def __ge__(self, other):
            other_v = other.version if isinstance(other, LooseVersion) else LooseVersion(other).version
            return self.version >= other_v
        def __str__(self):
            return self.vstring
        def __repr__(self):
            return f"LooseVersion ('{self.vstring}')"
    distutils_version_mod.LooseVersion = LooseVersion
    distutils_mod.version = distutils_version_mod
    sys.modules['distutils'] = distutils_mod
    sys.modules['distutils.version'] = distutils_version_mod
# -----------------------------------------------------------------------------------

import os
import time
import threading
import sys
import random
import re
from datetime import datetime
import uuid
import imaplib
import email
from email.header import decode_header
import json
import traceback

# ===== THƯ VIỆN CHROME CHO PC =====
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests
except ImportError:
    print("Đang cài đặt thư viện thiếu...")
    os.system("pip install undetected-chromedriver selenium requests")
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests

# BIẾN TOÀN CỤC
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock() 
DATA_LOCK = threading.Lock()
BROWSER_LOCK = threading.Lock()  # Khóa chống tranh chấp file khi mở đa luồng Chrome
INPUT_LOCK = threading.Lock()    # Khóa chống loạn Terminal khi hỏi y/n
TYPE_LOCK = threading.Lock()     # Khóa gõ phím (chống giật focus làm rớt ký tự khi chạy đa luồng)
CONFIG_FILE = "config_gmail.json"
BASE_YEAR = random.randint(1995, 2005)

# ========== BẢNG MÀU ==========
class Colors:
    PRIMARY = "\033[38;2;255;100;150m"
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
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

# ========== HÀM CƠ BẢN ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.PRIMARY}
 ██████╗ ██╗  ██╗██████╗  ██████╗ ███╗   ███╗███████╗
██╔════╝ ██║  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
██║  ███╗███████║██████╔╝██║   ██║██╔████╔██║█████╗  
██║   ██║██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝    ╚═╝╚══════╝
{Colors.RESET}""")
    print(f"{Colors.INFO}Phiên Bản: v12.31 (GIAO DIỆN MOBILE CHUYÊN NGHIỆP){Colors.RESET}")
    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
    except Exception: pass

def save_account(thread_id, email_str, password, username, full_name, mode="auto", cookie=""):
    folder_name = "Instagram_reg_PC"
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder_name}/account_{thread_id}_{timestamp}.txt"
    
    content = f"""========================================
THÔNG TIN TÀI KHOẢN INSTAGRAM (PC CHROME)
========================================
Ngày tạo: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Luồng:    {thread_id}
Chế độ:   {mode}
----------------------------------------
Email:    {email_str}
Password: {password}
Username: {username}
Họ tên:   {full_name}
Cookie:   {cookie}
----------------------------------------
Định dạng nhanh: {email_str}|{password}|{username}|{cookie}
========================================
"""
    try:
        with open(filename, 'w', encoding='utf-8') as f: f.write(content)
        with open(f"{folder_name}/ALL_ACCOUNTS.txt", 'a', encoding='utf-8') as f: 
            f.write(f"{email_str}|{password}|{username}|{full_name}|{cookie}\n")
    except Exception: pass

def VietnameseNameGenerator():
    first = random.choice(["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Đặng", "Bùi", "Đỗ"])
    middle = random.choice(["Văn", "Thị", "Minh", "Hoàng", "Anh", "Bảo", "Gia", "Khánh", "Ngọc", "Phương"])
    last = random.choice(["An", "Bình", "Cường", "Dũng", "Anh", "Bích", "Chi", "Diệp", "Dung", "Hải", "Hùng"])
    full_name = f"{first} {middle} {last}"
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
    return full_name, f"{cleaned}{random.randint(100, 99999)}"

# ==================== CÁC CLASS XỬ LÝ EMAIL ====================
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
        except Exception: return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10)
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except Exception: return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception: return False
            
    def get_otp_code(self, timeout=120):
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        start_time = time.time()
        last_id = None
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        sub = str(msg.get('subject', '')).lower()
                        frm = str(msg.get('from', {}).get('address', '')).lower()
                        if 'instagram' in sub or 'instagram' in frm:
                            if msg.get('id') != last_id:
                                last_id = msg['id']
                                detail = requests.get(f"{self.base_url}/messages/{last_id}", headers=headers, timeout=10).json()
                                text = detail.get('text', '') or re.sub('<[^<]+?>', '', str(detail.get('html', '')))
                                match = re.search(r'(?<!\d)(\d{6})(?!\d)', text)
                                if match: return match.group(1)
            except Exception: pass
            time.sleep(5)
        return None

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
        if not self.mail and not self.connect(): return 0
        try:
            self.mail.select("INBOX", readonly=True)
            status, data = self.mail.uid("search", None, 'ALL')
            if status == "OK" and data[0]:
                uids = data[0].split()
                if uids: return int(uids[-1]) 
        except Exception: pass
        return 0

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
        if html: return re.sub(r'<[^>]+>', ' ', "\n".join(html)).strip()
        return ""

    def decode_msg_header(self, raw_header):
        if not raw_header: return ""
        try:
            decoded = decode_header(raw_header)
            result = ""
            for text, charset in decoded:
                if isinstance(text, bytes):
                    try: result += text.decode(charset or 'utf-8', errors='replace')
                    except: result += text.decode('utf-8', errors='replace')
                else:
                    result += str(text)
            return result
        except: return str(raw_header)

    def get_otp_code(self, target_email, since_uid=0, timeout=120):
        if not self.mail:
            if not self.connect(): return None
        start_time = time.time()
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    for uid_bytes in reversed(uids[-10:]):
                        try: uid_int = int(uid_bytes)
                        except ValueError: continue
                        if uid_int <= since_uid or uid_bytes in self.seen_uids: continue
                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple): raw = item[1]; break
                            if raw:
                                msg = email.message_from_bytes(raw)
                                to_addr = self.decode_msg_header(msg.get("To", "")).lower()
                                subject = self.decode_msg_header(msg.get("Subject", "")).lower()
                                from_addr = self.decode_msg_header(msg.get("From", "")).lower()
                                
                                if target_email.lower() not in to_addr: continue
                                if "instagram" in subject or "instagram" in from_addr:
                                    self.seen_uids.add(uid_bytes) 
                                    body = self.get_text(msg)
                                    match = re.search(r'(?<!\d)(\d{6})(?!\d)', body)
                                    if match: return match.group(1)
            except Exception: pass
            time.sleep(5) 
        return None

# ==================== DỊCH VỤ HOTMAIL/OUTLOOK API ====================
class HotmailAPIService:
    def __init__(self, data_line, api_mode):
        self.url = "https://smail1s.com/get_messages"
        self.data_line = data_line.strip()
        self.api_mode = api_mode.strip()
        self.email = self.data_line.split('|')[0] if '|' in self.data_line else self.data_line
        self.seen_codes = set()

    def init_baseline(self):
        try:
            payload = {"mode": self.api_mode, "data": self.data_line}
            headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            response = requests.post(self.url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                data_array = response.json().get("data", [])
                if data_array and len(data_array) > 0:
                    messages = data_array[0].get("messages", [])
                    for msg in messages:
                        code_field = str(msg.get("code", "")).strip()
                        if code_field and code_field.isdigit() and len(code_field) == 6:
                            self.seen_codes.add(code_field)
                        else:
                            subject = str(msg.get("subject", "")).lower()
                            match_subj = re.search(r'\b(\d{6})\b', subject)
                            if match_subj: 
                                self.seen_codes.add(match_subj.group(1))
        except Exception: pass

    def get_otp_code(self, timeout=120):
        start_time = time.time()
        print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} (Mode: {self.api_mode})...', Colors.INFO)}")
        
        payload = {
            "mode": self.api_mode,
            "data": self.data_line
        }
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        last_logged = ""
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                response = requests.post(self.url, json=payload, headers=headers, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    data_array = res_json.get("data", [])
                    
                    if data_array and len(data_array) > 0:
                        account_data = data_array[0]
                        err = account_data.get("error")
                        
                        if err:
                            msg_err = f"Lỗi hộp thư: {err}"
                            if msg_err != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = account_data.get("messages", [])
                            msg_info = f"Tìm thấy {len(messages)} thư."
                            if msg_info != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_info} Đang quét mã mới...', Colors.INFO)}")
                                last_logged = msg_info
                                
                            for msg in messages:
                                subject = str(msg.get("subject", "")).lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))
                                code_field = str(msg.get("code", "")).strip()
                                
                                is_ig = ("instagram" in subject) or ("instagram" in from_sender) or ("instagram" in raw_msg.lower())
                                
                                if is_ig:
                                    if code_field and code_field.isdigit() and len(code_field) == 6:
                                        if code_field not in self.seen_codes:
                                            print(f"{Colors.color_text(f'[API Smail1s] Đã tìm thấy mã MỚI: {code_field}', Colors.SUCCESS)}")
                                            return code_field
                                    
                                    match_subj = re.search(r'\b(\d{6})\b', subject)
                                    if match_subj:
                                        code = match_subj.group(1)
                                        if code not in self.seen_codes:
                                            print(f"{Colors.color_text(f'[API Smail1s] Đã tìm thấy mã MỚI: {code}', Colors.SUCCESS)}")
                                            return code
                                            
                                    clean_text = re.sub(r'<[^>]+>', ' ', raw_msg)
                                    match_body = re.search(r'\b(\d{6})\b', clean_text)
                                    if match_body:
                                        code = match_body.group(1)
                                        if code not in self.seen_codes:
                                            print(f"{Colors.color_text(f'[API Smail1s] Đã tìm thấy mã MỚI: {code}', Colors.SUCCESS)}")
                                            return code
                else:
                    status_err = f"Lỗi HTTP {response.status_code}"
                    if status_err != last_logged:
                        print(f"{Colors.color_text(f'[API Smail1s] {status_err}', Colors.WARNING)}")
                        last_logged = status_err
            except Exception as e:
                err_str = f"Lỗi kết nối: {str(e)}"
                if err_str != last_logged:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str}', Colors.WARNING)}")
                    last_logged = err_str
            
            time.sleep(5)
        return None

def generate_dot_variants(gmail):
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com": return [gmail]
    if "." in local: local = local.replace(".", "")
    variants = []
    if local:
        for mask in range(1 << max(0, len(local) - 1)):
            value = local[0]
            for i in range(1, len(local)):
                if mask & (1 << (i - 1)): value += "."
                value += local[i]
            variants.append(value + "@" + domain)
    random.shuffle(variants)
    return variants

# ==================== HÀM HỎI ĐÓNG TRÌNH DUYỆT ====================
def ask_before_close(driver, thread_id):
    if driver:
        with INPUT_LOCK:
            while True:
                choice = input(f"{Colors.WARNING}[{thread_id}] Bạn có muốn đóng Chrome của luồng này không? (y/n): {Colors.RESET}").strip().lower()
                if choice == 'y':
                    try: 
                        driver.quit()
                        print(f"{Colors.SUCCESS}[{thread_id}] Đã đóng trình duyệt và giải phóng RAM.{Colors.RESET}")
                    except: pass
                    break
                elif choice == 'n':
                    print(f"{Colors.INFO}[{thread_id}] Đã giữ lại trình duyệt để bạn kiểm tra.{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.ERROR}Vui lòng chỉ nhập y hoặc n!{Colors.RESET}")

# ==================== HÀM QUẢN LÝ NHẬP FILE VÀ CHỌN DÒNG ====================
def process_file_input(config_key, default_prompt):
    config_data = load_config()
    saved_file = config_data.get(config_key)
    file_path = ""

    if saved_file and os.path.isfile(saved_file):
        print(f"{Colors.INFO}Phát hiện tệp danh sách cũ: {Colors.VALUE}{saved_file}{Colors.RESET}")
        use_old = input(f"{Colors.KEY}Bạn có muốn sử dụng lại tệp này không? (y/n): {Colors.RESET}").strip().lower()
        if use_old == 'y':
            file_path = saved_file

    if not file_path:
        file_path = input(default_prompt).strip().strip('"')
        if os.path.isfile(file_path):
            config_data[config_key] = file_path
            save_config(config_data)

    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        total = len(lines)
        if total == 0:
            print(f"{Colors.ERROR}File trống!{Colors.RESET}")
            return []
            
        print(f"{Colors.SUCCESS}Đã tải {total} dòng từ tệp.{Colors.RESET}")

        start_line = input(f"{Colors.KEY}Bạn muốn chạy TỪ mail số mấy? (Nhấn Enter để chạy từ đầu [1]): {Colors.RESET}").strip()
        end_line = input(f"{Colors.KEY}Bạn muốn chạy ĐẾN mail số mấy? (Nhấn Enter để chạy đến cuối [{total}]): {Colors.RESET}").strip()

        start_idx = int(start_line) if start_line.isdigit() else 1
        end_idx = int(end_line) if end_line.isdigit() else total

        start_idx = max(1, start_idx)
        end_idx = min(total, end_idx)

        if start_idx > end_idx:
            print(f"{Colors.WARNING}Số thứ tự không hợp lệ, sẽ tự động chạy tất cả!{Colors.RESET}")
            return lines
        else:
            selected_lines = lines[start_idx-1:end_idx]
            print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} mail (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
            return selected_lines
    else:
        return [e.strip() for e in file_path.split(",") if e.strip()]


# ==================== MAIN THREAD ====================
class starts(threading.Thread):
    def __init__(self, thread_id, mode, account_count, data_source, manual_password=None, base_gmail=None, app_password=None, api_mode=None):
        super().__init__()
        self.thread_id = f"Tab-{thread_id}"
        self.mode = mode
        self.account_count = account_count
        self.data_source = data_source
        self.manual_password = manual_password 
        self.base_gmail = base_gmail
        self.app_password = app_password
        self.api_mode = api_mode
    
    def run(self):
        global BASE_YEAR
        
        def create_one_account(account_index):
            global BASE_YEAR
            if STOP_EVENT.is_set(): return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{self.thread_id}] BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email = ""
            imap_service = None
            mail_service = None
            hotmail_service = None
            full_name, username = VietnameseNameGenerator()
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
            secure_pass = "".join(random.choice(chars) for _ in range(12))

            if self.mode == "1":
                mail_service = MailService()
                used_email = mail_service.create_account(username)
                if not used_email: return False
                mail_service.authenticate()
                
            elif self.mode == "2":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email = self.data_source.pop(0)
                if "mail.tm" in used_email.lower():
                    mail_service = MailService()
                    pass_to_use = self.manual_password if self.manual_password else "TempPass123!"
                    mail_service.authenticate(used_email, pass_to_use)
                
            elif self.mode == "3":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email, app_pass = self.data_source.pop(0)
                imap_service = GmailIMAPService(used_email, app_pass)
                
            elif self.mode == "4":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email = self.data_source.pop(0)
                imap_service = GmailIMAPService(self.base_gmail, self.app_password)

            elif self.mode == "5":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    data_line = self.data_source.pop(0)
                used_email = data_line.split('|')[0]
                hotmail_service = HotmailAPIService(data_line, self.api_mode)

            print(f"{Colors.color_text(f'[{self.thread_id}] Đang dùng Email: {used_email}', Colors.INFO)}")

            driver = None
            try:
                # ========================================================
                # CÁCH 1: XẾP GẠCH CỬA SỔ & THU NHỎ HIỂN THỊ (SCALE FACTOR)
                # ========================================================
                
                thread_idx = int(self.thread_id.split("-")[1]) - 1 
                
                # --- SỬA THÀNH KÍCH THƯỚC ĐIỆN THOẠI NHỎ VÀ XẾP NGANG MÀN HÌNH ---
                win_width = 380   
                win_height = 700  
                
                columns = 5       
                col = thread_idx % columns
                row = thread_idx // columns
                
                x_pos = col * win_width
                y_pos = row * win_height
                
                options = uc.ChromeOptions()
                options.add_argument('--incognito')
                options.add_argument('--mute-audio')
                options.add_argument('--disable-notifications')
                
                options.add_argument(f'--window-size={win_width},{win_height}')
                options.add_argument(f'--window-position={x_pos},{y_pos}')
                
                # Zoom màn hình xuống 0.7 để Instagram chuyển sang giao diện Mobile thực sự
                options.add_argument('--force-device-scale-factor=0.7')
                
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-dev-shm-usage')
                
                with BROWSER_LOCK:
                    driver = uc.Chrome(options=options)
                    time.sleep(1) 
                # ========================================================
                    
                wait = WebDriverWait(driver, 15)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang truy cập Instagram Web...', Colors.INFO)}")
                driver.get("https://www.instagram.com/accounts/emailsignup/")
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang chờ trang tải hoàn tất (10s)...', Colors.WARNING)}")
                time.sleep(10)
                
                try:
                    cookie_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Cho phép') or contains(text(), 'Đồng ý')]")
                    if cookie_btns:
                        driver.execute_script("arguments[0].click();", cookie_btns[0])
                        time.sleep(2)
                except: pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: current_year = "2005"
                current_day = str(random.randint(2, 28))
                
                # --- SỬA LẠI: TRẢ VỀ DẠNG SỐ ĐỂ KHỚP VỚI "THÁNG X" ---
                current_month = str(random.randint(1, 12))
                
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)

                def slow_scroll_to_element(element):
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(0.5)
                    except: pass

                def human_type(element, text, is_username=False):
                    with TYPE_LOCK:
                        slow_scroll_to_element(element)
                        
                        try: element.click() 
                        except: driver.execute_script("arguments[0].click();", element) 
                        time.sleep(0.5)
                        
                        driver.execute_script("arguments[0].focus();", element)
                        
                        if is_username:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Chờ IG gợi ý Username để tiến hành xóa...', Colors.WARNING)}")
                            time.sleep(2) 
                            element.send_keys(Keys.END)
                            time.sleep(0.2)
                            
                            current_val = element.get_attribute("value")
                            if current_val:
                                for _ in range(len(current_val) + 5):
                                    element.send_keys(Keys.BACKSPACE)
                                    time.sleep(0.01)
                                    
                            driver.execute_script("arguments[0].value = '';", element)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
                            time.sleep(0.5)
                        else:
                            element.send_keys(Keys.CONTROL + "a")
                            time.sleep(0.2)
                            element.send_keys(Keys.BACKSPACE)
                            time.sleep(0.3)
                        
                        for char in text:
                            driver.execute_script("arguments[0].focus();", element)
                            element.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.15)) 
                        time.sleep(random.uniform(0.5, 1.0))
                        
                        try: element.send_keys(Keys.TAB)
                        except: pass

                try:
                    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "input")))
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    
                    if len(inputs) >= 4:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Email...', Colors.INFO)}")
                        human_type(inputs[0], used_email)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Mật khẩu...', Colors.INFO)}")
                        human_type(inputs[1], secure_pass)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu chọn Ngày Sinh bằng Script Console...', Colors.INFO)}")
                        try:
                            wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@role="combobox"]')))
                            driver.set_script_timeout(15)
                            js_script = '''
                            const day = arguments[0];
                            const month = arguments[1];
                            const year = arguments[2];
                            const callback = arguments[arguments.length - 1];

                            (async function() {
                                async function selectComboboxStrict(box, targetText) {
                                    if (!box) return false;
                                    box.scrollIntoView({ block: 'center' });
                                    box.click(); 
                                    await new Promise(r => setTimeout(r, 600)); 
                                    
                                    const targetStr = String(targetText).trim().toLowerCase();

                                    const allElements = Array.from(document.querySelectorAll('div, span, li, option'));
                                    
                                    const matched = allElements.filter(el => {
                                        if (el.offsetHeight === 0 && !el.getClientRects().length) return false;
                                        const txt = el.innerText?.trim().toLowerCase() || "";
                                        return txt === targetStr || txt === "tháng " + targetStr;
                                    });

                                    if (matched.length > 0) {
                                        const targetEl = matched[matched.length - 1];
                                        targetEl.scrollIntoView({ block: 'nearest' });
                                        targetEl.click(); 
                                        await new Promise(r => setTimeout(r, 400)); 
                                        return true;
                                    }

                                    const fallback = allElements.filter(el => {
                                        if (el.offsetHeight === 0 && !el.getClientRects().length) return false;
                                        const txt = el.innerText?.trim().toLowerCase() || "";
                                        return txt.includes(targetStr);
                                    });

                                    if (fallback.length > 0) {
                                        fallback[fallback.length - 1].click();
                                        await new Promise(r => setTimeout(r, 400));
                                        return true;
                                    }

                                    return false;
                                }

                                const comboboxes = Array.from(document.querySelectorAll('[role="combobox"]'));
                                if (comboboxes.length < 3) {
                                    return callback("ERROR: Không tìm thấy 3 ô combobox Ngày/Tháng/Năm!");
                                }

                                await selectComboboxStrict(comboboxes[0], month);
                                await selectComboboxStrict(comboboxes[1], day);
                                await selectComboboxStrict(comboboxes[2], year);

                                callback("SUCCESS");
                            })();
                            '''
                            result = driver.execute_async_script(js_script, current_day, current_month, current_year)
                            if result == "SUCCESS":
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã chạy xong JS chọn: {current_day}/{current_month}/{current_year}', Colors.SUCCESS)}")
                            else:
                                print(f"{Colors.color_text(f'[{self.thread_id}] JS chạy lỗi: {result}', Colors.WARNING)}")
                                
                        except Exception as e:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi tải khối Ngày Sinh (JS): {e}', Colors.ERROR)}")
                            
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Họ Tên...', Colors.INFO)}")
                        human_type(inputs[2], full_name)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Xử lý form Username...', Colors.INFO)}")
                        human_type(inputs[3], username, is_username=True)
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Giao diện IG bị thay đổi!', Colors.ERROR)}")
                        ask_before_close(driver, self.thread_id)
                        return False
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã điền xong. Ngâm form 10s trước khi bấm nút Đăng Ký...', Colors.WARNING)}")
                    time.sleep(10)

                    uid_moc = 0
                    if self.mode in ["3", "4"] and imap_service:
                        uid_moc = imap_service.get_latest_uid()
                    elif self.mode == "5" and hotmail_service:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang quét hộp thư để loại trừ mã cũ...', Colors.INFO)}")
                        hotmail_service.init_baseline()

                    print(f"{Colors.color_text(f'[{self.thread_id}] Cuộn trang xuống cuối để tìm nút Gửi...', Colors.INFO)}")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                    print(f"{Colors.color_text(f'[{self.thread_id}] Click ra ngoài form để kích hoạt Validate...', Colors.INFO)}")
                    driver.execute_script("document.body.click();")
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Chờ form validate (Check Username)... (5s)', Colors.WARNING)}")
                    time.sleep(5)
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang tìm và nhấn nút Gửi/Đăng Ký (Sign up)...', Colors.INFO)}")
                    try:
                        click_result = driver.execute_script("""
                            let submitBtn = document.querySelector('button[type="submit"]');

                            if (!submitBtn) {
                                const allClickables = Array.from(document.querySelectorAll('button, div[role="button"]'));
                                submitBtn = allClickables.find(b => {
                                    const text = (b.innerText || b.textContent || "").trim().toLowerCase();
                                    return text === "submit" || text === "sign up" || text === "đăng ký" || text === "gửi" || text === "next" 
                                        || text.includes("submit") || text.includes("sign up") || text.includes("đăng ký");
                                });
                            }

                            if (!submitBtn) {
                                const spans = Array.from(document.querySelectorAll('span')).filter(s => {
                                    const t = s.innerText?.trim().toLowerCase() || "";
                                    return t === "submit" || t === "sign up" || t === "đăng ký" || t === "gửi" || t === "next";
                                });
                                if (spans.length > 0) {
                                    let p = spans[0].closest('button, div[role="button"]');
                                    if (p) submitBtn = p;
                                }
                            }

                            if (submitBtn) {
                                submitBtn.disabled = false;
                                submitBtn.removeAttribute('disabled');
                                submitBtn.style.pointerEvents = 'auto';
                                submitBtn.scrollIntoView({ block: 'center' });
                                
                                submitBtn.focus();
                                submitBtn.click(); 

                                ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                                    var evt = new MouseEvent(eventType, {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true,
                                        clientX: submitBtn.getBoundingClientRect().x + 20,
                                        clientY: submitBtn.getBoundingClientRect().y + 10
                                    });
                                    submitBtn.dispatchEvent(evt);
                                });
                                
                                return "CLICKED";
                            }
                            
                            const form = document.querySelector('form');
                            if (form) {
                                form.submit();
                                return "FORM_SUBMITTED";
                            }

                            return "NOT_FOUND";
                        """)
                        
                        if click_result in ["CLICKED", "FORM_SUBMITTED"]:
                            print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM NÚT SUBMIT/GỬI THÀNH CÔNG (Bằng Script)!', Colors.SUCCESS)}")
                        else:
                            print(f"{Colors.color_text(f'[{self.thread_id}] JS không tìm thấy, thử click qua Selenium button[type=submit]...', Colors.WARNING)}")
                            try:
                                btn_selenium = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                driver.execute_script("arguments[0].click();", btn_selenium)
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã click nút Submit qua Selenium thành công!', Colors.SUCCESS)}")
                            except:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm thấy nút qua Selenium, fallback phím ENTER...', Colors.WARNING)}")
                                try:
                                    inputs[3].send_keys(Keys.ENTER)
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm ENTER thành công!', Colors.SUCCESS)}")
                                except: pass

                    except Exception as ex:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi khi chạy Script click nút: {ex}', Colors.WARNING)}")
                    
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm gửi form, chờ load OTP (15s)...', Colors.SUCCESS)}")
                    time.sleep(15)
                except Exception as e:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi quá trình điền form: {e}', Colors.ERROR)}")
                    time.sleep(5)
                    ask_before_close(driver, self.thread_id)
                    return False

                # ==================== NHẬN DIỆN Ô NHẬP OTP ĐA LỚP ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ giao diện nhập OTP...', Colors.INFO)}")
                otp_input = None
                locators = [
                    (By.NAME, "email_confirmation_code"),
                    (By.NAME, "confirmationCode"),
                    (By.XPATH, "//input[contains(@aria-label, 'Mã')]"),
                    (By.XPATH, "//input[contains(@aria-label, 'Code')]"),
                    (By.XPATH, "//input[@type='text']")
                ]
                time.sleep(3)
                
                for loc in locators:
                    try:
                        otp_input = WebDriverWait(driver, 3).until(EC.presence_of_element_located(loc))
                        if otp_input: break
                    except: pass
                
                if not otp_input:
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        time.sleep(1)
                        otp_input = driver.execute_script("return document.querySelector('input');")
                    except: pass

                if not otp_input:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể tìm thấy ô nhập OTP trên giao diện.', Colors.ERROR)}")
                    time.sleep(5)
                    ask_before_close(driver, self.thread_id)
                    return False
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đã nhận diện được ô nhập OTP thành công!', Colors.SUCCESS)}")
                
                # ==================== CƠ CHẾ LẤY & NGÂM OTP ====================
                otp_code = None
                start_otp_wait = time.time()
                
                if self.mode == "2" and not (mail_service and mail_service.token):
                    with OTP_LOCK:
                        print(f"\n{Colors.color_text(f'[{self.thread_id}] MỜI SẾP NHẬP OTP CHO [{used_email}] TỪ BÀN PHÍM:', Colors.SUCCESS)}")
                        otp_code = input(">> ").strip()
                else:
                    target_wait = 60 if self.mode in ["3", "4", "5"] else 0
                    if target_wait > 0:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu chu trình quét OTP và ngâm form {target_wait}s...', Colors.INFO)}")
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang chờ lấy mã OTP từ Email...', Colors.INFO)}")

                    if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                        otp_code = mail_service.get_otp_code(timeout=120)
                    elif self.mode in ["3", "4"]:
                        otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=120)
                    elif self.mode == "5":
                        otp_code = hotmail_service.get_otp_code(timeout=120)
                
                if not otp_code:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Quá 120s không lấy được mã OTP. Bỏ qua acc!', Colors.ERROR)}")
                    time.sleep(5)
                    ask_before_close(driver, self.thread_id)
                    return False
                
                if self.mode in ["3", "4", "5"]:
                    elapsed = time.time() - start_otp_wait
                    remaining = target_wait - elapsed
                    if remaining > 0:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã lấy được mã ({otp_code}) ở giây thứ {int(elapsed)}! Đang ngâm form đợi hết {target_wait}s...', Colors.WARNING)}")
                        for w in range(int(remaining), 0, -5):
                            if STOP_EVENT.is_set(): return False
                            print(f"{Colors.color_text(f'[{self.thread_id}] Thời gian ngâm OTP còn lại: {w}s...', Colors.INFO)}")
                            time.sleep(min(5, w))
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã ngâm đủ {target_wait}s. Chuẩn bị điền mã OTP!', Colors.SUCCESS)}")

                # ==================== TIẾN HÀNH ĐIỀN MÃ LÊN WEB ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu điền mã OTP: {otp_code} vào trang Web...', Colors.SUCCESS)}")
                
                try:
                    fresh_input = None
                    for loc in locators:
                        try:
                            els = driver.find_elements(*loc)
                            for el in els:
                                if el.is_displayed():
                                    fresh_input = el
                                    break
                            if fresh_input: break
                        except: pass
                    
                    target_input = fresh_input if fresh_input else otp_input
                    
                    try:
                        human_type(target_input, otp_code)
                    except Exception:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Selenium bị chặn, đang ép điền mã bằng JavaScript...', Colors.WARNING)}")
                        driver.execute_script("""
                            let input = arguments[0];
                            let value = arguments[1];
                            let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                            nativeInputValueSetter.call(input, value);
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        """, target_input, otp_code)
                except Exception as ex:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi nghiêm trọng lúc điền ({ex}), dùng JS quét toàn cục...', Colors.WARNING)}")
                    driver.execute_script("""
                        let input = document.querySelector('input[type="text"], input[name*="code"]');
                        if(input) {
                            let value = arguments[0];
                            let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                            nativeInputValueSetter.call(input, value);
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    """, otp_code)
                    
                time.sleep(1.5)
                
                # --- SỬA LẠI: CLICK NÚT TIẾP TỤC (TỐI ƯU TIẾNG VIỆT) ---
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành Gửi mã OTP...', Colors.INFO)}")
                time.sleep(2)

                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Thử click nút Tiếp tục bằng JavaScript...', Colors.INFO)}")
                    click_result = driver.execute_script("""
                        let submitBtn = document.querySelector('button[type="submit"]');

                        if (!submitBtn) {
                            const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                            submitBtn = btns.find(b => {
                                const text = (b.innerText || b.textContent || "").trim().toLowerCase();
                                return text === "tiếp tục" || text === "xác nhận" || text === "next" || text.includes("tiếp tục") || text.includes("xác nhận");
                            });
                        }

                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.removeAttribute('disabled');
                            submitBtn.focus();
                            submitBtn.click();
                            
                            const events = ['mouseover', 'mousedown', 'mouseup', 'click'];
                            events.forEach(evt => {
                                submitBtn.dispatchEvent(new MouseEvent(evt, {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true,
                                    buttons: 1
                                }));
                            });
                            return "CLICKED";
                        }
                        
                        const form = document.querySelector('form');
                        if (form) {
                            form.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));
                            return "FORM_SUBMITTED";
                        }
                        
                        return "NOT_FOUND";
                    """)
                    if click_result in ["CLICKED", "FORM_SUBMITTED"]:
                        print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM NÚT TIẾP TỤC THÀNH CÔNG (Bằng Script)!', Colors.SUCCESS)}")
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] JS không tìm thấy nút Tiếp tục, thử dùng phím ENTER...', Colors.WARNING)}")
                except Exception as ex:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi click JS: {ex}', Colors.WARNING)}")

                # Phương án cực mạnh: Luôn bồi thêm phím ENTER vào chính ô nhập OTP
                try:
                    target_input.send_keys(Keys.ENTER)
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã bồi thêm phím ENTER vào ô nhập mã!', Colors.SUCCESS)}")
                except:
                    pass

                # ==================== ĐỢI 60s ĐỂ LẤY COOKIE VÀ KIỂM TRA ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ Server IG tạo tài khoản và load trang chủ để lấy cookie (60s)...', Colors.INFO)}")
                time.sleep(60)
                
                # Lấy danh sách cookies từ trình duyệt
                cookies_list = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies_list}
                
                # BƯỚC KIỂM TRA QUAN TRỌNG: NẾU KHÔNG CÓ SESSION ID TỨC LÀ TẠO XỊT
                if not cookie_dict.get('sessionid') or not cookie_dict.get('ds_user_id'):
                    print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                    print(f"{Colors.color_text(f'[{self.thread_id}] LỖI: Tài khoản chưa được tạo (Bị chặn form / sai mã / nút không phản hồi).', Colors.ERROR)}")
                    print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                    ask_before_close(driver, self.thread_id)
                    return False
                
                # Ép chuẩn định dạng chuỗi theo đúng thứ tự yêu cầu
                cookie_str = (
                    f"datr={cookie_dict.get('datr', '')}; "
                    f"ig_did={cookie_dict.get('ig_did', '')}; "
                    f"mid={cookie_dict.get('mid', '')}; "
                    f"wd={cookie_dict.get('wd', '1920x1080')}; "
                    f"dpr={cookie_dict.get('dpr', '1')}; "
                    f"csrftoken={cookie_dict.get('csrftoken', '')}; "
                    f"ds_user_id={cookie_dict.get('ds_user_id', '')}; "
                    f"sessionid={cookie_dict.get('sessionid', '')}; "
                    f"rur={cookie_dict.get('rur', '')}"
                )
                
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Mail: {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Pass: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie: {Colors.VALUE}{cookie_str if cookie_str else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(self.thread_id, used_email, secure_pass, username, full_name, f"mode_{self.mode}", cookie_str)
                
                ask_before_close(driver, self.thread_id)
                return True
                
            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ: {e}', Colors.ERROR)}")
                ask_before_close(driver, self.thread_id)
                return False
        
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set(): break
            if create_one_account(i): success_count += 1
            time.sleep(random.uniform(5, 10))
        
        print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT TAB: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

# ==================== MENU CHÍNH ====================
def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
    print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
    print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
    while True:
        choice = input(f"{Colors.KEY}Nhập lựa chọn [1-5]: {Colors.RESET}").strip()
        if choice in ["1", "2", "3", "4", "5"]: return choice

if __name__ == "__main__":
    banner()
    config_data = load_config()
    mode = select_mode()
    
    data_source = []
    base_gmail = None
    app_password = None
    manual_password = None
    api_mode = None

    if mode == "1":
        pass 
        
    elif mode == "2":
        prompt_txt = f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}"
        data_source = process_file_input("last_file_mode2", prompt_txt)
        if any("mail.tm" in e.lower() for e in data_source):
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}").strip()
            
    elif mode == "3":
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}"
        raw_list = process_file_input("last_file_mode3", prompt_txt)
        for line in raw_list:
            parts = re.split(r'[|:]', line.strip())
            if len(parts) >= 2: data_source.append((parts[0].strip(), parts[1].strip()))
        if not data_source: sys.exit()

    elif mode == "4":
        base_gmail = input(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}").strip()
        app_password = input(f"{Colors.KEY}Nhập App Password: {Colors.RESET}").strip()
        data_source = generate_dot_variants(base_gmail)

    elif mode == "5":
        print("1. OAuth | 2. Graph API | 3. Roundcube")
        c = input(">> ").strip()
        api_mode = "oauth" if c=="1" else "graph" if c=="2" else "roundcube"
        prompt_txt = f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}"
        data_source = process_file_input("last_file_mode5", prompt_txt)

    if not data_source and mode != "1" and mode != "4":
        print(f"{Colors.ERROR}Danh sách đầu vào trống! Thoát chương trình.{Colors.RESET}")
        sys.exit()

    print(f"\n{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc): {Colors.RESET}")
    threads_count = int(input(">> ").strip())
    
    print(f"{Colors.KEY}Nhập số tài khoản cần tạo MỖI LUỒNG: {Colors.RESET}")
    accs_per_thread = int(input(">> ").strip())
    
    threads = []
    for i in range(threads_count):
        t = starts(i+1, mode, accs_per_thread, data_source, manual_password, base_gmail, app_password, api_mode)
        threads.append(t)
        
    for t in threads: t.start()
    
    try:
        for t in threads: t.join()
        print(f"\n{Colors.color_text('AUTO HOÀN THÀNH TOÀN BỘ CÁC LUỒNG!', Colors.SUCCESS)}")
        input(f"{Colors.KEY}Nhấn Enter để thoát chương trình...{Colors.RESET}")
    except KeyboardInterrupt:
        STOP_EVENT.set() 
        print(f"\n{Colors.color_text('Đang đóng các luồng an toàn...', Colors.WARNING)}")
        sys.exit(0)
