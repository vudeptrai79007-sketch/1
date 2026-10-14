import time
import json
import urllib.parse
import re
import sys
import os
import random
import requests
import signal

def handle_sigint(sig, frame):
    os._exit(0)

signal.signal(signal.SIGINT, handle_sigint)

# --- CẤU HÌNH API XSMM ---
XSMM_TOKEN = "thêm token vo đây"
XSMM_HEADERS = {
    "Authorization": f"Bearer {XSMM_TOKEN}",
    "Content-Type": "application/json"
}

def parse_cookie_string(cookie_str: str) -> dict:
    """Tách chuỗi cookie thành dictionary."""
    cookies = {}
    cookie_str = cookie_str.strip().rstrip(',')
    for item in cookie_str.split(';'):
        if '=' in item:
            parts = item.strip().split('=', 1)
            if len(parts) == 2:
                key, value = parts
                cookies[key.strip()] = value.strip()
    return cookies

def get_media_id(input_str: str) -> str:
    """Hỗ trợ nhập cả Link bài viết hoặc Media ID trực tiếp."""
    input_str = str(input_str).strip()
    match = re.search(r'/p/([A-Za-z0-9_-]+)', input_str)
    if not match:
        match = re.search(r'/reel/([A-Za-z0-9_-]+)', input_str)
        
    if match:
        shortcode = match.group(1)
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        media_id = 0
        for char in shortcode:
            media_id = (media_id * 64) + alphabet.index(char)
        return str(media_id)
    return input_str

class INSTAGRAM():
    def __init__(self, cookies_str):
        self.cookies_dict = parse_cookie_string(cookies_str)
        self.csrftoken = self.cookies_dict.get('csrftoken', '')
            
    def GETINFO(self):
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            }
            response = requests.get("https://www.instagram.com/", headers=headers, cookies=self.cookies_dict).text
            
            userID_match = re.search(r'"viewerId":"(\d+)"', response)
            if not userID_match:
                userID_match = re.findall(r'userID":.*?,', response)
                userID1 = userID_match[0].split(':"')[1].split('",')[0] if userID_match else None
            else:
                userID1 = userID_match.group(1)
                
            username_match = re.search(r'"username":"([^"]+)"', response)
            ig_username = username_match.group(1) if username_match else userID1
            
            dtsg_match = re.search(r'"dtsg":\s*\{"token":"([^"]+)"', response)
            fb_dtsg = dtsg_match.group(1) if dtsg_match else ""
            
            return userID1, fb_dtsg, "", ig_username
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            return False, False, False, False

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd_token):
        """Thực hiện Like bài viết"""
        media_id = get_media_id(link if link else post_id)

        headers = {
            'User-Agent': 'Instagram 269.0.0.18.75 Android (28/9; 480dpi; 1080x1920; Xiaomi; Redmi Note 7; lavender; qcom; sm6150; en_US; 317822529)',
            'Accept-Language': 'vi-VN, en-US',
            'X-IG-Capabilities': '3brTvx0=',
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-App-ID': '1217981644879628',
            'X-CSRFToken': self.csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'i.instagram.com',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
        }

        url = f"https://i.instagram.com/api/v1/media/{media_id}/like/"
        data = {
            'module_name': 'feed_timeline',
            'media_id': media_id
        }

        try:
            response = requests.post(url, cookies=self.cookies_dict, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get('status') == 'ok':
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Like: {e}")
            return False

    def FOLLOW(self, dtsg, target_user_id):
        """Thực hiện Follow người dùng"""
        url = f"https://www.instagram.com/api/v1/friendships/create/{target_user_id}/"
        headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': '1217981644879628',
            'x-requested-with': 'XMLHttpRequest',
        }
        data = {
            'container_module': 'profile',
            'include_follow_friction_check': 'true',
            'nav_chain': 'PolarisProfileRoot:profilePage:1:via_cold_start',
            'user_id': str(target_user_id),
            'jazoest': '22613',
            'fb_dtsg': dtsg if dtsg else 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'
        }

        try:
            response = requests.post(url, cookies=self.cookies_dict, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get('status') == 'ok' or res_json.get('friendship_status', {}).get('following') == True:
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Follow: {e}")
            return False

    def COMMENT(self, av, dtsg, target_id, target_url, comment_content):
        """Thực hiện Comment bài viết sử dụng nội dung từ server XSMM"""
        url = "https://www.instagram.com/api/graphql"
        media_id = get_media_id(target_url if target_url else target_id)
        
        headers = {
            "authority": "www.instagram.com",
            "accept": "*/*",
            "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.instagram.com",
            "referer": f"https://www.instagram.com/p/{target_id}/comments/",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "x-asbd-id": "359341",
            "x-csrftoken": self.csrftoken,
            "x-fb-friendly-name": "PolarisPostCommentInputRevampedMutation",
            "x-ig-app-id": "1217981644879628",
            "x-ig-max-touch-points": "5",
            "x-requested-with": "XMLHttpRequest",
        }

        variables = (
            '{"connections":["client:root:__PolarisPostComments__xdt_api__v1__media__'
            + media_id
            + '__comments__connection_connection(data:{},media_id:\\"'
            + media_id
            + '\\",sort_order:\\"popular\\")"],"data":{"comment_text":"'
            + comment_content
            + '","media_id":"'
            + media_id
            + '"}}'
        )
        encoded_variables = urllib.parse.quote(variables)

        data = (
            f"av={av}&__d=www&__user=0&__a=1&__req=31"
            "&__hs=20716.HYP%3Ainstagram_web_pkg.2.1...0&dpr=3&__ccg=EXCELLENT&__rev=1047982529"
            "&__comet_req=7"
            f"&fb_dtsg={dtsg if dtsg else 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}"
            "&jazoest=26096&__spin_r=1047982529&__spin_b=trunk&__spin_t=1789924702"
            "&__crn=comet.igweb.PolarisMobileAllCommentsRouteNext&fb_api_caller_class=RelayModern"
            "&fb_api_req_friendly_name=PolarisPostCommentInputRevampedMutation&server_timestamps=true"
            f"&variables={encoded_variables}"
            "&doc_id=27261905640092552"
        )

        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if "data" in res_json or res_json.get("status") == "ok":
                        return True
                except:
                    if "ok" in response.text.lower():
                        return True
            return False
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"   [DEBUG] Lỗi Comment: {e}")
            return False

