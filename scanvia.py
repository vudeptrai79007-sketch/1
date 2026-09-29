import os
import time
import random
import re
import requests
import string
import imaplib
import email
from email.header import decode_header
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# ========== BẢNG MÀU GIAO DIỆN ==========
class Colors:
    SUCCESS = "\033[92m"
    ERROR = "\033[91m"
    INFO = "\033[96m"
    WARNING = "\033[93m"
    RESET = "\033[0m"

def log(msg, color=Colors.INFO):
    print(f"{color}{msg}{Colors.RESET}")

# ========== MODULE XỬ LÝ MAIL (TÍCH HỢP GRAPH API OAUTH2) ==========
class MailManager:
    @staticmethod
    def get_mail_tm_otp(email_address, password="TempPass123!@", timeout=60):
        base_url = "https://api.mail.tm"
        try:
            r = requests.post(f"{base_url}/token", json={"address": email_address, "password": password}, timeout=10)
            if r.status_code != 200: return None
            token = r.json()['token']
            headers = {"Authorization": f"Bearer {token}"}
            start_time = time.time()
            last_id = None
            
            while time.time() - start_time < timeout:
                try:
                    msg_req = requests.get(f"{base_url}/messages", headers=headers, timeout=10)
                    if msg_req.status_code == 200:
                        for msg in msg_req.json().get('hydra:member', []):
                            if 'Instagram' in msg.get('subject', ''):
                                if msg.get('id') != last_id:
                                    last_id = msg['id']
                                    detail = requests.get(f"{base_url}/messages/{last_id}", headers=headers, timeout=10).json()
                                    text = detail.get('text', '') or re.sub('<[^<]+?>', '', str(detail.get('html', '')))
                                    match = re.search(r'\b(\d{6})\b', text)
                                    if match: return match.group(1)
                except: pass
                time.sleep(5)
        except: pass
        return None

    @staticmethod
    def get_imap_otp(email_address, email_password, imap_host, timeout=60):
        try:
            mail = imaplib.IMAP4_SSL(imap_host, 993)
            mail.login(email_address, email_password)
            mail.select("INBOX", readonly=True)
            seen_uids = set()
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    status, data = mail.uid("search", None, 'ALL')
                    if status == "OK" and data[0]:
                        uids = data[0].split()
                        for uid_bytes in reversed(uids[-5:]):
                            if uid_bytes in seen_uids: continue
                            status, fetch_data = mail.uid("fetch", uid_bytes, "(RFC822)")
                            if status == "OK" and fetch_data:
                                raw = fetch_data[0][1]
                                msg = email.message_from_bytes(raw)
                                
                                subject_parts = decode_header(msg.get("Subject", ""))
                                subject = ""
                                for text, enc in subject_parts:
                                    if isinstance(text, bytes):
                                        subject += text.decode(enc or "utf-8", errors="replace")
                                    else:
                                        subject += text
                                        
                                if "instagram" in subject.lower():
                                    seen_uids.add(uid_bytes)
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                body = part.get_payload(decode=True).decode(errors="replace")
                                                break
                                    else:
                                        body = msg.get_payload(decode=True).decode(errors="replace")
                                        
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match: return match.group(1)
                except: pass
                time.sleep(5)
        except Exception as e:
            log(f"[!] Lỗi kết nối IMAP ({imap_host}): {e}", Colors.ERROR)
        return None

    @staticmethod
    def get_graph_api_otp(refresh_token, client_id, timeout=60):
        try:
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                "client_id": client_id,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            r = requests.post(token_url, data=data)
            
            if r.status_code != 200:
                token_url = "https://login.live.com/oauth20_token.srf"
                r = requests.post(token_url, data=data)
                
            access_token = r.json().get("access_token")
            if not access_token:
                log("[!] Token hết hạn hoặc Client ID sai!", Colors.ERROR)
                return None

            headers = {"Authorization": f"Bearer {access_token}"}
            msg_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top=5&$select=subject,bodyPreview&$orderby=receivedDateTime desc"

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    msgs = requests.get(msg_url, headers=headers).json()
                    for msg in msgs.get("value", []):
                        subject = msg.get("subject", "").lower()
                        body = msg.get("bodyPreview", "")
                        if "instagram" in subject:
                            match = re.search(r'\b(\d{6})\b', body)
                            if match: return match.group(1)
                except: pass
                time.sleep(5)
        except Exception as e:
            log(f"[!] Lỗi Graph API: {e}", Colors.ERROR)
        return None

