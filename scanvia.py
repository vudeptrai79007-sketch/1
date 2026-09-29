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

# ========== BẢNG MÀU GIAO DIỆN ==========
class Colors:
    SUCCESS = "\033[92m"
    ERROR = "\033[91m"
    INFO = "\033[96m"
    WARNING = "\033[93m"
    RESET = "\033[0m"

def log(msg, color=Colors.INFO):
    print(f"{color}{msg}{Colors.RESET}")

# ========== QUẢN LÝ CÁC DỊCH VỤ MAIL ==========
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
            
            while time.time() - start_time < timeout:
                try:
                    msg_req = requests.get(f"{base_url}/messages", headers=headers, timeout=10)
                    if msg_req.status_code == 200:
                        for msg in msg_req.json().get('hydra:member', []):
                            if 'Instagram' in msg.get('subject', ''):
                                detail = requests.get(f"{base_url}/messages/{msg['id']}", headers=headers, timeout=10).json()
                                text = detail.get('text', '') or detail.get('html', '')
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
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    status, data = mail.uid("search", None, 'ALL')
                    if status == "OK" and data[0]:
                        uids = data[0].split()
                        for uid_bytes in reversed(uids[-5:]):
                            status, fetch_data = mail.uid("fetch", uid_bytes, "(RFC822)")
                            if status == "OK" and fetch_data:
                                msg = email.message_from_bytes(fetch_data[0][1])
                                if "instagram" in str(msg.get("Subject", "")).lower():
                                    body = msg.get_payload(decode=True).decode(errors="replace")
                                    match = re.search(r'\b(\d{6})\b', body)
                                    if match: return match.group(1)
                except: pass
                time.sleep(5)
        except Exception as e:
            log(f"[!] Lỗi IMAP: {e}", Colors.ERROR)
        return None

    @staticmethod
    def get_graph_api_otp(refresh_token, client_id, timeout=60):
        try:
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {"client_id": client_id, "refresh_token": refresh_token, "grant_type": "refresh_token"}
            r = requests.post(token_url, data=data)
            if r.status_code != 200:
                r = requests.post("https://login.live.com/oauth20_token.srf", data=data)
            access_token = r.json().get("access_token")
            if not access_token: return None

            headers = {"Authorization": f"Bearer {access_token}"}
            msg_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top=5"
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    msgs = requests.get(msg_url, headers=headers).json()
                    for msg in msgs.get("value", []):
                        if "instagram" in msg.get("subject", "").lower():
                            match = re.search(r'\b(\d{6})\b', msg.get("bodyPreview", ""))
                            if match: return match.group(1)
                except: pass
                time.sleep(5)
        except Exception as e:
            log(f"[!] Lỗi Graph API: {e}", Colors.ERROR)
        return None

# ========== KHỞI TẠO TRÌNH DUYỆT CHROME CÁCH LY ==========
def start_isolated_chrome(username):
    profile_path = os.path.abspath(f"Chrome_Profiles/{username}")
    if not os.path.exists(profile_path): os.makedirs(profile_path)
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--lang=vi-VN")
    options.add_argument('--disable-blink-features=AutomationControlled')
    return uc.Chrome(options=options)

