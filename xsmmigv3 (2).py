# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import re
import random
import threading
import sqlite3
import base64
from datetime import datetime, timedelta
from urllib.parse import unquote
import keyboard
from curl_cffi import requests as c_requests
import requests
import customtkinter as ctk
from tkinter import filedialog, Menu

# Cấu hình giao diện Light Pro Theme (Enterprise Dashboard Style)
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

CONFIG_FILE = "config_mmo_fb_ig_v6.json"
DB_FILE = "mmo_fb_ig_accounts_v6.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEC_CH_UA_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def init_database():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        cookie TEXT,
                        proxy TEXT,
                        status TEXT,
                        coins INTEGER DEFAULT 0,
                        max_jobs INTEGER DEFAULT 100
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS fb_pages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_username TEXT,
                        page_id TEXT UNIQUE,
                        page_name TEXT,
                        page_token TEXT,
                        proxy TEXT,
                        status TEXT,
                        coins INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        level TEXT,
                        message TEXT
                    )''')
    
    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN max_jobs INTEGER DEFAULT 100;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN coins INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE fb_pages ADD COLUMN coins INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def encrypt_local_data(raw_text):
    return base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')

def decrypt_local_data(enc_text):
    try:
        return base64.b64decode(enc_text.encode('utf-8')).decode('utf-8')
    except:
        return enc_text

def ai_generate_unique_comment():
    comments = [
        "Bài viết tuyệt vời quá! 🔥",
        "Quá đỉnh luôn bạn ơi 💯",
        "Tuyệt vời, ủng hộ bạn nhé ✨",
        "Nhìn cuốn phết nhỉ 👍",
        "Quá chất lượng cho chiếc post này 🚀",
        "Thả tim nhiệt tình luôn nha ❤️",
        "Tuyệt vời ông mặt trời 🌟",
        "Đỉnh của chóp luôn bạn nhé 🎯",
        "Quá xuất sắc, tương tác mạnh nào 💎"
    ]
    return random.choice(comments) + f" [{random.randint(1000, 9999)}]"

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
    elif "@" in proxy_str:
        formatted = f"{scheme}://{proxy_str}"
    else:
        formatted = f"{scheme}://{proxy_str}"
    return {"http": formatted, "https": formatted}

def parse_real_earned_points(response_data, default_points=10):
    if isinstance(response_data, dict):
        if "error" in response_data:
            return 0, str(response_data.get("error"))
        val = response_data.get('points')
        if val is not None:
            try:
                v_int = int(val)
                if v_int > 0: return v_int, "Thành công"
            except: pass
        success_cnt = response_data.get('success_count')
        if success_cnt is not None:
            try:
                v_cnt = int(success_cnt)
                if v_cnt > 0: return v_cnt * default_points, "Thành công"
            except: pass
        msg = str(response_data.get("message", "Thành công"))
        return 0, msg
    return 0, "Phản hồi từ server không hợp lệ"

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_social_account(self, username_or_link, social_type="instagram"):
        url = f"{self.base_url}/accounts2"
        if "instagram.com" in username_or_link or "facebook.com" in username_or_link:
            link_fmt = username_or_link
        else:
            clean_user = username_or_link.replace("@", "").strip()
            link_fmt = f"https://www.instagram.com/{clean_user}" if social_type == "instagram" else f"https://www.facebook.com/{clean_user}"
            
        payload = {"type": social_type, "link_account": link_fmt}
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            res_json = response.json()
            if response.status_code in [200, 201] and ("id" in res_json or "account_id" in res_json or res_json.get("success")):
                return True
        except: pass
        return False

    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        endpoints_to_try = [
            (f"{self.base_url}/tasks2", {"type": job_type, "uid": str(uid).strip(), "typejob": typejob}),
            (f"{self.base_url}/tasks", {"type": job_type, "uid": str(uid).strip()}),
            (f"{self.base_url}/tasks2", {"type": job_type, "account_id": str(uid).strip(), "typejob": typejob}),
            (f"{self.base_url}/{job_type}", {"uid": str(uid).strip()})
        ]
        
        last_error_msg = ""
        for url, params in endpoints_to_try:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=12)
                res = response.json()
                
                if isinstance(res, list) and len(res) > 0:
                    return res, "OK"
                elif isinstance(res, dict):
                    if "error" in res or res.get("success") is False:
                        last_error_msg = res.get("message") or res.get("error") or "Lỗi từ API Server"
                    
                    for key in ["data", "tasks", "list", "result", "job", "jobs", "data_task", "items"]:
                        val = res.get(key)
                        if isinstance(val, list) and len(val) > 0:
                            return val, "OK"
            except Exception as e:
                last_error_msg = str(e)
                continue
        
        return [], last_error_msg if last_error_msg else "Hết job hoặc tài khoản chưa liên kết/chưa cấu hình trên web"

def gui_nhan_xu(job_type, task_ids, uid, cookie_check="", xsmm_obj=None):
    if isinstance(cookie_check, XSMMTool):
        xsmm_obj = cookie_check
        cookie_check = ""
        
    url = f"https://xsmm.net/api/taskapi/tasks2/complete"
    payload = {
        "type": job_type,
        "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
        "uid": str(uid)
    }
    if cookie_check:
        payload["cookie_check"] = cookie_check
    
    headers = xsmm_obj.headers if xsmm_obj and hasattr(xsmm_obj, "headers") else {"Content-Type": "application/json"}
    
    for _ in range(2):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            res_data = response.json()
            if isinstance(res_data, dict) and res_data.get("retry") is True:
                time.sleep(3)
                continue
            return res_data
        except requests.exceptions.Timeout:
            return {"is_timeout": True, "message": f"Đã gửi duyệt {len(payload['task_id'])} job thành công"}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Thất bại"}

def check_cookie_ig(cookie, proxy=None):
    try:
        return c_requests.get('https://www.instagram.com/api/v1/accounts/edit/web_form_data/', headers={'x-ig-app-id': '936619743392459', 'cookie': cookie, 'user-agent': USER_AGENT}, proxies=format_proxy(proxy), impersonate="chrome120", timeout=8, max_redirects=5).text
    except Exception as e:
        return json.dumps({"error": str(e)})

def scan_facebook_pages(cookie, proxy=None):
    pages_list = []
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try: k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.facebook.com')
            except: pass
    try:
        res = session.get("https://www.facebook.com/bookmarks/pages", impersonate="chrome120", timeout=12, max_redirects=5).text
        found_matches = re.findall(r'{"id":"(\d+)","name":"([^"]+)".*?"access_token":"([^"]+)"}', res)
        if not found_matches:
            found_matches = re.findall(r'entity_id["\s*:]+["\'](\d+)["\'][\s\S]*?name["\s*:]+["\']([^"\']+)["\']', res)
        for pid, pname, *ptok in found_matches:
            ptoken = ptok[0] if ptok else cookie
            pages_list.append({"page_id": pid, "page_name": unquote(pname).encode().decode('utf-8', 'ignore'), "page_token": ptoken})
    except Exception as e:
        print(f"Lỗi quét Page: {e}")
    return pages_list

def fb_page_like(target_url, page_token, proxy=None):
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    try:
        res = session.post("https://graph.facebook.com/v18.0/me/likes", data={"access_token": page_token, "object": target_url}, timeout=8)
        return res.text
    except Exception as e:
        return json.dumps({"error": str(e)})

def fb_page_follow(target_id, page_token, proxy=None):
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    try:
        res = session.post(f"https://graph.facebook.com/v18.0/{target_id}/subscribers", data={"access_token": page_token}, timeout=8)
        return res.text
    except Exception as e:
        return json.dumps({"error": str(e)})

def fb_page_comment(target_id_or_post, comment_text, page_token, proxy=None):
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    try:
        res = session.post(f"https://graph.facebook.com/v18.0/{target_id_or_post}/comments", data={"access_token": page_token, "message": comment_text}, timeout=8)
        return res.text
    except Exception as e:
        return json.dumps({"error": str(e)})

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id: return '{"error": "Thiếu target_id"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try: k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        res_home = session.get(profile_url if profile_url else "https://www.instagram.com/", impersonate="chrome120", timeout=8, max_redirects=5).text
        if lsd_match := re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home): lsd = lsd_match.group(1)
        if dtsg_match := (re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)): fb_dtsg = dtsg_match.group(1)
    except: pass
    dynamic_csrftoken = session.cookies.get('csrftoken') or (re.search(r'csrftoken=([^;]+)', cookie) or [None, "missing"])[1]
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, profile_url if profile_url else "https://www.instagram.com/"))
    actor_id = (re.search(r'ds_user_id=(\d+)', cookie) or [None, "0"])[1]
    variables = {"target_user_id": str(target_id), "container_module": "profile", "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link"}
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisFollowMutation",
        "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)
    }
    try:
        res = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=12, max_redirects=5)
        return res.text.strip()
    except Exception as e:
        return json.dumps({"error": f"Exception: {str(e)}"})

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie,
        'origin': 'https://www.instagram.com',
        'referer': referer,
        'sec-ch-ua': SEC_CH_UA_120,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': USER_AGENT,
        'x-asbd-id': '129477',
        'x-csrftoken': csrftoken,
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-requested-with': 'XMLHttpRequest'
    }

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error", "message": "Thiếu mediaid"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                key, val = item.strip().split('=', 1)
                session.cookies.set(key, val, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        res_home = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=8, max_redirects=5).text
        if lsd_match := re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home): lsd = lsd_match.group(1)
        if dtsg_match := (re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)): fb_dtsg = dtsg_match.group(1)
        if jazoest_match := re.search(r'name="jazoest" value="(\d+)"', res_home): jazoest = jazoest_match.group(1)
    except Exception: pass
    
    dynamic_csrftoken = session.cookies.get('csrftoken') or (re.search(r'csrftoken=([^;]+)', cookie) or [None, "missing"])[1]
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id = (re.search(r'ds_user_id=(\d+)', cookie) or [None, "0"])[1]
    tracking_token = ""
    if link_job:
        try:
            res_get = session.get(link_job, impersonate="chrome120", timeout=8, max_redirects=5).text
            if tt_match := re.search(r'"tracking_token":"([^"]+)"', res_get): tracking_token = tt_match.group(1)
        except Exception: pass
    variables = {"input": {"actor_id": actor_id, "client_mutation_id": str(random.randint(1000000, 9999999)), "container_module": "single_post", "media_id": str(mediaid)}}
    if tracking_token: variables["input"]["tracking_token"] = tracking_token
    data = {
        "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
        "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
        "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
        "lsd": lsd, "fb_api_caller_class": "RelayModern", "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
        "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)
    }
    try:
        return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=12, max_redirects=5).text.strip()
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Exception: {str(e)}"})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"error": "Thiếu mediaid"}'
    cookie = unquote(cookie)
    session = c_requests.Session()
    if proxies := format_proxy(proxy): session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try: k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        res_home = session.get(link_job if link_job else "https://www.instagram.com/", impersonate="chrome120", timeout=8, max_redirects=5).text
        if lsd_match := re.search(r'"LSD",\[\],{"token":"([^"]+)"}', res_home): lsd = lsd_match.group(1)
        if dtsg_match := (re.search(r'"dtsg":\{"token":"([^"]+)"', res_home) or re.search(r'name="fb_dtsg" value="([^"]+)"', res_home)): fb_dtsg = dtsg_match.group(1)
    except Exception: pass
    dynamic_csrftoken = session.cookies.get('csrftoken') or (re.search(r'csrftoken=([^;]+)', cookie) or [None, "missing"])[1]
    session.headers.update(get_ig_headers(cookie, dynamic_csrftoken, link_job if link_job else "https://www.instagram.com/"))
    actor_id = (re.search(r'ds_user_id=(\d+)', cookie) or [None, "0"])[1]
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
        res = session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=12, max_redirects=5)
        return res.text.strip()
    except Exception as e:
        return json.dumps({"error": f"Exception: {str(e)}"})

class MMOApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Enterprise Automation Pro - MMO Console")
        self.geometry("1420x860")
        self.configure(fg_color="#f8fafc")
        
        init_database()
        self.is_running = False
        self.total_coins = 0
        self.success_jobs = 0
        self.start_time = None
        self.lock = threading.Lock()
        
        self.acc_rows = {}
        self.page_rows = {}
        self.single_running_threads = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # ---------------- TOP NAVIGATION BAR (MODERN DASHBOARD STYLE) ----------------
        self.top_nav = ctk.CTkFrame(self, height=54, fg_color="#ffffff", corner_radius=0, border_width=1, border_color="#e2e8f0")
        self.top_nav.grid(row=0, column=0, sticky="ew")
        self.top_nav.grid_columnconfigure(4, weight=1)

        self.btn_tab_fb = ctk.CTkButton(self.top_nav, text="📱 Quản lý Instagram", fg_color="#2563eb", hover_color="#1d4ed8", text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("accounts"))
        self.btn_tab_fb.grid(row=0, column=0, padx=10, pady=9, sticky="w")

        self.btn_tab_page = ctk.CTkButton(self.top_nav, text="📘 Quản lý Facebook Page", fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("pages"))
        self.btn_tab_page.grid(row=0, column=1, padx=4, pady=9, sticky="w")

        self.btn_tab_coin = ctk.CTkButton(self.top_nav, text="📊 Dashboard & Logs", fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("dashboard"))
        self.btn_tab_coin.grid(row=0, column=2, padx=4, pady=9, sticky="w")

        self.btn_config_chung = ctk.CTkButton(self.top_nav, text="⚙️ Cấu hình chung", fg_color="#0f172a", hover_color="#1e293b", text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), height=36, corner_radius=8, command=self.open_config_modal)
        self.btn_config_chung.grid(row=0, column=4, padx=16, pady=9, sticky="e")

        # ---------------- MAIN CONTENT AREA (TABVIEWS) ----------------
        self.main_content = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        self.setup_tab_accounts()
        self.setup_tab_fb_pages()
        self.setup_tab_dashboard()

        # ---------------- BOTTOM STATUS BAR ----------------
        self.status_bar = ctk.CTkFrame(self, height=36, fg_color="#ffffff", corner_radius=0, border_width=1, border_color="#e2e8f0")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(3, weight=1)

        self.lbl_footer_stats = ctk.CTkLabel(self.status_bar, text="Tổng tài khoản: 0 | Đang chạy: 0 | Live: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155")
        self.lbl_footer_stats.grid(row=0, column=0, padx=16, pady=6, sticky="w")

        self.lbl_xsmm_balance = ctk.CTkLabel(self.status_bar, text="💰 TỔNG XU KIẾM ĐƯỢC: 0 XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669")
        self.lbl_xsmm_balance.grid(row=0, column=1, padx=16, pady=6, sticky="w")

        self.lbl_status_uptime = ctk.CTkLabel(self.status_bar, text="⏱️ UPTIME: 00:00:00 | Phím tắt: Ctrl+F5 (Start All), Ctrl+F6 (Kill Switch)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b")
        self.lbl_status_uptime.grid(row=0, column=3, padx=16, pady=6, sticky="e")

        # Hidden variables for backward compatibility & Job selection checkboxes
        self.ent_token = ctk.CTkEntry(self)
        self.ent_delay = ctk.CTkEntry(self)
        self.ent_threads = ctk.CTkEntry(self)
        
        # Checkboxes chọn loại job Instagram
        self.chk_ig_like = ctk.CTkCheckBox(self, text="Like")
        self.chk_ig_follow = ctk.CTkCheckBox(self, text="Follow")
        self.chk_ig_cmt = ctk.CTkCheckBox(self, text="Comment")
        self.chk_ig_like.select()
        self.chk_ig_follow.select()
        self.chk_ig_cmt.select()

        # Checkboxes chọn loại job Facebook Page
        self.chk_fb_like = ctk.CTkCheckBox(self, text="")
        self.chk_fb_follow = ctk.CTkCheckBox(self, text="")
        self.chk_fb_cmt = ctk.CTkCheckBox(self, text="")
        self.chk_fb_like.select(); self.chk_fb_follow.select(); self.chk_fb_cmt.select()

        self.ent_delay.insert(0, "2")
        self.ent_threads.insert(0, "5")

        self.load_config()
        self.load_accounts_from_db()
        self.load_fb_pages_from_db()
        self.update_uptime_loop()
        self.init_global_hotkeys()
        self.switch_tab("accounts")

    def switch_tab(self, tab_name):
        for frame in [self.frame_acc_tab, self.frame_page_tab, self.frame_dash_tab]:
            frame.grid_forget()
        
        for btn in [self.btn_tab_fb, self.btn_tab_page, self.btn_tab_coin]:
            btn.configure(fg_color="#f1f5f9", text_color="#475569")

        if tab_name == "accounts":
            self.frame_acc_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_fb.configure(fg_color="#2563eb", text_color="#ffffff")
        elif tab_name == "pages":
            self.frame_page_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_page.configure(fg_color="#2563eb", text_color="#ffffff")
        elif tab_name == "dashboard":
            self.frame_dash_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_coin.configure(fg_color="#2563eb", text_color="#ffffff")

    def open_config_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("⚙️ Cấu hình chung & Chọn Job Instagram")
        modal.geometry("580x560")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="🔑 HỆ THỐNG ACCESS TOKEN", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(20, 4))
        ent_t = ctk.CTkEntry(modal, placeholder_text="Nhập Bearer Token...", height=38, font=ctk.CTkFont(size=11), fg_color="#f8fafc", border_color="#cbd5e1")
        ent_t.pack(fill="x", padx=24, pady=(0, 12))
        try:
            current_t = self.ent_token.get()
            if current_t: ent_t.insert(0, current_t)
        except: pass

        # Bảng chọn Job Instagram tùy chỉnh
        ctk.CTkLabel(modal, text="🎯 TỰ CHỌN LOẠI JOB INSTAGRAM (CHỈ CHẠY JOB ĐƯỢC CHỌN)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(6, 4))
        
        frame_job_choices = ctk.CTkFrame(modal, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#e2e8f0")
        frame_job_choices.pack(fill="x", padx=24, pady=(0, 12))

        modal_chk_like = ctk.CTkCheckBox(frame_job_choices, text="Instagram Like (Thả tim)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_like.pack(anchor="w", padx=16, pady=8)
        if self.chk_ig_like.get(): modal_chk_like.select()

        modal_chk_follow = ctk.CTkCheckBox(frame_job_choices, text="Instagram Follow (Theo dõi)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_follow.pack(anchor="w", padx=16, pady=8)
        if self.chk_ig_follow.get(): modal_chk_follow.select()

        modal_chk_cmt = ctk.CTkCheckBox(frame_job_choices, text="Instagram Comment (Bình luận AI)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_cmt.pack(anchor="w", padx=16, pady=(8, 12))
        if self.chk_ig_cmt.get(): modal_chk_cmt.select()

        ctk.CTkLabel(modal, text="⚙️ THÔNG SỐ CHẠY & DELAY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(4, 4))
        
        row_p = ctk.CTkFrame(modal, fg_color="transparent")
        row_p.pack(fill="x", padx=24, pady=4)
        row_p.grid_columnconfigure((0, 1), weight=1)

        f1 = ctk.CTkFrame(row_p, fg_color="transparent")
        f1.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkLabel(f1, text="Delay (giây):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155").pack(anchor="w")
        ent_d = ctk.CTkEntry(f1, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_d.pack(fill="x", pady=(2, 0))
        ent_d.insert(0, self.ent_delay.get())

        f2 = ctk.CTkFrame(row_p, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(f2, text="Threads:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155").pack(anchor="w")
        ent_th = ctk.CTkEntry(f2, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_th.pack(fill="x", pady=(2, 0))
        ent_th.insert(0, self.ent_threads.get())

        def save_modal():
            self.ent_token.delete(0, "end")
            self.ent_token.insert(0, ent_t.get().strip())
            self.ent_delay.delete(0, "end")
            self.ent_delay.insert(0, ent_d.get().strip())
            self.ent_threads.delete(0, "end")
            self.ent_threads.insert(0, ent_th.get().strip())

            # Cập nhật trạng thái checkbox job Instagram chính
            if modal_chk_like.get(): self.chk_ig_like.select()
            else: self.chk_ig_like.deselect()

            if modal_chk_follow.get(): self.chk_ig_follow.select()
            else: self.chk_ig_follow.deselect()

            if modal_chk_cmt.get(): self.chk_ig_cmt.select()
            else: self.chk_ig_cmt.deselect()

            self.save_config()
            modal.destroy()
            self.log("⚙️ Đã cập nhật cấu hình và danh sách job Instagram muốn chạy!")

        ctk.CTkButton(modal, text="💾 Lưu Cấu Hình & Job", fg_color="#059669", hover_color="#047857", height=40, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8, command=save_modal).pack(fill="x", padx=24, pady=16)

    def setup_tab_accounts(self):
        self.frame_acc_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_acc_tab.grid_rowconfigure(3, weight=1)
        self.frame_acc_tab.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f8fafc", height=58, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top_bar.grid_columnconfigure(0, weight=1)

        self.ent_quick_cookie = ctk.CTkEntry(top_bar, placeholder_text="Nhập Cookie Instagram | Proxy...", height=36, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.ent_quick_cookie.grid(row=0, column=0, padx=(12, 6), pady=10, sticky="ew")

        self.max_jobs_entry = ctk.CTkEntry(top_bar, placeholder_text="Max Job (VD: 100)", width=130, height=36, font=ctk.CTkFont(size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.max_jobs_entry.grid(row=0, column=1, padx=6, pady=10)
        self.max_jobs_entry.insert(0, "100")

        ctk.CTkButton(top_bar, text="➕ Thêm Acc", width=110, height=36, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, command=self.quick_add_single_account).grid(row=0, column=2, padx=6, pady=10)
        ctk.CTkButton(top_bar, text="📥 Batch Import", width=120, height=36, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, command=self.batch_import_accounts).grid(row=0, column=3, padx=(6, 12), pady=10)

        tool_tbl = ctk.CTkFrame(self.frame_acc_tab, fg_color="transparent", height=42)
        tool_tbl.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        tool_tbl.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(tool_tbl, text="✓ Chọn Tất Cả", width=100, height=28, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_accounts(True)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(tool_tbl, text="✗ Bỏ Chọn", width=85, height=28, fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_accounts(False)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Đã Chọn", width=110, height=28, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_selected_accounts).grid(row=0, column=2, padx=2)

        tbl_head = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f1f5f9", height=36, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))
        tbl_head.grid_columnconfigure(3, weight=1)
        tbl_head.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=35).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=45).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="MODE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=70).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(tbl_head, text="UID / INSTAGRAM ID", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TÊN USERNAME", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=4, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="SỐ XU KIẾM ĐƯỢC", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=120, anchor="w").grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI / LÝ DO CHI TIẾT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=240, anchor="w").grid(row=0, column=6, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=90, anchor="e").grid(row=0, column=7, sticky="e", padx=12)

        self.scroll_accs = ctk.CTkScrollableFrame(self.frame_acc_tab, fg_color="#f8fafc", corner_radius=8)
        self.scroll_accs.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.scroll_accs.grid_columnconfigure(0, weight=1)

    def setup_tab_fb_pages(self):
        self.frame_page_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_page_tab.grid_rowconfigure(3, weight=1)
        self.frame_page_tab.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.frame_page_tab, fg_color="#f8fafc", height=58, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top_bar.grid_columnconfigure(0, weight=1)

        self.txt_fb_cookies = ctk.CTkEntry(top_bar, placeholder_text="Nhập Cookie Facebook chính để quét Page | Proxy...", height=36, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.txt_fb_cookies.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        ctk.CTkButton(top_bar, text="🔍 Quét Page Facebook", width=170, height=36, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, command=self.scan_and_import_fb_pages).grid(row=0, column=1, padx=6, pady=10)

        tool_tbl = ctk.CTkFrame(self.frame_page_tab, fg_color="transparent", height=42)
        tool_tbl.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        tool_tbl.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(tool_tbl, text="✓ Chọn Tất Cả", width=100, height=28, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(True)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(tool_tbl, text="✗ Bỏ Chọn", width=85, height=28, fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(False)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Đã Chọn", width=110, height=28, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_selected_pages).grid(row=0, column=2, padx=2)

        tbl_head = ctk.CTkFrame(self.frame_page_tab, fg_color="#f1f5f9", height=36, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))
        tbl_head.grid_columnconfigure(2, weight=1)
        tbl_head.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=35).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=45).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="TÊN FACEBOOK PAGE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=2, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="PAGE ID", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="SỐ XU KIẾM ĐƯỢC", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=120, anchor="w").grid(row=0, column=4, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI / LÝ DO CHI TIẾT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=240, anchor="w").grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=90, anchor="e").grid(row=0, column=6, sticky="e", padx=12)

        self.scroll_pages = ctk.CTkScrollableFrame(self.frame_page_tab, fg_color="#f8fafc", corner_radius=8)
        self.scroll_pages.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.scroll_pages.grid_columnconfigure(0, weight=1)

    def setup_tab_dashboard(self):
        self.frame_dash_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_dash_tab.grid_rowconfigure(1, weight=1)
        self.frame_dash_tab.grid_columnconfigure(0, weight=1)

        top_control = ctk.CTkFrame(self.frame_dash_tab, fg_color="#f8fafc", height=64, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_control.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top_control.grid_columnconfigure(2, weight=1)

        self.btn_toggle = ctk.CTkButton(top_control, text="🚀 START ALL (CHẠY TẤT CẢ ACC)", fg_color="#059669", hover_color="#047857", text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=40, width=260, corner_radius=8, command=self.toggle_run_all)
        self.btn_toggle.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        ctk.CTkButton(top_control, text="📥 Xuất File Log", fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#334155", font=ctk.CTkFont(size=11, weight="bold"), height=40, width=140, corner_radius=8, command=self.export_logs).grid(row=0, column=1, padx=6, pady=12, sticky="w")

        self.lbl_status_conn = ctk.CTkLabel(top_control, text="● SYSTEM: DISCONNECTED", font=ctk.CTkFont(size=11, weight="bold"), text_color="#dc2626")
        self.lbl_status_conn.grid(row=0, column=2, padx=16, pady=12, sticky="e")

        log_frame = ctk.CTkFrame(self.frame_dash_tab, fg_color="transparent")
        log_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.txt_log = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=10), text_color="#065f46", fg_color="#ffffff", border_width=1, border_color="#e2e8f0", corner_radius=8)
        self.txt_log.grid(row=0, column=0, sticky="nsew")

    def init_global_hotkeys(self):
        try:
            keyboard.add_hotkey('ctrl+f5', lambda: self.after(0, self.toggle_run_all))
            keyboard.add_hotkey('ctrl+f6', lambda: self.after(0, self.trigger_kill_switch))
        except: pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "token" in data: self.ent_token.insert(0, decrypt_local_data(data["token"]))
            except: pass

    def save_config(self):
        try:
            data = {
                "token": encrypt_local_data(self.ent_token.get().strip())
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except: pass

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        with self.lock:
            self.txt_log.insert("end", f"[{timestamp}] {message}\n")
            self.txt_log.see("end")

    def update_stats(self, coins=0, jobs=0, entity_type="account", entity_key=""):
        with self.lock:
            if coins: 
                self.total_coins += coins
                if entity_type == "account" and entity_key in self.acc_rows:
                    self.acc_rows[entity_key]["coins"] += coins
                    c_val = self.acc_rows[entity_key]["coins"]
                    self.after(0, lambda ek=entity_key, cv=c_val: self.acc_rows[ek]["coin_label"].configure(text=f"+{cv} xu"))
                    self.update_db_coins(entity_key, c_val, is_page=False)
                elif entity_type == "page" and entity_key in self.page_rows:
                    self.page_rows[entity_key]["coins"] += coins
                    c_val = self.page_rows[entity_key]["coins"]
                    self.after(0, lambda ek=entity_key, cv=c_val: self.page_rows[ek]["coin_label"].configure(text=f"+{cv} xu"))
                    self.update_db_coins(entity_key, c_val, is_page=True)

            if jobs: self.success_jobs += jobs
            self.lbl_xsmm_balance.configure(text=f"💰 TỔNG XU KIẾM ĐƯỢC: {self.total_coins} XU")

    def update_db_coins(self, key, coins, is_page=False):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            if is_page:
                cursor.execute("UPDATE fb_pages SET coins = ? WHERE page_id = ?", (coins, key))
            else:
                cursor.execute("UPDATE accounts SET coins = ? WHERE username = ?", (coins, key))
            conn.commit()
            conn.close()
        except: pass

    def update_uptime_loop(self):
        if self.is_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            td_str = str(timedelta(seconds=elapsed))
            self.lbl_status_uptime.configure(text=f"⏱️ UPTIME: {td_str} | Phím tắt: Ctrl+F5 (Start All), Ctrl+F6 (Kill Switch)")
        self.update_account_counter_ui()
        self.after(1000, self.update_uptime_loop)

    def update_account_counter_ui(self):
        total_ig = len(self.acc_rows)
        active_ig = sum(1 for item in self.acc_rows.values() if item["var"].get())
        total_pg = len(self.page_rows)
        active_pg = sum(1 for item in self.page_rows.values() if item["var"].get())
        running_count = sum(1 for status in self.single_running_threads.values() if status)
        total_all = total_ig + total_pg
        self.lbl_footer_stats.configure(text=f"Tổng tài khoản: {total_all} | Đang chạy độc lập: {running_count} | Live: {running_count}")

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f: f.write(self.txt_log.get("0.0", "end"))
                self.log("💾 Đã xuất file log thành công!")
            except Exception as e:
                self.log(f"✖ Lỗi xuất file log: {str(e)}")

    def trigger_kill_switch(self):
        self.is_running = False
        self.single_running_threads.clear()
        self.btn_toggle.configure(text="🚀 START ALL (CHẠY TẤT CẢ ACC)", fg_color="#059669")
        self.lbl_status_conn.configure(text="● SYSTEM: EMERGENCY STOP", text_color="#dc2626")
        for u, info in self.acc_rows.items():
            info["action_btn"].configure(text="Bắt đầu", fg_color="#2563eb", hover_color="#1d4ed8")
            info["status_label"].configure(text="Đã dừng", text_color="#d97706")
        for p, info in self.page_rows.items():
            info["action_btn"].configure(text="Bắt đầu", fg_color="#0284c7", hover_color="#0369a1")
            info["status_label"].configure(text="Đã dừng", text_color="#d97706")
        self.log("🛡️ KÍCH HOẠT KILL SWITCH (Ctrl+F6): Đã ngắt toàn bộ luồng hệ thống!")

    def load_accounts_from_db(self):
        if not os.path.exists(DB_FILE): return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT username, cookie, proxy, status, coins, max_jobs FROM accounts")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                ig_user, ck, proxy, status, db_coins, max_j = row
                idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"])[1]
                acc_data = {"username": ig_user, "cookie": ck, "proxy": proxy, "id": idfb, "coins": db_coins or 0, "max_jobs": max_j if max_j is not None else 100}
                self.add_account_row_to_ui(acc_data, status)
        except Exception as e:
            self.log(f"✖ Lỗi tải tài khoản IG từ Database: {str(e)}")

    def load_fb_pages_from_db(self):
        if not os.path.exists(DB_FILE): return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT parent_username, page_id, page_name, page_token, proxy, status, coins FROM fb_pages")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                parent, pid, pname, ptok, proxy, status, db_coins = row
                page_data = {"parent": parent, "page_id": pid, "page_name": pname, "page_token": ptok, "proxy": proxy, "coins": db_coins or 0}
                self.add_page_row_to_ui(page_data, status)
        except Exception as e:
            self.log(f"✖ Lỗi tải Page Facebook từ Database: {str(e)}")

    def add_account_row_to_ui(self, acc_data, status="Active"):
        ig_user = acc_data["username"]
        if ig_user in self.acc_rows: return

        row_frame = ctk.CTkFrame(self.scroll_accs, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#e2e8f0", height=40)
        row_frame.pack(fill="x", padx=4, pady=3)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)

        var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, fg_color="#059669")
        chk.grid(row=0, column=0, padx=(10, 6), pady=6, sticky="w")

        stt_idx = len(self.acc_rows) + 1
        lbl_stt = ctk.CTkLabel(row_frame, text=str(stt_idx), font=ctk.CTkFont(size=11), text_color="#334155", width=45)
        lbl_stt.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        lbl_mode = ctk.CTkLabel(row_frame, text="COOKIE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2563eb", width=70)
        lbl_mode.grid(row=0, column=2, padx=6, pady=6, sticky="w")

        lbl_id = ctk.CTkLabel(row_frame, text=str(acc_data.get('id', 'N/A')), font=ctk.CTkFont(family="Consolas", size=10), text_color="#475569")
        lbl_id.grid(row=0, column=3, padx=6, pady=6, sticky="w")

        lbl_user = ctk.CTkLabel(row_frame, text=f"@{ig_user}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a")
        lbl_user.grid(row=0, column=4, padx=6, pady=6, sticky="w")

        init_c = acc_data.get("coins", 0)
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{init_c} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=120, anchor="w")
        lbl_coin.grid(row=0, column=5, padx=6, pady=6, sticky="w")

        lbl_status = ctk.CTkLabel(row_frame, text="Sẵn sàng", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155", width=240, anchor="w")
        lbl_status.grid(row=0, column=6, padx=6, pady=6, sticky="w")

        def toggle_single_acc():
            is_currently_running = self.single_running_threads.get(ig_user, False)
            if not is_currently_running:
                token = self.ent_token.get().strip()
                if not token:
                    self.log("✖ Vui lòng nhập XSMM Access Token trong Cấu hình chung!")
                    return
                try: delay_val = int(self.ent_delay.get().strip())
                except: delay_val = 2
                
                # Lấy danh sách job IG người dùng đã chọn
                chosen_ig_jobs = []
                if self.chk_ig_like.get(): chosen_ig_jobs.append('instagram_like')
                if self.chk_ig_follow.get(): chosen_ig_jobs.append('instagram_follow')
                if self.chk_ig_cmt.get(): chosen_ig_jobs.append('instagram_comment')

                if not chosen_ig_jobs:
                    self.log(f"✖ [IG - @{ig_user}] Bạn chưa chọn loại job nào để chạy! Vào 'Cấu hình chung' để chọn.")
                    return

                self.single_running_threads[ig_user] = True
                btn_action.configure(text="Dừng", fg_color="#dc2626", hover_color="#b91c1c")
                lbl_status.configure(text=f"Đang chạy ({', '.join(chosen_ig_jobs)})...", text_color="#2563eb")
                self.log(f"▶ Khởi chạy luồng độc lập cho tài khoản IG: @{ig_user} với job: {chosen_ig_jobs}")
                
                threading.Thread(target=self.worker_single_account_loop, args=(token, chosen_ig_jobs, delay_val, acc_data, btn_action, lbl_status), daemon=True).start()
            else:
                self.single_running_threads[ig_user] = False
                btn_action.configure(text="Bắt đầu", fg_color="#2563eb", hover_color="#1d4ed8")
                lbl_status.configure(text="Đã dừng", text_color="#d97706")
                self.log(f"⏹ Đã dừng luồng tài khoản IG: @{ig_user}")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=80, height=26, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=toggle_single_acc)
        btn_action.grid(row=0, column=7, padx=10, pady=6, sticky="e")

        self.acc_rows[ig_user] = {"frame": row_frame, "var": var, "status_label": lbl_status, "coin_label": lbl_coin, "action_btn": btn_action, "coins": init_c, "data": acc_data}

    def add_page_row_to_ui(self, page_data, status="Active"):
        pid = page_data["page_id"]
        if pid in self.page_rows: return

        row_frame = ctk.CTkFrame(self.scroll_pages, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#e2e8f0", height=40)
        row_frame.pack(fill="x", padx=4, pady=3)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)

        var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, fg_color="#0284c7")
        chk.grid(row=0, column=0, padx=(10, 6), pady=6, sticky="w")

        stt_idx = len(self.page_rows) + 1
        lbl_stt = ctk.CTkLabel(row_frame, text=str(stt_idx), font=ctk.CTkFont(size=11), text_color="#334155", width=45)
        lbl_stt.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        lbl_name = ctk.CTkLabel(row_frame, text=page_data["page_name"], font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a")
        lbl_name.grid(row=0, column=2, padx=6, pady=6, sticky="w")

        lbl_id = ctk.CTkLabel(row_frame, text=str(pid), font=ctk.CTkFont(family="Consolas", size=10), text_color="#475569")
        lbl_id.grid(row=0, column=3, padx=6, pady=6, sticky="w")

        init_c = page_data.get("coins", 0)
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{init_c} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=120, anchor="w")
        lbl_coin.grid(row=0, column=4, padx=6, pady=6, sticky="w")

        lbl_status = ctk.CTkLabel(row_frame, text="Sẵn sàng", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155", width=240, anchor="w")
        lbl_status.grid(row=0, column=5, padx=6, pady=6, sticky="w")

        def toggle_single_page():
            is_currently_running = self.single_running_threads.get(pid, False)
            if not is_currently_running:
                token = self.ent_token.get().strip()
                if not token:
                    self.log("✖ Vui lòng nhập XSMM Access Token trong Cấu hình chung!")
                    return
                try: delay_val = int(self.ent_delay.get().strip())
                except: delay_val = 2
                
                self.single_running_threads[pid] = True
                btn_action.configure(text="Dừng", fg_color="#dc2626", hover_color="#b91c1c")
                lbl_status.configure(text="Đang chạy độc lập...", text_color="#0284c7")
                self.log(f"▶ Khởi chạy luồng độc lập cho Page: {page_data['page_name']}")
                
                listnv = ['facebook_like', 'facebook_follow', 'facebook_comment']
                threading.Thread(target=self.worker_single_page_loop, args=(token, listnv, delay_val, page_data, btn_action, lbl_status), daemon=True).start()
            else:
                self.single_running_threads[pid] = False
                btn_action.configure(text="Bắt đầu", fg_color="#0284c7", hover_color="#0369a1")
                lbl_status.configure(text="Đã dừng", text_color="#d97706")
                self.log(f"⏹ Đã dừng luồng Page: {page_data['page_name']}")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=80, height=26, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=toggle_single_page)
        btn_action.grid(row=0, column=6, padx=10, pady=6, sticky="e")

        self.page_rows[pid] = {"frame": row_frame, "var": var, "status_label": lbl_status, "coin_label": lbl_coin, "action_btn": btn_action, "coins": init_c, "data": page_data}

    def toggle_all_accounts(self, select_state):
        for item in self.acc_rows.values():
            item["var"].set(select_state)

    def toggle_all_pages(self, select_state):
        for item in self.page_rows.values():
            item["var"].set(select_state)

    def delete_selected_accounts(self):
        to_delete = [u for u, info in self.acc_rows.items() if not info["var"].get()]
        if not to_delete:
            self.log("💡 Vui lòng bỏ chọn checkbox các tài khoản IG muốn xóa.")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for ig_user in to_delete:
            self.single_running_threads[ig_user] = False
            cursor.execute("DELETE FROM accounts WHERE username = ?", (ig_user,))
            if ig_user in self.acc_rows:
                self.acc_rows[ig_user]["frame"].destroy()
                del self.acc_rows[ig_user]
        conn.commit()
        conn.close()
        self.log(f"🗑️ Đã xóa {len(to_delete)} tài khoản IG.")

    def delete_selected_pages(self):
        to_delete = [pid for pid, info in self.page_rows.items() if not info["var"].get()]
        if not to_delete:
            self.log("💡 Vui lòng bỏ chọn checkbox các Page muốn xóa.")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for pid in to_delete:
            self.single_running_threads[pid] = False
            cursor.execute("DELETE FROM fb_pages WHERE page_id = ?", (pid,))
            if pid in self.page_rows:
                self.page_rows[pid]["frame"].destroy()
                del self.page_rows[pid]
        conn.commit()
        conn.close()
        self.log(f"🗑️ Đã xóa {len(to_delete)} Page Facebook.")

    def quick_add_single_account(self):
        line = self.ent_quick_cookie.get().strip()
        if not line:
            self.log("✖ Vui lòng nhập Cookie Instagram!")
            return

        try:
            max_jobs_val = int(self.max_jobs_entry.get().strip())
        except:
            max_jobs_val = 100

        def process_quick():
            parts = line.split("|")
            ck = parts[0].strip()
            proxy = parts[1].strip() if len(parts) > 1 else ""
            idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"]).group(1)
            try:
                res_json_str = check_cookie_ig(ck, proxy)
                p_data = json.loads(res_json_str)
                if p_data and 'form_data' in p_data and p_data['form_data'].get('username'):
                    ig_user = p_data['form_data']['username']
                    if idfb == "0": idfb = str(p_data['form_data'].get('id', '0'))
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)", (ig_user, ck, proxy, "Active", 0, max_jobs_val))
                    conn.commit()
                    conn.close()

                    acc_data = {"cookie": ck, "id": idfb, "username": ig_user, "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val}
                    self.after(0, lambda: self.add_account_row_to_ui(acc_data))
                    self.after(0, lambda: self.ent_quick_cookie.delete(0, "end"))
                    self.log(f"✔ Thêm thành công acc IG: @{ig_user} (Max Jobs: {max_jobs_val})")
                else:
                    self.log(f"✖ Lỗi Cookie IG (@{idfb}): Cookie không hợp lệ hoặc hết hạn.")
            except Exception as e:
                self.log(f"✖ Lỗi xác thực cookie IG: {str(e)}")

        threading.Thread(target=process_quick, daemon=True).start()

    def batch_import_accounts(self):
        line = self.ent_quick_cookie.get().strip()
        if not line:
            self.log("✖ Vui lòng nhập Cookie Instagram vào ô nhập liệu!")
            return

        try:
            max_jobs_val = int(self.max_jobs_entry.get().strip())
        except:
            max_jobs_val = 100

        lines = [c.strip() for c in line.split("\n") if c.strip()]

        def process_import():
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            new_added = 0
            for l in lines:
                parts = l.split("|")
                ck = parts[0].strip()
                proxy = parts[1].strip() if len(parts) > 1 else ""
                idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"]).group(1)
                try:
                    p_data = json.loads(check_cookie_ig(ck, proxy))
                    if p_data and 'form_data' in p_data and p_data['form_data'].get('username'):
                        ig_user = p_data['form_data']['username']
                        if idfb == "0": idfb = str(p_data['form_data'].get('id', '0'))
                        
                        cursor.execute("INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)", (ig_user, ck, proxy, "Active", 0, max_jobs_val))
                        conn.commit()

                        acc_data = {"cookie": ck, "id": idfb, "username": ig_user, "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val}
                        new_added += 1
                        self.after(0, lambda a=acc_data: self.add_account_row_to_ui(a))
                        self.log(f"✔ Đã nạp thành công IG: @{ig_user}")
                except Exception as e:
                    pass
            conn.close()
            if new_added > 0:
                self.log(f"✨ Batch import thành công {new_added} tài khoản IG!")

        threading.Thread(target=process_import, daemon=True).start()

    def scan_and_import_fb_pages(self):
        raw_text = self.txt_fb_cookies.get().strip()
        if not raw_text:
            self.log("✖ Vui lòng nhập Cookie Facebook chính để quét Page!")
            return

        lines = [c.strip() for c in raw_text.split("\n") if c.strip()]

        def process_scan():
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            total_scanned_pages = 0
            
            for line in lines:
                parts = line.split("|")
                ck = parts[0].strip()
                proxy = parts[1].strip() if len(parts) > 1 else ""
                
                self.log("🔍 Đang kết nối Facebook để quét danh sách Page quản lý...")
                pages = scan_facebook_pages(ck, proxy)
                for p in pages:
                    pid = p["page_id"]
                    pname = p["page_name"]
                    ptok = p["page_token"]
                    parent_id = (re.search(r'c_user=(\d+)', ck) or [None, "Main"])[1]
                    
                    cursor.execute("INSERT OR REPLACE INTO fb_pages (parent_username, page_id, page_name, page_token, proxy, status, coins) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (parent_id, pid, pname, ptok, proxy, "Active", 0))
                    conn.commit()
                    
                    page_data = {"parent": parent_id, "page_id": pid, "page_name": pname, "page_token": ptok, "proxy": proxy, "coins": 0}
                    total_scanned_pages += 1
                    self.after(0, lambda pd=page_data: self.add_page_row_to_ui(pd))
                    self.log(f"✔ Tìm thấy & Nạp Page: {pname} (ID: {pid})")
                    
            conn.close()
            self.log(f"✨ Quét thành công tổng cộng {total_scanned_pages} Page Facebook.")

        threading.Thread(target=process_scan, daemon=True).start()

    def toggle_run_all(self):
        if not self.is_running:
            token = self.ent_token.get().strip()
            if not token:
                self.log("✖ Vui lòng nhập XSMM Access Token trong Cấu hình chung!")
                return
            
            self.save_config()
            try: delay_val = int(self.ent_delay.get().strip())
            except: delay_val = 2

            selected_ig = [info for info in self.acc_rows.values() if info["var"].get()]
            selected_pg = [info for info in self.page_rows.values() if info["var"].get()]

            if not selected_ig and not selected_pg:
                self.log("✖ Không có tài khoản hoặc Page nào được chọn (tick chọn checkbox) để chạy!")
                return

            # Lấy danh sách job IG được chọn chung
            chosen_ig_jobs = []
            if self.chk_ig_like.get(): chosen_ig_jobs.append('instagram_like')
            if self.chk_ig_follow.get(): chosen_ig_jobs.append('instagram_follow')
            if self.chk_ig_cmt.get(): chosen_ig_jobs.append('instagram_comment')

            if selected_ig and not chosen_ig_jobs:
                self.log("✖ Bạn chưa chọn loại job Instagram nào để chạy! Vào 'Cấu hình chung' để bật ít nhất 1 loại job.")
                return

            self.is_running = True
            self.start_time = time.time()
            self.btn_toggle.configure(text="🛑 STOP ALL (DỪNG TẤT CẢ)", fg_color="#dc2626", hover_color="#b91c1c")
            self.lbl_status_conn.configure(text="● SYSTEM: MULTI-THREAD ACTIVE", text_color="#059669")

            list_pg_nv = ['facebook_like', 'facebook_follow', 'facebook_comment']

            for info in selected_ig:
                acc_data = info["data"]
                ig_user = acc_data["username"]
                if not self.single_running_threads.get(ig_user, False):
                    self.single_running_threads[ig_user] = True
                    info["action_btn"].configure(text="Dừng", fg_color="#dc2626", hover_color="#b91c1c")
                    info["status_label"].configure(text=f"Đang chạy ({', '.join(chosen_ig_jobs)})...", text_color="#2563eb")
                    threading.Thread(target=self.worker_single_account_loop, args=(token, chosen_ig_jobs, delay_val, acc_data, info["action_btn"], info["status_label"]), daemon=True).start()

            for info in selected_pg:
                page_data = info["data"]
                pid = page_data["page_id"]
                if not self.single_running_threads.get(pid, False):
                    self.single_running_threads[pid] = True
                    info["action_btn"].configure(text="Dừng", fg_color="#dc2626", hover_color="#b91c1c")
                    info["status_label"].configure(text="Đang chạy độc lập...", text_color="#0284c7")
                    threading.Thread(target=self.worker_single_page_loop, args=(token, list_pg_nv, delay_val, page_data, info["action_btn"], info["status_label"]), daemon=True).start()

            self.log(f"🚀 Đã kích hoạt chạy đồng thời {len(selected_ig)} tài khoản IG (với job: {chosen_ig_jobs}) và {len(selected_pg)} Page FB!")
        else:
            self.is_running = False
            self.start_time = None
            self.single_running_threads.clear()
            self.btn_toggle.configure(text="🚀 START ALL (CHẠY TẤT CẢ ACC)", fg_color="#059669", hover_color="#047857")
            self.lbl_status_conn.configure(text="● SYSTEM: DISCONNECTED", text_color="#dc2626")
            
            for info in self.acc_rows.values():
                info["action_btn"].configure(text="Bắt đầu", fg_color="#2563eb", hover_color="#1d4ed8")
                info["status_label"].configure(text="Đã dừng", text_color="#d97706")
            for info in self.page_rows.values():
                info["action_btn"].configure(text="Bắt đầu", fg_color="#0284c7", hover_color="#0369a1")
                info["status_label"].configure(text="Đã dừng", text_color="#d97706")
            
            self.log("🛑 Đã dừng toàn bộ các luồng hệ thống.")

    def worker_single_account_loop(self, token, listnv, delay_val, acc, btn_action, lbl_status):
        xsmm = XSMMTool(token)
        username, ck, id_val, proxy = acc["username"], acc["cookie"], acc["id"], acc["proxy"]
        max_jobs = acc.get("max_jobs", 100)
        attempted_jobs = 0
        
        xsmm.add_social_account(username, "instagram")
        
        while self.single_running_threads.get(username, False):
            if attempted_jobs >= max_jobs:
                self.log(f"ℹ️ [IG - @{username}] Đã chạy đủ {max_jobs} job giới hạn.")
                self.after(0, lambda: lbl_status.configure(text=f"Đã hoàn thành {max_jobs} job", text_color="#059669"))
                break

            for rand_job in [j for j in listnv if 'instagram' in j]:
                if not self.single_running_threads.get(username, False) or attempted_jobs >= max_jobs: break
                
                self.after(0, lambda jn=rand_job: lbl_status.configure(text=f"Đang quét job: {jn}", text_color="#d97706"))

                tasks, err_msg = xsmm.get_tasks(rand_job, id_val)
                if not tasks or not isinstance(tasks, list):
                    fail_reason = f"⚠️ Hết job/Lỗi API: {err_msg[:30]}" if err_msg else "⚠️ Không tìm thấy job"
                    self.after(0, lambda fr=fail_reason: lbl_status.configure(text=fr, text_color="#d97706"))
                    continue

                csf = (re.search(r'csrftoken=([^;]+)', ck) or [None, ""])[1]
                
                if rand_job == 'instagram_follow':
                    success_task_ids = []
                    for nv in tasks:
                        if not self.single_running_threads.get(username, False) or attempted_jobs >= max_jobs: break
                        task_id, link_job = nv.get('id'), nv.get('target_url', '')
                        target_id = nv.get('target_id', '') or nv.get('target_id2', '')
                        default_p = int(nv.get('points', 10))
                        
                        self.after(0, lambda tid=task_id: lbl_status.configure(text=f"Đang Follow [{tid}]...", text_color="#2563eb"))

                        if not target_id or not str(target_id).isdigit():
                            try:
                                temp_sess = c_requests.Session()
                                if px := format_proxy(proxy): temp_sess.proxies = px
                                html = temp_sess.get(link_job, impersonate="chrome120", timeout=8, max_redirects=5).text
                                target_id = (re.search(r'"profile_id":"(\d+)"', html) or re.search(r'"user_id":"(\d+)"', html) or re.search(r'profilePage_(\d+)', html)).group(1)
                            except Exception as e:
                                attempted_jobs += 1
                                fail_msg = f"❌ Thất bại Follow [{task_id}]: Không lấy được target_id ({attempted_jobs}/{max_jobs})"
                                self.after(0, lambda fm=fail_msg: lbl_status.configure(text=fm, text_color="#dc2626"))
                                self.log(f"❌ [IG - @{username}] Follow [{task_id}] thất bại: Không lấy được target_id (Lỗi: {str(e)})")
                                continue

                        success = False
                        fail_reason_detail = "Lỗi kết nối Graph API"
                        if target_id and str(target_id).isdigit():
                            try:
                                res_raw = follow(target_id, ck, csf, link_job, proxy)
                                j = json.loads(res_raw)
                                if "errors" not in j and ("data" in j or j.get("status") == "ok"):
                                    success = True
                                else:
                                    fail_reason_detail = j.get("message") or str(j.get("errors", "IG Block/Checkpoint"))
                            except Exception as e:
                                fail_reason_detail = f"Exception: {str(e)[:25]}"

                        attempted_jobs += 1
                        if success:
                            success_task_ids.append(task_id)
                            self.after(0, lambda tid=task_id, c=attempted_jobs: lbl_status.configure(text=f"✅ Thành công Follow [{tid}] ({c}/{max_jobs})", text_color="#059669"))
                            self.log(f"✅ [IG - @{username}] Follow thành công task {task_id} ({attempted_jobs}/{max_jobs})")
                        else:
                            self.after(0, lambda tid=task_id, fr=fail_reason_detail, c=attempted_jobs: lbl_status.configure(text=f"❌ Thất bại Follow [{tid}]: {fr[:25]} ({c}/{max_jobs})", text_color="#dc2626"))
                            self.log(f"❌ [IG - @{username}] Thất bại Follow [{task_id}]: {fail_reason_detail} ({attempted_jobs}/{max_jobs})")
                        
                        if len(success_task_ids) >= 3 or attempted_jobs >= max_jobs:
                            if success_task_ids:
                                c_res = gui_nhan_xu(rand_job, success_task_ids, id_val, xsmm)
                                earned, _ = parse_real_earned_points(c_res, default_points=default_p * len(success_task_ids))
                                if earned > 0:
                                    self.update_stats(coins=int(earned), jobs=len(success_task_ids), entity_type="account", entity_key=username)
                                    self.log(f"✨ [IG - @{username}] Nhận +{earned} xu")
                                success_task_ids = []
                        time.sleep(min(3, max(1, delay_val)))
                else:
                    for nv in tasks:
                        if not self.single_running_threads.get(username, False) or attempted_jobs >= max_jobs: break
                        task_id, link_job = nv.get('id', ''), nv.get('target_url', '')
                        default_p = int(nv.get('points', 10))
                        success = False
                        fail_reason_detail = "Lỗi kết nối Graph API"
                        
                        job_name_vn = "Like" if rand_job == 'instagram_like' else "Comment"
                        self.after(0, lambda jn=job_name_vn, tid=task_id: lbl_status.configure(text=f"Đang {jn} [{tid}]...", text_color="#2563eb"))

                        if rand_job == 'instagram_like':
                            try:
                                res_raw = tym(nv.get('target_id', ''), ck, csf, link_job, proxy)
                                j = json.loads(res_raw)
                                if "errors" not in j and ("data" in j or j.get("status") == "ok"):
                                    success = True
                                else:
                                    fail_reason_detail = j.get("message") or str(j.get("errors", "IG Block/Checkpoint"))
                            except Exception as e:
                                fail_reason_detail = f"Exception: {str(e)[:25]}"
                        elif rand_job == 'instagram_comment':
                            idm, noidung = nv.get('target_id', ''), nv.get('comment', '') or ai_generate_unique_comment()
                            try:
                                res_raw = cmt(idm, noidung, ck, csf, link_job, proxy)
                                j = json.loads(res_raw)
                                if "errors" not in j and ("data" in j or j.get("status") == "ok"):
                                    success = True
                                else:
                                    fail_reason_detail = j.get("message") or str(j.get("errors", "IG Block/Checkpoint"))
                            except Exception as e:
                                fail_reason_detail = f"Exception: {str(e)[:25]}"

                        attempted_jobs += 1
                        if success:
                            c_res = gui_nhan_xu(rand_job, [task_id], id_val, xsmm)
                            earned, _ = parse_real_earned_points(c_res, default_points=default_p)
                            if earned > 0:
                                self.update_stats(coins=int(earned), jobs=1, entity_type="account", entity_key=username)
                                self.after(0, lambda jn=job_name_vn, tid=task_id, c=attempted_jobs: lbl_status.configure(text=f"✅ Thành công {jn} [{tid}] ({c}/{max_jobs})", text_color="#059669"))
                                self.log(f"✨ [IG - @{username}] Nhận +{earned} xu ({attempted_jobs}/{max_jobs})")
                        else:
                            self.after(0, lambda jn=job_name_vn, tid=task_id, fr=fail_reason_detail, c=attempted_jobs: lbl_status.configure(text=f"❌ Thất bại {jn} [{tid}]: {fr[:25]} ({c}/{max_jobs})", text_color="#dc2626"))
                            self.log(f"❌ [IG - @{username}] Thất bại {job_name_vn} [{task_id}]: {fail_reason_detail} ({attempted_jobs}/{max_jobs})")
                        time.sleep(max(1, delay_val))

            if self.single_running_threads.get(username, False) and attempted_jobs < max_jobs:
                self.after(0, lambda: lbl_status.configure(text="Live (Chờ job)", text_color="#059669"))
            time.sleep(3)

        self.single_running_threads[username] = False
        self.after(0, lambda: btn_action.configure(text="Bắt đầu", fg_color="#2563eb", hover_color="#1d4ed8"))
        self.after(0, lambda: lbl_status.configure(text="Đã dừng", text_color="#d97706"))

    def worker_single_page_loop(self, token, listnv, delay_val, page, btn_action, lbl_status):
        xsmm = XSMMTool(token)
        pid, pname, ptok, proxy = page["page_id"], page["page_name"], page["page_token"], page["proxy"]
        max_jobs = page.get("max_jobs", 100)
        attempted_jobs = 0
        xsmm.add_social_account(pname, "facebook")

        while self.single_running_threads.get(pid, False):
            if attempted_jobs >= max_jobs:
                self.log(f"ℹ️ [FB Page - {pname}] Đã chạy đủ {max_jobs} job giới hạn.")
                self.after(0, lambda: lbl_status.configure(text=f"Đã hoàn thành {max_jobs} job", text_color="#059669"))
                break

            for rand_job in [j for j in listnv if 'facebook' in j]:
                if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs: break
                self.after(0, lambda jn=rand_job: lbl_status.configure(text=f"Đang quét job: {jn}", text_color="#d97706"))

                tasks, err_msg = xsmm.get_tasks(rand_job, pid)
                if not tasks or not isinstance(tasks, list):
                    self.after(0, lambda: lbl_status.configure(text="⚠️ Hết job Page", text_color="#d97706"))
                    continue

                for nv in tasks:
                    if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs: break
                    task_id, link_job = nv.get('id', ''), nv.get('target_url', '')
                    default_p = int(nv.get('points', 10))
                    success = False
                    fail_reason_detail = "Lỗi FB Graph API"
                    
                    fb_job_desc = "FB Like" if 'like' in rand_job else ("FB Follow" if 'follow' in rand_job else "FB Cmt")
                    self.after(0, lambda jbd=fb_job_desc, tid=task_id: lbl_status.configure(text=f"Đang {jbd} [{tid}]...", text_color="#0284c7"))

                    if rand_job == 'facebook_like':
                        try:
                            res_raw = fb_page_like(link_job, ptok, proxy)
                            j = json.loads(res_raw)
                            if "success" in j or j.get("id"):
                                success = True
                            else:
                                fail_reason_detail = j.get("error", {}).get("message", "Token hết hạn / Block")
                        except Exception as e:
                            fail_reason_detail = f"Exception: {str(e)[:20]}"
                    elif rand_job == 'facebook_follow':
                        try:
                            res_raw = fb_page_follow(nv.get('target_id', ''), ptok, proxy)
                            j = json.loads(res_raw)
                            if "success" in j:
                                success = True
                            else:
                                fail_reason_detail = j.get("error", {}).get("message", "Token hết hạn / Block")
                        except Exception as e:
                            fail_reason_detail = f"Exception: {str(e)[:20]}"
                    elif rand_job == 'facebook_comment':
                        try:
                            res_raw = fb_page_comment(nv.get('target_id', '') or link_job, nv.get('comment', '') or ai_generate_unique_comment(), ptok, proxy)
                            j = json.loads(res_raw)
                            if "id" in j:
                                success = True
                            else:
                                fail_reason_detail = j.get("error", {}).get("message", "Token hết hạn / Block")
                        except Exception as e:
                            fail_reason_detail = f"Exception: {str(e)[:20]}"

                    attempted_jobs += 1
                    if success:
                        c_res = gui_nhan_xu(rand_job, [task_id], pid, xsmm)
                        earned, _ = parse_real_earned_points(c_res, default_points=default_p)
                        if earned > 0:
                            self.update_stats(coins=int(earned), jobs=1, entity_type="page", entity_key=pid)
                            self.after(0, lambda jbd=fb_job_desc, tid=task_id, c=attempted_jobs: lbl_status.configure(text=f"✅ Thành công {jbd} [{tid}] ({c}/{max_jobs})", text_color="#059669"))
                            self.log(f"✨ [FB Page - {pname}] Nhận +{earned} xu")
                    else:
                        self.after(0, lambda jbd=fb_job_desc, tid=task_id, fr=fail_reason_detail, c=attempted_jobs: lbl_status.configure(text=f"❌ Thất bại {jbd} [{tid}]: {fr[:25]} ({c}/{max_jobs})", text_color="#dc2626"))
                        self.log(f"❌ [FB Page - {pname}] Thất bại {fb_job_desc} [{task_id}]: {fail_reason_detail} ({attempted_jobs}/{max_jobs})")
                    time.sleep(max(1, delay_val))

            if self.single_running_threads.get(pid, False) and attempted_jobs < max_jobs:
                self.after(0, lambda: lbl_status.configure(text="Live (Chờ job)", text_color="#059669"))
            time.sleep(3)

        self.single_running_threads[pid] = False
        self.after(0, lambda: btn_action.configure(text="Bắt đầu", fg_color="#0284c7", hover_color="#0369a1"))
        self.after(0, lambda: lbl_status.configure(text="Đã dừng", text_color="#d97706"))

if __name__ == "__main__":
    app = MMOApp()
    app.mainloop()
