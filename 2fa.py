import os
import time
import subprocess
import sys
import random
import re
import pyotp
import json
import imaplib
import email
from email.header import decode_header
import requests
import uuid
import uiautomator2 as u2

# ========== BẢNG MÀU GIAO DIỆN ==========
class Colors:
    SUCCESS = "\033[92m"
    ERROR = "\033[91m"
    INFO = "\033[96m"
    WARNING = "\033[93m"
    RESET = "\033[0m"
    
def log(serial, msg, color=Colors.INFO):
    print(f"{color}[{serial}] {msg}{Colors.RESET}")

# ========== DỊCH VỤ MAIL.TM ==========
class MailService:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.token = None
        self.email_address = None
            
    def authenticate(self, email=None, password="TempPass123!"):
        if email: 
            self.email_address = email
        try:
            r = requests.post(f"{self.base_url}/token", json={"address": self.email_address, "password": password}, timeout=10)
            if r.status_code == 200: 
                self.token = r.json()['token']
                return True
        except Exception: 
            pass
        return False
            
    def get_otp_code(self, timeout=60):
        if not self.token: 
            return None
        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_id = None
        
        while time.time() - start_time < timeout:
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

# ========== DỊCH VỤ GMAIL IMAP ==========
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
        except Exception: 
            return False

    def decode_mime(self, value):
        if not value: 
            return ""
        parts = decode_header(value)
        out = []
        for text, enc in parts:
            if isinstance(text, bytes):
                try: out.append(text.decode(enc or "utf-8", errors="replace"))
                except Exception: out.append(text.decode("utf-8", errors="replace"))
            else: out.append(text)
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
        if html: return re.sub(r'<[^>]+>', ' ', "\n".join(html)).strip()
        return ""

    def get_otp_code(self, target_email, timeout=60):
        if not self.mail:
            if not self.connect(): return None
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.mail.select("INBOX", readonly=True)
                status, data = self.mail.uid("search", None, 'ALL')
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    for uid_bytes in reversed(uids[-5:]):
                        if uid_bytes in self.seen_uids: continue
                        status, fetch_data = self.mail.uid("fetch", uid_bytes, "(RFC822)")
                        if status == "OK" and fetch_data:
                            raw = None
                            for item in fetch_data:
                                if isinstance(item, tuple):
                                    raw = item[1]
                                    break
                            if raw:
                                msg = email.message_from_bytes(raw)
                                to_addr = self.decode_mime(msg.get("To", "")).lower()
                                subject = self.decode_mime(msg.get("Subject", "")).lower()
                                from_addr = self.decode_mime(msg.get("From", "")).lower()
                                if target_email.lower() not in to_addr: continue
                                if "instagram" in subject or "instagram" in from_addr:
                                    self.seen_uids.add(uid_bytes)
                                    body = self.get_text(msg)
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match: return match.group(1)
            except Exception: pass
            time.sleep(5)
        return None

