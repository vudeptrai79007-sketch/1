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
 ╚═╝  ╚═╝ ╚═════╝    ╚═╝         ╚═══╝   ╚═════╝{reset}
{yellow} ┌────────────────────────────────────────────────────────┐
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API ENGINE V2    {yellow}│
{yellow} │ {pink}📌 Bản quyền: {white}TA Tool (Optimized by HUY VŨ)           {yellow}│
{yellow} │ {cyan}⚡ Hiệu năng: {white}Tối ưu Socket & Xử lý Delay 0s           {yellow}│
{yellow} └────────────────────────────────────────────────────────┘{reset}
""")

# ================= CLASS API XSMM V2 =================
class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = self.session.get(url, timeout=20)
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
            response = self.session.get(url, params=params, timeout=20)
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
            response = self.session.post(url, json=payload, timeout=20)
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
            response = self.session.get(url, params=params, timeout=20)
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
                response = self.session.post(url, json=payload, timeout=35)
                res_data = response.json()
                
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    print(f"\n{yellow} ⏩ [Retry=True] Chờ {retry_wait}s trước khi gửi lại yêu cầu duyệt xu...{white}")
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

# ================= CẤU HÌNH HEADERS & PROXY =================
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(proxy_str):
    if not proxy_str or not str(proxy_str).strip():
        return None
    proxy_str = str(proxy_str).strip()
        
    scheme = "http"
    if "://" in proxy_str:
        scheme, proxy_str = proxy_str.split("://", 1)
        
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        formatted = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    else:
        formatted = f"{scheme}://{proxy_str}"
        
    return {"http": formatted, "https": formatted}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.6,en;q=0.5',
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
        delay_int = 0
    if delay_int <= 0:
        return

    colors = [
        ("\033[1;32m", "\033[1;33m"),
        ("\033[1;36m", "\033[1;34m"),
        ("\033[1;34m", "\033[1;31m"),
        ("\033[1;33m", "\033[1;32m"),
        ("\033[1;31m", "\033[1;36m")
    ]
    for x in range(delay_int, 0, -1):
        color_code, dash_color = colors[x % len(colors)]
        sys.stdout.write(f"\r{color_code}🇻🇳 HUY VŨ Tool \033[1;37m- \033[1;32mDelay: \033[1;37m{x} {dash_color}Giây  \r")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()

# ============ HÀM TƯƠNG TÁC INSTAGRAM ============
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
        res = c_requests.get(url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=20)
        return res.text
    except:
        return "{}"

def follow(session, target_id, cookie, csrftoken, profile_url=""):
    if not target_id:
        return '{"status": "error", "message": "Lỗi Target ID"}'
        
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_m:
            lsd = lsd_m.group(1)
        dtsg_m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_m:
            fb_dtsg = dtsg_m.group(1)
        jazoest_m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_m:
            jazoest = jazoest_m.group(1)
    except:
        pass

    session.headers.update(get_ig_headers(cookie, csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
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

def tym(session, mediaid, cookie, csrftoken, link_job=""):
    if not mediaid:
        return '{"status": "error", "message": "Lỗi Media ID"}'
        
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        lsd_m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_m:
            lsd = lsd_m.group(1)
        dtsg_m = re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_m:
            fb_dtsg = dtsg_m.group(1)
        jazoest_m = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_m:
            jazoest = jazoest_m.group(1)
    except:
        pass

    session.headers.update(get_ig_headers(cookie, csrftoken, link_job if link_job else "https://www.instagram.com/"))
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

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    if not task_list:
        return 0
    sys.stdout.write("\r" + " " * 50 + "\r")
    print(f"{yellow} ⏩ Gom {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    pts_earned = 0
    if isinstance(ck, dict):
        if 'message' in ck:
            pts_earned = ck.get('points', 0)
            succ = ck.get('success_count', len(task_list))
            print(f"[{now}] {green} ⏩ {ck['message']} (+{pts_earned} xu | Thành công: {succ} task){white}")
        elif ck.get("is_timeout"):
            print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck:
            print(f"[{now}] {red} ⏩ LỖI XSMM: {ck['error']}{white}")
        
        if ck.get('countdown', 0) > 0:
            print(f"{yellow} ⏩ Hệ thống yêu cầu nghỉ {ck['countdown']}s...{white}")
            time.sleep(ck['countdown'])
            
    return pts_earned

# ================= RUN TIME =================
banner()

xsmm_token = ""
xu = 0
username = "Unknown"

if os.path.exists("logXSMM.txt"):
    while True:
        print(f"{white} Nhập{cam} Enter{white} để dùng token đã lưu | Nhập{red} No{white} để nhập mới: ", end="")
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
    xu = int(user_info["user"].get("points", 0))
    username = user_info["user"].get("username", "Unknown")
    print(f"\n{white} ✅ {green}Đăng nhập thành công: {yellow}{username}{white}\n")
else:
    print(f"\n{red} ❌ Token sai hoặc đã hết hạn\n")
    if os.path.exists("logXSMM.txt"):
        os.remove("logXSMM.txt")
    sys.exit()

mangcookie = []
if os.path.exists("ListccXSMM.json"):
    print(f"{white} Nhập{cam} Enter{white} để dùng cookie đã lưu | Nhập{red} 1{white} để nhập lại: ", end="")
    nhapcc = input().strip()
    if nhapcc == '':
        try:
            with open("ListccXSMM.json", "r", encoding="utf-8") as f:
                listccdaluu = json.load(f)
            for acc_item in listccdaluu:
                cc = acc_item.get("cookie", "")
                px = acc_item.get("proxy", "")
                if cc:
                    mangcookie.append({"cookie": cc, "proxy": px})
        except:
            mangcookie = []

if not mangcookie:
    while True:
        try:
            luong = int(input(f"{white} ✏ {blue}Nhập số nick INSTA muốn chạy: ").strip())
            if luong >= 1:
                break
        except:
            pass
        print(f"{red}Vui lòng nhập số nguyên dương!")

    for c in range(1, luong + 1):
        cookie_str = input(f"{white} + {green}Cookie Nick {c}:{white} ").strip()
        proxy_str = input(f"{white}   {cyan}Proxy Nick {c} (Enter để bỏ qua):{white} ").strip()
        mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
        
    with open("ListccXSMM.json", "w", encoding="utf-8") as f:
        json.dump(mangcookie, f, ensure_ascii=False, indent=2)

dl = 60
doi = 99999
if len(mangcookie) > 1:
    while True:
        try:
            doi = int(input(f"{white} ⏩ {blue}Sau bao nhiêu nhiệm vụ thì đổi nick: {white}").strip())
            if doi >= 1:
                break
        except:
            pass
        print(f"{red}Nhập số nguyên dương!")

listnv = []
timedelaytym = 0
timedelaysub = 0

while True:
    chon_tym = input(f"{yellow} ⏩ {blue}Chế độ Tym (1: Bật / 2: Tắt): {white}").strip()
    if chon_tym == '1':
        listnv.append('instagram_like')
        while True:
            try:
                timedelaytym = int(input(f"{yellow} ⏩ {blue}Delay Tym (nhập 0 để chạy max tốc): {white}").strip())
                if timedelaytym >= 0:
                    break
            except:
                pass

    chon_sub = input(f"{yellow} ⏩ {blue}Chế độ Follow (1: Bật / 2: Tắt): {white}").strip()
    if chon_sub == '1':
        listnv.append('instagram_follow')
        while True:
            try:
                timedelaysub = int(input(f"{yellow} ⏩ {blue}Delay Follow (nhập 0 để chạy max tốc): {white}").strip())
                if timedelaysub >= 0:
                    break
            except:
                pass

    if listnv:
        break
    print(f"{red}Bạn phải bật ít nhất 1 loại Job!\n")

banner()
print(f"{cyan} ✅ {cam}XSMM User    : {white}{username}")
print(f"{cyan} ✅ {cam}Số Nick Chạy : {white}{len(mangcookie)}")
print(f"{cyan} ✅ {cam}Số Dư Ban Đầu: {green}{xu} xu")
print(f"{yellow} ────────────────────────────────────────────────────────{reset}\n")

# ================= VÒNG LẶP ENGINE CHÍNH =================
while True:
    if not mangcookie:
        print(f"\n{pink} ⛔ {red}Tất Cả Cookie Đều Die Hoặc Proxy Lỗi\n")
        tiep_tuc = input(f"{white} 🔄 Bơm thêm Nick để chạy tiếp? {pink}(1: Có / Phím khác: Thoát): {white}").strip()
        if tiep_tuc == '1':
            while True:
                try:
                    luong = int(input(f"{white} ✏ {blue}Nhập số nick muốn thêm: ").strip())
                    if luong >= 1:
                        break
                except:
                    pass
            for thu in range(1, luong + 1):
                cookie_str = input(f"{white} + {green}Cookie Thứ {thu}:{white} ").strip()
                proxy_str = input(f"{white}   {cyan}Proxy Thứ {thu} (Enter để bỏ qua):{white} ").strip()
                mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
                
            with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                json.dump(mangcookie, f, ensure_ascii=False, indent=2)
            continue
        else:
            if os.path.exists("ListccXSMM.json"):
                os.remove("ListccXSMM.json")
            break

    for l in range(len(mangcookie) - 1, -1, -1):
        acc_data = mangcookie[l]
        cookie = acc_data["cookie"]
        proxy = acc_data.get("proxy", "")
        
        # 1. Check Live IG
        access = check_cookie_ig(cookie, proxy)
        is_live = False
        tenfb, idfb = "", ""
        
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                is_live = True
                tenfb = configdata['form_data']['username']
                idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
                idfb = idfb_match.group(1) if idfb_match else str(configdata['form_data'].get('id', ''))
        except:
            is_live = False

        if not is_live or not idfb:
            print(f"{white} ⛔ {red}Cookie Die hoặc Proxy lỗi -> Đã xóa khỏi hàng chờ!\n")
            mangcookie.pop(l)
            with open("ListccXSMM.json", "w", encoding="utf-8") as f:
                json.dump(mangcookie, f, ensure_ascii=False, indent=2)
            continue

        px_display = f" | Proxy: {proxy}" if proxy else " | No Proxy"
        print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] ● {white}")

        # 2. Đồng bộ Nick lên XSMM
        try:
            acc_list = xsmm.get_accounts(account_type="instagram", search=idfb)
            exists = False
            if isinstance(acc_list, dict) and acc_list.get("accounts"):
                for acc in acc_list["accounts"]:
                    if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                        exists = True
                        break
            if not exists:
                xsmm.add_account("instagram", f"https://www.instagram.com/{tenfb}")
        except:
            pass

        # 3. Khởi tạo Persistent Session cho Nick này
        cur_session = c_requests.Session()
        proxies = format_proxy(proxy)
        if proxies:
            cur_session.proxies = proxies
        
        # Set cookies vào Session
        for item in unquote(cookie).split(';'):
            if '=' in item:
                try:
                    k, v = item.strip().split('=', 1)
                    cur_session.cookies.set(k, v, domain='.instagram.com')
                except:
                    pass

        csf_match = re.search(r'csrftoken=([^;]+)', cookie)
        csf = csf_match.group(1) if csf_match else "missing"

        # 4. Chạy việc
        jobs_done = 0
        error_count = 0
        
        while jobs_done < doi and error_count <= 4:
            rand_job = random.choice(listnv)
            list_tasks = xsmm.get_tasks(rand_job, uid=idfb)
            
            if not isinstance(list_tasks, list) or len(list_tasks) == 0:
                print(f"{yellow} ⚠️ Hết nhiệm vụ {rand_job}, nghỉ {dl}s...{white}")
                loadtime(dl)
                break

            # ===== NHIỆM VỤ TYM =====
            if rand_job == 'instagram_like':
                for nv in list_tasks:
                    task_id = nv.get('id')
                    idm = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    
                    print(f"{yellow} ⏩ {blue}Job Tym: {white}{link_job} | MediaID: {idm}")
                    res = tym(cur_session, idm, cookie, csf, link_job)
                    jobs_done += 1
                    
                    try:
                        g = json.loads(res)
                        if 'data' not in g and g.get('status') != 'ok':
                            raise Exception(g.get('message', 'Blocked by IG'))
                            
                        print(f"{green} ● TYM THÀNH CÔNG -> Gửi duyệt... ● {white}")
                        pts = gui_nhan_xu("instagram_like", [task_id], idfb, cookie, xsmm)
                        xu += pts
                        print(f"{green} 💰 TỔNG XU: {yellow}{xu}{white}")
                        error_count = 0
                    except Exception as e:
                        print(f"{red} ● TYM LỖI: {e} ● {white}")
                        error_count += 1
                        
                    loadtime(timedelaytym)
                    if error_count > 4 or jobs_done >= doi:
                        break

            # ===== NHIỆM VỤ FOLLOW =====
            elif rand_job == 'instagram_follow':
                batch_follow = []
                for nv in list_tasks:
                    task_id = nv.get('id')
                    target_id = nv.get('target_id', '')
                    link_job = nv.get('target_url', '')
                    
                    if not target_id or not str(target_id).isdigit():
                        try:
                            res_html = cur_session.get(link_job, impersonate="chrome120", timeout=10).text
                            m = re.search(r'"profile_id":"(\d+)"', res_html) or re.search(r'"user_id":"(\d+)"', res_html) or re.search(r'profilePage_(\d+)', res_html)
                            if m:
                                target_id = m.group(1)
                        except:
                            pass

                    if not target_id or not str(target_id).isdigit():
                        continue

                    print(f"{yellow} ⏩ {blue}Follow UID: {white}{target_id} ({link_job})")
                    res = follow(cur_session, target_id, cookie, csf, link_job)
                    jobs_done += 1
                    
                    try:
                        g = json.loads(res)
                        if 'data' not in g and g.get('status') != 'ok' and g.get('status') != 'success':
                            print(f"{red} ❌ Follow thất bại: {g.get('message', 'Blocked')}")
                            error_count += 1
                        else:
                            print(f"{green} ✅ Follow thành công!{white}")
                            batch_follow.append(task_id)
                            error_count = 0
                            
                            if len(batch_follow) >= 10:
                                pts = gui_nhan_xu("instagram_follow", batch_follow, idfb, cookie, xsmm)
                                xu += pts
                                print(f"{green} 💰 TỔNG XU: {yellow}{xu}{white}")
                                batch_follow = []
                    except Exception as e:
                        print(f"{red} ❌ Follow lỗi parse: {e}")
                        error_count += 1
                        
                    loadtime(timedelaysub)
                    if error_count > 4 or jobs_done >= doi:
                        break
                
                # Duyệt nốt số task follow còn sót lại
                if batch_follow:
                    pts = gui_nhan_xu("instagram_follow", batch_follow, idfb, cookie, xsmm)
                    xu += pts
                    print(f"{green} 💰 TỔNG XU: {yellow}{xu}{white}")
                    batch_follow = []

            if error_count > 4:
                print(f"{blue} ⏩ Dính hạn chế liên tục -> Chuyển sang nick tiếp theo!{white}\n")
                break
            if jobs_done >= doi:
                print(f"{cyan} 🔄 Đạt chỉ tiêu {doi} nhiệm vụ -> Đổi Nick!{white}\n")
                break
