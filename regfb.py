# Deobfuscation By ThieuHoang  
import requests
import json
import warnings
import re
import uuid
import random
import time
import os
import sys
import html as _html
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
warnings.filterwarnings('ignore')
GLOBAL_DEVICE_ID = '60DC365D-F964-4224-BD99-71D7259558E6'
GLOBAL_FAMILY_DEVICE_ID = '8f81379b-d587-4465-ae08-ae549d9f8c8f'
GLOBAL_MACHINE_ID = 'YAvmaQtOfBJFJBcqpXveKZ9g'
GLOBAL_WATERFALL_ID = 'bac03ebd268241e99fa00151141b4230'
GLOBAL_CLOUD_TRUST_TOKEN = '8252B111-5428-483D-8996-28A96D07DD579D2668CF-88D0-453D-B871-5D954FD059E0'
GLOBAL_AAC = '{"aac_init_timestamp":1790210000,"aacjid":"Q7jiDQG-coQCrATZCPNA3ZW5srq2bf7HKXXr1FTlIBj-8wGzkK7mS5RN335_vg7MGFEzbXAPA5OBfxIX9kb7KID-ab4UcCOR9pGwBv_qb1pzYxhJ8Mze8tUKwTbOiHYoqhHSoqEtg75jlBVgP2yPEBlA_HpO0Ue_jsKGIiow2G9YdKNZ06lZS_uO5muUQTfADV1JAtXRb5f8GsT7KRayoC2BF8rKLLEmOMhGxZsrqvEfjCwScdLKpwi4BFCTnpJU"}'
CLEAN_PWD_WILDE = '#PWD_WILDE:2:1790210764:AR2ZjAAC2MkJio6zDXsAAW0dJPNJHlKk74FY8Wqljgr0+FFsWpPMI5rl/c6g/CEREiay7H9sBgavn21al+bLYm2rm0VLviqXG//qccfdU29wLCsoriGK6+j1DZzg5WkWBiXuxh6SdfKiatFmExBd/8Voetimbx75uNnzzqJMaBl5QxdJCTEUkqyTel4MXhkPmI2cHLRtj/AtXj0H9JUhz1OslFs77aaI3XwDJ2er6L2viVmcASk15G5plYeRHVTiYoCINEJ5qwbQf5WbZUDsTSGGk2nyvIw5yCAB0nA7vhybwaLgR9OkINI+wPHrUtbWR1WFeYJ5UPjrHIqKUaTvmiiaqWT9kApVkrzzuABAjHRR2Qd39Xy2E2wxR9pSAgx656YrA5iAVOUa'
CURRENT_DEV = None

def generate_device_profile():
    return {'device_id': str(uuid.uuid4()).upper(), 'family_device_id': str(uuid.uuid4()), 'waterfall_id': uuid.uuid4().hex, 'flow_id': str(uuid.uuid4()), 'cloud_token': '{}{}'.format(str(uuid.uuid4()).upper(), str(uuid.uuid4()).upper()[:16]), 'sid': uuid.uuid4().hex, 'nid': '{}{}'.format(uuid.uuid4().hex[:32], ',Wifi')}
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_api.json')
DEFAULT_API_CONFIG = {'metaking_api_key': '', '1smail_api_key': '', '2oo9_api_key': '', 'autosms_api_key': '', 'otptrust_api_key': ''}

def load_api_config():
    cfg = DEFAULT_API_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    cfg.update(saved)
        except Exception:
            pass
    return cfg

def save_api_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=(lambda _186: _186 - 1)(0) == 1)
    except Exception:
        pass

def update_single_api_key(key_name, value):
    cfg = load_api_config()
    cfg[key_name] = value
    save_api_config(cfg)
_api_cfg = load_api_config()
API_KEY_1SMAIL = _api_cfg.get('1smail_api_key', '')
EMAIL_OTP_API_KEY = _api_cfg.get('metaking_api_key', '')
API_KEY_2OO9 = _api_cfg.get('2oo9_api_key', '')
AUTOSMS_API_KEY = _api_cfg.get('autosms_api_key', '')
API_KEY_OTPTRUST = _api_cfg.get('otptrust_api_key', '')
PRODUCT_IDS_1SMAIL = ['16469', '11695', '13828', '11696', '11697']

def get_1smail_balance(api_key=None):
    key = api_key if api_key is not None else API_KEY_1SMAIL
    if not key:
        return None
    try:
        r = requests.get('{}{}'.format('https://www.1smail.shop/api/profile.php?api_key=', key), timeout=10)
        data = r.json()
        if data.get('status') == 'success':
            return data.get('data', {})
    except Exception:
        pass
    return None

def buy_email_1smail(api_key=None):
    key = api_key if api_key is not None else API_KEY_1SMAIL
    if not key:
        print('  [-] Lỗi: Chưa cung cấp API Key 1smail.shop!')
        return None
    for pid in PRODUCT_IDS_1SMAIL:
        try:
            url = 'https://www.1smail.shop/api/buy_product'
            data = {'action': 'buyProduct', 'id': str(pid), 'amount': '1', 'coupon': '', 'api_key': key}
            r = requests.post(url, data=data, timeout=15)
            res = r.json()
            if res.get('status') == 'success' and res.get('data'):
                raw_line = res['data'][0]
                parts = raw_line.strip().split('|')
                if len(parts) >= 4:
                    return {'email': parts[0].strip(), 'password': parts[1].strip(), 'refresh_token': parts[2].strip(), 'client_id': parts[3].strip(), 'raw': raw_line.strip()}
                elif len(parts) >= 2:
                    return {'email': parts[0].strip(), 'password': parts[1].strip(), 'refresh_token': '', 'client_id': '', 'raw': raw_line.strip()}
            elif res.get('msg'):
                msg = res.get('msg', '')
                if 'hết hàng' in msg.lower() or 'số lượng không đủ' in msg.lower():
                    continue
                else:
                    print('{}{}{}{}'.format('  [!] 1smail phản hồi (SP ', pid, '): ', msg))
        except Exception as e:
            print('{}{}{}{}'.format('  [!] Lỗi kết nối 1smail.shop (SP ', pid, '): ', e))
    return None

def get_otp_oautcallable(email, password, refresh_token, client_id, timeout_sec=90):
    url = 'https://tools.dongvanfb.net/api/get_messages_oautcallable'
    headers = {'Content-Type': 'application/json'}
    payload = {'email': email, 'pass': password, 'refresh_token': refresh_token, 'client_id': client_id}
    start_time = time.time()
    print('{}{}{}'.format('[*] Đang lắng nghe OTP tự động cho ', email, '...'))
    while time.time() - start_time < timeout_sec:
        elapsed = int(time.time() - start_time)
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                data = r.json()
                if data.get('code'):
                    c = str(data['code']).strip()
                    if c and c.isdigit() and (len(c) in [5, 6, 8]):
                        return c
                messages = data.get('messages') or []
                for m in messages:
                    code_in_m = str(m.get('code') or '').strip()
                    if code_in_m and code_in_m.isdigit() and (len(code_in_m) in [5, 6, 8]):
                        return code_in_m
                    subject = m.get('subject') or ''
                    sender = m.get('from') or ''
                    body = m.get('message') or ''
                    if any((k in sender.lower() for k in ['facebook', 'fb'])) or any((k in subject.lower() for k in ['facebook', 'mã', 'code', 'xác nhận', 'confirmation'])):
                        fb_match = re.search('FB-(\\d{5,8})', subject + ' ' + body, re.I)
                        if fb_match:
                            return fb_match.group(1)
                        num_match = re.search('\\b(\\d{5,6})\\b', subject)
                        if num_match:
                            return num_match.group(1)
                        num_match_body = re.search('\\b(\\d{5,6})\\b', body)
                        if num_match_body:
                            return num_match_body.group(1)
            print('{}{}{}{}{}'.format('[*] Đang đợi mã OTP từ Facebook... (', elapsed, 's/', timeout_sec, 's)'), end='\r')
        except Exception:
            pass
        time.sleep(3)
    print()
    return None
URL_10MIN_ADDRESS = 'https://10minutemail.net/address.api.php'
URL_10MIN_MAIL = 'https://10minutemail.net/mail.api.php'
HEADERS_10MIN = {'accept': 'application/json, text/javascript, */*; q=0.01', 'x-requested-with': 'XMLHttpRequest', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'referer': 'https://10minutemail.net/m/?lang=vi'}

def get_10min_email():
    session = requests.Session()
    params = {'new': '1', '_': int(time.time() * 1000)}
    try:
        r = session.get(URL_10MIN_ADDRESS, headers=HEADERS_10MIN, params=params, timeout=12)
        if r.status_code == 200:
            data = r.json()
            email = data.get('mail_get_mail')
            if email:
                return {'email': email.strip(), 'session': session, 'type': '10min'}
    except Exception as e:
        print('{}{}'.format('  [!] Lỗi tạo 10MinuteMail: ', e))
    return None