# ========== LUỒNG ĐĂNG KÝ CHÍNH DÙNG JS INJECTION ==========
def register_instagram(driver, full_name, username, password, mail_mode, acc_data):
    wait = WebDriverWait(driver, 15)
    try:
        log("[*] Đang truy cập trang đăng ký Instagram...", Colors.INFO)
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(6)
        
        # Bơm dữ liệu trực tiếp bằng JavaScript để lách mọi kháng thể chống bot
        log("[*] Đang bơm dữ liệu qua Javascript thuần...", Colors.WARNING)
        driver.execute_script(f"""
            var e = document.querySelector("input[name='emailOrPhone']"); if(e) {{ e.value = '{acc_data['e']}'; e.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
            var n = document.querySelector("input[name='fullName']"); if(n) {{ n.value = '{full_name}'; n.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
            var u = document.querySelector("input[name='username']"); if(u) {{ u.value = '{username}'; u.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
            var p = document.querySelector("input[name='password']"); if(p) {{ p.value = '{password}'; p.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
        """)
        time.sleep(2)

        # Chọn ngày tháng năm sinh tự động
        try:
            driver.execute_script(f"""
                var selects = document.querySelectorAll('select');
                if(selects.length >= 3) {{
                    selects[0].value = '{random.randint(1, 12)}'; selects[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    selects[1].value = '{random.randint(1, 28)}'; selects[1].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    selects[2].value = '{random.randint(1995, 2002)}'; selects[2].dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
        except: pass
        time.sleep(1.5)

        log("[*] Đang thực thi gửi thông tin đăng ký...", Colors.INFO)
        driver.execute_script("document.querySelector(\"button[type='submit']\").click();")
        time.sleep(8)

    except Exception as e:
        log(f"[!] Không thể tự động điền form: {e}", Colors.ERROR)
        print(f"\n{Colors.SUCCESS}>>> CHUYỂN SANG CHẾ ĐỘ LÀM TAY <<<")
        print(f"Mail: {acc_data['e']} | Tên: {full_name} | User: {username} | Pass: {password}")
        input("Sếp tự thao tác trên Chrome đến bước nhập OTP rồi bấm ENTER: ")

    # Lấy mã OTP dựa theo chế độ mail đã chọn
    log("[*] Đang chờ lấy mã xác nhận OTP từ hòm thư...", Colors.INFO)
    otp_code = None
    if mail_mode == '1':
        otp_code = MailManager.get_mail_tm_otp(acc_data['e'], acc_data['p'] or "TempPass123!@")
    elif mail_mode == '2':
        otp_code = MailManager.get_imap_otp(acc_data['e'], acc_data['p'], "imap.gmail.com")
    elif mail_mode == '3':
        otp_code = MailManager.get_graph_api_otp(acc_data['t'], acc_data['c']) if acc_data['t'] else MailManager.get_imap_otp(acc_data['e'], acc_data['p'], "outlook.office365.com")
    elif mail_mode == '4':
        otp_code = input(f"{Colors.SUCCESS}Sếp hãy nhập mã OTP 6 số: {Colors.RESET}").strip()

    if otp_code:
        log(f"[*] Đã bắt được mã OTP: {otp_code}", Colors.SUCCESS)
        try:
            driver.execute_script(f"""
                var codeInp = document.querySelector("input[name='email_confirmation_code']");
                if(codeInp) {{
                    codeInp.value = '{otp_code}';
                    codeInp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            """)
            time.sleep(1)
            driver.execute_script("document.querySelectorAll(\"button\").forEach(b => { if(b.innerText.includes('Tiếp') || b.innerText.includes('Next')) b.click(); });")
        except:
            code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            for char in otp_code:
                code_input.send_keys(char)
                time.sleep(0.05)
            driver.find_element(By.XPATH, "//button[contains(text(), 'Tiếp') or contains(text(), 'Next')]").click()
            
        time.sleep(10)
        return True
    return False

# ========== CHƯƠNG TRÌNH CHÍNH ==========
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.SUCCESS}=== TOOL AUTO REG INSTAGRAM (BẢN ĐẦY ĐỦ RÕ RÀNG) ==={Colors.RESET}")
    print("1. Chế độ Mail.tm")
    print("2. Chế độ Gmail (IMAP)")
    print("3. Chế độ Outlook Trusted (Graph API Token / IMAP)")
    print("4. Chế độ Nhập Tay thủ công")
    
    mail_mode = ""
    while mail_mode not in ['1', '2', '3', '4']:
        mail_mode = input(f"\n{Colors.INFO}Chọn chế độ (1/2/3/4): {Colors.RESET}").strip()
        
    file_path = input(f"{Colors.SUCCESS}Kéo thả file chứa danh sách tài khoản vào đây: {Colors.RESET}").strip().strip('"').strip("'")
    
    accounts = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) > 0 and '@' in parts[0]:
                    accounts.append({
                        'e': parts[0].strip(),
                        'p': parts[1].strip() if len(parts) > 1 else '',
                        't': parts[2].strip() if len(parts) > 2 else '',
                        'c': parts[3].strip() if len(parts) > 3 else ''
                    })
                    
    print(f"{Colors.SUCCESS}Đã nạp thành công {len(accounts)} tài khoản. Tiến hành chạy...{Colors.RESET}")
    
    for idx, acc in enumerate(accounts, 1):
        password = f"Vip{random.randint(100, 999)}@!{random.choice(string.ascii_uppercase)}"
        full_name = f"Nguyen {random.choice(['Anh', 'Bao', 'Khoa', 'Linh', 'Ngoc'])}"
        username = f"{acc['e'].split('@')[0][:8]}.{random.randint(1000, 9999)}"
        
        print(f"\n{Colors.WARNING}--- ĐANG XỬ LÝ TÀI KHOẢN {idx}/{len(accounts)}: {acc['e']} ---{Colors.RESET}")
        driver = start_isolated_chrome(username)
        
        if register_instagram(driver, full_name, username, password, mail_mode, acc):
            with open("IG_ACCS.txt", "a", encoding="utf-8") as out:
                out.write(f"{acc['e']}|{password}|{username}|{full_name}\n")
            log(f"-> Đã lưu tài khoản thành công vào IG_ACCS.txt", Colors.SUCCESS)
            
        driver.quit()
        time.sleep(random.randint(10, 20))
