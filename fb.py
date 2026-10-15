# --- SHIM CHO PYTHON 3.12+ ---
import sys
import socket
import select
import base64
import io
import os
import time
import threading
import random
import re
from datetime import datetime
import uuid
import imaplib
import email
from email.header import decode_header
import json
import traceback
import string
import hashlib
import struct
import types

# Khắc phục lỗi font trên Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Fix lỗi distutils trên Python 3.12+
if 'distutils' not in sys.modules:
    distutils_mod = types.ModuleType('distutils')
    distutils_version_mod = types.ModuleType('distutils.version')
    class LooseVersion:
        def __init__(self, vstring=None):
            if vstring:
                self.parse(vstring)
        def parse(self, vstring):
            self.vstring = vstring
            self.version = [int(x) if x.isdigit() else x for x in re.compile(r'(\d+)').split(vstring) if x and x != '.']
        def __lt__(self, other):
            return self.version < (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __le__(self, other):
            return self.version <= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __eq__(self, other):
            return self.version == (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ne__(self, other):
            return self.version != (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __gt__(self, other):
            return self.version > (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ge__(self, other):
            return self.version >= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
    distutils_version_mod.LooseVersion = LooseVersion
    distutils_mod.version = distutils_version_mod
    sys.modules['distutils'] = distutils_mod
    sys.modules['distutils.version'] = distutils_version_mod

# Thư viện Chrome và Mã hóa
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Đang cài đặt thư viện thiếu...")
    os.system("pip install undetected-chromedriver selenium requests pyotp pycryptodome")
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import pyotp
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes

# Biến toàn cục
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock() 
DATA_LOCK = threading.Lock()
BROWSER_LOCK = threading.Lock()   
INPUT_LOCK = threading.Lock()        
TYPE_LOCK = threading.Lock() 
SUBMIT_LOCK = threading.Lock() 
PRINT_LOCK = threading.Lock()
DRIVER_LOCK = threading.Lock()
RESOURCE_LOCK = threading.Lock()

CONFIG_FILE = "config_gmail.json"
DELAY_CONFIG_FILE = "config_reg_fb.json"
BASE_YEAR = random.randint(1995, 2005)
APP_TOKEN = '350685531728|62f8ce9f74b12f84c123cc23437a4a32'

DEFAULT_DELAY_CONFIG = {
    'delay_mo_facebook': 10.0, 'delay_nhap_ho': 0.3, 'delay_nhap_ten': 0.3, 
    'delay_chon_ngay_sinh': 1.0, 'delay_chon_gioi_tinh': 0.5, 'delay_nhap_sdt_email': 1.0, 
    'delay_nhap_mat_khau': 1.0, 'delay_ngam_form_truoc_submit': 10.0, 'delay_validate_form': 5.0, 
    'delay_sau_khi_submit': 15.0, 'delay_ngam_otp': 60.0, 'delay_cho_load_trang_chu': 35.0, 
    'delay_giua_cac_lan_chay': 6.0, 'delay_thu_lai_khi_loi': 6.0, 'so_lan_thu_get_code': 2, 
    'mat_khau_fb': '', 'use_phone_bait': False, 'lay_token_android': True   
}

ALL_DRIVERS = []
GLOBAL_USED_PHONES = set()
GLOBAL_USED_NAMES = set()

# Print đồng bộ
built_in_print = print
PAUSE_FOR_INPUT = threading.Event()
PAUSE_FOR_INPUT.set() 
def thread_safe_print(*args, **kwargs):
    PAUSE_FOR_INPUT.wait() 
    with PRINT_LOCK:
        built_in_print(*args, **kwargs)
print = thread_safe_print 

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

def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    built_in_print(f"""{Colors.PRIMARY}
 ██████╗ ██╗  ██╗██████╗  ██████╗ ███╗   ███╗███████╗
██╔════╝ ██║  ██║██╔══██╗██╔═══██╗████╗ ████║██╔════╝
██║  ███╗███████║██████╔╝██║   ██║██╔████╔██║█████╗  
██║   ██║██╔══██║██╔══██║██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
{Colors.RESET}""")
    built_in_print(f"{Colors.INFO}Phiên Bản: v20.7 (Fixed Month Select & New Phone Bait UI) {Colors.RESET}")
    built_in_print(f"{Colors.LINE}{'─'*75}{Colors.RESET}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception: pass

def doc_delay_config():
    if os.path.exists(DELAY_CONFIG_FILE):
        try:
            with open(DELAY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_DELAY_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            return DEFAULT_DELAY_CONFIG.copy()
    else:
        with open(DELAY_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DELAY_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_DELAY_CONFIG.copy()

def luu_delay_config(config):
    try:
        with open(DELAY_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception: pass

def nhap_delay(tieu_de, gia_tri_mac_dinh):
    try:
        nhap = input(f'    {Colors.KEY}{tieu_de} ({gia_tri_mac_dinh} giây): {Colors.RESET}').strip()
        if nhap: return float(nhap)
    except KeyboardInterrupt: raise KeyboardInterrupt
    except Exception: pass
    return gia_tri_mac_dinh

def cau_hinh_delay():
    built_in_print(f'\n{Colors.LINE}──────────────────────────────────────────────────────────────────────{Colors.RESET}')
    built_in_print(f'{Colors.TITLE}⚙️  CẤU HÌNH DELAY & TÙY CHỌN NÂNG CAO{Colors.RESET}')
    built_in_print(f'{Colors.LINE}──────────────────────────────────────────────────────────────────────{Colors.RESET}')
    config = doc_delay_config()

    built_in_print(f'\n{Colors.INFO}【MẬT KHẨU & CHẾ ĐỘ ĐĂNG KÝ】{Colors.RESET}')
    mk_hien_tai = config['mat_khau_fb'] if config['mat_khau_fb'] else "Tự động Random 12 ký tự"
    mat_khau_moi = input(f'    {Colors.KEY}Nhập mật khẩu cố định (Enter giữ [{mk_hien_tai}], gõ "rand" để random): {Colors.RESET}').strip()
    if mat_khau_moi.lower() == 'rand': config['mat_khau_fb'] = ''
    elif mat_khau_moi: config['mat_khau_fb'] = mat_khau_moi

    chon_moi_sdt = input(f'    {Colors.KEY}Bật chế độ Mồi SĐT +84 ảo rồi đổi sang Xác nhận Email ở Mode 1-5? (y/n, hiện tại: {config["use_phone_bait"]}): {Colors.RESET}').strip().lower()
    if chon_moi_sdt in ['y', 'n']: config['use_phone_bait'] = (chon_moi_sdt == 'y')

    chon_token = input(f'    {Colors.KEY}Tự động lấy thêm Access Token Android (EAAAAU...) sau khi reg xong? (y/n, hiện tại: {config["lay_token_android"]}): {Colors.RESET}').strip().lower()
    if chon_token in ['y', 'n']: config['lay_token_android'] = (chon_token == 'y')

    built_in_print(f'\n{Colors.INFO}【THÔNG SỐ DELAY TRÌNH DUYỆT (Giây)】{Colors.RESET}')
    for k in ['delay_mo_facebook', 'delay_nhap_ho', 'delay_nhap_ten', 'delay_chon_ngay_sinh', 'delay_chon_gioi_tinh', 'delay_nhap_sdt_email', 'delay_nhap_mat_khau', 'delay_ngam_form_truoc_submit', 'delay_validate_form', 'delay_sau_khi_submit', 'delay_ngam_otp', 'delay_cho_load_trang_chu', 'delay_giua_cac_lan_chay']:
        config[k] = nhap_delay(f'Delay {k}', config[k])
    config['so_lan_thu_get_code'] = int(nhap_delay('Số lần bấm Gửi lại mã tối đa', config['so_lan_thu_get_code']))
    
    luu_delay_config(config)
    built_in_print(f'\n{Colors.SUCCESS}✅ Đã lưu cấu hình thành công!{Colors.RESET}\n')
    return config

def save_account(thread_id, email_str, password, uid, full_name, mode="auto", cookie="", two_fa="", access_token=""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_tong = os.path.join(current_dir, "danh_sach_acc_fb.txt")
    folder_name = os.path.join(current_dir, "Facebook_reg_PC")
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder_name, f"account_{thread_id}_{timestamp}.txt")
    dinh_dang_luu = f"{uid}|{password}|{email_str}|{two_fa}|{cookie}|{access_token}\n"
    try:
        with open(file_tong, 'a', encoding='utf-8') as f: f.write(dinh_dang_luu)
        content = f"Luồng: {thread_id}\nUID: {uid}\nHọ Tên: {full_name}\nEmail/SĐT: {email_str}\nPass: {password}\n2FA: {two_fa}\nAccess Token: {access_token}\nCookie: {cookie}\n"
        with open(filename, 'w', encoding='utf-8') as f: f.write(content)
    except Exception as e: print(f"Lỗi khi lưu file: {e}")

def tao_so_dien_thoai(used_phones=None):
    target_set = used_phones if used_phones is not None else GLOBAL_USED_PHONES
    dau_so = ['333', '338', '339', '358', '359', '368', '369', '378', '379',
              '388', '389', '396', '397', '398', '399', '777', '778', '779',
              '787', '788', '789', '968', '969', '978', '979', '988', '989']
    with RESOURCE_LOCK:
        while True:
            phone = f"+84{random.choice(dau_so)}{''.join(random.choices(string.digits, k=6))}"
            if phone not in target_set:
                target_set.add(phone)
                return phone

def VietnameseMaleNameGenerator(used_names=None):
    target_set = used_names if used_names is not None else GLOBAL_USED_NAMES
    ho_list = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Vu", "Dang", "Bui", "Do"]
    middle_list = ["Van", "Minh", "Hoang", "Duc", "Dinh", "Gia", "Bao", "Quang", "Tuan", "Xuan"]
    ten_list = ["An", "Binh", "Cuong", "Dung", "Hung", "Hai", "Son", "Tien", "Trung", "Vinh", "Nam", "Phuc", "Thanh", "Khoa"]
    
    with RESOURCE_LOCK:
        for _ in range(100):
            last_name_fb = f"{random.choice(ho_list)} {random.choice(middle_list)}"
            first_name_fb = random.choice(ten_list)
            full_name = f"{last_name_fb} {first_name_fb}"
            if full_name not in target_set:
                target_set.add(full_name)
                break
                
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())
    extra_chars = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=2))
    username = f"{cleaned}{extra_chars}{random.randint(10000, 999999)}"
    return last_name_fb, first_name_fb, full_name, username

class Facebook:
    def MaHoaMatKhau(self, mat_khau):
        try:
            url = 'https://b-graph.facebook.com/pwd_key_fetch'
            params = {
                'version': '2', 'flow': 'CONTROLLER_INITIALIZATION', 'method': 'GET',
                'fb_api_req_friendly_name': 'pwdKeyFetch',
                'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations',
                'access_token': '438142079694454|fc0a7caa49b192f64f6f5a6d9643bb28'
            }
            response = requests.post(url, params=params, timeout=15, proxies=self.proxy).json()
            public_key = response.get('public_key')
            key_id = str(response.get('key_id', '25'))
            rand_key = get_random_bytes(32)
            iv = get_random_bytes(12)
            pubkey = RSA.import_key(public_key)
            cipher_rsa = PKCS1_v1_5.new(pubkey)
            encrypted_rand_key = cipher_rsa.encrypt(rand_key)
            cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
            current_time = int(time.time())
            cipher_aes.update(str(current_time).encode('utf-8'))
            encrypted_passwd, auth_tag = cipher_aes.encrypt_and_digest(mat_khau.encode('utf-8'))
            buf = io.BytesIO()
            buf.write(bytes([1, int(key_id)]))
            buf.write(iv)
            buf.write(struct.pack('<h', len(encrypted_rand_key)))
            buf.write(encrypted_rand_key)
            buf.write(auth_tag)
            buf.write(encrypted_passwd)
            encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"#PWD_FB4A:2:{current_time}:{encoded}"
        except KeyboardInterrupt: raise KeyboardInterrupt
        except Exception: return mat_khau

    @staticmethod
    def _tao_machine_id():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=24))

    def __init__(self, email=None, mat_khau=None, auth=None, proxy=None):
        self.proxy = proxy
        self.email = email
        self.mat_khau = self.MaHoaMatKhau(mat_khau) if mat_khau else None
        self.auth = auth.replace(' ', '') if auth else None
        self.URL = 'https://b-graph.facebook.com/auth/login'
        self.API_KEY = '882a8490361da98702bf97a021ddc14d'
        self.SIG = '214049b9f17c38bd767de53752b53946'
        self.device_id = str(uuid.uuid4())
        self.adid = str(uuid.uuid4())
        self.machine_id = self._tao_machine_id()
        self.jazoest = ''.join(random.choices(string.digits, k=5))
        self.HEADERS = {
            'content-type': 'application/x-www-form-urlencoded', 'x-fb-net-hni': '45201', 'zero-rated': '0',
            'x-fb-sim-hni': '45201', 'x-fb-connection-quality': 'EXCELLENT', 'x-fb-friendly-name': 'authenticate',
            'x-fb-connection-bandwidth': '78032897', 'x-tigon-is-retry': 'False', 'authorization': 'OAuth null',
            'x-fb-connection-type': 'WIFI', 'x-fb-device-group': '3342', 'priority': 'u=3,i', 'x-fb-http-engine': 'Liger',
            'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True',
            'x-fb-request-analytics-tags': '{"network_tags":{"product":"350685531728","retry_attempt":"0"},"application_tags":"unknown"}',
            'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 9; 23113RKC6C Build/PQ3A.190705.08211809) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/vi_VN;FBBV/480086274;FBCR/MobiFone;FBMF/Redmi;FBBD/Redmi;FBDV/23113RKC6C;FBSV/9;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=1280,height=720};FB_FW/1;FBRV/0;]'
        }

    def DangNhap(self, app_token=APP_TOKEN):
        self.data = {
            'email': self.email, 'password': self.mat_khau, 'generate_session_cookies': '1', 'locale': 'vi_VN',
            'client_country_code': 'VN', 'access_token': app_token, 'api_key': self.API_KEY, 'adid': self.adid,
            'account_switcher_uids': f'["{self.email}"]', 'source': 'login', 'machine_id': self.machine_id,
            'jazoest': self.jazoest, 'meta_inf_fbmeta': 'V2_UNTAGGED', 'fb_api_req_friendly_name': 'authenticate',
            'fb_api_caller_class': 'Fb4aAuthHandler', 'sig': self.SIG
        }
        try:
            ket_qua = requests.post(self.URL, headers=self.HEADERS, data=self.data, timeout=15, proxies=self.proxy).json()
            if 'error' in ket_qua:
                error_msg = ket_qua.get('error', {}).get('message', 'Lỗi không xác định')
                error_data = ket_qua.get('error', {}).get('error_data', {})
                if 'login_first_factor' in error_data and 'uid' in error_data:
                    if self.auth: ma_2fa = pyotp.TOTP(self.auth).now()
                    else: return {'status': 401, 'msg': 'Yêu cầu 2FA nhưng chưa có Secret Key'}
                    data_2fa = {
                        'locale': 'vi_VN', 'format': 'json', 'email': self.email, 'device_id': self.device_id,
                        'access_token': app_token, 'generate_session_cookies': 'true', 'generate_machine_id': '1',
                        'twofactor_code': ma_2fa, 'credentials_type': 'two_factor', 'error_detail_type': 'button_with_disabled',
                        'first_factor': error_data['login_first_factor'], 'password': self.mat_khau,
                        'userid': error_data['uid'], 'machine_id': error_data['login_first_factor']
                    }
                    ket_qua = requests.post(self.URL, headers=self.HEADERS, data=data_2fa, timeout=15, proxies=self.proxy).json()
                else: return {'status': 401, 'msg': error_msg}
            if 'access_token' in ket_qua:
                access_token = ket_qua.get('access_token')
                cookies_list = ket_qua.get('session_cookies', [])
                cookies_string = '; '.join((f"{c['name']}={c['value']}" for c in cookies_list))
                return {'status': 200, 'data': {'cookies': cookies_string, 'token': access_token}}
            return {'status': 401, 'msg': ket_qua.get('error', {}).get('message', 'Đăng nhập thất bại')}
        except KeyboardInterrupt: raise KeyboardInterrupt
        except Exception as e: return {'status': 401, 'msg': str(e)}

def parse_proxy(proxy_str):
    if not proxy_str: return None
    p_str = str(proxy_str).strip()
    if not p_str: return None
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
        except Exception: pass
    parts = [x.strip() for x in p_str.split(":") if x.strip()]
    if len(parts) == 2: return {"ip": parts[0], "port": parts[1], "user": None, "pass": None}
    elif len(parts) == 4:
        if parts[1].isdigit() and not parts[2].isdigit(): return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
        elif parts[3].isdigit(): return {"ip": parts[2], "port": parts[3], "user": parts[0], "pass": parts[1]}
        else: return {"ip": parts[0], "port": parts[1], "user": parts[2], "pass": parts[3]}
    return None

def format_proxy(proxy_str):
    parsed = parse_proxy(proxy_str)
    if not parsed: return None
    if parsed["user"] and parsed["pass"]:
        formatted = f"http://{parsed['user']}:{parsed['pass']}@{parsed['ip']}:{parsed['port']}"
    else: formatted = f"http://{parsed['ip']}:{parsed['port']}"
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
            except Exception: break

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
                if auth_header: connect_req += auth_header
                connect_req += crlf
                remote_sock.sendall(connect_req)
                resp = b""
                while crlf2 not in resp:
                    c = remote_sock.recv(4096)
                    if not c: break
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
                if auth_header: new_req += auth_header
                new_req += crlf + rest
                remote_sock.sendall(new_req)

            remote_sock.settimeout(None)
            client_sock.settimeout(None)
            sockets = [client_sock, remote_sock]
            while self.running:
                r, _, _ = select.select(sockets, [], sockets, 30)
                if not r: break
                for s in r:
                    other = remote_sock if s is client_sock else client_sock
                    data = s.recv(16384)
                    if not data: return
                    other.sendall(data)
        except Exception: pass
        finally:
            try: client_sock.close()
            except: pass
            try: remote_sock.close()
            except: pass

    def close(self):
        self.running = False
        try: self.server_socket.close()
        except: pass

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
        except Exception: return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10, proxies=self.proxy)
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except Exception: return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        time.sleep(random.uniform(0.5, 2.0)) 
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10, proxies=self.proxy)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception: return False
            
    def get_otp_code(self, timeout=120, force_8_digits=False):
        if not self.token: return None
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        start_time = time.time()
        time.sleep(random.uniform(1.0, 5.0))
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=10, proxies=self.proxy)
                if r.status_code == 200:
                    for msg in r.json().get('hydra:member', []):
                        msg_id = msg.get('id')
                        if not msg_id or msg_id in self.seen_msg_ids: continue
                            
                        subject = str(msg.get('subject', '')).lower()
                        frm = str(msg.get('from', {}).get('address', '')).lower()
                        if any(k in subject or k in frm for k in ['facebook', 'facebookmail', 'fb', 'meta', 'instagram']):
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or re.sub('<[^<]+?>', ' ', str(detail.get('html', '')))
                            
                            code = None
                            if force_8_digits:
                                clean_txt = raw_text.replace(" ", "")
                                match = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_txt)
                                if match: code = match.group(1)
                            else:
                                match_fb = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', raw_text, re.IGNORECASE)
                                if match_fb: code = match_fb.group(1)
                                else:
                                    match_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                    if match_sub: code = match_sub.group(1)
                                    else:
                                        safe_text = raw_text.lower().replace(str(self.email_address).lower(), "")
                                        match_body = re.search(r'(?<!\d)(\d{5,6})(?!\d)', safe_text.replace(" ", ""))
                                        if match_body: code = match_body.group(1)

                            if code:
                                self.seen_msg_ids.add(msg_id)
                                return code
            except Exception: pass
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
        plain, html_list = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment": continue
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)
                if not payload: continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/plain": plain.append(text)
                elif ctype == "text/html": html_list.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/plain": plain.append(text)
                else: html_list.append(text)
        if plain: return "\n".join(plain).strip()
        if html_list: return re.sub(r'<[^>]+>', ' ', "\n".join(html_list)).strip()
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
                else: result += str(text)
            return result
        except: return str(raw_header)

    def get_otp_code(self, target_email, since_uid=0, timeout=120, force_8_digits=False):
        if not self.mail:
            if not self.connect(): return None
        start_time = time.time()
        time.sleep(random.uniform(1.0, 5.0))
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
                                
                                is_fb_meta = any(k in subject or k in from_addr for k in ["facebook", "facebookmail", "fb", "meta", "instagram"])
                                is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã", "authenticate", "profile", "confirm", "xác nhận", "fb-"])
                                
                                if is_fb_meta and is_security_mail:
                                    body = self.get_text(msg)
                                    code = None
                                    if force_8_digits:
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', body.replace(" ", ""))
                                        if match_8: code = match_8.group(1)
                                    else:
                                        match_fb = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', body, re.IGNORECASE)
                                        if match_fb: code = match_fb.group(1)
                                        else:
                                            match_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                            if match_sub: code = match_sub.group(1)
                                            else:
                                                safe_text = body.lower().replace(target_email.lower(), "")
                                                match_body = re.search(r'(?<!\d)(\d{5,6})(?!\d)', safe_text.replace(" ", ""))
                                                if match_body: code = match_body.group(1)

                                    if code:
                                        self.seen_uids.add(uid_bytes) 
                                        return code
            except Exception: pass
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
        if self.proxy: self.session.proxies.update(self.proxy)
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
                            if not msg_id: msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                            self.seen_msg_ids.add(msg_id)
                    break 
            except Exception: time.sleep(3) 

    def get_otp_code(self, timeout=180, force_8_digits=False): 
        start_time = time.time()
        loai_ma = "ÉP ĐỌC MÃ 8 SỐ 2FA" if force_8_digits else "ĐỌC MÃ ĐĂNG KÝ 5-6 SỐ"
        print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email} ({loai_ma})...', Colors.INFO)}")
        payload = {"mode": self.api_mode, "data": self.data_line}
        time.sleep(random.uniform(1.0, 5.0))
        last_logged = ""
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
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
                            if msg_err != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_err}', Colors.ERROR)}")
                                last_logged = msg_err
                        else:
                            messages = account_data.get("messages", [])
                            msg_info = f"Tìm thấy {len(messages)} thư."
                            if msg_info != last_logged:
                                print(f"{Colors.color_text(f'[API Smail1s] {msg_info} Đang check từng thư lấy mã...', Colors.INFO)}")
                                last_logged = msg_info
                            for msg in messages:
                                msg_id = str(msg.get("id", msg.get("uid", "")))
                                if not msg_id: msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                                if msg_id in self.seen_msg_ids: continue
                                
                                subject = str(msg.get("subject", "")).lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))
                                
                                is_fb_meta = any(k in subject or k in from_sender for k in ["facebook", "facebookmail", "fb", "meta", "instagram"])
                                is_security_mail = True 
                                if force_8_digits:
                                    is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã", "factor", "authenticate", "profile", "account"])
                                
                                if is_fb_meta and is_security_mail:
                                    code = None
                                    if force_8_digits:
                                        clean_text = re.sub(r'<[^>]+>', ' ', raw_msg).replace(" ", "")
                                        match_8 = re.search(r'(?<!\d)(\d{8})(?!\d)', clean_text)
                                        if match_8: code = match_8.group(1)
                                    else:
                                        match_fb = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', raw_msg, re.IGNORECASE)
                                        if match_fb: code = match_fb.group(1)
                                        else:
                                            match_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                            if match_sub: code = match_sub.group(1)
                                            else:
                                                safe_msg = raw_msg.lower().replace(self.email.lower(), "")
                                                clean_text = re.sub(r'<[^>]+>', ' ', safe_msg).replace(" ", "")
                                                match_6 = re.search(r'(?<!\d)(\d{5,6})(?!\d)', clean_text)
                                                if match_6: code = match_6.group(1)
                                    if code:
                                        self.seen_msg_ids.add(msg_id)
                                        print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}")
                                        return code
                else:
                    status_err = f"Lỗi HTTP {response.status_code}"
                    if status_err != last_logged:
                        print(f"{Colors.color_text(f'[API Smail1s] {status_err}', Colors.WARNING)}")
                        last_logged = status_err
            except requests.exceptions.RequestException as e:
                err_str = "Lỗi kết nối Smail1s. Đang thử lại..."
                if err_str != last_logged:
                    print(f"{Colors.color_text(f'[API Smail1s] {err_str} (Chi tiết: {e})', Colors.WARNING)}")
                    last_logged = err_str
                try: self._init_session() 
                except: pass
            except Exception as e: pass
            time.sleep(random.uniform(5.0, 8.0))
        return None

