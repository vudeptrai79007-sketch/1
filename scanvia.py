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

# ===== THƯ VIỆN DRISSIONPAGE & REQUESTS =====
try:
    from DrissionPage import ChromiumOptions, ChromiumPage
    import requests
except ImportError:
    print("Đang cài đặt thư viện thiếu...")
    os.system("pip install DrissionPage requests")
    from DrissionPage import ChromiumOptions, ChromiumPage
    import requests

# BIẾN TOÀN CỤC
STOP_EVENT = threading.Event()
OTP_LOCK = threading.Lock() 
DATA_LOCK = threading.Lock()
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
██║   ██║██╔══██║██╔══██║██║   ██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝    ╚═╝╚══════╝
{Colors.RESET}""")
    print(f"{Colors.INFO}Phiên Bản: v13.0 (DRISSIONPAGE & CHIA LƯỚI MÀN HÌNH TỰ ĐỘNG){Colors.RESET}")
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
THÔNG TIN TÀI KHOẢN INSTAGRAM (DRISSIONPAGE)
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
        
        payload = {"mode": self.api_mode, "data": self.data_line}
        headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        
        last_logged = ""
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): return None
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
                            for msg in messages:
                                subject = str(msg.get("subject", "")).lower()
                                from_sender = str(msg.get("from", "")).lower()
                                raw_msg = str(msg.get("message", ""))
                                code_field = str(msg.get("code", "")).strip()
                                
                                is_ig = ("instagram" in subject) or ("instagram" in from_sender) or ("instagram" in raw_msg.lower())
                                if is_ig:
                                    if code_field and code_field.isdigit() and len(code_field) == 6:
                                        if code_field not in self.seen_codes:
                                            return code_field
                                    match_subj = re.search(r'\b(\d{6})\b', subject)
                                    if match_subj:
                                        code = match_subj.group(1)
                                        if code not in self.seen_codes: return code
                                    clean_text = re.sub(r'<[^>]+>', ' ', raw_msg)
                                    match_body = re.search(r'\b(\d{6})\b', clean_text)
                                    if match_body:
                                        code = match_body.group(1)
                                        if code not in self.seen_codes: return code
            except Exception: pass
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

# ==================== HÀM HỎI TRƯỚC KHI ĐÓNG ====================
def ask_before_close(page, thread_id):
    if page:
        with OTP_LOCK:
            print(f"\n{Colors.color_text(f'[{thread_id}] Bạn có muốn đóng trình duyệt không? (y/n): ', Colors.WARNING)}", end="")
            choice = input().strip().lower()
            if choice == 'y':
                try: 
                    page.quit()
                    print(f"{Colors.color_text(f'[{thread_id}] Đã đóng trình duyệt an toàn.', Colors.SUCCESS)}")
                except: pass
            else:
                print(f"{Colors.color_text(f'[{thread_id}] Đã giữ trình duyệt mở.', Colors.INFO)}")

# ==================== MAIN THREAD (DRISSIONPAGE & CHIA LƯỚI) ====================
class starts(threading.Thread):
    def __init__(self, thread_index, total_threads, mode, account_count, data_source, manual_password=None, base_gmail=None, app_password=None, api_mode=None):
        super().__init__()
        self.thread_index = thread_index
        self.thread_id = f"Tab-{thread_index}"
        self.total_threads = total_threads
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

            page = None
            try:
                # Cấu hình DrissionPage ẩn danh và tự động chia lưới cửa sổ thu nhỏ phủ màn hình
                co = ChromiumOptions()
                co.incognito(True) # Chế độ ẩn danh
                co.set_argument('--mute-audio')
                co.set_argument('--disable-notifications')
                
                # Tính toán kích thước và vị trí chia lưới (Grid) phủ kín màn hình
                # Giả định màn hình chuẩn Full HD (1920x1080)
                screen_w, screen_h = 1920, 1040 
                cols = 2 if self.total_threads > 1 else 1
                if self.total_threads > 4: cols = 3
                rows = (self.total_threads + cols - 1) // cols
                
                win_w = screen_w // cols
                win_h = screen_h // rows
                
                idx = self.thread_index - 1
                pos_x = (idx % cols) * win_w
                pos_y = (idx // cols) * win_h
                
                co.set_window_size(win_w, win_h)
                co.set_window_position(pos_x, pos_y)

                page = ChromiumPage(addr_or_opts=co)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang truy cập Instagram Web...', Colors.INFO)}")
                page.get("https://www.instagram.com/accounts/emailsignup/")
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang chờ trang tải hoàn tất (8s)...', Colors.WARNING)}")
                time.sleep(8)
                
                # Xử lý nút Cookie nếu có
                try:
                    btn_cookie = page.ele('xpath://button[contains(text(), "Allow") or contains(text(), "Accept") or contains(text(), "Cho phép")]', timeout=2)
                    if btn_cookie: btn_cookie.click()
                except: pass

                current_year = str(BASE_YEAR + random.randint(-3, 3))
                if int(current_year) > 2005: current_year = "2005"
                current_day = str(random.randint(2, 28))
                current_month = str(random.randint(1, 12))
                
                BASE_YEAR -= 1
                if BASE_YEAR < 1990: BASE_YEAR = random.randint(1995, 2005)

                # Điền thông tin form bằng DrissionPage
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang điền thông tin đăng ký...', Colors.INFO)}")
                
                inputs = page.eles('tag:input')
                if len(inputs) >= 4:
                    inputs[0].input(used_email)
                    inputs[1].input(secure_pass)
                    inputs[2].input(full_name)
                    
                    # Xử lý Username thông minh
                    inputs[3].click()
                    time.sleep(1)
                    inputs[3].clear()
                    inputs[3].input(username)
                else:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Không tìm đủ ô input!', Colors.ERROR)}")
                    ask_before_close(page, self.thread_id)
                    return False

                # Chọn ngày tháng năm sinh bằng cấu hình combobox
                try:
                    combos = page.eles('xpath://*[@role="combobox"]')
                    if len(combos) >= 3:
                        combos[0].click(); time.sleep(0.3); page.ele(f'xpath://div[text()="{current_day}"] | //span[text()="{current_day}"]', timeout=2).click()
                        combos[1].click(); time.sleep(0.3); page.ele(f'xpath://div[contains(text(), "{current_month}")] | //span[contains(text(), "{current_month}")]', timeout=2).click()
                        combos[2].click(); time.sleep(0.3); page.ele(f'xpath://div[text()="{current_year}"] | //span[text()="{current_year}"]', timeout=2).click()
                except: pass

                print(f"{Colors.color_text(f'[{self.thread_id}] Đã điền xong. Đợi 5s trước khi bấm Đăng ký...', Colors.WARNING)}")
                time.sleep(5)

                uid_moc = 0
                if self.mode in ["3", "4"] and imap_service:
                    uid_moc = imap_service.get_latest_uid()
                elif self.mode == "5" and hotmail_service:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Đang quét hộp thư để loại trừ mã cũ...', Colors.INFO)}")
                    hotmail_service.init_baseline()

                # Bấm nút Gửi / Đăng ký qua JS của DrissionPage
                print(f"{Colors.color_text(f'[{self.thread_id}] Đang bấm nút Đăng ký...', Colors.INFO)}')
                page.run_js("""
                    const btn = Array.from(document.querySelectorAll('button, div[role="button"]')).find(b => {
                        const t = (b.innerText || "").trim().toLowerCase();
                        return t === "gửi" || t === "đăng ký" || t === "sign up" || t.includes("sign");
                    });
                    if(btn) { btn.disabled = false; btn.click(); }
                """)
                
                print(f"{Colors.color_text(f'[{self.thread_id}] Đã gửi form, chờ chuyển sang trang OTP (15s)...', Colors.SUCCESS)}")
                time.sleep(15)

                # Lấy mã OTP & Ngâm form
                otp_code = None
                start_otp_wait = time.time()
                
                if self.mode == "2" and not (mail_service and mail_service.token):
                    with OTP_LOCK:
                        print(f"\n{Colors.color_text(f'[{self.thread_id}] MỜI SẾP NHẬP OTP CHO [{used_email}] TỪ BÀN PHÍM:', Colors.SUCCESS)}")
                        otp_code = input(">> ").strip()
                else:
                    target_wait = 60 if self.mode in ["3", "4", "5"] else 0
                    if target_wait > 0:
                        print(f"{Colors.color_text(f'[{self.thread_id}] Đang quét mã OTP và ngâm form {target_wait}s...', Colors.INFO)}")
                    
                    if self.mode == "1" or (self.mode == "2" and mail_service and mail_service.token):
                        otp_code = mail_service.get_otp_code(timeout=120)
                    elif self.mode in ["3", "4"]:
                        otp_code = imap_service.get_otp_code(target_email=used_email, since_uid=uid_moc, timeout=120)
                    elif self.mode == "5":
                        otp_code = hotmail_service.get_otp_code(timeout=120)

                if not otp_code:
                    print(f"{Colors.color_text(f'[{self.thread_id}] Lỗi: Quá 120s không lấy được mã OTP!', Colors.ERROR)}")
                    ask_before_close(page, self.thread_id)
                    return False

                if self.mode in ["3", "4", "5"]:
                    elapsed = time.time() - start_otp_wait
                    remaining = target_wait - elapsed
                    if remaining > 0:
                        for w in range(int(remaining), 0, -5):
                            if STOP_EVENT.is_set(): return False
                            time.sleep(min(5, w))

                # Điền OTP và Bấm Tiếp tục
                print(f"{Colors.color_text(f'[{self.thread_id}] Điền mã OTP: {otp_code} và Xác nhận...', Colors.SUCCESS)}")
                
                # Tìm ô nhập OTP linh hoạt bằng DrissionPage
                otp_box = page.ele('xpath://input[@name="email_confirmation_code" or @name="confirmationCode" or contains(@aria-label, "Mã") or contains(@aria-label, "Code")] | //input[@type="text"]', timeout=5)
                if otp_box:
                    otp_box.input(otp_code)
                else:
                    page.run_js(f"document.querySelector('input').value = '{otp_code}';")

                time.sleep(1.5)

                # Bấm nút Tiếp tục
                page.run_js("""
                    const nextBtn = Array.from(document.querySelectorAll('button, div[role="button"]')).find(b => {
                        const t = (b.innerText || "").trim().toLowerCase();
                        return t.includes("tiếp tục") || t.includes("next") || t.includes("xác nhận") || t.includes("confirm");
                    });
                    if(nextBtn) { nextBtn.disabled = false; nextBtn.click(); }
                """)

                print(f"{Colors.color_text(f'[{self.thread_id}] Chờ Server tạo tài khoản (20s)...', Colors.INFO)}")
                time.sleep(20)

                cookies = page.cookies()
                cookie_str = "; ".join([f"{c.get('name')}={c.get('value')}" for c in cookies])

                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{self.thread_id}] THÀNH CÔNG ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Mail: {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Pass: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie: {Colors.VALUE}{cookie_str if cookie_str else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")

                save_account(self.thread_id, used_email, secure_pass, username, full_name, f"mode_{self.mode}", cookie_str)
                
                ask_before_close(page, self.thread_id)
                return True

            except Exception as e:
                print(f"{Colors.color_text(f'[{self.thread_id}] Gặp Lỗi Ngoại Lệ: {e}', Colors.ERROR)}")
                ask_before_close(page, self.thread_id)
                return False

        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set(): break
            if create_one_account(i): success_count += 1
            time.sleep(random.uniform(3, 6))

        print(f"\n{Colors.color_text(f'[{self.thread_id}] TỔNG KẾT: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

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
        email_input = input(f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}").strip().strip('"')
        if os.path.isfile(email_input):
            with open(email_input, 'r', encoding='utf-8') as f: data_source = [line.strip() for line in f if line.strip()]
        else: data_source = [e.strip() for e in email_input.split(",") if e.strip()]
        if any("mail.tm" in e.lower() for e in data_source):
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu chung cho Mail.tm (Để trống dùng TempPass123!): {Colors.RESET}").strip()
    elif mode == "3":
        file_path = input(f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}").strip().strip('"')
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = re.split(r'[|:]', line.strip())
                    if len(parts) >= 2: data_source.append((parts[0].strip(), parts[1].strip()))
        else: sys.exit()
    elif mode == "4":
        base_gmail = input(f"{Colors.KEY}Nhập Gmail gốc (VD: test@gmail.com): {Colors.RESET}").strip()
        app_password = input(f"{Colors.KEY}Nhập App Password: {Colors.RESET}").strip()
        data_source = generate_dot_variants(base_gmail)
    elif mode == "5":
        print("1. OAuth | 2. Graph API | 3. Roundcube")
        c = input(">> ").strip()
        api_mode = "oauth" if c=="1" else "graph" if c=="2" else "roundcube"
        account_input = input(f"{Colors.KEY}Nhập file/list Hotmail: {Colors.RESET}").strip().strip('"')
        if os.path.isfile(account_input):
            with open(account_input, 'r', encoding='utf-8') as f: data_source = [line.strip() for line in f if line.strip()]
        else: data_source = [e.strip() for e in account_input.split(",") if e.strip()]

    print(f"\n{Colors.KEY}Nhập số luồng (số tab Chrome chạy cùng lúc): {Colors.RESET}")
    threads_count = int(input(">> ").strip())
    
    print(f"{Colors.KEY}Nhập số tài khoản cần tạo MỖI LUỒNG: {Colors.RESET}")
    accs_per_thread = int(input(">> ").strip())
    
    threads = []
    for i in range(threads_count):
        # Truyền thêm tổng số luồng để thuật toán tự động chia lưới màn hình
        t = starts(i+1, threads_count, mode, accs_per_thread, data_source, manual_password, base_gmail, app_password, api_mode)
        threads.append(t)
        
    for t in threads: t.start()
    
    try:
        for t in threads: t.join()
        print(f"\n{Colors.color_text('AUTO HOÀN THÀNH TOÀN BỘ!', Colors.SUCCESS)}")
    except KeyboardInterrupt:
        STOP_EVENT.set() 
        print(f"\n{Colors.color_text('Đang đóng các luồng an toàn...', Colors.WARNING)}")
        sys.exit(0)