# --- CÁC HÀM GỌI API HỆ THỐNG XSMM ---

def get_xsmm_user():
    try:
        res = requests.get("https://xsmm.net/api/taskapi/user", headers=XSMM_HEADERS).json()
        return res.get("user", {}) if isinstance(res, dict) else {}
    except Exception:
        return {}

def get_instagram_accounts(search_uid=""):
    try:
        url = "https://xsmm.net/api/taskapi/accounts2?account_type=instagram"
        if search_uid:
            url += f"&search={search_uid}"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        if isinstance(res, dict) and "accounts" in res and isinstance(res["accounts"], list):
            return res["accounts"]
        return []
    except Exception:
        return []

def sync_and_get_xsmm_id(ig_username, fallback_av):
    link_account = f"https://www.instagram.com/{ig_username}"
    payload = {
        "type": "instagram",
        "link_account": link_account
    }
    try:
        requests.post("https://xsmm.net/api/taskapi/accounts2", headers=XSMM_HEADERS, json=payload)
    except Exception:
        pass

    accounts = get_instagram_accounts(search_uid=fallback_av)
    for acc in accounts:
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
            
    all_accounts = get_instagram_accounts()
    for acc in all_accounts:
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fallback_av) or ig_username.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
            
    return fallback_av

def get_tasks(task_type, uid):
    try:
        url = f"https://xsmm.net/api/taskapi/tasks2?type={task_type}&uid={uid}&typejob=normal"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        if isinstance(res, list):
            return res
        return []
    except Exception:
        return []

def complete_tasks(task_type, uid, task_ids, cookie_check):
    try:
        payload = {
            "type": task_type,
            "task_id": task_ids,
            "uid": str(uid),
            "cookie_check": cookie_check
        }
        res = requests.post("https://xsmm.net/api/taskapi/tasks2/complete", headers=XSMM_HEADERS, json=payload).json()
        return res if isinstance(res, dict) else {}
    except Exception:
        return {}

