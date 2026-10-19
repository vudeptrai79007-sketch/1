# ==================== PHẦN 1/2 ====================
# --- SHIM CHO PYTHON 3.12+ (Khắc phục hoàn toàn lỗi thiếu distutils và .version) ---
import sys
import socket
import select
import base64
import io
import types
import re
import hmac

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

# CỜ CHỐNG BẬT CỬA SỔ CMD NGẦM GÂY LAG TRÊN WINDOWS
ADB_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

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
DEFAULT_AVATAR_DIR = os.path.join(os.getcwd(), 'avatars')

# CẤU HÌNH THỜI GIAN & ANTI-CHECKPOINT TỐI ƯU NHẤT
DEFAULT_CONFIG = {
    'doi_ip_may_bay': True,
    'thoi_gian_bat_may_bay': 5.0,
    'thoi_gian_cho_4g': 6.0,
    'doi_android_id': True,
    'delay_mo_facebook': 8.0,
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
    'delay_click_tiep_lan2': 1.0,
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
    'delay_cho_toi_dong_y': 12.0,
    'delay_kiem_tra_loi': 1.2,
    'delay_click_tiep_tuc': 1.0,
    'delay_click_khong_cho_phep': 0.6,
    'delay_click_khong_cho_phep_lan2': 0.5,
    'delay_buoc_dung_fb': 0.5,
    'delay_mo_lai_fb': 7.0,
    'delay_click_toi_khong_nhan_duoc_ma': 1.0,
    'delay_click_xac_nhan_email': 0.8,
    'delay_nhap_email': 1.0,
    'delay_click_tiep_sau_email': 2.5,
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


# ========== HÀM CHUYỂN ĐỔI KÝ TỰ 2FA SANG MÃ OTP 6 SỐ CHUẨN TOTP ==========
def lam_sach_key_2fa(raw_key):
    """Lọc bỏ khoảng trắng, dấu gạch ngang và chỉ giữ lại ký tự Base32 hợp lệ (A-Z, 2-7)"""
    if not raw_key:
        return ""
    return re.sub(r'[^A-Z2-7]', '', str(raw_key).upper())


def chuyen_doi_2fa_sang_otp(secret_key, doi_chu_ky_moi=True):
    """
    Chuyển đổi chuỗi Secret Key 2FA thành mã OTP 6 chữ số.
    Nếu thời gian hiệu lực của mã hiện tại còn dưới 5 giây, tự động chờ sang chu kỳ 30s mới.
    """
    clean_key = lam_sach_key_2fa(secret_key)
    if len(clean_key) < 8:
        return None

    if doi_chu_ky_moi:
        con_lai = 30 - (int(time.time()) % 30)
        if con_lai < 5:
            time.sleep(con_lai + 0.5)

    try:
        padding = (8 - (len(clean_key) % 8)) % 8
        padded_key = clean_key + ('=' * padding)
        key_bytes = base64.b32decode(padded_key, casefold=True)
        counter = int(time.time()) // 30
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key_bytes, msg, hashlib.sha1).digest()
        offset = digest[19] & 0x0F
        code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
        return f"{code_int:06d}"
    except Exception:
        pass

    try:
        padding = (8 - (len(clean_key) % 8)) % 8
        return pyotp.TOTP(clean_key + ('=' * padding)).now()
    except Exception:
        return None


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
        time.sleep(random.uniform(1.0, 4.0))

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
                                match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                match_body = re.search(r'(?<!\d)(\d{5,8})(?!\d)', clean_body)
                                if match_sub:
                                    code = match_sub.group(1)
                                elif match_body:
                                    code = match_body.group(1)

                            if code:
                                self.seen_msg_ids.add(msg_id)
                                return code
            except Exception:
                pass
            time.sleep(random.uniform(5.0, 8.0))
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

    def close(self):
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

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
        time.sleep(random.uniform(1.0, 4.0))

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
                                        match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                        match_body = re.search(r'(?<!\d)(\d{5,8})(?!\d)', safe_body)
                                        if match_sub:
                                            code = match_sub.group(1)
                                        elif match_body:
                                            code = match_body.group(1)

                                    if code:
                                        self.seen_uids.add(uid_bytes)
                                        return code
            except Exception:
                pass
            time.sleep(random.uniform(5.0, 8.0))
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
        time.sleep(random.uniform(1.0, 2.5))

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
                time.sleep(2)

    def get_otp_code(self, timeout=180, force_8_digits=False):
        start_time = time.time()
        loai_ma = "ÉP ĐỌC MÃ 8 SỐ TỪ BODY" if force_8_digits else "ĐỌC MÃ ĐĂNG KÝ"
        if not multi_mode:
            print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} ({loai_ma})...', Colors.INFO)}")

        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 3.5))
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
                                        match_sub = re.search(r'(?<!\d)(\d{5,8})(?!\d)', subject)
                                        match_code = re.search(r'(?<!\d)(\d{5,8})(?!\d)', clean_text)
                                        if match_sub:
                                            code = match_sub.group(1)
                                        elif match_code:
                                            code = match_code.group(1)

                                    if code:
                                        self.seen_msg_ids.add(msg_id)
                                        if not multi_mode:
                                            print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}")
                                        return code
            except Exception:
                try:
                    self._init_session()
                except Exception:
                    pass

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


def generate_dot_variants(gmail, max_limit=5000):
    """Giới hạn số lượng biến thể tránh tràn RAM & đơ CPU khi tên Gmail quá dài"""
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com":
        return [gmail]
    local = local.replace(".", "")
    if not local:
        return [gmail]

    variants = []
    total_masks = 1 << max(0, min(len(local) - 1, 14))
    for mask in range(total_masks):
        value = local[0]
        for i in range(1, len(local)):
            if mask & (1 << (i - 1)):
                value += "."
            value += local[i]
        variants.append(value + "@" + domain)
        if len(variants) >= max_limit:
            break
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

        start_idx = max(1, int(start_line) if start_line.isdigit() else 1)
        end_idx = min(total, int(end_line) if end_line.isdigit() else total)

        if start_idx > end_idx:
            return lines
        selected_lines = lines[start_idx - 1:end_idx]
        built_in_print(f"{Colors.INFO}=> Đã chọn {len(selected_lines)} data (Từ số {start_idx} đến {end_idx}){Colors.RESET}")
        return selected_lines
    else:
        return [e.strip() for e in file_path.split(",") if e.strip()]


# ==================== CẤU HÌNH DELAY & TIỆN ÍCH ADB (ĐÃ TỐI ƯU CHỐNG LAG) ====================
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

    hoi_may_bay = input(f"   Bật tự động đổi IP 4G bằng Chế độ máy bay? (y/n, Enter={'y' if config.get('doi_ip_may_bay', True) else 'n'}): ").strip().lower()
    if hoi_may_bay in ['y', 'n']:
        config['doi_ip_may_bay'] = (hoi_may_bay == 'y')

    hoi_android_id = input(f"   Bật tự động đổi mã phần cứng Android ID mỗi acc? (y/n, Enter={'y' if config.get('doi_android_id', True) else 'n'}): ").strip().lower()
    if hoi_android_id in ['y', 'n']:
        config['doi_android_id'] = (hoi_android_id == 'y')

    mat_khau_moi = input(f"   Nhập mật khẩu FB muốn đặt (Enter giữ '{config['mat_khau_fb']}'): ").strip()
    if mat_khau_moi:
        config['mat_khau_fb'] = mat_khau_moi

    if config.get('doi_ip_may_bay', True):
        config['thoi_gian_bat_may_bay'] = nhap_delay('Thời gian ngâm Chế độ máy bay để nhả IP cũ', config.get('thoi_gian_bat_may_bay', 5.0))
        config['thoi_gian_cho_4g'] = nhap_delay('Thời gian chờ 4G kết nối lại sau khi tắt máy bay', config.get('thoi_gian_cho_4g', 6.0))

    config['delay_mo_facebook'] = nhap_delay('Delay chờ mở Facebook', config.get('delay_mo_facebook', 8.0))
    config['delay_up_avatar'] = nhap_delay('Delay chờ tải xong Avatar', config.get('delay_up_avatar', 8.0))
    config['delay_giua_cac_lan_chay'] = nhap_delay('Delay giữa các lần chạy', config.get('delay_giua_cac_lan_chay', 4.0))

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


def doc_tele():
    if os.path.exists(TELE_FILE):
        with open(TELE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            token, id_tele = None, None
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
    """Lưu thẳng thông tin Email/SĐT, Mật khẩu và 2FA vào FB_NhaTrong.txt"""
    two_fa_str = two_fa if two_fa else 'NO_2FA'
    with DATA_LOCK:
        with open(FB_ACCOUNT_FILE, 'a', encoding='utf-8') as f:
            f.write(f'{email_or_phone} | {password} | {two_fa_str}\n')


def chay_lenh_adb(cmd, serial=None, timeout=15):
    """Chạy lệnh ADB ẩn hoàn toàn cửa sổ ngầm trên Windows (CREATE_NO_WINDOW) kèm timeout chống đơ"""
    try:
        full_cmd = f'adb -s {serial} {cmd}' if serial else f'adb {cmd}'
        subprocess.run(
            full_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=ADB_CREATION_FLAGS,
            timeout=timeout
        )
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        pass


def chay_lenh_adb_lay_ket_qua(cmd, serial=None, timeout=5):
    try:
        full_cmd = f'adb -s {serial} {cmd}' if serial else f'adb {cmd}'
        res = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            creationflags=ADB_CREATION_FLAGS,
            timeout=timeout
        )
        return (res.stdout or '').strip()
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception:
        return ''


def lay_ip_hien_tai_adb(serial=None):
    """Kiểm tra nhanh IP 4G trong tối đa 2 giây để không làm treo luồng"""
    out = chay_lenh_adb_lay_ket_qua(
        'shell "curl -s --max-time 2 https://api.ipify.org || wget -qO- -T 2 https://api.ipify.org"',
        serial,
        timeout=3
    )
    if out and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', out.strip()):
        return out.strip()
    return None


def lam_moi_thong_so_thiet_bi_adb(serial=None, config=None):
    if config and not config.get('doi_android_id', True):
        return
    new_android_id = ''.join(random.choices('0123456789abcdef', k=16))
    chay_lenh_adb(f'shell "settings put secure android_id {new_android_id}; logcat -c"', serial, timeout=8)


def doi_ip_che_do_may_bay_adb(serial=None, device_name="Device", config=None):
    if config and not config.get('doi_ip_may_bay', True):
        return

    tg_may_bay = config.get('thoi_gian_bat_may_bay', 5.0) if config else 5.0
    tg_cho_4g = config.get('thoi_gian_cho_4g', 6.0) if config else 6.0

    chay_lenh_adb('shell "svc wifi disable; svc data enable"', serial, timeout=8)
    ip_cu = lay_ip_hien_tai_adb(serial)

    update_step(device_name, f"✈️ Đang bật Chế độ máy bay ({tg_may_bay}s) | IP cũ: {ip_cu or 'Đang lấy'}...")
    lenh_bat_mb = (
        "cmd connectivity airplane-mode enable; "
        "settings put global airplane_mode_on 1; "
        "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"
    )
    chay_lenh_adb(f'shell "{lenh_bat_mb}"', serial, timeout=10)

    time.sleep(tg_may_bay)

    update_step(device_name, "📡 Đang tắt Chế độ máy bay & chờ 4G kết nối lại...")
    lenh_tat_mb = (
        "cmd connectivity airplane-mode disable; "
        "settings put global airplane_mode_on 0; "
        "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false; "
        "svc wifi disable; "
        "svc data enable"
    )
    chay_lenh_adb(f'shell "{lenh_tat_mb}"', serial, timeout=10)

    time.sleep(tg_cho_4g)

    ip_moi = lay_ip_hien_tai_adb(serial)
    if ip_moi:
        update_step(device_name, f"🌐 Đổi IP 4G thành công: {ip_cu or 'N/A'} -> {ip_moi}")
    else:
        update_step(device_name, "✅ Đã bật/tắt máy bay xong (4G đang kết nối ổn định)")


