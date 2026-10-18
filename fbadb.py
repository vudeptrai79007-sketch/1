# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import socket
import select
import base64
import io
import types
import re

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
# -----------------------------------------------------------------------------------

import uiautomator2 as u2
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import subprocess
import urllib.parse
import string
import json
import html
import uuid
import struct
import threading
import imaplib
import email
from email.header import decode_header
import hashlib
import traceback
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

try:
    import pyotp
except ImportError:
    os.system("pip install pyotp")
    import pyotp

os.system('cls' if os.name == 'nt' else 'clear')
trang = Style.BRIGHT + Fore.WHITE
xanh = Style.BRIGHT + Fore.GREEN
do = Style.BRIGHT + Fore.RED
vang = Style.BRIGHT + Fore.YELLOW
xanh_duong = Style.BRIGHT + Fore.CYAN

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
log_lock = threading.Lock()
email_lock = threading.Lock()

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

CONFIG_FILE = 'config_reg_fb.json'
CONFIG_GMAIL_FILE = "config_gmail.json"
GOM_HOTMAIL_FILE = 'Gom_Hotmail_Dongvan.txt'
FB_ACCOUNT_FILE = 'FB_NhaTrong.txt'
TELE_FILE = 'Token-ID-Tele.txt'

# CẤU HÌNH THỜI GIAN & ANTI-CHECKPOINT TỐI ƯU NHẤT
DEFAULT_CONFIG = {
    'doi_ip_may_bay': True,
    'thoi_gian_bat_may_bay': 5.0,
    'thoi_gian_cho_4g': 6.0,
    'doi_android_id': True,
    'delay_mo_facebook': 9.0,
    'delay_chon_khong_cho_phep': 0.8,
    'delay_click_khoang_trong': 0.6,
    'delay_chon_toi_co_tai_khoan_roi': 0.8,
    'delay_click_tao_tk_lan1': 1.2,
    'delay_click_tao_tk_lan2': 1.0,
    'delay_chon_khong_cho_phep_lan2': 0.6,
    'delay_nhap_ho': 0.6,
    'delay_nhap_ten': 0.6,
    'delay_click_tiep_lan1': 1.2,
    'delay_click_chon': 0.8,
    'delay_click_tiep_lan2': 0.8,
    'delay_click_tiep_lan3': 1.0,
    'delay_nhap_tuoi': 0.7,
    'delay_click_tiep_lan4': 1.0,
    'delay_click_ok': 0.8,
    'delay_chon_gioi_tinh': 0.8,
    'delay_click_tiep_lan5': 1.2,
    'delay_nhap_sdt': 0.8,
    'delay_click_tiep_sdt': 2.0,
    'delay_click_tiep_tuc_tao_tk': 1.0,
    'delay_kiem_tra_sdt': 0.8,
    'delay_nhap_mat_khau': 1.2,
    'delay_click_tiep_sau_mk': 1.8,
    'delay_click_luu': 1.0,
    'delay_cho_toi_dong_y': 18.0,
    'delay_kiem_tra_loi': 1.2,
    'delay_click_tiep_tuc': 1.0,
    'delay_click_khong_cho_phep': 0.6,
    'delay_click_khong_cho_phep_lan2': 0.5,
    'delay_buoc_dung_fb': 0.5,
    'delay_mo_lai_fb': 7.0,
    'delay_click_toi_khong_nhan_duoc_ma': 1.0,
    'delay_click_xac_nhan_email': 0.8,
    'delay_nhap_email': 1.0,
    'delay_click_tiep_sau_email': 2.0,
    'delay_get_code': 2.5,
    'delay_nhap_code': 1.2,
    'delay_click_tiep_cuoi': 6.0,
    'delay_up_avatar': 8.0,
    'delay_giua_cac_lan_chay': 4.0,
    'delay_thu_lai_khi_loi': 5.0,
    'so_lan_thu_get_code': 20,
    'mat_khau_fb': '@Letien09'
}

device_steps = {}
device_last_step = {}
multi_mode = False
stop_flag = STOP_EVENT


def nghi_ngau_nhien(thoi_gian_goc, dao_dong=0.2):
    """Tạo độ trễ ngẫu nhiên +-20% quanh mốc cấu hình để chống thuật toán phát hiện bot của Meta"""
    try:
        t = float(thoi_gian_goc)
        if t <= 0:
            return
        min_t = max(0.05, t * (1.0 - dao_dong))
        max_t = t * (1.0 + dao_dong)
        time.sleep(random.uniform(min_t, max_t))
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        time.sleep(1)


# ========== HÀM CƠ BẢN & HỆ THỐNG XỬ LÝ PROXY ĐA NĂNG ==========
def load_config():
    if os.path.exists(CONFIG_GMAIL_FILE):
        try:
            with open(CONFIG_GMAIL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_GMAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def VietnameseMaleNameGenerator():
    ho_list = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Vu", "Dang", "Bui", "Do"]
    middle_list = ["Van", "Minh", "Hoang", "Duc", "Dinh", "Gia", "Bao", "Quang", "Tuan", "Xuan"]
    ten_list = ["An", "Binh", "Cuong", "Dung", "Hung", "Hai", "Son", "Tien", "Trung", "Vinh", "Nam", "Phuc", "Thanh", "Khoa"]

    ho = random.choice(ho_list)
    middle = random.choice(middle_list)
    ten = random.choice(ten_list)

    ho_part = f"{ho} {middle}"
    ten_part = ten
    full_name = f"{ho_part} {ten_part}"

    cleaned = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
    extra_chars = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=2))
    username = f"{cleaned}{extra_chars}{random.randint(10000, 999999)}"

    return ho_part, ten_part, full_name, username

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

    if "@" in p_str:
        try:
            auth_part, host_part = p_str.split("@", 1)
            u, pwd = auth_part.split(":", 1)
            ip, port = host_part.split(":", 1)
            return {"ip": ip.strip(), "port": port.strip(), "user": u.strip(), "pass": pwd.strip()}
        except Exception:
            pass

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
            except Exception:
                pass
            try:
                remote_sock.close()
            except Exception:
                pass

    def close(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass


# ==================== CÁC CLASS XỬ LÝ EMAIL & SĐT (6 CHẾ ĐỘ) ====================
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
            r = requests.post(
                f"{self.base_url}/accounts",
                json={"address": f"{name}@{self.domain}", "password": "TempPass123!"},
                timeout=10,
                proxies=self.proxy
            )
            if r.status_code == 201:
                self.email_address = r.json()['address']
                return self.email_address
        except Exception:
            return None

    def authenticate(self, email_addr=None, password="TempPass123!"):
        if email_addr:
            self.email_address = email_addr
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(
                f"{self.base_url}/token",
                json={"address": self.email_address, "password": password},
                timeout=10,
                proxies=self.proxy
            )
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
                        if any(k in subject or k in frm for k in ['facebook', 'fb', 'instagram', 'meta']):
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or re.sub('<[^<]+?>', ' ', str(detail.get('html', '')))
                            safe_body = raw_text.lower().replace(str(self.email_address).lower(), "")
                            clean_body = safe_body.replace(" ", "")

                            code = None
                            if force_8_digits:
                                match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_body)
                                if match_8:
                                    code = match_8.group(1)
                            else:
                                match_body_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_body)
                                match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                match_body = re.search(r'(?<!\d)(\d{5,8})(?!\d)', clean_body)
                                if match_body_8:
                                    code = match_body_8.group(1)
                                elif match_sub:
                                    code = match_sub.group(1)
                                elif match_body:
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
        plain, html_parts = [], []
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
                    html_parts.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain":
                    plain.append(text)
                else:
                    html_parts.append(text)
        if plain:
            return "\n".join(plain).strip()
        if html_parts:
            return re.sub(r'<[^>]+>', ' ', "\n".join(html_parts)).strip()
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
                    except Exception:
                        result += text.decode('utf-8', errors='replace')
                else:
                    result += str(text)
            return result
        except Exception:
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

                                is_target_service = any(k in subject or k in from_addr for k in ["facebook", "fb", "instagram", "meta"])
                                is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "xác nhận", "code", "mã", "authenticate", "profile", "fb-", "confirm"])

                                if is_target_service and (is_security_mail or not force_8_digits):
                                    body = self.get_text(msg)
                                    safe_body = body.lower().replace(target_email.lower(), "").replace(" ", "")
                                    code = None

                                    if force_8_digits:
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', safe_body)
                                        if match_8:
                                            code = match_8.group(1)
                                    else:
                                        match_body_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', safe_body)
                                        match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                        match_body = re.search(r'(?<!\d)(\d{5,8})(?!\d)', safe_body)
                                        if match_body_8:
                                            code = match_body_8.group(1)
                                        elif match_sub:
                                            code = match_sub.group(1)
                                        elif match_body:
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
        loai_ma = "ÉP ĐỌC MÃ 8 SỐ TỪ BODY" if force_8_digits else "ĐỌC MÃ ĐĂNG KÝ"
        if not multi_mode:
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
                        err = account_data.get("error")

                        if err:
                            msg_err = f"Lỗi hộp thư: {err}"
                            if msg_err != last_logged and not multi_mode:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = account_data.get("messages", [])
                            msg_info = f"Tìm thấy {len(messages)} thư."
                            if msg_info != last_logged and not multi_mode:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_info} Đang check từng thư lấy mã...', Colors.INFO)}")
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

                                is_target = any(k in subject or k in from_sender for k in ["facebook", "fb", "instagram", "meta"])
                                is_security_mail = True
                                if force_8_digits:
                                    is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "xác nhận", "code", "mã", "factor", "authenticate", "profile"])

                                if is_target and is_security_mail:
                                    safe_msg = raw_msg.lower().replace(self.email.lower(), "")
                                    clean_text = re.sub(r'<[^>]+>', ' ', safe_msg).replace(" ", "")
                                    code = None

                                    if force_8_digits:
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_text)
                                        if match_8:
                                            code = match_8.group(1)
                                    else:
                                        match_body_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_text)
                                        match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                        match_code = re.search(r'(?<!\d)(\d{5,8})(?!\d)', clean_text)
                                        if match_body_8:
                                            code = match_body_8.group(1)
                                        elif match_sub:
                                            code = match_sub.group(1)
                                        elif match_code:
                                            code = match_code.group(1)

                                    if code:
                                        self.seen_msg_ids.add(msg_id)
                                        if not multi_mode:
                                            print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}")
                                        return code
                else:
                    status_err = f"Lỗi HTTP {response.status_code}"
                    if status_err != last_logged and not multi_mode:
                        print(f"{Colors.color_text(f'[API Smail1s] {status_err}', Colors.WARNING)}")
                        last_logged = status_err

            except requests.exceptions.RequestException as e:
                err_str = "Lỗi kết nối Smail1s. Đang thử lại..."
                if err_str != last_logged and not multi_mode:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str} (Chi tiết: {e})', Colors.WARNING)}")
                    last_logged = err_str
                try:
                    self._init_session()
                except Exception:
                    pass

            except Exception as e:
                err_str = f"Lỗi không xác định: {str(e)}"
                if err_str != last_logged and not multi_mode:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str}', Colors.WARNING)}")
                    last_logged = err_str

            time.sleep(random.uniform(5.0, 8.0))
        return None


