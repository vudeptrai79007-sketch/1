# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import socket
import select
import base64
import io
import types
import re
import os
import time
import threading
import random
from datetime import datetime
import uuid
import imaplib
import email
from email.header import decode_header
import json
import traceback
import string
import hashlib

# Tự động cấu hình mã hóa UTF-8 cho Windows Console tránh lỗi UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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

# ===== THƯ VIỆN CHROME CHO PC & PYOTP =====
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp
except ImportError:
    print("Đang cài đặt thư viện thiếu (undetected-chromedriver, requests, pyotp)...")
    os.system("pip install undetected-chromedriver selenium requests pyotp")
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp

# BIẾN TOÀN CỤC & CÁC KHÓA (LOCK)
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock() 
DATA_LOCK = threading.Lock()
BROWSER_LOCK = threading.Lock()  
INPUT_LOCK = threading.Lock()    
TYPE_LOCK = threading.Lock() 
SUBMIT_LOCK = threading.Lock() 
PRINT_LOCK = threading.Lock()
DRIVER_LOCK = threading.Lock()

CONFIG_FILE = "config_gmail.json"
BASE_YEAR = random.randint(1995, 2005)

# Danh sách lưu toàn bộ Trình duyệt để hỏi đóng vào cuối cùng
ALL_DRIVERS = []

# --- CƠ CHẾ ĐÓNG BĂNG MÀN HÌNH CHỐNG TRÔI LỆNH TRONG ĐA LUỒNG ---
built_in_print = print
PAUSE_FOR_INPUT = threading.Event()
PAUSE_FOR_INPUT.set() 

def thread_safe_print(*args, **kwargs):
    PAUSE_FOR_INPUT.wait() 
    with PRINT_LOCK:
        built_in_print(*args, **kwargs)

print = thread_safe_print 

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
    built_in_print(f"""{Colors.PRIMARY}
 ██████╗ ██╗  ██╗██████╗  ██████╗ ███╗   ███╗███████╗
██╔════╝ ██║  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
██║  ███╗███████║██████╔╝██║   ██║██╔████╔██║█████╗  
██║   ██║██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
{Colors.RESET}""")
    built_in_print(f"{Colors.INFO}Phiên Bản: v18.0 (Bản Full Không Rút Gọn - Tích hợp AutoSMS & Retry OTP){Colors.RESET}")
    built_in_print(f"{Colors.LINE}{'─'*70}{Colors.RESET}\n")


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


def save_account(thread_id, email_str, password, username, full_name, mode="auto", cookie="", two_fa=""):
    folder_name = "Instagram_reg_PC"
    if not os.path.exists(folder_name): 
        os.makedirs(folder_name)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder_name}/account_{thread_id}_{timestamp}.txt"
    
    content = f"""========================================
THÔNG TIN TÀI KHOẢN INSTAGRAM (PC CHROME)
========================================
Ngày tạo: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Luồng:    {thread_id}
Chế độ:   {mode}
----------------------------------------
Tài Khoản:{email_str}
Password: {password}
Username: {username}
Họ tên:   {full_name}
2FA Key:  {two_fa if two_fa else 'Không có'}
Cookie:   {cookie}
----------------------------------------
Định dạng nhanh: {email_str}|{password}|{username}|{two_fa}|{cookie}
========================================
"""
    try:
        with open(filename, 'w', encoding='utf-8') as f: 
            f.write(content)
        with open(f"{folder_name}/ALL_ACCOUNTS.txt", 'a', encoding='utf-8') as f: 
            f.write(f"{email_str}|{password}|{username}|{full_name}|{two_fa}|{cookie}\n")
    except Exception: 
        pass


def VietnameseNameGenerator():
    first = random.choice(["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Vu", "Dang", "Bui", "Do"])
    middle = random.choice(["Van", "Thi", "Minh", "Hoang", "Anh", "Bao", "Gia", "Khanh", "Ngoc", "Phuong"])
    last = random.choice(["An", "Binh", "Cuong", "Dung", "Anh", "Bich", "Chi", "Diep", "Dung", "Hai", "Hung"])
    
    full_name = f"{first} {middle} {last}"
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
    
    extra_chars = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=2))
    username = f"{cleaned}{extra_chars}{random.randint(10000, 999999)}"
    
    return full_name, username


# >>> HỆ THỐNG XỬ LÝ PROXY ĐA NĂNG (IP:PORT, IP:PORT:USER:PASS, USER:PASS@IP:PORT) <<<
def parse_proxy(proxy_str):
    if not proxy_str:
        return None
        
    p_str = str(proxy_str).strip()
    if not p_str:
        return None
        
    for proto in ["http://", "https://", "socks5://", "socks4://"]:
        if p_str.lower().startswith(proto):
            p_str = p_str[len(proto):]
            break

    # TH 1: user:pass@ip:port
    if "@" in p_str:
        try:
            auth_part, host_part = p_str.split("@", 1)
            u, pwd = auth_part.split(":", 1)
            ip, port = host_part.split(":", 1)
            return {"ip": ip.strip(), "port": port.strip(), "user": u.strip(), "pass": pwd.strip()}
        except Exception:
            pass

    # TH 2: Dấu hai chấm ':'
    parts = [x.strip() for x in p_str.split(":") if x.strip()]
    if len(parts) == 2:
        return {"ip": parts[0], "port": parts[1], "user": None, "pass": None}
    elif len(parts) == 4:
        if parts[1].isdigit() and not parts[2].isdigit():
            return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
        elif parts[3].isdigit():
            return {"ip": parts[2], "port": parts[3], "user": parts[0], "pass": parts[1]}
        else:
            return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
            
    return None


def format_proxy(proxy_str):
    parsed = parse_proxy(proxy_str)
    if not parsed:
        return None
    if parsed["user"] and parsed["pass"]:
        formatted = f"http://{parsed['user']}:{parsed['pass']}@{parsed['ip']}:{parsed['port']}"
    else:
        formatted = f"http://{parsed['ip']}:{parsed['port']}"
    return {"http": formatted, "https": formatted}