# ========== BỘ TẠO DATA & ĐỌC FILE (ĐÃ FIX LỖI TỰ TẠO FILE TRỐNG) ==========
def generate_random_info(email_address):
    password = f"Vip{random.randint(1000, 9999)}@!{random.choice(string.ascii_uppercase)}"
    ho = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo", "Dang"]
    ten = ["Anh", "Bao", "Khoa", "Dung", "Duc", "Hoa", "Hung", "Linh", "Minh", "Ngoc", "Quang", "Trang", "Tuan"]
    full_name = f"{random.choice(ho)} {random.choice(ten)}"
    email_prefix = email_address.split('@')[0]
    username = f"{email_prefix[:8]}.{random.randint(10000, 999999)}"
    return password, full_name, username

def load_emails(file_path):
    accounts = []
    # ĐÃ FIX: Không tự động open(..., "w") nữa. Nếu file không tồn tại, trả về mảng rỗng để tool còi báo động.
    if not os.path.exists(file_path):
        return accounts
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if raw and "@" in raw:
                parts = raw.split("|")
                email_acc = parts[0].strip()
                email_pass = parts[1].strip() if len(parts) > 1 else ""
                refresh_token = parts[2].strip() if len(parts) > 2 else ""
                client_id = parts[3].strip() if len(parts) > 3 else ""
                
                accounts.append({
                    'email': email_acc, 
                    'mail_pass': email_pass,
                    'token': refresh_token,
                    'client_id': client_id
                })
    return accounts

# ========== XỬ LÝ CHROME & FORM REG ==========
def type_like_human(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def start_isolated_chrome(account_username, proxy_string=None):
    log(f"\n[*] Đang khởi tạo Profile Chrome sạch cho acc: {account_username}...")
    base_dir = os.path.abspath("Chrome_Profiles")
    profile_path = os.path.join(base_dir, account_username)
    if not os.path.exists(profile_path): os.makedirs(profile_path)
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    if proxy_string: options.add_argument(f'--proxy-server={proxy_string}')
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1280,800")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--lang=vi-VN") 
    
    driver = uc.Chrome(options=options)
    return driver

def handle_email_otp(driver, wait, mail_mode, acc_data):
    log(f"[*] Đang thực thi lấy mã OTP (Chế độ {mail_mode})...", Colors.INFO)
    try:
        otp_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
        otp_code = None
        
        email_address = acc_data['email']
        email_password = acc_data['mail_pass']
        refresh_token = acc_data['token']
        client_id = acc_data['client_id']
        
        if mail_mode == '1': 
            otp_code = MailManager.get_mail_tm_otp(email_address, email_password if email_password else "TempPass123!@")
        elif mail_mode == '2': 
            if not email_password: log("[!] Lỗi: Bạn chọn Gmail IMAP nhưng file không có Mật khẩu ứng dụng!", Colors.ERROR)
            else: otp_code = MailManager.get_imap_otp(email_address, email_password, "imap.gmail.com")
        elif mail_mode == '3': 
            if refresh_token and client_id:
                log("[*] Phát hiện Token OAuth2. Kích hoạt Graph API...", Colors.INFO)
                otp_code = MailManager.get_graph_api_otp(refresh_token, client_id)
            elif email_password:
                otp_code = MailManager.get_imap_otp(email_address, email_password, "outlook.office365.com")
            else: log("[!] Lỗi: Acc Outlook không có Token cũng không có Pass!", Colors.ERROR)
        elif mail_mode == '4': 
            print(f"\n{Colors.SUCCESS}{'='*50}")
            print(f">>> YÊU CẦU NHẬP MÃ THỦ CÔNG <<<")
            print(f"Mail đang đợi mã: {Colors.WARNING}{email_address}{Colors.SUCCESS}")
            print(f"{'='*50}{Colors.RESET}")
            user_input = input(f"{Colors.INFO}Nhập mã 6 số (Hoặc Enter để bỏ qua): {Colors.RESET}").strip()
            if user_input and len(user_input) >= 6: otp_code = user_input

        if otp_code:
            log(f"[*] Đã húp được mã OTP: {otp_code}. Đang nạp đạn...", Colors.SUCCESS)
            type_like_human(otp_input, otp_code)
            time.sleep(1.5)
            next_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Tiếp') or contains(text(), 'Next')]")
            next_btn.click()
            return True
            
        log("[!] Thất bại: Không lấy được mã OTP!", Colors.ERROR)
        return False
    except Exception as e:
        log(f"[!] Lỗi kẹt ở form nhập OTP: {e}", Colors.ERROR)
        return False