class AutoSMSService:
    def __init__(self, api_key, country="vn", proxy=None):
        self.api_key = api_key
        self.country = country
        self.service = "facebook"
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
        except Exception: pass
        return None

    def get_otp_code(self, timeout=120):
        if not self.order_id: return None
        start_time = time.time()
        url = f"{self.base_url}/orders/{self.order_id}?key={self.api_key}"
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                r = requests.get(url, timeout=10, proxies=self.proxy)
                js = r.json()
                if js.get("success") and js.get("data") and js["data"].get("code"):
                    return js["data"]["code"]
            except Exception: pass
            time.sleep(4)
        return None

    def cancel_order(self):
        if self.order_id:
            try: requests.get(f"{self.base_url}/cancel/{self.order_id}?key={self.api_key}", timeout=10, proxies=self.proxy)
            except Exception: pass

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

# ==================== MAIN THREAD ====================
class starts(threading.Thread):
    def __init__(self, thread_id, mode, account_count, data_source, delay_config, manual_password=None, base_gmail=None, app_password=None, api_mode=None, avatar_folder="", proxies_list=None, autosms_api_key=None, autosms_country="vn"):
        super().__init__()
        self.thread_id = f"Tab-{thread_id}"
        self.mode = mode
        self.account_count = account_count
        self.data_source = data_source
        self.delay_config = delay_config
        self.manual_password = manual_password 
        self.base_gmail = base_gmail
        self.app_password = app_password
        self.api_mode = api_mode
        self.avatar_folder = avatar_folder
        self.proxies_list = proxies_list or [] 
        self.autosms_api_key = autosms_api_key
        self.autosms_country = autosms_country
        self.used_phones = set()
        self.used_names = set()
    
    def run(self):
        global BASE_YEAR
        
        raw_proxy = None
        req_proxy = None
        if self.proxies_list:
            thread_idx_for_proxy = int(self.thread_id.split("-")[1]) - 1
            raw_proxy = self.proxies_list[thread_idx_for_proxy % len(self.proxies_list)]
            req_proxy = format_proxy(raw_proxy)
            p_info = parse_proxy(raw_proxy)
            
            if p_info and p_info.get("user"):
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (Có User/Pass): {p_info['ip']}:{p_info['port']}", Colors.WARNING))
            elif p_info:
                print(Colors.color_text(f"[{self.thread_id}] Đã gán Proxy (IP:Port): {p_info['ip']}:{p_info['port']}", Colors.WARNING))
        
        def create_one_account(account_index):
            global BASE_YEAR
            if STOP_EVENT.is_set(): return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{self.thread_id}] BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email = ""
            imap_service = None
            mail_service = None
            hotmail_service = None
            autosms_service = None
            
            last_name_fb, first_name_fb, full_name, username = VietnameseMaleNameGenerator(self.used_names)
            
            if self.delay_config.get('mat_khau_fb'):
                secure_pass = self.delay_config['mat_khau_fb']
            else:
                chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%"
                secure_pass = "".join(random.choice(chars) for _ in range(12))

            if self.mode == "1":
                mail_service = MailService(proxy=req_proxy)
                used_email = mail_service.create_account(username)
                if not used_email: return False
                mail_service.authenticate()
            elif self.mode == "2":
                with DATA_LOCK:
                    if len(self.data_source) == 0: return False
                    used_email = self.data_source.pop(0)
                if "mail.tm" in used_email.lower():
                    mail_service = MailService(proxy=req_proxy)
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
                hotmail_service = HotmailAPIService(data_line, self.api_mode, proxy=req_proxy)
            elif self.mode == "6":
                autosms_service = AutoSMSService(self.autosms_api_key, self.autosms_country, proxy=req_proxy)
                used_email = autosms_service.buy_number()
                if not used_email:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể thuê số điện thoại từ API (Hết số hoặc Sai Key)!', Colors.ERROR)}")
                    return False

            use_phone_bait = self.delay_config.get('use_phone_bait', False) and (self.mode in ["1", "2", "3", "4", "5"])
            contact_for_signup = tao_so_dien_thoai(self.used_phones) if use_phone_bait else used_email

            if use_phone_bait:
                print(f"{Colors.color_text(f'[{self.thread_id}] Chế độ Mồi SĐT: Nhập {contact_for_signup} -> Xác nhận qua Email: {used_email}', Colors.INFO)}")
            else:
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang dùng Email/SĐT: {used_email}', Colors.INFO)}")

            driver = None
            try:
                thread_idx = int(self.thread_id.split("-")[1]) - 1 
                win_width, win_height = 460, 520  
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
                options.add_argument('--incognito')
                
                forwarder = None
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
                    with DRIVER_LOCK: ALL_DRIVERS.append((self.thread_id, driver))
                    try:
                        driver.set_window_size(win_width, win_height)
                        driver.set_window_position(x_pos, y_pos)
                    except: pass
                    time.sleep(1) 
                    
                wait = WebDriverWait(driver, 15)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang truy cập Facebook Web qua Proxy...', Colors.INFO)}")
                driver.get("https://www.facebook.com/r.php")
                
                delay_mo_fb = self.delay_config['delay_mo_facebook']
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang chờ trang tải hoàn tất ({delay_mo_fb}s)...', Colors.WARNING)}")
                time.sleep(delay_mo_fb)
                
                try:
                    cookie_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Cho phép') or contains(text(), 'Đồng ý')] | //div[@role='button' and (contains(., 'Allow') or contains(., 'Cho phép'))]")
                    if cookie_btns:
                        driver.execute_script("arguments[0].click();", cookie_btns[0])
                        time.sleep(2)
                except: pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: current_year = "2005"
                current_day = str(random.randint(2, 28))
                current_month = str(random.randint(1, 12))
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)

                def slow_scroll_to_element(element):
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(0.5)
                    except: pass

                def human_type(element, text):
                    with TYPE_LOCK:
                        slow_scroll_to_element(element)
                        try: element.click() 
                        except: driver.execute_script("arguments[0].click();", element) 
                        time.sleep(0.5)
                        
                        driver.execute_script("arguments[0].focus();", element)
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

                # ==================== ĐIỀN FORM ĐĂNG KÝ FACEBOOK ====================
                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang phân tích các ô nhập liệu trên Form Meta...', Colors.INFO)}")

                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]")))
                    time.sleep(2)

                    visible_inputs = []
                    for inp in driver.find_elements(By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]"):
                        if inp.is_displayed():
                            visible_inputs.append(inp)

                    if len(visible_inputs) >= 4:
                        ho_el = visible_inputs[0]
                        ten_el = visible_inputs[1]
                        email_el = visible_inputs[2]
                        pass_el = visible_inputs[3]

                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Họ ({last_name_fb}) và Tên ({first_name_fb})...', Colors.INFO)}")
                        human_type(ho_el, last_name_fb)
                        time.sleep(self.delay_config['delay_nhap_ho'])
                        human_type(ten_el, first_name_fb)
                        time.sleep(self.delay_config['delay_nhap_ten'])

                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Email/SĐT ({contact_for_signup})...', Colors.INFO)}")
                        human_type(email_el, contact_for_signup)
                        time.sleep(self.delay_config['delay_nhap_sdt_email'])

                        time.sleep(1.5)
                        visible_inputs_after = [inp for inp in driver.find_elements(By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]") if inp.is_displayed()]
                        if len(visible_inputs_after) >= 5 and ("email" in contact_for_signup.lower() or "@" in contact_for_signup):
                            print(f"{Colors.color_text(f'[{self.thread_id}] Nhận diện có ô Xác nhận Email, tiến hành điền...', Colors.INFO)}")
                            human_type(visible_inputs_after[3], contact_for_signup)
                            pass_el = visible_inputs_after[4]

                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Mật khẩu...', Colors.INFO)}")
                        human_type(pass_el, secure_pass)
                        time.sleep(self.delay_config['delay_nhap_mat_khau'])
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm đủ 4 ô nhập liệu! Cấu trúc form chưa load xong.', Colors.ERROR)}")
                        return False

                    # CHỌN NGÀY THÁNG NĂM VÀ GIỚI TÍNH (ĐÃ FIX LỖI KHÔNG CHỌN ĐƯỢC THÁNG)
                    gender_text = "Nam"
                    print(f"{Colors.color_text(f'[{self.thread_id}] Chọn Ngày Sinh ({current_day}/{current_month}/{current_year}) và Giới tính ({gender_text})...', Colors.INFO)}")

                    try:
                        driver.set_script_timeout(30)
                        js_dropdowns = """
                        const day = String(arguments[0]), month = String(arguments[1]), year = String(arguments[2]), gender = String(arguments[3]), callback = arguments[4];

                        function isVisible(el) {
                            if (!el) return false;
                            const rect = el.getBoundingClientRect();
                            const style = window.getComputedStyle(el);
                            return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                        }

                        function triggerMouseClick(el) {
                            if (!el) return;
                            el.scrollIntoView({block: 'center'});
                            const rect = el.getBoundingClientRect();
                            const cx = rect.left + rect.width / 2;
                            const cy = rect.top + rect.height / 2;
                            ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(evtType => {
                                el.dispatchEvent(new MouseEvent(evtType, {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true,
                                    clientX: cx,
                                    clientY: cy
                                }));
                            });
                            try { el.click(); } catch(e) {}
                        }

                        function normalizeText(str) {
                            return (str || "").replace(/\\s+/g, " ").trim().toLowerCase();
                        }

                        const monthSynonyms = {
                            "1": ["tháng 1", "tháng 01", "thg 1", "thg 01", "tháng một", "tháng giêng", "jan", "january", "1", "01"],
                            "2": ["tháng 2", "tháng 02", "thg 2", "thg 02", "tháng hai", "feb", "february", "2", "02"],
                            "3": ["tháng 3", "tháng 03", "thg 3", "thg 03", "tháng ba", "mar", "march", "3", "03"],
                            "4": ["tháng 4", "tháng 04", "thg 4", "thg 04", "tháng tư", "tháng bốn", "apr", "april", "4", "04"],
                            "5": ["tháng 5", "tháng 05", "thg 5", "thg 05", "tháng năm", "may", "5", "05"],
                            "6": ["tháng 6", "tháng 06", "thg 6", "thg 06", "tháng sáu", "jun", "june", "6", "06"],
                            "7": ["tháng 7", "tháng 07", "thg 7", "thg 07", "tháng bảy", "jul", "july", "7", "07"],
                            "8": ["tháng 8", "tháng 08", "thg 8", "thg 08", "tháng tám", "aug", "august", "8", "08"],
                            "9": ["tháng 9", "tháng 09", "thg 9", "thg 09", "tháng chín", "sep", "sept", "september", "9", "09"],
                            "10": ["tháng 10", "thg 10", "tháng mười", "oct", "october", "10"],
                            "11": ["tháng 11", "thg 11", "tháng mười một", "nov", "november", "11"],
                            "12": ["tháng 12", "thg 12", "tháng mười hai", "tháng chạp", "dec", "december", "12"]
                        };

                        async function selectComboboxByIndex(index, searchValue, fieldType) {
                            let combos = Array.from(document.querySelectorAll('div[role="combobox"], select')).filter(isVisible);
                            if (combos.length <= index) {
                                // Dự phòng nếu giới tính là radio button truyền thống
                                if (fieldType === 'gender') {
                                    let radios = Array.from(document.querySelectorAll('input[type="radio"]')).filter(isVisible);
                                    let maleRadio = radios.find(r => r.value === "2") || radios[1] || radios[0];
                                    if (maleRadio) {
                                        triggerMouseClick(maleRadio);
                                        return true;
                                    }
                                }
                                return false;
                            }

                            let box = combos[index];

                            // Trường hợp thẻ <select> truyền thống
                            if (box.tagName.toLowerCase() === 'select') {
                                let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
                                nativeSetter.call(box, searchValue);
                                if (box.value !== String(searchValue) && fieldType === 'month') {
                                    let mIdx = parseInt(searchValue, 10);
                                    if (box.options.length > mIdx) box.selectedIndex = mIdx;
                                    else if (box.options.length === 12) box.selectedIndex = mIdx - 1;
                                }
                                box.dispatchEvent(new Event('input', { bubbles: true }));
                                box.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }

                            // Lưu lại các option đang hiển thị trước khi mở combobox để loại trừ
                            let preVisibleOptions = new Set(
                                Array.from(document.querySelectorAll('div[role="option"], li, div[role="menuitem"], div[role="menuitemradio"]')).filter(isVisible)
                            );

                            triggerMouseClick(box);
                            await new Promise(r => setTimeout(r, 900));

                            // Tìm các option đang hiển thị thực tế trên màn hình
                            let controlledId = box.getAttribute('aria-controls') || box.getAttribute('aria-owns');
                            let visibleOptions = [];
                            if (controlledId && document.getElementById(controlledId)) {
                                visibleOptions = Array.from(
                                    document.getElementById(controlledId).querySelectorAll('div[role="option"], li, div[role="menuitem"], div[role="menuitemradio"]')
                                ).filter(isVisible);
                            }

                            if (visibleOptions.length === 0) {
                                let allVis = Array.from(
                                    document.querySelectorAll('div[role="option"], li, div[role="menuitem"], div[role="menuitemradio"]')
                                ).filter(isVisible);
                                let newlyOpened = allVis.filter(o => !preVisibleOptions.has(o));
                                visibleOptions = newlyOpened.length > 0 ? newlyOpened : allVis;
                            }

                            let opt = null;
                            let search = normalizeText(searchValue);

                            if (fieldType === 'month') {
                                let validMonthTexts = monthSynonyms[search] || [search, "tháng " + search, "thg " + search, "0" + search];
                                // Ưu tiên khớp định dạng có chữ "tháng"/"thg"/tên tiếng Anh trước
                                for (let syn of validMonthTexts) {
                                    opt = visibleOptions.find(o => normalizeText(o.innerText || o.textContent) === syn);
                                    if (opt) break;
                                }
                                // Nếu chưa thấy, tìm option bắt đầu hoặc kết thúc bằng số tháng
                                if (!opt) {
                                    let regexMonth = new RegExp("^(tháng|thg|month)?\\\\s*0?" + search + "$", "i");
                                    opt = visibleOptions.find(o => regexMonth.test(normalizeText(o.innerText || o.textContent)));
                                }
                                // Dự phòng tuyệt đối: nếu menu đang mở có 12 tháng theo thứ tự 1..12 thì chọn thẳng theo index
                                if (!opt && visibleOptions.length === 12) {
                                    let mIdx = parseInt(search, 10) - 1;
                                    if (mIdx >= 0 && mIdx < 12) opt = visibleOptions[mIdx];
                                }
                            } else if (fieldType === 'gender') {
                                let genderSyns = ["nam", "male", "anh ấy", "he"];
                                opt = visibleOptions.find(o => {
                                    let t = normalizeText(o.innerText || o.textContent);
                                    return t === search || genderSyns.includes(t) || t.startsWith("nam ") || t.startsWith("male ");
                                });
                                if (!opt && visibleOptions.length >= 2) {
                                    opt = visibleOptions[1]; // Thường vị trí 0 là Nữ, 1 là Nam
                                }
                            } else {
                                opt = visibleOptions.find(o => {
                                    let t = normalizeText(o.innerText || o.textContent);
                                    return t === search || t === "0" + search;
                                });
                            }

                            if (opt) {
                                triggerMouseClick(opt);
                                await new Promise(r => setTimeout(r, 650));
                                return true;
                            } else {
                                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
                                document.body.click();
                                await new Promise(r => setTimeout(r, 400));
                                return false;
                            }
                        }

                        (async function() {
                            try {
                                let rDay = await selectComboboxByIndex(0, day, 'day');
                                let rMonth = await selectComboboxByIndex(1, month, 'month');
                                if (!rMonth) {
                                    await new Promise(r => setTimeout(r, 500));
                                    rMonth = await selectComboboxByIndex(1, month, 'month');
                                }
                                let rYear = await selectComboboxByIndex(2, year, 'year');
                                let rGender = await selectComboboxByIndex(3, gender, 'gender');
                                callback(`SUCCESS (Day:${rDay}, Month:${rMonth}, Year:${rYear}, Gender:${rGender})`);
                            } catch (e) {
                                callback("ERROR: " + e.toString());
                            }
                        })();
                        """
                        res = driver.execute_async_script(js_dropdowns, current_day, current_month, current_year, gender_text)
                        if "ERROR" in str(res):
                            print(f"{Colors.color_text(f'[{self.thread_id}] Cảnh báo JS Dropdown: {res}', Colors.WARNING)}")
                        else:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Kết quả chọn Dropdown: {res}', Colors.SUCCESS)}")
                    except Exception as e:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi chạy script Combobox: {e}', Colors.ERROR)}")

                    time.sleep(self.delay_config['delay_chon_gioi_tinh'])

                    ngam_form = self.delay_config['delay_ngam_form_truoc_submit']
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã điền xong. Ngâm form {ngam_form}s trước khi bấm nút Đăng Ký...', Colors.WARNING)}")
                    time.sleep(ngam_form)

                except Exception as e:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi quá trình điền form: {e}', Colors.ERROR)}")
                    time.sleep(5)
                    return False

                uid_moc = 0
                if self.mode in ["3", "4"] and imap_service:
                    uid_moc = imap_service.get_latest_uid()
                elif self.mode == "5" and hotmail_service:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Khởi tạo mốc hộp thư để tránh đọc thư cũ...', Colors.INFO)}")
                    hotmail_service.init_baseline()

                print(f"{Colors.color_text(f'[{self.thread_id}] Cuộn trang xuống cuối để tìm nút Gửi...', Colors.INFO)}")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                print(f"{Colors.color_text(f'[{self.thread_id}] Click ra ngoài form để kích hoạt Validate...', Colors.INFO)}")
                driver.execute_script("document.body.click();")
                
                val_wait = self.delay_config['delay_validate_form']
                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ form validate... ({val_wait}s)', Colors.WARNING)}")
                time.sleep(val_wait)
                
                with SUBMIT_LOCK:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang tìm và nhấn nút Gửi/Đăng Ký (Sign up)...', Colors.INFO)}")
                    try:
                        click_result = driver.execute_script("""
                            let submitBtn = document.querySelector('button[name="websubmit"], button[type="submit"]');

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
                                btn_selenium = driver.find_element(By.CSS_SELECTOR, "button[name='websubmit'], button[type='submit']")
                                driver.execute_script("arguments[0].click();", btn_selenium)
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã click nút Submit qua Selenium thành công!', Colors.SUCCESS)}")
                            except:
                                print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm thấy nút qua Selenium, fallback phím ENTER...', Colors.WARNING)}")
                                try:
                                    pass_el.send_keys(Keys.ENTER)
                                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm ENTER thành công!', Colors.SUCCESS)}")
                                except: pass

                    except Exception as ex:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi khi chạy Script click nút: {ex}', Colors.WARNING)}")
                    
                    sau_sub = self.delay_config['delay_sau_khi_submit']
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm gửi form, chờ load OTP ({sau_sub}s)...', Colors.SUCCESS)}")
                    time.sleep(sau_sub) 
                
            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi quá trình khởi tạo form: {e}', Colors.ERROR)}")
                time.sleep(5)
                return False

            # ==================== XỬ LÝ MỒI SĐT ĐỔI SANG EMAIL (GIAO DIỆN MỚI) ====================
            if use_phone_bait:
                print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu luồng Mồi SĐT: Đổi từ ({contact_for_signup}) sang Email ({used_email})...', Colors.INFO)}")
                try:
                    # Đánh dấu ô nhập OTP của SĐT cũ để tuyệt đối không nhập nhầm Email vào ô Mã xác nhận
                    driver.execute_script("""
                        document.querySelectorAll('input').forEach(inp => {
                            if (inp.offsetWidth > 0 && inp.offsetHeight > 0) {
                                inp.setAttribute('data-old-otp-input', 'true');
                            }
                        });
                    """)

                    # Bước 1: Bấm vào nút "Tôi không nhận được mã" (I didn't receive the code)
                    clicked_didnt_get_code = False
                    for _ in range(6):
                        clicked_didnt_get_code = driver.execute_script("""
                            function fireClick(el) {
                                el.scrollIntoView({block: 'center'});
                                const r = el.getBoundingClientRect();
                                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
                                    el.dispatchEvent(new MouseEvent(t, {view: window, bubbles: true, cancelable: true, clientX: r.left + r.width/2, clientY: r.top + r.height/2}));
                                });
                                try { el.click(); } catch(e) {}
                            }
                            let els = Array.from(document.querySelectorAll('div[role="button"], button, a, span'));
                            for (let el of els) {
                                let rect = el.getBoundingClientRect();
                                if (rect.width === 0 || rect.height === 0) continue;
                                let txt = (el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim().toLowerCase();
                                if (
                                    txt === 'tôi không nhận được mã' ||
                                    txt === 'tôi chưa nhận được mã' ||
                                    txt.includes('không nhận được mã') ||
                                    txt.includes('chưa nhận được mã') ||
                                    txt.includes("didn't receive") ||
                                    txt.includes("did not receive") ||
                                    txt.includes("didn't get a code")
                                ) {
                                    let btn = el.closest('div[role="button"], button, a') || el;
                                    fireClick(btn);
                                    return true;
                                }
                            }
                            return false;
                        """)
                        if clicked_didnt_get_code:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm nút \"Tôi không nhận được mã\"!', Colors.SUCCESS)}")
                            break
                        time.sleep(2)

                    time.sleep(3)

                    # Bước 2: Bấm vào "Thay đổi số di động hoặc email" trong bảng Popup
                    clicked_change_contact = False
                    for _ in range(6):
                        clicked_change_contact = driver.execute_script("""
                            function fireClick(el) {
                                el.scrollIntoView({block: 'center'});
                                const r = el.getBoundingClientRect();
                                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
                                    el.dispatchEvent(new MouseEvent(t, {view: window, bubbles: true, cancelable: true, clientX: r.left + r.width/2, clientY: r.top + r.height/2}));
                                });
                                try { el.click(); } catch(e) {}
                            }
                            let els = Array.from(document.querySelectorAll('div[role="button"], div[role="menuitem"], a, button, span'));
                            for (let el of els) {
                                let rect = el.getBoundingClientRect();
                                if (rect.width === 0 || rect.height === 0) continue;
                                let txt = (el.innerText || el.textContent || "").replace(/\\s+/g, " ").trim().toLowerCase();
                                if (
                                    txt === 'thay đổi số di động hoặc email' ||
                                    txt === 'thay đổi số điện thoại hoặc email' ||
                                    txt.includes('thay đổi số di động') ||
                                    txt.includes('thay đổi số điện thoại') ||
                                    txt.includes('cập nhật thông tin liên hệ') ||
                                    txt.includes('xác nhận bằng email') ||
                                    txt.includes('change mobile number or email') ||
                                    txt.includes('change phone number or email') ||
                                    txt.includes('update contact info') ||
                                    txt.includes('confirm by email')
                                ) {
                                    let btn = el.closest('div[role="button"], div[role="menuitem"], a, button') || el;
                                    fireClick(btn);
                                    return true;
                                }
                            }
                            return false;
                        """)
                        if clicked_change_contact:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm \"Thay đổi số di động hoặc email\"!', Colors.SUCCESS)}")
                            break
                        time.sleep(1.5)

                    time.sleep(3.5)

                    # Bước 3: Tìm ô nhập Email mới (tránh ô Mã xác nhận cũ) và điền Email
                    new_email_inp = None
                    for _ in range(6):
                        candidate_inputs = driver.execute_script("""
                            function isVis(el) {
                                if (!el) return false;
                                const r = el.getBoundingClientRect();
                                const s = window.getComputedStyle(el);
                                return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                            }
                            // 1. Ưu tiên tìm input nằm trong hộp thoại Dialog đang mở
                            let dialogs = Array.from(document.querySelectorAll('div[role="dialog"]')).filter(isVis);
                            if (dialogs.length > 0) {
                                let dlgInputs = Array.from(dialogs[dialogs.length - 1].querySelectorAll('input:not([type="hidden"])')).filter(isVis);
                                if (dlgInputs.length > 0) return dlgInputs;
                            }
                            // 2. Tìm các input mới xuất hiện (không phải ô mã xác nhận cũ)
                            let allInputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])')).filter(isVis);
                            let freshInputs = allInputs.filter(inp => inp.getAttribute('data-old-otp-input') !== 'true');
                            if (freshInputs.length > 0) return freshInputs;
                            return [];
                        """)
                        if candidate_inputs and len(candidate_inputs) > 0:
                            new_email_inp = candidate_inputs[-1]
                            break
                        time.sleep(1.5)

                    if new_email_inp:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang nhập Email mới ({used_email}) vào ô thay đổi liên hệ...', Colors.INFO)}")
                        try:
                            human_type(new_email_inp, used_email)
                        except Exception:
                            pass

                        # Kiểm tra và ép gán giá trị bằng JS nếu Selenium gõ thiếu
                        driver.execute_script("""
                            let inp = arguments[0];
                            let val = arguments[1];
                            if ((inp.value || "").trim() !== val) {
                                let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                setter.call(inp, val);
                                inp.dispatchEvent(new Event('input', { bubbles: true }));
                                inp.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, new_email_inp, used_email)
                        time.sleep(1.5)

                        # Cập nhật mốc đọc thư ngay trước khi bấm Gửi email mới
                        if self.mode in ["3", "4"] and imap_service:
                            uid_moc = imap_service.get_latest_uid()
                        elif self.mode == "5" and hotmail_service:
                            hotmail_service.init_baseline()

                        # Bước 4: Bấm nút Tiếp tục / Thêm / Cập nhật để gửi mã về Email
                        clicked_submit_new_email = driver.execute_script("""
                            function isVis(el) {
                                if (!el) return false;
                                const r = el.getBoundingClientRect();
                                const s = window.getComputedStyle(el);
                                return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                            }
                            function fireClick(el) {
                                el.scrollIntoView({block: 'center'});
                                const r = el.getBoundingClientRect();
                                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
                                    el.dispatchEvent(new MouseEvent(t, {view: window, bubbles: true, cancelable: true, clientX: r.left + r.width/2, clientY: r.top + r.height/2}));
                                });
                                try { el.click(); } catch(e) {}
                            }
                            let targetKeywords = ['tiếp tục', 'thêm', 'cập nhật', 'gửi', 'xác nhận', 'lưu', 'tiếp', 'continue', 'add', 'update', 'submit', 'next', 'save'];
                            
                            // Ưu tiên tìm nút bên trong Dialog trên cùng trước
                            let dialogs = Array.from(document.querySelectorAll('div[role="dialog"]')).filter(isVis);
                            let searchScopes = dialogs.length > 0 ? [dialogs[dialogs.length - 1], document.body] : [document.body];

                            for (let scope of searchScopes) {
                                let btns = Array.from(scope.querySelectorAll('div[role="button"], button, input[type="submit"]')).filter(isVis);
                                btns.reverse(); // Duyệt từ dưới lên để ưu tiên nút trên Modal mới nhất
                                for (let b of btns) {
                                    let txt = (b.innerText || b.value || b.textContent || "").replace(/\\s+/g, " ").trim().toLowerCase();
                                    if (targetKeywords.includes(txt) || b.name === 'change') {
                                        if (!b.disabled && b.getAttribute('aria-disabled') !== 'true') {
                                            fireClick(b);
                                            return txt;
                                        }
                                    }
                                }
                            }
                            return null;
                        """)

                        if clicked_submit_new_email:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã bấm nút gửi Email mới ({clicked_submit_new_email})! Chờ Facebook gửi OTP về Mail...', Colors.SUCCESS)}")
                        else:
                            try:
                                new_email_inp.send_keys(Keys.ENTER)
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã nhấn ENTER để gửi Email mới!', Colors.SUCCESS)}")
                            except Exception:
                                pass
                        time.sleep(6)
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Cảnh báo: Không tìm thấy ô nhập Email mới sau khi mở popup!', Colors.WARNING)}")
                except Exception as e:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Cảnh báo khi đổi SĐT sang Email: {e}', Colors.WARNING)}")

            print(f"{Colors.color_text(f'[{self.thread_id}] Chờ giao diện nhập OTP...', Colors.INFO)}")
            otp_input = None
            locators = [
                (By.NAME, "code"), (By.ID, "code_in_cliff"), (By.NAME, "email_confirmation_code"), (By.NAME, "confirmationCode"),
                (By.XPATH, "//input[contains(@name, 'code')]"), (By.XPATH, "//input[contains(@aria-label, 'FB-')]"),
                (By.XPATH, "//input[contains(@aria-label, 'Mã')]"), (By.XPATH, "//input[contains(@aria-label, 'Code')]"),
                (By.XPATH, "//input[@type='text' or @type='number' or @type='tel']")
            ]
            time.sleep(3)
            
            for loc in locators:
                try:
                    els = driver.find_elements(*loc)
                    for el in els:
                        if el.is_displayed():
                            otp_input = el
                            break
                    if otp_input: break
                except: pass
            
            if not otp_input:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    otp_input = driver.execute_script("return document.querySelector('input[type=\"text\"], input[name*=\"code\"], input');")
                except: pass

            if not otp_input:
                print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không thể tìm thấy ô nhập OTP trên giao diện.', Colors.ERROR)}")
                time.sleep(5)
                return False
            
            print(f"{Colors.color_text(f'[{self.thread_id}] Đã nhận diện được ô nhập OTP thành công!', Colors.SUCCESS)}")
            
            otp_code = None
            max_resend_attempts = int(self.delay_config.get('so_lan_thu_get_code', 2))
            
            for attempt in range(max_resend_attempts + 1):
                if STOP_EVENT.is_set(): return False
                
                start_otp_wait = time.time()
                
                if self.mode == "2" and not (mail_service and mail_service.token):
                    with OTP_LOCK:
                        PAUSE_FOR_INPUT.clear()
                        built_in_print(f"\n{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: MỜI SẾP NHẬP OTP CHO [{used_email}] TỪ BÀN PHÍM: ', Colors.SUCCESS)}", end="")
                        otp_code = input().strip()
                        PAUSE_FOR_INPUT.set()
                else:
                    target_wait = self.delay_config['delay_ngam_otp'] if self.mode in ["3", "4", "5", "6"] else 0
                    if target_wait > 0: print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Bắt đầu quét OTP và ngâm form {target_wait}s...', Colors.INFO)}")
                    else: print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Đang chờ lấy mã OTP...', Colors.INFO)}")

                    timeout_per_attempt = 100 
                    if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                        otp_code = mail_service.get_otp_code(timeout=timeout_per_attempt, force_8_digits=False)
                    elif self.mode in ["3", "4"]:
                        otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=timeout_per_attempt, force_8_digits=False)
                    elif self.mode == "5":
                        otp_code = hotmail_service.get_otp_code(timeout=100, force_8_digits=False) 
                    elif self.mode == "6" and autosms_service:
                        otp_code = autosms_service.get_otp_code(timeout=120)
                
                if otp_code:
                    if self.mode in ["3", "4", "5", "6"]:
                        elapsed = time.time() - start_otp_wait
                        remaining = target_wait - elapsed
                        if remaining > 0:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã lấy được mã ({otp_code}) ở giây thứ {int(elapsed)}! Đang ngâm form đợi hết {target_wait}s...', Colors.WARNING)}")
                            for w in range(int(remaining), 0, -5):
                                if STOP_EVENT.is_set(): return False
                                print(f"{Colors.color_text(f'[{self.thread_id}] Thời gian ngâm OTP còn lại: {w}s...', Colors.INFO)}")
                                time.sleep(min(5, w))
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã ngâm đủ {target_wait}s. Chuẩn bị điền mã OTP!', Colors.SUCCESS)}")
                    break 
                
                if attempt < max_resend_attempts:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1} không thấy mã. Tiến hành click yêu cầu Gửi lại mã...', Colors.WARNING)}")
                    
                    clicked_didnt_receive = driver.execute_script("""
                        let btns = Array.from(document.querySelectorAll('a, button, div[role="button"], span'));
                        for (let b of btns) {
                            let r = b.getBoundingClientRect();
                            if (r.width === 0 || r.height === 0) continue;
                            let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                            if (txt.includes('không nhận được mã') || txt.includes('chưa nhận được mã') || txt.includes("didn't receive") || txt.includes("did not receive") || txt.includes('gửi lại email') || txt.includes('send email again')) {
                                let clickable = b.closest('a, button, [role="button"]') || b;
                                clickable.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    if clicked_didnt_receive:
                        time.sleep(3) 
                        clicked_resend = driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"], div[role="menuitem"], a, span'));
                            for (let b of btns) {
                                let r = b.getBoundingClientRect();
                                if (r.width === 0 || r.height === 0) continue;
                                let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if (txt.includes('gửi lại') || txt.includes('resend') || txt.includes('send email again')) {
                                    let clickable = b.closest('button, [role="button"], [role="menuitem"], a') || b;
                                    clickable.click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        if clicked_resend:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã yêu cầu GỬI LẠI MÃ thành công. Chờ thư/sim mới...', Colors.INFO)}")
                            time.sleep(5)
                        else:
                            print(f"{Colors.color_text(f'[{self.thread_id}] Đã kích hoạt gửi lại mã trực tiếp. Chờ thư/sim mới...', Colors.INFO)}")
                            time.sleep(5)
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không tìm thấy nút Tôi không nhận được mã / Gửi lại email!', Colors.ERROR)}")

            if not otp_code:
                print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Đã thử Gửi lại {max_resend_attempts} lần nhưng vẫn KHÔNG CÓ MÃ. Báo Mail/Sim Die và bỏ qua acc!', Colors.ERROR)}")
                if self.mode == "6" and autosms_service:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang hoàn tiền đơn thuê sim...', Colors.INFO)}")
                    autosms_service.cancel_order()
                time.sleep(5)
                return False

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
                    let input = document.querySelector('input[name*="code"], input#code_in_cliff, input[type="text"]');
                    if(input) {
                        let value = arguments[0];
                        let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(input, value);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                """, otp_code)
                
            time.sleep(1.5)
            
            print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành Gửi mã OTP...', Colors.INFO)}")
            time.sleep(2)

            click_success = False

            try:
                print(f"{Colors.color_text(f'[{self.thread_id}] Thử click nút Tiếp tục/Xác nhận bằng vòng lặp JavaScript...', Colors.INFO)}")
                click_result = driver.execute_script("""
                    const btns = Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]'));
                    for (let b of btns) {
                        const text = (b.innerText || b.value || b.textContent || "").trim().toLowerCase();
                        if (b.name === "confirm" || text === "tiếp tục" || text === "next" || text === "confirm" || text === "continue" || text === "xác nhận" || b.type === "submit") {
                            b.disabled = false;
                            b.removeAttribute('disabled');
                            b.click();
                            return "CLICKED";
                        }
                    }
                    return "NOT_FOUND";
                """)
                if click_result == "CLICKED":
                    click_success = True
            except: pass

            if not click_success:
                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Thử click nút Tiếp tục bằng Selenium...', Colors.INFO)}")
                    btn_xpath = "//button[@name='confirm' or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tiếp tục') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue') or @type='submit']"
                    submit_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", submit_btn)
                    click_success = True
                except Exception: pass

            if not click_success:
                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Thử submit bằng phím ENTER...', Colors.INFO)}")
                    target_input.send_keys(Keys.ENTER)
                    click_success = True
                    time.sleep(1)
                except Exception: pass

            if click_success:
                print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM GỬI OTP THÀNH CÔNG!', Colors.SUCCESS)}")
            else:
                print(f"{Colors.color_text(f'[{self.thread_id}] KHÔNG THỂ BẤM NÚT, trình duyệt có thể bị treo.', Colors.ERROR)}")

            # CHỜ TẢI TRANG CHỦ & KIỂM TRA ACC DIE
            load_tc_wait = self.delay_config['delay_cho_load_trang_chu']
            print(f"{Colors.color_text(f'[{self.thread_id}] Chờ FB xử lý OTP và load trang chủ ({load_tc_wait}s)...', Colors.INFO)}")
            time.sleep(load_tc_wait)

            try:
                driver.execute_script("""
                    let btns = Array.from(document.querySelectorAll('button, div[role="button"], a'));
                    for (let b of btns) {
                        let txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                        if (txt === "ok" || txt === "tiếp tục" || txt === "continue") {
                            try { b.click(); } catch(e) {}
                        }
                    }
                """)
                time.sleep(5)
            except: pass
            
            print(f"{Colors.color_text(f'[{self.thread_id}] Đang kiểm tra xem acc có bị Checkpoint/Die không...', Colors.INFO)}")
            cookies_list = driver.get_cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies_list}
            fb_uid = cookie_dict.get('c_user', '')
            
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()
            
            is_dead = False
            if "checkpoint" in current_url or "challenge" in current_url or "suspended" in current_url:
                is_dead = True
            elif "tài khoản của bạn đã bị tạm ngưng" in page_source or "đình chỉ tài khoản" in page_source or "we suspended your account" in page_source:
                is_dead = True
            elif not fb_uid or not cookie_dict.get('xs'):
                is_dead = True
                
            if is_dead:
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{self.thread_id}] LỖI: TÀI KHOẢN ĐÃ DIE / CHECKPOINT!', Colors.ERROR)}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                return "DEAD" 

            print(f"{Colors.color_text(f'[{self.thread_id}] TÀI KHOẢN SỐNG (UID: {fb_uid})! Chuẩn bị up Avatar...', Colors.SUCCESS)}")

            if self.avatar_folder and os.path.exists(self.avatar_folder):
                images = [f for f in os.listdir(self.avatar_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                if images:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Bắt đầu quy trình up Avatar từ URL trang cá nhân...', Colors.INFO)}")
                    try:
                        image_path = os.path.abspath(os.path.join(self.avatar_folder, random.choice(images)))
                        driver.get("https://www.facebook.com/profile.php")
                        time.sleep(8)
                        
                        if "checkpoint" in driver.current_url.lower() or "suspended" in driver.current_url.lower():
                            print(f"{Colors.color_text(f'[{self.thread_id}] Acc vừa die (Checkpoint) khi truy cập profile! Bỏ qua up avatar.', Colors.ERROR)}")
                        else:
                            driver.execute_script("""
                                if (!window.hookedFileClick) {
                                    window.originalClick = window.HTMLInputElement.prototype.click;
                                    window.HTMLInputElement.prototype.click = function() {
                                        if (this.type === 'file') {
                                            this.style.display = 'block';
                                            this.style.opacity = '1';
                                            this.style.visibility = 'visible';
                                            this.style.position = 'fixed';
                                            this.style.top = '0';
                                            this.style.left = '0';
                                            this.style.zIndex = '99999';
                                        } else {
                                            window.originalClick.call(this);
                                        }
                                    };
                                    window.hookedFileClick = true;
                                }

                                let avatarBtn = document.querySelector('[aria-label*="ảnh đại diện"], [aria-label*="profile picture"], [aria-label*="Update profile picture"], svg[aria-label*="ảnh đại diện"]');
                                if (avatarBtn) {
                                    let clickable = avatarBtn.closest('div[role="button"], button, a') || avatarBtn;
                                    clickable.click();
                                }
                            """)
                            time.sleep(3)
                            
                            file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                            if file_inputs:
                                file_inputs[-1].send_keys(image_path) 
                                print(f"{Colors.color_text(f'[{self.thread_id}] Đã chèn file ảnh avatar! Chờ 6s để bấm nút Lưu...', Colors.SUCCESS)}")
                                time.sleep(6)
                                driver.execute_script("""
                                    let saveBtns = Array.from(document.querySelectorAll('div[aria-label="Lưu"], div[aria-label="Save"], div[role="button"], button, span'));
                                    for (let el of saveBtns) {
                                        let txt = (el.innerText || el.textContent || "").trim().toLowerCase();
                                        let aria = (el.getAttribute("aria-label") || "").toLowerCase();
                                        if (txt === "lưu" || txt === "save" || aria === "lưu" || aria === "save") {
                                            let btn = el.closest('div[role="button"], button') || el;
                                            btn.click();
                                            break;
                                        }
                                    }
                                """)
                                time.sleep(10) 
                            else: print(f"{Colors.color_text(f'[{self.thread_id}] Không tìm thấy khung upload ảnh trên trang cá nhân.', Colors.WARNING)}")
                    except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi trong quá trình up avatar: {e}', Colors.WARNING)}")
                else: print(f"{Colors.color_text(f'[{self.thread_id}] Thư mục avatar trống, không có ảnh nào để up.', Colors.WARNING)}")
            else: print(f"{Colors.color_text(f'[{self.thread_id}] Không cấu hình Up Avatar, bỏ qua bước này.', Colors.INFO)}")

            print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành cài đặt 2FA (Hỗ trợ song ngữ Anh - Việt)...', Colors.INFO)}")
            two_fa_secret = ""
            try:
                driver.get("https://accountscenter.facebook.com/password_and_security/two_factor/")
                time.sleep(7)

                print(f"{Colors.color_text(f'[{self.thread_id}] Xử lý chọn tài khoản / màn hình đệm Meta...', Colors.INFO)}")
                for _ in range(4):
                    try:
                        clicked_buffer = driver.execute_script("""
                            let targetUser = arguments[0].toLowerCase();
                            let allElements = Array.from(document.querySelectorAll('*'));
                            for(let el of allElements) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if((txt.includes(targetUser) || txt.includes('facebook')) && txt.length < 60) {
                                    let clickable = el.closest('div[role="button"], a[role="link"], button');
                                    if(clickable) { clickable.click(); return 'CLICK_USER'; }
                                }
                            }
                            return 'NOT_FOUND';
                        """, first_name_fb)
                        if clicked_buffer != 'NOT_FOUND':
                            time.sleep(4)
                            break
                        time.sleep(2)
                    except Exception: pass

                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ và bấm nút Bắt đầu (Get started)...', Colors.INFO)}")
                for _ in range(6):
                    clicked_start = driver.execute_script("""
                        let allElements = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                        for(let el of allElements) {
                            let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                            if(txt === 'bắt đầu' || txt === 'get started') {
                                let btn = el.closest('button, [role="button"]') || el;
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    if clicked_start:
                        print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ BẤM NÚT Bắt đầu THÀNH CÔNG!', Colors.SUCCESS)}")
                        time.sleep(4)
                        break
                    time.sleep(1.5)

                is_email_check_screen = False
                for _ in range(6):
                    is_email_check_screen = driver.execute_script("""
                        let txt = (document.body.innerText || document.body.textContent || '').toLowerCase();
                        return txt.includes('kiểm tra email') || txt.includes('check your email') || txt.includes('mã bảo mật') || txt.includes('security code') || txt.includes('kiểm tra tin nhắn');
                    """)
                    if is_email_check_screen: break
                    time.sleep(1.5)

                if is_email_check_screen:
                    print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ HIỆN MÀN HÌNH Kiểm tra email của bạn. Bắt đầu quét MÃ 8 SỐ...', Colors.WARNING)}")
                    verify_code = None
                    if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                        verify_code = mail_service.get_otp_code(timeout=120, force_8_digits=True)
                    elif self.mode in ["3", "4"]:
                        verify_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=120, force_8_digits=True)
                    elif self.mode == "5":
                        verify_code = hotmail_service.get_otp_code(timeout=180, force_8_digits=True)
                    elif self.mode == "6" and autosms_service:
                        verify_code = autosms_service.get_otp_code(timeout=120)

                    if verify_code:
                        print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ LẤY ĐƯỢC MÃ 8 SỐ CHUẨN XÁC: {verify_code}. Tiến hành điền...', Colors.SUCCESS)}")
                        driver.execute_script("""
                            let val = arguments[0];
                            let inp = document.querySelector('input[type="text"], input[type="tel"], input:not([type="hidden"])');
                            if (inp) {
                                let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                nativeInputValueSetter.call(inp, val);
                                inp.dispatchEvent(new Event('input', { bubbles: true }));
                                inp.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, verify_code)
                        time.sleep(1.5)
                        
                        driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                            for(let b of btns){
                                let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                                if(['tiếp tục', 'next', 'continue', 'gửi', 'tiếp', 'xác nhận', 'submit'].includes(t)){
                                    if(!b.disabled) { b.click(); return; }
                                }
                            }
                        """)
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã gửi mã 8 số! Đang quay trở lại luồng thiết lập 2FA...', Colors.INFO)}")
                        time.sleep(8)

                        if "two_factor" not in driver.current_url.lower():
                            driver.get("https://accountscenter.facebook.com/password_and_security/two_factor/")
                            time.sleep(5)
                        driver.execute_script("""
                            let targetUser = arguments[0].toLowerCase();
                            let allElements = Array.from(document.querySelectorAll('*'));
                            for(let el of allElements) {
                                let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                                if((txt.includes(targetUser) || txt.includes('facebook')) && txt.length < 60) {
                                    let clickable = el.closest('div[role="button"], a[role="link"], button');
                                    if(clickable) { clickable.click(); break; }
                                }
                            }
                        """, first_name_fb)
                        time.sleep(4)
                
                try:
                    clicked_app = driver.execute_script("""
                        let all = Array.from(document.querySelectorAll('*'));
                        for(let el of all) {
                            let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                            if(txt.includes('authentication app') || txt.includes('ứng dụng xác thực') || txt.includes('duo mobile')) {
                                let clickable = el.closest('div[role="button"], label, div[tabindex], button, [role="radio"]') || el;
                                clickable.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    if clicked_app:
                        time.sleep(2)
                        driver.execute_script("""
                            let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                            for(let b of btns) {
                                let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                                if(['continue', 'next', 'tiếp tục', 'tiếp'].includes(txt)) {
                                    let clickable = b.closest('button, [role="button"]') || b;
                                    if(!clickable.disabled) { clickable.click(); return; }
                                }
                            }
                        """)
                        time.sleep(5)
                except: pass

                print(f"{Colors.color_text(f'[{self.thread_id}] Đang tìm và bóc tách Secret Key 2FA...', Colors.INFO)}")
                driver.execute_script("""
                    window.hooked2FAKey = "";
                    if (navigator.clipboard && !window.clipboardHooked) {
                        const originalWriteText = navigator.clipboard.writeText;
                        navigator.clipboard.writeText = function(text) {
                            let clean = (text || '').replace(/\\s+/g, '').toUpperCase();
                            if (clean.length >= 16 && /^[A-Z2-7]+$/.test(clean)) {
                                window.hooked2FAKey = clean;
                            }
                            return originalWriteText.apply(this, arguments);
                        };
                        window.clipboardHooked = true;
                    }
                """)

                for attempt_2fa in range(6):
                    if STOP_EVENT.is_set(): return False
                    driver.execute_script("""
                        let els = Array.from(document.querySelectorAll('span, div, button, a'));
                        for(let el of els) {
                            let txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                            if(txt === 'sao chép khóa' || txt === 'copy key' || txt.includes('sao chép') || txt.includes("can't scan") || txt.includes("không quét được")) {
                                try { el.click(); } catch(e) {}
                            }
                        }
                    """)
                    time.sleep(2)

                    key_from_clipboard = driver.execute_script("return window.hooked2FAKey;")
                    if key_from_clipboard and len(key_from_clipboard) >= 16:
                        two_fa_secret = key_from_clipboard
                        break

                    extracted_key = driver.execute_script("""
                        let text = document.body.innerText || "";
                        let match = text.match(/\\b([A-Z2-7]{4}[\\s-]*){8}\\b/i);
                        if (match) {
                            return match[0].replace(/[^A-Z2-7]/gi, '').toUpperCase();
                        }
                        return null;
                    """)
                    if extracted_key and len(extracted_key) >= 16:
                        two_fa_secret = extracted_key
                        break
                    time.sleep(2)

                if two_fa_secret:
                    print(f"{Colors.color_text(f'[{self.thread_id}] ĐÃ LẤY CHUẨN XÁC SECRET KEY 2FA: {two_fa_secret}', Colors.SUCCESS)}")
                    driver.execute_script("""
                        let btns = Array.from(document.querySelectorAll('button, div[role="button"], span'));
                        for(let b of btns) {
                            let txt = (b.innerText || b.textContent || '').trim().toLowerCase();
                            if(['nhập mã', 'enter code', 'next', 'continue', 'tiếp tục', 'tiếp'].includes(txt)) {
                                let clickable = b.closest('button, [role="button"]') || b;
                                let rect = clickable.getBoundingClientRect();
                                if(rect.width > 0 && rect.height > 0 && !clickable.disabled) {
                                    clickable.click();
                                    return;
                                }
                            }
                        }
                    """)
                    time.sleep(4)

                    totp = pyotp.TOTP(two_fa_secret)
                    current_otp = totp.now()
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đã sinh mã OTP 6 số ({current_otp}). Đang điền...', Colors.INFO)}")

                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.is_displayed() and inp.get_attribute("type") != "file":
                            try: inp.clear()
                            except: pass
                            for digit in current_otp:
                                inp.send_keys(digit)
                                time.sleep(0.08)
                            time.sleep(1)
                            try: inp.send_keys(Keys.ENTER)
                            except: pass
                            driver.execute_script("document.body.click();")
                            break
                    time.sleep(3)

                    driver.execute_script("""
                        let btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                        btns.reverse();
                        for(let b of btns){
                            let t = (b.innerText || b.textContent || "").trim().toLowerCase();
                            if(['xong', 'done', 'tiếp', 'tiếp tục', 'next', 'continue', 'submit', 'xác nhận'].includes(t)){
                                let rect = b.getBoundingClientRect();
                                if(rect.width > 0 && rect.height > 0 && !b.disabled && b.getAttribute('aria-disabled') !== 'true') {
                                    b.click();
                                    return;
                                }
                            }
                        }
                    """)
                    time.sleep(5)
                    print(f"{Colors.color_text(f'[{self.thread_id}] BẬT 2FA THÀNH CÔNG RỰC RỠ!', Colors.SUCCESS)}")
                else: print(f"{Colors.color_text(f'[{self.thread_id}] Không nhận diện được Secret Key 2FA trên giao diện.', Colors.WARNING)}")
            except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] Quá trình 2FA gặp lỗi: {e}', Colors.WARNING)}")

            print(f"{Colors.color_text(f'[{self.thread_id}] Đang tiến hành lấy Cookie lưu tài khoản...', Colors.INFO)}")
            cookies_list = driver.get_cookies()
            cookie_dict = {c['name']: c['value'] for c in cookies_list}
            fb_uid = cookie_dict.get('c_user', fb_uid)
            
            cookie_str = (
                f"datr={cookie_dict.get('datr', '')}; "
                f"sb={cookie_dict.get('sb', '')}; "
                f"c_user={fb_uid}; "
                f"xs={cookie_dict.get('xs', '')}; "
                f"fr={cookie_dict.get('fr', '')}; "
                f"wd={cookie_dict.get('wd', '1920x1080')}"
            )

            access_token = ""
            if self.delay_config.get('lay_token_android', True):
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang gọi Graph API lấy Access Token Android (EAAAAU...)...', Colors.INFO)}")
                try:
                    fb_api = Facebook(email=fb_uid or used_email, mat_khau=secure_pass, auth=two_fa_secret, proxy=req_proxy)
                    ket_qua_token = fb_api.DangNhap(APP_TOKEN)
                    if ket_qua_token.get('status') == 200:
                        access_token = ket_qua_token['data'].get('token', '')
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đã lấy Access Token Android thành công!', Colors.SUCCESS)}")
                    else:
                        msg_err = ket_qua_token.get('msg')
                        print(f"{Colors.color_text(f'[{self.thread_id}] Không lấy được Token Android: {msg_err}', Colors.WARNING)}")
                except Exception as ex_tk:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi lấy Token Android: {ex_tk}', Colors.WARNING)}")
            
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
            print(f"{Colors.KEY}UID:       {Colors.USERNAME}{fb_uid}{Colors.RESET}")
            print(f"{Colors.KEY}Email/SĐT: {Colors.EMAIL}{used_email}{Colors.RESET}")
            print(f"{Colors.KEY}Pass:      {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
            print(f"{Colors.KEY}2FA:       {Colors.WARNING}{two_fa_secret if two_fa_secret else 'Lỗi không có'}{Colors.RESET}")
            print(f"{Colors.KEY}Token:     {Colors.INFO}{access_token[:35] + '...' if access_token else 'Trống'}{Colors.RESET}")
            print(f"{Colors.KEY}Cookie:    {Colors.VALUE}{cookie_str if cookie_str else 'Trống'}{Colors.RESET}")
            print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
            
            save_account(self.thread_id, used_email, secure_pass, fb_uid, full_name, f"mode_{self.mode}", cookie_str, two_fa_secret, access_token)
            return True
            
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set(): break
            try:
                status = create_one_account(i)
            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ Toàn Cục: {e}', Colors.ERROR)}")
                status = False

            if status == True: success_count += 1
            elif status == "DEAD":
                print(f"{Colors.color_text(f'[{self.thread_id}] Dừng luồng này vì acc đã Die, bảo toàn các tài nguyên còn lại!', Colors.WARNING)}")
                break 
            else:
                print(f"{Colors.color_text(f'[{self.thread_id}] Dừng luồng do lỗi quá trình tạo, bảo toàn tài nguyên!', Colors.WARNING)}")
                break 
            time.sleep(self.delay_config.get('delay_giua_cac_lan_chay', 6.0))
        print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT TAB: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

def select_mode():
    while True:
        built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}6. {Colors.VALUE}THUÊ SỐ ĐIỆN THOẠI  \033[97m[ Dùng API AutoSMS.site ]{Colors.RESET}")
        built_in_print(f"{Colors.NUMBER}7. {Colors.TITLE}CẤU HÌNH DELAY & TÙY CHỌN (Mật khẩu, Mồi SĐT +84, Token EAAAAU){Colors.RESET}")
        choice = input(f"{Colors.KEY}Nhập lựa chọn [1-7]: {Colors.RESET}").strip()
        if choice in ["1", "2", "3", "4", "5", "6"]: return choice
        elif choice == "7": cau_hinh_delay(); banner()

def process_file_input(config_key, default_prompt):
    config_data, file_path = load_config(), ""
    if config_data.get(config_key) and os.path.isfile(config_data.get(config_key)):
        built_in_print(f"{Colors.INFO}Phát hiện tệp danh sách cũ: {Colors.VALUE}{config_data.get(config_key)}{Colors.RESET}")
        if input(f"{Colors.KEY}Bạn có muốn sử dụng lại tệp này không? (y/n): {Colors.RESET}").strip().lower() == 'y': file_path = config_data.get(config_key)
    if not file_path:
        file_path = input(default_prompt).strip().strip('"')
        if os.path.isfile(file_path): config_data[config_key] = file_path; save_config(config_data)
    if os.path.isfile(file_path):
        lines = [line.strip() for line in open(file_path, 'r', encoding='utf-8') if line.strip()]
        if config_key == 'last_file_mode2' and any(':' in l and '@' not in l for l in lines):
            built_in_print(f"{Colors.ERROR}LỖI: Tệp này chứa Proxy, KHÔNG PHẢI danh sách Email!{Colors.RESET}")
            config_data.pop(config_key, None); save_config(config_data); return []
        if not lines: built_in_print(f"{Colors.ERROR}File trống!{Colors.RESET}"); return []
        built_in_print(f"{Colors.SUCCESS}Đã tải {len(lines)} dòng từ tệp.{Colors.RESET}")
        s = input(f"{Colors.KEY}Bạn muốn chạy TỪ dòng số mấy? (Nhấn Enter để chạy từ đầu [1]): {Colors.RESET}").strip()
        e = input(f"{Colors.KEY}Bạn muốn chạy ĐẾN dòng số mấy? (Nhấn Enter để chạy đến cuối [{len(lines)}]): {Colors.RESET}").strip()
        si, ei = max(1, int(s) if s.isdigit() else 1), min(len(lines), int(e) if e.isdigit() else len(lines))
        if si > ei: return lines
        else: built_in_print(f"{Colors.INFO}=> Đã chọn {ei-si+1} data (Từ số {si} đến {ei}){Colors.RESET}"); return lines[si-1:ei]
    else: return [e.strip() for e in file_path.split(",") if e.strip()]

if __name__ == "__main__":
    banner()
    config_data, delay_config, mode = load_config(), doc_delay_config(), select_mode()
    data_source, base_gmail, app_password, manual_password, api_mode, autosms_api_key, autosms_country = [], None, None, None, None, None, "vn"
    if mode == "1": pass 
    elif mode == "2":
        data_source = process_file_input("last_file_mode2", f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}")
        if any("mail.tm" in e.lower() for e in data_source): manual_password = input(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}").strip()
    elif mode == "3":
        raw_list = process_file_input("last_file_mode3", f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}")
        for line in raw_list:
            parts = re.split(r'[|:]', line.strip())
            if len(parts) >= 2: data_source.append((parts[0].strip(), parts[1].strip()))
        if not data_source: sys.exit()
    elif mode == "4":
        base_gmail = input(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}").strip()
        app_password = input(f"{Colors.KEY}Nhập App Password: {Colors.RESET}").strip()
        data_source = generate_dot_variants(base_gmail)
    elif mode == "5":
        chon_api = input("1. OAuth | 2. Graph API | 3. Roundcube\n>> ").strip()
        api_mode = "oauth" if chon_api == "1" else "graph" if chon_api == "2" else "roundcube"
        data_source = process_file_input("last_file_mode5", f"{Colors.KEY}Nhập đường dẫn file/list Hotmail: {Colors.RESET}")
    elif mode == "6":
        autosms_api_key = input(f"{Colors.KEY}Nhập API Key của web Autosms.site: {Colors.RESET}").strip()
        autosms_country = input(f"{Colors.KEY}Nhập Mã Quốc Gia thuê sim (VD: vn, us, kh - Bỏ trống mặc định là vn): {Colors.RESET}").strip() or "vn"
        data_source = ["dummy_for_sms"] * 999999
    if not data_source and mode not in ["1", "4", "6"]: sys.exit()
    
    avatar_folder_input = config_data.get("last_avatar_folder", "")
    if avatar_folder_input and os.path.isdir(avatar_folder_input):
        built_in_print(f"\n{Colors.INFO}Phát hiện thư mục Avatar cũ: {Colors.VALUE}{avatar_folder_input}{Colors.RESET}")
        if input(f"{Colors.KEY}Bạn có muốn dùng lại thư mục này không? (y/n): {Colors.RESET}").strip().lower() != 'y': avatar_folder_input = ""
    if not avatar_folder_input:
        avatar_folder_input = input(f"\n{Colors.KEY}Nhập đường dẫn thư mục chứa ảnh làm Avatar (Bỏ trống nếu không muốn up): {Colors.RESET}").strip().strip('"').strip("'")
        if avatar_folder_input and os.path.isdir(avatar_folder_input): config_data["last_avatar_folder"] = avatar_folder_input; save_config(config_data)

    proxies_list = []
    proxy_file_input = input(f"\n{Colors.KEY}Nhập đường dẫn file Proxy (.txt) (Hỗ trợ định dạng: IP:Port, IP:Port:User:Pass, User:Pass@IP:Port): {Colors.RESET}").strip().strip('"').strip("'")
    if proxy_file_input and os.path.isfile(proxy_file_input):
        with open(proxy_file_input, 'r', encoding='utf-8') as f_proxy: proxies_list = [line.strip() for line in f_proxy if line.strip()]

    threads_count = int(input(f"\n{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc): {Colors.RESET}").strip())
    accs_per_thread = int(input(f"{Colors.KEY}Nhập số tài khoản cần tạo MỖI LUỒNG: {Colors.RESET}").strip())
    
    threads = [starts(i+1, mode, accs_per_thread, data_source, delay_config, manual_password, base_gmail, app_password, api_mode, avatar_folder_input, proxies_list, autosms_api_key, autosms_country) for i in range(threads_count)]
    for t in threads: t.start()
    
    try:
        for t in threads: t.join()
        built_in_print(f"\n{Colors.LINE}={'='*68}{Colors.RESET}\n{Colors.color_text('AUTO ĐÃ HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!', Colors.SUCCESS)}\n{Colors.TITLE}TIẾN HÀNH RÀ SOÁT VÀ ĐÓNG TRÌNH DUYỆT CỦA TỪNG TAB:{Colors.RESET}")
        for tid, drv in ALL_DRIVERS:
            try:
                drv.title
                while True:
                    choice = input(f"{Colors.WARNING}[{tid}] Bạn có muốn đóng Chrome của luồng này không? (y/n): {Colors.RESET}").strip().lower()
                    if choice == 'y':
                        try: drv.quit()
                        except: pass
                        break
                    elif choice == 'n': break
            except: pass
        input(f"\n{Colors.SUCCESS}TOOL ĐÃ KẾT THÚC CÔNG VIỆC!{Colors.RESET}\n{Colors.KEY}Nhấn Enter để thoát chương trình...{Colors.RESET}")
    except KeyboardInterrupt:
        STOP_EVENT.set(); sys.exit(0)