class AutoSMSService:
    def __init__(self, api_key, country="vn", proxy=None, service="facebook"):
        self.api_key = api_key
        self.country = country
        self.service = service
        self.base_url = "https://autosms.site/api"
        self.order_id = None
        self.phone = None
        self.proxy = proxy

    def buy_number(self):
        url = f"{self.base_url}/buy-number/{self.country}/{self.service}?key={self.api_key}"
        try:
            r = requests.get(url, timeout=10, proxies=self.proxy)
            js = r.json()
            if js.get("success"):
                self.phone = js["data"]["phone"]
                self.order_id = js["data"]["order_id"]
                return self.phone
        except Exception:
            pass
        return None

    def get_otp_code(self, timeout=120):
        if not self.order_id:
            return None
        start_time = time.time()
        url = f"{self.base_url}/orders/{self.order_id}?key={self.api_key}"
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set():
                return None
            try:
                r = requests.get(url, timeout=10, proxies=self.proxy)
                js = r.json()
                if js.get("success") and js.get("data") and js["data"].get("code"):
                    return js["data"]["code"]
            except Exception:
                pass
            time.sleep(4)
        return None

    def cancel_order(self):
        if self.order_id:
            try:
                requests.get(f"{self.base_url}/cancel/{self.order_id}?key={self.api_key}", timeout=10, proxies=self.proxy)
            except Exception:
                pass


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


def select_mode():
    built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
    built_in_print(f"{Colors.NUMBER}6. {Colors.VALUE}THUÊ SỐ ĐIỆN THOẠI  \033[97m[ Dùng API AutoSMS.site ]{Colors.RESET}")
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

        if config_key == 'last_file_mode2':
            is_proxy_format = any(':' in l and '@' not in l for l in lines)
            if is_proxy_format:
                built_in_print(f"{Colors.ERROR}LỖI: Tệp này chứa Proxy, KHÔNG PHẢI danh sách Email!{Colors.RESET}")
                built_in_print(f"{Colors.WARNING}Gợi ý: Nếu không có sẵn file Email, hãy chạy Mode 1 (Tự động tạo email tạm thời).{Colors.RESET}")
                config_data.pop(config_key, None)
                save_config(config_data)
                return []

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
            built_in_print(f"{Colors.WARNING}Số thứ tự không hợp lệ, sẽ tự động chạy tất cả!{Colors.RESET}")
            return lines
        else:
            selected_lines = lines[start_idx - 1:end_idx]
            built_in_print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} data (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
            return selected_lines
    else:
        return [e.strip() for e in file_path.split(",") if e.strip()]


# ==================== CẤU HÌNH DELAY & TIỆN ÍCH ADB ====================
def doc_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()


def luu_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def ap_dung_config_chong_checkpoint():
    """Ghi đè bộ thông số thời gian chuẩn Anti-Checkpoint (giữ lại mật khẩu cũ nếu người dùng đã đặt)"""
    config_moi = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cu = json.load(f)
                if cu.get('mat_khau_fb'):
                    config_moi['mat_khau_fb'] = cu['mat_khau_fb']
                if 'doi_ip_may_bay' in cu:
                    config_moi['doi_ip_may_bay'] = cu['doi_ip_may_bay']
                if 'doi_android_id' in cu:
                    config_moi['doi_android_id'] = cu['doi_android_id']
        except Exception:
            pass
    luu_config(config_moi)
    return config_moi


def nhap_delay(tieu_de, gia_tri_mac_dinh):
    try:
        nhap = input(f'   {tieu_de} ({gia_tri_mac_dinh} giây): ').strip()
        if nhap:
            return float(nhap)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass
    return gia_tri_mac_dinh


def cau_hinh_delay():
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}⚙️  CẤU HÌNH DELAY & ANTI-CHECKPOINT (ĐỔI IP MÁY BAY + ANDROID ID)')
    print('──────────────────────────────────────────────────────────────────────')
    config = doc_config()

    print(f'1. Áp dụng ngay bộ Delay Chuẩn Anti-Checkpoint (Khuyên dùng - Nhanh & Ổn định)')
    print(f'2. Tự chỉnh từng thông số Delay thủ công')
    chon_loai = input('   Chọn (1 hoặc 2, Enter=1): ').strip()

    hoi_may_bay = input(f"   Bật tự động đổi IP 4G bằng Chế độ máy bay? (y/n, Enter={'y' if config.get('doi_ip_may_bay', True) else 'n'}): ").strip().lower()
    if hoi_may_bay in ['y', 'n']:
        config['doi_ip_may_bay'] = (hoi_may_bay == 'y')

    hoi_android_id = input(f"   Bật tự động đổi mã phần cứng Android ID mỗi acc? (y/n, Enter={'y' if config.get('doi_android_id', True) else 'n'}): ").strip().lower()
    if hoi_android_id in ['y', 'n']:
        config['doi_android_id'] = (hoi_android_id == 'y')

    if chon_loai != '2':
        luu_config(config)
        config = ap_dung_config_chong_checkpoint()
        mat_khau_moi = input(f"   Nhập mật khẩu FB muốn đặt (Enter giữ '{config['mat_khau_fb']}'): ").strip()
        if mat_khau_moi:
            config['mat_khau_fb'] = mat_khau_moi
        if config.get('doi_ip_may_bay', True):
            config['thoi_gian_bat_may_bay'] = nhap_delay('Thời gian ngâm Chế độ máy bay để nhả IP cũ', config.get('thoi_gian_bat_may_bay', 5.0))
            config['thoi_gian_cho_4g'] = nhap_delay('Thời gian chờ 4G kết nối lại sau khi tắt máy bay', config.get('thoi_gian_cho_4g', 6.0))
        luu_config(config)
        print('\n✅ Đã áp dụng cấu hình Anti-Checkpoint & Đổi IP 4G!')
        return config

    print('\n📌 CÁC THÔNG SỐ DELAY (giây):')
    print('──────────────────────────────────────────────────')
    print(f'\n{trang}【MẬT KHẨU & ĐỔI IP 4G】{trang}')
    mat_khau_moi = input('   Nhập mật khẩu muốn đặt: ').strip()
    if mat_khau_moi:
        config['mat_khau_fb'] = mat_khau_moi
    config['thoi_gian_bat_may_bay'] = nhap_delay('Thời gian giữ Chế độ máy bay', config.get('thoi_gian_bat_may_bay', 5.0))
    config['thoi_gian_cho_4g'] = nhap_delay('Thời gian chờ 4G lên mạng lại', config.get('thoi_gian_cho_4g', 6.0))

    print(f'\n{trang}【MỞ FACEBOOK】{trang}')
    config['delay_mo_facebook'] = nhap_delay('Delay mở Facebook', config['delay_mo_facebook'])

    print(f'\n{trang}【CÁC BƯỚC ĐĂNG KÝ】{trang}')
    config['delay_chon_khong_cho_phep'] = nhap_delay('Delay chọn Không cho phép', config['delay_chon_khong_cho_phep'])
    config['delay_click_khoang_trong'] = nhap_delay('Delay sau khi click khoảng trống tắt gợi ý TK', config.get('delay_click_khoang_trong', 0.6))
    config['delay_chon_toi_co_tai_khoan_roi'] = nhap_delay('Delay chọn Tôi có tài khoản rồi', config['delay_chon_toi_co_tai_khoan_roi'])
    config['delay_click_tao_tk_lan1'] = nhap_delay('Delay click Tạo tài khoản lần 1', config['delay_click_tao_tk_lan1'])
    config['delay_click_tao_tk_lan2'] = nhap_delay('Delay click Tạo tài khoản lần 2', config['delay_click_tao_tk_lan2'])
    config['delay_chon_khong_cho_phep_lan2'] = nhap_delay('Delay chọn Không cho phép lần 2', config['delay_chon_khong_cho_phep_lan2'])
    config['delay_nhap_ho'] = nhap_delay('Delay sau nhập Họ', config['delay_nhap_ho'])
    config['delay_nhap_ten'] = nhap_delay('Delay sau nhập Tên', config['delay_nhap_ten'])
    config['delay_click_tiep_lan1'] = nhap_delay('Delay click Tiếp lần 1', config['delay_click_tiep_lan1'])
    config['delay_click_chon'] = nhap_delay('Delay click CHỌN', config['delay_click_chon'])
    config['delay_click_tiep_lan2'] = nhap_delay('Delay click Tiếp lần 2', config['delay_click_tiep_lan2'])
    config['delay_click_tiep_lan3'] = nhap_delay('Delay click Tiếp lần 3', config['delay_click_tiep_lan3'])
    config['delay_nhap_tuoi'] = nhap_delay('Delay sau nhập Tuổi', config['delay_nhap_tuoi'])
    config['delay_click_tiep_lan4'] = nhap_delay('Delay click Tiếp lần 4', config['delay_click_tiep_lan4'])
    config['delay_click_ok'] = nhap_delay('Delay click OK', config['delay_click_ok'])
    config['delay_chon_gioi_tinh'] = nhap_delay('Delay sau chọn giới tính', config['delay_chon_gioi_tinh'])
    config['delay_click_tiep_lan5'] = nhap_delay('Delay click Tiếp lần 5', config['delay_click_tiep_lan5'])

    print(f'\n{trang}【NHẬP SĐT & MK】{trang}')
    config['delay_nhap_sdt'] = nhap_delay('Delay sau nhập SĐT', config['delay_nhap_sdt'])
    config['delay_click_tiep_sdt'] = nhap_delay('Delay click Tiếp sau SĐT', config['delay_click_tiep_sdt'])
    config['delay_click_tiep_tuc_tao_tk'] = nhap_delay('Delay click Tiếp tục tạo TK', config['delay_click_tiep_tuc_tao_tk'])
    config['delay_kiem_tra_sdt'] = nhap_delay('Delay kiểm tra SĐT hợp lệ', config['delay_kiem_tra_sdt'])
    config['delay_nhap_mat_khau'] = nhap_delay('Delay sau nhập Mật khẩu', config['delay_nhap_mat_khau'])
    config['delay_click_tiep_sau_mk'] = nhap_delay('Delay click Tiếp sau MK', config['delay_click_tiep_sau_mk'])
    config['delay_click_luu'] = nhap_delay('Delay click Lưu', config['delay_click_luu'])
    config['delay_cho_toi_dong_y'] = nhap_delay('Delay chờ Tôi đồng ý', config['delay_cho_toi_dong_y'])
    config['delay_kiem_tra_loi'] = nhap_delay('Delay kiểm tra lỗi đăng ký', config['delay_kiem_tra_loi'])
    config['delay_click_tiep_tuc'] = nhap_delay('Delay click Tiếp tục', config['delay_click_tiep_tuc'])
    config['delay_click_khong_cho_phep'] = nhap_delay('Delay click Không cho phép', config['delay_click_khong_cho_phep'])
    config['delay_click_khong_cho_phep_lan2'] = nhap_delay('Delay click Không cho phép lần 2', config['delay_click_khong_cho_phep_lan2'])

    print(f'\n{trang}【XÁC NHẬN EMAIL & AVATAR】{trang}')
    config['delay_buoc_dung_fb'] = nhap_delay('Delay buộc dừng FB', config['delay_buoc_dung_fb'])
    config['delay_mo_lai_fb'] = nhap_delay('Delay mở lại FB', config['delay_mo_lai_fb'])
    config['delay_click_toi_khong_nhan_duoc_ma'] = nhap_delay('Delay click Tôi không nhận được mã', config['delay_click_toi_khong_nhan_duoc_ma'])
    config['delay_click_xac_nhan_email'] = nhap_delay('Delay click Xác nhận bằng email', config['delay_click_xac_nhan_email'])
    config['delay_nhap_email'] = nhap_delay('Delay sau nhập Email', config['delay_nhap_email'])
    config['delay_click_tiep_sau_email'] = nhap_delay('Delay click Tiếp sau Email', config['delay_click_tiep_sau_email'])
    config['delay_get_code'] = nhap_delay('Delay giữa các lần get code', config['delay_get_code'])
    config['delay_nhap_code'] = nhap_delay('Delay sau nhập Code', config['delay_nhap_code'])
    config['delay_click_tiep_cuoi'] = nhap_delay('Delay click Tiếp lần cuối', config['delay_click_tiep_cuoi'])
    config['delay_up_avatar'] = nhap_delay('Delay chờ tải xong Avatar', config.get('delay_up_avatar', 8.0))

    print(f'\n{trang}【VÒNG LẶP】{trang}')
    config['delay_giua_cac_lan_chay'] = nhap_delay('Delay giữa các lần chạy', config['delay_giua_cac_lan_chay'])
    config['delay_thu_lai_khi_loi'] = nhap_delay('Delay thử lại khi lỗi', config['delay_thu_lai_khi_loi'])
    config['so_lan_thu_get_code'] = int(nhap_delay('Số lần thử get code', config['so_lan_thu_get_code']))

    luu_config(config)
    print('\n✅ Đã lưu cấu hình!')
    return config


