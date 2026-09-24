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
import threading
from concurrent.futures import ThreadPoolExecutor

# ================= BẢNG MÀU ANSI =================
xuong = "\n"
red = "\033[1;31m"
pink = "\033[1;35m"
green = "\033[1;32m"
yellow = "\033[1;33m"
white = "\033[0;37m"
cyan = "\033[1;36m"
blue = "\033[1;34m"
cam = "\033[38;5;208m"
reset = "\033[0m"

# Khóa đa luồng để tránh đè text và sai số xu
print_lock = threading.Lock()

def s_print(*args, **kwargs):
    """Hàm in ra màn hình an toàn cho đa luồng"""
    with print_lock:
        print(*args, **kwargs)

# ================= BANNER HUY VŨ =================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    s_print(f"""{cyan}
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
                
                if isinstance(res_data, dict) and res_data.get("retry") is True:
                    retry_wait = random.randint(10, 15)
                    s_print(f"\n{yellow} ⏩ [Retry=True] Đợi {retry_wait}s trước khi gửi lại yêu cầu duyệt xu...{white}")
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

# ================= CẤU HÌNH HEADERS =================
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(proxy_str):
    if not proxy_str: return None
    proxy_str = proxy_str.strip()
    if not proxy_str: return None
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
        'accept-language': 'vi-VN,vi;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie,
        'origin': 'https://www.instagram.com',
        'referer': referer,
        'sec-ch-ua': sec_ch_ua_120,
        'user-agent': useragent,
        'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest'
    }

