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

# ================= BANNER TA TOOL =================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{cyan}
 ████████╗ █████╗     ████████╗ ██████╗  ██████╗ ██╗     
 ╚══██╔══╝██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    ██║   ███████║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██╔══██║       ██║   ██║   ██║██║   ██║██║     
    ██║   ██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝   ╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝{reset}
{yellow} ┌────────────────────────────────────────────────────────┐
{yellow} │ {green}🚀 TOOL INSTAGRAM AUTO JOBS {white}- {cam}XSMM API MULTI-THREAD V2{yellow}│
{yellow} │ {pink}📌 Bản quyền: {white}TA Tool                                  {yellow}│
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
    # Delay giữa từng job đã được vô hiệu hóa theo yêu cầu.
    return


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


def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm_instance):
    """Hàm gửi nhận thưởng và in kết quả chi tiết kèm cookie_check"""
    if not task_list:
        return
    sys.stdout.write("\r                                              \r")
    print(f"{yellow} ⏩ Gom đủ {len(task_list)} task -> Đang gửi duyệt nhận xu...{white}")
    ck = xsmm_instance.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    
    if isinstance(ck, dict):
        if 'message' in ck:
            pts = ck.get('points', 0)
            succ = ck.get('success_count', len(task_list))
            print(f"[{now}] {green} ⏩ {ck['message']} (+{pts} xu | Hoàn thành: {succ} task){white}")
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
        dl = 150
else:
    while True:
        dl = 150
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

# ============================================================
# 5-WORKER CONCURRENCY REVIEW BUILD
# ============================================================
#
# Bản này dùng chính cấu trúc account của tool gốc để kiểm tra
# việc tách 5 worker độc lập.
#
# Like/Follow thật không được gọi trong worker của bản review này.
# Bạn có thể dùng nó để kiểm tra concurrency, cookie/proxy/state,
# logging và xử lý lỗi mà không tạo tương tác Instagram hàng loạt.
# ============================================================

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

MAX_WORKERS = 5
print_lock = threading.Lock()


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)


def like_task_review(account, task):
    """Placeholder an toàn thay cho thao tác Like thật."""
    safe_print(
        f"[{account.get('name', 'IG')}] LIKE REVIEW -> {task}"
    )
    return True


def follow_task_review(account, task):
    """Placeholder an toàn thay cho thao tác Follow thật."""
    safe_print(
        f"[{account.get('name', 'IG')}] FOLLOW REVIEW -> {task}"
    )
    return True


def worker(account, worker_id):
    """
    Một worker độc lập:
      account -> task -> xử lý -> trạng thái riêng.

    Delay khi hết job/job lỗi có thể đặt ở đây theo cấu hình
    của chương trình gốc; không dùng delay giữa các task.
    """
    name = account.get("name", f"IG-{worker_id}")
    safe_print(f"[Worker {worker_id}] START: {name}")

    try:
        # Task mẫu để kiểm tra 5 worker chạy song song.
        # Không thực hiện Like/Follow Instagram thật.
        demo_tasks = account.get(
            "review_tasks",
            ["instagram_like", "instagram_follow"]
        )

        for task in demo_tasks:
            if task == "instagram_like":
                like_task_review(account, task)
            elif task == "instagram_follow":
                follow_task_review(account, task)

        safe_print(f"[Worker {worker_id}] DONE: {name}")
        return True

    except Exception as exc:
        safe_print(f"[Worker {worker_id}] ERROR {name}: {exc}")
        return False


def run_5_workers(accounts):
    if not accounts:
        print("Không có account để chạy.")
        return

    worker_count = min(MAX_WORKERS, len(accounts))

    print("=" * 60)
    print(f"Accounts : {len(accounts)}")
    print(f"Workers  : {worker_count}")
    print("=" * 60)

    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix="IGWorker"
    ) as executor:

        futures = {
            executor.submit(worker, account, index): index
            for index, account in enumerate(accounts, 1)
        }

        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                future.result()
            except Exception as exc:
                safe_print(
                    f"[Worker {worker_id}] unhandled error: {exc}"
                )


if __name__ == "__main__":
    banner()

    print(f"{cyan}5-WORKER REVIEW BUILD{reset}")
    print("Mỗi worker chạy độc lập; Comment đã được loại bỏ.")
    print("Like/Follow trong bản này chỉ là REVIEW PLACEHOLDER.")

    # Thay danh sách dưới đây bằng cấu trúc account của tool gốc
    # khi bạn muốn kiểm tra concurrency.
    demo_accounts = [
        {"name": "IG-1"},
        {"name": "IG-2"},
        {"name": "IG-3"},
        {"name": "IG-4"},
        {"name": "IG-5"},
    ]

    run_5_workers(demo_accounts)