# ========== LUỒNG ĐĂNG KÝ CHÍNH (JS + NGÀY SINH + MANUAL FALLBACK) ==========
def register_instagram(driver, full_name, username, password, mail_mode, acc_data):
    wait = WebDriverWait(driver, 15)
    try:
        log("[*] Đang đâm vào trang Đăng ký...", Colors.INFO)
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(6) 
        
        # 1. Dùng Javascript dọn dẹp Popup Cookie
        try:
            driver.execute_script("""
                var btns = document.querySelectorAll('button');
                for(var i=0; i<btns.length; i++) {
                    if(btns[i].innerText.includes('Cho phép') || btns[i].innerText.includes('Allow')) {
                        btns[i].click();
                    }
                }
            """)
        except: pass

        log("[*] Đang dùng JAVASCRIPT & WAIT để ép nhập Form...", Colors.WARNING)
        try:
            # --- ĐIỀN 4 THÔNG TIN CƠ BẢN ---
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
            driver.execute_script("arguments[0].focus(); arguments[0].click();", email_input)
            time.sleep(0.5)
            type_like_human(email_input, acc_data['email'])
            
            name_input = wait.until(EC.presence_of_element_located((By.NAME, "fullName")))
            driver.execute_script("arguments[0].focus(); arguments[0].click();", name_input)
            time.sleep(0.5)
            type_like_human(name_input, full_name)
            
            user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            driver.execute_script("arguments[0].focus(); arguments[0].click();", user_input)
            time.sleep(0.5)
            type_like_human(user_input, username)
            time.sleep(2) 
            
            pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            driver.execute_script("arguments[0].focus(); arguments[0].click();", pass_input)
            time.sleep(0.5)
            type_like_human(pass_input, password)
            time.sleep(1.5)

            # --- TÍCH HỢP XỬ LÝ NGÀY SINH NGAY TẠI TRANG ---
            log("[*] Đang xử lý form Ngày Sinh bằng JS...", Colors.INFO)
            try:
                month_box = wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Tháng' or @title='Month']")))
                Select(month_box).select_by_value(str(random.randint(1, 12)))
                time.sleep(0.5)
                
                day_box = driver.find_element(By.XPATH, "//select[@title='Ngày' or @title='Day']")
                Select(day_box).select_by_value(str(random.randint(1, 28)))
                time.sleep(0.5)
                
                year_box = driver.find_element(By.XPATH, "//select[@title='Năm' or @title='Year']")
                Select(year_box).select_by_value(str(random.randint(1995, 2002)))
                time.sleep(1.5)
            except Exception:
                log("[!] Lỗi chọn Ngày Sinh (Có thể do mạng lag), cứ tiếp tục ép nút Gửi...", Colors.WARNING)

            # --- DÙNG JS ÉP BẤM NÚT GỬI ---
            log("[*] Đã điền xong tất cả! Đang dùng Javascript bắn nút Gửi...", Colors.INFO)
            submit_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@type='submit']")))
            driver.execute_script("arguments[0].click();", submit_btn) 
            time.sleep(8) 
            
        except Exception as e:
            # 2. CHẾ ĐỘ MANUAL (AUTO BẰNG TAY) - Kích hoạt khi bị block
            log(f"[!] Tool không thể tự gõ (Lỗi: {e}). KÍCH HOẠT CHẾ ĐỘ AUTO BẰNG TAY!", Colors.ERROR)
            print(f"\n{Colors.SUCCESS}{'='*50}")
            print(f">>> SẾP HÃY TỰ ĐIỀN FORM TRÊN TRÌNH DUYỆT <<<")
            print(f"1. Mail: {Colors.WARNING}{acc_data['email']}{Colors.SUCCESS}")
            print(f"2. Tên:  {Colors.WARNING}{full_name}{Colors.SUCCESS}")
            print(f"3. User: {Colors.WARNING}{username}{Colors.SUCCESS}")
            print(f"4. Pass: {Colors.WARNING}{password}{Colors.SUCCESS}")
            print(f"5. Sếp tự bấm Đăng Ký và chọn Ngày Sinh trên Chrome luôn nhé.")
            print(f"6. {Colors.ERROR}DỪNG LẠI{Colors.SUCCESS} khi IG hiện ra bảng [Nhập mã xác nhận 6 số]")
            print(f"{'='*50}{Colors.RESET}")
            
            input(f"{Colors.WARNING}Sếp làm đến bước hỏi OTP chưa? Bấm ENTER ở đây để Tool cào mã nhét vào:{Colors.RESET} ")
        
        # 3. CHỐT CHẶN CUỐI: Cào mã OTP 
        is_otp_success = handle_email_otp(driver, wait, mail_mode, acc_data)
        
        if is_otp_success:
            log("[*] REG THÀNH CÔNG! Đang ngâm tài khoản trong Browser...", Colors.SUCCESS)
            time.sleep(15) 
            return True
        return False
        
    except Exception as e:
        log(f"[!] Đăng ký thất bại (Dính Checkpoint/Block IP): {e}", Colors.ERROR)
        return False