def cap_quyen_bo_nho_fb(serial=None):
    """Cấp quyền bộ nhớ/Camera và chặn quyền đọc danh bạ/tài khoản máy để chống dính vết nick cũ"""
    lenh_gop_quyen = (
        "pm grant com.facebook.katana android.permission.READ_EXTERNAL_STORAGE; "
        "pm grant com.facebook.katana android.permission.WRITE_EXTERNAL_STORAGE; "
        "pm grant com.facebook.katana android.permission.READ_MEDIA_IMAGES; "
        "pm grant com.facebook.katana android.permission.CAMERA; "
        "cmd appops set com.facebook.katana READ_EXTERNAL_STORAGE allow; "
        "cmd appops set com.facebook.katana WRITE_EXTERNAL_STORAGE allow; "
        "cmd appops set com.facebook.katana READ_MEDIA_IMAGES allow; "
        "cmd appops set com.facebook.katana MANAGE_EXTERNAL_STORAGE allow; "
        "cmd appops set com.facebook.katana GET_ACCOUNTS ignore; "
        "cmd appops set com.facebook.katana READ_CONTACTS ignore; "
        "cmd appops set com.facebook.katana READ_PHONE_STATE ignore; "
        "cmd appops set com.facebook.katana READ_PHONE_NUMBERS ignore"
    )
    chay_lenh_adb(f'shell "{lenh_gop_quyen}"', serial, timeout=10)


def khoa_xoay_man_hinh(serial=None):
    chay_lenh_adb('shell settings put system accelerometer_rotation 0', serial, timeout=5)


def xoa_du_lieu_fb(serial=None):
    """
    Làm sạch dữ liệu Facebook như máy mới nhưng KHÔNG làm đơ PackageManager của điện thoại:
    - Tắt tự động đồng bộ & hủy bộ nhớ Autofill/SmartLock
    - Chỉ xóa sạch dữ liệu com.facebook.katana và các thư mục rác ẩn trên thẻ nhớ
    """
    lenh_gop_xoa = (
        "settings put global auto_sync 0; "
        "settings put secure backup_auto_restore 0; "
        "settings put secure autofill_service null; "
        "settings put secure credential_service null; "
        "cmd autofill destroy; "
        "am force-stop com.facebook.katana; "
        "pm clear com.facebook.katana; "
        "rm -rf /sdcard/Android/data/com.facebook.katana /sdcard/Android/media/com.facebook.katana /sdcard/.facebook* /sdcard/facebook*; "
        "am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS"
    )
    chay_lenh_adb(f'shell "{lenh_gop_xoa}"', serial, timeout=12)
    time.sleep(0.4)


def get_devices():
    try:
        result = subprocess.run(
            'adb devices',
            shell=True,
            capture_output=True,
            text=True,
            creationflags=ADB_CREATION_FLAGS,
            timeout=10
        )
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


