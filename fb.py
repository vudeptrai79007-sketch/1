# --- SHIM CHO PYTHON 3.12+ ---
import sys, socket, select, base64, io, types, re, os, time, threading, random, string, hashlib, struct, json, traceback, uuid, imaplib, email
from datetime import datetime
from email.header import decode_header
if sys.platform.startswith('win'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace'); sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except: pass
if 'distutils' not in sys.modules:
    distutils_mod = types.ModuleType('distutils'); distutils_version_mod = types.ModuleType('distutils.version')
    class LooseVersion:
        def __init__(self, vstring=None):
            if vstring: self.parse(vstring)
        def parse(self, vstring):
            self.vstring = vstring
            self.version = [int(x) if x.isdigit() else x for x in re.compile(r'(\d+)').split(vstring) if x and x != '.']
        def __lt__(self, other): return self.version < (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __le__(self, other): return self.version <= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __eq__(self, other): return self.version == (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ne__(self, other): return self.version != (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __gt__(self, other): return self.version > (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
        def __ge__(self, other): return self.version >= (other.version if isinstance(other, LooseVersion) else LooseVersion(other).version)
    distutils_version_mod.LooseVersion = LooseVersion; distutils_mod.version = distutils_version_mod
    sys.modules['distutils'] = distutils_mod; sys.modules['distutils.version'] = distutils_version_mod

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    import requests, pyotp
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    os.system("pip install undetected-chromedriver selenium requests pyotp pycryptodome")
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    import requests, pyotp
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes

STOP_EVENT = threading.Event()
OTP_LOCK, DATA_LOCK, BROWSER_LOCK, INPUT_LOCK, TYPE_LOCK, SUBMIT_LOCK, PRINT_LOCK, DRIVER_LOCK, RESOURCE_LOCK = (threading.Lock() for _ in range(9))
CONFIG_FILE, DELAY_CONFIG_FILE = "config_gmail.json", "config_reg_fb.json"
BASE_YEAR = random.randint(1995, 2005)
APP_TOKEN = '350685531728|62f8ce9f74b12f84c123cc23437a4a32'
DEFAULT_DELAY_CONFIG = {'delay_mo_facebook': 10.0, 'delay_nhap_ho': 0.3, 'delay_nhap_ten': 0.3, 'delay_chon_ngay_sinh': 1.0, 'delay_chon_gioi_tinh': 0.5, 'delay_nhap_sdt_email': 1.0, 'delay_nhap_mat_khau': 1.0, 'delay_ngam_form_truoc_submit': 10.0, 'delay_validate_form': 5.0, 'delay_sau_khi_submit': 15.0, 'delay_ngam_otp': 60.0, 'delay_cho_load_trang_chu': 35.0, 'delay_giua_cac_lan_chay': 6.0, 'delay_thu_lai_khi_loi': 6.0, 'so_lan_thu_get_code': 2, 'mat_khau_fb': '', 'use_phone_bait': False, 'lay_token_android': True}
ALL_DRIVERS, GLOBAL_USED_PHONES, GLOBAL_USED_NAMES = [], set(), set()
built_in_print = print
PAUSE_FOR_INPUT = threading.Event(); PAUSE_FOR_INPUT.set() 
def thread_safe_print(*args, **kwargs):
    PAUSE_FOR_INPUT.wait() 
    with PRINT_LOCK: built_in_print(*args, **kwargs)
print = thread_safe_print 

class Colors:
    PRIMARY, SUCCESS, ERROR, WARNING, INFO, KEY, VALUE, LINE, TITLE, NUMBER, EMAIL, USERNAME, PASSWORD, RESET = "\033[38;2;255;100;150m", "\033[38;2;0;255;127m", "\033[38;2;255;50;50m", "\033[38;2;255;200;50m", "\033[38;2;100;255;200m", "\033[38;2;200;160;255m", "\033[38;2;120;255;220m", "\033[38;2;190;235;210m", "\033[38;2;255;215;0m", "\033[38;2;255;165;0m", "\033[38;2;100;200;255m", "\033[38;2;0;255;255m", "\033[38;2;255;105;180m", "\033[0m"
    @staticmethod
    def color_text(text, color): return f"{color}{text}{Colors.RESET}"

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
    built_in_print(f"{Colors.INFO}Phiên Bản: v20.1 NÉN (FB Reg Index Form - 100% Nam - 1 FILE DUY NHẤT){Colors.RESET}")
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
                    if key not in config: config[key] = value
                return config
        except Exception: return DEFAULT_DELAY_CONFIG.copy()
    else:
        with open(DELAY_CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(DEFAULT_DELAY_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_DELAY_CONFIG.copy()

def luu_delay_config(config):
    try:
        with open(DELAY_CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception: pass

def nhap_delay(tieu_de, gia_tri_mac_dinh):
    try:
        nhap = input(f'   {Colors.KEY}{tieu_de} ({gia_tri_mac_dinh} giây): {Colors.RESET}').strip()
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
    mat_khau_moi = input(f'   {Colors.KEY}Nhập mật khẩu cố định (Enter giữ [{mk_hien_tai}], gõ "rand" để random): {Colors.RESET}').strip()
    if mat_khau_moi.lower() == 'rand': config['mat_khau_fb'] = ''
    elif mat_khau_moi: config['mat_khau_fb'] = mat_khau_moi
    chon_moi_sdt = input(f'   {Colors.KEY}Bật chế độ Mồi SĐT +84 ảo rồi đổi sang Xác nhận Email ở Mode 1-5? (y/n, hiện tại: {config["use_phone_bait"]}): {Colors.RESET}').strip().lower()
    if chon_moi_sdt in ['y', 'n']: config['use_phone_bait'] = (chon_moi_sdt == 'y')
    chon_token = input(f'   {Colors.KEY}Tự động lấy thêm Access Token Android (EAAAAU...) sau khi reg xong? (y/n, hiện tại: {config["lay_token_android"]}): {Colors.RESET}').strip().lower()
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
    dau_so = ['333','338','339','358','359','368','369','378','379','388','389','396','397','398','399','777','778','779','787','788','789','968','969','978','979','988','989']
    with RESOURCE_LOCK:
        while True:
            phone = f"+84{random.choice(dau_so)}{''.join(random.choices(string.digits, k=6))}"
            if phone not in target_set: target_set.add(phone); return phone

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
            if full_name not in target_set: target_set.add(full_name); break
    username = f"{re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())}{''.join(random.choices(string.ascii_lowercase, k=2))}{random.randint(10000, 999999)}"
    return last_name_fb, first_name_fb, full_name, username

class Facebook:
    def MaHoaMatKhau(self, mat_khau):
        try:
            params = {'version': '2', 'flow': 'CONTROLLER_INITIALIZATION', 'method': 'GET', 'fb_api_req_friendly_name': 'pwdKeyFetch', 'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations', 'access_token': '438142079694454|fc0a7caa49b192f64f6f5a6d9643bb28'}
            response = requests.post('https://b-graph.facebook.com/pwd_key_fetch', params=params, timeout=15, proxies=self.proxy).json()
            rand_key, iv = get_random_bytes(32), get_random_bytes(12)
            encrypted_rand_key = PKCS1_v1_5.new(RSA.import_key(response.get('public_key'))).encrypt(rand_key)
            cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
            current_time = int(time.time()); cipher_aes.update(str(current_time).encode('utf-8'))
            encrypted_passwd, auth_tag = cipher_aes.encrypt_and_digest(mat_khau.encode('utf-8'))
            buf = io.BytesIO(); buf.write(bytes([1, int(str(response.get('key_id', '25')))])); buf.write(iv); buf.write(struct.pack('<h', len(encrypted_rand_key))); buf.write(encrypted_rand_key); buf.write(auth_tag); buf.write(encrypted_passwd)
            return f"#PWD_FB4A:2:{current_time}:{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception: return mat_khau

    def __init__(self, email=None, mat_khau=None, auth=None, proxy=None):
        self.proxy, self.email, self.auth = proxy, email, auth.replace(' ', '') if auth else None
        self.mat_khau = self.MaHoaMatKhau(mat_khau) if mat_khau else None
        self.URL, self.API_KEY, self.SIG = 'https://b-graph.facebook.com/auth/login', '882a8490361da98702bf97a021ddc14d', '214049b9f17c38bd767de53752b53946'
        self.device_id, self.adid, self.machine_id = str(uuid.uuid4()), str(uuid.uuid4()), ''.join(random.choices(string.ascii_letters + string.digits, k=24))
        self.jazoest = ''.join(random.choices(string.digits, k=5))
        self.HEADERS = {'content-type': 'application/x-www-form-urlencoded', 'x-fb-net-hni': '45201', 'zero-rated': '0', 'x-fb-sim-hni': '45201', 'x-fb-connection-quality': 'EXCELLENT', 'x-fb-friendly-name': 'authenticate', 'x-fb-connection-bandwidth': '78032897', 'x-tigon-is-retry': 'False', 'authorization': 'OAuth null', 'x-fb-connection-type': 'WIFI', 'x-fb-device-group': '3342', 'priority': 'u=3,i', 'x-fb-http-engine': 'Liger', 'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True', 'x-fb-request-analytics-tags': '{"network_tags":{"product":"350685531728","retry_attempt":"0"},"application_tags":"unknown"}', 'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 9; 23113RKC6C Build/PQ3A.190705.08211809) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/vi_VN;FBBV/480086274;FBCR/MobiFone;FBMF/Redmi;FBBD/Redmi;FBDV/23113RKC6C;FBSV/9;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=1280,height=720};FB_FW/1;FBRV/0;]'}

    def DangNhap(self, app_token=APP_TOKEN):
        self.data = {'email': self.email, 'password': self.mat_khau, 'generate_session_cookies': '1', 'locale': 'vi_VN', 'client_country_code': 'VN', 'access_token': app_token, 'api_key': self.API_KEY, 'adid': self.adid, 'account_switcher_uids': f'["{self.email}"]', 'source': 'login', 'machine_id': self.machine_id, 'jazoest': self.jazoest, 'meta_inf_fbmeta': 'V2_UNTAGGED', 'fb_api_req_friendly_name': 'authenticate', 'fb_api_caller_class': 'Fb4aAuthHandler', 'sig': self.SIG}
        try:
            ket_qua = requests.post(self.URL, headers=self.HEADERS, data=self.data, timeout=15, proxies=self.proxy).json()
            if 'error' in ket_qua:
                error_data = ket_qua.get('error', {}).get('error_data', {})
                if 'login_first_factor' in error_data and 'uid' in error_data:
                    if not self.auth: return {'status': 401, 'msg': 'Yêu cầu 2FA nhưng chưa có Secret Key'}
                    data_2fa = {'locale': 'vi_VN', 'format': 'json', 'email': self.email, 'device_id': self.device_id, 'access_token': app_token, 'generate_session_cookies': 'true', 'generate_machine_id': '1', 'twofactor_code': pyotp.TOTP(self.auth).now(), 'credentials_type': 'two_factor', 'error_detail_type': 'button_with_disabled', 'first_factor': error_data['login_first_factor'], 'password': self.mat_khau, 'userid': error_data['uid'], 'machine_id': error_data['login_first_factor']}
                    ket_qua = requests.post(self.URL, headers=self.HEADERS, data=data_2fa, timeout=15, proxies=self.proxy).json()
                else: return {'status': 401, 'msg': ket_qua.get('error', {}).get('message', 'Lỗi')}
            if 'access_token' in ket_qua: return {'status': 200, 'data': {'cookies': '; '.join((f"{c['name']}={c['value']}" for c in ket_qua.get('session_cookies', []))), 'token': ket_qua.get('access_token')}}
            return {'status': 401, 'msg': 'Đăng nhập thất bại'}
        except Exception as e: return {'status': 401, 'msg': str(e)}

def parse_proxy(proxy_str):
    if not proxy_str: return None
    p_str = str(proxy_str).strip()
    for proto in ["http://", "https://", "socks5://", "socks4://"]:
        if p_str.lower().startswith(proto): p_str = p_str[len(proto):]; break
    if "@" in p_str:
        try:
            u, pwd = p_str.split("@", 1)[0].split(":", 1)
            ip, port = p_str.split("@", 1)[1].split(":", 1)
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
    p = parse_proxy(proxy_str)
    if not p: return None
    fmt = f"http://{p['user']}:{p['pass']}@{p['ip']}:{p['port']}" if p["user"] and p["pass"] else f"http://{p['ip']}:{p['port']}"
    return {"http": fmt, "https": fmt}

class LocalProxyForwarder:
    def __init__(self, remote_ip, remote_port, username=None, password=None):
        self.remote_ip, self.remote_port, self.username, self.password = remote_ip, int(remote_port), username, password
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
            except: break
    def _handle_client(self, client_sock):
        try:
            req = b""
            while b"\r\n\r\n" not in req:
                chunk = client_sock.recv(4096)
                if not chunk: client_sock.close(); return
                req += chunk
            header_part, rest = req.split(b"\r\n\r\n", 1)
            lines = header_part.split(b"\r\n")
            is_connect = lines[0].decode("utf-8", "ignore").startswith("CONNECT")
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(15); remote_sock.connect((self.remote_ip, self.remote_port))
            auth_header = b""
            if self.username and self.password: auth_header = f"Proxy-Authorization: Basic {base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()}".encode() + b"\r\n"
            if is_connect:
                connect_req = lines[0] + b"\r\n" + b"".join([l + b"\r\n" for l in lines[1:] if not l.lower().startswith(b"proxy-authorization")]) + auth_header + b"\r\n"
                remote_sock.sendall(connect_req)
                resp = b""
                while b"\r\n\r\n" not in resp:
                    c = remote_sock.recv(4096)
                    if not c: break
                    resp += c
                if b"200" in (resp.split(b"\r\n")[0] if resp else b""): client_sock.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
                else: client_sock.sendall(resp); client_sock.close(); remote_sock.close(); return
            else:
                new_req = lines[0] + b"\r\n" + b"".join([l + b"\r\n" for l in lines[1:] if not l.lower().startswith(b"proxy-authorization")]) + auth_header + b"\r\n" + rest
                remote_sock.sendall(new_req)
            remote_sock.settimeout(None); client_sock.settimeout(None)
            sockets = [client_sock, remote_sock]
            while self.running:
                r, _, _ = select.select(sockets, [], sockets, 30)
                if not r: break
                for s in r:
                    other = remote_sock if s is client_sock else client_sock
                    data = s.recv(16384)
                    if not data: return
                    other.sendall(data)
        except: pass
        finally:
            try: client_sock.close()
            except: pass
            try: remote_sock.close()
            except: pass

class MailService:
    def __init__(self, proxy=None):
        self.base_url, self.token, self.domain, self.email_address, self.seen_msg_ids, self.proxy = "https://api.mail.tm", None, None, None, set(), proxy 
    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10, proxies=self.proxy)
            if r.status_code == 200: self.domain = r.json()['hydra:member'][0]['domain']; return self.domain
        except: return None
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        time.sleep(random.uniform(0.5, 2.0))
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10, proxies=self.proxy)
            if r.status_code == 201: self.email_address = r.json()['address']; return self.email_address
        except: return None
    def authenticate(self, email=None, password="TempPass123!"):
        if email: self.email_address = email
        time.sleep(random.uniform(0.5, 2.0)) 
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10, proxies=self.proxy)
            if r.status_code == 200: self.token = r.json()['token']; return True
        except: return False
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
                        subject, frm = str(msg.get('subject', '')).lower(), str(msg.get('from', {}).get('address', '')).lower()
                        if any(k in subject or k in frm for k in ['facebook', 'facebookmail', 'fb', 'meta', 'instagram']):
                            detail = requests.get(f"{self.base_url}/messages/{msg_id}", headers=headers, timeout=10, proxies=self.proxy).json()
                            raw_text = detail.get('text', '') or re.sub('<[^<]+?>', ' ', str(detail.get('html', '')))
                            code = None
                            if force_8_digits:
                                m = re.search(r'(?<!\d)(\d{8})(?!\d)', raw_text.replace(" ", ""))
                                if m: code = m.group(1)
                            else:
                                m = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', raw_text, re.IGNORECASE)
                                if m: code = m.group(1)
                                else:
                                    m_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                    if m_sub: code = m_sub.group(1)
                                    else:
                                        m_body = re.search(r'(?<!\d)(\d{5,6})(?!\d)', raw_text.lower().replace(str(self.email_address).lower(), "").replace(" ", ""))
                                        if m_body: code = m_body.group(1)
                            if code: self.seen_msg_ids.add(msg_id); return code
            except: pass
            time.sleep(random.uniform(6.0, 10.0))
        return None

class GmailIMAPService:
    def __init__(self, base_email, app_password): self.base_email, self.app_password, self.mail, self.seen_uids = base_email, app_password.replace(" ", ""), None, set()
    def connect(self):
        try: self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993); self.mail.login(self.base_email, self.app_password); return True
        except Exception as e: print(f"{Colors.color_text(f'Lỗi IMAP: {e}', Colors.ERROR)}"); return False
    def get_latest_uid(self):
        if not self.mail and not self.connect(): return 0
        try:
            self.mail.select("INBOX", readonly=True)
            status, data = self.mail.uid("search", None, 'ALL')
            if status == "OK" and data[0]: return int(data[0].split()[-1]) 
        except: pass
        return 0
    def get_text(self, msg):
        plain, html_list = [], []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment": continue
                ctype, payload = part.get_content_type(), part.get_payload(decode=True)
                if not payload: continue
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                if ctype == "text/plain": plain.append(text)
                elif ctype == "text/html": html_list.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                if msg.get_content_type() == "text/plain": plain.append(text)
                else: html_list.append(text)
        if plain: return "\n".join(plain).strip()
        if html_list: return re.sub(r'<[^>]+>', ' ', "\n".join(html_list)).strip()
        return ""
    def decode_msg_header(self, raw_header):
        if not raw_header: return ""
        try:
            return "".join([t.decode(c or 'utf-8', errors='replace') if isinstance(t, bytes) else str(t) for t, c in decode_header(raw_header)])
        except: return str(raw_header)
    def get_otp_code(self, target_email, since_uid=0, timeout=120, force_8_digits=False):
        if not self.mail and not self.connect(): return None
        start_time = time.time()
        time.sleep(random.uniform(1.0, 5.0))
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    for uid_bytes in reversed(data[0].split()[-10:]):
                        try: uid_int = int(uid_bytes)
                        except: continue
                        if uid_int <= since_uid or uid_bytes in self.seen_uids: continue
                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = next((item[1] for item in fetch_data if isinstance(item, tuple)), None)
                            if raw:
                                msg = email.message_from_bytes(raw)
                                to_addr, subject, from_addr = self.decode_msg_header(msg.get("To", "")).lower(), self.decode_msg_header(msg.get("Subject", "")).lower(), self.decode_msg_header(msg.get("From", "")).lower()
                                if target_email.lower() not in to_addr: continue
                                if any(k in subject or k in from_addr for k in ["facebook", "facebookmail", "fb", "meta", "instagram"]) and any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã", "authenticate", "profile", "confirm", "xác nhận", "fb-"]):
                                    body = self.get_text(msg)
                                    code = None
                                    if force_8_digits:
                                        m = re.search(r'(?<!\d)(\d{8})(?!\d)', body.replace(" ", ""))
                                        if m: code = m.group(1)
                                    else:
                                        m = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', body, re.IGNORECASE)
                                        if m: code = m.group(1)
                                        else:
                                            m_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                            if m_sub: code = m_sub.group(1)
                                            else:
                                                m_body = re.search(r'(?<!\d)(\d{5,6})(?!\d)', body.lower().replace(target_email.lower(), "").replace(" ", ""))
                                                if m_body: code = m_body.group(1)
                                    if code: self.seen_uids.add(uid_bytes); return code
            except: pass
            time.sleep(random.uniform(6.0, 10.0)) 
        return None

class HotmailAPIService:
    def __init__(self, data_line, api_mode, proxy=None):
        self.url, self.data_line, self.api_mode, self.proxy = "https://smail1s.com/get_messages", data_line.strip(), api_mode.strip(), proxy
        self.email = self.data_line.split('|')[0] if '|' in self.data_line else self.data_line
        self.seen_msg_ids = set()
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries)); self.session.mount('https://', HTTPAdapter(max_retries=retries))
        if self.proxy: self.session.proxies.update(self.proxy)
        self.session.headers.update({'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    def init_baseline(self):
        time.sleep(random.uniform(1.0, 3.0)) 
        for _ in range(3):
            try:
                response = self.session.post(self.url, json={"mode": self.api_mode, "data": self.data_line}, timeout=20)
                if response.status_code == 200:
                    data_array = response.json().get("data", [])
                    if data_array and len(data_array) > 0:
                        for msg in data_array[0].get("messages", []):
                            msg_id = str(msg.get("id", msg.get("uid", "")))
                            if not msg_id: msg_id = hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                            self.seen_msg_ids.add(msg_id)
                    break 
            except: time.sleep(3) 
    def get_otp_code(self, timeout=180, force_8_digits=False): 
        start_time, last_logged = time.time(), ""
        print(f"{Colors.color_text(f'[API Smail1s] Đang check hộp thư {self.email}...', Colors.INFO)}")
        time.sleep(random.uniform(1.0, 5.0))
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                response = self.session.post(self.url, json={"mode": self.api_mode, "data": self.data_line}, timeout=20)
                if response.status_code == 200:
                    data_array = response.json().get("data", [])
                    if data_array and len(data_array) > 0:
                        if data_array[0].get("error"):
                            err = f"Lỗi hộp thư: {data_array[0].get('error')}"
                            if err != last_logged: print(f"{Colors.color_text(f'[API Smail1s] {err}', Colors.ERROR)}"); last_logged = err
                        else:
                            for msg in data_array[0].get("messages", []):
                                msg_id = str(msg.get("id", msg.get("uid", ""))) or hashlib.md5(str(msg.get("message", "")).encode()).hexdigest()
                                if msg_id in self.seen_msg_ids: continue
                                subject, from_sender, raw_msg = str(msg.get("subject", "")).lower(), str(msg.get("from", "")).lower(), str(msg.get("message", ""))
                                is_fb_meta = any(k in subject or k in from_sender for k in ["facebook", "facebookmail", "fb", "meta", "instagram"])
                                is_security_mail = any(kw in subject for kw in ["security", "bảo mật", "verify", "xác minh", "code", "mã", "factor", "authenticate", "profile", "account"]) if force_8_digits else True
                                if is_fb_meta and is_security_mail:
                                    code = None
                                    if force_8_digits:
                                        m = re.search(r'(?<!\d)(\d{8})(?!\d)', re.sub(r'<[^>]+>', ' ', raw_msg).replace(" ", ""))
                                        if m: code = m.group(1)
                                    else:
                                        m = re.search(r'fb[-\s]*(\d{5,6})\b', subject, re.IGNORECASE) or re.search(r'fb[-\s]*(\d{5,6})\b', raw_msg, re.IGNORECASE)
                                        if m: code = m.group(1)
                                        else:
                                            m_sub = re.search(r'(?<!\d)(\d{5,6})(?!\d)', subject)
                                            if m_sub: code = m_sub.group(1)
                                            else:
                                                m_body = re.search(r'(?<!\d)(\d{5,6})(?!\d)', re.sub(r'<[^>]+>', ' ', raw_msg.lower().replace(self.email.lower(), "")).replace(" ", ""))
                                                if m_body: code = m_body.group(1)
                                    if code: self.seen_msg_ids.add(msg_id); print(f"{Colors.color_text(f'[API Smail1s] ĐÃ BẮT ĐƯỢC MÃ CHUẨN: {code}', Colors.SUCCESS)}"); return code
            except Exception as e: pass
            time.sleep(random.uniform(5.0, 8.0))
        return None

class AutoSMSService:
    def __init__(self, api_key, country="vn", proxy=None): self.api_key, self.country, self.service, self.base_url, self.order_id, self.phone, self.proxy = api_key, country, "facebook", "https://autosms.site/api", None, None, proxy
    def buy_number(self):
        try:
            js = requests.get(f"{self.base_url}/buy-number/{self.country}/{self.service}?key={self.api_key}", timeout=10, proxies=self.proxy).json()
            if js.get("success"): self.phone, self.order_id = js["data"]["phone"], js["data"]["order_id"]; return self.phone
        except: pass
        return None
    def get_otp_code(self, timeout=120):
        if not self.order_id: return None
        start_time = time.time()
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
            try:
                js = requests.get(f"{self.base_url}/orders/{self.order_id}?key={self.api_key}", timeout=10, proxies=self.proxy).json()
                if js.get("success") and js.get("data") and js["data"].get("code"): return js["data"]["code"]
            except: pass
            time.sleep(4)
        return None
    def cancel_order(self):
        if self.order_id:
            try: requests.get(f"{self.base_url}/cancel/{self.order_id}?key={self.api_key}", timeout=10, proxies=self.proxy)
            except: pass

def generate_dot_variants(gmail):
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com": return [gmail]
    if "." in local: local = local.replace(".", "")
    variants = []
    if local:
        for mask in range(1 << max(0, len(local) - 1)):
            val = local[0]
            for i in range(1, len(local)): val += "." + local[i] if mask & (1 << (i - 1)) else local[i]
            variants.append(val + "@" + domain)
    random.shuffle(variants)
    return variants

# ==================== MAIN THREAD ====================
class starts(threading.Thread):
    def __init__(self, thread_id, mode, account_count, data_source, delay_config, manual_password=None, base_gmail=None, app_password=None, api_mode=None, avatar_folder="", proxies_list=None, autosms_api_key=None, autosms_country="vn"):
        super().__init__()
        self.thread_id, self.mode, self.account_count, self.data_source, self.delay_config, self.manual_password = f"Tab-{thread_id}", mode, account_count, data_source, delay_config, manual_password
        self.base_gmail, self.app_password, self.api_mode, self.avatar_folder, self.proxies_list, self.autosms_api_key, self.autosms_country = base_gmail, app_password, api_mode, avatar_folder, proxies_list or [], autosms_api_key, autosms_country
        self.used_phones, self.used_names = set(), set()
    
    def run(self):
        global BASE_YEAR
        raw_proxy, req_proxy = None, None
        if self.proxies_list:
            raw_proxy = self.proxies_list[(int(self.thread_id.split("-")[1]) - 1) % len(self.proxies_list)]
            req_proxy = format_proxy(raw_proxy)
            p_info = parse_proxy(raw_proxy)
            if p_info and p_info.get("user"): print(Colors.color_text(f"[{self.thread_id}] Proxy: {p_info['ip']}:{p_info['port']} (User: {p_info['user']})", Colors.WARNING))
            elif p_info: print(Colors.color_text(f"[{self.thread_id}] Proxy: {p_info['ip']}:{p_info['port']}", Colors.WARNING))
        
        def create_one_account(account_index):
            global BASE_YEAR
            if STOP_EVENT.is_set(): return False
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}\n{Colors.color_text(f'[{self.thread_id}] BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email, imap_service, mail_service, hotmail_service, autosms_service = "", None, None, None, None
            last_name_fb, first_name_fb, full_name, username = VietnameseMaleNameGenerator(self.used_names)
            secure_pass = self.delay_config['mat_khau_fb'] if self.delay_config.get('mat_khau_fb') else "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%") for _ in range(12))

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
                    mail_service.authenticate(used_email, self.manual_password if self.manual_password else "TempPass123!")
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
                used_email, hotmail_service = data_line.split('|')[0], HotmailAPIService(data_line, self.api_mode, proxy=req_proxy)
            elif self.mode == "6":
                autosms_service = AutoSMSService(self.autosms_api_key, self.autosms_country, proxy=req_proxy)
                used_email = autosms_service.buy_number()
                if not used_email: print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi thuê SĐT!', Colors.ERROR)}"); return False

            use_phone_bait = self.delay_config.get('use_phone_bait', False) and (self.mode in ["1", "2", "3", "4", "5"])
            contact_for_signup = tao_so_dien_thoai(self.used_phones) if use_phone_bait else used_email

            if use_phone_bait: print(f"{Colors.color_text(f'[{self.thread_id}] Mồi SĐT: {contact_for_signup} -> Xác nhận Email: {used_email}', Colors.INFO)}")
            else: print(f"{Colors.color_text(f'[{self.thread_id}] Email/SĐT đăng ký: {used_email}', Colors.INFO)}")

            driver = None
            try:
                thread_idx = int(self.thread_id.split("-")[1]) - 1 
                win_width, win_height, columns = 460, 520, 4       
                x_pos, y_pos = (thread_idx % columns) * win_width, (thread_idx // columns) * win_height
                
                options = uc.ChromeOptions()
                for arg in ['--mute-audio', '--disable-notifications', '--disable-save-password-bubble', '--password-store=basic', f'--window-size={win_width},{win_height}', f'--window-position={x_pos},{y_pos}', '--force-device-scale-factor=0.65', '--disable-gpu', '--disable-software-rasterizer', '--disable-dev-shm-usage', '--incognito']: options.add_argument(arg)
                options.add_experimental_option('prefs', {'credentials_enable_service': False, 'profile.password_manager_enabled': False, 'profile.password_manager_leak_detection': False, 'autofill.profile_enabled': False, 'profile.default_content_setting_values.notifications': 2})
                
                forwarder = None
                if raw_proxy:
                    parsed_p = parse_proxy(raw_proxy)
                    if parsed_p:
                        if parsed_p.get("user") and parsed_p.get("pass"):
                            forwarder = LocalProxyForwarder(parsed_p["ip"], parsed_p["port"], parsed_p["user"], parsed_p["pass"])
                            options.add_argument(f'--proxy-server=http://127.0.0.1:{forwarder.local_port}')
                        else: options.add_argument(f'--proxy-server=http://{parsed_p["ip"]}:{parsed_p["port"]}')
                
                with BROWSER_LOCK:
                    driver = uc.Chrome(options=options)
                    with DRIVER_LOCK: ALL_DRIVERS.append((self.thread_id, driver))
                    try: driver.set_window_size(win_width, win_height); driver.set_window_position(x_pos, y_pos)
                    except: pass
                    time.sleep(1) 
                    
                wait = WebDriverWait(driver, 15)
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang truy cập Facebook...', Colors.INFO)}")
                driver.get("https://www.facebook.com/r.php")
                time.sleep(self.delay_config['delay_mo_facebook'])
                
                try:
                    cookie_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Cho phép') or contains(text(), 'Đồng ý')] | //div[@role='button' and (contains(., 'Allow') or contains(., 'Cho phép'))]")
                    if cookie_btns: driver.execute_script("arguments[0].click();", cookie_btns[0]); time.sleep(2)
                except: pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: current_year = "2005"
                current_day, current_month = str(random.randint(2, 28)), str(random.randint(1, 12))
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)

                def human_type(element, text):
                    with TYPE_LOCK:
                        try: driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element); time.sleep(0.5)
                        except: pass
                        try: element.click() 
                        except: driver.execute_script("arguments[0].click();", element) 
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].focus();", element)
                        element.send_keys(Keys.CONTROL + "a"); time.sleep(0.2); element.send_keys(Keys.BACKSPACE); time.sleep(0.3)
                        for char in text:
                            driver.execute_script("arguments[0].focus();", element); element.send_keys(char); time.sleep(random.uniform(0.05, 0.15)) 
                        time.sleep(random.uniform(0.5, 1.0))
                        try: element.send_keys(Keys.TAB)
                        except: pass

                # ĐIỀN FORM INDEX MÀN HÌNH
                try:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang phân tích Form Meta...', Colors.INFO)}")
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]")))
                    time.sleep(2)

                    visible_inputs = [inp for inp in driver.find_elements(By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]") if inp.is_displayed()]

                    if len(visible_inputs) >= 4:
                        ho_el, ten_el, email_el, pass_el = visible_inputs[0], visible_inputs[1], visible_inputs[2], visible_inputs[3]
                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Họ Tên...', Colors.INFO)}")
                        human_type(ho_el, last_name_fb); time.sleep(self.delay_config['delay_nhap_ho'])
                        human_type(ten_el, first_name_fb); time.sleep(self.delay_config['delay_nhap_ten'])

                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Email/SĐT...', Colors.INFO)}")
                        human_type(email_el, contact_for_signup); time.sleep(self.delay_config['delay_nhap_sdt_email'])

                        time.sleep(1.5)
                        visible_inputs_after = [inp for inp in driver.find_elements(By.XPATH, "//input[not(@type='hidden') and not(@type='checkbox') and not(@type='radio')]") if inp.is_displayed()]
                        if len(visible_inputs_after) >= 5 and ("email" in contact_for_signup.lower() or "@" in contact_for_signup):
                            print(f"{Colors.color_text(f'[{self.thread_id}] Có ô Xác nhận Email...', Colors.INFO)}")
                            human_type(visible_inputs_after[3], contact_for_signup)
                            pass_el = visible_inputs_after[4]

                        print(f"{Colors.color_text(f'[{self.thread_id}] Điền Mật khẩu...', Colors.INFO)}")
                        human_type(pass_el, secure_pass); time.sleep(self.delay_config['delay_nhap_mat_khau'])
                    else:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi Form!', Colors.ERROR)}"); return False

                    gender_text = "Nam"
                    print(f"{Colors.color_text(f'[{self.thread_id}] Chọn JS Ngày Sinh & Giới tính...', Colors.INFO)}")
                    try:
                        driver.set_script_timeout(25)
                        js_dropdowns = """
                        const day = arguments[0], month = arguments[1], year = arguments[2], gender = arguments[3], callback = arguments[4];
                        async function sel(index, val) {
                            let combos = Array.from(document.querySelectorAll('div[role="combobox"], select'));
                            if (combos.length <= index) return false;
                            let box = combos[index];
                            if(box.tagName.toLowerCase() === 'select') {
                                Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set.call(box, val);
                                box.dispatchEvent(new Event('change', { bubbles: true })); return true;
                            }
                            box.scrollIntoView({block: 'center'}); box.click(); await new Promise(r => setTimeout(r, 800));
                            let opt = Array.from(document.querySelectorAll('div[role="option"], li')).find(o => {
                                let txt = (o.innerText || "").trim().toLowerCase(), search = String(val).toLowerCase();
                                return txt === search || txt === "tháng " + search || txt === "0" + search;
                            });
                            if(opt) { opt.scrollIntoView({block: 'center'}); opt.click(); await new Promise(r => setTimeout(r, 600)); return true; }
                            document.body.click(); await new Promise(r => setTimeout(r, 400)); return false;
                        }
                        (async function() { try { await sel(0, day); await sel(1, month); await sel(2, year); await sel(3, gender); callback("SUCCESS"); } catch (e) { callback("ERROR"); } })();
                        """
                        driver.execute_async_script(js_dropdowns, current_day, current_month, current_year, gender_text)
                    except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] JS Dropdown Lỗi: {e}', Colors.ERROR)}")

                    time.sleep(self.delay_config['delay_chon_gioi_tinh'])
                    time.sleep(self.delay_config['delay_ngam_form_truoc_submit'])

                except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi form: {e}', Colors.ERROR)}"); time.sleep(5); return False

                uid_moc = 0
                if self.mode in ["3", "4"] and imap_service: uid_moc = imap_service.get_latest_uid()
                elif self.mode == "5" and hotmail_service: hotmail_service.init_baseline()

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                driver.execute_script("document.body.click();")
                time.sleep(self.delay_config['delay_validate_form'])
                
                with SUBMIT_LOCK:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Bấm Sign up...', Colors.INFO)}")
                    try:
                        js_submit = """
                        let b = document.querySelector('button[name="websubmit"], button[type="submit"]');
                        if (!b) b = Array.from(document.querySelectorAll('button, div[role="button"]')).find(btn => { let t = (btn.innerText||"").trim().toLowerCase(); return ["submit","sign up","đăng ký","gửi","next"].includes(t) || t.includes("đăng ký"); });
                        if (!b) { let sp = Array.from(document.querySelectorAll('span')).find(s => ["submit","sign up","đăng ký","gửi","next"].includes((s.innerText||"").trim().toLowerCase())); if(sp) b = sp.closest('button, div[role="button"]'); }
                        if (b) {
                            b.disabled = false; b.removeAttribute('disabled'); b.style.pointerEvents = 'auto'; b.scrollIntoView({block:'center'}); b.focus(); b.click(); 
                            ['mousedown','mouseup','click'].forEach(e => b.dispatchEvent(new MouseEvent(e, {view: window, bubbles: true, cancelable: true, clientX: b.getBoundingClientRect().x+20, clientY: b.getBoundingClientRect().y+10})));
                            return "CLICKED";
                        }
                        let f = document.querySelector('form'); if(f){ f.submit(); return "FORM_SUBMITTED"; } return "NOT_FOUND";
                        """
                        if driver.execute_script(js_submit) not in ["CLICKED", "FORM_SUBMITTED"]:
                            try: driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[name='websubmit'], button[type='submit']"))
                            except: pass_el.send_keys(Keys.ENTER)
                    except: pass
                    time.sleep(self.delay_config['delay_sau_khi_submit']) 

                if use_phone_bait:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đổi SĐT -> Email...', Colors.INFO)}")
                    try:
                        driver.execute_script("Array.from(document.querySelectorAll('a, button, div[role=\"button\"], span')).find(el => {let t = (el.innerText||'').toLowerCase(); return t.includes('cập nhật') || t.includes('update') || t.includes('xác nhận') || t.includes('confirm') || t.includes('thay đổi'); })?.closest('a, button, [role=\"button\"]')?.click();")
                        time.sleep(4)
                        for nmi in driver.find_elements(By.XPATH, "//input[@name='new' or @name='contactpoint' or @type='email' or @type='text']"):
                            if nmi.is_displayed(): human_type(nmi, used_email); break
                        time.sleep(1.5)
                        driver.execute_script("Array.from(document.querySelectorAll('button, input[type=\"submit\"], div[role=\"button\"]')).find(b => {let t = (b.innerText||b.value||'').toLowerCase(); return ['thêm','add','cập nhật','update','tiếp tục','continue'].includes(t) || b.name==='change'; })?.click();")
                        time.sleep(6)
                    except: pass

                otp_input, locators = None, [(By.NAME, "code"), (By.ID, "code_in_cliff"), (By.NAME, "email_confirmation_code"), (By.NAME, "confirmationCode"), (By.XPATH, "//input[contains(@name, 'code')]"), (By.XPATH, "//input[contains(@aria-label, 'FB-')]"), (By.XPATH, "//input[contains(@aria-label, 'Mã')]"), (By.XPATH, "//input[contains(@aria-label, 'Code')]"), (By.XPATH, "//input[@type='text' or @type='number' or @type='tel']")]
                time.sleep(3)
                for loc in locators:
                    try: 
                        for el in driver.find_elements(*loc):
                            if el.is_displayed(): otp_input = el; break
                        if otp_input: break
                    except: pass
                if not otp_input:
                    try: driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);"); time.sleep(1); otp_input = driver.execute_script("return document.querySelector('input[type=\"text\"], input[name*=\"code\"], input');")
                    except: pass
                if not otp_input: return False
                
                otp_code, max_resend = None, int(self.delay_config.get('so_lan_thu_get_code', 2))
                for attempt in range(max_resend + 1):
                    if STOP_EVENT.is_set(): return False
                    start_otp_wait = time.time()
                    if self.mode == "2" and not getattr(mail_service, 'token', None):
                        with OTP_LOCK:
                            PAUSE_FOR_INPUT.clear()
                            otp_code = input(f"\n{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: NHẬP OTP CHO [{used_email}]: ', Colors.SUCCESS)}").strip()
                            PAUSE_FOR_INPUT.set()
                    else:
                        target_wait = self.delay_config['delay_ngam_otp'] if self.mode in ["3", "4", "5", "6"] else 0
                        print(f"{Colors.color_text(f'[{self.thread_id}] Lần {attempt+1}: Quét mã OTP...', Colors.INFO)}")
                        if self.mode == "1" or self.mode == "2": otp_code = mail_service.get_otp_code(100)
                        elif self.mode in ["3", "4"]: otp_code = imap_service.get_otp_code(used_email, uid_moc, 100)
                        elif self.mode == "5": otp_code = hotmail_service.get_otp_code(100) 
                        elif self.mode == "6": otp_code = autosms_service.get_otp_code(120)
                    if otp_code:
                        if self.mode in ["3", "4", "5", "6"] and (target_wait - (time.time() - start_otp_wait)) > 0:
                            rem = int(target_wait - (time.time() - start_otp_wait))
                            print(f"{Colors.color_text(f'[{self.thread_id}] Lấy mã {otp_code} thành công! Ngâm form {rem}s...', Colors.WARNING)}")
                            for w in range(rem, 0, -5):
                                if STOP_EVENT.is_set(): return False
                                time.sleep(min(5, w))
                        break 
                    if attempt < max_resend:
                        if driver.execute_script("let b=Array.from(document.querySelectorAll('a, button, div[role=\"button\"], span')).find(el=>{let t=(el.innerText||'').toLowerCase();return t.includes('không nhận')||t.includes('receive')||t.includes('gửi lại email');}); if(b){(b.closest('a, button, [role=\"button\"]')||b).click(); return true;} return false;"):
                            time.sleep(3) 
                            driver.execute_script("let b=Array.from(document.querySelectorAll('button, div[role=\"button\"], a, span')).find(el=>{let t=(el.innerText||'').toLowerCase();return t.includes('gửi lại')||t.includes('resend')||t.includes('send email again');}); if(b){(b.closest('button, [role=\"button\"], a')||b).click();}")
                            time.sleep(5)
                if not otp_code:
                    if self.mode == "6": autosms_service.cancel_order()
                    return False

                print(f"{Colors.color_text(f'[{self.thread_id}] Điền OTP: {otp_code}', Colors.SUCCESS)}")
                try: human_type(otp_input, otp_code)
                except: driver.execute_script("let i=arguments[0]; Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(i,arguments[1]); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true}));", otp_input, otp_code)
                time.sleep(1.5)

                if driver.execute_script("let b=Array.from(document.querySelectorAll('button, div[role=\"button\"], input[type=\"submit\"]')).find(el=>{let t=(el.innerText||el.value||'').toLowerCase(); return el.name==='confirm'||['tiếp tục','next','confirm','continue','xác nhận'].includes(t)||el.type==='submit';}); if(b){b.disabled=false; b.removeAttribute('disabled'); b.click(); return true;} return false;") is not True:
                    try: driver.execute_script("arguments[0].click();", WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@name='confirm' or @type='submit']"))))
                    except:
                        try: otp_input.send_keys(Keys.ENTER)
                        except: pass

                time.sleep(self.delay_config['delay_cho_load_trang_chu'])
                try: driver.execute_script("Array.from(document.querySelectorAll('button, div[role=\"button\"], a')).find(b=>{let t=(b.innerText||'').toLowerCase();return ['ok','tiếp tục','continue'].includes(t)})?.click();"); time.sleep(5)
                except: pass
                
                ck = {c['name']: c['value'] for c in driver.get_cookies()}
                fb_uid, src, url = ck.get('c_user', ''), driver.page_source.lower(), driver.current_url.lower()
                if "checkpoint" in url or "challenge" in url or "suspended" in url or "tài khoản của bạn đã bị tạm ngưng" in src or not fb_uid or not ck.get('xs'):
                    print(f"\n{Colors.color_text(f'[{self.thread_id}] LỖI: TÀI KHOẢN ĐÃ DIE / CHECKPOINT!', Colors.ERROR)}\n"); return "DEAD" 
                
                if self.avatar_folder and os.path.exists(self.avatar_folder):
                    imgs = [f for f in os.listdir(self.avatar_folder) if f.lower().endswith(('.png','.jpg','.jpeg','.webp'))]
                    if imgs:
                        try:
                            driver.get("https://www.facebook.com/profile.php"); time.sleep(8)
                            if "checkpoint" not in driver.current_url.lower():
                                driver.execute_script("if(!window.h){window.oC=window.HTMLInputElement.prototype.click;window.HTMLInputElement.prototype.click=function(){if(this.type==='file'){this.style.display='block';this.style.opacity='1';this.style.visibility='visible';this.style.position='fixed';this.style.top='0';this.style.left='0';this.style.zIndex='99999';}else{window.oC.call(this);}};window.h=true;} document.querySelector('[aria-label*=\"ảnh đại diện\"], [aria-label*=\"profile picture\"], svg[aria-label*=\"ảnh đại diện\"]')?.closest('div[role=\"button\"], button, a')?.click();")
                                time.sleep(3)
                                fis = driver.find_elements(By.XPATH, "//input[@type='file']")
                                if fis:
                                    fis[-1].send_keys(os.path.abspath(os.path.join(self.avatar_folder, random.choice(imgs)))); time.sleep(6)
                                    driver.execute_script("Array.from(document.querySelectorAll('div[aria-label=\"Lưu\"], div[aria-label=\"Save\"], div[role=\"button\"], button, span')).find(el=>{let t=(el.innerText||'').toLowerCase(), a=(el.getAttribute('aria-label')||'').toLowerCase(); return ['lưu','save'].includes(t) || ['lưu','save'].includes(a);})?.closest('div[role=\"button\"], button')?.click();")
                                    time.sleep(10)
                        except: pass

                two_fa_secret = ""
                try:
                    driver.get("https://accountscenter.facebook.com/password_and_security/two_factor/"); time.sleep(7)
                    for _ in range(4):
                        if driver.execute_script("let t=arguments[0].toLowerCase(); let b=Array.from(document.querySelectorAll('*')).find(el=>{let x=(el.innerText||'').toLowerCase();return (x.includes(t)||x.includes('facebook'))&&x.length<60;}); if(b){b.closest('div[role=\"button\"], a[role=\"link\"], button')?.click(); return true;} return false;", first_name_fb): time.sleep(4); break
                        time.sleep(2)
                    for _ in range(6):
                        if driver.execute_script("let b=Array.from(document.querySelectorAll('button, div[role=\"button\"], span')).find(el=>{let x=(el.innerText||'').toLowerCase();return x==='bắt đầu'||x==='get started';}); if(b){(b.closest('button, [role=\"button\"]')||b).click(); return true;} return false;"): time.sleep(4); break
                        time.sleep(1.5)
                    for _ in range(6):
                        if driver.execute_script("let x=(document.body.innerText||'').toLowerCase(); return x.includes('kiểm tra email')||x.includes('mã bảo mật');"): break
                        time.sleep(1.5)
                    if driver.execute_script("let x=(document.body.innerText||'').toLowerCase(); return x.includes('kiểm tra email')||x.includes('mã bảo mật');"):
                        verify_code = mail_service.get_otp_code(120, True) if self.mode in ["1","2"] else imap_service.get_otp_code(used_email, uid_moc, 120, True) if self.mode in ["3","4"] else hotmail_service.get_otp_code(180, True) if self.mode=="5" else autosms_service.get_otp_code(120)
                        if verify_code:
                            driver.execute_script("let i=document.querySelector('input[type=\"text\"], input[type=\"tel\"], input:not([type=\"hidden\"])'); if(i){Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(i,arguments[0]); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true}));}", verify_code); time.sleep(1.5)
                            driver.execute_script("Array.from(document.querySelectorAll('button, div[role=\"button\"]')).find(b=>['tiếp tục','next','continue','gửi','tiếp','xác nhận','submit'].includes((b.innerText||'').toLowerCase()) && !b.disabled)?.click();"); time.sleep(8)
                            if "two_factor" not in driver.current_url.lower(): driver.get("https://accountscenter.facebook.com/password_and_security/two_factor/"); time.sleep(5)
                            driver.execute_script("let t=arguments[0].toLowerCase(); let b=Array.from(document.querySelectorAll('*')).find(el=>{let x=(el.innerText||'').toLowerCase();return (x.includes(t)||x.includes('facebook'))&&x.length<60;}); b?.closest('div[role=\"button\"], a[role=\"link\"], button')?.click();", first_name_fb); time.sleep(4)
                    driver.execute_script("let b=Array.from(document.querySelectorAll('*')).find(el=>{let x=(el.innerText||'').toLowerCase();return x.includes('authentication app')||x.includes('ứng dụng xác thực');}); b?.closest('div[role=\"button\"], label, div[tabindex], button, [role=\"radio\"]')?.click();"); time.sleep(2)
                    driver.execute_script("Array.from(document.querySelectorAll('button, div[role=\"button\"], span')).find(b=>['continue','next','tiếp tục','tiếp'].includes((b.innerText||'').toLowerCase()))?.closest('button, [role=\"button\"]')?.click();"); time.sleep(5)
                    driver.execute_script("window.k=''; if(navigator.clipboard&&!window.cH){const o=navigator.clipboard.writeText; navigator.clipboard.writeText=function(t){let c=(t||'').replace(/\\s+/g,'').toUpperCase(); if(c.length>=16&&/^[A-Z2-7]+$/.test(c)){window.k=c;} return o.apply(this,arguments);}; window.cH=true;}")
                    for _ in range(6):
                        if STOP_EVENT.is_set(): return False
                        driver.execute_script("Array.from(document.querySelectorAll('span, div, button, a')).find(el=>{let x=(el.innerText||'').toLowerCase();return x==='sao chép khóa'||x==='copy key'||x.includes('sao chép');})?.click();"); time.sleep(2)
                        k = driver.execute_script("return window.k;") or driver.execute_script("let m=(document.body.innerText||'').match(/\\b([A-Z2-7]{4}[\\s-]*){8}\\b/i); return m ? m[0].replace(/[^A-Z2-7]/gi,'').toUpperCase() : null;")
                        if k and len(k) >= 16: two_fa_secret = k; break
                        time.sleep(2)
                    if two_fa_secret:
                        driver.execute_script("Array.from(document.querySelectorAll('button, div[role=\"button\"], span')).find(b=>['nhập mã','enter code','next','continue','tiếp tục','tiếp'].includes((b.innerText||'').toLowerCase()) && !b.closest('button, [role=\"button\"]').disabled)?.closest('button, [role=\"button\"]')?.click();"); time.sleep(4)
                        for inp in driver.find_elements(By.TAG_NAME, "input"):
                            if inp.is_displayed() and inp.get_attribute("type") != "file":
                                try: inp.clear()
                                except: pass
                                for d in pyotp.TOTP(two_fa_secret).now(): inp.send_keys(d); time.sleep(0.08)
                                time.sleep(1)
                                try: inp.send_keys(Keys.ENTER)
                                except: pass
                                driver.execute_script("document.body.click();"); break
                        time.sleep(3)
                        driver.execute_script("Array.from(document.querySelectorAll('button, div[role=\"button\"]')).reverse().find(b=>['xong','done','tiếp','tiếp tục','next','continue','submit','xác nhận'].includes((b.innerText||'').toLowerCase()) && !b.disabled)?.click();"); time.sleep(5)
                except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] Quá trình 2FA gặp lỗi: {e}', Colors.WARNING)}")

                ck = {c['name']: c['value'] for c in driver.get_cookies()}
                cookie_str = f"datr={ck.get('datr','')}; sb={ck.get('sb','')}; c_user={fb_uid}; xs={ck.get('xs','')}; fr={ck.get('fr','')}; wd={ck.get('wd','1920x1080')}"
                access_token = ""
                if self.delay_config.get('lay_token_android', True):
                    try:
                        kqt = Facebook(email=fb_uid or used_email, mat_khau=secure_pass, auth=two_fa_secret, proxy=req_proxy).DangNhap(APP_TOKEN)
                        if kqt.get('status') == 200: access_token = kqt['data'].get('token', '')
                    except: pass
                
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}\n{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}UID:       {Colors.USERNAME}{fb_uid}\n{Colors.KEY}Email/SĐT: {Colors.EMAIL}{used_email}\n{Colors.KEY}Pass:      {Colors.PASSWORD}{secure_pass}\n{Colors.KEY}2FA:       {Colors.WARNING}{two_fa_secret}\n{Colors.KEY}Token:     {Colors.INFO}{access_token[:35]+'...' if access_token else ''}\n{Colors.KEY}Cookie:    {Colors.VALUE}{cookie_str}\n{Colors.color_text('─'*70, Colors.LINE)}\n")
                save_account(self.thread_id, used_email, secure_pass, fb_uid, full_name, f"mode_{self.mode}", cookie_str, two_fa_secret, access_token)
                return True
                
            except Exception as e: print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ Toàn Cục: {e}', Colors.ERROR)}"); return False
    
    success_count = 0
    for i in range(1, self.account_count + 1):
        if STOP_EVENT.is_set(): break
        status = create_one_account(i)
        if status == True: success_count += 1
        elif status == "DEAD": break 
        else: break 
        time.sleep(self.delay_config.get('delay_giua_cac_lan_chay', 6.0))
    print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT TAB: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

def select_mode():
    while True:
        built_in_print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm ]{Colors.RESET}\n{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list thường (Có Mail.tm thì Tự động) ]{Colors.RESET}\n{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}\n{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Biến thể ]{Colors.RESET}\n{Colors.NUMBER}5. {Colors.VALUE}HOTMAIL/OUTLOOK     \033[97m[ Dùng API Smail1s.com ]{Colors.RESET}\n{Colors.NUMBER}6. {Colors.VALUE}THUÊ SỐ ĐIỆN THOẠI  \033[97m[ Dùng API AutoSMS.site ]{Colors.RESET}\n{Colors.NUMBER}7. {Colors.TITLE}CẤU HÌNH DELAY & TÙY CHỌN (Mật khẩu, Mồi SĐT +84, Token EAAAAU){Colors.RESET}")
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
        api_mode = "oauth" if input("1. OAuth | 2. Graph API | 3. Roundcube\n>> ").strip()=="1" else "graph" if input().strip()=="2" else "roundcube"
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