def print_multi_status():
    PAUSE_FOR_INPUT.wait()
    with log_lock:
        if device_steps:
            for _ in range(len(device_steps)):
                sys.stdout.write('\x1b[F\x1b[K')
            sys.stdout.flush()
            for i, (device, step) in enumerate(device_steps.items(), 1):
                if '✅' in step or '🎉' in step:
                    color = xanh
                elif '❌' in step:
                    color = do
                elif '⚠️' in step or '⏰' in step:
                    color = vang
                else:
                    color = xanh_duong
                built_in_print(f"{color}{i}. {device:<25} | {step}{trang}")
            sys.stdout.flush()


def update_step(device_name, step):
    if not multi_mode:
        print(f"[{device_name}] {step}")
        return
    PAUSE_FOR_INPUT.wait()
    with log_lock:
        if device_name in device_last_step and device_last_step[device_name] == step:
            return
        device_last_step[device_name] = step
        device_steps[device_name] = step
    print_multi_status()


def lay_email_tu_file_an_toan():
    with email_lock:
        if os.path.exists(GOM_HOTMAIL_FILE):
            with open(GOM_HOTMAIL_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines = [l.strip() for l in lines if l.strip()]
            if lines:
                dong = lines[0]
                parts = dong.split('|')
                if len(parts) >= 4:
                    email_addr = parts[0]
                    mat_khau_mail = parts[1]
                    refresh_token = parts[2]
                    client_id = parts[3]
                    with open(GOM_HOTMAIL_FILE, 'w', encoding='utf-8') as f:
                        for line in lines[1:]:
                            if line.strip():
                                f.write(line + '\n')
                    return (email_addr, mat_khau_mail, refresh_token, client_id)
    return (None, None, None, None)


def doc_tele():
    if os.path.exists(TELE_FILE):
        with open(TELE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            token = None
            id_tele = None
            for line in lines:
                if line.startswith('Token:'):
                    token = line.replace('Token:', '').strip()
                elif line.startswith('ID:'):
                    id_tele = line.replace('ID:', '').strip()
            return (token, id_tele)
    return (None, None)


def luu_tele(token, id_tele):
    with open(TELE_FILE, 'w', encoding='utf-8') as f:
        f.write(f'Token: {token}\n')
        f.write(f'ID: {id_tele}\n')


def gui_tele(token, id_tele, noi_dung):
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        payload = {'chat_id': id_tele, 'text': noi_dung, 'parse_mode': 'HTML'}
        requests.post(url, json=payload, timeout=10)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass


def luu_tai_khoan_fb(email_or_phone, password, two_fa):
    """Lưu thẳng thông tin Email/SĐT, Mật khẩu và 2FA vào FB_NhaTrong.txt trực tiếp từ thiết bị (Chống Checkpoint)"""
    two_fa_str = two_fa if two_fa else 'NO_2FA'
    with open(FB_ACCOUNT_FILE, 'a', encoding='utf-8') as f:
        f.write(f'{email_or_phone} | {password} | {two_fa_str}\n')


def chay_lenh_adb(cmd, serial=None):
    try:
        if serial:
            subprocess.run(f'adb -s {serial} {cmd}', shell=True, capture_output=True)
        else:
            subprocess.run(f'adb {cmd}', shell=True, capture_output=True)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass


def chay_lenh_adb_lay_ket_qua(cmd, serial=None, timeout=8):
    try:
        full_cmd = f'adb -s {serial} {cmd}' if serial else f'adb {cmd}'
        res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (res.stdout or '').strip()
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return ''


def lay_ip_hien_tai_adb(serial=None):
    for url in ['https://api.ipify.org', 'https://icanhazip.com', 'https://ifconfig.me/ip']:
        out = chay_lenh_adb_lay_ket_qua(f'shell curl -s --max-time 4 {url}', serial, timeout=6)
        if out and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', out.strip()):
            return out.strip()
    return None


def lam_moi_thong_so_thiet_bi_adb(serial=None, config=None):
    if config and not config.get('doi_android_id', True):
        return
    new_android_id = ''.join(random.choices('0123456789abcdef', k=16))
    chay_lenh_adb(f'shell settings put secure android_id {new_android_id}', serial)
    chay_lenh_adb('shell logcat -c', serial)


def doi_ip_che_do_may_bay_adb(serial=None, device_name="Device", config=None):
    if config and not config.get('doi_ip_may_bay', True):
        return

    tg_may_bay = config.get('thoi_gian_bat_may_bay', 5.0) if config else 5.0
    tg_cho_4g = config.get('thoi_gian_cho_4g', 6.0) if config else 6.0

    chay_lenh_adb('shell svc wifi disable', serial)
    chay_lenh_adb('shell svc data enable', serial)

    ip_cu = lay_ip_hien_tai_adb(serial)

    update_step(device_name, f"✈️ Đang bật Chế độ máy bay ({tg_may_bay}s) | IP cũ: {ip_cu or 'Đang lấy'}...")
    chay_lenh_adb('shell cmd connectivity airplane-mode enable', serial)
    chay_lenh_adb('shell settings put global airplane_mode_on 1', serial)
    chay_lenh_adb('shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true', serial)

    time.sleep(tg_may_bay)

    update_step(device_name, "📡 Đang tắt Chế độ máy bay & chờ 4G kết nối lại...")
    chay_lenh_adb('shell cmd connectivity airplane-mode disable', serial)
    chay_lenh_adb('shell settings put global airplane_mode_on 0', serial)
    chay_lenh_adb('shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false', serial)
    chay_lenh_adb('shell svc wifi disable', serial)
    chay_lenh_adb('shell svc data enable', serial)

    time.sleep(tg_cho_4g)

    ip_moi = None
    for _ in range(3):
        ip_moi = lay_ip_hien_tai_adb(serial)
        if ip_moi:
            break
        time.sleep(2)

    if ip_moi:
        update_step(device_name, f"🌐 Đổi IP 4G thành công: {ip_cu or 'N/A'} -> {ip_moi}")
    else:
        update_step(device_name, "⚠️ Đã bật/tắt máy bay xong (4G đang ổn định ngầm)")


def cap_quyen_bo_nho_fb(serial=None):
    permissions = [
        'android.permission.READ_EXTERNAL_STORAGE',
        'android.permission.WRITE_EXTERNAL_STORAGE',
        'android.permission.READ_MEDIA_IMAGES',
        'android.permission.CAMERA'
    ]
    for perm in permissions:
        chay_lenh_adb(f'shell pm grant com.facebook.katana {perm}', serial)


def khoa_xoay_man_hinh(serial=None):
    chay_lenh_adb('shell settings put system accelerometer_rotation 0', serial)


def xoa_du_lieu_fb(serial=None):
    chay_lenh_adb('shell settings put secure autofill_service null', serial)
    chay_lenh_adb('shell settings put secure credential_service null', serial)
    chay_lenh_adb('shell settings put secure credential_service_primary null', serial)
    chay_lenh_adb('shell cmd autofill destroy', serial)

    chay_lenh_adb('shell am force-stop com.facebook.katana', serial)
    time.sleep(0.15)
    chay_lenh_adb('shell pm clear com.facebook.katana', serial)
    time.sleep(0.25)

    chay_lenh_adb('shell pm clear com.facebook.services', serial)
    chay_lenh_adb('shell pm clear com.facebook.appmanager', serial)

    chay_lenh_adb('shell am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS', serial)
    time.sleep(0.2)


def get_devices():
    try:
        result = subprocess.run('adb devices', shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        for line in lines:
            if line.strip() and 'device' in line and 'offline' not in line:
                serial = line.split()[0]
                devices.append((serial, serial))
        return devices
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return []


# ==================== GIAO DIỆN ĐIỀU KHIỂN FACEBOOK UI (6 CHẾ ĐỘ + AUTO 2FA + AUTO AVATAR + LƯU TRỰC TIẾP CHỐNG CHECKPOINT) ====================
class FacebookUI:

    def __init__(self, serial=None, device_name=None, config=None, avatar_folder=""):
        if serial:
            self.d = u2.connect(serial)
            self.serial = serial
            self.device_name = device_name if device_name else serial
        else:
            self.d = u2.connect()
            self.serial = None
            self.device_name = "Device"
        self.package = 'com.facebook.katana'
        self.config = config
        self.avatar_folder = avatar_folder

    def log(self, text):
        if multi_mode and self.device_name:
            update_step(self.device_name, text)
        else:
            print(text)

    def lay_code_tu_mail(self, email_addr, refresh_token, client_id):
        self.log('🔢 Lấy code...')
        so_lan_thu = self.config['so_lan_thu_get_code']
        delay = self.config['delay_get_code']
        for i in range(so_lan_thu):
            url_code = 'https://tools.dongvanfb.net/api/graph_code'
            payload_code = {'email': email_addr, 'refresh_token': refresh_token, 'client_id': client_id, 'type': 'facebook'}
            try:
                ket_qua_code = requests.post(url_code, json=payload_code, timeout=10)
                du_lieu_code = ket_qua_code.json()
                if du_lieu_code.get('status') and du_lieu_code.get('code'):
                    code = du_lieu_code.get('code')
                    self.log(f'🔢 CODE: {code}')
                    return code
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:
                pass
            nghi_ngau_nhien(delay)
        self.log('❌ Không lấy được code')
        return None

    def click_text_chua(self, text, ten_nut, so_lan_thu=3, delay=0.8, click_duoi=False):
        for lan in range(so_lan_thu):
            if self.d(textContains=text).exists:
                elements = self.d(textContains=text)
                if click_duoi:
                    elem = elements[-1]
                else:
                    elem = elements[0] if hasattr(elements, '__getitem__') else elements
                elem.click()
                return True
            if self.d(descriptionContains=text).exists:
                elements = self.d(descriptionContains=text)
                if click_duoi:
                    elem = elements[-1]
                else:
                    elem = elements[0] if hasattr(elements, '__getitem__') else elements
                elem.click()
                return True
            time.sleep(delay)
        return False

    def click_toi_dong_y(self):
        if self.d(textContains='Tôi đồng ý').exists:
            elements = self.d(textContains='Tôi đồng ý')
            elements[-1].click()
            return True
        return False

    def click_text(self, text, ten_nut, so_lan_thu=3, delay=0.8):
        for lan in range(so_lan_thu):
            if self.d(text=text).exists:
                self.d(text=text).click()
                return True
            if self.d(description=text).exists:
                self.d(description=text).click()
                return True
            time.sleep(delay)
        return False

    def click_truong(self, ten_truong, double=False, so_lan_thu=3, delay=0.8):
        for lan in range(so_lan_thu):
            if self.d(text=ten_truong).exists:
                phan_tu = self.d(text=ten_truong)
                if double:
                    phan_tu.click()
                    time.sleep(0.2)
                phan_tu.click()
                return True
            if self.d(textContains=ten_truong).exists:
                phan_tu = self.d(textContains=ten_truong)[0]
                if double:
                    phan_tu.click()
                    time.sleep(0.2)
                phan_tu.click()
                return True
            time.sleep(delay)
        return False

    def nhap_text(self, text):
        self.d.send_keys(text)
        time.sleep(random.uniform(0.35, 0.55))

    def kiem_tra_text(self, danh_sach_text, so_lan_thu=2, delay=0.8):
        for lan in range(so_lan_thu):
            for text in danh_sach_text:
                if (
                    self.d(text=text).exists
                    or self.d(textContains=text).exists
                    or self.d(descriptionContains=text).exists
                ):
                    return True
            time.sleep(delay)
        return False

    def kiem_tra_loi_dang_ky(self):
        texts_loi = ['Để đăng ký, hãy đọc cũng như đồng ý với các điều khoản và chính sách của chúng tôi', 'Tìm hiểu thêm', 'Chính sách cookie']
        return self.kiem_tra_text(texts_loi, 2, 1)

    def click_khoang_trong_tat_goi_y(self):
        try:
            chay_lenh_adb('shell cmd autofill destroy', self.serial)
            chay_lenh_adb('shell am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS', self.serial)

            w, h = self.d.window_size()
            dau_hieu_goi_y = [
                'Tiếp tục với', 'Continue as', 'Chọn tài khoản', 'Choose an account',
                'Đăng nhập bằng tài khoản khác', 'Dùng tài khoản khác', 'Không phải bạn',
                'Tài khoản đã lưu', 'Saved accounts', 'Google'
            ]
            co_bang_goi_y = self.kiem_tra_text(dau_hieu_goi_y, 1, 0.2)
            chua_thay_nut_tao_tk = not (
                self.d(textContains='Tạo tài khoản mới').exists
                or self.d(descriptionContains='Tạo tài khoản mới').exists
                or self.d(textContains='Tôi có tài khoản rồi').exists
            )

            if co_bang_goi_y or chua_thay_nut_tao_tk:
                self.log('👆 Click ra khoảng trống tắt gợi ý tài khoản đã lưu...')
                self.d.click(int(w * 0.5), int(h * 0.12))
                time.sleep(0.3)
                self.d.click(int(w * 0.1), int(h * 0.12))
                nghi_ngau_nhien(self.config.get('delay_click_khoang_trong', 0.6))
            else:
                self.d.click(int(w * 0.5), int(h * 0.10))
                nghi_ngau_nhien(self.config.get('delay_click_khoang_trong', 0.6))
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception:
            pass

    def tao_so_dien_thoai(self, used_phones=None):
        if used_phones is not None and len(used_phones) >= 10000:
            used_phones.clear()
        while True:
            dau_so = ['333', '338', '339', '358', '359', '368', '369', '378', '379', '388', '389', '396', '397', '398', '399', '777', '778', '779', '787', '788', '789', '968', '969', '978', '979', '988', '989']
            so = random.choice(dau_so) + ''.join(random.choices(string.digits, k=6))
            phone = f'+84{so}'
            if used_phones is not None and phone in used_phones:
                continue
            if used_phones is not None:
                used_phones.add(phone)
            return phone

    def tao_ho_ten(self, used_names=None):
        if used_names is not None and len(used_names) >= 350:
            used_names.clear()
        while True:
            ho_list = ['Nguyen', 'Tran', 'Le', 'Pham', 'Hoang', 'Huynh', 'Phan', 'Vu', 'Vo', 'Dang', 'Bui', 'Do', 'Ngo', 'Duong', 'Ly', 'Dinh', 'Mai', 'Chau', 'Ha', 'Phung']
            ten_list = ['An', 'Binh', 'Cuong', 'Dung', 'Duc', 'Ha', 'Hieu', 'Hoa', 'Hung', 'Minh', 'Nam', 'Phuong', 'Quang', 'Son', 'Thanh', 'Thao', 'Thuy', 'Tien', 'Trung', 'Vinh']
            ho = random.choice(ho_list)
            ten = random.choice(ten_list)
            full_name = f'{ho} {ten}'
            if used_names is not None and full_name in used_names:
                continue
            if used_names is not None:
                used_names.add(full_name)
            return (ho, ten)

    def lay_otp_theo_che_do(self, mode, used_email, mail_service=None, imap_service=None, hotmail_service=None, uid_moc=0, refresh_token=None, client_id=None, force_8_digits=False):
        max_resend_attempts = 2
        loai_otp_str = "8 số từ body" if force_8_digits else "đăng ký"
        for attempt in range(max_resend_attempts + 1):
            if STOP_EVENT.is_set():
                return None

            otp_code = None
            if mode == "2" and not (mail_service and mail_service.token):
                with OTP_LOCK:
                    PAUSE_FOR_INPUT.clear()
                    built_in_print(f"\n{Colors.color_text(f'[{self.device_name}] Lần {attempt+1}: MỜI SẾP NHẬP OTP ({loai_otp_str}) CHO [{used_email}] TỪ BÀN PHÍM: ', Colors.SUCCESS)}", end="")
                    otp_code = input().strip()
                    PAUSE_FOR_INPUT.set()
            elif mode == "1" or (mode == "2" and mail_service and mail_service.token):
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Mail.tm (Lần {attempt+1})...')
                otp_code = mail_service.get_otp_code(timeout=100, force_8_digits=force_8_digits)
            elif mode in ["3", "4"] and imap_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Gmail IMAP (Lần {attempt+1})...')
                otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=100, force_8_digits=force_8_digits)
            elif mode == "5" and hotmail_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Smail1s (Lần {attempt+1})...')
                otp_code = hotmail_service.get_otp_code(timeout=120, force_8_digits=force_8_digits)
            elif refresh_token and client_id:
                otp_code = self.lay_code_tu_mail(used_email, refresh_token, client_id)

            if otp_code:
                self.log(f'🔢 CODE ({loai_otp_str}): {otp_code}')
                return otp_code

            if attempt < max_resend_attempts:
                self.log(f'⚠️ Chưa thấy mã ({loai_otp_str}) (Lần {attempt+1}), thử bấm gửi lại mã...')
                self.click_text_chua('Tôi không nhận được mã', 'Tôi không nhận được mã', 2, 0.5)
                time.sleep(1)
                self.click_text_chua('Gửi lại', 'Gửi lại', 2, 0.5) or self.click_text_chua('Nhận mã mới', 'Nhận mã mới', 2, 0.5)
                time.sleep(3)

        self.log(f'❌ Không lấy được code ({loai_otp_str}) sau khi thử lại')
        return None

    def trich_xuat_key_2fa_tu_man_hinh(self):
        try:
            for nut_copy in ['Sao chép khóa', 'Copy key', 'Sao chép', 'Copy']:
                if self.d(textContains=nut_copy).exists or self.d(descriptionContains=nut_copy).exists:
                    self.click_text_chua(nut_copy, nut_copy, 1, 0.5)
                    time.sleep(1)
                    clip_text = self.d.clipboard or ""
                    clean_clip = re.sub(r'[^A-Z2-7]', '', clip_text.upper())
                    if len(clean_clip) >= 16 and re.match(r'^[A-Z2-7]+$', clean_clip):
                        return clean_clip
        except Exception:
            pass

        try:
            xml_dump = self.d.dump_hierarchy()
            matches = re.findall(r'\b(?:[A-Z2-7]{4}[\s-]*){4,8}\b', xml_dump, re.IGNORECASE)
            for m in matches:
                clean_key = re.sub(r'[^A-Z2-7]', '', m.upper())
                if 16 <= len(clean_key) <= 64:
                    return clean_key
        except Exception:
            pass
        return None

    def dieu_huong_vao_man_hinh_2fa(self):
        chay_lenh_adb(
            'shell am start -a android.intent.action.VIEW -d "fb://faceweb/f?href=%2Fsecurity%2F2fac%2Fsetup%2Fintro"',
            self.serial
        )
        time.sleep(5)

        if not self.kiem_tra_text(['Xác thực 2 yếu tố', 'Two-factor', 'Ứng dụng xác thực', 'Authentication app', 'Bắt đầu', 'Get started', 'Chọn phương thức'], 2, 1):
            self.log('🛡️ Điều hướng 2FA qua Menu Cài đặt...')
            self.click_text_chua('Menu', 'Menu', 2, 0.5)
            time.sleep(1.5)
            try:
                self.d(scrollable=True).scroll.toEnd()
            except Exception:
                pass
            time.sleep(1)
            self.click_text_chua('Cài đặt & quyền riêng tư', 'Cài đặt & quyền riêng tư', 2, 0.5) or self.click_text_chua('Settings & privacy', 'Settings & privacy', 2, 0.5)
            time.sleep(1)
            self.click_text('Cài đặt', 'Cài đặt', 2, 0.5) or self.click_text('Settings', 'Settings', 2, 0.5)
            time.sleep(2.5)
            self.click_text_chua('Mật khẩu và bảo mật', 'Mật khẩu và bảo mật', 2, 0.5) or self.click_text_chua('Password and security', 'Password and security', 2, 0.5) or self.click_text_chua('Trung tâm tài khoản', 'Trung tâm tài khoản', 2, 0.5)
            time.sleep(2.5)
            self.click_text_chua('Mật khẩu và bảo mật', 'Mật khẩu và bảo mật', 2, 0.5) or self.click_text_chua('Password and security', 'Password and security', 2, 0.5)
            time.sleep(2)
            self.click_text_chua('Xác thực 2 yếu tố', 'Xác thực 2 yếu tố', 2, 0.5) or self.click_text_chua('Two-factor authentication', 'Two-factor authentication', 2, 0.5)
            time.sleep(3)

        if self.kiem_tra_text(['Chọn tài khoản', 'Select an account', 'Trang cá nhân', 'Profiles'], 2, 1):
            if self.d(className='android.view.ViewGroup', clickable=True).exists:
                self.d(className='android.view.ViewGroup', clickable=True)[0].click()
                time.sleep(3)

        for nut_bd in ['Bắt đầu', 'Get started', 'Sử dụng ứng dụng xác thực', 'Use authentication app']:
            if self.d(textContains=nut_bd).exists or self.d(descriptionContains=nut_bd).exists:
                self.click_text_chua(nut_bd, nut_bd, 1, 0.5)
                time.sleep(3)
                break

    def bat_2fa_fb(self, used_email, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, refresh_token_da_co=None, client_id_da_co=None):
        self.log('🛡️ Đang mở cài đặt Xác thực 2 yếu tố (2FA)...')
        two_fa_secret = ""
        try:
            for nut_bo_qua in ['Bỏ qua', 'Skip', 'Lúc khác', 'Not Now', 'Tiếp', 'Next', 'OK']:
                if self.d(text=nut_bo_qua).exists or self.d(description=nut_bo_qua).exists:
                    self.click_text(nut_bo_qua, nut_bo_qua, 1, 0.3)
                    time.sleep(0.5)

            self.dieu_huong_vao_man_hinh_2fa()

            if self.kiem_tra_text(['Nhập lại mật khẩu', 'Re-enter your password', 'Mật khẩu của bạn'], 1, 0.5):
                self.log('🔑 Nhập mật khẩu xác nhận bật 2FA...')
                if self.d(className='android.widget.EditText').exists:
                    self.d(className='android.widget.EditText')[0].click()
                    time.sleep(0.3)
                    self.nhap_text(self.config['mat_khau_fb'])
                    time.sleep(0.5)
                    self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5) or self.click_text_chua('Continue', 'Continue', 2, 0.5)
                    time.sleep(4)

            if self.kiem_tra_text(['Kiểm tra email', 'Check your email', 'Mã bảo mật', 'Nhập mã', 'Enter code', 'Xác nhận email'], 2, 1):
                self.log('📧 Phát hiện xác minh email khi bật 2FA -> Quét mã OTP 8 số trong body email...')
                uid_moc_2fa = 0
                if mode in ["3", "4"] and imap_service:
                    uid_moc_2fa = imap_service.get_latest_uid()

                verify_code = None
                if mode == "6" and autosms_service:
                    verify_code = autosms_service.get_otp_code(timeout=90)
                else:
                    verify_code = self.lay_otp_theo_che_do(
                        mode=mode,
                        used_email=used_email,
                        mail_service=mail_service,
                        imap_service=imap_service,
                        hotmail_service=hotmail_service,
                        uid_moc=uid_moc_2fa,
                        refresh_token=refresh_token_da_co,
                        client_id=client_id_da_co,
                        force_8_digits=True
                    )

                if verify_code:
                    self.log(f'🔢 Đã lấy mã xác minh 8 số từ body: {verify_code}. Đang nhập...')
                    if self.d(className='android.widget.EditText').exists:
                        self.d(className='android.widget.EditText')[0].click()
                        time.sleep(0.3)
                        self.nhap_text(verify_code)
                    else:
                        self.nhap_text(verify_code)
                    time.sleep(1)
                    self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5) or self.click_text_chua('Continue', 'Continue', 2, 0.5) or self.click_text_chua('Xác nhận', 'Xác nhận', 2, 0.5)
                    time.sleep(5)

                    self.log('🔄 Hoàn tất xác minh email! Quay trở lại quy trình thiết lập 2FA...')
                    if not self.kiem_tra_text(['Ứng dụng xác thực', 'Authentication app', 'Sao chép khóa', 'Copy key', 'Quét mã QR'], 2, 1):
                        self.dieu_huong_vao_man_hinh_2fa()

            for phuong_thuc in ['Ứng dụng xác thực', 'Authentication app', 'Sử dụng ứng dụng xác thực', 'Duo Mobile', 'Google Authenticator']:
                if self.d(textContains=phuong_thuc).exists or self.d(descriptionContains=phuong_thuc).exists:
                    self.click_text_chua(phuong_thuc, phuong_thuc, 2, 0.5)
                    time.sleep(1)
                    self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5, click_duoi=True) or self.click_text_chua('Continue', 'Continue', 2, 0.5, click_duoi=True) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.5, click_duoi=True)
                    time.sleep(4)
                    break

            self.log('🔑 Đang trích xuất khóa Secret Key 2FA...')
            for _ in range(5):
                two_fa_secret = self.trich_xuat_key_2fa_tu_man_hinh()
                if two_fa_secret:
                    break
                try:
                    self.d(scrollable=True).scroll.forward()
                except Exception:
                    pass
                time.sleep(1.5)

            if two_fa_secret:
                self.log(f'🔑 Đã lấy Secret Key 2FA: {two_fa_secret[:12]}...')
                for nut_tiep in ['Tiếp tục', 'Continue', 'Tiếp', 'Next', 'Nhập mã', 'Enter code']:
                    if self.d(textContains=nut_tiep).exists or self.d(descriptionContains=nut_tiep).exists:
                        self.click_text_chua(nut_tiep, nut_tiep, 2, 0.5, click_duoi=True)
                        time.sleep(3)
                        break

                totp_code = pyotp.TOTP(two_fa_secret).now()
                self.log(f'🔢 Sinh mã TOTP ({totp_code}) và kích hoạt 2FA...')
                if self.d(className='android.widget.EditText').exists:
                    self.d(className='android.widget.EditText')[0].click()
                    time.sleep(0.3)
                    self.nhap_text(totp_code)
                else:
                    self.click_text_chua('Nhập mã', 'Nhập mã', 2, 0.5) or self.click_text_chua('Mã xác nhận', 'Mã xác nhận', 2, 0.5)
                    time.sleep(0.3)
                    self.nhap_text(totp_code)
                time.sleep(1)

                for nut_xong in ['Tiếp tục', 'Continue', 'Tiếp', 'Next', 'Xác nhận', 'Xong', 'Done']:
                    if self.d(textContains=nut_xong).exists or self.d(descriptionContains=nut_xong).exists:
                        self.click_text_chua(nut_xong, nut_xong, 2, 0.5, click_duoi=True)
                        time.sleep(3)

                self.log(f'✅ BẬT 2FA THÀNH CÔNG: {two_fa_secret[:10]}...')
                return two_fa_secret
            else:
                self.log('⚠️ Không tìm thấy khóa 2FA trên màn hình, lưu acc không kèm 2FA')
                return ""
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi khi bật 2FA: {str(e)[:25]}')
            return ""

    def day_anh_qua_adb(self):
        if not self.avatar_folder or not os.path.isdir(self.avatar_folder):
            return None

        images = [f for f in os.listdir(self.avatar_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not images:
            self.log('⚠️ Thư mục Avatar trống, bỏ qua bước up ảnh!')
            return None

        chosen_img = random.choice(images)
        local_path = os.path.abspath(os.path.join(self.avatar_folder, chosen_img))
        ext = os.path.splitext(chosen_img)[1].lower() or '.jpg'
        remote_filename = f"IMG_{int(time.time() * 1000)}{ext}"
        remote_path = f"/sdcard/DCIM/Camera/{remote_filename}"

        try:
            cap_quyen_bo_nho_fb(self.serial)
            chay_lenh_adb('shell mkdir -p /sdcard/DCIM/Camera', self.serial)
            chay_lenh_adb('shell rm -f /sdcard/DCIM/Camera/IMG_*.jpg /sdcard/DCIM/Camera/IMG_*.png /sdcard/DCIM/Camera/IMG_*.jpeg /sdcard/DCIM/Camera/IMG_*.webp', self.serial)

            if self.serial:
                subprocess.run(f'adb -s {self.serial} push "{local_path}" "{remote_path}"', shell=True, capture_output=True)
            else:
                subprocess.run(f'adb push "{local_path}" "{remote_path}"', shell=True, capture_output=True)

            chay_lenh_adb(
                f'shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{remote_path}"',
                self.serial
            )
            time.sleep(1.5)
            return remote_path
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi đẩy ảnh ADB: {str(e)[:20]}')
            return None

    def up_avatar_fb(self):
        if not self.avatar_folder or not os.path.isdir(self.avatar_folder):
            return False

        self.log('🖼️ Đang đẩy ảnh từ PC vào điện thoại qua ADB...')
        remote_path = self.day_anh_qua_adb()
        if not remote_path:
            return False

        try:
            self.log('🖼️ Đang mở Trang cá nhân để cập nhật Avatar...')
            chay_lenh_adb(
                'shell am start -a android.intent.action.VIEW -d "fb://profile"',
                self.serial
            )
            time.sleep(4.5)

            for nut_dong in ['Lúc khác', 'Not Now', 'Bỏ qua', 'Skip', 'Đóng', 'Close', 'Dừng', 'Hủy']:
                if self.d(text=nut_dong).exists or self.d(description=nut_dong).exists:
                    self.click_text(nut_dong, nut_dong, 1, 0.3)
                    time.sleep(0.5)

            if not self.kiem_tra_text(['Thêm vào tin', 'Add to story', 'Chỉnh sửa trang cá nhân', 'Edit profile', 'ảnh đại diện', 'profile picture'], 2, 1):
                self.click_text_chua('Trang cá nhân', 'Trang cá nhân', 2, 0.5) or self.click_text_chua('Profile', 'Profile', 2, 0.5)
                time.sleep(3)

            da_click_khung_avatar = False
            nhan_avatar = ['Chọn ảnh đại diện', 'Select profile picture', 'Thêm ảnh đại diện', 'Add profile picture', 'ảnh đại diện', 'profile picture', 'Thêm ảnh', 'Add picture']
            for nhan in nhan_avatar:
                if self.d(textContains=nhan).exists or self.d(descriptionContains=nhan).exists:
                    self.click_text_chua(nhan, nhan, 1, 0.5)
                    da_click_khung_avatar = True
                    time.sleep(2)
                    break

            if not da_click_khung_avatar:
                w, h = self.d.window_size()
                self.d.click(int(w * 0.22), int(h * 0.32))
                time.sleep(2)

            for tuy_chon in ['Chọn ảnh đại diện', 'Select profile picture', 'Chọn trên Thiết bị', 'Chọn từ thư viện', 'Choose from Gallery', 'Tải ảnh lên']:
                if self.d(textContains=tuy_chon).exists or self.d(descriptionContains=tuy_chon).exists:
                    self.click_text_chua(tuy_chon, tuy_chon, 2, 0.5)
                    time.sleep(2.5)
                    break

            for nut_quyen in ['Cho phép tất cả', 'Allow all', 'Cho phép', 'Allow', 'Trong khi dùng ứng dụng', 'While using the app']:
                if self.d(textContains=nut_quyen).exists:
                    self.click_text_chua(nut_quyen, nut_quyen, 1, 0.5)
                    time.sleep(2)

            self.log('🖼️ Đang chọn ảnh từ thư viện thiết bị...')
            da_chon_anh = False
            if self.d(descriptionContains='Ảnh').exists or self.d(descriptionContains='Photo').exists:
                phan_tu_anh = self.d(descriptionContains='Ảnh') if self.d(descriptionContains='Ảnh').exists else self.d(descriptionContains='Photo')
                phan_tu_anh[0].click()
                da_chon_anh = True
            elif self.d(className='android.widget.GridView').exists:
                grid = self.d(className='android.widget.GridView')[0]
                if grid.child(clickable=True).exists:
                    grid.child(clickable=True)[0].click()
                    da_chon_anh = True

            if not da_chon_anh:
                w, h = self.d.window_size()
                self.d.click(int(w * 0.18), int(h * 0.35))

            time.sleep(2.5)

            self.log('💾 Đang bấm Lưu ảnh đại diện...')
            da_luu = False
            for nut_luu in ['Lưu', 'Save', 'Xong', 'Done', 'Áp dụng', 'Apply', 'Tiếp', 'Next', 'Chia sẻ', 'Share']:
                if self.d(text=nut_luu).exists or self.d(description=nut_luu).exists:
                    self.click_text(nut_luu, nut_luu, 2, 0.5)
                    da_luu = True
                    time.sleep(1.5)
                    if self.d(text='Lưu').exists or self.d(description='Lưu').exists:
                        self.click_text('Lưu', 'Lưu', 1, 0.5)
                    elif self.d(text='Save').exists or self.d(description='Save').exists:
                        self.click_text('Save', 'Save', 1, 0.5)
                    break

            if not da_luu:
                w, h = self.d.window_size()
                self.d.click(int(w * 0.90), int(h * 0.07))

            delay_avatar = self.config.get('delay_up_avatar', 8.0)
            self.log(f'⏳ Chờ {delay_avatar}s để Facebook tải lên Avatar...')
            nghi_ngau_nhien(delay_avatar, 0.15)
            self.log('✅ ĐÃ CẬP NHẬT AVATAR THÀNH CÔNG!')
            return True
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi khi up Avatar: {str(e)[:25]}')
            return False
        finally:
            if remote_path:
                chay_lenh_adb(f'shell rm -f "{remote_path}"', self.serial)

    def sdt(self, used_email, mode="1", mail_service=None, imap_service=None, hotmail_service=None, refresh_token_da_co=None, client_id_da_co=None, used_phones=None, used_names=None):
        while True:
            self.log('📞 Nhập số điện thoại...')
            so_dt = self.tao_so_dien_thoai(used_phones)
            if self.click_truong('Số di động', False, 3, 0.8):
                self.nhap_text(so_dt)
                self.log(f'📞 {so_dt}')
            nghi_ngau_nhien(self.config['delay_nhap_sdt'])
            self.log('⏩ Click Tiếp')
            if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                nghi_ngau_nhien(self.config['delay_click_tiep_sdt'])
                self.click_text_chua('Tiếp tục tạo tài khoản', 'Tiếp tục tạo tài khoản', 2, 0.8, click_duoi=True)
                nghi_ngau_nhien(self.config['delay_click_tiep_tuc_tao_tk'])
                texts_loi = ['Số di động của bạn là gì?', 'Nhập số di động có thể dùng để liên hệ với bạn.']
                if self.kiem_tra_text(texts_loi, 2, self.config['delay_kiem_tra_sdt']):
                    self.log('⚠️ Số điện thoại không hợp lệ, nhập lại...')
                    self.click_truong('Số di động', False, 2, 0.5)
                    time.sleep(0.3)
                    self.d.clear_text()
                    time.sleep(0.5)
                    continue
                mat_khau_fb = self.config['mat_khau_fb']
                self.log('🔑 Nhập Mật khẩu')
                if self.click_truong('Mật khẩu', False, 5, 0.8):
                    self.nhap_text(mat_khau_fb)
                    nghi_ngau_nhien(self.config['delay_nhap_mat_khau'])
                    self.log('⏩ Click Tiếp')
                    if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                        nghi_ngau_nhien(self.config['delay_click_tiep_sau_mk'])
                        self.log('💾 Click Lưu')
                        self.click_text_chua('Lưu', 'Lưu', 2, 0.5, click_duoi=True)
                        nghi_ngau_nhien(self.config['delay_click_luu'])
                        self.log('✅ Click Tôi đồng ý')
                        self.click_toi_dong_y()
                        nghi_ngau_nhien(self.config['delay_cho_toi_dong_y'], 0.1)
                        if self.kiem_tra_loi_dang_ky():
                            return None
                        self.log('⏩ Click Tiếp tục')
                        self.click_text_chua('Tiếp tục', 'Tiếp tục', 3, 0.8)
                        nghi_ngau_nhien(self.config['delay_click_tiep_tuc'])
                        self.log('❌ Click Không cho phép')
                        self.click_text_chua('Không cho phép', 'Không cho phép', 2, 0.5) or self.click_text_chua('TỪ CHỐI', 'TỪ CHỐI', 2, 0.5)
                        nghi_ngau_nhien(self.config['delay_click_khong_cho_phep'])
                        self.click_text_chua('Không cho phép', 'Không cho phép', 2, 0.5) or self.click_text_chua('TỪ CHỐI', 'TỪ CHỐI', 2, 0.5)
                        nghi_ngau_nhien(self.config['delay_click_khong_cho_phep_lan2'])
                        self.log('⏹️ Buộc dừng Facebook')
                        chay_lenh_adb('shell am force-stop com.facebook.katana', self.serial)
                        khoa_xoay_man_hinh(self.serial)
                        nghi_ngau_nhien(self.config['delay_buoc_dung_fb'])
                        self.log('🚀 Mở lại Facebook')
                        chay_lenh_adb('shell am start -n com.facebook.katana/com.facebook.katana.LoginActivity', self.serial)
                        khoa_xoay_man_hinh(self.serial)
                        nghi_ngau_nhien(self.config['delay_mo_lai_fb'], 0.15)
                        self.log('📧 Click Tôi không nhận được mã')
                        self.click_text_chua('Tôi không nhận được mã', 'Tôi không nhận được mã', 3, 0.8)
                        nghi_ngau_nhien(self.config['delay_click_toi_khong_nhan_duoc_ma'])
                        self.log('📧 Click Xác nhận bằng email')
                        self.click_text_chua('Xác nhận bằng email', 'Xác nhận bằng email', 3, 0.8)
                        nghi_ngau_nhien(self.config['delay_click_xac_nhan_email'])

                        if used_email:
                            uid_moc = 0
                            if mode in ["3", "4"] and imap_service:
                                uid_moc = imap_service.get_latest_uid()
                            elif mode == "5" and hotmail_service:
                                self.log('📧 Khởi tạo mốc hộp thư Smail1s...')
                                hotmail_service.init_baseline()

                            self.log(f'📧 Nhập Email: {used_email[:25]}')
                            if self.click_truong('Email', False, 3, 0.8):
                                self.nhap_text(used_email)
                            nghi_ngau_nhien(self.config['delay_nhap_email'])
                            self.log('⏩ Click Tiếp')
                            if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                                nghi_ngau_nhien(self.config['delay_click_tiep_sau_email'])
                                code = self.lay_otp_theo_che_do(
                                    mode=mode,
                                    used_email=used_email,
                                    mail_service=mail_service,
                                    imap_service=imap_service,
                                    hotmail_service=hotmail_service,
                                    uid_moc=uid_moc,
                                    refresh_token=refresh_token_da_co,
                                    client_id=client_id_da_co,
                                    force_8_digits=False
                                )
                                if code:
                                    self.log('🔢 Nhập mã xác nhận')
                                    if self.click_text_chua('Mã xác nhận', 'Mã xác nhận', 3, 0.8):
                                        self.nhap_text(code)
                                    nghi_ngau_nhien(self.config['delay_nhap_code'])
                                    self.log('⏩ Click Tiếp lần cuối')
                                    if self.click_text_chua('Tiếp', 'Tiếp lần cuối', 3, 0.8):
                                        nghi_ngau_nhien(self.config['delay_click_tiep_cuoi'])
                                        self.log(f'✅ XÁC MINH EMAIL XONG: {used_email} -> Quay sang bật 2FA...')
                                        two_fa_key = self.bat_2fa_fb(
                                            used_email=used_email,
                                            mode=mode,
                                            mail_service=mail_service,
                                            imap_service=imap_service,
                                            hotmail_service=hotmail_service,
                                            refresh_token_da_co=refresh_token_da_co,
                                            client_id_da_co=client_id_da_co
                                        )
                                        # Tự động đẩy ảnh qua ADB và cập nhật Avatar sau khi bật 2FA
                                        self.up_avatar_fb()
                                        return (used_email, mat_khau_fb, two_fa_key)
                        return None
                    else:
                        return None
                else:
                    return None
            else:
                return None

    def sdt_mode6_autosms(self, autosms_service: AutoSMSService):
        """Chế độ 6: Đăng ký và nhận mã OTP trực tiếp qua AutoSMS.site, sau đó bật 2FA và up Avatar"""
        self.log('📞 Đang thuê số từ AutoSMS.site...')
        so_dt = autosms_service.buy_number()
        if not so_dt:
            self.log('❌ Không thể thuê SĐT (Hết số hoặc sai API Key)!')
            return None

        if self.click_truong('Số di động', False, 3, 0.8):
            self.nhap_text(so_dt)
            self.log(f'📞 Đã nhập số thuê: {so_dt}')
        nghi_ngau_nhien(self.config['delay_nhap_sdt'])
        self.log('⏩ Click Tiếp')
        if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
            nghi_ngau_nhien(self.config['delay_click_tiep_sdt'])
            time.sleep(2.5)
            self.click_text_chua('Tiếp tục tạo tài khoản', 'Tiếp tục tạo tài khoản', 2, 0.8, click_duoi=True)
            nghi_ngau_nhien(self.config['delay_click_tiep_tuc_tao_tk'])
            texts_loi = ['Số di động của bạn là gì?', 'Nhập số di động có thể dùng để liên hệ với bạn.']
            if self.kiem_tra_text(texts_loi, 2, self.config['delay_kiem_tra_sdt']):
                self.log('⚠️ SĐT thuê không hợp lệ trên FB, đang hủy đơn...')
                autosms_service.cancel_order()
                return None

            mat_khau_fb = self.config['mat_khau_fb']
            self.log('🔑 Nhập Mật khẩu')
            if self.click_truong('Mật khẩu', False, 5, 0.8):
                self.nhap_text(mat_khau_fb)
                nghi_ngau_nhien(self.config['delay_nhap_mat_khau'])
                self.log('⏩ Click Tiếp')
                if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                    nghi_ngau_nhien(self.config['delay_click_tiep_sau_mk'])
                    self.log('💾 Click Lưu')
                    self.click_text_chua('Lưu', 'Lưu', 2, 0.5, click_duoi=True)
                    nghi_ngau_nhien(self.config['delay_click_luu'])
                    self.log('✅ Click Tôi đồng ý')
                    self.click_toi_dong_y()
                    nghi_ngau_nhien(self.config['delay_cho_toi_dong_y'], 0.1)
                    if self.kiem_tra_loi_dang_ky():
                        autosms_service.cancel_order()
                        return None
                    self.log('⏩ Click Gửi mã qua SMS')
                    self.click_text_chua('Gửi mã qua SMS', 'Gửi mã qua SMS', 2, 0.5)
                    nghi_ngau_nhien(self.config['delay_click_tiep_tuc'])
                    self.click_text_chua('Gửi mã qua SMS', 'Gửi mã qua SMS', 2, 0.5)
                    time.sleep(2.5)
                    self.log('⏹️ Buộc dừng Facebook')
                    chay_lenh_adb('shell am force-stop com.facebook.katana', self.serial)
                    khoa_xoay_man_hinh(self.serial)
                    nghi_ngau_nhien(self.config['delay_buoc_dung_fb'])
                    self.log('🚀 Mở lại Facebook')
                    chay_lenh_adb('shell am start -n com.facebook.katana/com.facebook.katana.LoginActivity', self.serial)
                    khoa_xoay_man_hinh(self.serial)
                    nghi_ngau_nhien(self.config['delay_mo_lai_fb'], 0.15)
                    self.click_text_chua('Gửi mã qua SMS', 'Gửi mã qua SMS', 2, 0.5)
                    self.log('🔢 Chờ code AutoSMS (max 90s)...')
                    code = autosms_service.get_otp_code(timeout=90)
                    if not code:
                        self.log('🔢 Thử gửi lại code SMS...')
                        self.click_text_chua('Tôi không nhận được mã', 'Tôi không nhận được mã', 2, 0.5)
                        time.sleep(0.5)
                        self.click_text_chua('Gửi mã qua SMS', 'Gửi mã qua SMS', 2, 0.5)
                        time.sleep(0.5)
                        self.click_text_chua('Gửi lại mã đến SMS', 'Gửi lại mã đến SMS', 2, 0.5)
                        time.sleep(6)
                        code = autosms_service.get_otp_code(timeout=90)

                    if not code:
                        self.log('❌ Không có mã SMS! Đang hủy đơn hoàn tiền...')
                        autosms_service.cancel_order()
                        return None

                    self.log(f'🔢 Nhập mã xác nhận: {code}')
                    if self.click_text_chua('Mã xác nhận', 'Mã xác nhận', 3, 0.8):
                        self.nhap_text(code)
                        nghi_ngau_nhien(self.config['delay_nhap_code'])
                        self.log('⏩ Click Tiếp lần cuối')
                        if self.click_text_chua('Tiếp', 'Tiếp lần cuối', 3, 0.8):
                            nghi_ngau_nhien(self.config['delay_click_tiep_cuoi'])
                            self.log(f'✅ XÁC MINH SĐT XONG: {so_dt} -> Tiến hành bật 2FA...')
                            two_fa_key = self.bat_2fa_fb(
                                used_email=so_dt,
                                mode="6",
                                autosms_service=autosms_service
                            )
                            # Tự động đẩy ảnh qua ADB và cập nhật Avatar sau khi bật 2FA
                            self.up_avatar_fb()
                            return (so_dt, mat_khau_fb, two_fa_key)
        autosms_service.cancel_order()
        return None

    def chay_dang_ky(self, used_email=None, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, refresh_token_da_co=None, client_id_da_co=None, used_phones=None, used_names=None):
        # 1. Đầu tiên xóa sạch dữ liệu app, tắt Autofill/Smart Lock, làm mới Android ID và đổi IP 4G qua Chế độ máy bay
        self.log('🧹 Xóa dữ liệu FB & tắt Autofill/Smart Lock...')
        xoa_du_lieu_fb(self.serial)
        lam_moi_thong_so_thiet_bi_adb(self.serial, self.config)
        doi_ip_che_do_may_bay_adb(self.serial, self.device_name, self.config)

        self.log('🔒 Khóa xoay & Cấp quyền bộ nhớ')
        khoa_xoay_man_hinh(self.serial)
        cap_quyen_bo_nho_fb(self.serial)

        # 2. Bật ứng dụng Facebook trên IP 4G mới và Android ID mới
        self.log('🚀 Mở Facebook')
        chay_lenh_adb('shell am start -n com.facebook.katana/com.facebook.katana.LoginActivity', self.serial)
        self.log(f"⏳ Chờ {self.config['delay_mo_facebook']} giây")
        nghi_ngau_nhien(self.config['delay_mo_facebook'], 0.1)

        # 3. Xử lý bảng hỏi quyền nếu có
        self.log('❌ Không cho phép')
        self.click_text_chua('Không cho phép', 'Không cho phép', 2, 0.5, click_duoi=True) or self.click_text_chua('TỪ CHỐI', 'TỪ CHỐI', 2, 0.5, click_duoi=True)
        nghi_ngau_nhien(self.config['delay_chon_khong_cho_phep'])

        # 4. Click ra khoảng trống để tắt bảng gợi ý các tài khoản đã lưu (nếu còn sót)
        self.click_khoang_trong_tat_goi_y()

        # 5. Chuyển vào luồng Tạo tài khoản mới
        self.log('👤 Tôi có tài khoản')
        self.click_text_chua('Tôi có tài khoản rồi', 'Tôi có tài khoản rồi', 2, 0.5, click_duoi=True) or self.click_text_chua('I already have a profile', 'I already have a profile', 2, 0.5, click_duoi=True)
        nghi_ngau_nhien(self.config['delay_chon_toi_co_tai_khoan_roi'])

        if not (self.d(textContains='Tạo tài khoản mới').exists or self.d(descriptionContains='Tạo tài khoản mới').exists):
            self.click_khoang_trong_tat_goi_y()

        self.log('➕ Tạo tài khoản')
        if self.click_text_chua('Tạo tài khoản mới', 'Tạo tài khoản mới', 3, 0.8):
            nghi_ngau_nhien(self.config['delay_click_tao_tk_lan1'])
            self.log('➕ Tạo TK lần 2')
            self.click_text_chua('Tạo tài khoản mới', 'Tạo tài khoản mới', 3, 0.5, click_duoi=True)
            nghi_ngau_nhien(self.config['delay_click_tao_tk_lan2'])
            self.log('❌ Không cho phép')
            self.click_text_chua('Không cho phép', 'Không cho phép', 2, 0.5, click_duoi=True) or self.click_text_chua('TỪ CHỐI', 'TỪ CHỐI', 2, 0.5, click_duoi=True)
            nghi_ngau_nhien(self.config['delay_chon_khong_cho_phep_lan2'])
            w, h = self.d.window_size()
            self.d.click(int(w / 2), int(h / 2))
            ho, ten = self.tao_ho_ten(used_names)
            self.log(f'📝 Họ: {ho}')
            if self.click_truong('Họ', False, 3, 0.8):
                self.nhap_text(ho)
            nghi_ngau_nhien(self.config['delay_nhap_ho'])
            self.d.click(int(w / 2), int(h / 2))
            self.log(f'📝 Tên: {ten}')
            if self.click_truong('Tên', False, 3, 0.8):
                self.nhap_text(ten)
            nghi_ngau_nhien(self.config['delay_nhap_ten'])
            self.d.click(int(w / 2), int(h / 2))
            self.log('⏩ Tiếp')
            if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                nghi_ngau_nhien(self.config['delay_click_tiep_lan1'])
                self.log('📅 Hủy/Chọn ngày sinh')
                self.click_text_chua('HỦY', 'HỦY', 3, 0.8) or self.click_text_chua('CHỌN', 'CHỌN', 2, 0.5, click_duoi=True)
                nghi_ngau_nhien(self.config['delay_click_chon'])
                self.log('⏩ Tiếp')
                if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                    nghi_ngau_nhien(self.config['delay_click_tiep_lan2'])
                    self.log('⏩ Tiếp')
                    if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                        nghi_ngau_nhien(self.config['delay_click_tiep_lan3'])
                        self.log('🎂 Nhập Tuổi')
                        tuoi = str(random.randint(19, 36))
                        if self.click_truong('Tuổi', False, 3, 0.8):
                            self.nhap_text(tuoi)
                            self.log(f'🎂 Tuổi: {tuoi}')
                        nghi_ngau_nhien(self.config['delay_nhap_tuoi'])
                        self.log('⏩ Tiếp')
                        if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                            nghi_ngau_nhien(self.config['delay_click_tiep_lan4'])
                            self.log('✅ OK')
                            self.click_text('OK', 'OK', 3, 0.8)
                            nghi_ngau_nhien(self.config['delay_click_ok'])
                            self.log('👤 Giới tính')
                            gioi_tinh = random.choice(['Nam', 'Nữ'])
                            self.click_text(gioi_tinh, gioi_tinh, 3, 0.8)
                            self.log(f'👤 {gioi_tinh}')
                            nghi_ngau_nhien(self.config['delay_chon_gioi_tinh'])
                            self.log('⏩ Tiếp')
                            if self.click_text_chua('Tiếp', 'Tiếp', 3, 0.8):
                                nghi_ngau_nhien(self.config['delay_click_tiep_lan5'])
                                self.log('📱 Số di động')
                                if self.click_text_chua('Số di động', 'Số di động', 3, 0.8):
                                    if mode == "6" and autosms_service:
                                        return self.sdt_mode6_autosms(autosms_service)
                                    return self.sdt(
                                        used_email=used_email,
                                        mode=mode,
                                        mail_service=mail_service,
                                        imap_service=imap_service,
                                        hotmail_service=hotmail_service,
                                        refresh_token_da_co=refresh_token_da_co,
                                        client_id_da_co=client_id_da_co,
                                        used_phones=used_phones,
                                        used_names=used_names
                                    )
        xoa_du_lieu_fb(self.serial)
        return None


def khoi_tao_dich_vu_theo_mode(mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country):
    used_email = ""
    mail_service = None
    imap_service = None
    hotmail_service = None
    autosms_service = None

    if mode == "1":
        mail_service = MailService(proxy=req_proxy)
        random_user = f"fb_{uuid.uuid4().hex[:8]}{random.randint(10, 99)}"
        used_email = mail_service.create_account(random_user)
        if not used_email:
            return None, None, None, None, None
        mail_service.authenticate()

    elif mode == "2":
        with DATA_LOCK:
            if len(data_source) == 0:
                return None, None, None, None, None
            used_email = data_source.pop(0)
        if "mail.tm" in used_email.lower():
            mail_service = MailService(proxy=req_proxy)
            pass_to_use = manual_password if manual_password else "TempPass123!"
            mail_service.authenticate(used_email, pass_to_use)

    elif mode == "3":
        with DATA_LOCK:
            if len(data_source) == 0:
                return None, None, None, None, None
            used_email, app_pass = data_source.pop(0)
        imap_service = GmailIMAPService(used_email, app_pass)

    elif mode == "4":
        with DATA_LOCK:
            if len(data_source) == 0:
                return None, None, None, None, None
            used_email = data_source.pop(0)
        imap_service = GmailIMAPService(base_gmail, app_password)

    elif mode == "5":
        with DATA_LOCK:
            if len(data_source) == 0:
                return None, None, None, None, None
            data_line = data_source.pop(0)
        used_email = data_line.split('|')[0]
        hotmail_service = HotmailAPIService(data_line, api_mode, proxy=req_proxy)

    elif mode == "6":
        autosms_service = AutoSMSService(autosms_api_key, autosms_country, proxy=req_proxy, service="facebook")
        used_email = "AUTOSMS_MODE_6"

    return used_email, mail_service, imap_service, hotmail_service, autosms_service


def chay_mot_thiet_bi_loop(serial, device_name, config, mode, data_source, manual_password=None, base_gmail=None, app_password=None, api_mode=None, avatar_folder="", proxies_list=None, autosms_api_key=None, autosms_country="vn", device_idx=0):
    used_names = set()
    used_phones = set()
    req_proxy = None
    if proxies_list:
        raw_proxy = proxies_list[device_idx % len(proxies_list)]
        req_proxy = format_proxy(raw_proxy)

    while not stop_flag.is_set():
        try:
            used_email, mail_service, imap_service, hotmail_service, autosms_service = khoi_tao_dich_vu_theo_mode(
                mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country
            )
            if not used_email:
                update_step(device_name, '⚠️ Đã hết dữ liệu đầu vào hoặc lỗi tạo mail! Dừng luồng...')
                break

            fb_ui = FacebookUI(serial, device_name, config, avatar_folder=avatar_folder)
            if mode != "6":
                update_step(device_name, f'📧 Dùng: {used_email[:25]}')
            else:
                update_step(device_name, '📱 Đang chạy Mode 6 (AutoSMS)...')

            ket_qua = fb_ui.chay_dang_ky(
                used_email=used_email,
                mode=mode,
                mail_service=mail_service,
                imap_service=imap_service,
                hotmail_service=hotmail_service,
                autosms_service=autosms_service,
                used_phones=used_phones,
                used_names=used_names
            )

            if ket_qua:
                email_or_phone, mat_khau_fb, two_fa_key = ket_qua
                # LƯU TRỰC TIẾP TỪ THIẾT BỊ KHÔNG GỌI API LOGIN TRÊN PC (CHỐNG CHECKPOINT 100%)
                luu_tai_khoan_fb(email_or_phone, mat_khau_fb, two_fa_key)
                token_tele, id_tele = doc_tele()
                if token_tele and id_tele:
                    two_fa_display = two_fa_key if two_fa_key else 'NO_2FA'
                    noi_dung = (
                        f'<code>{html.escape(str(email_or_phone))}</code> | '
                        f'<code>{html.escape(mat_khau_fb)}</code> | '
                        f'<code>{html.escape(two_fa_display)}</code>'
                    )
                    gui_tele(token_tele, id_tele, noi_dung)
                update_step(device_name, f'✅ THÀNH CÔNG: {email_or_phone} (2FA: {two_fa_key[:8] if two_fa_key else "None"})')
            else:
                update_step(device_name, '❌ ĐĂNG KÝ THẤT BẠI')

            nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            update_step(device_name, f'❌ Lỗi: {str(e)[:25]}')
            nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])