# ==================== CLASS ĐIỀU KHIỂN GIAO DIỆN FACEBOOK ====================
class FacebookUI:

    def __init__(self, serial=None, device_name=None, config=None, avatar_folder="", d_instance=None):
        if d_instance is not None:
            self.d = d_instance
            self.serial = serial
            self.device_name = device_name if device_name else (serial or "Device")
        elif serial:
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

    def chay_shell_nhanh(self, shell_cmd):
        """Gửi lệnh trực tiếp qua socket u2.shell kèm timeout=5s chống treo cứng luồng"""
        try:
            self.d.shell(shell_cmd, timeout=5)
        except Exception:
            chay_lenh_adb(f'shell {shell_cmd}', self.serial, timeout=8)

    def click_toa_do_an_toan(self, x, y):
        """Bắn tap trực tiếp qua socket shell để mượt và không bị MIUI chặn ngầm trên Xiaomi"""
        x, y = int(x), int(y)
        self.chay_shell_nhanh(f'input tap {x} {y}')

    def vuot_toa_do_an_toan(self, x1, y1, x2, y2, duration_ms=220):
        """Vuốt trực tiếp qua socket shell để cuộn mượt không lag PC"""
        x1, y1, x2, y2, duration_ms = int(x1), int(y1), int(x2), int(y2), int(duration_ms)
        self.chay_shell_nhanh(f'input swipe {x1} {y1} {x2} {y2} {duration_ms}')

    def _click_phan_tu_an_toan(self, elem):
        """Lấy tâm tọa độ của phần tử để tap qua socket shell + fallback u2.click"""
        try:
            b = elem.info['bounds']
            cx = (b['left'] + b['right']) // 2
            cy = (b['top'] + b['bottom']) // 2
            if cx > 0 and cy > 0:
                self.chay_shell_nhanh(f'input tap {cx} {cy}')
                return True
        except Exception:
            pass
        try:
            elem.click()
            return True
        except Exception:
            return False

    def click_text_chua(self, text, ten_nut="", so_lan_thu=3, delay=0.6, click_duoi=False):
        for _ in range(so_lan_thu):
            if self.d(textContains=text).exists:
                elements = self.d(textContains=text)
                elem = elements[-1] if click_duoi else (elements[0] if hasattr(elements, '__getitem__') else elements)
                if self._click_phan_tu_an_toan(elem):
                    return True
            if self.d(descriptionContains=text).exists:
                elements = self.d(descriptionContains=text)
                elem = elements[-1] if click_duoi else (elements[0] if hasattr(elements, '__getitem__') else elements)
                if self._click_phan_tu_an_toan(elem):
                    return True
            time.sleep(delay)
        return False

    def click_text(self, text, ten_nut="", so_lan_thu=3, delay=0.6):
        for _ in range(so_lan_thu):
            if self.d(text=text).exists:
                elem = self.d(text=text)[0] if hasattr(self.d(text=text), '__getitem__') else self.d(text=text)
                if self._click_phan_tu_an_toan(elem):
                    return True
            if self.d(description=text).exists:
                elem = self.d(description=text)[0] if hasattr(self.d(description=text), '__getitem__') else self.d(description=text)
                if self._click_phan_tu_an_toan(elem):
                    return True
            time.sleep(delay)
        return False

    def click_truong(self, ten_truong, double=False, so_lan_thu=3, delay=0.6):
        for _ in range(so_lan_thu):
            if self.d(text=ten_truong).exists:
                phan_tu = self.d(text=ten_truong)[0]
                if double:
                    self._click_phan_tu_an_toan(phan_tu)
                    time.sleep(0.2)
                if self._click_phan_tu_an_toan(phan_tu):
                    return True
            if self.d(textContains=ten_truong).exists:
                phan_tu = self.d(textContains=ten_truong)[0]
                if double:
                    self._click_phan_tu_an_toan(phan_tu)
                    time.sleep(0.2)
                if self._click_phan_tu_an_toan(phan_tu):
                    return True
            if self.d(descriptionContains=ten_truong).exists:
                phan_tu = self.d(descriptionContains=ten_truong)[0]
                if self._click_phan_tu_an_toan(phan_tu):
                    return True
            time.sleep(delay)
        return False

    def nhap_text(self, text):
        try:
            self.d.send_keys(str(text))
        except Exception:
            safe_str = str(text).replace(' ', '%s')
            self.chay_shell_nhanh(f'input text "{safe_str}"')
        time.sleep(random.uniform(0.3, 0.5))

    def kiem_tra_text(self, danh_sach_text, so_lan_thu=2, delay=0.5):
        for _ in range(so_lan_thu):
            for text in danh_sach_text:
                if (
                    self.d(text=text).exists
                    or self.d(textContains=text).exists
                    or self.d(descriptionContains=text).exists
                ):
                    return True
            time.sleep(delay)
        return False

    def tat_quyen_khong_cho_phep(self):
        """Tự động bấm KHÔNG CHO PHÉP khi hiện bảng hỏi quyền danh bạ / cuộc gọi"""
        cac_nut_tu_choi = [
            'KHÔNG CHO PHÉP',
            'Không cho phép',
            'TỪ CHỐI',
            'Từ chối',
            "DON'T ALLOW",
            'Don’t allow',
            'Deny'
        ]
        for nut in cac_nut_tu_choi:
            if self.d(text=nut).exists:
                self._click_phan_tu_an_toan(self.d(text=nut)[0])
                time.sleep(0.5)
                return True
            if self.d(textContains=nut).exists:
                self._click_phan_tu_an_toan(self.d(textContains=nut)[-1])
                time.sleep(0.5)
                return True
        return False

    def bo_qua_luu_thong_tin_dang_nhap(self):
        """
        Luôn bấm 'LÚC KHÁC' / 'Lúc khác' khi hiện bảng 'Lưu thông tin đăng nhập?' vào bản sao lưu.
        Tuyệt đối KHÔNG bấm 'LƯU' để tránh lần sau mở app bị tự đăng nhập lại acc cũ.
        """
        if self.kiem_tra_text([
            'Lưu thông tin đăng nhập',
            'bản sao lưu trên đám mây',
            'khôi phục từ bản sao lưu',
            'Lưu thông tin',
            'LÚC KHÁC'
        ], 1, 0.2):
            self.log('🚫 Phát hiện bảng Lưu thông tin đăng nhập -> Bấm "LÚC KHÁC" (Không lưu)')
            if not (
                self.click_text('LÚC KHÁC', 'LÚC KHÁC', 2, 0.4)
                or self.click_text('Lúc khác', 'Lúc khác', 2, 0.4)
                or self.click_text_chua('LÚC KHÁC', 'LÚC KHÁC', 1, 0.4)
                or self.click_text_chua('Lúc khác', 'Lúc khác', 1, 0.4, click_duoi=True)
                or self.click_text('KHÔNG LƯU', 'KHÔNG LƯU', 1, 0.3)
                or self.click_text('Không lưu', 'Không lưu', 1, 0.3)
                or self.click_text('Not now', 'Not now', 1, 0.3)
                or self.click_text('NOT NOW', 'NOT NOW', 1, 0.3)
            ):
                w, h = self.d.window_size()
                if self.kiem_tra_text(['khôi phục từ bản sao lưu', 'Bạn sẽ không cần nhập lại'], 1, 0.1):
                    self.click_toa_do_an_toan(int(w * 0.59), int(h * 0.58))
                else:
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.885))
            time.sleep(1.0)
            return True
        return False

    def dong_goi_y_google(self):
        """Đóng bảng gợi ý Google Smart Lock nếu bất ngờ hiện lên"""
        try:
            self.chay_shell_nhanh('cmd autofill destroy')
            if self.d(packageName='com.google.android.gms').exists:
                self.d.press('back')
                time.sleep(0.5)
        except Exception:
            pass

    def tao_ho_ten(self, used_names=None):
        if used_names is not None and len(used_names) >= 350:
            used_names.clear()
        while True:
            ho_list = ['Nguyen', 'Tran', 'Le', 'Pham', 'Hoang', 'Huynh', 'Phan', 'Vu', 'Vo', 'Dang', 'Bui', 'Do', 'Ngo', 'Duong']
            dem_list = ['Van', 'Minh', 'Hoang', 'Duc', 'Dinh', 'Gia', 'Bao', 'Quang', 'Tuan', 'Xuan', 'Ngoc', 'Thanh']
            ten_list = ['An', 'Binh', 'Cuong', 'Dung', 'Duc', 'Ha', 'Hieu', 'Hoa', 'Hung', 'Minh', 'Nam', 'Phuong', 'Quang', 'Son', 'Thanh', 'Thao', 'Thuy', 'Tien', 'Trung', 'Vinh']
            ho = random.choice(ho_list)
            ten = f"{random.choice(dem_list)} {random.choice(ten_list)}"
            full_name = f'{ho} {ten}'
            if used_names is not None and full_name in used_names:
                continue
            if used_names is not None:
                used_names.add(full_name)
            return (ho, ten)

    def tao_so_dien_thoai(self, used_phones=None):
        if used_phones is not None and len(used_phones) >= 10000:
            used_phones.clear()
        while True:
            dau_so = ['033', '034', '035', '036', '037', '038', '039', '070', '077', '078', '079', '083', '084', '085', '096', '097', '098']
            phone = random.choice(dau_so) + ''.join(random.choices(string.digits, k=7))
            if used_phones is not None and phone in used_phones:
                continue
            if used_phones is not None:
                used_phones.add(phone)
            return phone

    def _dang_hien_bang_chon_ngay(self):
        return (
            self.d(text='Chọn ngày').exists
            or self.d(text='CHỌN').exists
            or self.d(text='HỦY').exists
            or self.d(className='android.widget.NumberPicker').exists
            or self.d(resourceId='android:id/datePicker').exists
        )

    def _lay_toa_do_vung_to_do_ngay_sinh(self):
        w, h = self.d.window_size()
        x_do = int(w * 0.65)
        y_do = None

        for dau_hieu in ['Ngày sinh (', 'tuổi)', 'tháng', '2026', '2025']:
            for selector in [self.d(textContains=dau_hieu), self.d(descriptionContains=dau_hieu)]:
                try:
                    if selector.exists:
                        for i in range(selector.count):
                            b = selector[i].info['bounds']
                            cy = (b['top'] + b['bottom']) // 2
                            if int(h * 0.22) <= cy <= int(h * 0.42):
                                y_do = cy
                                break
                    if y_do:
                        break
                except Exception:
                    pass
            if y_do:
                break

        if not y_do:
            for sel_tiep in [self.d(text='Tiếp'), self.d(description='Tiếp'), self.d(textContains='Tiếp')]:
                try:
                    if sel_tiep.exists:
                        b_tiep = sel_tiep[0].info['bounds']
                        if b_tiep['top'] > int(h * 0.28):
                            y_do = b_tiep['top'] - int(h * 0.062)
                            break
                except Exception:
                    pass

        if not y_do:
            y_do = int(h * 0.30)

        return x_do, y_do

    def mo_bang_chon_ngay(self):
        w, h = self.d.window_size()

        for _ in range(8):
            if self._dang_hien_bang_chon_ngay():
                return True
            if self.kiem_tra_text(['Ngày sinh của bạn là khi nào', 'Ngày sinh (', 'tuổi)'], 1, 0.2):
                break
            time.sleep(0.4)

        for lan_bam in range(5):
            if self._dang_hien_bang_chon_ngay():
                return True

            x_do, y_do = self._lay_toa_do_vung_to_do_ngay_sinh()
            x_tap = x_do if lan_bam % 2 == 0 else int(w * 0.68)
            self.log(f'📅 Bấm vào vùng tô đỏ ô Ngày sinh ({x_tap}, {y_do}) để mở bảng 3 cột...')
            self.click_toa_do_an_toan(x_tap, y_do)
            time.sleep(1.1)

            if self._dang_hien_bang_chon_ngay():
                return True

        return self._dang_hien_bang_chon_ngay()

    def _lay_nam_hien_tai_trong_bang_3_cot(self):
        try:
            pickers = self.d(className='android.widget.NumberPicker')
            if pickers.count >= 3:
                ds_picker = []
                for i in range(pickers.count):
                    b = pickers[i].info['bounds']
                    ds_picker.append((b['left'], pickers[i]))
                ds_picker.sort(key=lambda item: item[0])
                cot_nam = ds_picker[2][1]

                edit_nam = cot_nam.child(className='android.widget.EditText')
                if edit_nam.exists:
                    txt = (edit_nam.info.get('text') or '').strip()
                    if txt.isdigit() and len(txt) == 4:
                        return int(txt)
        except Exception:
            pass

        try:
            inputs = self.d(resourceId='android:id/numberpicker_input')
            if inputs.count >= 3:
                ds_in = []
                for i in range(inputs.count):
                    b = inputs[i].info['bounds']
                    ds_in.append((b['left'], inputs[i].info.get('text') or ''))
                ds_in.sort(key=lambda item: item[0])
                txt_nam = ds_in[2][1].strip()
                if txt_nam.isdigit() and len(txt_nam) == 4:
                    return int(txt_nam)
        except Exception:
            pass
        return None

    def _kiem_tra_tuoi_hop_le_ngoai_man_hinh(self):
        try:
            xml_dump = self.d.dump_hierarchy()
            match_tuoi = re.search(r'\((\d+)\s*tuổi\)', xml_dump, re.IGNORECASE)
            if match_tuoi:
                so_tuoi = int(match_tuoi.group(1))
                return so_tuoi >= 18

            match_nam = re.findall(r'\b(19\d\d|20\d\d)\b', xml_dump)
            for nam_str in match_nam:
                nam_val = int(nam_str)
                if 1980 <= nam_val <= 2006:
                    return True
                if nam_val >= 2009:
                    return False
        except Exception:
            pass
        return False

    def vuot_chon_ngay_thang_nam_sinh(self):
        w, h = self.d.window_size()

        for lan_thu in range(4):
            if not self.mo_bang_chon_ngay():
                self.log('⚠️ Chưa hiện bảng Chọn ngày, bấm lại vào vùng tô đỏ...')
                x_do, y_do = self._lay_toa_do_vung_to_do_ngay_sinh()
                self.click_toa_do_an_toan(x_do, y_do)
                time.sleep(1.2)

            x_day = int(w * 0.295)
            x_month = int(w * 0.500)
            x_year = int(w * 0.705)
            y_top = int(h * 0.405)
            y_bot = int(h * 0.575)

            pickers = self.d(className='android.widget.NumberPicker')
            if pickers.count >= 3:
                try:
                    ds_bounds = [pickers[i].info['bounds'] for i in range(pickers.count)]
                    ds_bounds.sort(key=lambda b: b['left'])
                    b_day, b_month, b_year = ds_bounds[0], ds_bounds[1], ds_bounds[2]

                    x_day = (b_day['left'] + b_day['right']) // 2
                    x_month = (b_month['left'] + b_month['right']) // 2
                    x_year = (b_year['left'] + b_year['right']) // 2
                    y_top = b_year['top'] + int((b_year['bottom'] - b_year['top']) * 0.18)
                    y_bot = b_year['top'] + int((b_year['bottom'] - b_year['top']) * 0.82)
                except Exception:
                    pass

            self.log('📅 Đang vuốt chọn Cột 1 (Ngày) & Cột 2 (Tháng)...')
            for _ in range(random.randint(2, 4)):
                if random.choice([True, False]):
                    self.vuot_toa_do_an_toan(x_day, y_top, x_day, y_bot, 180)
                else:
                    self.vuot_toa_do_an_toan(x_day, y_bot, x_day, y_top, 180)
                time.sleep(0.25)

            for _ in range(random.randint(2, 4)):
                if random.choice([True, False]):
                    self.vuot_toa_do_an_toan(x_month, y_top, x_month, y_bot, 180)
                else:
                    self.vuot_toa_do_an_toan(x_month, y_bot, x_month, y_top, 180)
                time.sleep(0.25)

            nam_muc_tieu = random.randint(1994, 2004)
            self.log(f'📅 Đang cuộn Cột 3 (Năm) lùi về khoảng {nam_muc_tieu}...')
            for nhip in range(14):
                self.vuot_toa_do_an_toan(x_year, y_top, x_year, y_bot, 130)
                time.sleep(0.28)
                if nhip >= 4:
                    nam_hien_tai = self._lay_nam_hien_tai_trong_bang_3_cot()
                    if nam_hien_tai and 1985 <= nam_hien_tai <= 2005:
                        self.log(f'✅ Đã cuộn Cột 3 tới năm: {nam_hien_tai}')
                        break

            time.sleep(0.5)
            self.log('📅 Bấm nút CHỌN trên bảng Chọn ngày')
            if not (self.click_text('CHỌN', 'CHỌN', 2, 0.5) or self.click_text('OK', 'OK', 1, 0.4)):
                self.click_toa_do_an_toan(int(w * 0.72), int(h * 0.633))
            time.sleep(1.0)

            if self._kiem_tra_tuoi_hop_le_ngoai_man_hinh():
                self.log('✅ Ngày tháng năm sinh đã hợp lệ (>= 18 tuổi)!')
                break
            self.log('⚠️ Năm sinh chưa lùi đủ 18 tuổi, mở lại bảng Chọn ngày để cuộn thêm...')

        self.log('⏩ Bấm nút Tiếp (sau khi chọn xong Ngày tháng năm sinh)')
        if not (self.click_text('Tiếp', 'Tiếp', 3, 0.8) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6)):
            self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.388))
        nghi_ngau_nhien(self.config.get('delay_click_tiep_lan2', 1.0))

        if self.d(text='OK').exists or self.d(text='Xác nhận').exists:
            self.click_text('OK', 'OK', 1, 0.4) or self.click_text('Xác nhận', 'Xác nhận', 1, 0.4)
            time.sleep(0.8)

    def day_anh_qua_adb(self):
        """
        Lấy ngẫu nhiên 1 ảnh từ thư mục trên máy tính (PC), đẩy sang điện thoại qua ADB
        với timeout=15s chống treo, cập nhật thời gian thực để nằm ở ô đầu tiên trong Thư viện.
        """
        folder_pc = self.avatar_folder if (self.avatar_folder and os.path.isdir(self.avatar_folder)) else DEFAULT_AVATAR_DIR
        if not os.path.isdir(folder_pc):
            try:
                os.makedirs(folder_pc, exist_ok=True)
            except Exception:
                pass
            self.log(f'⚠️ Chưa có thư mục ảnh trên PC: {folder_pc}')
            return None

        images = [f for f in os.listdir(folder_pc) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not images:
            self.log(f'⚠️ Thư mục "{folder_pc}" trên máy tính đang trống! Hãy bỏ ảnh .jpg/.png vào đó.')
            return None

        chosen_img = random.choice(images)
        local_path = os.path.abspath(os.path.join(folder_pc, chosen_img))
        ext = os.path.splitext(chosen_img)[1].lower() or '.jpg'
        remote_filename = f"IMG_{int(time.time() * 1000)}{ext}"
        remote_path_dcim = f"/sdcard/DCIM/Camera/{remote_filename}"
        remote_path_pic = f"/sdcard/Pictures/{remote_filename}"

        try:
            self.log(f'💻 Chọn ảnh từ PC: {chosen_img} -> Đang bắn sang điện thoại...')
            cap_quyen_bo_nho_fb(self.serial)
            self.chay_shell_nhanh('mkdir -p /sdcard/DCIM/Camera /sdcard/Pictures; rm -f /sdcard/DCIM/Camera/IMG_*.* /sdcard/Pictures/IMG_*.*')

            for r_path in [remote_path_dcim, remote_path_pic]:
                cmd_push = f'adb -s {self.serial} push "{local_path}" "{r_path}"' if self.serial else f'adb push "{local_path}" "{r_path}"'
                subprocess.run(cmd_push, shell=True, capture_output=True, creationflags=ADB_CREATION_FLAGS, timeout=15)
                self.chay_shell_nhanh(f'touch "{r_path}"; am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{r_path}"')

            time.sleep(1.5)
            return [remote_path_dcim, remote_path_pic]
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception:
            return None

    def up_avatar_fb(self):
        """Xử lý chuẩn 5 màn hình Thêm ảnh đại diện ngay sau bước OTP"""
        self.bo_qua_luu_thong_tin_dang_nhap()
        remote_paths = self.day_anh_qua_adb()
        if not remote_paths:
            if self.d(text='Bỏ qua').exists or self.d(description='Bỏ qua').exists:
                self.click_text('Bỏ qua', 'Bỏ qua', 1, 0.5)
            return False

        w, h = self.d.window_size()
        try:
            for _ in range(6):
                self.bo_qua_luu_thong_tin_dang_nhap()
                if self.kiem_tra_text(['Thêm ảnh đại diện', 'Thêm ảnh', 'Add profile picture', 'Add picture'], 1, 0.3):
                    break
                time.sleep(0.5)

            self.log('🖼️ [Bước 1/5] Bấm nút "Thêm ảnh"...')
            if not (self.click_text('Thêm ảnh', 'Thêm ảnh', 2, 0.5) or self.click_text_chua('Thêm ảnh', 'Thêm ảnh', 2, 0.5, click_duoi=True)):
                self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.82))
            time.sleep(1.5)

            for _ in range(8):
                if self.d(text='Thư viện').exists or self.d(description='Thư viện').exists or self.d(text='Gallery').exists:
                    break

                if self.d(textContains='Chọn từ thư viện').exists or self.d(descriptionContains='Chọn từ thư viện').exists:
                    self.click_text_chua('Chọn từ thư viện', 'Chọn từ thư viện', 1, 0.4)
                    time.sleep(1.0)
                    continue

                if self.d(text='Cho phép truy cập').exists or self.d(description='Cho phép truy cập').exists or self.d(textContains='truy cập vào thư viện ảnh').exists:
                    self.log('🔓 [Bước 2/5] Bấm nút "Cho phép truy cập"...')
                    if not (self.click_text('Cho phép truy cập', 'Cho phép truy cập', 2, 0.4) or self.click_text_chua('Cho phép truy cập', 'Cho phép truy cập', 1, 0.4)):
                        self.click_toa_do_an_toan(int(w * 0.46), int(h * 0.59))
                    time.sleep(1.2)
                    continue

                if self.d(textContains='sử dụng bộ nhớ điện thoại').exists or self.d(text='Cho phép').exists:
                    self.log('🔓 [Bước 3/5] Bấm "Cho phép" (sử dụng bộ nhớ điện thoại)...')
                    if not self.click_text('Cho phép', 'Cho phép', 2, 0.4):
                        self.click_toa_do_an_toan(int(w * 0.78), int(h * 0.56))
                    time.sleep(1.2)
                    continue

                for nut_he_thong in ['CHO PHÉP', 'Cho phép tất cả', 'Allow all', 'ALLOW', 'Allow', 'Trong khi dùng ứng dụng']:
                    if self.d(text=nut_he_thong).exists or self.d(textContains=nut_he_thong).exists:
                        self.log(f'🔓 [Bước 4/5] Bấm "{nut_he_thong}" (quyền ảnh hệ thống)...')
                        if not (self.click_text(nut_he_thong, nut_he_thong, 1, 0.4) or self.click_text_chua(nut_he_thong, nut_he_thong, 1, 0.4)):
                            self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.53))
                        time.sleep(1.2)
                        break

                time.sleep(0.5)

            for r_path in remote_paths:
                self.chay_shell_nhanh(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d "file://{r_path}"')
            time.sleep(1.5)

            self.log('🖼️ [Bước 5/5] Đã vào "Thư viện" -> Chọn ảnh vừa đẩy từ PC (ô đầu tiên góc trên trái)...')
            self.click_toa_do_an_toan(int(w * 0.16), int(h * 0.18))
            time.sleep(2.0)

            if self.d(text='Thư viện').exists or self.d(description='Thư viện').exists:
                self.log('🖼️ Thử chọn ô ảnh tiếp theo trong Thư viện...')
                self.click_toa_do_an_toan(int(w * 0.16), int(h * 0.32))
                time.sleep(2.0)

            self.log('💾 Bấm Lưu / Xong ảnh đại diện...')
            da_bam_luu = False
            for nut_luu in ['Xong', 'Lưu', 'Done', 'Save', 'Áp dụng', 'Apply', 'Tiếp', 'Next', 'Chia sẻ']:
                if self.d(text=nut_luu).exists or self.d(description=nut_luu).exists or self.d(textContains=nut_luu).exists:
                    self.click_text(nut_luu, nut_luu, 2, 0.5) or self.click_text_chua(nut_luu, nut_luu, 1, 0.5, click_duoi=True)
                    da_bam_luu = True
                    time.sleep(1.5)
                    if self.d(text='Lưu').exists or self.d(description='Lưu').exists:
                        self.click_text('Lưu', 'Lưu', 1, 0.5)
                    break

            if not da_bam_luu:
                self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.90))
                time.sleep(1.0)

            delay_avatar = self.config.get('delay_up_avatar', 8.0)
            self.log(f'⏳ Chờ {delay_avatar}s tải xong Avatar...')
            nghi_ngau_nhien(delay_avatar, 0.15)
            self.log('✅ ĐÃ CẬP NHẬT AVATAR TỪ MÁY TÍNH THÀNH CÔNG!')
            return True
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi up Avatar: {str(e)[:25]}')
            return False
        finally:
            for r_path in remote_paths:
                self.chay_shell_nhanh(f'rm -f "{r_path}"')