# ========== HÀM ĐẨY ẢNH QUA ADB (CÓ CHỈ ĐỊNH HOẶC RANDOM) ==========
def push_avatar(serial, specific_image_path=None, avatar_folder="avatars"):
    local_path = ""
    
    # 1. Nếu sếp truyền link ảnh vào file txt
    if specific_image_path and os.path.exists(specific_image_path):
        local_path = specific_image_path
        log(serial, f"Đã nhận diện ảnh chỉ định từ file txt: {os.path.basename(local_path)}", Colors.INFO)
        
    # 2. Nếu không có, tự động lấy ngẫu nhiên trong thư mục 'avatars'
    else:
        if specific_image_path:
            log(serial, f"Không tìm thấy ảnh tại: {specific_image_path} -> Chuyển sang lấy random!", Colors.WARNING)
            
        if not os.path.exists(avatar_folder):
            os.makedirs(avatar_folder)
            log(serial, f"LỖI: Thư mục '{avatar_folder}' không tồn tại. Hãy chép ảnh vào!", Colors.ERROR)
            return None
            
        images = [f for f in os.listdir(avatar_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images: 
            log(serial, f"LỖI: Thư mục '{avatar_folder}' đang trống!", Colors.ERROR)
            return None
            
        img_name = random.choice(images)
        local_path = os.path.join(avatar_folder, img_name)
        log(serial, f"Đang bốc random ảnh: {img_name}", Colors.WARNING)

    # Đẩy ảnh qua cáp USB bằng lệnh ADB hệ thống
    remote_path = "/sdcard/Pictures/avatar_ig.jpg"
    log(serial, f"Đang bắn ảnh vào bộ nhớ điện thoại...", Colors.INFO)
    subprocess.run(f"adb -s {serial} push \"{local_path}\" {remote_path}", shell=True, capture_output=True)
    
    # Kích hoạt quét thư viện để hiện ảnh lên ngay
    subprocess.run(f"adb -s {serial} shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}", shell=True, capture_output=True)
    return remote_path

# ========== HÀM BẬT 2FA ==========
def enable_2fa(d, serial, size):
    log(serial, "Đang mở Accounts Center thiết lập 2FA...", Colors.INFO)
    d.click(size[0] * 0.5, size[1] * 0.05)
    time.sleep(1)
    d(className="android.widget.EditText").set_text("https://accountscenter.instagram.com/password_and_security/two_factor/")
    d.press("enter")
    time.sleep(10)
    
    for _ in range(3):
        btn = d(textMatches=r"(?i).*Ứng dụng xác thực.*|.*Authenticator app.*|.*Tiếp.*|.*Next.*")
        if btn.exists(timeout=3):
            btn.click()
            time.sleep(3)
            
    log(serial, "Đang trích xuất Secret Key...", Colors.INFO)
    secret_key = ""
    texts = d(className="android.widget.TextView")
    for t in texts:
        txt = str(t.get_text()).replace(" ", "")
        if re.match(r"^[A-Z2-7]{16,32}$", txt):
            secret_key = txt
            break
            
    if not secret_key:
        copy_btn = d(textMatches=r"(?i).*Sao chép khóa.*|.*Copy key.*")
        if copy_btn.exists:
            copy_btn.click()
            time.sleep(1)
            secret_key = d.clipboard
            
    if not secret_key:
        log(serial, "Lỗi: Không tìm thấy Secret Key!", Colors.ERROR)
        return None
        
    log(serial, f"Secret Key: {secret_key}", Colors.SUCCESS)
    totp = pyotp.TOTP(secret_key.replace(" ", ""))
    code = totp.now()
    log(serial, f"Mã OTP hệ thống tự sinh: {code}", Colors.WARNING)
    
    d(textMatches=r"(?i).*Tiếp.*|.*Next.*").click()
    time.sleep(3)
    
    otp_input = d(className="android.widget.EditText")
    if otp_input.exists(timeout=3):
        otp_input.set_text(code)
        time.sleep(1)
        d(textMatches=r"(?i).*Xong.*|.*Done.*|.*Tiếp.*").click()
        time.sleep(5)
        log(serial, "KÍCH HOẠT 2FA THÀNH CÔNG!", Colors.SUCCESS)
        return secret_key
    return None

# ========== CHU TRÌNH ĐĂNG NHẬP & NUÔI TÀI KHOẢN ==========
def start_nuoi_acc(serial, acc_info):
    email_val = acc_info.get('email', '')
    password_val = acc_info.get('password', '')
    username_val = acc_info.get('username', '')
    cookie_val = acc_info.get('cookie', '')
    avatar_val = acc_info.get('avatar', None)
        
    log(serial, f"Bắt đầu xử lý: {username_val} | {email_val}", Colors.INFO)
    
    try:
        d = u2.connect(serial)
        size = d.window_size()
        
        # 1. Reset dữ liệu Via Browser
        d.app_stop("mark.via.gp")
        subprocess.run(f"adb -s {serial} shell pm clear mark.via.gp", shell=True, capture_output=True)
        time.sleep(2)
        d.app_start("mark.via.gp", stop=True)
        time.sleep(4)
        
        btn_agree = d(textMatches=r"(?i)Đồng ý|Agree")
        if btn_agree.exists(timeout=2): 
            btn_agree.click()
        
        # 2. Mở trang đăng nhập
        d.click(size[0] * 0.5, size[1] * 0.45)
        time.sleep(1)
        d(className="android.widget.EditText").set_text("https://www.instagram.com/accounts/login/")
        d.press("enter")
        time.sleep(8)
        
        user_input = d(textMatches=r"(?i).*Tên người dùng.*|.*Username.*")
        if user_input.exists(timeout=5):
            user_input.set_text(username_val)
            time.sleep(1)
            d(className="android.widget.EditText")[-1].set_text(password_val.strip())
            time.sleep(1)
            d(textMatches=r"(?i).*Đăng nhập.*|.*Log in.*").click()
            time.sleep(10) 
            
            # XỬ LÝ CHECKPOINT LOGIN (AUTO / NHẬP TAY)
            security_check = d(textMatches=r"(?i).*Mã bảo mật.*|.*Security code.*|.*gửi mã.*|.*sent a code.*")
            if security_check.exists(timeout=5):
                log(serial, f"Phát hiện Checkpoint mã gửi về: {email_val}", Colors.WARNING)
                otp_code = None
                
                if "mail.tm" in email_val.lower():
                    log(serial, "Đang quét mã từ Mail.tm...", Colors.INFO)
                    mail_service = MailService()
                    mail_service.authenticate(email_val, "TempPass123!") 
                    otp_code = mail_service.get_otp_code(timeout=15)
                else:
                    try:
                        if os.path.exists("config_gmail.json"):
                            with open("config_gmail.json", "r", encoding="utf-8") as f:
                                cfg = json.load(f)
                                app_pass = cfg.get("dot_trick_app_pass", "")
                                base_mail = cfg.get("dot_trick_email", "")
                                if app_pass:
                                    log(serial, "Đang quét mã từ Gmail IMAP...", Colors.INFO)
                                    imap_svc = GmailIMAPService(base_mail, app_pass)
                                    otp_code = imap_svc.get_otp_code(email_val, timeout=15)
                    except Exception: pass
                
                if not otp_code:
                    print(f"\n{Colors.SUCCESS}{'=' * 60}")
                    print(f">>> YÊU CẦU NHẬP MÃ THỦ CÔNG CHO TÀI KHOẢN <<<")
                    print(f"Địa chỉ Email: {Colors.WARNING}{email_val}{Colors.SUCCESS}")
                    print(f"{'=' * 60}{Colors.RESET}")
                    
                    user_otp = input(f"{Colors.INFO}Nhập mã 6 số (Nhấn Enter trống để bỏ qua): {Colors.RESET}").strip()
                    if user_otp and len(user_otp) >= 6:
                        otp_code = user_otp

                if otp_code:
                    log(serial, f"Điền mã xác thực: {otp_code}", Colors.SUCCESS)
                    otp_input = d(className="android.widget.EditText")
                    if otp_input.exists(timeout=3):
                        otp_input.click()
                        time.sleep(0.5)
                        d.send_keys(otp_code)
                        time.sleep(1)
                        d(textMatches=r"(?i).*Xác nhận.*|.*Confirm.*|.*Gửi.*").click()
                        time.sleep(10)
                else:
                    log(serial, "Không có mã xác minh! Bỏ qua tài khoản này.", Colors.ERROR)
                    return False
            else:
                log(serial, "Đăng nhập trực tiếp thành công!", Colors.SUCCESS)
                time.sleep(5)

        # 3. Tải lên Avatar (KẾT HỢP PUSH ADB)
        remote_img = push_avatar(serial, specific_image_path=avatar_val)
        if remote_img:
            log(serial, "Đang mở trang cập nhật Avatar...", Colors.INFO)
            d.click(size[0] * 0.5, size[1] * 0.05)
            time.sleep(1)
            d(className="android.widget.EditText").set_text("https://www.instagram.com/accounts/edit/")
            d.press("enter")
            time.sleep(8)
            
            change_pic_btn = d(textMatches=r"(?i).*Thay đổi ảnh.*|.*Change photo.*")
            if change_pic_btn.exists(timeout=5):
                change_pic_btn.click()
                time.sleep(3)
                
                file_btn = d(textMatches=r"(?i).*Tệp.*|.*Files.*|.*Media.*")
                if file_btn.exists(timeout=3):
                    file_btn.click()
                time.sleep(3)
                
                first_img = d(resourceIdMatches=r".*image_view.*|.*icon_thumb.*")
                if first_img.exists(timeout=3):
                    first_img.click()
                else:
                    d.click(size[0] * 0.25, size[1] * 0.25)
                time.sleep(8) 
                log(serial, "ĐÃ CẬP NHẬT XONG AVATAR!", Colors.SUCCESS)
                
        # 4. Kích hoạt 2FA
        secret_2fa = enable_2fa(d, serial, size)
        
        # 5. Lưu tài khoản hoàn thiện
        with open("ACC_FULL_TRUST.txt", "a", encoding="utf-8") as f:
            f.write(f"{email_val}|{password_val}|{username_val}|{secret_2fa if secret_2fa else 'ChuaBat2FA'}\n")
            
        log(serial, f"HOÀN THÀNH TOÀN BỘ CHO ACC: {username_val}\n", Colors.SUCCESS)
        return True
    except Exception as e:
        log(serial, f"Lỗi phát sinh: {e}", Colors.ERROR)
        return False

# ========== BỘ ĐỌC FILE SIÊU THÔNG MINH ==========
def load_accounts_flexible(file_path):
    accounts = []
    if not os.path.exists(file_path): return accounts
        
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    current_acc = {}
    for line in lines:
        raw = line.strip()
        if not raw: continue
            
        # Dùng từ khóa "Mail:" làm mốc phân tách khối tài khoản mới
        if raw.lower().startswith("mail:"):
            # Nếu bộ đệm đang có acc cũ thì lưu lại trước khi ghi đè
            if current_acc:
                accounts.append(current_acc)
                current_acc = {}
            current_acc['email'] = raw.split(":", 1)[1].strip()
            
        elif raw.lower().startswith("pass:"): current_acc['password'] = raw.split(":", 1)[1].strip()
        elif raw.lower().startswith("user:"): current_acc['username'] = raw.split(":", 1)[1].strip()
        elif raw.lower().startswith("cookie:"): current_acc['cookie'] = raw.split(":", 1)[1].strip()
        elif raw.lower().startswith("avatar:"): current_acc['avatar'] = raw.split(":", 1)[1].strip()
            
        # Hỗ trợ dự phòng định dạng ngang phân tách bằng dấu |
        elif "|" in raw:
            parts = raw.split("|")
            if len(parts) >= 3:
                accounts.append({
                    'email': parts[0].strip(),
                    'password': parts[1].strip(),
                    'username': parts[2].strip(),
                    'cookie': parts[3].strip() if len(parts) > 3 else "",
                    'avatar': parts[4].strip() if len(parts) > 4 else None
                })
                
    # Bắt mẻ acc cuối cùng ở dưới đáy file (vì không có mốc Mail: tiếp theo)
    if current_acc and 'email' in current_acc:
        accounts.append(current_acc)
        
    return accounts

# ========== CHƯƠNG TRÌNH CHÍNH ==========
if __name__ == "__main__":
    print(f"{Colors.SUCCESS}=== TOOL 2: AUTO AVATAR & 2FA (BẢN V5 - HOÀN THIỆN) ==={Colors.RESET}")
    
    # Tìm file tài khoản tự động (Hỗ trợ file New Text Document.txt của sếp)
    default_files = ["New Text Document.txt", "Instagram_reg/ALL_ACCOUNTS.txt", "ALL_ACCOUNTS.txt"]
    target_file = ""
    for f_name in default_files:
        if os.path.exists(f_name):
            target_file = f_name
            break
            
    if not target_file:
        target_file = input(f"{Colors.INFO}Nhập đường dẫn file chứa danh sách tài khoản: {Colors.RESET}").strip().strip('"').strip("'")
        
    accounts_to_run = load_accounts_flexible(target_file)
    
    if not accounts_to_run:
        print(f"{Colors.ERROR}LỖI: Không đọc được tài khoản nào từ file '{target_file}'! Hãy kiểm tra lại định dạng file.{Colors.RESET}")
        sys.exit(1)
        
    print(f"{Colors.SUCCESS}Đã bóc tách thành công {len(accounts_to_run)} tài khoản từ '{target_file}'!{Colors.RESET}")
    
    # Kết nối ADB
    try:
        adb_output = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        connected_devices = [line.split("\t")[0] for line in adb_output.strip().splitlines()[1:] if "\tdevice" in line]
    except Exception:
        connected_devices = []
        
    if not connected_devices:
        print(f"{Colors.ERROR}Chưa cắm điện thoại hoặc chưa bật USB Debugging!{Colors.RESET}")
        sys.exit(1)
        
    serial_device = connected_devices[0]
    print(f"{Colors.INFO}Kết nối thành công thiết bị: {serial_device}{Colors.RESET}\n")
    
    # Cho tool chạy cày dọc danh sách
    for idx, acc in enumerate(accounts_to_run, 1):
        print(f"{Colors.WARNING}--- ĐANG XỬ LÝ ACC {idx}/{len(accounts_to_run)}: {acc.get('username', 'Unknown')} ---{Colors.RESET}")
        start_nuoi_acc(serial_device, acc)
        
        if idx < len(accounts_to_run):
            rest_time = random.randint(5, 10)
            print(f"{Colors.INFO}Xong 1 acc, nghỉ xả hơi {rest_time}s...{Colors.RESET}\n")
            time.sleep(rest_time)
            
    print(f"\n{Colors.SUCCESS}=== TOOL ĐÃ CHẠY XONG! THÀNH PHẨM LƯU TẠI: ACC_FULL_TRUST.txt ==={Colors.RESET}")