def main():
    global multi_mode
    token_tele, id_tele = doc_tele()
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}🤖 𝗧𝗢𝗢𝗟 𝗖𝗥𝗘𝗔𝗧𝗘 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞 𝗔𝗗𝗕 (𝗔𝗡𝗧𝗜-𝗖𝗛𝗘𝗖𝗞𝗣𝗢𝗜𝗡𝗧 𝗗 I R E C T){trang}')
    print('──────────────────────────────────────────────────────────────────────')

    if os.path.exists(CONFIG_FILE):
        chon_config = input('Chọn cấu hình Delay: [a = Chuẩn Anti-Checkpoint + Đổi IP 4G (Khuyên dùng) / y = Giữ file cũ / n = Tự chỉnh] (Enter=a): ').strip().lower()
        if chon_config == 'y':
            config = doc_config()
            print('✅ Đã tải cấu hình cũ!')
        elif chon_config == 'n':
            config = cau_hinh_delay()
        else:
            config = ap_dung_config_chong_checkpoint()
            print('✅ Đã nạp cấu hình Chuẩn Anti-Checkpoint + Tự động đổi IP 4G & Android ID!')
    else:
        config = ap_dung_config_chong_checkpoint()
        print('✅ Đã khởi tạo cấu hình Chuẩn Anti-Checkpoint + Tự động đổi IP 4G & Android ID!')

    trang_thai_ip = f"{xanh}✔ Bật{trang}" if config.get('doi_ip_may_bay', True) else f"{do}✘ Tắt{trang}"
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}📋  MENU CHÍNH')
    print('──────────────────────────────────────────────────────────────────────')
    print(f'1. Chạy Reg FB + Auto 2FA + Auto Avatar (Lưu trực tiếp chống Checkpoint)')
    print(f"2. Gửi Về Tele   │ {(f'{xanh}✔{trang} Đã cấu hình' if token_tele and id_tele else f'{do}✘{trang} Chưa cấu hình')}")
    print(f'3. Cấu Hình Delay │ Đổi IP Máy Bay: {trang_thai_ip} • Anti-Checkpoint')
    print('──────────────────────────────────────────────────────────────────────')

    chon = input('Chọn Đi Bé (1, 2 hoặc 3): ').strip()

    if chon == '2':
        print('\n──────────────────────────────────────────────────────────────────────')
        print('📧 CẤU HÌNH TELEGRAM')
        print('──────────────────────────────────────────────────────────────────────')
        token_tele, id_tele = doc_tele()
        if token_tele and id_tele:
            print(f'🔑 Token hiện tại: {token_tele}')
            print(f'🆔 ID hiện tại: {id_tele}')
            print('\n1. Dùng Lại Token Và ID Cũ')
            print('2. Cấu Hình Lại')
            print('3. Hủy Cấu Hình')
            chon_tele = input('Chọn: ').strip()
            if chon_tele == '1':
                print('✅ Sử dụng cấu hình cũ!')
            elif chon_tele == '2':
                token_tele_moi = input('Nhập Token mới: ').strip()
                id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
                if token_tele_moi and id_tele_moi:
                    luu_tele(token_tele_moi, id_tele_moi)
                    print('✅ Đã cập nhật cấu hình Telegram!')
                else:
                    print('❌ Token hoặc ID không hợp lệ!')
            elif chon_tele == '3':
                if os.path.exists(TELE_FILE):
                    os.remove(TELE_FILE)
                    print('🗑️ Đã xóa cấu hình Telegram!')
                else:
                    print('⚠️ Không có cấu hình để xóa!')
        else:
            print('⚠️ Chưa cấu hình Telegram!\n')
            token_tele_moi = input('Nhập Token: ').strip()
            id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
            if token_tele_moi and id_tele_moi:
                luu_tele(token_tele_moi, id_tele_moi)
                print('✅ Đã lưu cấu hình Telegram!')
        print('\n✅ Hoàn tất cấu hình! Chạy lại tool để bắt đầu.')
        input('Nhấn Enter để tiếp tục...')
        main()
        return

    elif chon == '3':
        cau_hinh_delay()
        print('\n✅ Đã cấu hình xong! Chạy lại tool để bắt đầu.')
        input('Nhấn Enter để tiếp tục...')
        main()
        return

    elif chon == '1':
        print('\n──────────────────────────────────────────────────────────────────────')
        print(f'{trang}🔥 CHỌN CHẾ ĐỘ XÁC MINH (6 MODES)')
        print('──────────────────────────────────────────────────────────────────────')
        config_data = load_config()
        mode = select_mode()

        data_source = []
        base_gmail = None
        app_password = None
        manual_password = None
        api_mode = None
        autosms_api_key = None
        autosms_country = "vn"

        if mode == "1":
            pass

        elif mode == "2":
            prompt_txt = f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}"
            data_source = process_file_input("last_file_mode2", prompt_txt)
            if any("mail.tm" in e.lower() for e in data_source):
                built_in_print(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}", end="")
                manual_password = input().strip()

        elif mode == "3":
            prompt_txt = f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}"
            raw_list = process_file_input("last_file_mode3", prompt_txt)
            for line in raw_list:
                parts = re.split(r'[|:]', line.strip())
                if len(parts) >= 2:
                    data_source.append((parts[0].strip(), parts[1].strip()))
            if not data_source:
                built_in_print(f"{Colors.ERROR}Danh sách Gmail IMAP không hợp lệ!{Colors.RESET}")
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
            api_mode = "oauth" if c == "1" else "graph" if c == "2" else "roundcube"
            prompt_txt = f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}"
            data_source = process_file_input("last_file_mode5", prompt_txt)

        elif mode == "6":
            built_in_print(f"{Colors.KEY}Nhập API Key của web Autosms.site: {Colors.RESET}", end="")
            autosms_api_key = input().strip()
            built_in_print(f"{Colors.KEY}Nhập Mã Quốc Gia thuê sim (VD: vn, us, kh - Bỏ trống mặc định là vn): {Colors.RESET}", end="")
            autosms_country = input().strip()
            if not autosms_country:
                autosms_country = "vn"
            data_source = ["dummy_for_sms"] * 999999

        if not data_source and mode not in ["1", "4", "6"]:
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
            built_in_print(f"\n{Colors.KEY}Nhập đường dẫn thư mục chứa ảnh làm Avatar (Bỏ trống nếu không muốn up): {Colors.RESET}", end="")
            avatar_folder_input = input().strip().strip('"').strip("'")
            if avatar_folder_input and os.path.isdir(avatar_folder_input):
                config_data["last_avatar_folder"] = avatar_folder_input
                save_config(config_data)

        built_in_print(f"\n{Colors.KEY}Nhập đường dẫn file Proxy (.txt) cho API Mail/SMS (Bỏ trống nếu không dùng): {Colors.RESET}", end="")
        proxy_file_input = input().strip().strip('"').strip("'")
        proxies_list = []
        if proxy_file_input and os.path.isfile(proxy_file_input):
            with open(proxy_file_input, 'r', encoding='utf-8') as f_proxy:
                proxies_list = [line.strip() for line in f_proxy if line.strip()]
            built_in_print(f"{Colors.SUCCESS}Đã tải {len(proxies_list)} Proxy từ tệp.{Colors.RESET}")

        try:
            devices = get_devices()
            if not devices:
                print(f'{do}❌ Không tìm thấy thiết bị ADB nào!{trang}')
                return

            print(f'\n{xanh}📱 TÌM THẤY {len(devices)} THIẾT BỊ:{trang}')
            for i, (serial, name) in enumerate(devices, 1):
                print(f'   {i}. {serial}')

            if len(devices) > 1:
                print(f'\n{vang}🚀 PHÁT HIỆN NHIỀU THIẾT BỊ{trang}')
                chon_multi = input('Bạn có muốn chạy đồng thời tất cả? (y/n): ').strip().lower()
                if chon_multi == 'y':
                    multi_mode = True
                    device_steps.clear()
                    device_last_step.clear()
                    stop_flag.clear()
                    print(f'\n{xanh}✅ ĐANG CHẠY ĐỒNG THỜI TRÊN {len(devices)} THIẾT BỊ...{trang}')
                    threads = []
                    for idx_dev, (serial, device_name) in enumerate(devices):
                        t = threading.Thread(
                            target=chay_mot_thiet_bi_loop,
                            args=(serial, serial, config, mode, data_source, manual_password, base_gmail, app_password, api_mode, avatar_folder_input, proxies_list, autosms_api_key, autosms_country, idx_dev)
                        )
                        t.daemon = True
                        t.start()
                        threads.append(t)
                    print(f'\n{xanh}Ý SỜI Ý SỜI')
                    print(f'{vang}BÚ MẠNH{trang}')
                    while any(t.is_alive() for t in threads):
                        time.sleep(1)
                    print(f'\n{vang}🏁 Đã hoàn tất chạy trên tất cả thiết bị!{trang}')
                    return
                else:
                    multi_mode = False
                    chon_device = input(f'Chọn thiết bị (1-{len(devices)}): ').strip()
                    try:
                        idx = int(chon_device) - 1
                        serial, device_name = devices[idx]
                    except Exception:
                        serial, device_name = devices[0]
            else:
                multi_mode = False
                serial, device_name = devices[0]

            used_names = set()
            used_phones = set()
            lan_chay = 0
            req_proxy = format_proxy(proxies_list[0]) if proxies_list else None

            while True:
                used_email, mail_service, imap_service, hotmail_service, autosms_service = khoi_tao_dich_vu_theo_mode(
                    mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country
                )
                if not used_email:
                    print(f'\n{vang}⚠️ Đã hết dữ liệu đầu vào hoặc lỗi tạo mail! Dừng chương trình.{trang}')
                    break

                lan_chay += 1
                print('\n──────────────────────────────────────────────────────────────────────')
                print(f'🔄 LẦN CHẠY THỨ {lan_chay} (MODE {mode})')
                print('──────────────────────────────────────────────────────────────────────')
                fb_ui = FacebookUI(serial, device_name, config, avatar_folder=avatar_folder_input)

                if mode != "6":
                    print(f'📧 Đang sử dụng Email: {used_email}')
                else:
                    print('📱 Đang sử dụng Chế độ 6 (Thuê SĐT AutoSMS.site)')

                ket_qua_dang_ky = fb_ui.chay_dang_ky(
                    used_email=used_email,
                    mode=mode,
                    mail_service=mail_service,
                    imap_service=imap_service,
                    hotmail_service=hotmail_service,
                    autosms_service=autosms_service,
                    used_phones=used_phones,
                    used_names=used_names
                )

                if ket_qua_dang_ky:
                    email_or_phone, mat_khau_fb, two_fa_key = ket_qua_dang_ky
                    print(f'\n✅ Đăng ký thành công! Tài khoản: {email_or_phone} | 2FA: {two_fa_key if two_fa_key else "Chưa bật"}')
                    # LƯU TRỰC TIẾP TỪ THIẾT BỊ KHÔNG GỌI API LOGIN TRÊN PC
                    luu_tai_khoan_fb(email_or_phone, mat_khau_fb, two_fa_key)
                    token_tele, id_tele = doc_tele()
                    if token_tele and id_tele:
                        two_fa_display = two_fa_key if two_fa_key else 'NO_2FA'
                        noi_dung = (
                            f'<code>{html.escape(str(email_or_phone))}</code> | '
                            f'<code>{html.escape(mat_khau_fb)}</code> | '
                            f'<code>{html.escape(two_fa_display)}</code>'
                        )
                        gui_tele(token_tele, id_tele, noi_dung)
                else:
                    print('\n❌ Đăng ký thất bại!')

                xoa_du_lieu_fb(serial)
                print(f"\n⏳ CHỜ {config['delay_giua_cac_lan_chay']} GIÂY...")
                nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])

        except KeyboardInterrupt:
            print(f'\n\n{do}🛑 ĐÃ DỪNG{trang}')
            stop_flag.set()
            sys.exit(0)
        except Exception as e:
            print(f'Lỗi: {e}')
    else:
        print('❌ Lựa chọn không hợp lệ!')
        return


if __name__ == '__main__':
    main()