# ==================== KẾT THÚC PHẦN 1/2 ====================
# ==================== PHẦN 2/2 (DÁN NỐI TIẾP NGAY DƯỚI PHẦN 1/2) ====================
    def dong_tab_va_mo_lai_fb_giu_nick(self):
        """
        Mở Đa nhiệm vuốt đóng tab Facebook hiện tại rồi mở lại Facebook (KHÔNG xóa data)
        để thoát hoàn toàn khỏi màn hình cài đặt 2FA và quay về trang chủ có nút 3 gạch.
        """
        w, h = self.d.window_size()
        self.log('🔄 Thoát tab Facebook hiện tại rồi mở lại để ra màn hình chính...')

        try:
            self.d.press('recent')
        except Exception:
            self.chay_shell_nhanh('input keyevent KEYCODE_APP_SWITCH')
        time.sleep(1.2)

        # Vuốt đóng tab trên màn hình Đa nhiệm
        if self.d(resourceId='com.miui.home:id/clearAnimView').exists:
            self._click_phan_tu_an_toan(self.d(resourceId='com.miui.home:id/clearAnimView')[0])
        else:
            self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.55), int(w * 0.50), int(h * 0.12), 180)
            time.sleep(0.4)
            self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.50), int(w * 0.95), int(h * 0.50), 180)

        time.sleep(0.8)
        # Đảm bảo tiến trình Facebook đóng hẳn rồi mở lại từ đầu
        self.chay_shell_nhanh('am force-stop com.facebook.katana; input keyevent KEYCODE_HOME')
        time.sleep(1.0)

        self.log('🚀 Đang mở lại Facebook để thực hiện Đăng xuất & Gỡ trang cá nhân...')
        self.chay_shell_nhanh('am start -n com.facebook.katana/com.facebook.katana.LoginActivity')
        nghi_ngau_nhien(self.config.get('delay_mo_lai_fb', 6.5), 0.1)
        self.tat_quyen_khong_cho_phep()
        self.bo_qua_luu_thong_tin_dang_nhap()

    def xoa_tab_da_nhiem_va_lam_moi_fb(self):
        """
        Nhấn nút Đa nhiệm, vuốt đóng tab Facebook,
        xóa sạch dữ liệu ứng dụng và mở lại bản Facebook như mới (Không đổi lại IP).
        """
        w, h = self.d.window_size()
        self.log('🧹 Mở thanh điều hướng Đa nhiệm -> Đóng tab Facebook...')

        try:
            self.d.press('recent')
        except Exception:
            self.chay_shell_nhanh('input keyevent KEYCODE_APP_SWITCH')
        time.sleep(1.5)

        if self.d(packageName='com.facebook.katana').exists and not self.d(packageName='com.miui.home').exists:
            self.click_toa_do_an_toan(int(w * 0.27), int(h * 0.96))
            time.sleep(1.5)

        if self.d(resourceId='com.miui.home:id/clearAnimView').exists:
            self._click_phan_tu_an_toan(self.d(resourceId='com.miui.home:id/clearAnimView')[0])
        elif self.d(descriptionContains='Xóa').exists or self.d(descriptionContains='Clear').exists:
            self.click_text_chua('Xóa', 'Xóa tab', 1, 0.3) or self.click_text_chua('Clear', 'Clear tab', 1, 0.3)
        else:
            self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.50), int(w * 0.95), int(h * 0.50), 180)
            time.sleep(0.5)
            self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.89))

        time.sleep(1.0)
        self.chay_shell_nhanh('input keyevent KEYCODE_HOME')
        time.sleep(0.5)

        self.log('🗑️ Đang làm sạch dữ liệu Facebook để mở lại như máy mới...')
        xoa_du_lieu_fb(self.serial)
        khoa_xoay_man_hinh(self.serial)
        cap_quyen_bo_nho_fb(self.serial)

        self.log('🚀 Mở lại Facebook mới...')
        self.chay_shell_nhanh('am start -n com.facebook.katana/com.facebook.katana.LoginActivity')
        nghi_ngau_nhien(self.config['delay_mo_facebook'], 0.1)
        self.tat_quyen_khong_cho_phep()
        self.dong_goi_y_google()

    def _bam_nut_3_gach_goc_trai(self):
        """
        Tìm và bấm chính xác nút 3 gạch ngang ở góc trên bên trái (hoặc mở thẳng tab Menu).
        Trả về True nếu đã mở được trang Menu (có chữ Cài đặt / Đăng xuất / Trợ giúp).
        """
        w, h = self.d.window_size()

        # 1. Tìm phần tử Menu nằm ở vùng góc trên màn hình (tránh bấm nhầm node ẩn)
        for sel in [
            self.d(descriptionContains='Menu'),
            self.d(descriptionContains='menu'),
            self.d(text='Menu')
        ]:
            if sel.exists:
                for i in range(sel.count):
                    try:
                        b = sel[i].info['bounds']
                        cx = (b['left'] + b['right']) // 2
                        cy = (b['top'] + b['bottom']) // 2
                        if 0 < cy < int(h * 0.22):
                            self.click_toa_do_an_toan(cx, cy)
                            time.sleep(1.5)
                            if self.kiem_tra_text(['Đăng xuất', 'Log out', 'Cài đặt và quyền riêng tư', 'Trợ giúp và hỗ trợ', 'Cài đặt'], 1, 0.3):
                                return True
                    except Exception:
                        pass

        # 2. Bấm dải tọa độ nút 3 gạch ở GÓC TRÊN BÊN TRÁI (tương thích mọi tỷ lệ màn hình)
        ds_toa_do_goc_trai = [
            (int(w * 0.085), int(h * 0.112)),
            (int(w * 0.100), int(h * 0.135)),
            (int(w * 0.085), int(h * 0.082)),
        ]
        for tx, ty in ds_toa_do_goc_trai:
            self.click_toa_do_an_toan(tx, ty)
            time.sleep(1.5)
            if self.kiem_tra_text(['Đăng xuất', 'Log out', 'Cài đặt và quyền riêng tư', 'Trợ giúp và hỗ trợ', 'Cài đặt'], 1, 0.3):
                return True

        # 3. Fallback: Dùng DeepLink mở thẳng vào trang Menu 3 gạch của Facebook
        self.log('⚡ Mở trực tiếp trang Menu 3 gạch bằng DeepLink...')
        self.chay_shell_nhanh('am start -a android.intent.action.VIEW -d "fb://bookmarks"')
        time.sleep(2.2)
        return self.kiem_tra_text(['Đăng xuất', 'Log out', 'Cài đặt và quyền riêng tư', 'Trợ giúp và hỗ trợ'], 1, 0.3)

    def _go_trang_ca_nhan_ngoai_man_hinh_cho(self):
        """
        Xử lý chuẩn giao diện Gỡ trang cá nhân:
        1. Bấm dấu 3 chấm (...) hoặc biểu tượng Bánh răng cài đặt ở góc trên phải
        2. Bấm 'Gỡ trang cá nhân' / nút 'Gỡ' cạnh tên nick
        3. Khi hiện bảng 'Gỡ <Tên>?' ở đáy màn hình -> Bấm chính xác nút 'Gỡ' màu xanh ở dưới cùng
        """
        w, h = self.d.window_size()
        self.log('🗑️ [Bước 3] Mở tùy chọn Gỡ trang cá nhân...')

        if not self.kiem_tra_text(['Gỡ trang cá nhân khỏi thiết bị này', 'Gỡ trang cá nhân', 'Remove profile'], 1, 0.3):
            da_mo_menu_go = False
            for mo_ta in ['Tùy chọn khác', 'More options', 'Cài đặt', 'Settings', 'Quản lý trang cá nhân']:
                if self.d(descriptionContains=mo_ta).exists or self.d(textContains=mo_ta).exists:
                    if self.click_text_chua(mo_ta, mo_ta, 1, 0.4):
                        da_mo_menu_go = True
                        time.sleep(1.2)
                        break

            if not da_mo_menu_go:
                self.click_toa_do_an_toan(int(w * 0.91), int(h * 0.085))
                time.sleep(1.0)
                if not self.kiem_tra_text(['Gỡ trang cá nhân', 'Remove profile', 'Quản lý'], 1, 0.3):
                    self.click_toa_do_an_toan(int(w * 0.92), int(h * 0.14))
                    time.sleep(1.0)

        if self.d(textContains='Gỡ trang cá nhân').exists or self.d(descriptionContains='Gỡ trang cá nhân').exists:
            if not self.d(textContains='Gỡ trang cá nhân khỏi thiết bị này').exists:
                self.click_text_chua('Gỡ trang cá nhân', 'Gỡ trang cá nhân', 1, 0.5)
                time.sleep(1.5)

        if self.kiem_tra_text(['Gỡ trang cá nhân khỏi thiết bị này'], 1, 0.3) and not self.kiem_tra_text(['Hủy', 'lần đăng nhập tiếp theo'], 1, 0.2):
            self.log('👤 Bấm nút "Gỡ" bên cạnh tên tài khoản...')
            if not self.click_text('Gỡ', 'Nút Gỡ cạnh tên', 1, 0.4):
                self.click_toa_do_an_toan(int(w * 0.815), int(h * 0.242))
            time.sleep(1.5)

        for _ in range(3):
            if self.kiem_tra_text(['lần đăng nhập tiếp theo', 'Hủy', 'Gỡ'], 1, 0.3):
                self.log('✅ Bấm nút "Gỡ" màu xanh dương dưới đáy màn hình...')
                da_bam_go_xanh = False

                for sel in [self.d(text='Gỡ'), self.d(description='Gỡ'), self.d(text='GỠ')]:
                    if sel.exists:
                        for i in range(sel.count - 1, -1, -1):
                            try:
                                b = sel[i].info['bounds']
                                cy = (b['top'] + b['bottom']) // 2
                                if cy > int(h * 0.70):
                                    self._click_phan_tu_an_toan(sel[i])
                                    da_bam_go_xanh = True
                                    break
                            except Exception:
                                pass
                    if da_bam_go_xanh:
                        break

                if not da_bam_go_xanh:
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.825))

                time.sleep(3.0)
                if not self.kiem_tra_text(['lần đăng nhập tiếp theo', 'Gỡ trang cá nhân khỏi thiết bị này'], 1, 0.4):
                    self.log('🎉 Đã gỡ trang cá nhân khỏi thiết bị thành công!')
                    return True
            time.sleep(0.8)

        return False

    def dang_xuat_va_go_trang_ca_nhan(self, thoat_tab_truoc=False):
        """
        Thực hiện chuẩn luồng Đăng xuất & Gỡ tài khoản:
        - Nếu thoat_tab_truoc=True (sau khi bật 2FA): Đóng tab đa nhiệm -> Mở lại FB từ đầu.
        - Bước 1: Bấm 3 gạch ngang ở GÓC TRÊN BÊN TRÁI -> Lướt xuống đáy -> Bấm Đăng xuất.
        - Bước 2: Bấm 'LÚC KHÁC' (Không lưu mật khẩu) -> Bấm 'ĐĂNG XUẤT'.
        - Bước 3: Ra màn hình chờ bên ngoài -> Gỡ trang cá nhân -> Bấm nút 'Gỡ' màu xanh dưới đáy.
        """
        w, h = self.d.window_size()

        if thoat_tab_truoc:
            self.dong_tab_va_mo_lai_fb_giu_nick()

        self.bo_qua_luu_thong_tin_dang_nhap()
        for nut_phu in ['Xong', 'Done', 'LÚC KHÁC', 'Lúc khác', 'Not now', 'Bỏ qua', 'Skip', 'Đóng', 'Close']:
            if self.d(text=nut_phu).exists or self.d(description=nut_phu).exists:
                self.click_text(nut_phu, nut_phu, 1, 0.4)
                time.sleep(0.6)

        if self.kiem_tra_text(['Gỡ trang cá nhân khỏi thiết bị này', 'lần đăng nhập tiếp theo'], 1, 0.3):
            self._go_trang_ca_nhan_ngoai_man_hinh_cho()
            return

        # Không dùng từ khóa 'Bắt đầu' ở đây để tránh nhận nhầm thẻ gợi ý trên trang chủ
        dang_o_ngoai = (
            self.d(text='Tạo tài khoản mới').exists
            or self.d(description='Tạo tài khoản mới').exists
            or self.d(text='Create new account').exists
            or self.kiem_tra_text([
                'Dùng trang cá nhân khác',
                'Dùng tài khoản khác',
                'Use another account',
                'Đăng nhập bằng tài khoản khác'
            ], 1, 0.3)
        )

        if not dang_o_ngoai:
            self.log('🚪 [Bước 1] Bấm nút 3 gạch ngang (góc trên trái) -> Lướt xuống bấm Đăng xuất...')
            self._bam_nut_3_gach_goc_trai()

            for _ in range(6):
                if self.kiem_tra_text(['Đăng xuất', 'Log out'], 1, 0.2):
                    break
                self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.85), int(w * 0.50), int(h * 0.15), 200)
                time.sleep(0.6)

            if not self.kiem_tra_text(['Đăng xuất', 'Log out'], 1, 0.2):
                self.chay_shell_nhanh('am start -a android.intent.action.VIEW -d "fb://bookmarks"')
                time.sleep(2.0)
                for _ in range(5):
                    if self.kiem_tra_text(['Đăng xuất', 'Log out'], 1, 0.2):
                        break
                    self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.85), int(w * 0.50), int(h * 0.15), 200)
                    time.sleep(0.6)

            if (
                self.click_text('Đăng xuất', 'Đăng xuất', 2, 0.5)
                or self.click_text_chua('Đăng xuất', 'Đăng xuất', 2, 0.5, click_duoi=True)
                or self.click_text_chua('Log out', 'Log out', 1, 0.5, click_duoi=True)
            ):
                time.sleep(1.2)

                if self.kiem_tra_text(['Lưu thông tin đăng nhập', 'khôi phục từ bản sao lưu', 'LÚC KHÁC', 'Lúc khác', 'Không lưu'], 2, 0.4):
                    self.log('🚫 [Bước 2A] Bấm "LÚC KHÁC" (Không lưu thông tin đăng nhập)...')
                    if not (
                        self.click_text('LÚC KHÁC', 'LÚC KHÁC', 2, 0.4)
                        or self.click_text('Lúc khác', 'Lúc khác', 2, 0.4)
                        or self.click_text_chua('LÚC KHÁC', 'LÚC KHÁC', 1, 0.4)
                        or self.click_text_chua('Lúc khác', 'Lúc khác', 1, 0.4, click_duoi=True)
                        or self.click_text('Không lưu', 'Không lưu', 1, 0.3)
                    ):
                        self.click_toa_do_an_toan(int(w * 0.59), int(h * 0.578))
                    time.sleep(1.2)

                if self.kiem_tra_text(['Đăng xuất khỏi tài khoản', 'ĐĂNG XUẤT', 'Đăng xuất', 'LOG OUT'], 2, 0.4):
                    self.log('🚪 [Bước 2B] Xác nhận bấm "ĐĂNG XUẤT"...')
                    if not (
                        self.click_text('ĐĂNG XUẤT', 'ĐĂNG XUẤT', 2, 0.4)
                        or self.click_text_chua('ĐĂNG XUẤT', 'ĐĂNG XUẤT', 1, 0.4, click_duoi=True)
                        or self.click_text_chua('Đăng xuất', 'Đăng xuất', 1, 0.4, click_duoi=True)
                        or self.click_text('LOG OUT', 'LOG OUT', 1, 0.4)
                    ):
                        self.click_toa_do_an_toan(int(w * 0.755), int(h * 0.528))
                    time.sleep(3.5)

        self._go_trang_ca_nhan_ngoai_man_hinh_cho()

    def dam_bao_man_hinh_tao_tai_khoan_moi(self):
        """
        Kiểm tra ngay khi vào Facebook:
        - Nếu ở màn hình sạch hoàn toàn (chỉ có Bắt đầu / Tạo tài khoản mới) -> Đi tiếp luôn.
        - Nếu còn nick cũ -> Thực hiện Đăng xuất + Gỡ trang cá nhân hoàn tất rồi mới làm mới App.
        """
        for _ in range(5):
            if self.kiem_tra_text([
                'Lưu thông tin đăng nhập',
                'Dùng trang cá nhân khác',
                'Dùng tài khoản khác',
                'Bạn đang nghĩ gì',
                'Gỡ trang cá nhân khỏi thiết bị này'
            ], 1, 0.3):
                break

            if self.kiem_tra_text(['Bắt đầu', 'Tạo tài khoản mới', 'Create new account', 'Tham gia Facebook', 'Bạn tên gì'], 1, 0.3):
                return True
            time.sleep(0.5)

        self.log('⚠️ Phát hiện còn nick cũ trên máy -> Tiến hành Đăng xuất & Gỡ trang cá nhân...')
        self.dang_xuat_va_go_trang_ca_nhan(thoat_tab_truoc=False)

        if not self.kiem_tra_text(['Bắt đầu', 'Tạo tài khoản mới', 'Create new account'], 2, 0.5):
            self.xoa_tab_da_nhiem_va_lam_moi_fb()
        return True

    def lay_otp_theo_che_do(self, mode, used_email, mail_service=None, imap_service=None, hotmail_service=None, uid_moc=0, force_8_digits=False):
        max_resend_attempts = 2
        loai_otp_str = "8 số bảo mật" if force_8_digits else "xác nhận đăng ký"
        for attempt in range(max_resend_attempts + 1):
            if STOP_EVENT.is_set():
                return None

            otp_code = None
            if mode == "2" and not (mail_service and mail_service.token):
                with OTP_LOCK:
                    PAUSE_FOR_INPUT.clear()
                    try:
                        built_in_print(f"\n{Colors.color_text(f'[{self.device_name}] Lần {attempt+1}: NHẬP MÃ OTP ({loai_otp_str}) CHO [{used_email}]: ', Colors.SUCCESS)}", end="")
                        otp_code = input().strip()
                    finally:
                        PAUSE_FOR_INPUT.set()
            elif mode == "1" or (mode == "2" and mail_service and mail_service.token):
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Mail.tm (Lần {attempt+1})...')
                otp_code = mail_service.get_otp_code(timeout=95, force_8_digits=force_8_digits)
            elif mode in ["3", "4"] and imap_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Gmail IMAP (Lần {attempt+1})...')
                otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=95, force_8_digits=force_8_digits)
            elif mode == "5" and hotmail_service:
                self.log(f'🔢 Đang chờ OTP ({loai_otp_str}) Smail1s (Lần {attempt+1})...')
                otp_code = hotmail_service.get_otp_code(timeout=110, force_8_digits=force_8_digits)

            if otp_code:
                self.log(f'🔢 ĐÃ LẤY ĐƯỢC OTP ({loai_otp_str}): {otp_code}')
                return otp_code

            if attempt < max_resend_attempts:
                self.log(f'⚠️ Chưa nhận được mã (Lần {attempt+1}), thử bấm gửi lại mã...')
                self.click_text_chua('Tôi không nhận được mã', 'Không nhận được mã', 2, 0.5) or self.click_text_chua('Gửi lại mã', 'Gửi lại mã', 2, 0.5)
                time.sleep(1.0)
                self.click_text_chua('Gửi lại', 'Gửi lại', 2, 0.5) or self.click_text_chua('Nhận mã mới', 'Nhận mã mới', 2, 0.5)
                time.sleep(3.0)

        self.log(f'❌ Không lấy được OTP ({loai_otp_str})!')
        return None

    def trich_xuat_key_2fa_tu_man_hinh(self):
        """
        Trích xuất dòng code 2FA (VD: VAEI HQNR I2PH Z4HZ XV3D IN3M BKL4 6IAS) ở Hình 3:
        1. Quét toàn bộ text / content-desc trong XML để bắt đúng dòng 8 cụm 4 ký tự dưới mã QR
        2. Nếu cần có thể chạm giữ / sao chép vào Clipboard
        """
        try:
            xml_dump = self.d.dump_hierarchy()
            cac_chuoi = re.findall(r'(?:text|content-desc)="([^"]+)"', xml_dump)
            for s in cac_chuoi:
                s_clean = s.strip()
                # Bắt chuẩn định dạng 8 cụm 4 ký tự (VD: VAEI HQNR I2PH Z4HZ XV3D IN3M BKL4 6IAS)
                m_group = re.search(r'\b(?:[A-Z2-7]{4}[\s-]+){3,7}[A-Z2-7]{4}\b', s_clean.upper())
                if m_group:
                    key_cand = lam_sach_key_2fa(m_group.group(0))
                    if 16 <= len(key_cand) <= 64:
                        return key_cand

                if re.fullmatch(r'[A-Z2-7\s-]{16,45}', s_clean):
                    key_cand = lam_sach_key_2fa(s_clean)
                    if len(key_cand) in [16, 24, 32] and any(c.isalpha() for c in key_cand):
                        return key_cand
        except Exception:
            pass

        try:
            for nut_copy in ['Sao chép khóa', 'Copy key', 'Sao chép mã', 'Sao chép', 'Copy']:
                if self.d(textContains=nut_copy).exists or self.d(descriptionContains=nut_copy).exists:
                    self.click_text_chua(nut_copy, nut_copy, 1, 0.4)
                    time.sleep(0.8)
                    clip_text = ""
                    try:
                        clip_text = self.d.clipboard or ""
                    except Exception:
                        pass
                    if not clip_text:
                        clip_text = chay_lenh_adb_lay_ket_qua('shell cmd clipboard get-text', self.serial)
                    clean_clip = lam_sach_key_2fa(clip_text)
                    if 16 <= len(clean_clip) <= 64:
                        return clean_clip
        except Exception:
            pass

        return None

    def dieu_huong_vao_man_hinh_2fa(self):
        """Mở thẳng trang thiết lập 2FA bằng DeepLink hoặc qua Menu Cài đặt"""
        w, h = self.d.window_size()
        self.chay_shell_nhanh(
            'am start -a android.intent.action.VIEW -d "fb://faceweb/f?href=%2Fsecurity%2F2fac%2Fsetup%2Fintro"'
        )
        time.sleep(4.5)

        if not self.kiem_tra_text([
            'Xác thực 2 yếu tố', 'Chọn phương thức bảo mật', 'Dùng ứng dụng xác thực',
            'Ứng dụng xác thực', 'Two-factor', 'Authentication app', 'Bắt đầu'
        ], 2, 0.8):
            self.log('🛡️ Mở 2FA qua Menu Cài đặt...')
            self._bam_nut_3_gach_goc_trai()
            time.sleep(1.5)

            for _ in range(3):
                self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.82), int(w * 0.50), int(h * 0.20), 200)
                time.sleep(0.5)

            self.click_text_chua('Cài đặt & quyền riêng tư', 'Cài đặt & quyền riêng tư', 2, 0.5) or self.click_text_chua('Settings & privacy', 'Settings', 2, 0.5)
            time.sleep(1.0)
            self.click_text('Cài đặt', 'Cài đặt', 2, 0.5) or self.click_text('Settings', 'Settings', 2, 0.5)
            time.sleep(2.0)
            self.click_text_chua('Trung tâm tài khoản', 'Trung tâm TK', 2, 0.5) or self.click_text_chua('Mật khẩu và bảo mật', 'Mật khẩu & bảo mật', 2, 0.5)
            time.sleep(2.0)
            self.click_text_chua('Mật khẩu và bảo mật', 'Mật khẩu & bảo mật', 2, 0.5) or self.click_text_chua('Password and security', 'Password', 2, 0.5)
            time.sleep(2.0)
            self.click_text_chua('Xác thực 2 yếu tố', 'Xác thực 2 yếu tố', 2, 0.5) or self.click_text_chua('Two-factor authentication', '2FA', 2, 0.5)
            time.sleep(2.5)

        if self.kiem_tra_text(['Chọn tài khoản', 'Select an account', 'Chọn trang cá nhân', 'Trang cá nhân'], 2, 0.6):
            if not self.click_text_chua('Facebook', 'Tài khoản FB', 1, 0.4):
                self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.32))
            time.sleep(2.5)

    def _nhap_mat_khau_xac_nhan_2fa_hinh_2(self):
        """
        Xử lý chuẩn HÌNH 2: Màn hình 'Nhập mật khẩu' ('Vì lý do bảo mật, vui lòng nhập lại mật khẩu của bạn để tiếp tục.')
        - Bấm vào ô 'Mật khẩu'
        - Nhập mật khẩu đã tạo tài khoản ở trên
        - Bấm nút màu xanh 'Tiếp tục'
        """
        w, h = self.d.window_size()
        if self.kiem_tra_text([
            'Nhập mật khẩu',
            'Vì lý do bảo mật',
            'nhập lại mật khẩu của bạn',
            'Quên mật khẩu',
            'Re-enter your password'
        ], 2, 0.5):
            self.log('🔑 [Hình 2] Phát hiện màn hình Nhập mật khẩu -> Đang nhập mật khẩu tài khoản...')
            da_focus_mk = False
            if self.d(className='android.widget.EditText').exists:
                 da_focus_mk = self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
            elif self.click_truong('Mật khẩu', False, 2, 0.4):
                da_focus_mk = True

            if not da_focus_mk:
                # Tọa độ chuẩn ô Mật khẩu theo Hình 2
                self.click_toa_do_an_toan(int(w * 0.45), int(h * 0.193))

            time.sleep(0.4)
            self.nhap_text(self.config['mat_khau_fb'])
            time.sleep(0.8)

            self.log('⏩ [Hình 2] Bấm nút màu xanh "Tiếp tục" sau khi nhập mật khẩu...')
            if not (
                self.click_text('Tiếp tục', 'Tiếp tục', 2, 0.5)
                or self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5)
                or self.click_text('Continue', 'Continue', 1, 0.4)
            ):
                # Tọa độ chuẩn nút xanh Tiếp tục theo Hình 2
                self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.253))

            time.sleep(3.5)
            return True
        return False

    def _nhap_otp_hoac_mk_phu_2fa(self, used_email, mode, mail_service, imap_service, hotmail_service, autosms_service):
        """Xử lý trường hợp Facebook hỏi lại Mật khẩu (Hình 2) hoặc Mã bảo mật Email/SMS trong quá trình bật 2FA"""
        self._nhap_mat_khau_xac_nhan_2fa_hinh_2()

        if self.kiem_tra_text(['Kiểm tra email', 'Check your email', 'Kiểm tra tin nhắn', 'Nhập mã gồm', 'chúng tôi đã gửi mã'], 1, 0.4):
            self.log('📧 Phát hiện bước xác minh Email/SMS phụ khi bật 2FA -> Đang lấy mã...')
            uid_moc_2fa = imap_service.get_latest_uid() if (mode in ["3", "4"] and imap_service) else 0
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
                    force_8_digits=False
                )
            if verify_code:
                self.log(f'🔢 Nhập mã xác minh bảo mật: {verify_code}')
                if self.d(className='android.widget.EditText').exists:
                    self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
                    time.sleep(0.3)
                else:
                    w, h = self.d.window_size()
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.35))
                    time.sleep(0.3)
                self.nhap_text(verify_code)
                time.sleep(0.8)
                self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5, click_duoi=True) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.5, click_duoi=True)
                time.sleep(4.0)

    def bat_2fa_fb(self, used_email, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None):
        """
        Luồng bật 2FA chuẩn theo đúng 4 hình ảnh:
        - Hình 1: Màn hình 'Chọn phương thức bảo mật' -> Bấm nút màu xanh 'Dùng ứng dụng xác thực'
        - Hình 2: Màn hình 'Nhập mật khẩu' -> Nhập mật khẩu tạo tài khoản -> Bấm nút xanh 'Tiếp tục'
        - Hình 3: Màn hình 'Thiết lập ứng dụng trên một thiết bị khác' -> Sao chép dòng code 2FA dưới QR -> Bấm 'Tiếp tục'
        - Hình 4: Màn hình 'Nhập mã xác nhận' -> Nhập OTP 6 số vào ô 'Mã xác nhận' -> Bấm 'Tiếp tục' -> Bấm 'Xong'
        """
        self.log('🛡️ Đang mở cài đặt Xác thực 2 yếu tố (2FA)...')
        two_fa_secret = ""
        w, h = self.d.window_size()

        try:
            self.bo_qua_luu_thong_tin_dang_nhap()
            for nut_bo_qua in ['Bỏ qua', 'Skip', 'LÚC KHÁC', 'Lúc khác', 'Not Now', 'OK']:
                if self.d(text=nut_bo_qua).exists or self.d(description=nut_bo_qua).exists:
                    self.click_text(nut_bo_qua, nut_bo_qua, 1, 0.3)
                    time.sleep(0.4)

            self.dieu_huong_vao_man_hinh_2fa()

            # Nếu hỏi mật khẩu ngay khi vừa vào
            self._nhap_mat_khau_xac_nhan_2fa_hinh_2()

            # ==================== BƯỚC 1 (HÌNH 1): BẤM NÚT MÀU XANH "DÙNG ỨNG DỤNG XÁC THỰC" ====================
            self.log('🛡️ [Hình 1] Bấm nút màu xanh "Dùng ứng dụng xác thực"...')
            da_bam_nut_xanh_hinh_1 = False
            for nut_hinh_1 in [
                'Dùng ứng dụng xác thực',
                'Sử dụng ứng dụng xác thực',
                'Use authentication app',
                'Ứng dụng xác thực'
            ]:
                if self.d(text=nut_hinh_1).exists or self.d(description=nut_hinh_1).exists or self.d(textContains=nut_hinh_1).exists:
                    if self.click_text(nut_hinh_1, nut_hinh_1, 2, 0.4) or self.click_text_chua(nut_hinh_1, nut_hinh_1, 2, 0.4):
                        da_bam_nut_xanh_hinh_1 = True
                        break

            if not da_bam_nut_xanh_hinh_1:
                # Tọa độ chuẩn nút màu xanh "Dùng ứng dụng xác thực" trên Hình 1
                self.click_toa_do_an_toan(int(w * 0.464), int(h * 0.436))

            time.sleep(2.5)

            # Nếu giao diện nào vẫn còn nút Tiếp tục ở dưới thì bấm thêm
            if self.kiem_tra_text(['Chọn phương thức bảo mật'], 1, 0.2):
                self.click_toa_do_an_toan(int(w * 0.464), int(h * 0.436))
                time.sleep(2.0)

            # ==================== BƯỚC 2 (HÌNH 2): NHẬP MẬT KHẨU TÀI KHOẢN & BẤM TIẾP TỤC ====================
            self._nhap_otp_hoac_mk_phu_2fa(used_email, mode, mail_service, imap_service, hotmail_service, autosms_service)

            # ==================== BƯỚC 3 (HÌNH 3): LẤY DÒNG CODE 2FA DƯỚI MÃ QR & BẤM TIẾP TỤC ====================
            self.log('📜 [Hình 3] Đang lấy dòng code 2FA dưới mã QR...')
            for lan_quet in range(6):
                two_fa_secret = self.trich_xuat_key_2fa_tu_man_hinh()
                if two_fa_secret:
                    break
                # Nếu chưa tới Hình 3 vì vẫn đang ở Hình 2 (mật khẩu) thì xử lý lại Hình 2
                if self.kiem_tra_text(['Nhập mật khẩu', 'Vì lý do bảo mật'], 1, 0.2):
                    self._nhap_mat_khau_xac_nhan_2fa_hinh_2()
                    continue
                if lan_quet >= 2:
                    self.vuot_toa_do_an_toan(int(w * 0.50), int(h * 0.78), int(w * 0.50), int(h * 0.35), 250)
                time.sleep(1.2)

            if not two_fa_secret:
                self.log('⚠️ Không tìm thấy dòng code 2FA trên màn hình Hình 3!')
                return ""

            self.log(f'🔑 [Hình 3] Đã sao chép Key 2FA: {two_fa_secret}')

            self.log('⏩ [Hình 3] Bấm nút màu xanh "Tiếp tục" để sang màn hình Nhập mã xác nhận...')
            if not (
                self.click_text('Tiếp tục', 'Tiếp tục', 2, 0.5)
                or self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5, click_duoi=True)
                or self.click_text('Tiếp', 'Tiếp', 1, 0.4)
                or self.click_text_chua('Continue', 'Continue', 1, 0.4, click_duoi=True)
            ):
                # Tọa độ chuẩn nút xanh "Tiếp tục" ở đáy Hình 3
                self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.869))
            time.sleep(2.5)

            # ==================== BƯỚC 4 (HÌNH 4): NHẬP MÃ OTP 6 SỐ VÀO Ô "MÃ XÁC NHẬN" & BẤM TIẾP TỤC ====================
            ma_otp_6_so = chuyen_doi_2fa_sang_otp(two_fa_secret, doi_chu_ky_moi=True)
            self.log(f'🔢 [Hình 4] Mã OTP 6 số từ 2FA: {ma_otp_6_so} -> Bấm vào ô "Mã xác nhận"...')

            if ma_otp_6_so:
                da_bam_o_ma = False
                if self.d(className='android.widget.EditText').exists:
                    da_bam_o_ma = self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
                elif (
                    self.click_truong('Mã xác nhận', False, 2, 0.4)
                    or self.click_text_chua('Mã xác nhận', 'Mã xác nhận', 1, 0.4)
                ):
                    da_bam_o_ma = True

                if not da_bam_o_ma:
                    # Tọa độ chuẩn ô "Mã xác nhận" trên Hình 4
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.369))

                time.sleep(0.5)
                self.nhap_text(ma_otp_6_so)
                time.sleep(1.0)

                # Ẩn bàn phím nếu bàn phím che nút Tiếp tục
                if self.d(text='Tiếp tục').exists or self.d(description='Tiếp tục').exists:
                    pass
                else:
                    self.d.press('back')
                    time.sleep(0.6)

                self.log('⏩ [Hình 4] Bấm nút "Tiếp tục" để hoàn tất bật 2FA...')
                if not (
                    self.click_text('Tiếp tục', 'Tiếp tục', 2, 0.5)
                    or self.click_text_chua('Tiếp tục', 'Tiếp tục', 2, 0.5, click_duoi=True)
                    or self.click_text('Tiếp', 'Tiếp', 1, 0.4)
                    or self.click_text('Xác nhận', 'Xác nhận', 1, 0.4)
                ):
                    # Tọa độ chuẩn nút "Tiếp tục" trên Hình 4
                    self.click_toa_do_an_toan(int(w * 0.50), int(h * 0.450))
                time.sleep(3.5)

                self._nhap_otp_hoac_mk_phu_2fa(used_email, mode, mail_service, imap_service, hotmail_service, autosms_service)

                # Bấm nút Xong / Hoàn tất ở màn hình thông báo 2FA đã bật
                for _ in range(3):
                    for nut_xong in ['Xong', 'Done', 'Hoàn tất', 'OK', 'Tiếp tục']:
                        if self.d(text=nut_xong).exists or self.d(description=nut_xong).exists or self.d(textContains=nut_xong).exists:
                            self.click_text(nut_xong, nut_xong, 1, 0.4) or self.click_text_chua(nut_xong, nut_xong, 1, 0.4, click_duoi=True)
                            time.sleep(1.5)
                            break

                self.log(f'✅ ĐÃ BẬT 2FA HOÀN TẤT! Key: {two_fa_secret[:12]}... (OTP: {ma_otp_6_so})')
                return two_fa_secret

            return ""
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            self.log(f'⚠️ Lỗi khi bật 2FA: {str(e)[:30]}')
            return ""

    def xu_ly_mat_khau_va_otp(self, tai_khoan_lien_he, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, uid_moc=0):
        """
        Xử lý chuỗi màn hình sau khi nhập Email / SĐT:
        - Mật khẩu -> Tiếp
        - Lưu thông tin đăng nhập? -> BẮT BUỘC BẤM 'LÚC KHÁC' (Không lưu đám mây)
        - Tôi đồng ý -> Nhập OTP -> Bấm 'LÚC KHÁC' nếu hỏi lại Lưu thông tin -> Up Avatar -> Bật 2FA
        - Sau khi xong 2FA -> Thoát tab Facebook hiện tại, vào lại FB và thực hiện Đăng xuất & Gỡ trang cá nhân
        """
        mat_khau_fb = self.config['mat_khau_fb']
        da_nhap_otp = False

        for _ in range(14):
            self.tat_quyen_khong_cho_phep()

            if self.bo_qua_luu_thong_tin_dang_nhap():
                continue

            if self.kiem_tra_text(['Tạo mật khẩu', 'Mật khẩu'], 1, 0.2) and not self.kiem_tra_text(['Mã xác nhận', 'Nhập mã'], 1, 0.1):
                self.log('🔑 Nhập Mật khẩu...')
                if self.click_truong('Mật khẩu', False, 2, 0.5) or self.d(className='android.widget.EditText').exists:
                    if self.d(className='android.widget.EditText').exists:
                        self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
                    self.nhap_text(mat_khau_fb)
                    nghi_ngau_nhien(self.config['delay_nhap_mat_khau'])
                    self.log('⏩ Bấm Tiếp (sau Mật khẩu)')
                    self.click_text('Tiếp', 'Tiếp', 3, 0.6) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.5)
                    nghi_ngau_nhien(self.config['delay_click_tiep_sau_mk'])
                    continue

            if self.kiem_tra_text(['Tôi đồng ý', 'điều khoản và chính sách'], 1, 0.2):
                self.log('✅ Bấm Tôi đồng ý')
                if self.d(textContains='Tôi đồng ý').exists:
                    self._click_phan_tu_an_toan(self.d(textContains='Tôi đồng ý')[-1])
                elif self.d(descriptionContains='Tôi đồng ý').exists:
                    self._click_phan_tu_an_toan(self.d(descriptionContains='Tôi đồng ý')[-1])
                nghi_ngau_nhien(self.config['delay_cho_toi_dong_y'], 0.15)
                continue

            if self.kiem_tra_text(['Gửi mã qua SMS', 'Nhận mã qua SMS'], 1, 0.2):
                self.click_text_chua('Gửi mã qua SMS', 'Gửi mã qua SMS', 2, 0.5)
                time.sleep(2.0)
                continue

            if self.kiem_tra_text(['Mã xác nhận', 'Nhập mã xác nhận', 'Nhập mã gồm', 'Xác nhận tài khoản'], 1, 0.3):
                self.log('📩 Đã vào trang Nhập mã OTP!')
                if mode == "6" and autosms_service:
                    code = autosms_service.get_otp_code(timeout=95)
                else:
                    code = self.lay_otp_theo_che_do(
                        mode=mode,
                        used_email=tai_khoan_lien_he,
                        mail_service=mail_service,
                        imap_service=imap_service,
                        hotmail_service=hotmail_service,
                        uid_moc=uid_moc,
                        force_8_digits=False
                    )

                if not code:
                    if mode == "6" and autosms_service:
                        autosms_service.cancel_order()
                    return None

                self.log(f'🔢 Nhập mã OTP: {code}')
                if self.d(className='android.widget.EditText').exists:
                    self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
                    time.sleep(0.3)
                    self.nhap_text(code)
                elif self.click_truong('Mã xác nhận', False, 2, 0.5):
                    self.nhap_text(code)
                else:
                    self.nhap_text(code)

                nghi_ngau_nhien(self.config['delay_nhap_code'])
                self.log('⏩ Bấm Tiếp / Gửi mã OTP')
                self.click_text('Tiếp', 'Tiếp', 2, 0.6) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6) or self.click_text_chua('Gửi', 'Gửi', 2, 0.5) or self.click_text_chua('Xác nhận', 'Xác nhận', 2, 0.5)
                nghi_ngau_nhien(self.config['delay_click_tiep_cuoi'])
                da_nhap_otp = True
                break

            time.sleep(1.5)

        if not da_nhap_otp:
            self.log('❌ Không tìm thấy màn hình nhập OTP!')
            return None

        for _ in range(3):
            if self.bo_qua_luu_thong_tin_dang_nhap():
                break
            time.sleep(0.6)

        self.log(f'🎉 XÁC MINH OTP THÀNH CÔNG ({tai_khoan_lien_he}) -> Tiến hành Thêm ảnh đại diện & Bật 2FA...')
        self.up_avatar_fb()
        self.bo_qua_luu_thong_tin_dang_nhap()

        two_fa_key = self.bat_2fa_fb(
            used_email=tai_khoan_lien_he,
            mode=mode,
            mail_service=mail_service,
            imap_service=imap_service,
            hotmail_service=hotmail_service,
            autosms_service=autosms_service
        )

        self.log('🧹 Đang thoát tab FB, vào lại FB để Đăng xuất & Gỡ trang cá nhân khỏi thiết bị...')
        self.dang_xuat_va_go_trang_ca_nhan(thoat_tab_truoc=True)

        return (tai_khoan_lien_he, mat_khau_fb, two_fa_key)

    def chay_dang_ky(self, used_email=None, mode="1", mail_service=None, imap_service=None, hotmail_service=None, autosms_service=None, used_phones=None, used_names=None):
        """
        Quy trình Đăng ký chuẩn sạch như máy mới:
        Xóa sạch dữ liệu FB & Autofill -> Đổi Android ID -> Đổi IP 4G -> Mở FB
        -> Đảm bảo ở trang Tạo TK mới (Nếu kẹt nick cũ thì Đăng xuất + Gỡ hoàn toàn)
        -> KHÔNG CHO PHÉP -> Họ & Tên -> Ngày sinh (3 cột) -> Giới tính -> Email / SĐT
        -> Mật khẩu & OTP -> Thêm ảnh đại diện từ PC -> Bật 2FA -> Thoát tab vào lại FB -> Đăng xuất & Gỡ trang cá nhân
        """
        self.log('🧹 Làm sạch dữ liệu FB, tắt Autofill & đổi thông số phần cứng...')
        xoa_du_lieu_fb(self.serial)
        lam_moi_thong_so_thiet_bi_adb(self.serial, self.config)
        doi_ip_che_do_may_bay_adb(self.serial, self.device_name, self.config)

        khoa_xoay_man_hinh(self.serial)
        cap_quyen_bo_nho_fb(self.serial)

        self.log('🚀 Mở Facebook...')
        self.chay_shell_nhanh('am start -n com.facebook.katana/com.facebook.katana.LoginActivity')
        nghi_ngau_nhien(self.config['delay_mo_facebook'], 0.1)

        self.tat_quyen_khong_cho_phep()
        self.dong_goi_y_google()
        self.dam_bao_man_hinh_tao_tai_khoan_moi()

        self.log('🔵 Bấm nút Bắt đầu / Tạo tài khoản mới...')
        da_bam_bat_dau = (
            self.click_text('Bắt đầu', 'Bắt đầu', 3, 0.8)
            or self.click_text_chua('Bắt đầu', 'Bắt đầu', 2, 0.6)
            or self.click_text_chua('Tạo tài khoản mới', 'Tạo tài khoản mới', 2, 0.6)
        )
        if not da_bam_bat_dau:
            self.dong_goi_y_google()
            self.click_text_chua('Bắt đầu', 'Bắt đầu', 3, 0.8) or self.click_text_chua('Tạo tài khoản mới', 'Tạo TK mới', 2, 0.6)

        nghi_ngau_nhien(self.config['delay_click_tao_tk_lan1'])

        if self.d(text='Bắt đầu').exists or self.d(description='Bắt đầu').exists:
            self.click_text('Bắt đầu', 'Bắt đầu', 2, 0.5)
            time.sleep(1.0)

        self.log('❌ Kiểm tra & bấm KHÔNG CHO PHÉP quyền danh bạ...')
        for _ in range(3):
            if self.tat_quyen_khong_cho_phep():
                break
            time.sleep(0.4)
        nghi_ngau_nhien(self.config['delay_chon_khong_cho_phep_lan2'])

        self.dong_goi_y_google()
        ho, ten = self.tao_ho_ten(used_names)
        self.log(f'📝 Nhập Họ: {ho} | Tên: {ten}')

        edit_texts = self.d(className='android.widget.EditText')
        if edit_texts.count >= 2:
            self._click_phan_tu_an_toan(edit_texts[0])
            time.sleep(0.25)
            self.nhap_text(ho)
            nghi_ngau_nhien(self.config['delay_nhap_ho'])

            self._click_phan_tu_an_toan(edit_texts[1])
            time.sleep(0.25)
            self.nhap_text(ten)
            nghi_ngau_nhien(self.config['delay_nhap_ten'])
        else:
            if self.click_truong('Họ', False, 3, 0.6):
                self.nhap_text(ho)
            nghi_ngau_nhien(self.config['delay_nhap_ho'])
            if self.click_truong('Tên', False, 3, 0.6):
                self.nhap_text(ten)
            nghi_ngau_nhien(self.config['delay_nhap_ten'])

        self.log('⏩ Bấm nút Tiếp (sau khi nhập Họ Tên)')
        self.click_text('Tiếp', 'Tiếp', 3, 0.8) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6)
        nghi_ngau_nhien(self.config['delay_click_tiep_lan1'])

        self.vuot_chon_ngay_thang_nam_sinh()

        gioi_tinh = random.choice(['Nam', 'Nữ'])
        self.log(f'👤 Chọn giới tính: {gioi_tinh}')
        self.click_text(gioi_tinh, gioi_tinh, 3, 0.8) or self.click_text_chua(gioi_tinh, gioi_tinh, 2, 0.6)
        nghi_ngau_nhien(self.config['delay_chon_gioi_tinh'])

        self.log('⏩ Bấm nút Tiếp (sau khi chọn Giới tính)')
        self.click_text('Tiếp', 'Tiếp', 3, 0.8) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6)
        nghi_ngau_nhien(self.config['delay_click_tiep_lan5'])

        self.tat_quyen_khong_cho_phep()

        if mode == "6" and autosms_service:
            self.log('📞 [Mode 6] Đang thuê SĐT từ AutoSMS.site...')
            so_dt = autosms_service.buy_number()
            if not so_dt:
                self.log('❌ Không thuê được SĐT!')
                return None
            self.log(f'📞 Nhập SĐT thuê: {so_dt}')
            if self.d(className='android.widget.EditText').exists:
                self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
            else:
                self.click_truong('Số di động', False, 3, 0.6)
            time.sleep(0.3)
            self.nhap_text(so_dt)
            nghi_ngau_nhien(self.config['delay_nhap_sdt'])

            self.log('⏩ Bấm Tiếp (sau khi nhập SĐT)')
            self.click_text('Tiếp', 'Tiếp', 3, 0.8) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6)
            nghi_ngau_nhien(self.config['delay_click_tiep_sdt'])
            self.click_text_chua('Tiếp tục tạo tài khoản', 'Tiếp tục tạo TK', 2, 0.6, click_duoi=True)

            return self.xu_ly_mat_khau_va_otp(
                tai_khoan_lien_he=so_dt,
                mode="6",
                autosms_service=autosms_service
            )

        self.log('📧 Bấm nút "Đăng ký bằng email"...')
        if self.d(textContains='Đăng ký bằng email').exists or self.d(descriptionContains='Đăng ký bằng email').exists:
            self.click_text_chua('Đăng ký bằng email', 'Đăng ký bằng email', 3, 0.6)
            time.sleep(1.5)

        self.tat_quyen_khong_cho_phep()
        self.dong_goi_y_google()

        uid_moc = 0
        if mode in ["3", "4"] and imap_service:
            uid_moc = imap_service.get_latest_uid()
        elif mode == "5" and hotmail_service:
            hotmail_service.init_baseline()

        self.log(f'📧 Nhập Email: {used_email}')
        if self.d(className='android.widget.EditText').exists:
            self._click_phan_tu_an_toan(self.d(className='android.widget.EditText')[0])
            time.sleep(0.25)
            try:
                self.d.clear_text()
            except Exception:
                pass
            self.nhap_text(used_email)
        elif self.click_truong('Email', False, 3, 0.6):
            self.nhap_text(used_email)

        nghi_ngau_nhien(self.config['delay_nhap_email'])
        self.log('⏩ Bấm nút Tiếp (sau khi nhập Email)')
        self.click_text('Tiếp', 'Tiếp', 3, 0.8) or self.click_text_chua('Tiếp', 'Tiếp', 2, 0.6)
        nghi_ngau_nhien(self.config['delay_click_tiep_sau_email'])

        return self.xu_ly_mat_khau_va_otp(
            tai_khoan_lien_he=used_email,
            mode=mode,
            mail_service=mail_service,
            imap_service=imap_service,
            hotmail_service=hotmail_service,
            uid_moc=uid_moc
        )


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

    d_conn = None
    try:
        d_conn = u2.connect(serial) if serial else u2.connect()
    except Exception:
        d_conn = None

    while not stop_flag.is_set():
        try:
            used_email, mail_service, imap_service, hotmail_service, autosms_service = khoi_tao_dich_vu_theo_mode(
                mode, data_source, manual_password, base_gmail, app_password, api_mode, req_proxy, autosms_api_key, autosms_country
            )
            if not used_email:
                update_step(device_name, '⚠️ Đã hết dữ liệu đầu vào hoặc lỗi tạo mail! Dừng luồng...')
                break

            if d_conn is None:
                d_conn = u2.connect(serial) if serial else u2.connect()

            fb_ui = FacebookUI(serial, device_name, config, avatar_folder=avatar_folder, d_instance=d_conn)
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

            if imap_service:
                imap_service.close()

            if ket_qua:
                email_or_phone, mat_khau_fb, two_fa_key = ket_qua
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
            d_conn = None
            update_step(device_name, f'❌ Lỗi: {str(e)[:25]}')
            nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])