def get_10min_otp(session, timeout_sec=90):
    start_time = time.time()
    print('[*] Đang lắng nghe OTP từ 10MinuteMail...')
    while time.time() - start_time < timeout_sec:
        elapsed = int(time.time() - start_time)
        try:
            params = {'_': int(time.time() * 1000)}
            r = session.get(URL_10MIN_ADDRESS, headers=HEADERS_10MIN, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                mail_list = data.get('mail_list', [])
                for item in mail_list:
                    mail_id = item.get('mail_id', '')
                    if mail_id == 'welcome':
                        continue
                    subject = item.get('subject', '')
                    sender = item.get('from', '')
                    match = re.search('\\b(\\d{5,8})\\b', subject)
                    if match:
                        return match.group(1)
                    try:
                        r_content = session.get(URL_10MIN_MAIL, headers=HEADERS_10MIN, params={'mailid': mail_id, '_': int(time.time() * 1000)}, timeout=10)
                        if r_content.status_code == 200:
                            content_data = r_content.json()
                            body = content_data.get('plain') or content_data.get('html') or ''
                            c_match = re.search('FB-(\\d{5,8})', body, re.I) or re.search('\\b(\\d{5,6})\\b', body)
                            if c_match:
                                return c_match.group(1)
                    except Exception:
                        pass
            print('{}{}{}{}{}'.format('[*] Đang đợi mã OTP từ Facebook về 10MinuteMail... (', elapsed, 's/', timeout_sec, 's)'), end='\r')
        except Exception:
            pass
        time.sleep(3)
    print()
    return None
EMAIL_OTP_BASE_URL = 'https://metaking.top'

def get_email_otp_headers(api_key=None):
    key = api_key if api_key is not None else EMAIL_OTP_API_KEY
    h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if key:
        h['Authorization'] = '{}{}'.format('Bearer ', key)
        h['X-API-Key'] = key
    return h

def get_metaking_balance(api_key=None):
    key = api_key if api_key is not None else EMAIL_OTP_API_KEY
    if not key:
        return None
    try:
        r = requests.get('{}{}'.format(EMAIL_OTP_BASE_URL.rstrip('/'), '/api/balance'), headers=get_email_otp_headers(key), timeout=8)
        d = r.json()
        if d.get('success') and d.get('data'):
            return d['data'].get('balance_vnd', d['data'].get('balance', 0))
    except Exception:
        pass
    return None

def rent_email_otp(server=1, domain='icloud.com', service_id=1, price='low', api_key=None):
    url = '{}{}'.format(EMAIL_OTP_BASE_URL.rstrip('/'), '/api/email-otp/rent')
    payload = {'service_id': service_id, 'domain': domain, 'server': server}
    if server == 4:
        payload['price'] = price
    try:
        r = requests.post(url, headers=get_email_otp_headers(api_key), json=payload, timeout=15)
        res = r.json()
        if res.get('success') and res.get('data'):
            data = res['data']
            return {'rental_id': data.get('rental_id'), 'email': data.get('email_address'), 'domain': data.get('domain'), 'price': data.get('price'), 'balance': data.get('balance'), 'type': 'email_otp'}
        else:
            msg = res.get('message') or res.get('msg') or r.text
            print('{}{}'.format('  [!] Thuê email OTP thất bại: ', msg))
    except Exception as e:
        print('{}{}'.format('  [!] Lỗi kết nối API Email OTP: ', e))
    return None

def poll_email_otp(rental_id, timeout_sec=120):
    url = '{}{}{}{}'.format(EMAIL_OTP_BASE_URL.rstrip('/'), '/api/email-otp/rentals/', rental_id, '/status')
    start_time = time.time()
    print('{}{}{}'.format('[*] Đang lắng nghe OTP từ hệ thống Email OTP (Rental ID: ', rental_id, ')...'))
    while time.time() - start_time < timeout_sec:
        elapsed = int(time.time() - start_time)
        try:
            r = requests.get(url, headers=get_email_otp_headers(), timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get('success') and res.get('data'):
                    data = res['data']
                    status = data.get('status')
                    codes = data.get('codes') or []
                    if codes:
                        for c in codes:
                            if c:
                                code_str = str(c).strip()
                                match = re.search('\\b(\\d{5,8})\\b', code_str)
                                if match:
                                    return match.group(1)
                                if code_str.isdigit():
                                    return code_str
                    if status in ['completed', 'refunded', 'cancelled', 'failed']:
                        if status != 'waiting_otp' and (not codes):
                            break
            print('{}{}{}{}{}'.format('[*] Đang đợi mã OTP từ Facebook... (', elapsed, 's/', timeout_sec, 's)'), end='\r')
        except Exception:
            pass
        time.sleep(3)
    print()
    return None

def cancel_email_otp(rental_id):
    url = '{}{}{}{}'.format(EMAIL_OTP_BASE_URL.rstrip('/'), '/api/email-otp/rentals/', rental_id, '/cancel')
    try:
        r = requests.post(url, headers=get_email_otp_headers(), timeout=10)
        return r.json()
    except Exception:
        return None
API_KEY_2OO9 = 'MFBLMYLMLY6'
GET_NUM_URL_2OO9 = 'https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum'
GET_OTP_URL_2OO9 = 'https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp'
BLOCKED_RANGES_2OO9 = ['2290163', '2290165', '2290198', '2290193', '38091', '23762']
RANGES_2OO9 = ['22898', '22870', '22871', '22896', '22890', '22897', '22891', '2289071', '22892', '2289219', '2287023', '22465', '26134', '2613', '26138', '2666', '2666376', '2666342', '23276', '23674', '223698']

def get_number_2oo9(rid, api_key=API_KEY_2OO9):
    headers = {'mauthapi': api_key, 'Content-Type': 'application/json'}
    clean_rid = str(rid).replace('X', '').strip()
    payload = {'rid': clean_rid}
    try:
        response = requests.post(GET_NUM_URL_2OO9, headers=headers, json=payload, timeout=12)
        data = response.json()
        if data.get('meta', {}).get('code') == 200:
            return data.get('data', {})
        if 'X' in str(rid):
            resp_raw = requests.post(GET_NUM_URL_2OO9, headers=headers, json={'rid': str(rid)}, timeout=12)
            data_raw = resp_raw.json()
            if data_raw.get('meta', {}).get('code') == 200:
                return data_raw.get('data', {})
        if data.get('message'):
            print('{}{}{}{}'.format(' [!] 2oo9.cloud (', clean_rid, '): ', data.get('message')))
        return None
    except Exception as e:
        print('{}{}'.format(' [!] Lỗi khi lấy số từ 2oo9.cloud: ', e))
        return None

def check_otp_2oo9(phone_number, api_key=API_KEY_2OO9, wait_time=60, interval=4):
    headers = {'mauthapi': api_key}
    start_time = time.time()
    clean_num = str(phone_number).replace('+', '').strip()
    print('{}{}{}{}{}'.format(' [*] Đang đợi SMS OTP cho số ', clean_num, ' (tối đa ', wait_time, 's)...'))
    while time.time() - start_time < wait_time:
        try:
            response = requests.get(GET_OTP_URL_2OO9, headers=headers, timeout=10)
            data = response.json()
            if data.get('meta', {}).get('code') == 200:
                otps = data.get('data', {}).get('otps', [])
                for item in otps:
                    num_in_item = str(item.get('number', '')).replace('+', '').strip()
                    if clean_num in num_in_item or num_in_item in clean_num:
                        return item
        except Exception:
            pass
        time.sleep(interval)
    return None

def rent_sim_2oo9(api_key=API_KEY_2OO9, target_rid=None):
    if target_rid:
        clean_target = str(target_rid).replace('X', '').strip()
        if clean_target in BLOCKED_RANGES_2OO9:
            print('{}{}{}'.format('[!] CẢNH BÁO: Dải rid ', clean_target, ' nằm trong danh sách BỊ FACEBOOK CHẶN/CHECKPOINT!'))
        ranges_to_try = [target_rid]
    else:
        ranges_to_try = [r for r in RANGES_2OO9 if r not in BLOCKED_RANGES_2OO9]
    for rid in ranges_to_try:
        clean_r = str(rid).replace('X', '').strip()
        print('{}{}{}'.format('[*] Đang thử lấy số từ dải rid ', clean_r, ' (2oo9.cloud)...'))
        num_data = get_number_2oo9(rid, api_key=api_key)
        if num_data:
            full_num = num_data.get('full_number')
            no_plus = num_data.get('no_plus_number') or str(full_num).replace('+', '')
            print('{}{}{}{}{}{}{}'.format('[+] Lấy số thành công: ', full_num, ' (Quốc gia: ', num_data.get('country'), ', Mạng: ', num_data.get('operator'), ')'))
            return {'type': '2oo9', 'phone': full_num, 'no_plus': no_plus, 'country': num_data.get('country'), 'operator': num_data.get('operator'), 'rid': clean_r, 'api_key': api_key}
    return None
AUTOSMS_BASE_URL = 'https://autosms.site/api'

def get_autosms_balance(api_key=None):
    key = api_key if api_key is not None else AUTOSMS_API_KEY
    if not key:
        return None
    url = '{}{}'.format(AUTOSMS_BASE_URL, '/balance')
    try:
        r = requests.get(url, params={'key': key}, timeout=10)
        data = r.json()
        if data.get('success') and data.get('data'):
            return data.get('data', {})
    except Exception:
        pass
    return None

def rent_sim_autosms(country='us', service='facebook', api_key=None, retries=3):
    key = api_key if api_key is not None else AUTOSMS_API_KEY
    if not key:
        print('[-] Lỗi: Chưa cung cấp API Key autosms.site!')
        return None
    url = '{}{}{}{}{}'.format(AUTOSMS_BASE_URL, '/buy-number/', country, '/', service)
    for attempt in range(1, retries + 1):
        try:
            print('{}{}{}{}{}{}{}'.format('[*] Đang gửi yêu cầu thuê số Facebook (', country.upper(), ') từ autosms.site (lần ', attempt, '/', retries, ')...'))
            r = requests.get(url, params={'key': key}, timeout=15)
            data = r.json()
            if data.get('success') and data.get('data'):
                d = data.get('data', {})
                phone = d.get('phone')
                order_id = d.get('order_id')
                price = d.get('price')
                if phone and order_id:
                    clean_phone = str(phone).strip()
                    no_plus = clean_phone.replace('+', '')
                    print('{}{}{}{}{}{}{}'.format('[+] Thuê số thành công: ', clean_phone, ' (Order ID: ', order_id, ', Giá: ', price, 'đ)'))
                    return {'type': 'autosms', 'phone': clean_phone, 'no_plus': no_plus, 'order_id': order_id, 'price': price, 'country': country, 'api_key': key}
            else:
                msg = data.get('message') or 'Hết số hoặc lỗi dịch vụ'
                print('{}{}'.format('[-] autosms.site: ', msg))
        except Exception as e:
            print('{}{}'.format('[-] Lỗi kết nối autosms.site: ', e))
        time.sleep(3)
    return None

def check_otp_autosms(order_id, api_key=None, wait_time=90, interval=4):
    key = api_key if api_key is not None else AUTOSMS_API_KEY
    if not key or not order_id:
        return None
    url = '{}{}{}'.format(AUTOSMS_BASE_URL, '/orders/', order_id)
    start_time = time.time()
    while time.time() - start_time < wait_time:
        elapsed = int(time.time() - start_time)
        try:
            r = requests.get(url, params={'key': key}, timeout=10)
            data = r.json()
            if data.get('success') and data.get('data'):
                d = data.get('data', {})
                code = d.get('code')
                msg = d.get('message') or ''
                status = str(d.get('status', '')).lower()
                if code:
                    code_str = str(code).strip()
                    m = re.search('\\b(\\d{4,8})\\b', code_str)
                    if m:
                        return m.group(1)
                    return code_str
                if msg:
                    m = re.search('\\b(\\d{5,8})\\b', str(msg))
                    if m:
                        return m.group(1)
                if status in ['cancel', 'cancelled', 'failed', 'expired']:
                    print('{}{}{}{}{}'.format('\n[-] autosms.site: Đơn hàng ', order_id, ' ở trạng thái ', status, '.'))
                    break
            print('{}{}{}{}{}'.format('[*] Đang đợi SMS OTP từ autosms.site... (', elapsed, 's/', wait_time, 's)'), end='\r')
        except Exception:
            pass
        time.sleep(interval)
    print()
    return None

def cancel_order_autosms(order_id, api_key=None):
    key = api_key if api_key is not None else AUTOSMS_API_KEY
    if not key or not order_id:
        return None
    url = '{}{}{}'.format(AUTOSMS_BASE_URL, '/cancel/', order_id)
    try:
        r = requests.get(url, params={'key': key}, timeout=10)
        return r.json()
    except Exception:
        return None
OTPTRUST_BASE_URL = 'https://otptrust.com/api/v1/email'

def get_otptrust_services(api_key=None, domain=None):
    key = api_key if api_key is not None else API_KEY_OTPTRUST
    if not key:
        return []
    headers = {'Authorization': '{}{}'.format('Bearer ', key), 'Accept': 'application/json'}
    url = '{}{}'.format(OTPTRUST_BASE_URL, '/services')
    params = {}
    if domain:
        params['domain'] = domain
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        data = r.json()
        if data.get('success'):
            return data.get('data', [])
        elif data.get('message'):
            print('{}{}{}{}'.format('[-] otptrust.com (', domain or 'default', '): ', data.get('message')))
    except Exception as e:
        print('{}{}{}{}'.format('[-] Lỗi kết nối otptrust.com (', domain or 'default', '): ', e))
    return []

def get_otptrust_facebook_options(api_key=None):
    key = api_key if api_key is not None else API_KEY_OTPTRUST
    options = []
    print('[*] Đang tải danh sách dịch vụ Facebook từ otptrust.com...')
    std_services = get_otptrust_services(key, domain=None)
    for s in std_services:
        name = s.get('name', '')
        code = s.get('service_code', '')
        if 'facebook' in name.lower() or 'facebook' in code.lower() or 'fb' in code.lower():
            p_vn = s.get('price_vn') or s.get('price_us') or '5,000₫'
            avail_hot = s.get('available_hotmail')
            avail_hot_str = 'Hết hàng' if avail_hot == 0 else '{}'.format(avail_hot) if avail_hot is not None else 'Có sẵn'
            options.append({'provider': 'hotmail', 'service_id': s['id'], 'name': '{}{}{}'.format('Hotmail (', name, ')'), 'price': p_vn, 'available': avail_hot_str, 'api_key': key})
            avail_out = s.get('available_outlook')
            avail_out_str = 'Hết hàng' if avail_out == 0 else '{}'.format(avail_out) if avail_out is not None else 'Có sẵn'
            options.append({'provider': 'outlook', 'service_id': s['id'], 'name': '{}{}{}'.format('Outlook (', name, ')'), 'price': p_vn, 'available': avail_out_str, 'api_key': key})
    icloud_services = get_otptrust_services(key, domain='icloud')
    for s in icloud_services:
        name = s.get('name', '')
        code = s.get('service_code', '')
        if 'facebook' in name.lower() or 'facebook' in code.lower() or 'fb' in code.lower():
            p_vn = s.get('price_vn') or s.get('price_us') or '2,000₫'
            avail = s.get('available')
            avail_str = 'Hết hàng' if avail == 0 else '{}'.format(avail) if avail is not None else 'Có sẵn'
            options.append({'provider': 'icloud', 'service_id': s['id'], 'name': '{}{}{}'.format('iCloud (', name, ')'), 'price': p_vn, 'available': avail_str, 'api_key': key})
    gmail_services = get_otptrust_services(key, domain='gmail')
    for s in gmail_services:
        name = s.get('name', '')
        code = s.get('service_code', '')
        if 'facebook' in name.lower() or 'facebook' in code.lower() or 'fb' in code.lower():
            p_vn = s.get('price_vn') or s.get('price_us') or '2,000₫'
            avail = s.get('available')
            avail_str = 'Hết hàng' if avail == 0 else '{}'.format(avail) if avail is not None else 'Có sẵn'
            options.append({'provider': 'gmail', 'service_id': s['id'], 'name': '{}{}{}'.format('Gmail (', name, ')'), 'price': p_vn, 'available': avail_str, 'api_key': key})
    if not options:
        print('[!] Không lấy được danh sách động từ API, sử dụng cấu hình mặc định otptrust.')
        options = [{'provider': 'hotmail', 'service_id': 1, 'name': 'Hotmail (Facebook)', 'price': '5,000₫', 'available': 'Có sẵn', 'api_key': key}, {'provider': 'outlook', 'service_id': 1, 'name': 'Outlook (Facebook)', 'price': '5,000₫', 'available': 'Có sẵn', 'api_key': key}, {'provider': 'icloud', 'service_id': 10, 'name': 'iCloud (Facebook)', 'price': '2,000₫', 'available': 'Có sẵn', 'api_key': key}, {'provider': 'gmail', 'service_id': 20, 'name': 'Gmail (Facebook)', 'price': '2,000₫', 'available': 'Có sẵn', 'api_key': key}]
    return options

def rent_email_otptrust(api_key, service_id, provider):
    key = api_key if api_key else API_KEY_OTPTRUST
    if not key:
        print('[-] Lỗi: Chưa cung cấp API Key otptrust.com!')
        return None
    url = '{}{}'.format(OTPTRUST_BASE_URL, '/rent')
    headers = {'Authorization': '{}{}'.format('Bearer ', key), 'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = {'service_id': int(service_id), 'provider': str(provider).lower()}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        res = r.json()
        if res.get('success') and res.get('data'):
            data = res['data']
            return {'type': 'otptrust', 'email': data['email'], 'order_id': data['order_id'], 'service': data.get('service'), 'price': data.get('price_vn') or data.get('price_us'), 'provider': provider, 'api_key': key}
        else:
            msg = res.get('message') or res.get('msg') or 'Hết hàng hoặc số dư không đủ'
            print('{}{}'.format('[-] otptrust.com thuê mail thất bại: ', msg))
    except Exception as e:
        print('{}{}'.format('[-] Lỗi gọi API thuê mail otptrust.com: ', e))
    return None

def poll_otp_otptrust(order_id, api_key=None, timeout_sec=120, interval=4):
    key = api_key if api_key else API_KEY_OTPTRUST
    if not key or not order_id:
        return None
    url = '{}{}{}'.format(OTPTRUST_BASE_URL, '/orders/', order_id)
    headers = {'Authorization': '{}{}'.format('Bearer ', key), 'Accept': 'application/json'}
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        elapsed = int(time.time() - start_time)
        try:
            r = requests.get(url, headers=headers, timeout=10)
            res = r.json()
            if res.get('success') and res.get('data'):
                data = res['data']
                otp = data.get('otp')
                status = data.get('status', '')
                if otp:
                    otp_str = str(otp).strip()
                    m = re.search('\\b(\\d{5,8})\\b', otp_str)
                    if m:
                        return m.group(1)
                    return otp_str
                if status in ['failed', 'released']:
                    print('{}{}{}{}'.format('\n[-] otptrust.com: Đơn thuê ', order_id, ' đã kết thúc với trạng thái: ', status))
                    break
            print('{}{}{}{}{}'.format('[*] Đang đợi OTP từ otptrust.com... (', elapsed, 's/', timeout_sec, 's)'), end='\r')
        except Exception:
            pass
        time.sleep(interval)
    print()
    return None

def cancel_email_otptrust(order_id, api_key=None):
    key = api_key if api_key else API_KEY_OTPTRUST
    if not key or not order_id:
        return None
    url = '{}{}{}{}'.format(OTPTRUST_BASE_URL, '/orders/', order_id, '/cancel')
    headers = {'Authorization': '{}{}'.format('Bearer ', key), 'Accept': 'application/json'}
    try:
        r = requests.post(url, headers=headers, timeout=10)
        res = r.json()
        if res.get('success'):
            print('{}{}'.format('[+] Hủy đơn otptrust.com thành công: ', res.get('message', 'Đã hủy đơn')))
        return res
    except Exception:
        return None
UA_DESKTOP = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
UA_MOBILE = 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
BROWSE_HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.7', 'Upgrade-Insecure-Requests': '1', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'document', 'Connection': 'keep-alive'}
_check_sess = requests.Session()
_check_sess.mount('https://', requests.adapters.HTTPAdapter(pool_connections=8, pool_maxsize=8, max_retries=1))

def _req_check(url: str, ua: str):
    h = dict(BROWSE_HEADERS)
    h['User-Agent'] = ua
    try:
        return _check_sess.get(url, headers=h, timeout=8, allow_redirects=(lambda _1318: _1318 + 1)(0) == 1)
    except Exception:
        return None

def _extract_name(html: str):
    BAD = ['facebook', 'error', 'sorry', "content isn't available", 'nội dung hiện không khả dụng', 'page not found', "we're sorry", 'đã xảy ra sự cố']
    m = re.search('<meta\\s+property=["\\\']og:title["\\\']\\s+content=["\\\']([^"\\\']+)["\\\']', html, re.I)
    s1 = _html.unescape(m.group(1)).strip() if m else None
    m2 = re.search('<title>(.*?)</title>', html, re.S | re.I)
    s2 = re.sub('\\s*\\|\\s*Facebook.*$', '', _html.unescape(m2.group(1)).strip(), flags=re.I).strip() if m2 else None
    for s in (s1, s2):
        if s and len(s) >= 2 and (not any((b in s.lower() for b in BAD))):
            return s
    return None

def check_live_die(uid: str, proxies=None, token=None, fallback_name=None):
    if not uid or not str(uid).isdigit():
        return ((lambda _136: _136 - 1)(0) == 1, None)
    is_live = (lambda _1619: _1619 - 1)(0) == 1
    try:
        url_graph = '{}{}{}'.format('https://graph.facebook.com/', uid, '/picture?redirect=false')
        r = requests.get(url_graph, proxies=proxies, timeout=10)
        if r.status_code == 200:
            data = r.json().get('data', {})
            pic_url = data.get('url', '')
            if 'static.xx' in pic_url or 'rsrc.php' in pic_url:
                return ((lambda _512: _512 - 1)(0) == 1, None)
            if 'height' in data and 'width' in data and ('scontent' in pic_url):
                is_live = (lambda _1116: _1116 + 1)(0) == 1
    except Exception:
        pass
    if not is_live:
        return ((lambda _219: _219 - 1)(0) == 1, None)
    real_name = None
    if token:
        try:
            r_me = requests.get('{}{}{}'.format('https://graph.facebook.com/me?access_token=', token, '&fields=name'), proxies=proxies, timeout=6)
            if r_me.status_code == 200:
                real_name = r_me.json().get('name')
        except Exception:
            pass
    if not real_name:
        real_name = fallback_name or 'Facebook User'
    return ((lambda _116: _116 + 1)(0) == 1, real_name)

def extract_session_cookies(session, extra_text=''):
    cookies = []
    try:
        for c in session.cookies:
            if c.name and c.value:
                cookies.append('{}{}{}'.format(c.name, '=', c.value))
    except Exception:
        pass
    if not cookies and extra_text:
        matches = re.findall('"name"\\s*:\\s*"([^"]+)"\\s*,\\s*"value"\\s*:\\s*"([^"]+)"', extra_text)
        for n, v in matches:
            cookies.append('{}{}{}'.format(n, '=', v))
    seen = {}
    for item in cookies:
        if '=' in item:
            k, v = item.split('=', 1)
            seen[k] = v
    if seen:
        return '; '.join(['{}{}{}'.format(k, '=', v) for k, v in seen.items()]) + ';'
    return ''

def get_token_eaaau_and_cookie(uid, password, proxies=None, timeout=20):
    url = 'https://b-graph.facebook.com/auth/login'
    timestamp = int(time.time())
    encrypted_password = '{}{}{}{}'.format('#PWD_FB4A:0:', timestamp, ':', password)
    device_id = str(uuid.uuid4())
    ad_id = str(uuid.uuid4())
    headers = {'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; G011A Build/N2G48H) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/en_US;FBBV/480086274;FBCR/Sprint;FBMF/google;FBBD/google;FBDV/G011A;FBSV/7.1.2;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=720,height=1280};FB_FW/1;FBRV/0;]', 'content-type': 'application/x-www-form-urlencoded'}
    data = {'adid': ad_id, 'format': 'json', 'device_id': device_id, 'email': str(uid), 'openid_flow': 'android_login', 'password': encrypted_password, 'generate_analytics_claim': '1', 'cpl': 'true', 'family_device_id': device_id, 'credentials_type': 'password', 'generate_session_cookies': '1', 'error_detail_type': 'button_with_disabled', 'source': 'register_api', 'locale': 'en_US', 'client_country_code': 'US', 'api_key': '882a8490361da98702bf97a021ddc14d', 'sig': '4579f821656bf86619416f9458b06788', 'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32'}
    try:
        r = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=timeout)
        rs = r.text or ''
        token_match = re.search('"access_token"\\s*:\\s*"(EAAAAU[^"]+)"', rs)
        token = token_match.group(1) if token_match else None
        cookie_matches = re.findall('"name"\\s*:\\s*"([^"]+)"\\s*,\\s*"value"\\s*:\\s*"([^"]+)"', rs)
        cookie_str = '; '.join(['{}{}{}'.format(n, '=', v) for n, v in cookie_matches]) + ';' if cookie_matches else ''
        return (token, cookie_str)
    except Exception:
        return (None, '')

def extract_reg_context(response_text, fallback_context):
    if not response_text:
        return fallback_context
    m = re.search('logged_out[^\\w]*(AX[a-zA-Z0-9_\\-\\|]+?)(?:\\\\\\\\\\\\"|"|\\\')', response_text)
    if m:
        return m.group(1)
    m2 = re.search('reg_context\\\\"[^\\w]*(AX[a-zA-Z0-9_\\-\\|]+?)(?:\\\\\\\\\\\\"|"|\\\')', response_text)
    if m2:
        return m2.group(1)
    matches = re.findall('(AX[a-zA-Z0-9_\\-\\|]{100,})', response_text)
    if matches:
        return max(matches, key=len)
    return fallback_context

def create_nested_variables(app_id, client_inputs, server_inputs):
    dev = CURRENT_DEV or {'device_id': GLOBAL_DEVICE_ID, 'waterfall_id': GLOBAL_WATERFALL_ID, 'cloud_token': GLOBAL_CLOUD_TRUST_TOKEN}
    client_inputs['machine_id'] = GLOBAL_MACHINE_ID
    client_inputs['aac'] = GLOBAL_AAC
    client_inputs['cloud_trust_token'] = dev.get('cloud_token', GLOBAL_CLOUD_TRUST_TOKEN)
    server_inputs['machine_id'] = GLOBAL_MACHINE_ID
    server_inputs['device_id'] = dev.get('device_id', GLOBAL_DEVICE_ID)
    server_inputs['waterfall_id'] = dev.get('waterfall_id', GLOBAL_WATERFALL_ID)
    server_inputs['cloud_trust_token'] = dev.get('cloud_token', GLOBAL_CLOUD_TRUST_TOKEN)
    inner_payload = {'client_input_params': client_inputs, 'server_params': server_inputs}
    middle_payload = {'params': json.dumps(inner_payload), 'bloks_versioning_id': '9f6640a4dfe5a7dbef8a547602beb113245c252866cda233a02a797683c2b120', 'app_id': app_id}
    variables = {'generic_attachment_tall_cover_image_width': 1164, 'generic_attachment_small_cover_image_height': 120, 'params': middle_payload, 'formatType': 'concise', 'include_workplace_fields': 'false', 'device': 'iphone', 'generic_attachment_tall_cover_image_height': 612, 'generic_attachment_tall_cover_image_width_no_scale': 388, 'nt_context': {'bloks_version': '9f6640a4dfe5a7dbef8a547602beb113245c252866cda233a02a797683c2b120', 'styles_id': 'a8f4a1c2a3aae6ce1e5ac6aee64fbb75', 'pixel_ratio': 3, 'theme_params': [{'design_system_name': 'FDS', 'value': ['BLUEPRINT_TEST_ROUNDED_CORNERS_NO_GUTTERS', 'DEFAULT']}]}, 'scale': 3, 'should_include_delegate_page': (lambda _153: _153 + 1)(0) == 1, 'generic_attachment_small_cover_image_width': 120, 'voiceover_enabled': 'false'}
    return json.dumps(variables)

def parse_single_proxy(proxy_str):
    if not proxy_str:
        return None
    p = proxy_str.strip()
    if not p:
        return None
    scheme = 'http'
    if p.startswith('socks5://'):
        scheme = 'socks5'
        p = p[len('socks5://'):]
    elif p.startswith('http://'):
        scheme = 'http'
        p = p[len('http://'):]
    elif p.startswith('https://'):
        scheme = 'http'
        p = p[len('https://'):]
    if '@' in p:
        proxy_url = '{}{}{}'.format(scheme, '://', p)
        return {'http': proxy_url, 'https': proxy_url}
    parts = p.split(':')
    if len(parts) == 2:
        proxy_url = '{}{}{}{}{}'.format(scheme, '://', parts[0], ':', parts[1])
        return {'http': proxy_url, 'https': proxy_url}
    elif len(parts) == 4:
        if parts[1].isdigit() and (not parts[3].isdigit()):
            ip, port, user, pwd = (parts[0], parts[1], parts[2], parts[3])
        elif parts[3].isdigit() and (not parts[1].isdigit()):
            user, pwd, ip, port = (parts[0], parts[1], parts[2], parts[3])
        else:
            ip, port, user, pwd = (parts[0], parts[1], parts[2], parts[3])
        proxy_url = '{}{}{}{}{}{}{}{}{}'.format(scheme, '://', user, ':', pwd, '@', ip, ':', port)
        return {'http': proxy_url, 'https': proxy_url}
    else:
        proxy_url = '{}{}{}'.format(scheme, '://', p)
        return {'http': proxy_url, 'https': proxy_url}

def prompt_proxy_source():
    print('\n--- CẤU HÌNH PROXY ---')
    val = input('[?] Nhập file proxy (ví dụ: proxy.txt) hoặc proxy đơn (Enter bỏ qua): ').strip()
    if not val:
        print('[*] Chạy trực tiếp bằng IP máy (Không dùng Proxy).')
        return []
    if os.path.isfile(val):
        proxy_list = []
        try:
            with open(val, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and (not line.startswith('#')):
                        parsed = parse_single_proxy(line)
                        if parsed:
                            proxy_list.append({'raw': line, 'dict': parsed})
            print('{}{}{}{}{}'.format('[+] Đã tải ', len(proxy_list), " proxy từ file '", val, "'. Tool sẽ tự động xoay proxy cho từng acc."))
            return proxy_list
        except Exception as e:
            print('{}{}{}{}{}'.format("[-] Lỗi đọc file proxy '", val, "': ", e, '. Tiếp tục bằng IP máy.'))
            return []
    else:
        parsed = parse_single_proxy(val)
        if parsed:
            print('{}{}'.format('[+] Sử dụng Proxy đơn: ', val))
            return [{'raw': val, 'dict': parsed}]
        else:
            print('[-] Định dạng proxy không hợp lệ, tiếp tục bằng IP máy.')
            return []

def get_proxy_for_run(proxy_list, index):
    if not proxy_list:
        return None
    p_item = proxy_list[index % len(proxy_list)]
    print('{}{}{}{}{}{}'.format('[*] [Xoay Proxy] Dùng Proxy #', index % len(proxy_list) + 1, '/', len(proxy_list), ': ', p_item['raw']))
    return p_item['dict']

def print_registration_summary(stats):
    total = stats.get('total', 0)
    live = stats.get('live', 0)
    die = stats.get('die', 0)
    error = stats.get('error', 0)
    print('\n' + '=' * 55)
    print('              BÁO CÁO TỔNG KẾT ĐĂNG KÝ')
    print('=' * 55)
    print('{}{}'.format('  Tổng số tài khoản yêu cầu : ', total))
    print('{}{}'.format('  [\x1b[1;32mLIVE\x1b[0m] Thành công            : ', live))
    print('{}{}'.format('  [\x1b[1;31mDIE / CHECKPOINT\x1b[0m] Bị khóa   : ', die))
    print('{}{}'.format('  [\x1b[1;33mLỖI\x1b[0m] Thất bại / Hủy luồng   : ', error))
    print('=' * 55)
    if live > 0:
        print('[+] Danh sách nick LIVE lưu tại: acc_fb_thanhcong.txt (UID|PASS|COOKIE|TOKEN|MAIL)')
    if die > 0:
        print('[-] Danh sách nick DIE lưu tại: acc_fb_die_checkpoint.txt')
    print('=' * 55 + '\n')

def prompt_delay_between_accs(default_sec=5):
    del_in = input('{}{}{}'.format('[?] Nghỉ bao nhiêu giây để reg tiếp (Enter = ', default_sec, 's): ')).strip()
    if del_in.isdigit():
        return max(0, int(del_in))
    return default_sec

def countdown_delay(seconds):
    if seconds <= 0:
        return
    for s in range(seconds, 0, -1):
        print('{}{}{}'.format('[*] Nghỉ ', s, 's trước khi chạy acc tiếp theo...   '), end='\r')
        time.sleep(1)
    print(' ' * 60, end='\r')

def safe_append_file(filename, line_content, max_retries=5, delay=0.8):
    cleaned_line = str(line_content).strip()
    if not cleaned_line:
        return (lambda _318: _318 + 1)(0) == 1
    for attempt in range(max_retries):
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(cleaned_line + '\n')
            print('{}{}{}'.format("[*] Đã lưu thông tin vào file '", filename, "' thành công!"))
            return (lambda _93: _93 + 1)(0) == 1
        except PermissionError:
            print('{}{}{}{}{}{}{}'.format("[!] Cảnh báo: File '", filename, "' đang bị một chương trình khác (Excel/Notepad/Antivirus) chiếm quyền mở. Thử lại lần ", attempt + 1, '/', max_retries, '...'))
            time.sleep(delay)
        except Exception as e:
            print('{}{}{}{}'.format("[-] Lỗi ghi file '", filename, "': ", e))
            break
    fallback_name = '{}{}'.format('backup_', filename)
    try:
        with open(fallback_name, 'a', encoding='utf-8') as fb:
            fb.write(cleaned_line + '\n')
        print('{}{}{}{}{}'.format("[+] ĐÃ TỰ ĐỘNG LƯU VÀO FILE DỰ PHÒNG '", fallback_name, "' DO '", filename, "' ĐANG BỊ KHÓA!"))
        return (lambda _149: _149 + 1)(0) == 1
    except Exception as e2:
        print('{}{}{}{}'.format("[-] Không thể lưu vào cả file dự phòng '", fallback_name, "': ", e2))
        print('\n' + '!' * 55)
        print('  [KHẨN CẤP] VUI LÒNG COPY THÔNG TIN NICK DƯỚI ĐÂY:')
        print('{}{}'.format('  ', cleaned_line))
        print('!' * 55 + '\n')
        return (lambda _1718: _1718 - 1)(0) == 1

def safe_write_file(filename, content):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(content))
    except Exception:
        pass

def facebook_registration_flow(first_name, last_name, gender, proxies, email_mode, password_input, mail_item=None, otp_server=1, otp_domain='icloud.com', otp_price='low', phone_number=None, phone_obj=None, otptrust_service=None):
    session = requests.Session()
    global CURRENT_DEV
    CURRENT_DEV = generate_device_profile()
    dev = CURRENT_DEV
    print('\n' + '=' * 50)
    print('{}{}{}'.format('Bắt đầu luồng đăng ký iOS (Thiết bị ID: ', dev['device_id'][:8], '...)...'))
    if proxies:
        try:
            res_ip = requests.get('https://ifconfig.me/ip', proxies=proxies, timeout=10)
            print('{}{}'.format('[+] Proxy Live! Đang chạy trên IP: ', res_ip.text.strip()))
            session.proxies.update(proxies)
        except Exception:
            print('[!] Lỗi kết nối Proxy, chuyển về chạy bằng IP thật...')
    else:
        try:
            res_ip = requests.get('https://ifconfig.me/ip', timeout=10)
            print('{}{}'.format('[+] Đang chạy trên IP thật: ', res_ip.text.strip()))
        except Exception:
            print('[!] Không thể kiểm tra IP, tiếp tục chạy.')
    print('=' * 50)
    url = 'https://graph.facebook.com/graphql'
    dynamic_user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/21E219 [FBAN/FBIOS;FBAV/520.0.0.38.101;FBBV/756351453;FBDV/iPhone13,4;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBID/phone;FBLC/vi_VN;FBOP/5;FBRV/0]'
    headers = {'x-fb-request-analytics-tags': '{"network_tags":{"product":"6628568379","purpose":"fetch","request_category":"graphql","retry_attempt":"0"}}', 'priority': 'u=1', 'x-tigon-is-retry': 'False', 'x-graphql-request-purpose': 'fetch', 'content-type': 'application/x-www-form-urlencoded', 'x-fb-tasos-experimental': '1', 'x-graphql-client-library': 'pando', 'x-fb-appnetsession-sid': dev['sid'], 'x-fb-integrity-machine-id': GLOBAL_MACHINE_ID, 'user-agent': dynamic_user_agent, 'x-fb-connection-type': 'wifi', 'x-fb-appnetsession-nid': dev['nid'], 'x-fb-sim-hni': '45204', 'authorization': 'OAuth 6628568379|c1e620fa708a1d5696fb991c1bde5662', 'x-meta-zca': '{"e": {"c":7}}', 'x-fb-congestion-signal': '0', 'accept-encoding': 'gzip, deflate', 'x-fb-http-engine': 'Tigon/Liger', 'x-fb-client-ip': 'True', 'x-fb-server-cluster': 'True'}
    flow_info_str = '{"flow_name":"new_to_family_fb_default","flow_type":"ntf"}'
    reg_info_dict = {'first_name': None, 'last_name': None, 'full_name': None, 'contactpoint': None, 'ar_contactpoint': None, 'attempted_empty_last_name': (lambda _1218: _1218 - 1)(0) == 1, 'contactpoint_type': None, 'is_using_unified_cp': None, 'unified_cp_screen_variant': None, 'is_cp_auto_confirmed': (lambda _159: _159 - 1)(0) == 1, 'is_cp_auto_confirmable': (lambda _198: _198 - 1)(0) == 1, 'is_cp_claimed': (lambda _1319: _1319 - 1)(0) == 1, 'confirmation_code': None, 'birthday': None, 'birthday_derived_from_age': None, 'age_range': None, 'did_use_age': (lambda _37: _37 - 1)(0) == 1, 'os_shared_age_range': None, 'gender': None, 'use_custom_gender': (lambda _136: _136 - 1)(0) == 1, 'custom_gender': None, 'encrypted_password': None, 'username': None, 'username_prefill': None, 'accounts_list_client': [], 'fb_conf_source': None, 'device_id': dev['device_id'], 'ig4a_qe_device_id': None, 'family_device_id': dev['family_device_id'], 'fdid_available_on_start': None, 'fdid_rid_available_on_start': None, 'asdid_available_on_start': None, 'user_id': None, 'safetynet_token': None, 'skip_slow_rel_check': (lambda _27: _27 - 1)(0) == 1, 'safetynet_response': None, 'machine_id': GLOBAL_MACHINE_ID, 'profile_photo': None, 'profile_photo_id': None, 'profile_photo_upload_id': None, 'avatar': None, 'email_oauth_token_no_contact_perm': None, 'email_oauth_token': None, 'email_oauth_tokens': [], 'sign_in_with_google_email': None, 'should_skip_two_step_conf': None, 'openid_tokens_for_testing': None, 'encrypted_msisdn': None, 'encrypted_msisdn_for_safetynet': None, 'cached_headers_safetynet_info': None, 'should_skip_headers_safetynet': None, 'headers_last_infra_flow_id': None, 'headers_last_infra_flow_id_safetynet': None, 'headers_flow_id': None, 'was_headers_prefill_available': None, 'sso_enabled': None, 'existing_accounts': None, 'used_ig_birthday': None, 'create_new_to_app_account': None, 'skip_session_info': None, 'ck_error': None, 'ck_id': None, 'ck_nonce': None, 'should_save_password': (lambda _214: _214 + 1)(0) == 1, 'fb_access_token': None, 'is_msplit_reg': None, 'is_spectra_reg': None, 'dema_account_consent_given': None, 'spectra_entry_source': None, 'spectra_reg_token': None, 'spectra_reg_guardian_id': None, 'spectra_reg_guardian_logged_in_context': None, 'spectra_requester_user_id': None, 'user_id_of_msplit_creator': None, 'msplit_creator_nonce': None, 'dma_data_combination_consent_given': None, 'xapp_accounts': None, 'fb_device_id': None, 'fb_machine_id': None, 'ig_device_id': None, 'ig_machine_id': None, 'should_skip_nta_upsell': None, 'big_blue_token': None, 'caa_reg_flow_source': 'aymh_multi_profiles_native_integration_point', 'ig_authorization_token': None, 'full_sheet_flow': (lambda _1218: _1218 - 1)(0) == 1, 'crypted_user_id': None, 'is_ca_late_teen': None, 'is_early_teen': None, 'is_caa_perf_enabled': (lambda _19: _19 + 1)(0) == 1, 'is_preform': (lambda _158: _158 + 1)(0) == 1, 'should_show_rel_error': (lambda _516: _516 - 1)(0) == 1, 'ignore_suma_check': (lambda _42: _42 - 1)(0) == 1, 'dismissed_login_upsell_with_cna': (lambda _1310: _1310 - 1)(0) == 1, 'ignore_existing_login': (lambda _510: _510 - 1)(0) == 1, 'ignore_existing_login_from_suma': (lambda _124: _124 - 1)(0) == 1, 'ignore_existing_login_after_errors': (lambda _98: _98 - 1)(0) == 1, 'suggested_first_name': None, 'suggested_last_name': None, 'suggested_full_name': None, 'frl_authorization_token': None, 'post_form_errors': None, 'skip_step_without_errors': (lambda _112: _112 - 1)(0) == 1, 'existing_account_exact_match_checked': (lambda _191: _191 + 1)(0) == 1, 'existing_account_fuzzy_match_checked': (lambda _117: _117 - 1)(0) == 1, 'email_oauth_exists': (lambda _1213: _1213 - 1)(0) == 1, 'confirmation_code_send_error': None, 'consent_jurisdiction_at_gate': None, 'consent_jurisdiction_at_inflow': None, 'pc_enforcement_outcome': None, 'pc_inflow_decision': None, 'is_too_young': (lambda _615: _615 - 1)(0) == 1, 'source_account_type': None, 'whatsapp_installed_on_client': (lambda _617: _617 + 1)(0) == 1, 'confirmation_medium': None, 'source_credentials_type': None, 'source_cuid': None, 'source_account_reg_info': None, 'soap_creation_source': None, 'source_account_type_to_reg_info': None, 'registration_flow_id': dev['flow_id'], 'should_skip_youth_tos': (lambda _121: _121 + 1)(0) == 1, 'is_youth_regulation_flow_complete': (lambda _28: _28 - 1)(0) == 1, 'is_on_cold_start': (lambda _37: _37 - 1)(0) == 1, 'email_prefilled': (lambda _167: _167 - 1)(0) == 1, 'cp_confirmed_by_auto_conf': (lambda _73: _73 - 1)(0) == 1, 'in_sowa_experiment': (lambda _175: _175 - 1)(0) == 1, 'youth_regulation_config': {'isEnabled': (lambda _1614: _1614 + 1)(0) == 1, 'consentJurisdiction': 'VN', 'shouldRaiseAgeGating': (lambda _167: _167 - 1)(0) == 1, 'ageOfConsent': None, 'ageOfParentalConsent': None, 'requiresAgeVerification': (lambda _142: _142 - 1)(0) == 1, 'requiresParentalConsent': (lambda _1318: _1318 - 1)(0) == 1, 'ageThresholdForRegBlocking': None}, 'conf_allow_back_nav_after_change_cp': None, 'conf_bouncing_cliff_screen_type': None, 'conf_show_bouncing_cliff': None, 'eligible_to_flash_call_in_ig4a': (lambda _152: _152 - 1)(0) == 1, 'eligible_to_mo_sms_in_ig4a': (lambda _49: _49 - 1)(0) == 1, 'mo_sms_ent_id': None, 'flash_call_permissions_status': None, 'gms_incoming_call_retriever_eligibility': None, 'attestation_result': None, 'request_data_and_challenge_nonce_string': None, 'confirmed_cp_and_code': None, 'notification_callback_id': None, 'reg_suma_state': 0, 'is_msplit_neutral_choice': (lambda _74: _74 - 1)(0) == 1, 'msg_previous_cp': None, 'ntp_import_source_info': None, 'youth_consent_decision_time': None, 'sk_pipa_consent_given': None, 'should_show_spi_before_conf': (lambda _817: _817 + 1)(0) == 1, 'google_oauth_account': None, 'is_reg_request_from_ig_suma': (lambda _1917: _1917 - 1)(0) == 1, 'is_toa_reg': (lambda _51: _51 - 1)(0) == 1, 'is_threads_public': (lambda _137: _137 - 1)(0) == 1, 'spc_import_flow': (lambda _1118: _1118 - 1)(0) == 1, 'caa_play_integrity_attestation_result': None, 'client_known_key_hash': None, 'flash_call_provider': None, 'is_in_gms_experience': None, 'flash_call_nonce_prefix_details': None, 'spc_birthday_input': (lambda _47: _47 - 1)(0) == 1, 'failed_birthday_year_count': None, 'user_presented_medium_source': None, 'user_opted_out_of_ntp': None, 'is_from_registration_reminder': (lambda _124: _124 - 1)(0) == 1, 'show_youth_reg_in_ig_spc': (lambda _511: _511 - 1)(0) == 1, 'fb_suma_is_high_confidence': None, 'screen_visited': ['CAA_REG_WELCOME_SCREEN'], 'fb_email_login_upsell_skip_suma_post_tos': (lambda _110: _110 - 1)(0) == 1, 'fb_suma_is_from_email_login_upsell': (lambda _813: _813 - 1)(0) == 1, 'fb_suma_is_from_phone_login_upsell': (lambda _17: _17 - 1)(0) == 1, 'should_prefill_cp_in_ar': None, 'ig_partially_created_account_user_id': None, 'ig_partially_created_account_nonce': None, 'ig_partially_created_account_nonce_expiry': None, 'force_sessionless_nux_experience': (lambda _136: _136 - 1)(0) == 1, 'has_seen_suma_landing_page_pre_conf': (lambda _319: _319 - 1)(0) == 1, 'has_seen_suma_candidate_page_pre_conf': (lambda _195: _195 - 1)(0) == 1, 'has_seen_confirmation_screen': (lambda _86: _86 - 1)(0) == 1, 'suma_on_conf_threshold': -1, 'should_show_error_msg': (lambda _1116: _1116 + 1)(0) == 1, 'th_profile_photo_token': None, 'attempted_silent_auth_in_fb': (lambda _1817: _1817 - 1)(0) == 1, 'attempted_silent_auth_in_ig': (lambda _67: _67 - 1)(0) == 1, 'sa_prefetch_callback_id': None, 'cp_suma_results_map': None, 'source_username': None, 'next_uri': None, 'should_use_next_uri': None, 'linking_entry_point': None, 'fb_encrypted_partial_new_account_properties': None, 'starter_pack_name': None, 'starter_pack_creator_user_ids': None, 'wa_data_bundle': None, 'bloks_controller_source': None, 'airwave_registration_code': None, 'is_sessionless_nux': None, 'login_contactpoint': None, 'login_contactpoint_type': None, 'should_show_bday_after_name_suggestions': None, 'should_override_back_nav': (lambda _818: _818 - 1)(0) == 1, 'ig_footer_variant': 'control', 'ig_gender': None, 'device_network_info': None, 'is_from_web_lite_reg_controller': None, 'login_form_siwg_email': None, 'account_setup_waterfall_id': None, 'is_wanted_suma_user': (lambda _16: _16 - 1)(0) == 1, 'device_zero_balance_state': None, 'wa_to_ig_merged_tos_variant': None, 'is_in_nta_single_form': (lambda _152: _152 - 1)(0) == 1, 'source_account_image_asset_id': None, 'passkey_eligible_device': None, 'nta_ac_opted_out': None, 'nta_control_reason': None, 'nta_risk_type': None, 'nta_single_form_variant': None, 'enable_survey': None, 'phone_prefetch_outcome': None, 'tos_accepted_on_profile_info': None}
    current_reg_context = ''
    full_name = '{}{}{}'.format(last_name, ' ', first_name)
    print('{}{}{}'.format('Đang thực hiện Bước 1: Gửi thông tin Tên (', full_name, ')...'))
    client_inputs_1 = {'zero_balance_state': '', 'network_bssid': None, 'lastname': first_name, 'google_id_token': '', 'block_store_machine_id': '', 'firstname': last_name, 'device_network_info': None, 'google_id_email': '', 'lois_settings': {'lois_token': ''}}
    server_inputs_1 = {'INTERNAL__latency_qpl_marker_id': 36707139, 'event_request_id': str(uuid.uuid4()), 'login_surface': 'aymh_one_tap', 'use_single_name_field': 0, 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'access_flow_version': 'pre_mt_behavior', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'flow_info': flow_info_str, 'INTERNAL__latency_qpl_instance_id': 175808452300238, 'login_entry_point': 'logged_out', 'is_from_logged_out': 1, 'layered_homepage_experiment_group': 'not_in_experiment', 'reg_context': current_reg_context, 'reg_info': json.dumps(reg_info_dict), 'current_step': 1, 'flow_modifier': flow_info_str, 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'family_device_id': None}
    payload_step_1 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.name.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.name.async', client_inputs_1, server_inputs_1)}
    try:
        headers_step_1 = headers.copy()
        headers_step_1['x-fb-friendly-name'] = payload_step_1['fb_api_req_friendly_name']
        response_1 = session.post(url, headers=headers_step_1, data=payload_step_1, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 1: HTTP ', response_1.status_code))
        current_reg_context = extract_reg_context(response_1.text, current_reg_context)
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 1: ', e))
    delay_1 = round(random.uniform(2.0, 3.5), 1)
    print('{}{}{}'.format('[*] Chờ ', delay_1, 's (mô phỏng thao tác chọn ngày sinh)...'))
    time.sleep(delay_1)
    birthday_str = '24-09-1966'
    birthday_timestamp = -103249140
    print('{}{}{}'.format('Đang thực hiện Bước 2: Gửi Ngày sinh (', birthday_str, ')...'))
    reg_info_dict['first_name'] = last_name
    reg_info_dict['last_name'] = first_name
    reg_info_dict['full_name'] = full_name
    reg_info_dict['screen_visited'] = ['CAA_REG_WELCOME_SCREEN', 'bloks.caa.reg.birthday']
    client_inputs_2 = {'should_skip_youth_tos': 0, 'block_store_machine_id': '', 'zero_balance_state': '', 'accounts_list': [], 'birthday_or_current_date_string': birthday_str, 'network_bssid': None, 'birthday_timestamp': birthday_timestamp, 'lois_settings': {'lois_token': ''}, 'os_age_range': '', 'client_timezone': 'Asia/Ho_Chi_Minh', 'is_youth_regulation_flow_complete': 0}
    server_inputs_2 = {'is_from_logged_out': 1, 'access_flow_version': 'pre_mt_behavior', 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'reg_context': current_reg_context, 'family_device_id': None, 'layered_homepage_experiment_group': 'not_in_experiment', 'INTERNAL__latency_qpl_instance_id': 175872741300230, 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'login_surface': 'aymh_one_tap', 'flow_info': flow_info_str, 'reg_info': json.dumps(reg_info_dict), 'login_entry_point': 'logged_out', 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'current_step': 2, 'INTERNAL__latency_qpl_marker_id': 36707139}
    payload_step_2 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.birthday.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.birthday.async', client_inputs_2, server_inputs_2)}
    try:
        headers_step_2 = headers.copy()
        headers_step_2['x-fb-friendly-name'] = payload_step_2['fb_api_req_friendly_name']
        response_2 = session.post(url, headers=headers_step_2, data=payload_step_2, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 2: HTTP ', response_2.status_code))
        current_reg_context = extract_reg_context(response_2.text, current_reg_context)
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 2: ', e))
    delay_2 = round(random.uniform(2.0, 3.5), 1)
    print('{}{}{}'.format('[*] Chờ ', delay_2, 's (mô phỏng thao tác chọn giới tính)...'))
    time.sleep(delay_2)
    print('{}{}{}'.format('Đang thực hiện Bước 3: Gửi thông tin Giới tính (', 'Nữ' if gender == 1 else 'Nam', ')...'))
    reg_info_dict['birthday'] = birthday_str
    reg_info_dict['age_range'] = 'o18'
    reg_info_dict['gender'] = gender
    client_inputs_3 = {'device_emails': [], 'gender': gender, 'network_bssid': None, 'lois_settings': {'lois_token': ''}, 'device_phone_numbers': [], 'zero_balance_state': '', 'block_store_machine_id': '', 'pronoun': 0, 'custom_gender': ''}
    server_inputs_3 = {'is_from_logged_out': 1, 'access_flow_version': 'pre_mt_behavior', 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'reg_context': current_reg_context, 'family_device_id': None, 'layered_homepage_experiment_group': 'not_in_experiment', 'INTERNAL__latency_qpl_instance_id': 176167360100158, 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'login_surface': 'aymh_one_tap', 'flow_info': flow_info_str, 'reg_info': json.dumps(reg_info_dict), 'login_entry_point': 'logged_out', 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'current_step': 3, 'INTERNAL__latency_qpl_marker_id': 36707139}
    payload_step_3 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.gender.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.gender.async', client_inputs_3, server_inputs_3)}
    try:
        headers_step_3 = headers.copy()
        headers_step_3['x-fb-friendly-name'] = payload_step_3['fb_api_req_friendly_name']
        response_3 = session.post(url, headers=headers_step_3, data=payload_step_3, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 3: HTTP ', response_3.status_code))
        current_reg_context = extract_reg_context(response_3.text, current_reg_context)
        safe_write_file('step3_debug.json', response_3.text)
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 3: ', e))
    delay_3 = round(random.uniform(2.0, 3.5), 1)
    print('{}{}{}'.format('[*] Chờ ', delay_3, 's (mô phỏng thao tác chuẩn bị thông tin liên hệ)...'))
    time.sleep(delay_3)
    mail_obj = None
    is_phone = email_mode == 'phone' or bool(phone_number)
    if is_phone:
        contact_point = str(phone_number).strip()
        print('{}{}'.format('[*] Sử dụng Số điện thoại đăng ký: ', contact_point))
    elif email_mode == 1:
        email = input('4. Nhập Email đăng ký: ').strip()
        contact_point = email
    elif email_mode == 2:
        print('[*] Đang kết nối 1smail.shop để mua mail Outlook/Hotmail...')
        mail_obj = buy_email_1smail(API_KEY_1SMAIL)
        if not mail_obj:
            print('[-] Không thể mua mail từ 1smail.shop (Hết số dư hoặc lỗi kết nối). Hủy luồng.')
            return 'ERROR'
        mail_obj['type'] = '1smail'
        email = mail_obj['email']
        contact_point = email
        print('{}{}'.format('[+] Mua mail thành công từ 1smail.shop: ', email))
    elif email_mode == 3:
        print('[*] Đang lấy mail ảo miễn phí từ 10minutemail.net...')
        mail_obj = get_10min_email()
        if not mail_obj:
            print('[-] Không thể khởi tạo 10MinuteMail. Hủy luồng.')
            return 'ERROR'
        email = mail_obj['email']
        contact_point = email
        print('{}{}'.format('[+] Lấy thành công 10MinuteMail: ', email))
    elif email_mode == 4:
        print('{}{}{}{}{}'.format('[*] Đang kết nối thuê email OTP (', otp_domain, ' - Server ', otp_server, ')...'))
        mail_obj = rent_email_otp(server=otp_server, domain=otp_domain, service_id=1, price=otp_price)
        if not mail_obj:
            print('[-] Không thể thuê email OTP (Hết số dư hoặc dịch vụ tắt). Hủy luồng.')
            return 'ERROR'
        email = mail_obj['email']
        contact_point = email
        print('{}{}{}{}{}{}{}'.format('[+] Thuê email thành công: ', email, ' (Giá: ', mail_obj.get('price'), 'đ, Số dư ví: ', mail_obj.get('balance'), 'đ)'))
    elif email_mode == 5 and mail_item:
        mail_obj = mail_item
        mail_obj['type'] = 'file'
        email = mail_obj['email']
        contact_point = email
        print('{}{}'.format('[+] Sử dụng mail từ file: ', email))
    elif email_mode == 6 and otptrust_service:
        provider = otptrust_service.get('provider', 'hotmail')
        service_id = otptrust_service.get('service_id', 1)
        api_k = otptrust_service.get('api_key') or API_KEY_OTPTRUST
        p_name = otptrust_service.get('name', provider.upper())
        print('{}{}{}{}{}'.format('[*] Đang kết nối otptrust.com để thuê ', provider.upper(), ' (', p_name, ')...'))
        mail_obj = rent_email_otptrust(api_k, service_id, provider)
        if not mail_obj:
            print('[-] Không thể thuê mail từ otptrust.com (Hết số dư hoặc lỗi dịch vụ). Hủy luồng.')
            return 'ERROR'
        email = mail_obj['email']
        contact_point = email
        print('{}{}{}{}{}'.format('[+] Thuê email thành công từ otptrust.com: ', email, ' (Giá: ', mail_obj.get('price'), ')'))
    else:
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        random_prefix = ''.join((random.choice(chars) for _ in range(random.randint(8, 12))))
        random_domain = random.choice(['@gmail.com', '@icloud.com', '@outlook.com'])
        email = random_prefix + random_domain
        contact_point = email
        print('{}{}'.format('[*] Đã tự động tạo Email: ', email))
    if is_phone:
        print('{}{}{}'.format('Đang thực hiện Bước 4: Gửi thông tin Số điện thoại (', contact_point, ')...'))
        parsed_country = 'VN'
        try:
            import phonenumbers
            from phonenumbers import phonenumberutil
            p_obj = phonenumbers.parse(contact_point, None)
            parsed_country = str(p_obj.country_code) if p_obj.country_code else '84'
        except Exception:
            pass
        reg_info_dict['contactpoint'] = contact_point
        reg_info_dict['contactpoint_type'] = 'phone_number'
        reg_info_dict['screen_visited'] = ['CAA_REG_WELCOME_SCREEN', 'bloks.caa.reg.birthday', 'CAA_REG_CONTACT_POINT_PHONE']
        client_inputs_4 = {'family_device_id': '', 'seen_login_upsell': 0, 'block_store_machine_id': '', 'confirmed_cp_and_code': {}, 'zero_balance_state': '', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'accounts_list': [], 'fb_ig_device_id': [], 'network_bssid': None, 'lois_settings': {'lois_token': ''}, 'has_rejected_rel': 0, 'msg_previous_cp': '', 'phone': contact_point, 'country_code': parsed_country}
        friendly_name_4 = 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.async.contactpoint_phone.async'
        var_query_4 = 'com.bloks.www.bloks.caa.reg.async.contactpoint_phone.async'
        step4_text_input_id = 'vzj9pz:113'
    else:
        print('{}{}{}'.format('Đang thực hiện Bước 4: Gửi thông tin Email (', contact_point, ')...'))
        reg_info_dict['contactpoint'] = contact_point
        reg_info_dict['contactpoint_type'] = 'email'
        reg_info_dict['screen_visited'] = ['CAA_REG_WELCOME_SCREEN', 'bloks.caa.reg.birthday', 'CAA_REG_CONTACT_POINT_PHONE', 'CAA_REG_CONTACT_POINT_EMAIL']
        client_inputs_4 = {'switch_cp_have_seen_suma': 0, 'family_device_id': '', 'seen_login_upsell': 0, 'block_store_machine_id': '', 'confirmed_cp_and_code': {}, 'zero_balance_state': '', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'accounts_list': [], 'fb_ig_device_id': [], 'network_bssid': None, 'email_prefilled': 0, 'lois_settings': {'lois_token': ''}, 'has_rejected_rel': 0, 'msg_previous_cp': '', 'is_from_device_emails': 0, 'email': contact_point, 'switch_cp_first_time_loading': 1}
        friendly_name_4 = 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.async.contactpoint_email.async'
        var_query_4 = 'com.bloks.www.bloks.caa.reg.async.contactpoint_email.async'
        step4_text_input_id = 't7ud3m:28'
    server_inputs_4 = {'INTERNAL__latency_qpl_marker_id': 36707139, 'event_request_id': str(uuid.uuid4()), 'login_surface': 'aymh_one_tap', 'cp_source': 0, 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'access_flow_version': 'pre_mt_behavior', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'flow_info': flow_info_str, 'INTERNAL__latency_qpl_instance_id': 176669307400128, 'cp_funnel': 0, 'login_entry_point': 'logged_out', 'is_from_logged_out': 1, 'text_input_id': step4_text_input_id, 'layered_homepage_experiment_group': 'not_in_experiment', 'reg_info': json.dumps(reg_info_dict), 'current_step': 4, 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'family_device_id': None}
    payload_step_4 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': friendly_name_4, 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables(var_query_4, client_inputs_4, server_inputs_4)}
    try:
        headers_step_4 = headers.copy()
        headers_step_4['x-fb-friendly-name'] = payload_step_4['fb_api_req_friendly_name']
        response_4 = session.post(url, headers=headers_step_4, data=payload_step_4, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 4: HTTP ', response_4.status_code))
        if 'errors' in response_4.text and '"data":{"fb_bloks_action":null}' in response_4.text:
            print('{}{}{}'.format('[-] Facebook từ chối tại Bước 4 (', 'SĐT' if is_phone else 'Email', ').'))
            try:
                err_data = response_4.json().get('errors', [{}])[0]
                summary = err_data.get('summary', 'Lỗi')
                msg = err_data.get('description', err_data.get('message', ''))
                print('{}{}{}{}'.format('    Chi tiết: ', summary, ' - ', msg))
            except Exception:
                pass
            safe_write_file('fb_checkpoint_log.json', response_4.text)
            return 'ERROR'
        current_reg_context = extract_reg_context(response_4.text, current_reg_context)
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 4: ', e))
        return 'ERROR'
    delay_4 = round(random.uniform(2.5, 4.0), 1)
    print('{}{}{}'.format('[*] Chờ ', delay_4, 's (mô phỏng thao tác nhập mật khẩu)...'))
    time.sleep(delay_4)
    password_to_send = password_input if password_input else CLEAN_PWD_WILDE
    password_to_save = password_input if password_input else 'anhem1234'
    print('Đang thực hiện Bước 5: Gửi thông tin Mật khẩu...')
    reg_info_dict['encrypted_password'] = password_to_send
    if is_phone:
        reg_info_dict['screen_visited'] = ['CAA_REG_WELCOME_SCREEN', 'bloks.caa.reg.birthday', 'CAA_REG_CONTACT_POINT_PHONE', 'CAA_REG_PASSWORD']
    else:
        reg_info_dict['screen_visited'] = ['CAA_REG_WELCOME_SCREEN', 'bloks.caa.reg.birthday', 'CAA_REG_CONTACT_POINT_PHONE', 'CAA_REG_CONTACT_POINT_EMAIL', 'CAA_REG_PASSWORD']
    client_inputs_5 = {'block_store_machine_id': '', 'zero_balance_state': '', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'email_oauth_token_map': {}, 'fb_ig_device_id': [], 'network_bssid': None, 'encrypted_password': password_to_send, 'client_known_key_hash': '', 'whatsapp_installed_on_client': 1, 'encrypted_msisdn_for_safetynet': '', 'lois_settings': {'lois_token': ''}, 'safetynet_token': '', 'caa_play_integrity_attestation_result': '', 'has_rejected_rel': 0, 'safetynet_response': '', 'spi_action': 1, 'headers_last_infra_flow_id_safetynet': ''}
    server_inputs_5 = {'INTERNAL__latency_qpl_marker_id': 36707139, 'event_request_id': str(uuid.uuid4()), 'login_surface': 'aymh_one_tap', 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'access_flow_version': 'pre_mt_behavior', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'flow_info': flow_info_str, 'INTERNAL__latency_qpl_instance_id': 176773764300378, 'login_entry_point': 'logged_out', 'is_from_logged_out': 1, 'layered_homepage_experiment_group': 'not_in_experiment', 'reg_context': current_reg_context, 'reg_info': json.dumps(reg_info_dict), 'current_step': 5, 'flow_modifier': flow_info_str, 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'family_device_id': None}
    payload_step_5 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.password.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.password.async', client_inputs_5, server_inputs_5)}
    try:
        headers_step_5 = headers.copy()
        headers_step_5['x-fb-friendly-name'] = payload_step_5['fb_api_req_friendly_name']
        response_5 = session.post(url, headers=headers_step_5, data=payload_step_5, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 5: HTTP ', response_5.status_code))
        if 'errors' in response_5.text and '"data":{"fb_bloks_action":null}' in response_5.text:
            print('[-] Facebook từ chối tại Bước 5 (Mật khẩu).')
            try:
                err_data = response_5.json().get('errors', [{}])[0]
                summary = err_data.get('summary', 'Lỗi')
                msg = err_data.get('description', err_data.get('message', ''))
                print('{}{}{}{}'.format('    Chi tiết: ', summary, ' - ', msg))
            except Exception:
                pass
            safe_write_file('fb_checkpoint_log.json', response_5.text)
            return 'ERROR'
        current_reg_context = extract_reg_context(response_5.text, current_reg_context)
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 5: ', e))
        return 'ERROR'
    delay_5 = round(random.uniform(2.5, 4.5), 1)
    print('{}{}{}'.format('[*] Chờ ', delay_5, 's (mô phỏng thao tác xác nhận tạo tài khoản)...'))
    time.sleep(delay_5)
    print('Đang thực hiện Bước 6: Yêu cầu tạo tài khoản trên hệ thống Facebook...')
    client_inputs_6 = {'ig_partially_created_account_user_id': 0, 'block_store_machine_id': '', 'ck_id': '', 'zero_balance_state': '', 'ck_nonce': '', 'ig_partially_created_account_nonce': '', 'encrypted_msisdn': '', 'failed_birthday_year_count': '', 'ck_error': '', 'network_bssid': None, 'no_contact_perm_email_oauth_token': '', 'lois_settings': {'lois_token': ''}, 'reached_from_tos_screen': 1, 'ig_partially_created_account_nonce_expiry': 0, 'headers_last_infra_flow_id': ''}
    server_inputs_6 = {'INTERNAL__latency_qpl_marker_id': 36707139, 'event_request_id': str(uuid.uuid4()), 'login_surface': 'aymh_one_tap', 'is_from_logged_in_switcher': 0, 'is_platform_login': 0, 'access_flow_version': 'pre_mt_behavior', 'cloud_trust_token': GLOBAL_CLOUD_TRUST_TOKEN, 'flow_info': flow_info_str, 'INTERNAL__latency_qpl_instance_id': 176973951800024, 'login_entry_point': 'logged_out', 'is_from_logged_out': 1, 'layered_homepage_experiment_group': 'not_in_experiment', 'reg_context': current_reg_context, 'reg_info': json.dumps(reg_info_dict), 'current_step': 8, 'bloks_controller_source': 'bk_caa_reg_icon_text_list_tos_screen', 'offline_experiment_group': 'caa_launch_fbios_combined_60_percent', 'family_device_id': None}
    payload_step_6 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.create.account.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.create.account.async', client_inputs_6, server_inputs_6)}
    try:
        headers_step_6 = headers.copy()
        headers_step_6['x-fb-friendly-name'] = payload_step_6['fb_api_req_friendly_name']
        response_6 = session.post(url, headers=headers_step_6, data=payload_step_6, proxies=proxies)
        print('{}{}'.format('Kết quả Bước 6: HTTP ', response_6.status_code))
        uid = None
        uid_match = re.search('["\\\'](?:uid|user_id|actor_id|created_userid)["\\\']\\s*:\\s*["\\\']?(\\d{10,20})["\\\']?', response_6.text)
        if uid_match:
            uid = uid_match.group(1)
        else:
            backup_match = re.search('(1000\\d{11}|615\\d{11,12})', response_6.text)
            if backup_match:
                uid = backup_match.group(1)
        if not uid and session.cookies.get('c_user'):
            uid = session.cookies.get('c_user')
        if uid:
            print('{}'.format('\n[+] BÙM! TẠO TÀI KHOẢN THÀNH CÔNG!'))
            print('{}{}'.format('[+] UID: ', uid))
            print('{}{}{}{}'.format('[+] ', 'Số điện thoại' if is_phone else 'Email', ': ', contact_point))
            access_token = None
            token_match = re.search('(EAAAA[a-zA-Z0-9]+)', response_6.text)
            if token_match:
                access_token = token_match.group(1)
            otp_code = None
            if phone_obj and phone_obj.get('type') == '2oo9':
                no_plus = phone_obj.get('no_plus')
                current_2oo9_key = phone_obj.get('api_key') or API_KEY_2OO9
                print('{}{}{}'.format('[*] Đang tự động đợi SMS OTP từ 2oo9.cloud (', no_plus, ')...'))
                otp_res = check_otp_2oo9(no_plus, api_key=current_2oo9_key, wait_time=75, interval=4)
                if otp_res:
                    msg = str(otp_res.get('message', ''))
                    code_match = re.search('\\b(\\d{5,8})\\b', msg)
                    if code_match:
                        otp_code = code_match.group(1)
                    else:
                        otp_code = msg.strip()
                    print('{}{}'.format('\n[+] TỰ ĐỘNG BẮT ĐƯỢC SMS OTP: ', otp_code))
                else:
                    print('\n[-] Không nhận được SMS OTP từ 2oo9.cloud trong thời gian chờ.')
            elif phone_obj and phone_obj.get('type') == 'autosms':
                order_id = phone_obj.get('order_id')
                autosms_key = phone_obj.get('api_key') or AUTOSMS_API_KEY
                print('{}{}{}'.format('[*] Đang tự động đợi SMS OTP từ autosms.site (Order ID: ', order_id, ')...'))
                otp_code = check_otp_autosms(order_id, api_key=autosms_key, wait_time=90, interval=4)
                if otp_code:
                    print('{}{}'.format('\n[+] TỰ ĐỘNG BẮT ĐƯỢC SMS OTP: ', otp_code))
                else:
                    print('\n[-] Không nhận được SMS OTP từ autosms.site trong thời gian chờ.')
                    print('[*] Đang tự động gửi lệnh hủy đơn hàng và hoàn tiền...')
                    c_res = cancel_order_autosms(order_id, api_key=autosms_key)
                    if c_res and c_res.get('success'):
                        print('{}{}'.format('[+] Hoàn tiền thành công: ', c_res.get('message', 'Đã hủy đơn')))
            elif mail_obj:
                mail_type = mail_obj.get('type')
                if mail_type == 'email_otp' and mail_obj.get('rental_id'):
                    print('{}{}{}{}{}'.format('[*] Đang tự động đợi và lấy mã OTP từ Email OTP Server ', otp_server, ' (', email, ')...'))
                    otp_code = poll_email_otp(mail_obj['rental_id'], timeout_sec=120)
                    if not otp_code:
                        print('[*] Hết thời gian chờ OTP, đang tự động gửi lệnh hủy/hoàn tiền...')
                        cancel_res = cancel_email_otp(mail_obj['rental_id'])
                        if cancel_res and cancel_res.get('success'):
                            print('{}{}{}'.format('[+] Hoàn tiền thành công: ', cancel_res.get('data', {}).get('refund'), 'đ'))
                elif mail_type == '10min' and mail_obj.get('session'):
                    print('{}{}{}'.format('[*] Đang tự động đợi và lấy mã OTP từ 10MinuteMail (', email, ')...'))
                    otp_code = get_10min_otp(mail_obj['session'], timeout_sec=90)
                elif mail_type == 'otptrust' and mail_obj.get('order_id'):
                    provider_tag = mail_obj.get('provider', 'mail').upper()
                    print('{}{}{}{}{}'.format('[*] Đang tự động đợi và lấy mã OTP từ otptrust.com (', provider_tag, ' - ', email, ')...'))
                    otp_code = poll_otp_otptrust(mail_obj['order_id'], mail_obj.get('api_key', API_KEY_OTPTRUST), timeout_sec=120)
                    if not otp_code:
                        print('[*] Hết thời gian chờ OTP, đang tự động gửi lệnh hủy đơn otptrust.com...')
                        cancel_email_otptrust(mail_obj['order_id'], mail_obj.get('api_key', API_KEY_OTPTRUST))
                elif mail_obj.get('refresh_token') and mail_obj.get('client_id'):
                    print('{}{}{}'.format('[*] Đang tự động đợi và lấy mã OTP từ email (', email, ')...'))
                    otp_code = get_otp_oautcallable(mail_obj['email'], mail_obj['password'], mail_obj['refresh_token'], mail_obj['client_id'], timeout_sec=90)
                if otp_code:
                    print('{}{}'.format('\n[+] TỰ ĐỘNG BẮT ĐƯỢC MÃ OTP: ', otp_code))
                else:
                    print('\n[-] Không tự động bắt được OTP trong thời gian chờ.')
            if not otp_code:
                otp_code = input('{}{}{}'.format('[?] Nhập mã xác nhận (OTP) gửi về ', contact_point, ': ')).strip()
            print('{}{}{}'.format('Đang thực hiện Bước 7: Xác nhận mã OTP (', otp_code, ') để hoàn tất...'))
            reg_info_dict['user_id'] = str(uid)
            reg_info_dict['contactpoint'] = contact_point
            reg_info_dict['contactpoint_type'] = 'phone_number' if is_phone else 'email'
            reg_info_dict['confirmation_code'] = otp_code
            client_inputs_7 = {'confirmed_cp_and_code': {}, 'lois_settings': {'lois_token': ''}, 'network_bssid': None, 'cloud_trust_token': None, 'code': otp_code, 'family_device_id': '', 'block_store_machine_id': '', 'fb_ig_device_id': []}
            server_inputs_7 = {'is_from_logged_out': 0, 'offline_experiment_group': None, 'family_device_id': None, 'layered_homepage_experiment_group': None, 'wa_timer_id': 'wa_retriever', 'INTERNAL__latency_qpl_instance_id': int(time.time() * 1000), 'event_request_id': str(uuid.uuid4()), 'login_surface': 'unknown', 'sms_retriever_started_prior_step': 0, 'flow_info': flow_info_str, 'reg_info': json.dumps(reg_info_dict), 'text_input_id': 'yqncc:57', 'is_platform_login': 0, 'current_step': 10, 'is_from_logged_in_switcher': 0, 'INTERNAL__latency_qpl_marker_id': 36707139, 'access_flow_version': 'pre_mt_behavior'}
            payload_step_7 = {'method': 'post', 'pretty': 'false', 'format': 'json', 'server_timestamps': 'true', 'locale': 'vi_VN', 'purpose': 'fetch', 'fb_api_req_friendly_name': 'FBBloksActionRootQuery-com.bloks.www.bloks.caa.reg.confirmation.async', 'client_doc_id': '375801096012207349486705547963', 'variables': create_nested_variables('com.bloks.www.bloks.caa.reg.confirmation.async', client_inputs_7, server_inputs_7)}
            headers_step_7 = headers.copy()
            headers_step_7['x-fb-friendly-name'] = payload_step_7['fb_api_req_friendly_name']
            if access_token:
                headers_step_7['authorization'] = '{}{}'.format('OAuth ', access_token)
            try:
                response_7 = session.post(url, headers=headers_step_7, data=payload_step_7, proxies=proxies)
                print('{}{}'.format('Kết quả Bước 7 (Xác nhận OTP): HTTP ', response_7.status_code))
                if 'CAA_REG_CONFIRMATION:is_confirmed' in response_7.text and 'true' in response_7.text.lower():
                    print('{}{}{}'.format('[+] XÁC NHẬN OTP THÀNH CÔNG CHO ', contact_point, '!'))
                else:
                    print('[-] LỖI XÁC NHẬN OTP: Mã không hợp lệ hoặc Facebook từ chối (có thể do IP/Thiết bị).')
            except Exception as e:
                print('{}{}'.format('Lỗi Bước 7: ', e))
            print('\n[*] Đang ngâm tài khoản 10s trước khi kiểm tra trạng thái Live/Die...')
            for sec in range(10, 0, -1):
                print('{}{}{}'.format('[*] Đang ngâm tài khoản... (', sec, 's)'), end='\r')
                time.sleep(1)
            print(' ' * 50, end='\r')
            print('{}{}{}'.format('[*] Đang kiểm tra Live/Die cho UID ', uid, '...'))
            is_live, name = check_live_die(str(uid), proxies=proxies, token=access_token, fallback_name=full_name)
            if is_live:
                print('{}{}{}{}'.format('[\x1b[1;32mLIVE\x1b[0m] UID: ', uid, ' | Tên: ', name))
                print('[*] Đang tự động trích xuất Cookie và Token...')
                sess_cookie = extract_session_cookies(session, response_7.text if 'response_7' in locals() else '')
                token_eaaau, cookie_android = get_token_eaaau_and_cookie(uid, password_to_save, proxies=proxies)
                final_cookie = cookie_android or sess_cookie or ''
                final_token = access_token or token_eaaau or ''
                if final_cookie:
                    print('{}{}'.format('[+] Cookie: ', final_cookie))
                if access_token:
                    print('{}{}'.format('[+] Token iOS (EAAAAY): ', access_token))
                if token_eaaau:
                    print('{}{}'.format('[+] Token Android (EAAAU): ', token_eaaau))
                mail_part = mail_obj['raw'] if mail_obj and mail_obj.get('raw') else contact_point
                full_info_line = '{}{}{}{}{}{}{}{}{}'.format(uid, '|', password_to_save, '|', final_cookie, '|', final_token, '|', mail_part)
                safe_append_file('acc_fb_thanhcong.txt', full_info_line)
                return 'LIVE'
            else:
                print('{}{}{}'.format('[\x1b[1;31mDIE / CHECKPOINT\x1b[0m] UID: ', uid, ' (Bị Checkpoint hoặc chưa public trang cá nhân)'))
                mail_part = mail_obj['raw'] if mail_obj and mail_obj.get('raw') else contact_point
                safe_append_file('acc_fb_die_checkpoint.txt', '{}{}{}{}{}'.format(uid, '|', password_to_save, '|', mail_part))
                return 'DIE'
        else:
            print('[-] Không tìm thấy UID (Tài khoản bị block/checkpoint dạng màn hình).')
            safe_write_file('fb_checkpoint_log.json', response_6.text)
            print("[*] Đã lưu mã nguồn màn hình chặn vào file 'fb_checkpoint_log.json'.")
            try:
                decoded_text = response_6.text.encode('utf-8').decode('unicode_escape')
                print('\n[!] NỘI DUNG MÀN HÌNH CHẶN TỪ FACEBOOK:')
                texts = re.findall('([A-ZĐ][^\\\\]{15,})', decoded_text)
                found_msg = (lambda _32: _32 - 1)(0) == 1
                for t in set(texts):
                    if any((keyword in t for keyword in ['bạn', 'Tài khoản', 'Chúng tôi', 'Vi phạm', 'Tiêu chuẩn', 'Xác minh', 'vô hiệu hóa', 'nhập mã', 'số điện thoại'])):
                        print('{}{}'.format('  -> ', t))
                        found_msg = (lambda _512: _512 + 1)(0) == 1
                if not found_msg:
                    print('  -> (Tài khoản bị kẹt ở bước xác minh ẩn, Captcha, hoặc Integrity Block)')
            except Exception:
                pass
            return 'DIE'
    except Exception as e:
        print('{}{}'.format('Lỗi Bước 6: ', e))
        return 'ERROR'
VIETNAMESE_FIRST_NAMES = ['Quang', 'Huy', 'Anh', 'Minh', 'Tuan', 'Dung', 'Nam', 'Thang', 'Duc', 'Hoang', 'Long', 'Khoa', 'Phong', 'Thanh', 'Hieu', 'Linh', 'Trang', 'Huong', 'Ha', 'Phuong', 'Mai', 'Ngoc', 'Lan', 'Vy', 'Yen']
VIETNAMESE_LAST_NAMES = ['Nguyen', 'Tran', 'Le', 'Pham', 'Hoang', 'Huynh', 'Phan', 'Vu', 'Vo', 'Dang', 'Bui', 'Do', 'Ho', 'Ngo', 'Duong', 'Ly']
if __name__ == '__main__':
    print('=' * 45)
    print('      BỘ ĐĂNG KÝ FACEBOOK (iOS)')
    print('=' * 45)
    print('1. Reg bằng Mail')
    print('2. Reg bằng SĐT')
    print('3. Quản lý / Kiểm tra số dư API Key')
    print('-' * 45)
    choice = input('[?] Chọn (1-3): ').strip()
    if choice == '1':
        print('\n--- CHỌN LOẠI MAIL ---')
        print('1. Thuê iCloud (metaking.top)')
        print('2. Mua Hotmail (1smail.shop)')
        print('3. Mail ảo miễn phí (10minutemail)')
        print('4. File mail (mail.txt)')
        print('5. Tùy chỉnh nâng cao (metaking.top)')
        print('6. Thuê Mail OTP từ otptrust.com (Hotmail, Outlook, iCloud, Gmail...)')
        mail_choice = input('[?] Chọn nguồn mail (1-6): ').strip()
        if mail_choice in ['1', '2', '3']:
            if mail_choice == '1':
                curr_k = EMAIL_OTP_API_KEY or ''
                preview = '{}{}{}'.format(curr_k[:8], '...', curr_k[-4:]) if len(curr_k) > 12 else curr_k or 'chưa có'
                key_in = input('{}{}{}'.format('[?] Nhập API Key metaking (Enter để dùng: ', preview, '): ')).strip()
                if key_in:
                    EMAIL_OTP_API_KEY = key_in
                    update_single_api_key('metaking_api_key', key_in)
                print('[*] Đang kiểm tra số dư metaking.top...')
                bal = get_metaking_balance(EMAIL_OTP_API_KEY)
                if bal is not None:
                    print('{}{}{}'.format('[+] Số dư metaking.top: ', bal, ' VNĐ'))
                else:
                    print('[-] Không lấy được số dư metaking.top (Vui lòng kiểm tra lại API Key hoặc mạng)!')
            elif mail_choice == '2':
                curr_k = API_KEY_1SMAIL or ''
                preview = '{}{}{}'.format(curr_k[:8], '...', curr_k[-4:]) if len(curr_k) > 12 else curr_k or 'chưa có'
                key_in = input('{}{}{}'.format('[?] Nhập API Key 1smail.shop (Enter để dùng: ', preview, '): ')).strip()
                if key_in:
                    API_KEY_1SMAIL = key_in
                    update_single_api_key('1smail_api_key', key_in)
                print('[*] Đang kiểm tra tài khoản 1smail.shop...')
                bal_info = get_1smail_balance(API_KEY_1SMAIL)
                if bal_info:
                    print('{}{}{}{}{}'.format('[+] Tài khoản: ', bal_info.get('username', ''), ' | Số dư: ', bal_info.get('balance', 0), ' VNĐ'))
                else:
                    print('[-] Không lấy được số dư 1smail.shop (Vui lòng kiểm tra lại API Key hoặc mạng)!')
            num_input = input('[?] Số lượng acc: ').strip()
            num_accs = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 1
            delay_sec = prompt_delay_between_accs()
            proxy_list = prompt_proxy_source()
            stats = {'total': num_accs, 'live': 0, 'die': 0, 'error': 0}
            mode_map = {'1': 4, '2': 2, '3': 3}
            mode = mode_map[mail_choice]
            for i in range(num_accs):
                fn = random.choice(VIETNAMESE_FIRST_NAMES)
                ln = random.choice(VIETNAMESE_LAST_NAMES)
                gd = random.choice([1, 2])
                cur_proxy = get_proxy_for_run(proxy_list, i)
                print('{}{}{}{}{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', num_accs, ' (', ln, ' ', fn, ') ', '=' * 15))
                if mode == 4:
                    status = facebook_registration_flow(fn, ln, gd, cur_proxy, 4, '', otp_server=1, otp_domain='icloud.com', otp_price='low')
                else:
                    status = facebook_registration_flow(fn, ln, gd, cur_proxy, mode, '')
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                if i < num_accs - 1:
                    countdown_delay(delay_sec)
            print_registration_summary(stats)
        elif mail_choice == '4':
            file_path = input('[?] File mail (Enter = mail.txt): ').strip() or 'mail.txt'
            if not os.path.exists(file_path):
                print('{}{}'.format('[-] Không tìm thấy file: ', file_path))
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip() and '|' in l]
                print('{}{}{}'.format('[+] Tìm thấy ', len(lines), ' mail trong file.'))
                if lines:
                    delay_sec = prompt_delay_between_accs()
                    proxy_list = prompt_proxy_source()
                    stats = {'total': len(lines), 'live': 0, 'die': 0, 'error': 0}
                    for i, line in enumerate(lines):
                        parts = line.split('|')
                        mail_item = {'email': parts[0].strip(), 'password': parts[1].strip() if len(parts) > 1 else '', 'refresh_token': parts[2].strip() if len(parts) > 2 else '', 'client_id': parts[3].strip() if len(parts) > 3 else '', 'raw': line}
                        fn = random.choice(VIETNAMESE_FIRST_NAMES)
                        ln = random.choice(VIETNAMESE_LAST_NAMES)
                        gd = random.choice([1, 2])
                        cur_proxy = get_proxy_for_run(proxy_list, i)
                        print('{}{}{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', len(lines), ' (', mail_item['email'], ') ', '=' * 15))
                        status = facebook_registration_flow(fn, ln, gd, cur_proxy, 5, '', mail_item=mail_item)
                        if status == 'LIVE':
                            stats['live'] += 1
                        elif status == 'DIE':
                            stats['die'] += 1
                        else:
                            stats['error'] += 1
                        if i < len(lines) - 1:
                            countdown_delay(delay_sec)
                    print_registration_summary(stats)
        elif mail_choice == '5':
            curr_k = EMAIL_OTP_API_KEY or ''
            preview = '{}{}{}'.format(curr_k[:8], '...', curr_k[-4:]) if len(curr_k) > 12 else curr_k or 'chưa có'
            key_in = input('{}{}{}'.format('[?] Nhập API Key metaking (Enter để dùng: ', preview, '): ')).strip()
            if key_in:
                EMAIL_OTP_API_KEY = key_in
                update_single_api_key('metaking_api_key', key_in)
            bal = get_metaking_balance(EMAIL_OTP_API_KEY)
            if bal is not None:
                print('{}{}{}'.format('[+] Số dư metaking.top: ', bal, ' VNĐ'))
            fn_in = input('[?] Tên (Enter = random): ').strip()
            ln_in = input('[?] Họ (Enter = random): ').strip()
            gd_in = input('[?] Giới tính (1=Nữ, 2=Nam, Enter=Random): ').strip()
            gd = int(gd_in) if gd_in in ['1', '2'] else random.choice([1, 2])
            pwd_in = input('[?] Mật khẩu (Enter dùng mặc định): ').strip()
            server_in = input('[?] Server metaking (1-5, Enter=1): ').strip()
            otp_server = int(server_in) if server_in in ['1', '2', '3', '4', '5'] else 1
            domain_in = input('[?] Domain (1=icloud.com, 2=gmail.com, 3=hotmail.com): ').strip()
            domain_map = {'1': 'icloud.com', '2': 'gmail.com', '3': 'hotmail.com'}
            otp_domain = domain_map.get(domain_in, 'icloud.com')
            num_in = input('[?] Số lượng acc: ').strip()
            num_accs = int(num_in) if num_in.isdigit() and int(num_in) > 0 else 1
            delay_sec = prompt_delay_between_accs()
            proxy_list = prompt_proxy_source()
            stats = {'total': num_accs, 'live': 0, 'die': 0, 'error': 0}
            for i in range(num_accs):
                fn = fn_in if fn_in else random.choice(VIETNAMESE_FIRST_NAMES)
                ln = ln_in if ln_in else random.choice(VIETNAMESE_LAST_NAMES)
                cur_proxy = get_proxy_for_run(proxy_list, i)
                print('{}{}{}{}{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', num_accs, ' (', ln, ' ', fn, ') ', '=' * 15))
                status = facebook_registration_flow(fn, ln, gd, cur_proxy, 4, pwd_in, otp_server=otp_server, otp_domain=otp_domain)
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                if i < num_accs - 1:
                    countdown_delay(delay_sec)
            print_registration_summary(stats)
        elif mail_choice == '6':
            curr_k = API_KEY_OTPTRUST or ''
            preview = '{}{}{}'.format(curr_k[:8], '...', curr_k[-4:]) if len(curr_k) > 12 else curr_k or 'chưa có'
            key_in = input('{}{}{}'.format('[?] Nhập API Key otptrust.com (Enter để dùng: ', preview, '): ')).strip()
            if key_in:
                API_KEY_OTPTRUST = key_in
                update_single_api_key('otptrust_api_key', key_in)
            fb_options = get_otptrust_facebook_options(API_KEY_OTPTRUST)
            print('\n--- DANH SÁCH GÓI MAIL FACEBOOK TRÊN OTPTRUST.COM ---')
            for idx, opt in enumerate(fb_options, 1):
                print('{}{}{}{}{}{}{}{}'.format('[', idx, '] ', opt['name'], ' | Giá: ', opt['price'], ' | Còn lại: ', opt['available']))
            pkg_input = input('{}{}{}'.format('\n[?] Chọn hàng cần mua (1-', len(fb_options), ', Enter mặc định 1): ')).strip()
            pkg_idx = int(pkg_input) - 1 if pkg_input.isdigit() and 1 <= int(pkg_input) <= len(fb_options) else 0
            selected_pkg = fb_options[pkg_idx]
            print('{}{}{}{}{}'.format('[+] Bạn đã chọn: ', selected_pkg['name'], ' (Giá: ', selected_pkg['price'], ')'))
            num_input = input('[?] Số lượng acc: ').strip()
            num_accs = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 1
            delay_sec = prompt_delay_between_accs()
            proxy_list = prompt_proxy_source()
            stats = {'total': num_accs, 'live': 0, 'die': 0, 'error': 0}
            for i in range(num_accs):
                fn = random.choice(VIETNAMESE_FIRST_NAMES)
                ln = random.choice(VIETNAMESE_LAST_NAMES)
                gd = random.choice([1, 2])
                cur_proxy = get_proxy_for_run(proxy_list, i)
                print('{}{}{}{}{}{}{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', num_accs, ' (', ln, ' ', fn, ' - ', selected_pkg['provider'].upper(), ') ', '=' * 15))
                status = facebook_registration_flow(fn, ln, gd, cur_proxy, 6, '', otptrust_service=selected_pkg)
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                if i < num_accs - 1:
                    countdown_delay(delay_sec)
            print_registration_summary(stats)
        else:
            print('[-] Lựa chọn không hợp lệ!')
    elif choice == '2':
        print('\n--- CHỌN NGUỒN SỐ ĐIỆN THOẠI ---')
        print('1. Tự động thuê số (API 2oo9.cloud)')
        print('2. Tự động thuê số (API autosms.site)')
        print('3. Nhập số điện thoại thủ công')
        phone_opt = input('[?] Chọn (1-3): ').strip()
        if phone_opt == '1':
            curr_k = API_KEY_2OO9 or 'MFBLMYLMLY6'
            api_key_custom = input('{}{}{}'.format('[?] Nhập API Key 2oo9 (Enter dùng mặc định ', curr_k, '): ')).strip() or curr_k
            if api_key_custom != API_KEY_2OO9:
                API_KEY_2OO9 = api_key_custom
                update_single_api_key('2oo9_api_key', api_key_custom)
            target_rid_input = input('[?] Dải số rid (Enter để tự động quét 34 dải Facebook): ').strip() or None
            num_input = input('[?] Số lượng acc: ').strip()
            num_accs = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 1
            delay_sec = prompt_delay_between_accs()
            proxy_list = prompt_proxy_source()
            stats = {'total': num_accs, 'live': 0, 'die': 0, 'error': 0}
            for i in range(num_accs):
                print('{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', num_accs, ' (SĐT 2oo9.cloud) ', '=' * 15))
                phone_item = rent_sim_2oo9(api_key=api_key_custom, target_rid=target_rid_input)
                if not phone_item:
                    print('[-] Không lấy được số từ 2oo9.cloud (Hết số hoặc API Key chưa đúng). Dừng tiến trình.')
                    stats['error'] += num_accs - i
                    break
                fn = random.choice(VIETNAMESE_FIRST_NAMES)
                ln = random.choice(VIETNAMESE_LAST_NAMES)
                gd = random.choice([1, 2])
                cur_proxy = get_proxy_for_run(proxy_list, i)
                status = facebook_registration_flow(fn, ln, gd, cur_proxy, 'phone', '', phone_number=phone_item['phone'], phone_obj=phone_item)
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                if i < num_accs - 1:
                    countdown_delay(delay_sec)
            print_registration_summary(stats)
        elif phone_opt == '2':
            curr_k = AUTOSMS_API_KEY or ''
            preview = '{}{}{}'.format(curr_k[:8], '...', curr_k[-4:]) if len(curr_k) > 12 else curr_k or 'chưa có'
            api_key_custom = input('{}{}{}'.format('[?] Nhập API Key autosms.site (Enter để dùng: ', preview, '): ')).strip()
            if api_key_custom:
                AUTOSMS_API_KEY = api_key_custom
                update_single_api_key('autosms_api_key', api_key_custom)
            print('[*] Đang kiểm tra số dư autosms.site...')
            bal_info = get_autosms_balance(AUTOSMS_API_KEY)
            if bal_info:
                print('{}{}{}{}{}'.format('[+] Tài khoản autosms: ', bal_info.get('username', ''), ' | Số dư: ', bal_info.get('balance', 0), ' VNĐ'))
            else:
                print('[-] Không lấy được số dư autosms.site (Vui lòng kiểm tra lại API Key hoặc mạng)!')
            country_in = input('[?] Mã quốc gia (ví dụ: us, vn, kh - Enter = us): ').strip().lower() or 'us'
            num_input = input('[?] Số lượng acc: ').strip()
            num_accs = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 1
            delay_sec = prompt_delay_between_accs()
            proxy_list = prompt_proxy_source()
            stats = {'total': num_accs, 'live': 0, 'die': 0, 'error': 0}
            for i in range(num_accs):
                print('{}{}{}{}{}{}{}{}{}{}'.format('\n', '=' * 15, ' ĐANG CHẠY ACC ', i + 1, '/', num_accs, ' (SĐT autosms.site - ', country_in.upper(), ') ', '=' * 15))
                phone_item = rent_sim_autosms(country=country_in, service='facebook', api_key=AUTOSMS_API_KEY)
                if not phone_item:
                    print('[-] Không lấy được số từ autosms.site (Hết số hoặc lỗi API). Dừng tiến trình.')
                    stats['error'] += num_accs - i
                    break
                fn = random.choice(VIETNAMESE_FIRST_NAMES)
                ln = random.choice(VIETNAMESE_LAST_NAMES)
                gd = random.choice([1, 2])
                cur_proxy = get_proxy_for_run(proxy_list, i)
                status = facebook_registration_flow(fn, ln, gd, cur_proxy, 'phone', '', phone_number=phone_item['phone'], phone_obj=phone_item)
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                if i < num_accs - 1:
                    countdown_delay(delay_sec)
            print_registration_summary(stats)
        elif phone_opt == '3':
            phone_input = input('\n[?] Nhập số điện thoại (ví dụ: +84912345678): ').strip()
            if not phone_input:
                print('[-] Số điện thoại không được để trống!')
            else:
                proxy_list = prompt_proxy_source()
                cur_proxy = get_proxy_for_run(proxy_list, 0)
                stats = {'total': 1, 'live': 0, 'die': 0, 'error': 0}
                fn = random.choice(VIETNAMESE_FIRST_NAMES)
                ln = random.choice(VIETNAMESE_LAST_NAMES)
                gd = random.choice([1, 2])
                print('{}{}{}'.format('\n[*] Đang đăng ký với SĐT: ', phone_input, '...'))
                status = facebook_registration_flow(fn, ln, gd, cur_proxy, 'phone', '', phone_number=phone_input)
                if status == 'LIVE':
                    stats['live'] += 1
                elif status == 'DIE':
                    stats['die'] += 1
                else:
                    stats['error'] += 1
                print_registration_summary(stats)
        else:
            print('[-] Lựa chọn không hợp lệ!')
    elif choice == '3':
        print('\n' + '=' * 45)
        print('      QUẢN LÝ CẤU HÌNH API KEY & SỐ DƯ')
        print('=' * 45)
        print('{}'.format('1. Metaking.top (iCloud/Mail OTP):'))
        print('{}{}{}{}'.format('   -> Key hiện tại: ', EMAIL_OTP_API_KEY[:8], '...', EMAIL_OTP_API_KEY[-4:] if EMAIL_OTP_API_KEY else 'Chưa có'))
        bal_meta = get_metaking_balance(EMAIL_OTP_API_KEY)
        if bal_meta is not None:
            print('{}{}{}'.format('   -> Số dư: ', bal_meta, ' VNĐ'))
        else:
            print('{}'.format('   -> Số dư: [Không kiểm tra được]'))
        print('{}'.format('\n2. 1smail.shop (Hotmail):'))
        print('{}{}{}{}'.format('   -> Key hiện tại: ', API_KEY_1SMAIL[:8], '...', API_KEY_1SMAIL[-4:] if API_KEY_1SMAIL else 'Chưa có'))
        bal_1s = get_1smail_balance(API_KEY_1SMAIL)
        if bal_1s:
            print('{}{}{}{}{}'.format('   -> Tài khoản: ', bal_1s.get('username', ''), ' | Số dư: ', bal_1s.get('balance', 0), ' VNĐ'))
        else:
            print('{}'.format('   -> Số dư: [Không kiểm tra được]'))
        print('{}'.format('\n3. 2oo9.cloud (SMS OTP):'))
        print('{}{}'.format('   -> Key hiện tại: ', API_KEY_2OO9))
        print('{}'.format('\n4. Autosms.site (SMS OTP):'))
        print('{}{}{}{}'.format('   -> Key hiện tại: ', AUTOSMS_API_KEY[:8], '...', AUTOSMS_API_KEY[-4:] if AUTOSMS_API_KEY else 'Chưa có'))
        bal_auto = get_autosms_balance(AUTOSMS_API_KEY)
        if bal_auto:
            print('{}{}{}{}{}'.format('   -> Tài khoản: ', bal_auto.get('username', ''), ' | Số dư: ', bal_auto.get('balance', 0), ' VNĐ'))
        else:
            print('{}'.format('   -> Số dư: [Không kiểm tra được]'))
        print('{}'.format('\n5. Otptrust.com (Mail OTP):'))
        print('{}{}{}{}'.format('   -> Key hiện tại: ', API_KEY_OTPTRUST[:8], '...', API_KEY_OTPTRUST[-4:] if API_KEY_OTPTRUST else 'Chưa có'))
        print('\n' + '-' * 45)
        edit_c = input('[?] Chọn dịch vụ muốn đổi API Key (1-5, hoặc Enter để thoát): ').strip()
        if edit_c == '1':
            new_k = input('[?] Nhập API Key metaking.top mới: ').strip()
            if new_k:
                EMAIL_OTP_API_KEY = new_k
                update_single_api_key('metaking_api_key', new_k)
                print('[+] Đã lưu API Key metaking.top vào config_api.json!')
        elif edit_c == '2':
            new_k = input('[?] Nhập API Key 1smail.shop mới: ').strip()
            if new_k:
                API_KEY_1SMAIL = new_k
                update_single_api_key('1smail_api_key', new_k)
                print('[+] Đã lưu API Key 1smail.shop vào config_api.json!')
        elif edit_c == '3':
            new_k = input('[?] Nhập API Key 2oo9.cloud mới: ').strip()
            if new_k:
                API_KEY_2OO9 = new_k
                update_single_api_key('2oo9_api_key', new_k)
                print('[+] Đã lưu API Key 2oo9.cloud vào config_api.json!')
        elif edit_c == '4':
            new_k = input('[?] Nhập API Key autosms.site mới: ').strip()
            if new_k:
                AUTOSMS_API_KEY = new_k
                update_single_api_key('autosms_api_key', new_k)
                print('[+] Đã lưu API Key autosms.site vào config_api.json!')
        elif edit_c == '5':
            new_k = input('[?] Nhập API Key otptrust.com mới: ').strip()
            if new_k:
                API_KEY_OTPTRUST = new_k
                update_single_api_key('otptrust_api_key', new_k)
                print('[+] Đã lưu API Key otptrust.com vào config_api.json!')
    else:
        print('[-] Lựa chọn không hợp lệ!')