# ========== MENU KHỞI CHẠY CHÍNH ==========
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.SUCCESS}{'='*50}")
    print("      TOOL AUTO REG INSTAGRAM (BẢN FINAL V5 - HOÀN THIỆN)")
    print(f"{'='*50}{Colors.RESET}")
    print(f"{Colors.WARNING}Ghi chú định dạng file:")
    print("- Outlook Token: Mail | Pass | Token | ClientID | Recovery")
    print(f"- Các loại Mail khác: Mail | Pass_App (Nếu cần){Colors.RESET}\n")
    
    print("1. Chế độ Mail.tm")
    print("2. Chế độ Gmail (IMAP)")
    print(f"3. {Colors.INFO}Chế độ Outlook Trusted (Graph API Token / IMAP){Colors.RESET}")
    print("4. Chế độ Nhập Tay thủ công")
    
    mail_mode = ""
    while mail_mode not in ['1', '2', '3', '4']:
        mail_mode = input(f"\n{Colors.INFO}Sếp chọn chế độ nào (1/2/3/4): {Colors.RESET}").strip()
    
    # --- VÒNG LẶP HỎI FILE LIÊN TỤC ĐẾN KHI CÓ DATA THÌ THÔI ---
    account_list = []
    
    while not account_list:
        target_file = input(f"\n{Colors.SUCCESS}Mời sếp kéo thả file TXT chứa list Mail vào đây rồi bấm ENTER: {Colors.RESET}").strip().strip('"').strip("'")
        
        # Nếu sếp lỡ tay bấm Enter luôn mà không điền gì thì báo lỗi bắt điền lại
        if not target_file:
            print(f"{Colors.ERROR}[!] Sếp chưa kéo file vào kìa! Vui lòng làm lại.{Colors.RESET}")
            continue
            
        account_list = load_emails(target_file)
        if not account_list:
            print(f"{Colors.ERROR}[!] LỖI: Đường dẫn không đúng hoặc file '{target_file}' đang trống. Sếp kiểm tra lại nhé!{Colors.RESET}")
            
    # -------------------------------------------------------------
        
    print(f"{Colors.SUCCESS}\nĐã nạp thành công {len(account_list)} data! Bắt đầu lên trại...{Colors.RESET}")
    
    proxy_hien_tai = None # Sếp điền Proxy vào đây nếu có
    
    for idx, acc_data in enumerate(account_list, 1):
        email_reg = acc_data['email']
        
        password_reg, full_name_reg, username_reg = generate_random_info(email_reg)
        
        print(f"\n{Colors.WARNING}--- ĐANG REG ACC {idx}/{len(account_list)}: {email_reg} ---{Colors.RESET}")
        print(f"[{Colors.INFO}INFO{Colors.RESET}] User: {username_reg} | Pass: {password_reg} | Name: {full_name_reg}")
        
        driver = None
        try:
            driver = start_isolated_chrome(account_username=username_reg, proxy_string=proxy_hien_tai)
            
            is_success = register_instagram(driver, full_name_reg, username_reg, password_reg, mail_mode, acc_data)
            
            if is_success:
                with open("IG_PC_ACCOUNTS.txt", "a", encoding="utf-8") as f:
                    f.write(f"{email_reg}|{password_reg}|{username_reg}|{full_name_reg}\n")
                log(f"-> Đã xuất xưởng thành công Acc: {username_reg} vào file IG_PC_ACCOUNTS.txt!", Colors.SUCCESS)
                
        except Exception as e:
            log(f"Lỗi kịch bản: {e}", Colors.ERROR)
        finally:
            if driver:
                driver.quit()
                
        if idx < len(account_list):
            delay = random.randint(15, 30)
            log(f"Đang xả tab, đợi {delay}s để tránh khóa IP...", Colors.INFO)
            time.sleep(delay)