def main():
    global multi_mode
    os.makedirs(DEFAULT_AVATAR_DIR, exist_ok=True)
    print('\n──────────────────────────────────────────────────────────────────────')
    print(f'{trang}🤖 𝗧𝗢𝗢𝗟 𝗖𝗥𝗘𝗔𝗧𝗘 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞 𝗔𝗗𝗕 (𝗡𝗘𝗪 𝗨𝗜 + 𝗔𝗨𝗧𝗢 𝟮𝗙𝗔 𝗧𝗢𝗧𝗣){trang}')
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

    while True:
        token_tele, id_tele = doc_tele()
        trang_thai_ip = f"{xanh}✔ Bật{trang}" if config.get('doi_ip_may_bay', True) else f"{do}✘ Tắt{trang}"
        print('\n──────────────────────────────────────────────────────────────────────')
        print(f'{trang}📋  MENU CHÍNH')
        print('──────────────────────────────────────────────────────────────────────')
        print('1. Chạy Reg FB Giao Diện Mới + Auto Vuốt Ngày Sinh + Auto Avatar & 2FA')
        print(f"2. Gửi Về Tele    │ {(f'{xanh}✔{trang} Đã cấu hình' if token_tele and id_tele else f'{do}✘{trang} Chưa cấu hình')}")
        print(f'3. Cấu Hình Delay │ Đổi IP Máy Bay: {trang_thai_ip} • Anti-Checkpoint')
        print('4. Công Cụ Đổi Chuỗi Ký Tự 2FA -> Mã OTP 6 Số (Lấy mã nhanh)')
        print('──────────────────────────────────────────────────────────────────────')

        chon = input('Chọn chức năng (1, 2, 3 hoặc 4): ').strip()

        if chon == '4':
            print('\n──────────────────────────────────────────────────────────────────────')
            print('🔢 CHUYỂN ĐỔI KÝ TỰ SECRET KEY 2FA SANG MÃ OTP 6 SỐ')
            print('──────────────────────────────────────────────────────────────────────')
            raw_2fa = input('Nhập chuỗi 2FA (VD: ABCD EFGH IJKL...): ').strip()
            otp_6 = chuyen_doi_2fa_sang_otp(raw_2fa, doi_chu_ky_moi=False)
            if otp_6:
                con_lai = 30 - (int(time.time()) % 30)
                print(f'✅ Key sạch : {lam_sach_key_2fa(raw_2fa)}')
                print(f'🔢 Mã OTP   : {xanh}{otp_6}{trang} (Còn hiệu lực: {con_lai} giây)')
            else:
                print(f'{do}❌ Chuỗi 2FA không hợp lệ!{trang}')
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        elif chon == '2':
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
                if chon_tele == '2':
                    token_tele_moi = input('Nhập Token mới: ').strip()
                    id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
                    if token_tele_moi and id_tele_moi:
                        luu_tele(token_tele_moi, id_tele_moi)
                        print('✅ Đã cập nhật cấu hình Telegram!')
                elif chon_tele == '3' and os.path.exists(TELE_FILE):
                    os.remove(TELE_FILE)
                    print('🗑️ Đã xóa cấu hình Telegram!')
            else:
                token_tele_moi = input('Nhập Token: ').strip()
                id_tele_moi = input('Nhập ID Acc Tele Của Bạn: ').strip()
                if token_tele_moi and id_tele_moi:
                    luu_tele(token_tele_moi, id_tele_moi)
                    print('✅ Đã lưu cấu hình Telegram!')
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        elif chon == '3':
            config = cau_hinh_delay()
            input('\nNhấn Enter để quay lại Menu chính...')
            continue

        elif chon == '1':
            break
        else:
            print('❌ Lựa chọn không hợp lệ!')

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

    if mode == "2":
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
        built_in_print(f"{Colors.KEY}Nhập Mã Quốc Gia thuê sim (VD: vn, us, kh - Enter mặc định vn): {Colors.RESET}", end="")
        autosms_country = input().strip() or "vn"
        data_source = ["dummy_for_sms"] * 999999

    if not data_source and mode not in ["1", "4", "6"]:
        built_in_print(f"{Colors.ERROR}Danh sách đầu vào trống! Thoát chương trình.{Colors.RESET}")
        sys.exit()

    saved_avatar_folder = config_data.get("last_avatar_folder", "")
    avatar_folder_input = ""

    built_in_print(f"\n{Colors.TITLE}📁 CẤU HÌNH THƯ MỤC ẢNH AVATAR TRÊN MÁY TÍNH:{Colors.RESET}")
    built_in_print(f"   • Tool đã tạo sẵn thư mục mặc định tại: {Colors.VALUE}{DEFAULT_AVATAR_DIR}{Colors.RESET}")
    built_in_print(f"   • Bạn chỉ cần copy các ảnh (.jpg, .png) trên máy tính bỏ vào thư mục đó (hoặc nhập đường dẫn thư mục bất kỳ trên PC).")

    if saved_avatar_folder and os.path.isdir(saved_avatar_folder):
        built_in_print(f"   • Phát hiện thư mục Avatar lần trước: {Colors.VALUE}{saved_avatar_folder}{Colors.RESET}")
        use_old_avatar = input(f"{Colors.KEY}Bạn có muốn dùng lại thư mục này không? (y/n, Enter=y): {Colors.RESET}").strip().lower()
        if use_old_avatar in ['', 'y']:
            avatar_folder_input = saved_avatar_folder

    if not avatar_folder_input:
        built_in_print(f"{Colors.KEY}Nhập đường dẫn thư mục chứa ảnh trên PC (Nhấn Enter để dùng thư mục '{DEFAULT_AVATAR_DIR}'): {Colors.RESET}", end="")
        nhap_folder = input().strip().strip('"').strip("'")
        avatar_folder_input = nhap_folder if nhap_folder else DEFAULT_AVATAR_DIR
        if os.path.isdir(avatar_folder_input):
            config_data["last_avatar_folder"] = avatar_folder_input
            save_config(config_data)

    so_anh_pc = 0
    if os.path.isdir(avatar_folder_input):
        so_anh_pc = len([f for f in os.listdir(avatar_folder_input) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
    built_in_print(f"{Colors.SUCCESS}=> Đang dùng thư mục PC: {avatar_folder_input} (Tìm thấy {so_anh_pc} ảnh){Colors.RESET}")

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
                while any(t.is_alive() for t in threads):
                    time.sleep(1)
                print(f'\n{vang}🏁 Đã hoàn tất chạy trên tất cả thiết bị!{trang}')
                return
            else:
                multi_mode = False
                chon_device = input(f'Chọn thiết bị (1-{len(devices)}): ').strip()
                try:
                    serial, device_name = devices[int(chon_device) - 1]
                except Exception:
                    serial, device_name = devices[0]
        else:
            multi_mode = False
            serial, device_name = devices[0]

        used_names = set()
        used_phones = set()
        lan_chay = 0
        req_proxy = format_proxy(proxies_list[0]) if proxies_list else None

        d_conn_single = u2.connect(serial) if serial else u2.connect()

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
            fb_ui = FacebookUI(serial, device_name, config, avatar_folder=avatar_folder_input, d_instance=d_conn_single)

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

            if imap_service:
                imap_service.close()

            if ket_qua_dang_ky:
                email_or_phone, mat_khau_fb, two_fa_key = ket_qua_dang_ky
                print(f'\n✅ Đăng ký thành công! Tài khoản: {email_or_phone} | 2FA: {two_fa_key if two_fa_key else "Chưa bật"}')
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

            print(f"\n⏳ CHỜ {config['delay_giua_cac_lan_chay']} GIÂY...")
            nghi_ngau_nhien(config['delay_giua_cac_lan_chay'])

    except KeyboardInterrupt:
        print(f'\n\n{do}🛑 ĐÃ DỪNG{trang}')
        stop_flag.set()
        sys.exit(0)
    except Exception as e:
        print(f'Lỗi: {e}')


if __name__ == '__main__':
    main()
# ==================== KẾT THÚC PHẦN 2/2 ====================