# ============ CÁC HÀM TƯƠNG TÁC INSTAGRAM ============
def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {
        'x-ig-app-id': '936619743392459',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.instagram.com/accounts/edit/',
        'cookie': cookie,
        'user-agent': useragent
    }
    proxies = format_proxy(proxy)
    try:
        return c_requests.get(url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=30, allow_redirects=False).text
    except:
        return "{}"

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id: return '{"status": "error"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=10, allow_redirects=False).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', res_home)
        if jazoest_match: jazoest = jazoest_match.group(1)
    except: pass
    
    session.headers.update(get_ig_headers(cookie, csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {"target_user_id": str(target_id), "container_module": "profile"}
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
        "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, 
        "fb_api_req_friendly_name": "usePolarisFollowMutation",
        "doc_id": "26508036048874888", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15, allow_redirects=False).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10, allow_redirects=False).text
        lsd_match = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home)
        if lsd_match: lsd = lsd_match.group(1)
        dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)
        if dtsg_match: fb_dtsg = dtsg_match.group(1)
    except: pass
    
    session.headers.update(get_ig_headers(cookie, csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id_match = re.search(r'ds_user_id=(\d+)', cookie)
    actor_id = actor_id_match.group(1) if actor_id_match else "0"
    variables = {
        "input": {
            "actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)),
            "container_module": "single_post", "media_id": str(mediaid)
        }
    }
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd, 
        "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15, allow_redirects=False).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    global xu
    if not task_list: return
    s_print(f"{yellow} ⏩ UID {uid} gom đủ {len(task_list)} task -> Đang duyệt xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = int(ck.get('points', 0)) if str(ck.get('points')).isdigit() else 0
            with print_lock:
                xu += pts
            succ = ck.get('success_count', len(task_list))
            s_print(f"[{now}] {green} ⏩ {ck['message']} (+{pts} xu | Hoàn thành: {succ} task | Tổng: {xu} xu){white}")
        elif ck.get("is_timeout"):
            s_print(f"[{now}] {cam} ⏩ {ck['message']}{white}")
        elif 'error' in ck:
            s_print(f"[{now}] {red} ⏩ LỖI XSMM: {ck['error']}{white}")
        
        if ck.get('countdown', 0) > 0:
            s_print(f"{yellow} ⏩ UID {uid} Hệ thống yêu cầu nghỉ {ck['countdown']}s...{white}")
            time.sleep(ck['countdown'])

# ================= HÀM CHẠY 1 NICK (WORKER) =================
def run_account_worker(acc_data, xsmm, listnv, dl, doi, timedelays):
    cookie = acc_data["cookie"]
    proxy = acc_data.get("proxy", "")
    
    while True:
        access = check_cookie_ig(cookie, proxy)
        is_live, tenfb, idfb = False, "", ""
        
        try:
            configdata = json.loads(access)
            if configdata and 'form_data' in configdata and configdata['form_data'].get('username'):
                is_live = True
                tenfb = configdata['form_data']['username']
                idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
                idfb = idfb_match.group(1) if idfb_match else str(configdata['form_data'].get('id', ''))
        except Exception:
            pass

        if not is_live or not idfb:
            s_print(f"{white} ⛔ {red}Cookie UID: {idfb} Die hoặc Proxy lỗi - ĐANG DỪNG LUỒNG NÀY\n")
            break # Thoát luồng nếu cookie die

        px_display = f" | Proxy: {proxy}" if proxy else " | Không Proxy"
        s_print(f"{green} ● NICK LIVE [{tenfb} | UID: {idfb}{px_display}] ● {white}")

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
                    s_print(f"{green} ➕ Đã thêm tài khoản [{tenfb}] vào XSMM thành công!{white}")
        except Exception as e:
            s_print(f"{yellow} ⚠️ Lỗi đồng bộ tài khoản {tenfb}: {e}{white}")

        s_print(f"{white} Bắt đầu nhận việc cho UID: {cam}{idfb} ({tenfb})")
        max_job = 0
        rand_job = random.choice(listnv)
        
        list_nv = xsmm.get_tasks(rand_job, uid=idfb)
        
        if isinstance(list_nv, dict) and "error" in list_nv:
            s_print(f"{white} ❌ {red}Lỗi từ XSMM (UID {idfb}): {list_nv['error']}")
            if dl > 0: time.sleep(dl)
            continue
            
        elif isinstance(list_nv, list) and len(list_nv) == 0:
            s_print(f"{white} ❌ {yellow}Hết nhiệm vụ {rand_job} cho UID {idfb}!")
            if dl > 0: time.sleep(dl)
            continue
            
        elif isinstance(list_nv, list):
            cache_batch_nv = []
            soloi = 0
            
            for nv in list_nv:
                task_id = nv.get('id')
                link_job = nv.get('target_url', '')
                csf_match = re.search(r'csrftoken=([^;]+)', cookie)
                csf = csf_match.group(1) if csf_match else ""

                if rand_job == 'instagram_like':
                    idm = nv.get('target_id', '')
                    s_print(f"{yellow} ⏩ {blue}[{idfb}] Job Tym: {white}{link_job}")
                    kq = tym(idm, cookie, csf, link_job, proxy=proxy)
                    delay_job = timedelays['tym']
                    
                elif rand_job == 'instagram_follow':
                    target_id = nv.get('target_id', '')
                    s_print(f"{yellow} ⏩ {blue}[{idfb}] Follow: {white}{link_job}")
                    kq = follow(target_id, cookie, csf, link_job, proxy=proxy)
                    delay_job = timedelays['sub']

                max_job += 1
                try:
                    g = json.loads(kq)
                    if 'data' not in g and g.get('status') not in ['ok', 'success']:
                        s_print(f"{red} ❌ {idfb} Thất bại: {g.get('message', 'Block/Lỗi API')}")
                        soloi += 1
                    else:
                        s_print(f"{green} ✅ {idfb} Làm Job thành công!{white}")
                        cache_batch_nv.append(task_id)
                        soloi = 0
                        
                        if rand_job == 'instagram_follow' and len(cache_batch_nv) >= 10:
                            gui_nhan_xu(rand_job, cache_batch_nv, idfb, cookie, xsmm)
                            cache_batch_nv = []
                        elif rand_job == 'instagram_like':
                            gui_nhan_xu(rand_job, cache_batch_nv, idfb, cookie, xsmm)
                            cache_batch_nv = []
                            
                except Exception as e:
                    s_print(f"{red} ❌ Lỗi JSON {idfb}: {e}")
                    soloi += 1

                # Delay tĩnh ngầm
                if delay_job > 0:
                    time.sleep(delay_job)

                if soloi > 4:
                    s_print(f"{blue} ⏩ [{idfb}] Lỗi liên tiếp -> Chuyển vòng! ● {white}")
                    break
                        
                if max_job >= doi:
                    max_job = 0
                    break

            if len(cache_batch_nv) > 0:
                gui_nhan_xu(rand_job, cache_batch_nv, idfb, cookie, xsmm)

# ================= MAIN RUN =================
if __name__ == "__main__":
    banner()
    xsmm_token = ""
    xu = 0
    username = "Unknown"

    if os.path.exists("logXSMM.txt"):
        while True:
            print(f"{white} Nhập{cam} Enter{white} để dùng token XSMM đã lưu! {xuong} Nhập{red} No{white} để nhập lại Token : ", end="")
            nhap = input().strip().lower()
            if nhap in ['', 'no']: break
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
        if os.path.exists("logXSMM.txt"): os.remove("logXSMM.txt")
        sys.exit()

    mangcookie = []
    nhaplaicc = False

    if os.path.exists("ListccXSMM.json"):
        while True:
            print(f"{white} Nhập{cam} Enter{white} để dùng list cookies đã lưu! {xuong} Nhập{red} 1{white} để nhập lại : ", end="")
            nhapcc = input().strip()
            if nhapcc in ['', '1']: break
            
        if nhapcc == '':
            try:
                with open("ListccXSMM.json", "r", encoding="utf-8") as f:
                    listccdaluu = json.load(f)
                for acc_item in listccdaluu:
                    if acc_item.get("cookie"):
                        mangcookie.append(acc_item)
            except:
                nhaplaicc = True
        else:
            nhaplaicc = True
    else:
        nhaplaicc = True

    if nhaplaicc:
        if os.path.exists("ListccXSMM.json"): os.remove("ListccXSMM.json")
        while True:
            print(f"{white} ✏ {blue}Nhập số nick INSTA muốn chạy: ", end="")
            try:
                luong_nick = int(input().strip())
                if 1 <= luong_nick <= 2000: break
            except: pass

        for i in range(1, luong_nick + 1):
            print(f"{white} + {green}Nhập Cookie Thứ {i}:{white} ", end="")
            cookie_str = input().strip()
            print(f"{white}   {cyan}Nhập Proxy cho Nick {i} {pink}(Enter để bỏ qua){white}: ", end="")
            proxy_str = input().strip()
            mangcookie.append({"cookie": cookie_str, "proxy": proxy_str})
            
        with open("ListccXSMM.json", "w", encoding="utf-8") as f:
            json.dump(mangcookie, f)

    dl = 0
    doi = 99999
    print(f"{white} ⏩ {blue}Sau bao nhiêu nhiệm vụ thì chuyển vòng : {white}", end="")
    try:
        doi = int(input().strip())
        if doi <= 0: doi = 99999
    except:
        doi = 99999

    listnv = []
    timedelays = {'tym': 0, 'sub': 0}

    print(f"{yellow} ⏩ {blue}Chế độ Tym (1: Bật / 2: Tắt): {white}", end="")
    if input().strip() == '1':
        listnv.append('instagram_like')
        print(f"{yellow} ⏩ {blue}Delay Tym (Nhập 0 để bỏ qua): {white}", end="")
        try: timedelays['tym'] = int(input().strip())
        except: pass

    print(f"{yellow} ⏩ {blue}Chế độ Follow (1: Bật / 2: Tắt): {white}", end="")
    if input().strip() == '1':
        listnv.append('instagram_follow')
        print(f"{yellow} ⏩ {blue}Delay Follow (Nhập 0 để bỏ qua): {white}", end="")
        try: timedelays['sub'] = int(input().strip())
        except: pass

    if not listnv:
        print(f"{red}Chọn tối thiểu 1 loại Job!\n")
        sys.exit()

    print(f"{yellow} ⏩ {blue}Nhập số Luồng (Thread) muốn chạy song song: {white}", end="")
    try:
        so_luong = int(input().strip())
        if so_luong < 1: so_luong = 1
    except:
        so_luong = len(mangcookie)

    banner()
    print(f"{cyan} ✅ {cam}XSMM User    : {white}{username}")
    print(f"{cyan} ✅ {cam}Số Nick Chạy : {white}{len(mangcookie)}")
    print(f"{cyan} ✅ {cam}Đang chạy    : {white}{so_luong} Luồng Song Song")
    print(f"{cyan} ✅ {cam}Số Dư Ban Đầu: {green}{xu} xu")
    print(f"{yellow} ────────────────────────────────────────────────────────{reset}\n")

    # Bắt đầu ThreadPoolExecutor để chạy Đa Luồng
    with ThreadPoolExecutor(max_workers=so_luong) as executor:
        for acc_data in mangcookie:
            executor.submit(run_account_worker, acc_data, xsmm, listnv, dl, doi, timedelays)