# --- CHƯƠNG TRÌNH CHÍNH ---
def main():
    print("==========================================")
    print("   AUTO INSTAGRAM TASK - XSMM.NET         ")
    print("==========================================")
    
    user_info = get_xsmm_user()
    print(f"Tài khoản: {user_info.get('username')} | Số xu hiện tại: {user_info.get('points')}")
    print("-" * 42)

    instagram_cookie = input("Nhập Cookie Instagram của bạn: ").strip()
    if not instagram_cookie:
        print("Cookie không được để trống!")
        return

    print("\nCHỌN LOẠI NHIỆM VỤ:")
    print("1. Chạy nhiệm vụ LIKE (Nhận xu ngay từng nhiệm vụ)")
    print("2. Chạy nhiệm vụ FOLLOW (Đủ 12 nhiệm vụ mới nhận xu)")
    print("3. Chạy nhiệm vụ COMMENT (Nhận xu ngay từng nhiệm vụ với nội dung từ Server)")
    choice = input("Nhập lựa chọn của bạn (1, 2 hoặc 3): ").strip()

    if choice == '1':
        task_type = "instagram_like"
    elif choice == '2':
        task_type = "instagram_follow"
    elif choice == '3':
        task_type = "instagram_comment"
    else:
        print("Lựa chọn không hợp lệ, mặc định chạy Like!")
        task_type = "instagram_like"

    # Cấu hình delay thao tác
    try:
        delay_min = int(input("Nhập delay thao tác (Tối thiểu - giây, VD: 10): ") or 10)
        delay_max = int(input("Nhập delay thao tác (Tối đa - giây, VD: 15): ") or 15)
    except ValueError:
        delay_min, delay_max = 10, 15

    # Cấu hình delay nhận xu
    try:
        delay_coin_min = int(input("Nhập delay nhận xu (Tối thiểu - giây, VD: 3): ") or 3)
        delay_coin_max = int(input("Nhập delay nhận xu (Tối đa - giây, VD: 5): ") or 5)
    except ValueError:
        delay_coin_min, delay_coin_max = 3, 5

    print("\nĐang kiểm tra cookie và lấy thông tin tài khoản...")
    ig = INSTAGRAM(instagram_cookie)
    res_info = ig.GETINFO()
    
    if res_info == False:
        print("[-] Không thể lấy thông tin phiên đăng nhập. Cookie có thể đã chết!")
        return
        
    av, fb_dtsg, _, ig_username = res_info
    
    if not av:
        print("[-] Không tìm thấy User ID từ Cookie!")
        return

    print(f"[+] Đăng nhập thành công!")
    print(f"    - Instagram Username: {ig_username}")
    print(f"    - Instagram User ID (AV): {av}")

    print("\nĐang đồng bộ tài khoản lên hệ thống XSMM...")
    xsmm_uid = sync_and_get_xsmm_id(ig_username, av)
    print(f"[+] Sử dụng XSMM ID để làm nhiệm vụ: {xsmm_uid}")

    print(f"\nBắt đầu quét nhiệm vụ [{task_type}]...")
    
    success_count_total = 0
    follow_cache_ids = []

    while True:
        tasks = get_tasks(task_type, xsmm_uid)
        
        if not tasks:
            print(f"[-] Không có nhiệm vụ [{task_type}] nào khả dụng. Đang chờ 10 giây quét lại...")
            time.sleep(10)
            continue

        print(f"[+] Tìm thấy {len(tasks)} nhiệm vụ. Đang tiến hành xử lý...")
        
        for index, task in enumerate(tasks, 1):
            task_id = task.get("id")
            target_id = task.get("target_id")
            target_url = task.get("target_url")
            
            # Lấy nội dung comment động từ server (thường nằm ở 'msg' hoặc 'comment')
            comment_content = task.get("msg") or task.get("comment") or "Tuyệt vời quá!"
            
            idorlink = task.get("idorlink") or target_url or target_id or "Không rõ mục tiêu"
            
            print(f"-> Đang thực hiện [{index}/{len(tasks)}]: {idorlink}")
            if task_type == "instagram_comment":
                print(f"   [💬 Nội dung]: {comment_content}")
            
            is_done = False
            if task_type == "instagram_like":
                is_done = ig.LIKE(av, fb_dtsg, target_id, instagram_cookie, target_url, "")
            elif task_type == "instagram_follow":
                follow_uid = target_id if target_id else get_media_id(idorlink)
                is_done = ig.FOLLOW(fb_dtsg, follow_uid)
            elif task_type == "instagram_comment":
                is_done = ig.COMMENT(av, fb_dtsg, target_id, target_url, comment_content)
            
            if is_done:
                print("   [+] Thao tác thành công!")
                success_count_total += 1
                
                if task_type in ["instagram_like", "instagram_comment"]:
                    # Nhận xu ngay lập tức cho Like và Comment
                    result = complete_tasks(task_type, xsmm_uid, [task_id], instagram_cookie)
                    print(f"   [>>] Phản hồi nhận xu: {result}")
                    
                    delay_coin = random.randint(delay_coin_min, delay_coin_max)
                    print(f"   [>>] Nghỉ {delay_coin} giây sau khi nhận xu...")
                    time.sleep(delay_coin)
                    
                elif task_type == "instagram_follow":
                    # Follow gom đủ 12 task mới nhận xu
                    follow_cache_ids.append(task_id)
                    print(f"   [>>] Đã tích lũy trong cache Follow: {len(follow_cache_ids)}/12 nhiệm vụ")
                    
                    if len(follow_cache_ids) >= 12:
                        print("   [>>] Đã đủ 12 nhiệm vụ Follow! Đang tiến hành gửi nhận xu...")
                        result = complete_tasks(task_type, xsmm_uid, follow_cache_ids, instagram_cookie)
                        print(f"   [>>] Phản hồi nhận xu hàng loạt: {result}")
                        
                        follow_cache_ids = []
                        
                        delay_coin = random.randint(delay_coin_min, delay_coin_max)
                        print(f"   [>>] Nghỉ {delay_coin} giây sau khi nhận xu...")
                        time.sleep(delay_coin)

                if success_count_total % 5 == 0:
                    rest_time = random.randint(20, 30)
                    print(f"[*] Đã hoàn thành tổng cộng {success_count_total} nhiệm vụ, nghỉ ngơi an toàn {rest_time} giây...")
                    time.sleep(rest_time)
            else:
                print("   [-] Thao tác thất bại hoặc bị giới hạn tính năng.")
            
            delay_action = random.randint(delay_min, delay_max)
            print(f"   [~] Đang chờ {delay_action} giây trước nhiệm vụ tiếp theo...\n")
            time.sleep(delay_action)
        
        print(f"\n--- Đang tìm đợt nhiệm vụ [{task_type}] tiếp theo ---")
        time.sleep(5)

if __name__ == "__main__":
    main()
