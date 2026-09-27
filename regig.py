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

# BIẾN TOÀN CỤC ĐỂ DỪNG TOOL
STOP_EVENT = threading.Event()
CONFIG_FILE = "config_gmail.json"

# ========== CÀI ĐẶT MÀU RGB TOÀN CỤC ==========
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

try:
    import requests
    import uiautomator2 as u2
except ImportError:
    print(f"{Colors.color_text('Đang cài đặt thư viện thiếu...', Colors.WARNING)}")
    os.system("pip install requests uiautomator2 numpy opencv-python")
    import requests
    import uiautomator2 as u2

# ========== HÀM CƠ BẢN VÀ LƯU TRỮ CẤU HÌNH ==========
def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.BANNER1} ██░ ██  █    ██  ▓██   ██▓   ██▒   █▓   ▄▀▄  
{Colors.BANNER2}▓██░ ██▒ ██  ▓██▒  ▒██  ██▒  ▓██░   █▒ █    ██ 
{Colors.BANNER3}▒██▀▀██░ ▓██  ▒██░  ▒██ ██░   ▓██  █▒░ ██  ▓██▒
{Colors.BANNER4}░▓█ ░██  ▓▓█  ░██░  ░ ▐██▓░    ▒██ █░░ ▓██  ▒██░
{Colors.BANNER5}░▓█▒░██▓ ▒▒█████▓   ░ ██▒▓░     ▒▀█░   ▓▓█  ░██░
{Colors.RESET}""")
    print(f"{Colors.DEVICE_INFO}[</>] {Colors.KEY}ADMIN: {Colors.VALUE}HUY VŨ   {Colors.DEVICE_INFO}Phiên Bản: {Colors.VALUE}v7.8 (Auto Tùy Chỉnh Đổi IP + Lưu Mật Khẩu){Colors.RESET}")
    print(f"{Colors.LINE}{'─'*70}{Colors.RESET}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except: pass

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
            f.write(f"{email}|{password}|{username}|{full_name}|{cookie}\n")
    except:
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

# ========== GMAIL IMAP SERVICE (DOT TRICK & MULTI GMAIL) ==========
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
            print(f"{Colors.color_text(f'Lỗi đăng nhập IMAP cho {self.base_email}', Colors.ERROR)}")
            return False

    def decode_mime(self, value):
        if not value: return ""
        parts = decode_header(value)
        out = []
        for text, enc in parts:
            if isinstance(text, bytes):
                try: 
                    out.append(text.decode(enc or "utf-8", errors="replace"))
                except: 
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

    def get_otp_code(self, target_email, timeout=120):
        if not self.mail:
            if not self.connect(): 
                return None
                
        start_time = time.time()
        while time.time() - start_time < timeout:
            if STOP_EVENT.is_set(): 
                return None
                
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    for uid in reversed(uids[-8:]):
                        if uid in self.seen_uids: 
                            continue
                            
                        status, fetch_data = self.mail.uid("fetch", uid, "(RFC822)")
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
                                
                                # Bộ lọc: Mail phải gửi đến đúng biến thể hiện tại
                                if target_email.lower() not in to_addr:
                                    continue
                                    
                                if "instagram" in subject or "instagram" in from_addr:
                                    self.seen_uids.add(uid) 
                                    body = self.get_text(msg)
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match: 
                                        return match.group(1)
            except: 
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

# ========== MODULES CŨ (MAIL.TM, DỌN RÁC, TÊN) ==========
class MailService:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.domain = None
        
    def get_domain(self):
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=10)
            if r.status_code == 200: 
                self.domain = r.json()['hydra:member'][0]['domain']
                return self.domain
        except: 
            return None
            
    def create_account(self, address=None):
        if not self.domain and not self.get_domain(): 
            return None
        name = address if address else f"user_{uuid.uuid4().hex[:8]}"
        try:
            r = requests.post(f"{self.base_url}/accounts", json={"address": f"{name}@{self.domain}", "password": "TempPass123!"}, timeout=10)
            if r.status_code == 201: 
                self.email_address = r.json()['address']
                return self.email_address
        except: 
            return None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: 
            self.email_address = email
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except: 
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
            except: 
                pass
            time.sleep(5)
        return None

class AppCleaner:
    def __init__(self, d, serial):
        self.d = d
        self.serial = serial
        self.package_name = "mark.via.gp"

    def clear_via_data(self):
        if STOP_EVENT.is_set(): 
            return False
            
        print(f"{Colors.color_text(f'[{self.serial}] ========== DỌN RÁC VIA BROWSER ==========', Colors.TITLE)}")
        
        # Đóng đa nhiệm
        try:
            self.d.press("recent")
            time.sleep(1.5)
            size = self.d.window_size()
            for _ in range(3): 
                self.d.swipe(size[0]*0.5, size[1]*0.6, size[0]*0.5, size[1]*0.1, duration=0.3)
                time.sleep(0.5)
            self.d.press("home")
            time.sleep(1)
        except: 
            pass
        
        # Dừng và vào cài đặt App
        self.d.app_stop(self.package_name)
        time.sleep(1.5)
        
        try: 
            subprocess.run(f"adb -s {self.serial} shell am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{self.package_name}", shell=True, timeout=8)
        except: 
            pass
        time.sleep(2.5)
        
        # Bấm Storage
        for _ in range(2): 
            self.d.swipe(size[0]*0.5, size[1]*0.8, size[0]*0.5, size[1]*0.3, duration=0.3)
            
        for sel in [{"textMatches": r"(?i).*(storage|dung lượng|bộ nhớ|storage & cache).*"}]:
            if self.d(**sel).exists(timeout=3): 
                self.d(**sel).click()
                break
        else: 
            self.d.click(int(size[0]*0.5), int(size[1]*0.6))
        time.sleep(2)
        
        # Bấm Clear Data
        for sel in [{"textMatches": r"(?i).*(clear data|clear storage|xóa dữ liệu|xóa bộ nhớ).*"}]:
            if self.d(**sel).exists(timeout=3): 
                self.d(**sel).click()
                break
        else: 
            self.d.click(int(size[0]*0.5), int(size[1]*0.75))
        time.sleep(1.5)
        
        # Bấm Confirm
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

# ========== SETUP TOOL ==========
def select_devices():
    try:
        out = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        devices = [line.split("\t")[0] for line in out.strip().splitlines()[1:] if "\tdevice" in line]
    except: 
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
            c = int(input(f"{Colors.KEY}Chọn thiết bị: {Colors.RESET}"))
            if 1 <= c <= len(devices): 
                return [devices[c-1]]
            elif c == len(devices) + 1: 
                return devices
        except: 
            pass

def select_mode():
    print(f"{Colors.NUMBER}1. {Colors.VALUE}TỰ ĐỘNG HOÀN TOÀN   \033[97m[ Dùng email Mail.tm tự tạo ]{Colors.RESET}")
    print(f"{Colors.NUMBER}2. {Colors.VALUE}NHẬP TAY/FILE EMAIL \033[97m[ Dùng list email thường ]{Colors.RESET}")
    print(f"{Colors.NUMBER}3. {Colors.VALUE}NHIỀU GMAIL (IMAP)  \033[97m[ Dùng file txt: email|pass ]{Colors.RESET}")
    print(f"{Colors.NUMBER}4. {Colors.VALUE}GMAIL DOT TRICK     \033[97m[ 1 Gmail gốc -> Nhiều biến thể ]{Colors.RESET}")
    
    while True:
        choice = input(f"{Colors.KEY}Nhập lựa chọn \033[97m[ 1, 2, 3 hoặc 4 ]: {Colors.RESET}").strip()
        if choice == "1": return "auto"
        elif choice == "2": return "manual"
        elif choice == "3": return "multi_gmail"
        elif choice == "4": return "dot_trick"

# ========== MAIN THREAD ==========
class starts(threading.Thread):
    def __init__(self, device, mode, account_count, ip_change_freq, manual_emails=None, manual_password=None, multi_gmail_list=None, base_gmail=None, app_password=None):
        super().__init__()
        self.device = device
        self.mode = mode
        self.account_count = account_count
        self.ip_change_freq = ip_change_freq
        self.manual_emails = manual_emails if manual_emails else []
        self.manual_password = manual_password
        self.multi_gmail_list = multi_gmail_list if multi_gmail_list else []
        self.base_gmail = base_gmail
        self.app_password = app_password
    
    def run(self):
        def create_one_account(serial, account_index):
            if STOP_EVENT.is_set(): 
                return False
                
            print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
            print(f"{Colors.color_text(f'[{serial}]  BẮT ĐẦU TẠO TÀI KHOẢN THỨ {account_index}', Colors.TITLE)}")
            
            used_email = ""
            imap_service = None
            mail_service = None
            
            full_name, username = VietnameseNameGenerator()
            secure_pass = "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%") for _ in range(12))

            # --- SETUP EMAIL DỰA THEO CHẾ ĐỘ ---
            if self.mode == "auto":
                mail_service = MailService()
                used_email = mail_service.create_account(username)
                if not used_email: return False
                mail_service.authenticate()
                
            elif self.mode == "manual":
                if not self.manual_emails: 
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã hết email trong danh sách!', Colors.ERROR)}")
                    return False
                used_email = self.manual_emails.pop(0)
                if "mail.tm" in used_email.lower():
                    mail_service = MailService()
                    mail_service.authenticate(used_email, self.manual_password or "TempPass123!")
                    
            elif self.mode == "multi_gmail":
                if not self.multi_gmail_list: 
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã dùng hết list Multi-Gmail!', Colors.ERROR)}")
                    return False
                used_email, app_pass = self.multi_gmail_list.pop(0)
                imap_service = GmailIMAPService(used_email, app_pass)
                
            elif self.mode == "dot_trick":
                if not self.manual_emails: 
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Đã dùng hết biến thể Dot Trick!', Colors.ERROR)}")
                    return False
                used_email = self.manual_emails.pop(0)
                imap_service = GmailIMAPService(self.base_gmail, self.app_password)

            print(f"{Colors.color_text(f'[{serial}] Đang dùng Email: {used_email}', Colors.INFO)}")

            # --- VÀO VIỆC TRÊN ĐIỆN THOẠI ---
            try:
                d = u2.connect(serial)
                try: 
                    d.healthcheck()
                except: 
                    pass
                
                # Dọn rác
                if not AppCleaner(d, serial).clear_via_data(): 
                    return False
                if STOP_EVENT.is_set(): 
                    return False
                
                # Mở trình duyệt
                print(f"{Colors.color_text(f'[{serial}] Đang mở Via Browser...', Colors.INFO)}")
                d.app_start("mark.via.gp", stop=True)
                time.sleep(4)
                
                if d(textMatches=r"(?i)Đồng ý|Agree|Accept").exists(timeout=2): 
                    d(textMatches=r"(?i)Đồng ý|Agree|Accept").click()
                if d(textMatches=r"(?i)Bỏ qua|Skip").exists(timeout=2): 
                    d(textMatches=r"(?i)Bỏ qua|Skip").click()

                # Bật chế độ Desktop
                print(f"{Colors.color_text(f'[{serial}] Đang bật chế độ Trang máy tính...', Colors.INFO)}")
                try:
                    size = d.window_size()
                    d.click(size[0]*0.90, size[1]*0.93)
                    time.sleep(1.5)
                    
                    if d(textMatches=r"(?i).*Trang máy tính.*|.*Desktop.*").exists(timeout=2): 
                        d(textMatches=r"(?i).*Trang máy tính.*|.*Desktop.*").click()
                    else: 
                        d.click(size[0]*0.5, size[1]*0.80)
                        
                    time.sleep(1.5)
                    d.click(size[0]*0.5, size[1]*0.20)
                except: 
                    pass

                # Truy cập Web
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
                else: 
                    return False

                if STOP_EVENT.is_set(): 
                    return False

                # --- ĐIỀN FORM ĐĂNG KÝ ---
                print(f"{Colors.color_text(f'[{serial}] Đang điền form đăng ký...', Colors.INFO)}")
                time.sleep(3)
                
                # Điền Email
                print(f"{Colors.color_text(f'[{serial}] Nhập Email...', Colors.INFO)}")
                if d(textMatches=r"(?i).*email.*").exists(timeout=2): 
                    d(textMatches=r"(?i).*email.*").click()
                else: 
                    d(className="android.widget.EditText")[0].click()
                    
                time.sleep(0.5)
                d.send_keys(used_email)
                time.sleep(1)
                d.press("back")
                time.sleep(1)

                # Điền Pass
                print(f"{Colors.color_text(f'[{serial}] Nhập Mật khẩu...', Colors.INFO)}")
                if d(textMatches=r"(?i).*Mật khẩu.*|.*Password.*").exists(timeout=2): 
                    d(textMatches=r"(?i).*Mật khẩu.*|.*Password.*").click()
                else:
                    edits = d(className="android.widget.EditText")
                    if edits.count > 1: 
                        edits[1].click()
                    else: 
                        edits[0].click()
                        
                time.sleep(0.5)
                d.send_keys(secure_pass)
                time.sleep(1)
                d.press("back")
                time.sleep(1.5)

                # Vuốt màn hình nhẹ để lòi mục Ngày Sinh
                d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.4, duration=0.5)
                time.sleep(1.5)
                
                # Random Ngày, Tháng, Năm (2-7)
                print(f"{Colors.color_text(f'[{serial}] Chọn Ngày, Tháng, Năm sinh...', Colors.INFO)}")
                
                if d(textMatches=r"(?i)^\s*Ngày\s*$|^\s*Day\s*$").exists(timeout=2):
                    d(textMatches=r"(?i)^\s*Ngày\s*$|^\s*Day\s*$").click()
                    time.sleep(1.5)
                    random_day = str(random.randint(2, 7))
                    if d(text=random_day).exists(timeout=2): 
                        d(text=random_day).click()
                    else: 
                        d.click(size[0]*0.25, size[1]*0.4) 
                    time.sleep(1)

                if d(textMatches=r"(?i)^\s*Tháng\s*$|^\s*Month\s*$").exists(timeout=2):
                    d(textMatches=r"(?i)^\s*Tháng\s*$|^\s*Month\s*$").click()
                    time.sleep(1.5)
                    random_m = str(random.randint(2, 7))
                    if d(text=f"Tháng {random_m}").exists(timeout=2): 
                        d(text=f"Tháng {random_m}").click()
                    elif d(text=random_m).exists(timeout=2): 
                        d(text=random_m).click()
                    else: 
                        d.click(size[0]*0.50, size[1]*0.4)
                    time.sleep(1)

                if d(textMatches=r"(?i)^\s*Năm\s*$|^\s*Year\s*$").exists(timeout=2):
                    d(textMatches=r"(?i)^\s*Năm\s*$|^\s*Year\s*$").click()
                    time.sleep(1.5)
                    for _ in range(random.randint(4, 7)):
                        d.swipe(size[0]*0.85, size[1]*0.8, size[0]*0.85, size[1]*0.4, duration=0.5)
                        time.sleep(0.3)
                    d.click(size[0]*0.85, size[1]*0.5)
                    time.sleep(1)

                # Vuốt nhẹ tiếp để lòi form Name và User
                d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.5, duration=0.6)
                time.sleep(1.5)

                # Điền Name
                print(f"{Colors.color_text(f'[{serial}] Nhập Tên đầy đủ...', Colors.INFO)}")
                if d(textMatches=r"(?i).*Tên đầy đủ.*").exists(timeout=2): 
                    d(textMatches=r"(?i).*Tên đầy đủ.*").click()
                else: 
                    d(className="android.widget.EditText")[-2].click()
                    
                time.sleep(0.5)
                d.send_keys(full_name)
                time.sleep(1)
                d.press("back")
                time.sleep(1.5)

                # Điền Username
                print(f"{Colors.color_text(f'[{serial}] Nhập Username...', Colors.INFO)}")
                if d(textMatches=r"(?i).*Tên người dùng.*").exists(timeout=2): 
                    d(textMatches=r"(?i).*Tên người dùng.*").click()
                else: 
                    d(className="android.widget.EditText")[-1].click()
                    
                time.sleep(0.5)
                d.clear_text()
                time.sleep(0.5)
                d.send_keys(username)
                time.sleep(1)
                d.press("back")
                time.sleep(1.5)

                # Bấm Submit
                print(f"{Colors.color_text(f'[{serial}] Bấm Gửi/Đăng ký...', Colors.INFO)}")
                if d(className="android.widget.Button", textMatches=r"(?i).*Đăng ký.*|.*Sign up.*").exists(timeout=2): 
                    d(className="android.widget.Button", textMatches=r"(?i).*Đăng ký.*|.*Sign up.*").click()
                else: 
                    d.click(size[0]*0.5, size[1]*0.85)

                # Vuốt lộ form OTP
                print(f"{Colors.color_text(f'[{serial}] Đợi 5s cuộn trang lấy form OTP...', Colors.INFO)}")
                time.sleep(5) 
                d.swipe(size[0]*0.5, size[1]*0.3, size[0]*0.5, size[1]*0.8, duration=0.6)
                time.sleep(1.5)

                if STOP_EVENT.is_set(): 
                    return False

                # --- QUÉT MÃ OTP TỪ MAIL ---
                print(f"{Colors.color_text(f'[{serial}] Đang quét mã OTP từ mail...', Colors.INFO)}")
                otp_code = None
                
                if self.mode in ["multi_gmail", "dot_trick"]:
                    otp_code = imap_service.get_otp_code(target_email=used_email, timeout=120)
                elif self.mode == "auto" or (self.mode == "manual" and mail_service and mail_service.token):
                    otp_code = mail_service.get_otp_code(timeout=120)
                
                if not otp_code: 
                    print(f"{Colors.color_text(f'[{serial}] Lỗi: Không nhận được OTP. Bỏ qua acc!', Colors.ERROR)}")
                    return False
                
                # --- NGÂM 90S OTP BYPASS ---
                print(f"{Colors.color_text(f'[{serial}] Đã bắt được mã OTP: {otp_code}!', Colors.SUCCESS)}")
                print(f"{Colors.color_text(f'[{serial}] Đang ngâm OTP 90s để bypass Bot...', Colors.WARNING)}")
                
                for w in range(90, 0, -10):
                    if STOP_EVENT.is_set(): 
                        return False
                    print(f"{Colors.color_text(f'[{serial}] Còn {w}s...', Colors.INFO)}")
                    time.sleep(10)
                
                if STOP_EVENT.is_set(): 
                    return False
                    
                # Điền OTP
                print(f"{Colors.color_text(f'[{serial}] Đã ngâm xong, tiến hành nhập OTP...', Colors.SUCCESS)}")
                otp_input = d(className="android.widget.EditText")
                
                if otp_input.exists(timeout=5):
                    otp_input.click()
                    time.sleep(0.5)
                    d.send_keys(otp_code)
                    time.sleep(1.5)
                    
                    # Ẩn bàn phím
                    d.click(size[0]*0.1, size[1]*0.3)
                    time.sleep(1.5)
                    
                    # Xác nhận
                    if d(className="android.widget.Button", textMatches=r"(?i).*Tiếp.*|.*Xác nhận.*").exists(timeout=3): 
                        d(className="android.widget.Button", textMatches=r"(?i).*Tiếp.*|.*Xác nhận.*").click()
                    else: 
                        d.click(size[0]*0.5, size[1]*0.5)
                        
                    print(f"{Colors.color_text(f'[{serial}] Đang chờ đúng 30s để load vào nick...', Colors.WARNING)}")
                    time.sleep(30)
                
                # --- LẤY COOKIE ---
                print(f"{Colors.color_text(f'[{serial}] Đang mở menu để lấy Cookie...', Colors.INFO)}")
                cookie = ""
                try:
                    d.click(size[0]*0.1, size[1]*0.08)
                    time.sleep(2)
                    
                    if d(textMatches=r"(?i).*Xem cookie.*").exists(timeout=3):
                        d(textMatches=r"(?i).*Xem cookie.*").click()
                        time.sleep(2)
                        for elem in d(className="android.widget.TextView"):
                            if "csrftoken=" in str(elem.get_text()): 
                                cookie = elem.get_text()
                                break
                        # Thoát menu cookie
                        d.click(size[0]*0.5, size[1]*0.1)
                except: 
                    pass

                # --- SUCCESS ---
                print(f"\n{Colors.color_text('─'*70, Colors.LINE)}")
                print(f"{Colors.color_text(f'[{serial}] DONE ACC {account_index}!', Colors.SUCCESS)}")
                print(f"{Colors.KEY}Mail: {Colors.EMAIL}{used_email}{Colors.RESET}")
                print(f"{Colors.KEY}Pass: {Colors.PASSWORD}{secure_pass}{Colors.RESET}")
                print(f"{Colors.KEY}User: {Colors.USERNAME}{username}{Colors.RESET}")
                print(f"{Colors.KEY}Cookie: {Colors.VALUE}{cookie if cookie else 'Trống'}{Colors.RESET}")
                print(f"{Colors.color_text('─'*70, Colors.LINE)}\n")
                
                save_account(serial, used_email, secure_pass, username, full_name, self.mode, cookie)
                return True
                
            except Exception as e: 
                return False
        
        # --- VÒNG LẶP CHO TỪNG THIẾT BỊ ---
        success_count = 0
        for i in range(1, self.account_count + 1):
            if STOP_EVENT.is_set():
                print(f"{Colors.color_text(f'[{self.device}] Lệnh dừng được kích hoạt. Đang thoát luồng...', Colors.WARNING)}")
                break
            
            if create_one_account(self.device, i):
                success_count += 1
            
            # Auto đảo mạng sau tùy chỉnh acc
            if i < self.account_count and not STOP_EVENT.is_set():
                if self.ip_change_freq > 0 and i % self.ip_change_freq == 0: 
                    toggle_airplane_mode(self.device)
                else: 
                    time.sleep(random.uniform(10, 20))
        
        print(f"\n{Colors.color_text(f'[{self.device}] TỔNG KẾT: {success_count}/{self.account_count} THÀNH CÔNG', Colors.TITLE)}")

# ========== MAIN ENTRY POINT ==========
if __name__ == "__main__":
    banner()
    print(f"{Colors.color_text('MẸO: Bạn có thể ấn tổ hợp phím Ctrl + C bất cứ lúc nào để DỪNG TOOL an toàn.', Colors.WARNING)}\n")
    
    # Load cấu hình
    config_data = load_config()
    
    mode = select_mode()
    
    manual_emails = []
    multi_gmail_list = []
    manual_password = None
    base_gmail = None
    app_password = None

    if mode == "manual":
        email_input = input(f"{Colors.KEY}Nhập list email (cách nhau dấu phẩy) HOẶC đường dẫn file .txt: {Colors.RESET}").strip().strip('"').strip("'")
        if os.path.isfile(email_input):
            with open(email_input, 'r', encoding='utf-8') as f: 
                manual_emails = [line.strip() for line in f if line.strip()]
            print(f"{Colors.color_text(f'Đã tải {len(manual_emails)} email từ file.', Colors.INFO)}")
        else: 
            manual_emails = [e.strip() for e in email_input.split(",") if e.strip()]
            
        if any("mail.tm" in e.lower() for e in manual_emails): 
            manual_password = input(f"{Colors.KEY}Nhập mật khẩu (mail.tm): {Colors.RESET}").strip() or "TempPass123!"

    elif mode == "multi_gmail":
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
            file_path = input(f"{Colors.KEY}Nhập đường dẫn file txt (Định dạng: email|app_password): {Colors.RESET}").strip().strip('"').strip("'")
            config_data["multi_gmail_path"] = file_path
            save_config(config_data)
            
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = re.split(r'[|:]', line.strip())
                    if len(parts) >= 2: 
                        multi_gmail_list.append((parts[0].strip(), parts[1].strip()))
            print(f"{Colors.color_text(f'Đã tải thành công {len(multi_gmail_list)} Gmail từ file!', Colors.SUCCESS)}")
        else: 
            print(f"{Colors.color_text('Lỗi: Không tìm thấy file txt!', Colors.ERROR)}")
            sys.exit()

    elif mode == "dot_trick":
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
            base_gmail = input(f"{Colors.KEY}Nhập Gmail gốc (VD: huyvu@gmail.com): {Colors.RESET}").strip()
            app_password = input(f"{Colors.KEY}Nhập App Password (16 ký tự): {Colors.RESET}").strip()
            # Lưu lại cấu hình
            config_data["dot_trick_email"] = base_gmail
            config_data["dot_trick_app_pass"] = app_password
            save_config(config_data)
            
        manual_emails = generate_dot_variants(base_gmail)
        print(f"{Colors.color_text(f'Đã tạo ra {len(manual_emails)} biến thể.', Colors.SUCCESS)}")

    while True:
        try:
            account_count = int(input(f"\n{Colors.KEY}Nhập số lượng tài khoản cần tạo \033[97m[VD: 100]: {Colors.RESET}").strip())
            break
        except: pass
        
    ip_change_freq = 4
    while True:
        try:
            freq_str = input(f"{Colors.KEY}Sau bao nhiêu acc thành công thì Đổi IP? (Nhập 0 để Tắt) \033[97m[Mặc định: 4]: {Colors.RESET}").strip()
            if not freq_str:
                break # Mặc định là 4
            ip_change_freq = int(freq_str)
            break
        except: pass

    devices = select_devices()
    
    if devices:
        try:
            threads = [starts(serial, mode, account_count, ip_change_freq, manual_emails, manual_password, multi_gmail_list, base_gmail, app_password) for serial in devices]
            for t in threads: t.start()
            for t in threads: t.join()
            print(f"\n{Colors.color_text('  AUTO HOÀN THÀNH TOÀN BỘ!  ', Colors.SUCCESS)}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.color_text('!!! PHÁT HIỆN LỆNH DỪNG (CTRL+C) - ĐANG HỦY TIẾN TRÌNH !!!', Colors.ERROR)}")
            STOP_EVENT.set() 
            for t in threads: t.join() 
            print(f"{Colors.color_text('Tool đã dừng an toàn.', Colors.SUCCESS)}")
            sys.exit(0)
