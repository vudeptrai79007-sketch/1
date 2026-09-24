import os
import sys
import time
import json
import re
from datetime import datetime
import random
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests

# ================= BẢNG MÀU ANSI =================
xuong = "\n"
do = "\033[1;91m"
maufulldo = "\033[1;47;31m"
maunenhong = "\033[1;41;33m"
red = "\033[1;31m"
pink = "\033[1;35m"
green = "\033[1;32m"
yellow = "\033[1;33m"
white = "\033[0;37m"
cyan = "\033[1;36m"
blue = "\033[1;34m"
cam = "\033[38;5;208m"
reset = "\033[0m"

# ================= BANNER HUY VŨ =================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{cyan}
 ██╗  ██╗██╗   ██╗██╗   ██╗    ██╗   ██╗██╗   ██╗
 ██║  ██║██║   ██║╚██╗ ██╔╝    ██║   ██║██║   ██║
 ███████║██║   ██║ ╚████╔╝     ██║   ██║██║   ██║
 ██╔══██║██║   ██║  ╚██╔╝      ╚██╗ ██╔╝██║   ██║
 ██║  ██║╚██████╔╝   ██║        ╚████╔╝ ╚██████╔╝
 ╚═╝  ╚═╝ ╚═════╝    ╚═╝         ╚═══╝   ╚═════╝ {reset}
{yellow} ┌────────────────────────────────────────────────────────┐
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API MULTI-THREAD V2{yellow}│
{yellow} │ {pink}📌 Bản quyền: {white}Huy Vũ                                   {yellow}│
{yellow} │ {cyan}☕ Donate MoMo: {green}0373607456                             {yellow}│
{yellow} └────────────────────────────────────────────────────────┘{reset}
""")

# ================= CLASS API XSMM V2 =================
class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_accounts(self, account_type=None, search=None):
        url = f"{self.base_url}/accounts2"
        params = {}
        if account_type:
            params['account_type'] = account_type
        if search:
            params['search'] = search
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_account(self, account_type, link_account):
        url = f"{self.base_url}/accounts2"
        payload = {
            "type": account_type,
            "link_account": link_account
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        url = f"{self.base_url}/tasks2"
        params = {
            "type": job_type,
            "uid": str(uid),
            "typejob": typejob
        }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        url = f"{self.base_url}/tasks2/complete"
        payload = {
            "type": job_type,
            "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
            "uid": str(uid)
        }
        if cookie_check:
            payload["cookie_check"] = cookie_check
        
        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=35)
                res_data = response.json()
                
                # Tự động gửi lại nếu hệ thống yêu cầu retry: True
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu (lần {attempt + 1})...{white}")
                    time.sleep(retry_wait)
                    attempt += 1
                    continue
                    
                return res_data
            except requests.exceptions.Timeout:
                return {
                    "is_timeout": True, 
                    "message": f"Server phản hồi chậm nhưng đã gửi duyệt {len(payload['task_id'])} job thành công"
                }
            except Exception as e:
                return {"error": str(e)}
                
        return {"error": "Đã thử lại nhiều lần nhưng không thành công"}

# ================= CẤU HÌNH HEADERS & USER-AGENT =================
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(proxy_str):
    if not proxy_str:
        return None
    proxy_str = proxy_str.strip()
    if not proxy_str:
        return None
        
    scheme = "http"
    if "://" in proxy_str:
        scheme, proxy_str = proxy_str.split("://", 1)
        
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        formatted = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    elif "@" in proxy_str:
        formatted = f"{scheme}://{proxy_str}"
    elif len(parts) == 2:
        formatted = f"{scheme}://{proxy_str}"
    else:
        formatted = f"{scheme}://{proxy_str}"
        
    return {"http": formatted, "https": formatted}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie,
        'origin': 'https://www.instagram.com',
        'priority': 'u=1, i',
        'referer': referer,
        'sec-ch-ua': sec_ch_ua_120,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': useragent,
        'x-asbd-id': '129477',
        'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-requested-with': 'XMLHttpRequest'
    }

def loadtime(time_delay):
    try:
        delay_int = int(time_delay)
    except:
        delay_int = 10
        
    if delay_int <= 0:
        return
        
    for x in range(delay_int, 0, -1):
        for color_code, dash_color in [
            ("\033[1;32m", "\033[1;33m"),
            ("\033[1;36m", "\033[1;34m"),
            ("\033[1;34m", "\033[1;31m"),
            ("\033[1;33m", "\033[1;32m"),
            ("\033[1;31m", "\033[1;36m")
        ]:
            sys.stdout.write(f"\r                                                      \r")
            sys.stdout.write(f"{color_code}🇻🇳 Huy Vũ \033[1;37m- \033[1;32mDelay Tránh Block: \033[1;37m{x} {dash_color}Giây")
            sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write(f"\r                                                      \r")
    sys.stdout.flush()

# ============ CÁC HÀM TƯƠNG TÁC INSTAGRAM ============
def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.instagram.com/accounts/edit/',
        'cookie': cookie,
        'user-agent': useragent,
        'sec-ch-ua': sec_ch_ua_120
    }
    proxies = format_proxy(proxy)
    try:
        return c_requests.get(url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=30).text
    except:
        return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id:
        return '{"status": "error", "message": "Lỗi Target ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "target_user_id": str(target_id),
        "container_module": "profile",
        "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisFollowMutation",
        "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)
    }
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid:
        return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    tracking_token = ""
    try:
        if link_job:
            res_get = session.get(link_job, impersonate="chrome120", timeout=10).text
            tt_match = re.search(r'"tracking_token":"([^"]+)"', res_get)
            if tt_match:
                tracking_token = tt_match.group(1)
    except:
        pass
    variables = {
        "input": {
            "actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
            "container_module": "single_post", "media_id": str(mediaid)
        }
    }
    if tracking_token:
        variables["input"]["tracking_token"] = tracking_token
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid:
        return '{"status": "error", "message": "Lỗi Media ID"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies:
        session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except:
                pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        res_home = session.get(link_job if link_job else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match:
            lsd = lsd_match.group(1)
        dtsg_match = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home)
        if not dtsg_match:
            dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match:
            jazoest = jazoest_match.group(1)
    except:
        pass
    dynamic_csrftoken = session.cookies.get('csrftoken')
    if not dynamic_csrftoken:
        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        dynamic_csrftoken = csf_match.group(1) if csf_match else "missing"
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "connections": [f"client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:\"{mediaid}\",sort_order:\"popular\")"],
        "data": {"comment_text": text, "media_id": str(mediaid)}
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
        "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)
    }
    try:
        res_gql = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15)
        return res_gql.text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    """Hàm gửi nhận thưởng và in kết quả chi tiết kèm cookie_check"""
    global xu # Gọi biến tổng xu ở ngoài vào để cộng dồn
    
    if not task_list:
        return
    sys.stdout.write("\r                                                      \r")
    print(f"{yellow} ⏩ Gom đủ {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    if isinstance(ck, dict):
        if 'message' in ck:
            try:
                pts = int(ck.get('points', 0))
            except:
                pts = 0
                
            xu += pts 
            
            succ = ck.get('success_count', len(task_list))
            print(f"[{now}] {green} ⏩ {ck['message']} (+{pts} xu | Hoàn thành: {succ} task | Tổng: {xu} xu){white}")
            
        elif ck.get("is_timeout"):
            print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck:
            print(f"[{now}] {red} ⏩ LỖI XSMM: {ck['error']}{white}")
        
        if ck.get('countdown', 0) > 0:
            print(f"{yellow} ⏩ Hệ thống yêu cầu nghỉ {ck['countdown']}s...{white}")
            time.sleep(ck['countdown'])

# ================= MAIN RUN =================
banner()

xsmm_token = ""
xu = 0
username = "Unknown"

if os.path.exists("logXSMM.txt"):
    while True:
        print(f"{white} Nhập{cam} Enter{white} để dùng token XSMM đã lưu! {xuong} Nhập{red} No{white} để nhập lại Token : ", end="")
        nhap = input().strip().lower()
        if nhap in ['', 'no']:
            break
        print(f"{red}Sai Định Dạng\n")
        
    if nhap == 'no':
        xsmm_token = input(f"{white} ⏩ {green}Access Token XSMM: ").strip()
        with open("logXSMM.txt", "w") as f:
            json.dump({"token": xsmm_token}, f)
    else:
        with open("logXSMM.txt", "r") as f:
            acc = json.load(f)
            xsmm_token = acc.get("token", "")
else:
    xsmm_token = input(f"{white} ⏩ {green}Access Token XSMM: ").strip()
    with open("logXSMM.txt", "w") as f:
        json.dump({"token": xsmm_token}, f)

xsmm = XSMMTool(token=xsmm_token)
user_info = xsmm.get_user_info()

if isinstance(user_info, dict) and "user" in user_info:
    xu = user_info["user"].get("points", 0)
    username = user_info["user"].get("username", "Unknown")
    print(f"\n{white} ✅ {green}Đăng nhập XSMM thành công: {yellow}{username}{white}\n")
else:
    print(f"\n{red} ❌ Token sai hoặc đã hết hạn\n")
    if os.path.exists("logXSMM.txt"):
        os.remove("logXSMM.txt")
    sys.exit()

nhaplaicc = False
mangcookie = []

if os.path.exists("ListccXSMM.json"):
    while True:
        print(f"{white} Nhập{cam} Enter{white} để dùng list cookies đã lưu! {xuong} Nhập{red} 1{white} để nhập lại list cookie : ", end="")
        nhapcc = input().strip()
        if nhapcc in ['', '1']:
            break
        print(f"{red}Sai lựa chọn\n")
        
    if nhapcc == '':
        try:
            with open("ListccXSMM.json", "r", encoding="utf-8") as f:
                listccdaluu = json.load(f)
            for acc_item in listccdaluu:
                cc = acc_item.get("cookie", "")
                px = acc_item.get("proxy", "")
                if not cc:
                    continue
                access = check_cookie_ig(cc, px)
                try:
                    configdata = json.loads(access)
                    if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                        mangcookie.append({"cookie": cc, "proxy": px})
                except:
                    pass
            luong = len(mangcookie)
        except:
            nhaplaicc = True
    else:
        nhaplaicc = True
elif os.path.exists("ListccXSMM.txt"):
    try:
        with open("ListccXSMM.txt", "r") as f:
            listccdaluu = f.read().splitlines()
        for cc in listccdaluu:
            if not cc:
                continue
            access = check_cookie_ig(cc)
            try:
                configdata = json.loads(access)
                if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                    mangcookie.append({"cookie": cc, "proxy": ""})
            except:
                pass
        luong = len(mangcookie)
        with open("ListccXSMM.json", "w", encoding="utf-8") as f:
            json.dump(mangcookie, f)
        os.remove("ListccXSMM.txt")
    except:
        nhaplaicc = True
else:
    nhaplaicc = True

if nhaplaicc:
    if os.path.exists("ListccXSMM.json"):
        os.remove("ListccXSMM.json")
    if os.path.exists("ListccXSMM.txt"):
        os.remove("ListccXSMM.txt")
        
    while True:
        print(f"{white} ✏ {blue}Nhập số nick INSTA muốn chạy: ", end="")
        try:
            luong = int(input().strip())
            if 1 <= luong <= 2000:
                break
            print(f"{red}Ít nhất là 1 và nhiều nhất là 2000!\n")
        except:
            print(f"{red}Nhập số hợp lệ!")

    thu = 1
    c = 1
    while c <= luong:
        print(f"{white} + {green}Nhập Cookie Thứ {thu}:{white} ", end="")
        cookie_str = input().strip()
        print(f"{white}   {cyan}Nhập Proxy cho Nick {thu} {pink}(Enter để bỏ qua){white}: ", end="")
        proxy_str = input().strip()
        
        access = check_cookie_ig(cookie_str, proxy_str)
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
                with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                    json.dump(mangcookie, f)
                c += 1
                thu += 1
            else:
                print(f"{white} ⛔ {red}Cookie hoặc Proxy lỗi, thử lại đi \n")
        except:
            print(f"{white} ⛔ {red}Cookie hoặc Proxy lỗi, thử lại đi \n")

dl = 0
doi = 99999
if len(mangcookie) == 1:
    print(f"{white} ⏩ {blue}Hết nhiệm vụ hoặc lỗi thì dừng bao lâu? : {white}", end="")
    try:
        dl = int(input().strip())
    except:
        dl = 0
else:
    while True:
        dl = 0
        print(f"{white} ⏩ {blue}Sau bao nhiêu nhiệm vụ thì đổi nick : {white}", end="")
        try:
            doi = int(input().strip())
            if doi >= 1:
                break
            print(f"{red}Lựa chọn không hợp lệ !\n")
        except:
            print(f"{red}Nhập số hợp lệ!")

listnv = []
timedelaytym = 10
timedelaysub = 15
timedelaycmt = 20

while True:
    print(f"{yellow} ⏩ {blue}Chế độ Tym trên XSMM{pink} (on/off): {white}", end="")
    chon_tym = input().strip().lower()
    if chon_tym == 'on':
        listnv.append('instagram_like')
        while True:
            print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Tym (Nhập 0 để bỏ qua): {white}", end="")
            try:
                timedelaytym = int(input().strip())
                if timedelaytym >= 0:
                    break
                print(f"{red}Không được nhập số âm!\n")
            except:
                pass

    print(f"{yellow} ⏩ {blue}Chế độ Follow trên XSMM{pink} (on/off): {white}", end="")
    chon_sub = input().strip().lower()
    if chon_sub == 'on':
        listnv.append('instagram_follow')
        while True:
            print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Follow (Nhập 0 để bỏ qua): {white}", end="")
            try:
                timedelaysub = int(input().strip())
                if timedelaysub >= 0:
                    break
                print(f"{red}Không được nhập số âm!\n")
            except:
                pass

    print(f"{yellow} ⏩ {blue}Chế độ Comment trên XSMM{pink} (on/off): {white}", end="")
    chon_cmt = input().strip().lower()
    if chon_cmt == 'on':
        listnv.append('instagram_comment')
        while True:
            print(f"{yellow} ⏩ {blue}Delay Nhiệm Vụ Cmt (Nhập 0 để bỏ qua): {white}", end="")
            try:
                timedelaycmt = int(input().strip())
                if timedelaycmt >= 0:
                    break
                print(f"{red}Không được nhập số âm!\n")
            except:
                pass

    if len(listnv) == 0:
        print(f"{red}Chọn tối thiểu 1 loại Job !\n")
    else:
        break

banner()
print(f"{cyan} ✅ {cam}XSMM User    : {white}{username}")
print(f"{cyan} ✅ {cam}Số Nick Chạy : {white}{len(mangcookie)}")
print(f"{cyan} ✅ {cam}Số Dư Ban Đầu: {green}{xu} xu")
print(f"{yellow} ────────────────────────────────────────────────────────{reset}\n")

while True:
    for l in range(len(mangcookie)-1, -1, -1):
        acc_data = mangcookie[l]
        cookie = acc_data["cookie"]
        proxy = acc_data.get("proxy", "")
        
        # 1. KIỂM TRA ĐỘ SỐNG CỦA COOKIE INSTAGRAM
        access = check_cookie_ig(cookie, proxy)
        is_live = False
        tenfb = ""
        idfb = ""
        
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                is_live = True
                tenfb = configdata['form_data']['username']
                
                # Trích xuất UID từ Cookie
                idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
                idfb = idfb_match.group(1) if idfb_match else str(configdata['form_data'].get('id', ''))
        except Exception:
            is_live = False

        if not is_live or not idfb:
            print(f"{white} ⛔ {red}Cookie Die hoặc Proxy lỗi - ĐANG ĐỔI NICK\n")
            mangcookie.pop(l)
            with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                json.dump(mangcookie, f)
            continue

        px_display = f" | Proxy: {proxy}" if proxy else " | Không Proxy"
        print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] ● {white}")

        # 2. ĐỒNG BỘ NICK LÊN XSMM (AN TOÀN)
        try:
            acc_list = xsmm.get_accounts(account_type="instagram", search=idfb)
            exists = False
            
            if isinstance(acc_list, dict) and acc_list.get("accounts"):
                for acc in acc_list["accounts"]:
                    if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                        exists = True
                        break
                        
            if not exists:
                link_ig = f"https://www.instagram.com/{tenfb}"
                add_res = xsmm.add_account("instagram", link_ig)
                if isinstance(add_res, dict) and "id" in add_res:
                    print(f"{green} ➕ Đã thêm tài khoản [{tenfb}] vào XSMM thành công!{white}")
        except Exception as e:
            print(f"{yellow} ⚠️ Không thể đồng bộ tài khoản: {e}{white}")

        # 3. BẮT ĐẦU NHẬN TASK
        print(f"{white} Bắt đầu nhận việc cho UID: {cam}{idfb} ({tenfb})")
        max_job = 0
        rand_job = random.choice(listnv)
        
        # ================= XỬ LÝ NHIỆM VỤ TYM =================
        if rand_job == 'instagram_like':
            list_nv = xsmm.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                print(f"{white} ❌ {yellow}Hết nhiệm vụ Tym hoặc chưa tới lượt!")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list):
                soloitym = 0
                for nv in list_nv:
                    task_id = nv.get('id')
                    idm = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""
                    
                    print(f"{yellow} ⏩ {blue}Job Tym: {white}{link_job} | MediaID: {idm}")
                    chayfl = tym(idm, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    
                    try:
                        g = json.loads(chayfl)
                        if 'data' not in g and g.get('status') != 'ok':
                            raise Exception(g.get('message', 'Bị IG chặn thao tác'))
                            
                        print(f"{green} ● TYM THÀNH CÔNG -> Đang gửi nhận xu... ● {white}")
                        gui_nhan_xu("instagram_like", [task_id], idfb, cookie, xsmm)
                        soloitym = 0
                    except Exception as e:
                        print(f"{red} ● TYM LỖI: {str(e)} ● {white}")
                        soloitym += 1
                        
                    loadtime(int(timedelaytym))
                    
                    if soloitym > 4:
                        print(f"{blue} ⏩ Gặp lỗi quá nhiều -> Đổi Nick! ● {white}")
                        break
                            
                    if max_job >= doi:
                        max_job = 0
                        break

        # ================= XỬ LÝ NHIỆM VỤ FOLLOW =================
        elif rand_job == 'instagram_follow':
            list_nv = xsmm.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                print(f"{white} ❌ {yellow}Hết nhiệm vụ Follow hoặc chưa tới lượt!")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list):
                soloisub = 0
                cache_batch_nv = []
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies:
                    temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                
                for nv in list_nv:
                    task_id = nv.get('id')
                    target_id = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    
                    if not target_id or not str(target_id).isdigit():
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'"profile_id":"(\d+)"', res_html)
                            if not m:
                                m = re.search(r'"user_id":"(\d+)"', res_html)
                            if not m:
                                m = re.search(r'profilePage_(\d+)', res_html)
                            if m:
                                target_id = m.group(1)
                        except:
                            pass

                    print(f"{yellow} ⏩ {blue}Follow Target ID: {white}{target_id} ({link_job})")

                    if not target_id or not str(target_id).isdigit():
                        print(f"{red} ❌ Không trích xuất được ID số, bỏ qua!")
                        continue

                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""

                    chay_sub = follow(target_id, cookie, csf, link_job, proxy=proxy)
                    max_job += 1

                    try:
                        g = json.loads(chay_sub)
                        if 'data' not in g and g.get('status') != 'ok' and g.get('status') != 'success':
                            print(f"{red} ❌ Follow ID {target_id} thất bại: {g.get('message', 'Block')}")
                            soloisub += 1
                        else:
                            print(f"{green} ✅ Follow ID {target_id} thành công!{white}")
                            cache_batch_nv.append(task_id)
                            soloisub = 0
                            
                            # Gom đủ 10 nhiệm vụ: Gửi nhận xu và break ngay để refresh lấy nhóm task mới
                            if len(cache_batch_nv) >= 10:
                                gui_nhan_xu("instagram_follow", cache_batch_nv, idfb, cookie, xsmm)
                                cache_batch_nv = []
                                print(f"{cyan} 🔄 Đã hoàn tất đợt 10 task -> Refresh lấy danh sách task mới...{white}")
                                break
                    except Exception as e:
                        print(f"{red} ❌ Follow ID {target_id} lỗi JSON: {e}")
                        soloisub += 1

                    # Delay chạy trực tiếp ngay sau mỗi lần follow
                    loadtime(int(timedelaysub))

                    if soloisub > 4:
                        print(f"{blue} ⏩ Lỗi liên tiếp -> Đổi Nick! ● {white}")
                        break
                            
                    if max_job >= doi:
                        max_job = 0
                        break

                # Gửi nhận số task còn dư lại (nếu danh sách ban đầu ít hơn 10 task)
                if len(cache_batch_nv) > 0:
                    gui_nhan_xu("instagram_follow", cache_batch_nv, idfb, cookie, xsmm)
                    cache_batch_nv = []

        # ================= XỬ LÝ NHIỆM VỤ COMMENT =================
        elif rand_job == 'instagram_comment':
            list_nv = xsmm.get_tasks(rand_job, uid=idfb)
            if isinstance(list_nv, dict) and "error" in list_nv:
                print(f"{white} ❌ {red}Lỗi từ XSMM: {list_nv['error']}")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list) and len(list_nv) == 0:
                print(f"{white} ❌ {yellow}Hết nhiệm vụ Comment hoặc chưa tới lượt!")
                if len(mangcookie) == 1:
                    for j in range(dl, 0, -1):
                        sys.stdout.write(f"\r{green}Đang Chờ Delay Tránh Block {yellow}{j} Giây\r")
                        sys.stdout.flush()
                        time.sleep(1)
            elif isinstance(list_nv, list):
                soloicmt = 0
                temp_sess = c_requests.Session()
                proxies = format_proxy(proxy)
                if proxies:
                    temp_sess.proxies = proxies
                temp_sess.headers.update({"User-Agent": useragent})
                
                for nv in list_nv:
                    task_id = nv.get('id')
                    idm = nv.get('target_id', '')
                    noidung = nv.get('comment', '❤️❤️❤️')
                    link_job = nv.get('target_url', '')
                        
                    if not idm:
                        try:
                            res_html = temp_sess.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'instagram://media\?id=(\d+)', res_html)
                            if not m:
                                m = re.search(r'"media_id":"(\d+)"', res_html)
                            if not m:
                                m = re.search(r'media\?id=(\d+)', res_html)
                            if m:
                                idm = m.group(1)
                        except:
                            pass

                    print(f"{yellow} ⏩ {blue}Job CMT: {white}{link_job} | ND: {noidung}")
                    
                    if not idm:
                        print(f"{red} ● CMT LỖI: Không tìm thấy Media ID ● {white}")
                        soloicmt += 1
                        continue

                    csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_match.group(1) if csf_match else ""

                    chay_cmt = cmt(idm, noidung, cookie, csf, link_job, proxy=proxy)
                    max_job += 1
                    
                    try:
                        g = json.loads(chay_cmt)
                        if g.get('status') != 'ok' and 'data' not in g:
                            raise Exception(g.get('message', 'Bị IG chặn cmt'))
                            
                        print(f"{green} ● COMMENT THÀNH CÔNG -> Đang gửi nhận xu... ● {white}")
                        gui_nhan_xu("instagram_comment", [task_id], idfb, cookie, xsmm)
                        soloicmt = 0
                    except Exception as e:
                        print(f"{red} ● CMT LỖI: {str(e)} ● {white}")
                        soloicmt += 1
                        
                    loadtime(int(timedelaycmt))
                    
                    if soloicmt > 4:
                        print(f"{blue} ⏩ Lỗi liên tiếp -> Đổi Nick! ● {white}")
                        break
                            
                    if max_job >= doi:
                        max_job = 0
                        break

    if len(mangcookie) == 1 and dl == 0:
        print(f"{pink} ⏩ {blue}Dừng Thời Gian: ", end="")
        try:
            dl = int(input().strip())
        except:
            dl = 0

    if len(mangcookie) == 0:
        if os.path.exists("ListccXSMM.json"):
            os.remove("ListccXSMM.json")
        print(f"\n{pink} ⛔ {red}Tất Cả Cookie Đều Die Hoặc Proxy Lỗi\n")
        break