class LocalProxyForwarder:
    def __init__(self, remote_ip, remote_port, username=None, password=None):
        self.remote_ip = remote_ip
        self.remote_port = int(remote_port)
        self.username = username
        self.password = password
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', 0))
        self.local_port = self.server_socket.getsockname()[1]
        self.running = True
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.server_socket.listen(100)
        while self.running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_sock):
        try:
            crlf2 = bytes([13, 10, 13, 10])
            crlf = bytes([13, 10])
            req = b""
            while crlf2 not in req:
                chunk = client_sock.recv(4096)
                if not chunk:
                    client_sock.close()
                    return
                req += chunk

            header_part, rest = req.split(crlf2, 1)
            lines = header_part.split(crlf)
            first_line = lines[0].decode("utf-8", "ignore")
            is_connect = first_line.startswith("CONNECT")

            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(15)
            remote_sock.connect((self.remote_ip, self.remote_port))

            auth_header = b""
            if self.username and self.password:
                cred = f"{self.username}:{self.password}"
                b64_cred = base64.b64encode(cred.encode()).decode()
                auth_header = f"Proxy-Authorization: Basic {b64_cred}".encode() + crlf

            if is_connect:
                connect_req = lines[0] + crlf
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization"):
                        connect_req += line + crlf
                        
                if auth_header:
                    connect_req += auth_header
                connect_req += crlf
                remote_sock.sendall(connect_req)

                resp = b""
                while crlf2 not in resp:
                    c = remote_sock.recv(4096)
                    if not c:
                        break
                    resp += c

                resp_first_line = resp.split(crlf)[0] if resp else b""
                
                if b"200" in resp_first_line:
                    client_sock.sendall(b"HTTP/1.1 200 Connection established" + crlf2)
                else:
                    client_sock.sendall(resp)
                    client_sock.close()
                    remote_sock.close()
                    return
            else:
                new_req = lines[0] + crlf
                for line in lines[1:]:
                    if not line.lower().startswith(b"proxy-authorization"):
                        new_req += line + crlf
                        
                if auth_header:
                    new_req += auth_header
                new_req += crlf + rest
                remote_sock.sendall(new_req)

            remote_sock.settimeout(None)
            client_sock.settimeout(None)
            sockets = [client_sock, remote_sock]
            
            while self.running:
                r, _, _ = select.select(sockets, [], sockets, 30)
                if not r:
                    break
                for s in r:
                    other = remote_sock if s is client_sock else client_sock
                    data = s.recv(16384)
                    if not data:
                        return
                    other.sendall(data)
                    
        except Exception:
            pass
        finally:
            try: 
                client_sock.close()
            except: 
                pass
            try: 
                remote_sock.close()
            except: 
                pass

    def close(self):
        self.running = False
        try: 
            self.server_socket.close()
        except: 
            pass


# ==================== CLASS API AUTOSMS THUÊ SIM ====================
class AutoSMS_Service:
    def __init__(self, api_key, country="vn", proxy=None):
        self.base_url = "https://autosms.site"
        self.api_key = api_key
        self.country = country
        self.service_id = "instagram"
        self.current_order_id = None
        self.current_phone = None
        self.proxy = proxy

    def get_balance(self):
        try:
            url = f"{self.base_url}/api/balance?key={self.api_key}"
            resp = requests.get(url, timeout=10, proxies=self.proxy)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data["data"]["balance"]
        except Exception as e: 
            print(f"Lỗi khi check số dư AutoSMS: {e}")
        return None

    def buy_number(self):
        try:
            url = f"{self.base_url}/api/buy-number/{self.country}/{self.service_id}?key={self.api_key}"
            resp = requests.get(url, timeout=15, proxies=self.proxy)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    self.current_phone = str(data["data"]["phone"])
                    self.current_order_id = str(data["data"]["order_id"])
                    return self.current_phone
        except Exception as e:
            print(f"Lỗi API Mua Số AutoSMS: {e}")
        return None

    def get_otp(self, timeout=120):
        if not self.current_order_id: 
            return None
            
        start = time.time()
        
        while time.time() - start < timeout:
            if STOP_EVENT.is_set(): 
                return None
            try:
                url = f"{self.base_url}/api/orders/{self.current_order_id}?key={self.api_key}"
                resp = requests.get(url, timeout=10, proxies=self.proxy)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        otp = data["data"].get("code")
                        if otp and str(otp).strip() != "" and str(otp).lower() != "null":
                            return str(otp).strip()
            except Exception: 
                pass
                
            time.sleep(5)
            
        return None

    def cancel_order(self):
        if not self.current_order_id: 
            return False
            
        try:
            url = f"{self.base_url}/api/cancel/{self.current_order_id}?key={self.api_key}"
            resp = requests.get(url, timeout=10, proxies=self.proxy)
            if resp.status_code == 200:
                return True
        except: 
            pass
            
        return False


# ==================== CÁC CLASS XỬ LÝ EMAIL ====================
class MailService:
    def __init__(self, proxy=None):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.domain = None
        self.email_address = None
        self.seen_msg_ids = set() 
        self.proxy = proxy 
        
    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10, proxies=self.proxy)
            if r.status_code == 200: 
                self.domain = r.json()['hydra:member'][0]['domain']
                return self.domain
        except Exception: 
            return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): 
            return None
            
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        time.sleep(random.uniform(0.5, 2.0))
        
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10, proxies=self.proxy)
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except Exception: 
            return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: 
            self.email_address = email
            
        time.sleep(random.uniform(0.5, 2.0)) 
        
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10, proxies=self.proxy)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception: 
            return False
            
    def get_otp_code(self, timeout=120, force_8_digits=False):
        if not self.token: 
            return None
            
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        start_time = time.time()
        time.sleep(random.uniform(1.0, 5.0))
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): 
                return None
                
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10, proxies=self.proxy)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        msg_id = msg.get('id')
                        if not msg_id or msg_id in self.seen_msg_ids: 
                            continue
                            
                        subject = str(msg.get('subject', '')).lower()
                        frm = str(msg.get('from', {}).get('address', '')).lower()
                        
                        if 'instagram' in subject or 'instagram' in frm:
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or re.sub('<[^<]+?>', ' ', str(detail.get('html', '')))
                            
                            code = None
                            if force_8_digits:
                                clean_txt = raw_text.replace(" ", "")
                                match = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_txt)
                                if match: 
                                    code = match.group(1)
                            else:
                                match_sub = re.search(r'(?<!\d)(\d{6})(?!\d)', subject)
                                if match_sub: 
                                    code = match_sub.group(1)
                                else:
                                    safe_text = raw_text.lower().replace(str(self.email_address).lower(), "")
                                    match_body = re.search(r'(?<!\d)(\d{6})(?!\d)', safe_text.replace(" ", ""))
                                    if match_body: 
                                        code = match_body.group(1)

                            if code:
                                self.seen_msg_ids.add(msg_id)
                                return code
            except Exception: 
                pass
                
            time.sleep(random.uniform(6.0, 10.0))
            
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

    def get_text(self, msg):
        plain = []
        html = []
        
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

    def decode_msg_header(self, raw_header):
        if not raw_header: 
            return ""
            
        try:
            decoded = decode_header(raw_header)
            result = ""
            for text, charset in decoded:
                if isinstance(text, bytes):
                    try: 
                        result += text.decode(charset or 'utf-8', errors='replace')
                    except: 
                        result += text.decode('utf-8', errors='replace')
                else:
                    result += str(text)
            return result
        except: 
            return str(raw_header)

    def get_otp_code(self, target_email, since_uid=0, timeout=120, force_8_digits=False):
        if not self.mail:
            if not self.connect(): 
                return None
                
        start_time = time.time()
        time.sleep(random.uniform(1.0, 5.0))
        
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
                            
                        if uid_int <= since_uid or uid_bytes in self.seen_uids: 
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
                                to_addr = self.decode_msg_header(msg.get("To", "")).lower()
                                subject = self.decode_msg_header(msg.get("Subject", "")).lower()
                                from_addr = self.decode_msg_header(msg.get("From", "")).lower()
                                
                                if target_email.lower() not in to_addr: 
                                    continue
                                
                                is_ig = "instagram" in subject or "instagram" in from_addr
                                is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã"])
                                
                                if is_ig and is_security_mail:
                                    body = self.get_text(msg)
                                    code = None
                                    
                                    if force_8_digits:
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', body.replace(" ", ""))
                                        if match_8: 
                                            code = match_8.group(1)
                                    else:
                                        match_sub = re.search(r'(?<!\d)(\d{6})(?!\d)', subject)
                                        if match_sub: 
                                            code = match_sub.group(1)
                                        else:
                                            safe_text = body.lower().replace(target_email.lower(), "")
                                            match_body = re.search(r'(?<!\d)(\d{6})(?!\d)', safe_text.replace(" ", ""))
                                            if match_body: 
                                                code = match_body.group(1)

                                    if code:
                                        self.seen_uids.add(uid_bytes) 
                                        return code
            except Exception: 
                pass
                
            time.sleep(random.uniform(6.0, 10.0)) 
            
        return None


class HotmailAPIService:
    def __init__(self, data_line, api_mode, proxy=None):
        self.url = "https://smail1s.com/get_messages"
        self.data_line = data_line.strip()
        self.api_mode = api_mode.strip()
        self.email = self.data_line.split('|')[0] if '|' in self.data_line else self.data_line
        self.seen_msg_ids = set() 
        self.proxy = proxy
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        if self.proxy: 
            self.session.proxies.update(self.proxy)
            
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def init_baseline(self):
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 3.0)) 
        
        for _ in range(3):
            try:
                response = self.session.post(self.url, json=payload, timeout=20)
                if response.status_code == 200:
                    data_array = response.json().get("data", [])
                    if data_array and len(data_array) > 0:
                        messages = data_array[0].get("messages", [])
                        for msg in messages:
                            msg_id = str(msg.get("id", msg.get("uid", "")))
                            if not msg_id: 
                                msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                            self.seen_msg_ids.add(msg_id)
                    break 
            except Exception: 
                time.sleep(3) 

    def get_otp_code(self, timeout=180, force_8_digits=False): 
        start_time = time.time()
        loai_ma = "ÉP ĐỌC MÃ 8 SỐ 2FA" if force_8_digits else "ĐỌC MÃ ĐĂNG KÝ 6 SỐ"
        print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} ({loai_ma})...', Colors.INFO)}")
        
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 5.0))
        last_logged = ""
        
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): 
                return None
                
            try:
                response = self.session.post(self.url, json=payload, timeout=20)
                
                if response.status_code == 200:
                    res_json = response.json()
                    data_array = res_json.get("data", [])
                    
                    if data_array and len(data_array) > 0:
                        account_data = data_array[0]
                        
                        if account_data.get("error"):
                            msg_err = f"Lỗi hộp thư: {account_data['error']}"
                            if msg_err != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = account_data.get("messages", [])
                            msg_info = f"Tìm thấy {len(messages)} thư."
                            if msg_info != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_info} Đang MỞ SÂU NỘI DUNG THƯ để đọc mã...', Colors.INFO)}")
                                last_logged = msg_info
                                
                            for msg in messages:
                                msg_id = str(msg.get("id", msg.get("uid", "")))
                                if not msg_id: 
                                    msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                                    
                                if msg_id in self.seen_msg_ids: 
                                    continue
                                
                                subject = str(msg.get("subject", "")).lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))
                                
                                is_ig = ("instagram" in subject) or ("instagram" in from_sender)
                                is_security_mail = True 
                                
                                if force_8_digits: 
                                    is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã", "factor"])
                                
                                if is_ig and is_security_mail:
                                    code = None
                                    if force_8_digits:
                                        clean_text = re.sub(r'<[^>]+>', ' ', raw_msg).replace(" ", "")
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_text)
                                        if match_8: 
                                            code = match_8.group(1)
                                    else:
                                        match_sub = re.search(r'(?<!\d)(\d{6})(?!\d)', subject)
                                        if match_sub: 
                                            code = match_sub.group(1)
                                        else:
                                            safe_msg = raw_msg.lower().replace(self.email.lower(), "")
                                            clean_text = re.sub(r'<[^>]+>', ' ', safe_msg).replace(" ", "")
                                            match_6 = re.search(r'(?<!\d)(\d{6})(?!\d)', clean_text)
                                            if match_6: 
                                                code = match_6.group(1)
                                    
                                    if code:
                                        self.seen_msg_ids.add(msg_id) 
                                        print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}")
                                        return code
                else:
                    status_err = f"Lỗi HTTP {response.status_code}"
                    if status_err != last_logged:
                        print(f"{Colors.color_text(f'[API Smail1s] {status_err}', Colors.WARNING)}")
                        last_logged = status_err
                        
            except requests.exceptions.RequestException:
                err_str = "Lỗi kết nối API. Đang tự động thử lại..."
                if err_str != last_logged:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str}', Colors.WARNING)}")
                    last_logged = err_str
                try: 
                    self._init_session() 
                except: 
                    pass
            except Exception: 
                pass
                
            time.sleep(random.uniform(5.0, 8.0))
            
        return None


# ==================== MAIN THREAD ====================
class starts(threading.Thread):
    def __init__(self, thread_id, mode, account_count, data_source, manual_password=None, base_gmail=None, app_password=None, api_mode=None, avatar_folder="", proxies_list=None, auto_sms_key="", auto_sms_country=""):
        super().__init__()
        self.thread_id = f"Tab-{thread_id}"
        self.mode = mode
        self.account_count = account_count
        self.data_source = data_source
        self.manual_password = manual_password 
        self.base_gmail = base_gmail
        self.app_password = app_password
        self.api_mode = api_mode
        self.avatar_folder = avatar_folder
        self.proxies_list = proxies_list or [] 
        self.auto_sms_key = auto_sms_key
        self.auto_sms_country = auto_sms_country
    
    def run(self):
        global BASE_YEAR
        
        # --- LẤY PROXY LOCAL DÀNH CHO LUỒNG NÀY ---
        raw_proxy = None
        req_proxy = None
        
        if self.proxies_list:
            thread_idx_for_proxy = int(self.thread_id.split("-")[1]) - 1
            raw_proxy = self.proxies_list[thread_idx_for_proxy % len(self.proxies_list)]
            req_proxy = format_proxy(raw_proxy)
            p_info = parse_proxy(raw_proxy)
            
            if p_info and p_info.get("user"):
                p_ip = p_info["ip"]
                p_port = p_info["port"]
                p_user = p_info["user"]
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (Có User/Pass): {p_ip}:{p_port} (User: {p_user})", Colors.WARNING))
            elif p_info:
                p_ip = p_info["ip"]
                p_port = p_info["port"]
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (IP:Port): {p_ip}:{p_port}", Colors.WARNING))
            else:
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy: {raw_proxy}", Colors.WARNING))
        
        def create_one_account(account_index):
            global BASE_YEAR
            if STOP_EVENT.is_set(): 
                return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{self.thread_id}] BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_account = ""
            imap_service = None
            mail_service = None
            hotmail_service = None
            sms_service = None
            
            full_name, username = VietnameseNameGenerator()
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
            secure_pass = "".join(random.choice(chars) for _ in range(12))

            if self.mode == "6":
                # Chế độ Số điện thoại AutoSMS
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang mua số điện thoại ({self.auto_sms_country}) từ AutoSMS...', Colors.INFO)}")
                sms_service = AutoSMS_Service(self.auto_sms_key, self.auto_sms_country, req_proxy)
                used_account = sms_service.buy_number()
                if not used_account:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể mua số điện thoại. Có thể hết số hoặc hết tiền.', Colors.ERROR)}")
                    return False
            else:
                # Các chế độ Email
                if self.mode == "1":
                    mail_service = MailService(proxy=req_proxy)
                    used_account = mail_service.create_account(username)
                    if not used_account: 
                        return False
                    mail_service.authenticate()
                    
                elif self.mode == "2":
                    with DATA_LOCK:
                        if len(self.data_source) == 0: 
                            return False
                        used_account = self.data_source.pop(0)
                        
                    if "mail.tm" in used_account.lower():
                        mail_service = MailService(proxy=req_proxy)
                        pass_to_use = self.manual_password if self.manual_password else "TempPass123!"
                        mail_service.authenticate(used_account, pass_to_use)
                        
                elif self.mode == "3":
                    with DATA_LOCK:
                        if len(self.data_source) == 0: 
                            return False
                        used_account, app_pass = self.data_source.pop(0)
                    imap_service = GmailIMAPService(used_account, app_pass)
                    
                elif self.mode == "4":
                    with DATA_LOCK:
                        if len(self.data_source) == 0: 
                            return False
                        used_account = self.data_source.pop(0)
                    imap_service = GmailIMAPService(self.base_gmail, self.app_password)
                    
                elif self.mode == "5":
                    with DATA_LOCK:
                        if len(self.data_source) == 0: 
                            return False
                        data_line = self.data_source.pop(0)
                        
                    used_account = data_line.split('|')[0]
                    hotmail_service = HotmailAPIService(data_line, self.api_mode, proxy=req_proxy)

            print(f"{Colors.color_text(f'[{self.thread_id}] Đang dùng Tài khoản đăng ký: {used_account}', Colors.INFO)}")

            driver = None
            try:
                # MỞ TRÌNH DUYỆT CÓ CHIA LƯỚI
                thread_idx = int(self.thread_id.split("-")[1]) - 1 
                win_width = 460   
                win_height = 520  
                columns = 4       
                col = thread_idx % columns
                row = thread_idx // columns
                x_pos = col * win_width
                y_pos = row * win_height
                
                options = uc.ChromeOptions()
                options.add_argument('--mute-audio')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-save-password-bubble')
                options.add_argument('--password-store=basic')
                
                prefs = {
                    'credentials_enable_service': False,
                    'profile.password_manager_enabled': False,
                    'profile.password_manager_leak_detection': False,
                    'autofill.profile_enabled': False,
                    'profile.default_content_setting_values.notifications': 2
                }
                options.add_experimental_option('prefs', prefs)
                
                options.add_argument(f'--window-size={win_width},{win_height}')
                options.add_argument(f'--window-position={x_pos},{y_pos}')
                options.add_argument('--force-device-scale-factor=0.65')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-dev-shm-usage')
                
                forwarder = None
                options.add_argument('--incognito')
                
                if raw_proxy:
                    parsed_p = parse_proxy(raw_proxy)
                    if parsed_p:
                        if parsed_p.get("user") and parsed_p.get("pass"):
                            forwarder = LocalProxyForwarder(parsed_p["ip"], parsed_p["port"], parsed_p["user"], parsed_p["pass"])
                            options.add_argument(f'--proxy-server=http://127.0.0.1:{forwarder.local_port}')
                        else:
                            options.add_argument(f'--proxy-server=http://{parsed_p["ip"]}:{parsed_p["port"]}')
                
                with BROWSER_LOCK:
                    driver = uc.Chrome(options=options)
                    with DRIVER_LOCK:
                        ALL_DRIVERS.append((self.thread_id, driver))
                    try:
                        driver.set_window_size(win_width, win_height)
                        driver.set_window_position(x_pos, y_pos)
                    except: 
                        pass
                    time.sleep(1) 
                    
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
                except: 
                    pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: 
                    current_year = "2005"
                current_day = str(random.randint(2, 28))
                current_month = str(random.randint(1, 12))
                
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: 
                    BASE_YEAR = random.randint(1995, 2005)

                def slow_scroll_to_element(element):
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(0.5)
                    except: 
                        pass

                def human_type(element, text, is_username=False):
                    with TYPE_LOCK:
                        slow_scroll_to_element(element)
                        try: 
                            element.click() 
                        except: 
                            driver.execute_script("arguments[0].click();", element) 
                            
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].focus();", element)
                        
                        if is_username:
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
                        try: 
                            element.send_keys(Keys.TAB)
                        except: 
                            pass

                # ĐIỀN FORM ĐĂNG KÝ
                try:
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, '//select | //*[@role="combobox"]')))
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    
                    if len(inputs) >= 4:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Phone/Email...', Colors.INFO)}")
                        
                        # Nếu là số điện thoại, lọc chuỗi format
                        if self.mode == "6":
                            phone_str = used_account.replace("+", "")
                            human_type(inputs[0], phone_str)
                        else:
                            human_type(inputs[0], used_account)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Mật khẩu...', Colors.INFO)}")
                        human_type(inputs[1], secure_pass)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Chọn Ngày Sinh...', Colors.INFO)}")
                        try:
                            driver.set_script_timeout(15)
                            js_script = '''
                            const day = arguments[0];
                            const month = arguments[1];
                            const year = arguments[2];
                            const callback = arguments[arguments.length - 1];

                            (async function() {
                                try {
                                    const selects = Array.from(document.querySelectorAll('select'));
                                    if (selects.length >= 3) {
                                        function setSelectVal(el, val) {
                                            let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
                                            nativeSetter.call(el, val);
                                            el.dispatchEvent(new Event('change', { bubbles: true }));
                                        }
                                        for (let sel of selects) {
                                            const t = (sel.title || "").toLowerCase();
                                            if (t.includes("tháng") || t.includes("month")) {
                                                setSelectVal(sel, month);
                                            } else if (t.includes("ngày") || t.includes("day")) {
                                                setSelectVal(sel, day);
                                            } else if (t.includes("năm") || t.includes("year")) {
                                                setSelectVal(sel, year);
                                            }
                                        }
                                        await new Promise(r => setTimeout(r, 1000));
                                        return callback("SUCCESS");
                                    }

                                    const comboboxes = Array.from(document.querySelectorAll('[role="combobox"]'));
                                    if (comboboxes.length < 3) return callback("ERROR: Không tìm thấy 3 ô combobox!");

                                    const monthNum = parseInt(month, 10);
                                    const enMonths = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
                                    const viMonths = ["tháng 1", "tháng 2", "tháng 3", "tháng 4", "tháng 5", "tháng 6", "tháng 7", "tháng 8", "tháng 9", "tháng 10", "tháng 11", "tháng 12"];
                                    const possibleMonths = [String(monthNum), "0" + monthNum, enMonths[monthNum-1], viMonths[monthNum-1]];

                                    async function clickOption(box, possibleValues) {
                                        box.scrollIntoView({ block: 'center' });
                                        box.click();
                                        await new Promise(r => setTimeout(r, 600));
                                        
                                        const options = Array.from(document.querySelectorAll('div, span, li, option'));
                                        const matched = options.filter(el => {
                                            if (el.offsetHeight === 0 && !el.getClientRects().length) return false;
                                            const txt = el.innerText?.trim().toLowerCase() || "";
                                            return possibleValues.includes(txt);
                                        });

                                        if (matched.length > 0) {
                                            const target = matched[matched.length - 1];
                                            target.scrollIntoView({ block: 'nearest' });
                                            target.click();
                                            await new Promise(r => setTimeout(r, 400));
                                            return true;
                                        }
                                        
                                        document.body.click(); 
                                        await new Promise(r => setTimeout(r, 200));
                                        return false;
                                    }

                                    const htmlLang = document.documentElement.lang.toLowerCase();
                                    if (htmlLang.includes('vi')) {
                                        await clickOption(comboboxes[0], [String(day), "0" + day]);
                                        await clickOption(comboboxes[1], possibleMonths);
                                        await clickOption(comboboxes[2], [String(year)]);
                                    } else {
                                        await clickOption(comboboxes[0], possibleMonths);
                                        await clickOption(comboboxes[1], [String(day), "0" + day]);
                                        await clickOption(comboboxes[2], [String(year)]);
                                    }
                                    
                                    callback("SUCCESS");
                                } catch (err) {
                                    callback("ERROR: " + err.toString());
                                }
                            })();
                            '''
                            driver.execute_async_script(js_script, current_day, current_month, current_year)
                        except: 
                            pass
                            
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Họ Tên...', Colors.INFO)}")
                        human_type(inputs[2], full_name)
                        
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Username...', Colors.INFO)}")
                        human_type(inputs[3], username, is_username=True)
                    else:
                        return False
                    
                    time.sleep(10)
                    
                    uid_moc = 0
                    if self.mode in ["3", "4"] and imap_service:
                        uid_moc = imap_service.get_latest_uid()
                    elif self.mode == "5" and hotmail_service:
                        hotmail_service.init_baseline()

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    driver.execute_script("document.body.click();")
                    time.sleep(5)
                    
                    with SUBMIT_LOCK:
                        try:
                            driver.execute_script("""
                                let submitBtn = document.querySelector('button[type="submit"]');
                                if (!submitBtn) {
                                    const allClickables = Array.from(document.querySelectorAll('button, div[role="button"]'));
                                    submitBtn = allClickables.find(b => {
                                        const text = (b.innerText || b.textContent || "").trim().toLowerCase();
                                        return text === "submit" || text === "sign up" || text === "đăng ký" || text === "next";
                                    });
                                }
                                if (submitBtn) {
                                    submitBtn.disabled = false;
                                    submitBtn.removeAttribute('disabled');
                                    submitBtn.click();
                                }
                            """)
                        except: 
                            pass
                        time.sleep(15) 
                    
                except Exception as e:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi điền form: {e}', Colors.ERROR)}")
                    if self.mode == "6" and sms_service: 
                        sms_service.cancel_order()
                    return False

                # ==================== NHẬN DIỆN Ô NHẬP OTP 6 SỐ ====================
                otp_input = None
                locators = [
                    (By.NAME, "email_confirmation_code"),
                    (By.NAME, "confirmationCode"),
                    (By.XPATH, "//input[@type='text']")
                ]
                time.sleep(3)
                for loc in locators:
                    try:
                        otp_input = WebDriverWait(driver, 3).until(EC.presence_of_element_located(loc))
                        if otp_input: 
                            break
                    except: 
                        pass
                
                if not otp_input:
                    try: 
                        otp_input = driver.execute_script("return document.querySelector('input');")
                    except: 
                        pass

                if not otp_input:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể tìm thấy ô nhập OTP.', Colors.ERROR)}")
                    if self.mode == "6" and sms_service: 
                        sms_service.cancel_order()
                    return False
                
                # ==================== CƠ CHẾ LẤY OTP ĐĂNG KÝ VỚI VÒNG LẶP RETRY ====================
                otp_code = None
                max_resend_attempts = 2 
                
                for attempt in range(max_resend_attempts + 1):
                    if STOP_EVENT.is_set(): 
                        if self.mode == "6" and sms_service: 
                            sms_service.cancel_order()
                        return False
                    
                    if self.mode == "2" and not (mail_service and mail_service.token):
                        with OTP_LOCK:
                            PAUSE_FOR_INPUT.clear()
                            built_in_print(f"\n{Colors.color_text(f'[{self.thread_id}] MỜI NHẬP OTP TỪ BÀN PHÍM: ', Colors.SUCCESS)}", end="")
                            otp_code = input().strip()
                            PAUSE_FOR_INPUT.set()
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Đang chờ lấy OTP...', Colors.INFO)}")
                        
                        if self.mode == "6":
                            # Lấy OTP qua AutoSMS
                            otp_code = sms_service.get_otp(timeout=100)
                        else:
                            # Lấy OTP qua Email
                            if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                                otp_code = mail_service.get_otp_code(timeout=100, force_8_digits=False)
                            elif self.mode in ["3", "4"]:
                                otp_code = imap_service.get_otp_code(target_email=used_account, since_uid=uid_moc, timeout=100, force_8_digits=False)
                            elif self.mode == "5":
                                otp_code = hotmail_service.get_otp_code(timeout=120, force_8_digits=False) 
                    
                    if otp_code: 
                        break 
                    
                    if attempt < max_resend_attempts:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Không thấy mã, tự động click Gửi lại...', Colors.WARNING)}")
                        
                        clicked_didnt_receive = driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                            for (let b of btns) {
                                let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if (txt.includes('không nhận được mã') || txt.includes("didn't receive") || txt.includes("resend sms")) {
                                    b.click(); return true;
                                }
                            }
                            return false;
                        """)
                        if clicked_didnt_receive:
                            time.sleep(3) 
                            driver.execute_script("""
                                let btns = Array.from(document.querySelectorAll('button, div[role="button"], a, span'));
                                for (let b of btns) {
                                    let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                                    if (txt.includes('gửi lại') || txt.includes('resend')) {
                                        let clickable = b.closest('button, [role="button"]') || b;
                                        clickable.click(); return true;
                                    }
                                }
                                return false;
                            """)
                            time.sleep(5)
                            # Cập nhật mốc thời gian hòm thư để lấy thư mới nếu dùng IMAP
                            if self.mode in ["3", "4"] and imap_service:
                                uid_moc = imap_service.get_latest_uid()

                if not otp_code:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Đã thử Gửi lại nhưng không có mã OTP!', Colors.ERROR)}")
                    if self.mode == "6" and sms_service: 
                        sms_service.cancel_order()
                    return False

                print(f"{Colors.color_text(f'[{self.thread_id}] Điền mã OTP: {otp_code}', Colors.SUCCESS)}")
                try: 
                    human_type(otp_input, otp_code)
                except:
                    driver.execute_script("""
                        let input = arguments[0]; let val = arguments[1];
                        let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        setter.call(input, val);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    """, otp_input, otp_code)
                    
                time.sleep(1.5)
                try: 
                    otp_input.send_keys(Keys.ENTER)
                except: 
                    pass
                
                try:
                    btn_xpath = "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tiếp tục') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') or @type='submit']"
                    submit_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
                    driver.execute_script("arguments[0].click();", submit_btn)
                except: 
                    pass

                # ==================== CHỜ TẢI TRANG CHỦ & KIỂM TRA ACC DIE ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ IG xử lý OTP (40s)...', Colors.INFO)}")
                time.sleep(40)
                
                cookies_list = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies_list}
                current_url = driver.current_url.lower()
                page_source = driver.page_source.lower()
                
                if "challenge" in current_url or "suspended" in current_url or not cookie_dict.get('sessionid'):
                    print(f"{Colors.color_text(f'[{self.thread_id}] LỖI: TÀI KHOẢN ĐÃ DIE / CHECKPOINT!', Colors.ERROR)}")
                    return "DEAD" 

                print(f"{Colors.color_text(f'[{self.thread_id}] TÀI KHOẢN SỐNG! Chuẩn bị up Avatar...', Colors.SUCCESS)}")

                # --- UP AVATAR ---
                if self.avatar_folder and os.path.exists(self.avatar_folder):
                    images = [f for f in os.listdir(self.avatar_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    if images:
                        try:
                            image_path = os.path.abspath(os.path.join(self.avatar_folder, random.choice(images)))
                            driver.get(f"https://www.instagram.com/{username}/")
                            time.sleep(8)
                            
                            if "challenge" not in driver.current_url.lower():
                                driver.execute_script("""
                                    if (!window.hookedFileClick) {
                                        window.originalClick = window.HTMLInputElement.prototype.click;
                                        window.HTMLInputElement.prototype.click = function() {
                                            if (this.type === 'file') {
                                                this.style.display = 'block'; this.style.opacity = '1';
                                                this.style.visibility = 'visible'; this.style.position = 'fixed';
                                                this.style.top = '0'; this.style.left = '0'; this.style.zIndex = '99999';
                                            } else { window.originalClick.call(this); }
                                        };
                                        window.hookedFileClick = true;
                                    }
                                    let header = document.querySelector('header');
                                    if (header) { let btns = header.querySelectorAll('button, div[role="button"]'); if (btns.length > 0) btns[0].click(); }
                                """)
                                time.sleep(3)
                                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                                if file_inputs:
                                    file_inputs[-1].send_keys(image_path) 
                                    time.sleep(10) 
                        except: 
                            pass

                # ==================== TÍCH HỢP TỰ ĐỘNG BẬT 2FA ====================
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành cài đặt 2FA...', Colors.INFO)}")
                two_fa_secret = ""
                try:
                    driver.get("https://accountscenter.instagram.com/password_and_security/two_factor/")
                    time.sleep(7)

                    for _ in range(4):
                        clicked_buffer = driver.execute_script("""
                            let t = arguments[0].toLowerCase();
                            let els = Array.from(document.querySelectorAll('*'));
                            for(let el of els) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if(txt.includes(t) && txt.length < 50) {
                                    let click = el.closest('div[role="button"], a[role="link"], button');
                                    if(click) { click.click(); return true; }
                                }
                            }
                            return false;
                        """, username)
                        if clicked_buffer: 
                            time.sleep(4)
                            break
                        time.sleep(2)

                    # BẤT ĐẦU 2FA
                    for _ in range(6):
                        clicked_start = driver.execute_script("""
                            let els = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                            for(let el of els) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if(txt === 'bắt đầu' || txt === 'get started') {
                                    let btn = el.closest('button, [role="button"]') || el;
                                    btn.click(); return true;
                                }
                            }
                            return false;
                        """)
                        if clicked_start: 
                            time.sleep(4)
                            break
                        time.sleep(1.5)

                    # CHECK EMAIL / SMS VERIFY
                    is_verify_screen = False
                    for _ in range(6):
                        is_verify_screen = driver.execute_script("""
                            let txt = (document.body.innerText || document.body.textContent || '').toLowerCase();
                            return txt.includes('kiểm tra email') || txt.includes('check your email') || txt.includes('nhập mã') || txt.includes('enter code');
                        """)
                        if is_verify_screen: 
                            break
                        time.sleep(1.5)

                    if is_verify_screen:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Phát hiện màn hình đệm 2FA, đang chờ mã xác nhận...', Colors.WARNING)}")
                        verify_code = None
                        
                        if self.mode == "6":
                            # Với số ĐT đôi khi nó gửi SMS verify 6 số
                            verify_code = sms_service.get_otp(timeout=100)
                        else:
                            if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                                verify_code = mail_service.get_otp_code(timeout=120, force_8_digits=True)
                            elif self.mode in ["3", "4"]:
                                verify_code = imap_service.get_otp_code(target_email=used_account, since_uid=uid_moc, timeout=120, force_8_digits=True)
                            elif self.mode == "5":
                                verify_code = hotmail_service.get_otp_code(timeout=180, force_8_digits=True)

                        if verify_code:
                            driver.execute_script("""
                                let val = arguments[0];
                                let inp = document.querySelector('input');
                                if (inp) {
                                    let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                    setter.call(inp, val);
                                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                                    inp.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            """, verify_code)
                            time.sleep(1.5)
                            driver.execute_script("""
                                let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                                for(let b of btns){
                                    let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                                    if(['tiếp tục', 'next', 'continue', 'gửi', 'xác nhận', 'submit'].includes(t)){
                                        if(!b.disabled) { b.click(); return; }
                                    }
                                }
                            """)
                            time.sleep(6) 

                    # CHỌN AUTHENTICATOR APP
                    try:
                        driver.execute_script("""
                            let all = Array.from(document.querySelectorAll('*'));
                            for(let el of all) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if(txt.includes('authentication app') || txt.includes('ứng dụng xác thực')) {
                                    let click = el.closest('div[role="button"], label, div[tabindex], button, [role="radio"]') || el;
                                    click.click(); return;
                                }
                            }
                        """)
                        time.sleep(2)
                        driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                            for(let b of btns) {
                                let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                                if(['continue', 'next', 'tiếp tục'].includes(txt)) {
                                    let click = b.closest('button, [role="button"]') || b;
                                    if(!click.disabled) { click.click(); return; }
                                }
                            }
                        """)
                        time.sleep(5)
                    except: 
                        pass

                    # LẤY SECRET KEY
                    for attempt in range(8):
                        driver.execute_script("""
                            let els = Array.from(document.querySelectorAll('button, div[role="button"], span, a'));
                            for(let el of els) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if(txt.includes("can't scan") || txt.includes("copy key") || txt.includes("sao chép") || txt.includes("không thể quét")) {
                                    el.click(); return;
                                }
                            }
                        """)
                        time.sleep(2)

                        extracted_key = driver.execute_script("""
                            let spans = Array.from(document.querySelectorAll('span, div, p, code'));
                            for (let el of spans) {
                                let clean = (el.innerText || el.textContent || '').replace(/\\s+/g, '').toUpperCase();
                                if (/^[A-Z2-7]{32}$/.test(clean)) {
                                    if (!clean.includes('FXAC') && !clean.includes('META')) return clean;
                                }
                            }
                            return null;
                        """)
                        if extracted_key: 
                            two_fa_secret = extracted_key
                            break
                        
                        txt = driver.execute_script("return document.body.innerText || document.body.textContent;")
                        match = re.search(r'\b([A-Z2-7]{4}(?:\s+[A-Z2-7]{4}){7})\b', txt)
                        if match:
                            can = re.sub(r'\s+', '', match.group(1)).upper()
                            if 'META' not in can and 'FXAC' not in can:
                                two_fa_secret = can
                                break
                        time.sleep(2)

                    if two_fa_secret:
                        print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ LẤY CHUẨN XÁC SECRET KEY 2FA: {two_fa_secret}', Colors.SUCCESS)}")
                        driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                            for(let b of btns) {
                                let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                                if(['next', 'continue', 'tiếp tục', 'nhập mã'].includes(txt)) {
                                    let click = b.closest('button, [role="button"]') || b;
                                    if(!click.disabled) { click.click(); return; }
                                }
                            }
                        """)
                        time.sleep(4)

                        totp = pyotp.TOTP(two_fa_secret)
                        current_otp = totp.now()
                        
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        for inp in inputs:
                            if inp.is_displayed():
                                try: 
                                    inp.clear()
                                except: 
                                    pass
                                for digit in current_otp: 
                                    inp.send_keys(digit)
                                    time.sleep(0.08)
                                    
                                time.sleep(1)
                                try: 
                                    inp.send_keys(Keys.ENTER)
                                except: 
                                    pass
                                driver.execute_script("document.body.click();")
                                break
                                
                        time.sleep(2)

                        driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                            btns.reverse();
                            for(let b of btns){
                                let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if(['tiếp', 'tiếp tục', 'next', 'xong', 'done'].includes(t)){
                                    if(!b.disabled && b.getAttribute('aria-disabled') !== 'true') { b.click(); return; }
                                }
                            }
                        """)
                        time.sleep(5)
                except: 
                    pass

                # ==================== LẤY LẠI COOKIE LẦN CUỐI & LƯU ACC ====================
                cookies_list = driver.get_cookies()
                cookie_dict = {c['name']: c['value'] for c in cookies_list}
                cookie_str = (f"datr={cookie_dict.get('datr', '')}; ig_did={cookie_dict.get('ig_did', '')}; mid={cookie_dict.get('mid', '')}; wd={cookie_dict.get('wd', '1920x1080')}; dpr={cookie_dict.get('dpr', '1')}; csrftoken={cookie_dict.get('csrftoken', '')}; ds_user_id={cookie_dict.get('ds_user_id', '')}; sessionid={cookie_dict.get('sessionid', '')}; rur={cookie_dict.get('rur', '')}")
                
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}2FA:  {Colors.WARNING}{two_fa_secret if two_fa_secret else 'Lỗi không có'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(self.thread_id, used_account, secure_pass, username, full_name, f"mode_{self.mode}", cookie_str, two_fa_secret)
                return True
                
            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ: {e}', Colors.ERROR)}")
                if self.mode == "6" and sms_service: 
                    sms_service.cancel_order()
                return False
        
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set(): 
                break
                
            status = create_one_account(i)
            if status == True: 
                success_count += 1
            elif status == "DEAD": 
                break 
            else: 
                break 
                
            time.sleep(random.uniform(5, 10))
        
        print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT TAB: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

# ==================== MENU CHÍNH ====================
def select_mode():
    built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}6. {Colors.VALUE}THUÊ SIM (SMS OTP)  \033[97m[ Dùng API autosms.site ]{Colors.RESET}")
    
    while True:
        built_in_print(f"{Colors.KEY}Nhập lựa chọn [1-6]: {Colors.RESET}", end="")
        choice = input().strip()
        if choice in ["1", "2", "3", "4", "5", "6"]: 
            return choice

def process_file_input(config_key, default_prompt):
    config_data = load_config()
    saved_file = config_data.get(config_key)
    file_path = ""
    
    if saved_file and os.path.isfile(saved_file):
        built_in_print(f"{Colors.INFO}Phát hiện tệp danh sách cũ: {Colors.VALUE}{saved_file}{Colors.RESET}")
        use_old = input(f"{Colors.KEY}Bạn có muốn sử dụng lại tệp này không? (y/n): {Colors.RESET}").strip().lower()
        if use_old == 'y': 
            file_path = saved_file
            
    if not file_path:
        built_in_print(default_prompt, end="")
        file_path = input().strip().strip('"')
        if os.path.isfile(file_path):
            config_data[config_key] = file_path
            save_config(config_data)

    if os.path.isfile(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        total = len(lines)
        if total == 0:
            built_in_print(f"{Colors.ERROR}File trống!{Colors.RESET}")
            return []
            
        built_in_print(f"{Colors.SUCCESS}Đã tải {total} dòng từ tệp.{Colors.RESET}")
        start_line = input(f"{Colors.KEY}Bạn muốn chạy TỪ dòng số mấy? (Nhấn Enter để chạy từ đầu [1]): {Colors.RESET}").strip()
        end_line = input(f"{Colors.KEY}Bạn muốn chạy ĐẾN dòng số mấy? (Nhấn Enter để chạy đến cuối [{total}]): {Colors.RESET}").strip()

        start_idx = int(start_line) if start_line.isdigit() else 1
        end_idx = int(end_line) if end_line.isdigit() else total
        
        start_idx = max(1, start_idx)
        end_idx = min(total, end_idx)

        if start_idx > end_idx:
            built_in_print(f"{Colors.WARNING}Số thứ tự không hợp lệ, tự động chạy tất cả!{Colors.RESET}")
            return lines
        else:
            selected_lines = lines[start_idx-1:end_idx]
            built_in_print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} mục (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
            return selected_lines
    else:
        return [e.strip() for e in file_path.split(",") if e.strip()]

if __name__ == "__main__":
    banner()
    config_data = load_config()
    mode = select_mode()
    
    data_source = []
    base_gmail = None
    app_password = None
    manual_password = None
    api_mode = None
    auto_sms_key = ""
    auto_sms_country = "vn"

    if mode == "1": 
        pass 
        
    elif mode == "2":
        data_source = process_file_input("last_file_mode2", f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}")
        if any("mail.tm" in e.lower() for e in data_source):
            built_in_print(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}", end="")
            manual_password = input().strip()
            
    elif mode == "3":
        raw_list = process_file_input("last_file_mode3", f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}")
        for line in raw_list:
            parts = re.split(r'[|:]', line.strip())
            if len(parts) >= 2: 
                data_source.append((parts[0].strip(), parts[1].strip()))
        if not data_source: 
            sys.exit()
            
    elif mode == "4":
        built_in_print(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}", end="")
        base_gmail = input().strip()
        built_in_print(f"{Colors.KEY}Nhập App Password: {Colors.RESET}", end="")
        app_password = input().strip()
        data_source = generate_dot_variants(base_gmail)
        
    elif mode == "5":
        built_in_print("1. OAuth | 2. Graph API | 3. Roundcube\n>> ", end="")
        c = input().strip()
        api_mode = "oauth" if c=="1" else "graph" if c=="2" else "roundcube"
        data_source = process_file_input("last_file_mode5", f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}")
        
    elif mode == "6":
        # CONFIG AUTOSMS
        saved_key = config_data.get("autosms_api_key", "")
        if saved_key:
            built_in_print(f"{Colors.INFO}Phát hiện API KEY cũ: {Colors.VALUE}{saved_key[:5]}...{saved_key[-5:]}{Colors.RESET}")
            use_old = input(f"{Colors.KEY}Bạn có muốn sử dụng lại API KEY này không? (y/n): {Colors.RESET}").strip().lower()
            if use_old == 'y': 
                auto_sms_key = saved_key
            
        if not auto_sms_key:
            built_in_print(f"{Colors.KEY}Nhập API KEY của AutoSMS.site: {Colors.RESET}", end="")
            auto_sms_key = input().strip()
            config_data["autosms_api_key"] = auto_sms_key
            save_config(config_data)

        # CONFIG QUỐC GIA
        saved_country = config_data.get("autosms_country", "vn")
        built_in_print(f"{Colors.KEY}Nhập mã quốc gia (Ví dụ: vn, us, th). Để trống mặc định dùng '{saved_country}': {Colors.RESET}", end="")
        input_country = input().strip().lower()
        if input_country:
            auto_sms_country = input_country
            config_data["autosms_country"] = auto_sms_country
            save_config(config_data)
        else:
            auto_sms_country = saved_country
            
        # Call API check số dư xem API key có hợp lệ không
        test_api = AutoSMS_Service(auto_sms_key)
        bal = test_api.get_balance()
        if bal is not None:
            built_in_print(f"{Colors.SUCCESS}Kết nối AutoSMS thành công! Số dư hiện tại: {bal}đ{Colors.RESET}")
            data_source = ["SMS_MODE"] * 999999  # Giả lập data_source vô hạn cho chế độ SMS
        else:
            built_in_print(f"{Colors.ERROR}Lỗi: API KEY không hợp lệ hoặc web AutoSMS đang lỗi. Thoát chương trình.{Colors.RESET}")
            sys.exit()

    if not data_source and mode != "1" and mode != "4":
        built_in_print(f"{Colors.ERROR}Danh sách đầu vào trống! Thoát chương trình.{Colors.RESET}")
        sys.exit()
        
    saved_avatar_folder = config_data.get("last_avatar_folder", "")
    avatar_folder_input = ""

    if saved_avatar_folder and os.path.isdir(saved_avatar_folder):
        built_in_print(f"\n{Colors.INFO}Phát hiện thư mục Avatar cũ: {Colors.VALUE}{saved_avatar_folder}{Colors.RESET}")
        use_old_avatar = input(f"{Colors.KEY}Bạn có muốn dùng lại thư mục này không? (y/n): {Colors.RESET}").strip().lower()
        if use_old_avatar == 'y': 
            avatar_folder_input = saved_avatar_folder

    if not avatar_folder_input:
        built_in_print(f"\n{Colors.KEY}Nhập thư mục chứa ảnh làm Avatar (Bỏ trống nếu không up): {Colors.RESET}", end="")
        avatar_folder_input = input().strip().strip('"').strip("'")
        if avatar_folder_input and os.path.isdir(avatar_folder_input):
            config_data["last_avatar_folder"] = avatar_folder_input
            save_config(config_data)

    built_in_print(f"\n{Colors.KEY}Nhập đường dẫn file Proxy (.txt) (Để trống nếu chạy mạng máy): {Colors.RESET}", end="")
    proxy_file_input = input().strip().strip('"').strip("'")
    proxies_list = []
    
    if proxy_file_input and os.path.isfile(proxy_file_input):
        with open(proxy_file_input, 'r', encoding='utf-8') as f_proxy:
            proxies_list = [line.strip() for line in f_proxy if line.strip()]
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(proxies_list)} Proxy.{Colors.RESET}")

    built_in_print(f"\n{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc): {Colors.RESET}", end="")
    threads_count = int(input().strip())
    
    built_in_print(f"{Colors.KEY}Nhập số tài khoản cần tạo MỖI LUỒNG: {Colors.RESET}", end="")
    accs_per_thread = int(input().strip())
    
    threads = []
    for i in range(threads_count):
        t = starts(i+1, mode, accs_per_thread, data_source, manual_password, base_gmail, app_password, api_mode, avatar_folder_input, proxies_list, auto_sms_key, auto_sms_country)
        threads.append(t)
        
    for t in threads: 
        t.start()
    
    try:
        for t in threads: 
            t.join()
        
        built_in_print(f"\n{Colors.LINE}={'='*68}{Colors.RESET}")
        built_in_print(f"{Colors.color_text('AUTO ĐÃ HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!', Colors.SUCCESS)}")
        built_in_print(f"{Colors.TITLE}TIẾN HÀNH RÀ SOÁT VÀ ĐÓNG TRÌNH DUYỆT:{Colors.RESET}")
        
        for tid, drv in ALL_DRIVERS:
            try:
                drv.title 
                while True:
                    built_in_print(f"{Colors.WARNING}[{tid}] Bạn có muốn đóng Chrome của luồng này không? (y/n): {Colors.RESET}", end="")
                    choice = input().strip().lower()
                    
                    if choice == 'y':
                        try: 
                            drv.quit()
                        except: 
                            pass
                        built_in_print(f"{Colors.SUCCESS}>> Đã đóng trình duyệt của {tid}.{Colors.RESET}")
                        break
                        
                    elif choice == 'n':
                        built_in_print(f"{Colors.INFO}>> Đã giữ lại trình duyệt của {tid}.{Colors.RESET}")
                        break
                        
            except: 
                pass 
                
        built_in_print(f"\n{Colors.SUCCESS}TOOL ĐÃ KẾT THÚC!{Colors.RESET}")
        built_in_print(f"{Colors.KEY}Nhấn Enter để thoát...{Colors.RESET}", end="")
        input()
        
    except KeyboardInterrupt:
        STOP_EVENT.set() 
        sys.exit(0)
