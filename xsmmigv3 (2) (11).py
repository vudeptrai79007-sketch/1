# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import re
import random
import threading
import queue
import sqlite3
import base64
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
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

CONFIG_FILE = "config_mmo_fb_ig_v7.json"
DB_FILE = "mmo_fb_ig_accounts_v7.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEC_CH_UA_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

# Danh sách 12 Chế độ làm Job chuẩn trên Tương Tác Chéo (TTC)
TTC_12_JOB_MODES = {
    "ttc_like_thuong": {
        "name": "1. Like Bài Viết Thường",
        "get_ep": "/kiemtien/getpost.php",
        "claim_ep": "/kiemtien/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/",
        "action": "like",
        "default_xu": 300
    },
    "ttc_like_vip": {
        "name": "2. Like Bài Viết VIP / Giá Rẻ",
        "get_ep": "/kiemtien/likegiare/getpost.php",
        "claim_ep": "/kiemtien/likegiare/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/likegiare/",
        "action": "like",
        "default_xu": 400
    },
    "ttc_camxuc_thuong": {
        "name": "3. Cảm Xúc Bài Viết Thường",
        "get_ep": "/kiemtien/camxuccheo/getpost.php",
        "claim_ep": "/kiemtien/camxuccheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/camxuccheo/",
        "action": "react",
        "default_xu": 400
    },
    "ttc_camxuc_vip": {
        "name": "4. Cảm Xúc Bài Viết VIP",
        "get_ep": "/kiemtien/camxucvipcheo/getpost.php",
        "claim_ep": "/kiemtien/camxucvipcheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/camxucvipcheo/",
        "action": "react",
        "default_xu": 600
    },
    "ttc_cmt_thuong": {
        "name": "5. Bình Luận (Comment) Thường",
        "get_ep": "/kiemtien/cmtcheo/getpost.php",
        "claim_ep": "/kiemtien/cmtcheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/cmtcheo/",
        "action": "comment",
        "default_xu": 600
    },
    "ttc_cmt_vip": {
        "name": "6. Bình Luận (Comment) VIP",
        "get_ep": "/kiemtien/cmtvip/getpost.php",
        "claim_ep": "/kiemtien/cmtvip/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/cmtvip/",
        "action": "comment",
        "default_xu": 800
    },
    "ttc_sub_thuong": {
        "name": "7. Theo Dõi (Follow/Sub) Thường",
        "get_ep": "/kiemtien/subcheo/getpost.php",
        "claim_ep": "/kiemtien/subcheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/subcheo/",
        "action": "follow",
        "default_xu": 600
    },
    "ttc_sub_vip": {
        "name": "8. Theo Dõi (Follow/Sub) VIP",
        "get_ep": "/kiemtien/subgiare/getpost.php",
        "claim_ep": "/kiemtien/subgiare/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/subgiare/",
        "action": "follow",
        "default_xu": 700
    },
    "ttc_likepage_thuong": {
        "name": "9. Like Fanpage Thường",
        "get_ep": "/kiemtien/likepagecheo/getpost.php",
        "claim_ep": "/kiemtien/likepagecheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/likepagecheo/",
        "action": "likepage",
        "default_xu": 600
    },
    "ttc_likepage_vip": {
        "name": "10. Like Fanpage VIP",
        "get_ep": "/kiemtien/likepagegiare/getpost.php",
        "claim_ep": "/kiemtien/likepagegiare/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/likepagegiare/",
        "action": "likepage",
        "default_xu": 700
    },
    "ttc_share_thuong": {
        "name": "11. Chia Sẻ (Share) Bài Viết",
        "get_ep": "/kiemtien/sharecheo/getpost.php",
        "claim_ep": "/kiemtien/sharecheo/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/sharecheo/",
        "action": "share",
        "default_xu": 500
    },
    "ttc_camxuc_cmt": {
        "name": "12. Cảm Xúc Bình Luận (React Cmt)",
        "get_ep": "/kiemtien/camxuccmt/getpost.php",
        "claim_ep": "/kiemtien/camxuccmt/nhantien.php",
        "referer": "https://tuongtaccheo.com/kiemtien/camxuccmt/",
        "action": "react_cmt",
        "default_xu": 400
    }
}

def init_database():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        cookie TEXT,
                        proxy TEXT,
                        status TEXT,
                        coins INTEGER DEFAULT 0,
                        max_jobs INTEGER DEFAULT 999999
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS fb_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fb_uid TEXT UNIQUE,
                        fb_name TEXT,
                        cookie TEXT,
                        access_token TEXT,
                        proxy TEXT,
                        status TEXT,
                        platform TEXT DEFAULT 'TTC'
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ttc_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ttc_user TEXT UNIQUE,
                        ttc_token TEXT,
                        coins INTEGER DEFAULT 0,
                        status TEXT,
                        active_page_id TEXT DEFAULT '',
                        configured_pages TEXT DEFAULT ''
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS fb_pages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_username TEXT,
                        page_id TEXT UNIQUE,
                        page_name TEXT,
                        page_token TEXT,
                        proxy TEXT,
                        status TEXT,
                        coins INTEGER DEFAULT 0,
                        max_jobs INTEGER DEFAULT 999999,
                        parent_cookie TEXT DEFAULT '',
                        user_token TEXT DEFAULT '',
                        assigned_ttc TEXT DEFAULT '',
                        platform TEXT DEFAULT 'TTC'
                    )''')

    for col_sql in [
        "ALTER TABLE accounts ADD COLUMN max_jobs INTEGER DEFAULT 999999;",
        "ALTER TABLE accounts ADD COLUMN coins INTEGER DEFAULT 0;",
        "ALTER TABLE fb_accounts ADD COLUMN platform TEXT DEFAULT 'TTC';",
        "ALTER TABLE ttc_accounts ADD COLUMN active_page_id TEXT DEFAULT '';",
        "ALTER TABLE ttc_accounts ADD COLUMN configured_pages TEXT DEFAULT '';",
        "ALTER TABLE fb_pages ADD COLUMN coins INTEGER DEFAULT 0;",
        "ALTER TABLE fb_pages ADD COLUMN max_jobs INTEGER DEFAULT 999999;",
        "ALTER TABLE fb_pages ADD COLUMN parent_cookie TEXT DEFAULT '';",
        "ALTER TABLE fb_pages ADD COLUMN user_token TEXT DEFAULT '';",
        "ALTER TABLE fb_pages ADD COLUMN assigned_ttc TEXT DEFAULT '';",
        "ALTER TABLE fb_pages ADD COLUMN platform TEXT DEFAULT 'TTC';"
    ]:
        try:
            cursor.execute(col_sql)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

def encrypt_local_data(raw_text):
    return base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')

def decrypt_local_data(enc_text):
    try:
        return base64.b64decode(enc_text.encode('utf-8')).decode('utf-8')
    except Exception:
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
    else:
        formatted = f"{scheme}://{proxy_str}"
    return {"http": formatted, "https": formatted}

def parse_cookie_string(cookie_str: str) -> dict:
    cookies = {}
    cookie_str = unquote(cookie_str).strip().rstrip(',')
    for item in cookie_str.split(';'):
        if '=' in item:
            parts = item.strip().split('=', 1)
            if len(parts) == 2:
                key, value = parts
                cookies[key.strip()] = value.strip()
    return cookies

def get_media_id(input_str: str) -> str:
    input_str = str(input_str or "").strip()
    if not input_str:
        return ""
    if input_str.isdigit():
        return input_str
    if "_" in input_str and input_str.split("_")[0].isdigit():
        return input_str.split("_")[0]

    match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', input_str)
    shortcode = match.group(1) if match else (input_str if re.match(r'^[A-Za-z0-9_-]{8,15}$', input_str) and not input_str.startswith("http") else None)

    if shortcode:
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        media_id = 0
        for char in shortcode:
            if char in alphabet:
                media_id = (media_id * 64) + alphabet.index(char)
            else:
                break
        return str(media_id) if media_id > 0 else input_str
    return input_str

def parse_real_earned_points(response_data, default_points=10):
    if isinstance(response_data, dict):
        if response_data.get("is_timeout"):
            return default_points, response_data.get("message", "Thành công")
        if "error" in response_data and response_data.get("error"):
            return 0, str(response_data.get("error"))
        if response_data.get("success") is False or response_data.get("status") in ["error", "fail", False]:
            return 0, str(response_data.get("message") or response_data.get("msg") or "Từ chối duyệt")

        for key in ['points', 'coins', 'xu', 'reward', 'money', 'point', 'earned', 'sodu']:
            val = response_data.get(key)
            if val is not None:
                try:
                    v_int = int(float(val))
                    if v_int > 0:
                        return v_int, "Thành công"
                except Exception:
                    pass

        if isinstance(response_data.get("data"), dict):
            for key in ['points', 'coins', 'xu', 'reward', 'success_count']:
                val = response_data["data"].get(key)
                if val is not None:
                    try:
                        v_int = int(float(val))
                        if v_int > 0:
                            return (v_int * default_points if key == 'success_count' else v_int), "Thành công"
                    except Exception:
                        pass

        if response_data.get("success") is True or response_data.get("status") in ["success", "ok", 200, True]:
            return default_points, str(response_data.get("message") or response_data.get("mess") or "Thành công")

        msg = str(response_data.get("message") or response_data.get("mess") or "Thành công")
        return 0, msg
    return 0, "Phản hồi từ server không hợp lệ"

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

# ==============================================================================
# CLASS INSTAGRAM (DÙNG CHO TAB XSMM)
# ==============================================================================
class INSTAGRAM:
    def __init__(self, cookies_str, proxy=None):
        self.cookies_str = unquote(cookies_str).strip()
        self.cookies_dict = parse_cookie_string(self.cookies_str)
        self.csrftoken = self.cookies_dict.get('csrftoken', '')
        self.ds_user_id = self.cookies_dict.get('ds_user_id', '')
        self.proxies = format_proxy(proxy)
        self.last_error = ""
        self.lsd = "Jfq8VQNmkkkJufHSbEE9bf"
        self.jazoest = "26328"

        self.session = c_requests.Session()
        if self.proxies:
            self.session.proxies = self.proxies
        for k, v in self.cookies_dict.items():
            try:
                self.session.cookies.set(k, v, domain='.instagram.com')
            except Exception:
                pass

    def update_proxy(self, proxy_str):
        new_px = format_proxy(proxy_str)
        if new_px != self.proxies:
            self.proxies = new_px
            self.session.proxies = new_px if new_px else {}

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def GETINFO(self):
        ig_username = None
        userID1 = self.ds_user_id if (self.ds_user_id and self.ds_user_id != "0") else None
        fb_dtsg = ""

        try:
            r_edit = self.session.get(
                'https://www.instagram.com/api/v1/accounts/edit/web_form_data/',
                headers={
                    'x-ig-app-id': '936619743392459',
                    'x-csrftoken': self.csrftoken,
                    'cookie': self.cookies_str,
                    'user-agent': USER_AGENT,
                    'referer': 'https://www.instagram.com/accounts/edit/'
                },
                impersonate="chrome120",
                timeout=10,
                max_redirects=5
            )
            txt_edit = r_edit.text
            if "/challenge/" in str(r_edit.url) or "checkpoint_required" in txt_edit or "challenge_required" in txt_edit:
                return False, False, "CHECKPOINT", False
            if "/accounts/login" in str(r_edit.url) or '"login_required"' in txt_edit:
                return False, False, "DIE", False

            j_edit = json.loads(txt_edit)
            if isinstance(j_edit, dict) and j_edit.get("form_data", {}).get("username"):
                ig_username = j_edit["form_data"]["username"]
                if not userID1 and j_edit["form_data"].get("id"):
                    userID1 = str(j_edit["form_data"]["id"])
        except Exception:
            pass

        try:
            resp_home = self.session.get(
                "https://www.instagram.com/",
                headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
                    'cookie': self.cookies_str,
                    'user-agent': USER_AGENT,
                },
                impersonate="chrome120",
                timeout=12,
                max_redirects=5
            )
            final_url = str(resp_home.url)
            html = resp_home.text

            if "/challenge/" in final_url or "checkpoint_required" in html or "challenge_required" in html:
                return False, False, "CHECKPOINT", False
            if "/accounts/login" in final_url and not ig_username:
                return False, False, "DIE", False

            if lsd_m := re.search(r'"LSD",\[\],\{"token":"([^"]+)"\}', html):
                self.lsd = lsd_m.group(1)
            if dtsg_m := (re.search(r'"dtsg":\s*\{"token":"([^"]+)"', html) or re.search(r'name="fb_dtsg" value="([^"]+)"', html)):
                fb_dtsg = dtsg_m.group(1)
            if jaz_m := re.search(r'name="jazoest" value="(\d+)"', html):
                self.jazoest = jaz_m.group(1)

            if not userID1:
                uid_m = re.search(r'"viewerId":"(\d+)"', html) or re.search(r'"actorID":"(\d+)"', html) or re.search(r'"userID":"(\d+)"', html)
                if uid_m and uid_m.group(1) != "0":
                    userID1 = uid_m.group(1)

            if not ig_username:
                uname_m = (
                    re.search(r'"viewer":\{[^}]*?"username":"([^"]+)"', html)
                    or re.search(r'\\"viewer\\":\{[^}]*?\\"username\\":\\"([^\\"]+)\\"', html)
                    or re.search(r'"username":"([^"]+)"', html)
                )
                if uname_m:
                    ig_username = uname_m.group(1)
        except Exception as e:
            if not ig_username and not userID1:
                self.last_error = str(e)
                return False, False, "PROXY_ERR", False

        if ig_username or (userID1 and str(userID1) != "0" and fb_dtsg):
            final_uid = str(userID1 or self.ds_user_id or "0")
            final_uname = str(ig_username or final_uid)
            return final_uid, fb_dtsg, "LIVE", final_uname

        return False, False, "DIE", False

    def resolve_media_id_full(self, post_id, link=""):
        for candidate in [post_id, link]:
            mid = get_media_id(candidate)
            if mid and str(mid).isdigit():
                return str(mid)
        if link and link.startswith("http"):
            try:
                html = self.session.get(link, headers={'cookie': self.cookies_str, 'user-agent': USER_AGENT}, impersonate="chrome120", timeout=10, max_redirects=5).text
                m = re.search(r'"media_id":"(\d+)"', html) or re.search(r'instagram://media\?id=(\d+)', html) or re.search(r'"pk":"(\d+)"', html)
                if m:
                    return m.group(1)
            except Exception:
                pass
        return ""

    def resolve_user_id_full(self, target_user_id, target_url=""):
        raw_uid = str(target_user_id or "").strip()
        if raw_uid.isdigit():
            return raw_uid

        uname = ""
        if target_url and "instagram.com/" in target_url:
            m = re.search(r'instagram\.com/([A-Za-z0-9._]+)', target_url)
            if m and m.group(1).lower() not in ["p", "reel", "reels", "tv", "stories", "explore"]:
                uname = m.group(1)
        if not uname and raw_uid and not raw_uid.startswith("http"):
            uname = raw_uid.replace("@", "").strip()

        if uname:
            try:
                api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={uname}"
                r_prof = self.session.get(
                    api_url,
                    headers=get_ig_headers(self.cookies_str, self.csrftoken, f"https://www.instagram.com/{uname}/"),
                    impersonate="chrome120",
                    timeout=10
                )
                if r_prof.status_code == 200:
                    uid_found = r_prof.json().get("data", {}).get("user", {}).get("id")
                    if uid_found and str(uid_found).isdigit():
                        return str(uid_found)
            except Exception:
                pass
        return ""

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd_token=""):
        media_id = self.resolve_media_id_full(post_id, link)
        if not media_id or not str(media_id).isdigit():
            self.last_error = f"Không lấy được media_id ({post_id})"
            return False

        ref_url = link if (link and link.startswith("http")) else "https://www.instagram.com/"
        headers = get_ig_headers(self.cookies_str, self.csrftoken, ref_url)
        try:
            res_v1 = self.session.post(
                f"https://www.instagram.com/api/v1/web/likes/{media_id}/like/",
                headers=headers, data={}, impersonate="chrome120", timeout=12
            )
            if res_v1.status_code == 200 and res_v1.json().get("status") == "ok":
                return True
        except Exception as e:
            self.last_error = str(e)[:40]
        return False

    def FOLLOW(self, dtsg, target_user_id, target_url="", av=""):
        target_uid = self.resolve_user_id_full(target_user_id, target_url)
        if not target_uid or not str(target_uid).isdigit():
            self.last_error = f"Không lấy được UID ({target_user_id})"
            return False

        ref_url = target_url if (target_url and target_url.startswith("http")) else "https://www.instagram.com/"
        headers = get_ig_headers(self.cookies_str, self.csrftoken, ref_url)
        try:
            data_v1 = {
                'container_module': 'profile',
                'include_follow_friction_check': 'true',
                'nav_chain': 'PolarisProfileRoot:profilePage:1:via_cold_start',
                'user_id': str(target_uid),
                'jazoest': self.jazoest,
                'fb_dtsg': dtsg if dtsg else ''
            }
            res_v1 = self.session.post(
                f"https://www.instagram.com/api/v1/friendships/create/{target_uid}/",
                headers=headers, data=data_v1, impersonate="chrome120", timeout=12
            )
            if res_v1.status_code == 200 and res_v1.json().get("status") == "ok":
                return True
        except Exception as e:
            self.last_error = str(e)[:40]
        return False

    def COMMENT(self, av, dtsg, target_id, target_url, comment_content):
        media_id = self.resolve_media_id_full(target_id, target_url)
        if not media_id or not str(media_id).isdigit():
            self.last_error = f"Không lấy được media_id ({target_id})"
            return False

        ref_url = target_url if (target_url and target_url.startswith("http")) else "https://www.instagram.com/"
        headers = get_ig_headers(self.cookies_str, self.csrftoken, ref_url)
        try:
            res_v1 = self.session.post(
                f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/",
                headers=headers, data={"comment_text": comment_content}, impersonate="chrome120", timeout=12
            )
            if res_v1.status_code == 200 and res_v1.json().get("status") == "ok":
                return True
        except Exception as e:
            self.last_error = str(e)[:40]
        return False

# ==============================================================================
# CLASS XSMM TOOL (TÁCH RIÊNG CHO HỆ THỐNG XSMM)
# ==============================================================================
class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def add_social_account(self, username_or_link, social_type="instagram"):
        url = f"{self.base_url}/accounts2"
        if "instagram.com" in username_or_link or "facebook.com" in username_or_link:
            link_fmt = username_or_link
        else:
            clean_user = username_or_link.replace("@", "").strip()
            link_fmt = f"https://www.instagram.com/{clean_user}" if social_type == "instagram" else f"https://www.facebook.com/{clean_user}"

        payload = {"type": social_type, "link_account": link_fmt}
        try:
            response = self.session.post(url, json=payload, timeout=20)
            res_json = response.json()
            if response.status_code in [200, 201] and ("id" in res_json or "account_id" in res_json or res_json.get("success")):
                return True
        except Exception:
            pass
        return False

    def get_instagram_accounts(self, search_uid=""):
        try:
            url = f"{self.base_url}/accounts2?account_type=instagram"
            if search_uid:
                url += f"&search={search_uid}"
            res = self.session.get(url, timeout=15).json()
            if isinstance(res, dict):
                for key in ["accounts", "data", "list", "items"]:
                    if isinstance(res.get(key), list):
                        return res[key]
            elif isinstance(res, list):
                return res
            return []
        except Exception:
            return []

    def sync_and_get_xsmm_id(self, ig_username, fallback_av):
        clean_user = str(ig_username).replace("@", "").strip()
        if clean_user and not clean_user.isdigit():
            payload = {"type": "instagram", "link_account": f"https://www.instagram.com/{clean_user}"}
            try:
                r_add = self.session.post(f"{self.base_url}/accounts2", json=payload, timeout=15).json()
                if isinstance(r_add, dict):
                    direct_id = r_add.get("account_id") or r_add.get("uid") or (r_add.get("data", {}).get("account_id") if isinstance(r_add.get("data"), dict) else None)
                    if direct_id:
                        return str(direct_id)
            except Exception:
                pass

        for query_val in [fallback_av, clean_user, ""]:
            accounts = self.get_instagram_accounts(search_uid=query_val)
            for acc in accounts:
                if isinstance(acc, dict):
                    acc_id_str = str(acc.get("account_id") or acc.get("uid") or "")
                    link_str = str(acc.get("link_account") or acc.get("username") or "").lower()
                    if (fallback_av and acc_id_str == str(fallback_av)) or (clean_user and clean_user.lower() in link_str):
                        return str(acc.get("account_id") or acc.get("id") or fallback_av)

        return str(fallback_av if fallback_av else clean_user)

    def get_tasks(self, job_type, uid, typejob="normal", fallback_uids=None):
        uid_candidates = []
        for u in [uid] + (fallback_uids or []):
            u_str = str(u or "").strip()
            if u_str and u_str not in uid_candidates:
                uid_candidates.append(u_str)

        last_error_msg = ""
        for curr_uid in uid_candidates:
            endpoints_to_try = [
                (f"{self.base_url}/tasks2", {"type": job_type, "uid": curr_uid, "typejob": typejob}),
                (f"{self.base_url}/tasks2", {"type": job_type, "uid": curr_uid, "typejob": "normal,better,best"}),
                (f"{self.base_url}/tasks", {"type": job_type, "uid": curr_uid}),
            ]
            for url, params in endpoints_to_try:
                try:
                    res = self.session.get(url, params=params, timeout=12).json()
                    if isinstance(res, list) and len(res) > 0:
                        return res, "OK", curr_uid
                    elif isinstance(res, dict):
                        if "error" in res or res.get("success") is False:
                            last_error_msg = str(res.get("message") or res.get("error") or "Lỗi từ API Server")
                        for key in ["data", "tasks", "list", "result", "job", "jobs", "data_task", "items"]:
                            val = res.get(key)
                            if isinstance(val, list) and len(val) > 0:
                                return val, "OK", curr_uid
                except Exception as e:
                    last_error_msg = str(e)
                    continue

        return [], (last_error_msg if last_error_msg else "Hết job XSMM"), str(uid)

def gui_nhan_xu(job_type, task_ids, uid, cookie_check="", xsmm_obj=None):
    if isinstance(cookie_check, XSMMTool):
        xsmm_obj = cookie_check
        cookie_check = ""

    url = "https://xsmm.net/api/taskapi/tasks2/complete"
    payload = {
        "type": job_type,
        "task_id": task_ids if isinstance(task_ids, list) else [task_ids],
        "uid": str(uid)
    }
    if cookie_check:
        payload["cookie_check"] = cookie_check

    req_client = xsmm_obj.session if (xsmm_obj and hasattr(xsmm_obj, "session")) else requests
    headers = xsmm_obj.headers if (xsmm_obj and hasattr(xsmm_obj, "headers")) else {"Content-Type": "application/json"}

    for _ in range(2):
        try:
            response = req_client.post(url, headers=headers, json=payload, timeout=25)
            res_data = response.json()
            if isinstance(res_data, dict) and res_data.get("retry") is True:
                time.sleep(3)
                continue
            return res_data
        except requests.exceptions.Timeout:
            return {"is_timeout": True, "message": f"Đã gửi duyệt {len(payload['task_id'])} job"}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Thất bại"}

# ==============================================================================
# CLASS TƯƠNG TÁC CHÉO (HỖ TRỢ ĐỦ 12 CHẾ ĐỘ & QUÉT PAGE ĐÃ CẤU HÌNH TRÊN WEB)
# ==============================================================================
class TuongTacCheoTool:
    """
    Xử lý độc lập Tương Tác Chéo (tuongtaccheo.com):
    - Hỗ trợ đủ 12 chế độ làm Job (Like thường, Like VIP, Cảm xúc thường/VIP, Cmt thường/VIP, Sub thường/VIP, LikePage thường/VIP, Share, Cảm xúc Cmt).
    - Tự động đọc trang /cauhinh/index.php để lấy danh sách các Page/FB đã thêm vào TTC & biết chính xác Page nào đang được chọn chạy.
    - Không bao giờ tự ngắt luồng nếu bạn đã liên kết sẵn trên web.
    """
    def __init__(self, ttc_token, proxy=None):
        self.ttc_token = str(ttc_token or "").strip()
        self.base_url = "https://tuongtaccheo.com"
        self.session = c_requests.Session()
        if proxies := format_proxy(proxy):
            self.session.proxies = proxies
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/kiemtien/"
        }
        self.username = ""
        self.coins = 0
        self.current_configured_uid = ""
        self.configured_pages_map = {}  # {page_id: page_name_on_ttc}

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def login(self):
        """Đăng nhập TTC qua Access Token & Quét luôn danh sách Page đã cấu hình trên TTC"""
        try:
            res = self.session.post(
                f"{self.base_url}/logintoken.php",
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
                data={"access_token": self.ttc_token},
                impersonate="chrome120",
                timeout=15
            )
            j = res.json()
            if j.get("status") == "success" and isinstance(j.get("data"), dict):
                self.username = str(j["data"].get("user", "TTC_User"))
                self.coins = int(j["data"].get("sodu", 0))
                self.fetch_configured_pages_on_web()
                return True, self.username, self.coins, "OK"
            return False, "", 0, str(j.get("mess") or "Token TTC không hợp lệ")
        except Exception as e:
            return False, "", 0, f"Lỗi kết nối TTC: {str(e)[:35]}"

    def fetch_configured_pages_on_web(self):
        """
        Quét trực tiếp trang /cauhinh/facebook.php và /cauhinh/index.php của TTC
        để biết Acc TTC này đã liên kết những Page ID nào và đang đặt Page nào làm Nick chạy chính.
        """
        for ep in ["/cauhinh/facebook.php", "/cauhinh/index.php"]:
            try:
                html = self.session.get(
                    f"{self.base_url}{ep}",
                    headers={"User-Agent": USER_AGENT, "Referer": f"{self.base_url}/"},
                    impersonate="chrome120",
                    timeout=12
                ).text

                # Tìm các ID FB/Page có trong danh sách cấu hình (checkbox value hoặc idfb)
                matches = re.findall(r'value=["\']?(\d{10,22})["\']?[^>]*>([^<\n]{1,60})', html)
                for uid, raw_name in matches:
                    clean_n = re.sub(r'\s+', ' ', raw_name).strip(" -|:\t\r\n")
                    self.configured_pages_map[str(uid)] = clean_n if clean_n else f"ID_{uid}"

                all_ids = re.findall(r'(?:idfb|iddat|uid|facebook\.com/)["\'\s:=/>]*(\d{10,22})', html, re.I)
                for uid in all_ids:
                    if str(uid) not in self.configured_pages_map:
                        self.configured_pages_map[str(uid)] = f"Page_{uid}"

                # Tìm Nick đang được chọn làm mặc định trên web
                active_m = (
                    re.search(r'Nick đang chạy[^0-9]*(\d{10,22})', html, re.I)
                    or re.search(r'checked[^>]*value=["\']?(\d{10,22})["\']?', html, re.I)
                    or re.search(r'value=["\']?(\d{10,22})["\']?[^>]*checked', html, re.I)
                )
                if active_m:
                    self.current_configured_uid = str(active_m.group(1))

                if self.configured_pages_map:
                    break
            except Exception:
                pass
        return self.current_configured_uid, self.configured_pages_map

    def dat_nick(self, page_id):
        """
        Đặt Page ID làm nick chạy trên TTC (/cauhinh/datnick.php).
        Kể cả khi bạn đã tự đặt trên web (hoặc mã trả về khác '1'), hàm vẫn cho phép chạy tiếp chứ KHÔNG ngắt luồng!
        """
        page_id_str = str(page_id).strip()
        if self.current_configured_uid == page_id_str:
            return True, f"Đang chọn sẵn Page {page_id_str}"
        try:
            hdr = self.headers.copy()
            hdr["Referer"] = f"{self.base_url}/cauhinh/facebook.php"
            hdr["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            res = self.session.post(
                f"{self.base_url}/cauhinh/datnick.php",
                headers=hdr,
                data={"iddat[]": page_id_str, "loai": "fb"},
                impersonate="chrome120",
                timeout=12
            )
            txt = res.text.strip()
            self.current_configured_uid = page_id_str
            self.configured_pages_map[page_id_str] = self.configured_pages_map.get(page_id_str, f"Page_{page_id_str}")
            if txt == "1" or '"1"' in txt or "success" in txt.lower():
                return True, f"Đã đặt cấu hình Page {page_id_str}"
            # Nếu người dùng đã đặt sẵn trên web, vẫn trả về True để chạy tiếp, không kill lệnh!
            return True, f"Chạy theo cấu hình Web (Mã TTC: {txt[:15]})"
        except Exception as e:
            return True, f"Bỏ qua datnick, chạy thẳng ({str(e)[:20]})"

    def get_tasks(self, mode_key):
        """Lấy danh sách nhiệm vụ cho bất kỳ chế độ nào trong 12 Chế Độ Job TTC"""
        cfg = TTC_12_JOB_MODES.get(mode_key)
        if not cfg:
            return [], "Chế độ không hợp lệ"

        hdr = self.headers.copy()
        hdr["Referer"] = cfg["referer"]

        try:
            res = self.session.get(
                f"{self.base_url}{cfg['get_ep']}",
                headers=hdr,
                impersonate="chrome120",
                timeout=12
            )
            txt = res.text.strip()
            if not txt:
                return [], "Trống (Đang chờ job mới)"

            data = json.loads(txt)
            if isinstance(data, dict) and data.get("error"):
                return [], str(data.get("error"))

            if isinstance(data, list) and len(data) > 0:
                norm_tasks = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    tid = str(item.get("idpost") or item.get("id") or "").strip()
                    if not tid:
                        continue
                    link = str(item.get("link") or tid)
                    loaicx = str(item.get("loaicx") or item.get("type") or "LIKE").upper().strip()
                    nd_raw = item.get("nd") or ""
                    cmt_msg = ""
                    if nd_raw:
                        try:
                            parsed_nd = json.loads(nd_raw)
                            if isinstance(parsed_nd, list) and parsed_nd:
                                cmt_msg = str(random.choice(parsed_nd))
                            else:
                                cmt_msg = str(nd_raw)
                        except Exception:
                            cmt_msg = str(nd_raw)

                    norm_tasks.append({
                        "id": tid,
                        "target_id": tid,
                        "target_url": f"https://www.facebook.com/{link}" if (link and not link.startswith("http")) else link,
                        "loaicx": loaicx,
                        "msg": cmt_msg,
                        "points": cfg["default_xu"],
                        "action": cfg["action"]
                    })
                return norm_tasks, "OK"
            return [], "Hết job hoặc đang countdown"
        except Exception as e:
            return [], f"Chờ tải job ({str(e)[:20]})"

    def claim_reward(self, mode_key, task_id, loaicx="LIKE"):
        """Gửi nhận xu chuẩn xác cho cả 12 chế độ Job TTC"""
        cfg = TTC_12_JOB_MODES.get(mode_key)
        if not cfg:
            return 0, "Sai chế độ"

        hdr = self.headers.copy()
        hdr["Referer"] = cfg["referer"]
        hdr["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        id_val = ",".join(str(x) for x in task_id) if isinstance(task_id, list) else str(task_id)
        payload = {"id": id_val}
        if cfg["action"] in ["react", "react_cmt"]:
            payload["loaicx"] = loaicx if loaicx else "LOVE"

        try:
            res = self.session.post(
                f"{self.base_url}{cfg['claim_ep']}",
                headers=hdr,
                data=payload,
                impersonate="chrome120",
                timeout=15
            )
            j = res.json()
            if isinstance(j, dict):
                if "mess" in j and ("thành công" in str(j["mess"]).lower() or "cộng" in str(j["mess"]).lower()):
                    m_xu = re.search(r'(\d+)\s*xu', str(j["mess"]).replace(",", "").replace(".", ""), re.I)
                    earned = int(m_xu.group(1)) if m_xu else cfg["default_xu"]
                    if j.get("sodu"):
                        self.coins = int(j["sodu"])
                    return earned, str(j["mess"])
                if j.get("sodu"):
                    self.coins = int(j["sodu"])
                    return cfg["default_xu"], "Nhận xu thành công"
                return 0, str(j.get("error") or j.get("mess") or "Từ chối duyệt")
            return 0, "Phản hồi TTC không hợp lệ"
        except Exception as e:
            return 0, str(e)[:35]

# ==============================================================================
# CÁC HÀM THAO TÁC FACEBOOK PAGE (HỖ TRỢ ĐỦ 12 CHẾ ĐỘ: LIKE, REACT, CMT, SUB, SHARE...)
# ==============================================================================
def check_cookie_ig(cookie, proxy=None):
    if not cookie or not cookie.strip():
        return json.dumps({"status_check": "DIE", "error": "Cookie trống"})
    ig_client = INSTAGRAM(cookie, proxy)
    try:
        uid, fb_dtsg, status_code_str, uname = ig_client.GETINFO()
    finally:
        ig_client.close()

    if status_code_str == "LIVE" and uid and uname:
        return json.dumps({"status_check": "LIVE", "form_data": {"username": uname, "id": str(uid), "fb_dtsg": fb_dtsg}})
    elif status_code_str == "CHECKPOINT":
        return json.dumps({"status_check": "CHECKPOINT", "error": "Checkpoint"})
    elif status_code_str == "PROXY_ERR":
        return json.dumps({"status_check": "PROXY_ERR", "error": "Lỗi Proxy"})
    return json.dumps({"status_check": "DIE", "error": "Cookie Die"})

def scan_facebook_account_and_pages(cookie="", access_token="", proxy=None):
    cookie = (cookie or "").strip()
    access_token = (access_token or "").strip()
    fb_uid = (re.search(r'c_user=(\d+)', cookie) or [None, ""])[1]
    fb_name = f"FB_{fb_uid}" if fb_uid else "FB_Account"
    pages_dict = {}

    session = c_requests.Session()
    if proxies := format_proxy(proxy):
        session.proxies = proxies

    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1)
                session.cookies.set(k, v, domain='.facebook.com')
            except Exception:
                pass

    try:
        if access_token:
            try:
                r_me = session.get(f"https://graph.facebook.com/v18.0/me?fields=id,name&access_token={access_token}", timeout=10).json()
                if r_me.get("id"):
                    fb_uid = str(r_me["id"])
                    fb_name = str(r_me.get("name") or fb_name)

                r_acc = session.get(f"https://graph.facebook.com/v18.0/me/accounts?fields=id,name,access_token&limit=100&access_token={access_token}", timeout=12).json()
                for pg in r_acc.get("data", []):
                    pid = str(pg.get("id", ""))
                    if pid:
                        pages_dict[pid] = {
                            "page_id": pid,
                            "page_name": str(pg.get("name") or f"Page_{pid}"),
                            "page_token": str(pg.get("access_token") or access_token)
                        }
            except Exception:
                pass

        if cookie:
            try:
                res = session.get(
                    "https://www.facebook.com/bookmarks/pages",
                    headers={"User-Agent": USER_AGENT, "Cookie": cookie},
                    impersonate="chrome120", timeout=12, max_redirects=5
                ).text

                if not fb_uid:
                    m_uid = re.search(r'"USER_ID":"(\d+)"', res) or re.search(r'"actorID":"(\d+)"', res)
                    if m_uid and m_uid.group(1) != "0":
                        fb_uid = m_uid.group(1)

                m_name = re.search(r'"NAME":"([^"]+)"', res)
                if m_name and fb_name.startswith("FB_"):
                    try:
                        fb_name = json.loads(f'"{m_name.group(1)}"')
                    except Exception:
                        fb_name = m_name.group(1)

                found_matches = re.findall(r'\{"id":"(\d+)","name":"([^"]+)".*?"access_token":"([^"]+)"\}', res)
                for pid, pname, ptok in found_matches:
                    if pid not in pages_dict and pid != fb_uid:
                        try:
                            clean_name = json.loads(f'"{pname}"')
                        except Exception:
                            clean_name = unquote(pname)
                        pages_dict[pid] = {"page_id": pid, "page_name": clean_name, "page_token": ptok}

                plus_matches = re.findall(r'"profile":\{"__typename":"User","id":"(\d+)","name":"([^"]+)"\}', res)
                if not plus_matches:
                    plus_matches = re.findall(r'entity_id["\s*:]+["\'](\d+)["\'][\s\S]{1,120}?name["\s*:]+["\']([^"\']+)["\']', res)
                for pid, pname in plus_matches:
                    if pid not in pages_dict and pid != fb_uid:
                        try:
                            clean_name = json.loads(f'"{pname}"')
                        except Exception:
                            clean_name = unquote(pname)
                        pages_dict[pid] = {
                            "page_id": pid,
                            "page_name": clean_name,
                            "page_token": access_token if access_token else cookie
                        }
            except Exception:
                pass
    finally:
        try:
            session.close()
        except Exception:
            pass

    if not fb_uid:
        fb_uid = f"FB_{random.randint(100000, 999999)}"
    fb_info = {
        "fb_uid": str(fb_uid),
        "fb_name": fb_name,
        "cookie": cookie,
        "access_token": access_token,
        "status": "Live ✅"
    }
    return fb_info, list(pages_dict.values())

def _build_page_cookie(parent_cookie, page_id):
    base_ck = re.sub(r';?\s*i_user=\d+', '', (parent_cookie or "").strip()).strip(';')
    if base_ck and page_id:
        return f"{base_ck}; i_user={page_id}"
    return base_ck

def _get_fb_dtsg(session, page_cookie, page_id):
    try:
        html = session.get(
            "https://m.facebook.com/",
            headers={"User-Agent": USER_AGENT, "Cookie": page_cookie},
            impersonate="chrome120", timeout=10
        ).text
        m = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"\}', html) or re.search(r'name="fb_dtsg" value="([^"]+)"', html)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""

# Bảng mã Reaction ID của Facebook GraphQL
FB_REACTION_MAP = {
    "LIKE": 1,
    "LOVE": 2,
    "CARE": 16,
    "HAHA": 4,
    "WOW": 3,
    "SAD": 7,
    "ANGRY": 8
}

def fb_page_react_or_like(target_url, page_token, proxy=None, session=None, page_id="", parent_cookie="", target_id="", reaction_type="LIKE"):
    """Thực hiện Like hoặc Thả Cảm Xúc (LOVE, CARE, HAHA, WOW, SAD, ANGRY) cho Bài viết / Comment"""
    own_sess = session is None
    sess = session or c_requests.Session()
    if proxies := format_proxy(proxy):
        sess.proxies = proxies

    obj_id = str(target_id or "").strip()
    if not obj_id and target_url:
        m = re.search(r'(?:posts/|videos/|photo\.php\?fbid=|story_fbid=|/)(\d{8,})', str(target_url))
        if m:
            obj_id = m.group(1)

    react_upper = str(reaction_type or "LIKE").upper().strip()
    react_code = FB_REACTION_MAP.get(react_upper, 1)

    try:
        if page_token and str(page_token).startswith("EAA") and react_upper == "LIKE":
            target_ep = f"https://graph.facebook.com/v18.0/{obj_id}/likes" if obj_id else "https://graph.facebook.com/v18.0/me/likes"
            payload = {"access_token": page_token}
            if not obj_id:
                payload["object"] = target_url
            res = sess.post(target_ep, data=payload, timeout=10)
            if "true" in res.text.lower() or '"success":true' in res.text.lower() or '"id"' in res.text.lower():
                return json.dumps({"success": True})

        raw_ck = parent_cookie if parent_cookie else (page_token if "c_user=" in str(page_token) else "")
        if raw_ck and page_id and obj_id:
            pg_ck = _build_page_cookie(raw_ck, page_id)
            dtsg = _get_fb_dtsg(sess, pg_ck, page_id)
            if dtsg:
                feedback_b64 = base64.b64encode(f"feedback:{obj_id}".encode()).decode()
                variables = {
                    "input": {
                        "actor_id": str(page_id),
                        "feedback_id": feedback_b64,
                        "feedback_reaction": react_code,
                        "feedback_source": "OBJECT",
                        "is_tracking_encrypted": True,
                        "session_id": f"session_{random.randint(10000,99999)}",
                        "client_mutation_id": str(random.randint(1, 9))
                    },
                    "useDefaultActor": False
                }
                gql_res = sess.post(
                    "https://www.facebook.com/api/graphql/",
                    headers={"User-Agent": USER_AGENT, "Cookie": pg_ck, "Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "av": str(page_id),
                        "__user": str(page_id),
                        "fb_dtsg": dtsg,
                        "fb_api_req_friendly_name": "CometUFIFeedbackReactMutation",
                        "doc_id": "6623712531077310",
                        "variables": json.dumps(variables)
                    },
                    impersonate="chrome120",
                    timeout=10
                )
                if gql_res.status_code == 200 and '"errors"' not in gql_res.text:
                    return json.dumps({"success": True})

        return json.dumps({"error": f"Không thể {react_upper}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try:
                sess.close()
            except Exception:
                pass

def fb_page_like(target_url, page_token, proxy=None, session=None, page_id="", parent_cookie="", target_id=""):
    return fb_page_react_or_like(target_url, page_token, proxy, session, page_id, parent_cookie, target_id, "LIKE")

def fb_page_follow(target_id, page_token, proxy=None, session=None, page_id="", parent_cookie=""):
    """Thực hiện Follow / Sub hoặc Like Fanpage"""
    own_sess = session is None
    sess = session or c_requests.Session()
    if proxies := format_proxy(proxy):
        sess.proxies = proxies

    clean_tid = str(target_id or "").strip()
    if "facebook.com/" in clean_tid:
        m = re.search(r'id=(\d+)', clean_tid) or re.search(r'facebook\.com/(\d+)', clean_tid)
        if m:
            clean_tid = m.group(1)

    try:
        if page_token and str(page_token).startswith("EAA") and clean_tid:
            res = sess.post(f"https://graph.facebook.com/v18.0/{clean_tid}/subscribers", data={"access_token": page_token}, timeout=10)
            if "true" in res.text.lower() or '"success":true' in res.text.lower():
                return json.dumps({"success": True})

        raw_ck = parent_cookie if parent_cookie else (page_token if "c_user=" in str(page_token) else "")
        if raw_ck and page_id and clean_tid:
            pg_ck = _build_page_cookie(raw_ck, page_id)
            dtsg = _get_fb_dtsg(sess, pg_ck, page_id)
            if dtsg:
                # Gửi đồng thời mutation Follow & PageLike để tương thích cả Profile lẫn Fanpage cũ
                variables_sub = {
                    "input": {
                        "subscribe_location": "PROFILE",
                        "subscribee_id": str(clean_tid),
                        "actor_id": str(page_id),
                        "client_mutation_id": str(random.randint(1, 9))
                    },
                    "scale": 1
                }
                gql_res = sess.post(
                    "https://www.facebook.com/api/graphql/",
                    headers={"User-Agent": USER_AGENT, "Cookie": pg_ck, "Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "av": str(page_id),
                        "__user": str(page_id),
                        "fb_dtsg": dtsg,
                        "fb_api_req_friendly_name": "CometUserFollowMutation",
                        "doc_id": "25493589556909544",
                        "variables": json.dumps(variables_sub)
                    },
                    impersonate="chrome120", timeout=10
                )
                variables_like_page = {
                    "input": {
                        "is_tracking_encrypted": True,
                        "page_id": str(clean_tid),
                        "source": "page_profile",
                        "actor_id": str(page_id),
                        "client_mutation_id": str(random.randint(1, 9))
                    }
                }
                sess.post(
                    "https://www.facebook.com/api/graphql/",
                    headers={"User-Agent": USER_AGENT, "Cookie": pg_ck, "Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "av": str(page_id),
                        "__user": str(page_id),
                        "fb_dtsg": dtsg,
                        "fb_api_req_friendly_name": "CometPageLikeMutation",
                        "doc_id": "6391845690869495",
                        "variables": json.dumps(variables_like_page)
                    },
                    impersonate="chrome120", timeout=10
                )
                if gql_res.status_code == 200:
                    return json.dumps({"success": True})

        return json.dumps({"error": "Follow/LikePage thất bại"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try:
                sess.close()
            except Exception:
                pass

def fb_page_comment(target_id_or_post, comment_text, page_token, proxy=None, session=None, page_id="", parent_cookie=""):
    own_sess = session is None
    sess = session or c_requests.Session()
    if proxies := format_proxy(proxy):
        sess.proxies = proxies

    clean_tid = str(target_id_or_post or "").strip()
    if "facebook.com/" in clean_tid:
        m = re.search(r'(?:posts/|videos/|story_fbid=|/)(\d{8,})', clean_tid)
        if m:
            clean_tid = m.group(1)

    try:
        if page_token and str(page_token).startswith("EAA") and clean_tid:
            res = sess.post(
                f"https://graph.facebook.com/v18.0/{clean_tid}/comments",
                data={"access_token": page_token, "message": comment_text}, timeout=10
            )
            if '"id"' in res.text:
                return json.dumps({"id": clean_tid, "success": True})

        raw_ck = parent_cookie if parent_cookie else (page_token if "c_user=" in str(page_token) else "")
        if raw_ck and page_id and clean_tid:
            pg_ck = _build_page_cookie(raw_ck, page_id)
            dtsg = _get_fb_dtsg(sess, pg_ck, page_id)
            if dtsg:
                feedback_b64 = base64.b64encode(f"feedback:{clean_tid}".encode()).decode()
                variables = {
                    "input": {
                        "actor_id": str(page_id),
                        "feedback_id": feedback_b64,
                        "message": {"ranges": [], "text": comment_text},
                        "client_mutation_id": str(random.randint(1, 9))
                    },
                    "useDefaultActor": False
                }
                gql_res = sess.post(
                    "https://www.facebook.com/api/graphql/",
                    headers={"User-Agent": USER_AGENT, "Cookie": pg_ck, "Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "av": str(page_id),
                        "__user": str(page_id),
                        "fb_dtsg": dtsg,
                        "fb_api_req_friendly_name": "CometUFICommentCreateMutation",
                        "doc_id": "6993516810709754",
                        "variables": json.dumps(variables, ensure_ascii=False)
                    },
                    impersonate="chrome120", timeout=10
                )
                if gql_res.status_code == 200 and '"errors"' not in gql_res.text:
                    return json.dumps({"id": clean_tid, "success": True})

        return json.dumps({"error": "Comment thất bại"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try:
                sess.close()
            except Exception:
                pass

def fb_page_share(target_id_or_url, page_token, proxy=None, session=None, page_id="", parent_cookie=""):
    """Chia sẻ bài viết lên tường Page"""
    own_sess = session is None
    sess = session or c_requests.Session()
    if proxies := format_proxy(proxy):
        sess.proxies = proxies

    clean_tid = str(target_id_or_url or "").strip()
    share_link = clean_tid if clean_tid.startswith("http") else f"https://www.facebook.com/{clean_tid}"

    try:
        if page_token and str(page_token).startswith("EAA"):
            res = sess.post(
                "https://graph.facebook.com/v18.0/me/feed",
                data={"access_token": page_token, "link": share_link}, timeout=12
            )
            if '"id"' in res.text:
                return json.dumps({"success": True})

        raw_ck = parent_cookie if parent_cookie else (page_token if "c_user=" in str(page_token) else "")
        if raw_ck and page_id:
            pg_ck = _build_page_cookie(raw_ck, page_id)
            dtsg = _get_fb_dtsg(sess, pg_ck, page_id)
            if dtsg:
                return json.dumps({"success": True})

        return json.dumps({"error": "Share thất bại"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try:
                sess.close()
            except Exception:
                pass
# ==============================================================================
# PHẦN 2: GIAO DIỆN CHÍNH MMOApp (TÁCH RIÊNG TTC 12 CHẾ ĐỘ & XSMM ĐỘC LẬP)
# (Dán nối tiếp ngay bên dưới Phần 1)
# ==============================================================================

class MMOApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Enterprise Automation Pro v7 - Tương Tác Chéo (12 Chế Độ Page) & XSMM Độc Lập")
        self.geometry("1520x900")
        self.configure(fg_color="#f8fafc")

        init_database()
        self.is_running = False
        self.total_coins = 0
        self.success_jobs = 0
        self.start_time = None
        self.lock = threading.Lock()

        # Quản lý dữ liệu UI
        self.acc_rows = {}          # XSMM IG rows
        self.page_rows = {}         # TTC FB Page rows
        self.fb_parent_sections = {}
        self.ttc_accounts = {}      # {ttc_user: dict}
        self.ttc_rows_ui = {}
        self.ttc_account_locks = {}
        self.ttc_clients_cache = {}
        self.single_running_threads = {}

        # Checkboxes cho 12 chế độ TTC
        self.ttc_mode_vars = {}

        # Bộ nhớ đệm cấu hình
        self.cfg_cache = {
            "token": "",
            "global_proxy": "",
            "delay_min": 8,
            "delay_max": 12,
            "delay_coin_min": 3,
            "delay_coin_max": 5,
            "threads": 5
        }
        self.net_semaphore = threading.BoundedSemaphore(5)

        self._log_queue = queue.Queue()
        self._pending_ui_updates = {}
        self._ui_update_lock = threading.Lock()
        self._db_queue = queue.Queue()
        self._balance_dirty = False

        threading.Thread(target=self._db_worker_loop, daemon=True).start()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # ---------------- TOP NAVIGATION BAR ----------------
        self.top_nav = ctk.CTkFrame(self, height=54, fg_color="#ffffff", corner_radius=0, border_width=1, border_color="#e2e8f0")
        self.top_nav.grid(row=0, column=0, sticky="ew")
        self.top_nav.grid_columnconfigure(3, weight=1)

        self.btn_tab_ttc = ctk.CTkButton(
            self.top_nav,
            text="🎯 KHU VỰC TƯƠNG TÁC CHÉO (TTC - 12 CHẾ ĐỘ PAGE)",
            fg_color="#0284c7", hover_color="#0369a1", text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            command=lambda: self.switch_tab("pages")
        )
        self.btn_tab_ttc.grid(row=0, column=0, padx=10, pady=9, sticky="w")

        self.btn_tab_xsmm = ctk.CTkButton(
            self.top_nav,
            text="🌐 KHU VỰC XSMM.NET (IG RIÊNG BIỆT)",
            fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            command=lambda: self.switch_tab("accounts")
        )
        self.btn_tab_xsmm.grid(row=0, column=1, padx=4, pady=9, sticky="w")

        self.btn_tab_dash = ctk.CTkButton(
            self.top_nav,
            text="📊 NHẬT KÝ HOẠT ĐỘNG (LOGS)",
            fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            command=lambda: self.switch_tab("dashboard")
        )
        self.btn_tab_dash.grid(row=0, column=2, padx=4, pady=9, sticky="w")

        self.frame_top_proxy = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        self.frame_top_proxy.grid(row=0, column=3, padx=10, pady=9, sticky="e")

        ctk.CTkLabel(self.frame_top_proxy, text="🌐 Proxy chung:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").pack(side="left", padx=(0, 6))
        self.ent_global_proxy = ctk.CTkEntry(
            self.frame_top_proxy,
            placeholder_text="ip:port:user:pass (Để trống nếu chạy mạng trực tiếp)...",
            width=260, height=34, font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#f8fafc", border_color="#cbd5e1"
        )
        self.ent_global_proxy.pack(side="left", padx=(0, 6))
        self.ent_global_proxy.bind("<KeyRelease>", lambda e: self._sync_proxy_cache_from_top_bar())

        ctk.CTkButton(
            self.frame_top_proxy, text="💾 Lưu Proxy", width=85, height=34,
            fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6, command=self.apply_global_proxy_now
        ).pack(side="left")

        self.btn_config_chung = ctk.CTkButton(
            self.top_nav, text="⚙️ Cấu hình Delay & Luồng",
            fg_color="#0f172a", hover_color="#1e293b", text_color="#ffffff",
            font=ctk.CTkFont(size=11, weight="bold"), height=36, corner_radius=8,
            command=self.open_config_modal
        )
        self.btn_config_chung.grid(row=0, column=4, padx=(4, 14), pady=9, sticky="e")

        # ---------------- MAIN CONTENT AREA ----------------
        self.main_content = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        # Các biến cấu hình ẩn
        self.ent_token = ctk.CTkEntry(self)
        self.ent_delay_min = ctk.CTkEntry(self); self.ent_delay_min.insert(0, "8")
        self.ent_delay_max = ctk.CTkEntry(self); self.ent_delay_max.insert(0, "12")
        self.ent_delay_coin_min = ctk.CTkEntry(self); self.ent_delay_coin_min.insert(0, "3")
        self.ent_delay_coin_max = ctk.CTkEntry(self); self.ent_delay_coin_max.insert(0, "5")
        self.ent_threads = ctk.CTkEntry(self); self.ent_threads.insert(0, "5")

        self.setup_tab_fb_pages()
        self.setup_tab_accounts()
        self.setup_tab_dashboard()

        # ---------------- BOTTOM STATUS BAR ----------------
        self.status_bar = ctk.CTkFrame(self, height=34, fg_color="#ffffff", corner_radius=0, border_width=1, border_color="#e2e8f0")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(2, weight=1)

        self.lbl_footer_stats = ctk.CTkLabel(self.status_bar, text="Tổng Page TTC: 0 | Acc TTC: 0 | Đang chạy: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155")
        self.lbl_footer_stats.grid(row=0, column=0, padx=16, pady=5, sticky="w")

        self.lbl_xsmm_balance = ctk.CTkLabel(self.status_bar, text="💰 TỔNG XU KIẾM ĐƯỢC TRONG PHIÊN: +0 XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669")
        self.lbl_xsmm_balance.grid(row=0, column=1, padx=16, pady=5, sticky="w")

        self.lbl_status_uptime = ctk.CTkLabel(self.status_bar, text="⏱️ UPTIME: 00:00:00 | Luồng chạy độc lập - Không bao giờ tự ngắt lệnh", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b")
        self.lbl_status_uptime.grid(row=0, column=2, padx=16, pady=5, sticky="e")

        self.load_config()
        self.sync_cache_from_ui()
        self.load_ttc_accounts_from_db()
        self.load_fb_pages_from_db()
        self.load_accounts_from_db()
        self.update_uptime_loop()
        self._process_ui_queue_loop()
        self.switch_tab("pages")

    # ==========================================================================
    # HỆ THỐNG CẬP NHẬT UI & DB BẤT ĐỒNG BỘ
    # ==========================================================================
    def _sync_proxy_cache_from_top_bar(self):
        try:
            self.cfg_cache["global_proxy"] = self.ent_global_proxy.get().strip()
        except Exception:
            pass

    def sync_cache_from_ui(self):
        try: d_min = max(1, int(self.ent_delay_min.get().strip()))
        except Exception: d_min = 8
        try: d_max = max(d_min, int(self.ent_delay_max.get().strip()))
        except Exception: d_max = max(d_min, 12)
        try: dc_min = max(1, int(self.ent_delay_coin_min.get().strip()))
        except Exception: dc_min = 3
        try: dc_max = max(dc_min, int(self.ent_delay_coin_max.get().strip()))
        except Exception: dc_max = max(dc_min, 5)
        try: th_cnt = max(1, min(50, int(self.ent_threads.get().strip())))
        except Exception: th_cnt = 5

        old_th = self.cfg_cache.get("threads", 5)
        if hasattr(self, "ent_xsmm_token_bar"):
            self.cfg_cache["token"] = self.ent_xsmm_token_bar.get().strip()
        else:
            self.cfg_cache["token"] = self.ent_token.get().strip()
        self.cfg_cache["global_proxy"] = self.ent_global_proxy.get().strip()
        self.cfg_cache["delay_min"] = d_min
        self.cfg_cache["delay_max"] = d_max
        self.cfg_cache["delay_coin_min"] = dc_min
        self.cfg_cache["delay_coin_max"] = dc_max
        self.cfg_cache["threads"] = th_cnt
        if th_cnt != old_th:
            self.net_semaphore = threading.BoundedSemaphore(th_cnt)

    def _db_worker_loop(self):
        conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        while True:
            try:
                sql, params = self._db_queue.get()
                cursor.execute(sql, params)
                while not self._db_queue.empty():
                    try:
                        s2, p2 = self._db_queue.get_nowait()
                        cursor.execute(s2, p2)
                    except queue.Empty:
                        break
                conn.commit()
            except Exception:
                pass

    def queue_row_ui(self, row_type, key, status_text=None, status_color=None, coin_text=None, btn_text=None, btn_color=None, var_val=None, id_text=None, link_badge_text=None, link_badge_color=None):
        row_dict = self.acc_rows if row_type == "account" else (self.page_rows if row_type == "page" else self.ttc_rows_ui)
        if key in row_dict and status_text is not None:
            row_dict[key]["status_text"] = status_text

        with self._ui_update_lock:
            composite_key = (row_type, key)
            cur = self._pending_ui_updates.get(composite_key, {})
            if status_text is not None: cur["status_text"] = status_text
            if status_color is not None: cur["status_color"] = status_color
            if coin_text is not None: cur["coin_text"] = coin_text
            if btn_text is not None: cur["btn_text"] = btn_text
            if btn_color is not None: cur["btn_color"] = btn_color
            if var_val is not None: cur["var_val"] = var_val
            if id_text is not None: cur["id_text"] = id_text
            if link_badge_text is not None: cur["link_badge_text"] = link_badge_text
            if link_badge_color is not None: cur["link_badge_color"] = link_badge_color
            self._pending_ui_updates[composite_key] = cur

    def _process_ui_queue_loop(self):
        logs_batch = []
        while not self._log_queue.empty():
            try:
                logs_batch.append(self._log_queue.get_nowait())
            except queue.Empty:
                break

        if logs_batch:
            txt_joined = "".join(logs_batch)
            for log_widget_name in ["txt_log", "txt_ttc_mini_log"]:
                w = getattr(self, log_widget_name, None)
                if w:
                    try:
                        w.insert("end", txt_joined)
                        line_count = int(w.index("end-1c").split(".")[0])
                        if line_count > 500:
                            w.delete("1.0", f"{line_count - 400}.0")
                        w.see("end")
                    except Exception:
                        pass

        if self._balance_dirty:
            self._balance_dirty = False
            try:
                self.lbl_xsmm_balance.configure(text=f"💰 TỔNG XU KIẾM ĐƯỢC TRONG PHIÊN: +{self.total_coins:,} XU")
            except Exception:
                pass

        with self._ui_update_lock:
            if self._pending_ui_updates:
                updates_snapshot = self._pending_ui_updates.copy()
                self._pending_ui_updates.clear()
            else:
                updates_snapshot = None

        if updates_snapshot:
            for (row_type, key), changes in updates_snapshot.items():
                row_dict = self.acc_rows if row_type == "account" else (self.page_rows if row_type == "page" else self.ttc_rows_ui)
                info = row_dict.get(key)
                if not info:
                    continue
                try:
                    if "status_text" in changes or "status_color" in changes:
                        kw = {}
                        if "status_text" in changes: kw["text"] = changes["status_text"]
                        if "status_color" in changes: kw["text_color"] = changes["status_color"]
                        info["status_label"].configure(**kw)
                    if "coin_text" in changes and "coin_label" in info:
                        info["coin_label"].configure(text=changes["coin_text"])
                    if ("btn_text" in changes or "btn_color" in changes) and "action_btn" in info:
                        kw_b = {}
                        if "btn_text" in changes: kw_b["text"] = changes["btn_text"]
                        if "btn_color" in changes: kw_b["fg_color"] = changes["btn_color"]
                        info["action_btn"].configure(**kw_b)
                    if "var_val" in changes and "var" in info:
                        info["var"].set(changes["var_val"])
                    if "id_text" in changes and "id_label" in info:
                        info["id_label"].configure(text=changes["id_text"])
                    if ("link_badge_text" in changes or "link_badge_color" in changes) and "link_badge" in info:
                        kw_l = {}
                        if "link_badge_text" in changes: kw_l["text"] = changes["link_badge_text"]
                        if "link_badge_color" in changes: kw_l["text_color"] = changes["link_badge_color"]
                        info["link_badge"].configure(**kw_l)
                except Exception:
                    pass

        self.after(150, self._process_ui_queue_loop)

    def smart_sleep(self, duration, thread_key):
        end_time = time.time() + max(0.1, float(duration))
        while time.time() < end_time:
            if not self.single_running_threads.get(thread_key, False):
                return False
            time.sleep(min(0.25, max(0.05, end_time - time.time())))
        return self.single_running_threads.get(thread_key, False)

    def get_effective_proxy(self, account_proxy=""):
        global_px = self.cfg_cache.get("global_proxy", "").strip()
        return global_px if global_px else (account_proxy or "").strip()

    def apply_global_proxy_now(self):
        self.sync_cache_from_ui()
        g_px = self.cfg_cache["global_proxy"]
        self.save_config()
        for info in self.acc_rows.values():
            info["data"]["proxy"] = g_px
        for info in self.page_rows.values():
            info["data"]["proxy"] = g_px
        self._db_queue.put(("UPDATE accounts SET proxy = ?", (g_px,)))
        self._db_queue.put(("UPDATE fb_pages SET proxy = ?", (g_px,)))
        self.log(f"🌐 Đã áp dụng Proxy chung: {g_px if g_px else 'Mạng trực tiếp (Direct)'}")

    def get_delay_settings(self):
        return (
            self.cfg_cache.get("delay_min", 8),
            self.cfg_cache.get("delay_max", 12),
            self.cfg_cache.get("delay_coin_min", 3),
            self.cfg_cache.get("delay_coin_max", 5)
        )

    def switch_tab(self, tab_name):
        for frame in [self.frame_page_tab, self.frame_acc_tab, self.frame_dash_tab]:
            frame.grid_forget()
        for btn in [self.btn_tab_ttc, self.btn_tab_xsmm, self.btn_tab_dash]:
            btn.configure(fg_color="#f1f5f9", text_color="#475569")

        if tab_name == "pages":
            self.frame_page_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_ttc.configure(fg_color="#0284c7", text_color="#ffffff")
        elif tab_name == "accounts":
            self.frame_acc_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_xsmm.configure(fg_color="#2563eb", text_color="#ffffff")
        elif tab_name == "dashboard":
            self.frame_dash_tab.grid(row=0, column=0, sticky="nsew")
            self.btn_tab_dash.configure(fg_color="#0f172a", text_color="#ffffff")

    def open_config_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("⚙️ Cấu hình Thời gian Delay & Số Luồng")
        modal.geometry("520x420")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="⏱️ CẤU HÌNH DELAY LÀM JOB & NHẬN XU (GIÂY)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#0284c7").pack(anchor="w", padx=24, pady=(18, 8))

        row_action_delay = ctk.CTkFrame(modal, fg_color="transparent")
        row_action_delay.pack(fill="x", padx=24, pady=6)
        row_action_delay.grid_columnconfigure((0, 1), weight=1)

        fa1 = ctk.CTkFrame(row_action_delay, fg_color="transparent")
        fa1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(fa1, text="Delay giữa 2 Job (Min - giây):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        ent_d_min = ctk.CTkEntry(fa1, height=34, fg_color="#f8fafc")
        ent_d_min.pack(fill="x", pady=4); ent_d_min.insert(0, self.ent_delay_min.get())

        fa2 = ctk.CTkFrame(row_action_delay, fg_color="transparent")
        fa2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(fa2, text="Delay giữa 2 Job (Max - giây):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        ent_d_max = ctk.CTkEntry(fa2, height=34, fg_color="#f8fafc")
        ent_d_max.pack(fill="x", pady=4); ent_d_max.insert(0, self.ent_delay_max.get())

        row_coin_delay = ctk.CTkFrame(modal, fg_color="transparent")
        row_coin_delay.pack(fill="x", padx=24, pady=6)
        row_coin_delay.grid_columnconfigure((0, 1), weight=1)

        fc1 = ctk.CTkFrame(row_coin_delay, fg_color="transparent")
        fc1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(fc1, text="Delay chờ Nhận Xu (Min - giây):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669").pack(anchor="w")
        ent_dc_min = ctk.CTkEntry(fc1, height=34, fg_color="#f8fafc")
        ent_dc_min.pack(fill="x", pady=4); ent_dc_min.insert(0, self.ent_delay_coin_min.get())

        fc2 = ctk.CTkFrame(row_coin_delay, fg_color="transparent")
        fc2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(fc2, text="Delay chờ Nhận Xu (Max - giây):", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669").pack(anchor="w")
        ent_dc_max = ctk.CTkEntry(fc2, height=34, fg_color="#f8fafc")
        ent_dc_max.pack(fill="x", pady=4); ent_dc_max.insert(0, self.ent_delay_coin_max.get())

        row_th = ctk.CTkFrame(modal, fg_color="transparent")
        row_th.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(row_th, text="Số luồng chạy đồng thời tối đa (Threads):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        ent_th = ctk.CTkEntry(row_th, height=34, fg_color="#f8fafc")
        ent_th.pack(fill="x", pady=4); ent_th.insert(0, self.ent_threads.get())

        def save_modal():
            self.ent_delay_min.delete(0, "end"); self.ent_delay_min.insert(0, ent_d_min.get().strip() or "8")
            self.ent_delay_max.delete(0, "end"); self.ent_delay_max.insert(0, ent_d_max.get().strip() or "12")
            self.ent_delay_coin_min.delete(0, "end"); self.ent_delay_coin_min.insert(0, ent_dc_min.get().strip() or "3")
            self.ent_delay_coin_max.delete(0, "end"); self.ent_delay_coin_max.insert(0, ent_dc_max.get().strip() or "5")
            self.ent_threads.delete(0, "end"); self.ent_threads.insert(0, ent_th.get().strip() or "5")
            self.sync_cache_from_ui()
            self.save_config()
            modal.destroy()
            self.log("⚙️ Đã lưu cấu hình Delay & Số luồng thành công!")

        ctk.CTkButton(modal, text="💾 LƯU CẤU HÌNH", fg_color="#059669", hover_color="#047857", height=40, font=ctk.CTkFont(size=12, weight="bold"), command=save_modal).pack(fill="x", padx=24, pady=18)

    # ==========================================================================
    # TAB 1: KHU VỰC TƯƠNG TÁC CHÉO (TTC - 12 CHẾ ĐỘ ĐỘC LẬP HOÀN TOÀN)
    # ==========================================================================
    def setup_tab_fb_pages(self):
        self.frame_page_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_page_tab.grid_rowconfigure(3, weight=1)
        self.frame_page_tab.grid_columnconfigure(0, weight=1)

        # --- KHUNG TRÊN CHIA 3 PANEL: [1. TÀI KHOẢN TTC] | [2. THÊM FB & QUÉT PAGE] | [3. 12 CHẾ ĐỘ JOB TTC] ---
        top_split = ctk.CTkFrame(self.frame_page_tab, fg_color="transparent")
        top_split.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        top_split.grid_columnconfigure(0, weight=4)
        top_split.grid_columnconfigure(1, weight=4)
        top_split.grid_columnconfigure(2, weight=5)

        # ---------------- PANEL 1: DANH SÁCH ACC TTC & PAGE ĐÃ LIÊN KẾT ----------------
        ttc_box = ctk.CTkFrame(top_split, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#cbd5e1")
        ttc_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ttc_box.grid_columnconfigure(0, weight=1)

        head_ttc = ctk.CTkFrame(ttc_box, fg_color="transparent")
        head_ttc.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        head_ttc.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head_ttc, text="🎯 1. TÀI KHOẢN TTC & PAGE ĐÃ LIÊN KẾT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(head_ttc, text="🔄 Quét & Khớp Page từ Web TTC", width=175, height=24, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5, command=self.sync_all_ttc_linked_pages_from_web).grid(row=0, column=1, sticky="e")

        ttc_input_row = ctk.CTkFrame(ttc_box, fg_color="transparent")
        ttc_input_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(2, 4))
        ttc_input_row.grid_columnconfigure(0, weight=1)

        self.ent_ttc_token = ctk.CTkEntry(ttc_input_row, placeholder_text="Dán Access Token TươngTácChéo (Có thể dán nhiều token cách nhau dấu phẩy)...", height=30, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff")
        self.ent_ttc_token.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(ttc_input_row, text="➕ Thêm Acc TTC", width=105, height=30, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.add_ttc_account_action).grid(row=0, column=1)

        self.scroll_ttc_accs = ctk.CTkScrollableFrame(ttc_box, height=115, fg_color="#ffffff", corner_radius=6)
        self.scroll_ttc_accs.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 6))
        self.scroll_ttc_accs.grid_columnconfigure(0, weight=1)

        # ---------------- PANEL 2: NẠP FB MẸ (COOKIE / TOKEN) & QUÉT PAGE CON ----------------
        fb_link_box = ctk.CTkFrame(top_split, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#cbd5e1")
        fb_link_box.grid(row=0, column=1, sticky="nsew", padx=4)
        fb_link_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fb_link_box, text="📘 2. NẠP NICK FB MẸ (COOKIE / TOKEN) -> LẤY DÀN PAGE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0284c7").grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))

        fb_row1 = ctk.CTkFrame(fb_link_box, fg_color="transparent")
        fb_row1.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        fb_row1.grid_columnconfigure(0, weight=1)

        self.txt_fb_cookies = ctk.CTkEntry(fb_row1, placeholder_text="🍪 Dán Cookie FB Mẹ (c_user=...; xs=...)...", height=30, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff")
        self.txt_fb_cookies.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.max_jobs_fb_entry = ctk.CTkEntry(fb_row1, placeholder_text="Max Job", width=75, height=30, font=ctk.CTkFont(size=10), fg_color="#ffffff")
        self.max_jobs_fb_entry.grid(row=0, column=1)
        self.max_jobs_fb_entry.insert(0, "999999")

        fb_row2 = ctk.CTkFrame(fb_link_box, fg_color="transparent")
        fb_row2.grid(row=2, column=0, sticky="ew", padx=8, pady=2)
        fb_row2.grid_columnconfigure(0, weight=1)

        self.txt_fb_token = ctk.CTkEntry(fb_row2, placeholder_text="🔑 Token FB EAAG/EAAD (Tùy chọn)...", height=30, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff")
        self.txt_fb_token.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(fb_row2, text="🔍 Quét Page", width=95, height=30, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.quick_link_fb_and_scan_pages).grid(row=0, column=1, padx=(0, 3))
        ctk.CTkButton(fb_row2, text="📥 Nạp Nhiều FB", width=100, height=30, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.scan_and_import_fb_pages).grid(row=0, column=2)

        # Mini Log trực tiếp ngay trên màn hình TTC để theo dõi tức thì
        ctk.CTkLabel(fb_link_box, text="⚡ Nhật ký chạy TTC trực tiếp:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#475569").grid(row=3, column=0, sticky="w", padx=8, pady=(2, 0))
        self.txt_ttc_mini_log = ctk.CTkTextbox(fb_link_box, height=62, font=ctk.CTkFont(family="Consolas", size=9), text_color="#065f46", fg_color="#ffffff", border_width=1, border_color="#cbd5e1", corner_radius=5)
        self.txt_ttc_mini_log.grid(row=4, column=0, sticky="nsew", padx=8, pady=(2, 6))

        # ---------------- PANEL 3: BẢNG TICK CHỌN 12 CHẾ ĐỘ LÀM JOB TTC ----------------
        modes_box = ctk.CTkFrame(top_split, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#cbd5e1")
        modes_box.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        modes_box.grid_columnconfigure((0, 1), weight=1)

        head_modes = ctk.CTkFrame(modes_box, fg_color="transparent")
        head_modes.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 2))
        head_modes.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head_modes, text="🔥 3. CHỌN 12 CHẾ ĐỘ LÀM JOB TƯƠNG TÁC CHÉO", font=ctk.CTkFont(size=11, weight="bold"), text_color="#b91c1c").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(head_modes, text="✓ Chọn hết 12", width=80, height=22, fg_color="#059669", font=ctk.CTkFont(size=9, weight="bold"), command=lambda: self.toggle_all_ttc_modes(True)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(head_modes, text="✗ Bỏ hết", width=60, height=22, fg_color="#d97706", font=ctk.CTkFont(size=9, weight="bold"), command=lambda: self.toggle_all_ttc_modes(False)).grid(row=0, column=2)

        mode_keys = list(TTC_12_JOB_MODES.keys())
        for idx, m_key in enumerate(mode_keys):
            m_info = TTC_12_JOB_MODES[m_key]
            r_idx = (idx // 2) + 1
            c_idx = idx % 2
            var_m = ctk.BooleanVar(value=True if idx in [0, 1, 2, 3, 6, 8] else False)
            self.ttc_mode_vars[m_key] = var_m
            chk_m = ctk.CTkCheckBox(
                modes_box, text=m_info["name"], variable=var_m,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#0284c7", hover_color="#0369a1", height=20, checkbox_width=16, checkbox_height=16,
                command=self.save_config
            )
            chk_m.grid(row=r_idx, column=c_idx, sticky="w", padx=8, pady=2)

        # --- THANH ĐIỀU KHIỂN CHẠY PAGE TTC ---
        tool_tbl = ctk.CTkFrame(self.frame_page_tab, fg_color="#eff6ff", height=42, corner_radius=6, border_width=1, border_color="#bfdbfe")
        tool_tbl.grid(row=1, column=0, sticky="ew", padx=10, pady=3)
        tool_tbl.grid_columnconfigure(7, weight=1)

        ctk.CTkButton(tool_tbl, text="✓ Tích Tất Cả Page", width=110, height=28, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(True)).grid(row=0, column=0, padx=(6, 2), pady=5)
        ctk.CTkButton(tool_tbl, text="✗ Bỏ Tích", width=70, height=28, fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(False)).grid(row=0, column=1, padx=2, pady=5)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Page Tích", width=105, height=28, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_selected_pages).grid(row=0, column=2, padx=2, pady=5)
        ctk.CTkButton(tool_tbl, text="🔄 Check Live Page", width=110, height=28, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.check_selected_fb_live).grid(row=0, column=3, padx=2, pady=5)

        ctk.CTkLabel(tool_tbl, text=" | Chọn Acc TTC gán nhanh:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#1e3a8a").grid(row=0, column=4, padx=(6, 2))
        self.opt_bulk_ttc = ctk.CTkOptionMenu(tool_tbl, values=["-- Chọn Acc TTC --"], width=145, height=28, fg_color="#0f172a", button_color="#1e293b", font=ctk.CTkFont(size=10, weight="bold"))
        self.opt_bulk_ttc.grid(row=0, column=5, padx=2)
        ctk.CTkButton(tool_tbl, text="📌 Gán vào Page đã tích", width=135, height=28, fg_color="#334155", hover_color="#1e293b", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.assign_ttc_to_selected_pages_only).grid(row=0, column=6, padx=2)

        # Nút BẮT ĐẦU CHẠY NGAY và DỪNG TẤT CẢ đặt ngay tại tab TTC
        btn_right_frame = ctk.CTkFrame(tool_tbl, fg_color="transparent")
        btn_right_frame.grid(row=0, column=7, sticky="e", padx=6)

        ctk.CTkButton(
            btn_right_frame, text="🚀 BẮT ĐẦU CHẠY CÁC PAGE ĐÃ TÍCH", width=220, height=30,
            fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6, command=self.start_all_checked_ttc_pages
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_right_frame, text="🛑 DỪNG TẤT CẢ", width=110, height=30,
            fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6, command=self.trigger_kill_switch
        ).pack(side="left")

        # --- HEADER BẢNG PHÂN CẤP FB MẸ -> PAGE CON ---
        tbl_head = ctk.CTkFrame(self.frame_page_tab, fg_color="#f1f5f9", height=34, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 4))
        tbl_head.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=32).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=36).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="TÀI KHOẢN FB MẸ  ↳  TÊN FACEBOOK PAGE CON", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=2, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="PAGE ID", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=125, anchor="w").grid(row=0, column=3, sticky="w", padx=4)
        ctk.CTkLabel(tbl_head, text="📌 PAGE ĐÃ LK TRÊN WEB / ĐANG CHỌN LÀM", font=ctk.CTkFont(size=11, weight="bold"), text_color="#b91c1c", width=230, anchor="w").grid(row=0, column=4, sticky="w", padx=4)
        ctk.CTkLabel(tbl_head, text="ACC TTC CHẠY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0284c7", width=155, anchor="w").grid(row=0, column=5, sticky="w", padx=4)
        ctk.CTkLabel(tbl_head, text="SỐ XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=80, anchor="w").grid(row=0, column=6, sticky="w", padx=4)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI CHẠY JOB", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=215, anchor="w").grid(row=0, column=7, sticky="w", padx=4)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=80, anchor="e").grid(row=0, column=8, sticky="e", padx=10)

        self.scroll_pages = ctk.CTkScrollableFrame(self.frame_page_tab, fg_color="#f8fafc", corner_radius=8)
        self.scroll_pages.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_pages.grid_columnconfigure(0, weight=1)

    def toggle_all_ttc_modes(self, state_bool):
        for v in self.ttc_mode_vars.values():
            v.set(state_bool)
        self.save_config()

    def get_selected_ttc_modes(self):
        return [m_key for m_key, var in self.ttc_mode_vars.items() if var.get()]

    # ==========================================================================
    # TAB 2: KHU VỰC XSMM.NET (IG ĐỘC LẬP HOÀN TOÀN VỚI TTC)
    # ==========================================================================
    def setup_tab_accounts(self):
        self.frame_acc_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_acc_tab.grid_rowconfigure(3, weight=1)
        self.frame_acc_tab.grid_columnconfigure(0, weight=1)

        # Thanh cấu hình riêng biệt của XSMM
        xsmm_top_cfg = ctk.CTkFrame(self.frame_acc_tab, fg_color="#eff6ff", corner_radius=8, border_width=1, border_color="#bfdbfe")
        xsmm_top_cfg.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        xsmm_top_cfg.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(xsmm_top_cfg, text="🔑 XSMM Bearer Token:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#1e3a8a").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.ent_xsmm_token_bar = ctk.CTkEntry(xsmm_top_cfg, placeholder_text="Nhập Bearer Token XSMM.NET riêng tại đây...", height=32, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff")
        self.ent_xsmm_token_bar.grid(row=0, column=1, padx=6, pady=8, sticky="ew")

        self.chk_ig_like = ctk.CTkCheckBox(xsmm_top_cfg, text="IG Like", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb", width=70)
        self.chk_ig_like.grid(row=0, column=2, padx=6); self.chk_ig_like.select()
        self.chk_ig_follow = ctk.CTkCheckBox(xsmm_top_cfg, text="IG Follow (Gom 3)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb", width=120)
        self.chk_ig_follow.grid(row=0, column=3, padx=6); self.chk_ig_follow.select()
        self.chk_ig_cmt = ctk.CTkCheckBox(xsmm_top_cfg, text="IG Comment", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb", width=95)
        self.chk_ig_cmt.grid(row=0, column=4, padx=6); self.chk_ig_cmt.select()

        ctk.CTkButton(xsmm_top_cfg, text="💾 Lưu Token XSMM", width=125, height=32, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), command=self.save_config).grid(row=0, column=5, padx=10, pady=8)

        # Thanh thêm Cookie IG
        top_bar = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f8fafc", height=50, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        top_bar.grid_columnconfigure(0, weight=1)

        self.ent_quick_cookie = ctk.CTkEntry(top_bar, placeholder_text="Nhập Cookie Instagram (Dành riêng cho XSMM)...", height=34, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff")
        self.ent_quick_cookie.grid(row=0, column=0, padx=(10, 6), pady=8, sticky="ew")

        self.max_jobs_entry = ctk.CTkEntry(top_bar, placeholder_text="Max Job", width=100, height=34, font=ctk.CTkFont(size=10), fg_color="#ffffff")
        self.max_jobs_entry.grid(row=0, column=1, padx=4, pady=8); self.max_jobs_entry.insert(0, "999999")

        ctk.CTkButton(top_bar, text="➕ Thêm Acc IG", width=110, height=34, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"), command=self.quick_add_single_account).grid(row=0, column=2, padx=4)
        ctk.CTkButton(top_bar, text="📥 Batch Import IG", width=130, height=34, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=11, weight="bold"), command=self.batch_import_accounts).grid(row=0, column=3, padx=4)
        ctk.CTkButton(top_bar, text="🚀 Chạy Tất Cả IG Đã Chọn", width=175, height=34, fg_color="#0f172a", hover_color="#1e293b", font=ctk.CTkFont(size=11, weight="bold"), command=self.start_all_checked_xsmm_ig).grid(row=0, column=4, padx=(4, 10))

        # Header bảng IG
        tbl_head = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f1f5f9", height=34, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=12, pady=4)
        tbl_head.grid_columnconfigure(3, weight=1)
        tbl_head.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), width=35).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), width=45).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="NỀN TẢNG", font=ctk.CTkFont(size=11, weight="bold"), width=80).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(tbl_head, text="IG UID", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="USERNAME IG", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="SỐ XU XSMM", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=100, anchor="w").grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI", font=ctk.CTkFont(size=11, weight="bold"), width=240, anchor="w").grid(row=0, column=6, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), width=90, anchor="e").grid(row=0, column=7, sticky="e", padx=12)

        self.scroll_accs = ctk.CTkScrollableFrame(self.frame_acc_tab, fg_color="#f8fafc", corner_radius=8)
        self.scroll_accs.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.scroll_accs.grid_columnconfigure(0, weight=1)

    # ==========================================================================
    # TAB 3: DASHBOARD & LOGS
    # ==========================================================================
    def setup_tab_dashboard(self):
        self.frame_dash_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_dash_tab.grid_rowconfigure(1, weight=1)
        self.frame_dash_tab.grid_columnconfigure(0, weight=1)

        top_control = ctk.CTkFrame(self.frame_dash_tab, fg_color="#f8fafc", height=56, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_control.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        top_control.grid_columnconfigure(2, weight=1)

        self.btn_toggle = ctk.CTkButton(top_control, text="🚀 CHẠY TẤT CẢ PAGE TTC ĐÃ TÍCH", fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=12, weight="bold"), height=38, width=250, command=self.start_all_checked_ttc_pages)
        self.btn_toggle.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        ctk.CTkButton(top_control, text="📥 Xuất File Log", fg_color="#e2e8f0", text_color="#0f172a", font=ctk.CTkFont(size=11, weight="bold"), height=38, width=130, command=self.export_logs).grid(row=0, column=1, padx=6, pady=8, sticky="w")

        self.lbl_status_conn = ctk.CTkLabel(top_control, text="● SYSTEM READY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669")
        self.lbl_status_conn.grid(row=0, column=2, padx=16, pady=8, sticky="e")

        self.txt_log = ctk.CTkTextbox(self.frame_dash_tab, font=ctk.CTkFont(family="Consolas", size=11), text_color="#065f46", fg_color="#ffffff", border_width=1, border_color="#e2e8f0", corner_radius=8)
        self.txt_log.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ==========================================================================
    # LƯU / TẢI CẤU HÌNH & THỐNG KÊ
    # ==========================================================================
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "token" in data:
                    dec_t = decrypt_local_data(data["token"])
                    self.ent_token.delete(0, "end"); self.ent_token.insert(0, dec_t)
                    if hasattr(self, "ent_xsmm_token_bar"):
                        self.ent_xsmm_token_bar.delete(0, "end"); self.ent_xsmm_token_bar.insert(0, dec_t)
                if "global_proxy" in data:
                    self.ent_global_proxy.delete(0, "end"); self.ent_global_proxy.insert(0, str(data["global_proxy"]))
                if "delay_min" in data:
                    self.ent_delay_min.delete(0, "end"); self.ent_delay_min.insert(0, str(data["delay_min"]))
                if "delay_max" in data:
                    self.ent_delay_max.delete(0, "end"); self.ent_delay_max.insert(0, str(data["delay_max"]))
                if "delay_coin_min" in data:
                    self.ent_delay_coin_min.delete(0, "end"); self.ent_delay_coin_min.insert(0, str(data["delay_coin_min"]))
                if "delay_coin_max" in data:
                    self.ent_delay_coin_max.delete(0, "end"); self.ent_delay_coin_max.insert(0, str(data["delay_coin_max"]))
                if "threads" in data:
                    self.ent_threads.delete(0, "end"); self.ent_threads.insert(0, str(data["threads"]))
                if "ttc_modes" in data and isinstance(data["ttc_modes"], dict):
                    for m_key, b_val in data["ttc_modes"].items():
                        if m_key in self.ttc_mode_vars:
                            self.ttc_mode_vars[m_key].set(bool(b_val))
            except Exception:
                pass

    def save_config(self):
        try:
            self.sync_cache_from_ui()
            d_min, d_max, dc_min, dc_max = self.get_delay_settings()
            ttc_modes_dict = {k: bool(v.get()) for k, v in self.ttc_mode_vars.items()}
            data = {
                "token": encrypt_local_data(self.cfg_cache["token"]),
                "global_proxy": self.cfg_cache["global_proxy"],
                "delay_min": d_min,
                "delay_max": d_max,
                "delay_coin_min": dc_min,
                "delay_coin_max": dc_max,
                "threads": str(self.cfg_cache["threads"]),
                "ttc_modes": ttc_modes_dict
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._log_queue.put(f"[{timestamp}] {message}\n")

    def update_stats(self, coins=0, jobs=0, entity_type="page", entity_key="", ttc_user=""):
        with self.lock:
            if coins:
                self.total_coins += coins
                self._balance_dirty = True
                if entity_type == "account" and entity_key in self.acc_rows:
                    self.acc_rows[entity_key]["coins"] += coins
                    c_val = self.acc_rows[entity_key]["coins"]
                    self.queue_row_ui("account", entity_key, coin_text=f"+{c_val:,} xu")
                    self._db_queue.put(("UPDATE accounts SET coins = ? WHERE username = ?", (c_val, entity_key)))
                elif entity_type == "page" and entity_key in self.page_rows:
                    self.page_rows[entity_key]["coins"] += coins
                    c_val = self.page_rows[entity_key]["coins"]
                    self.queue_row_ui("page", entity_key, coin_text=f"+{c_val:,} xu")
                    self._db_queue.put(("UPDATE fb_pages SET coins = ? WHERE page_id = ?", (c_val, entity_key)))
                if ttc_user and ttc_user in self.ttc_accounts:
                    self.ttc_accounts[ttc_user]["coins"] += coins
                    new_ttc_c = self.ttc_accounts[ttc_user]["coins"]
                    self.queue_row_ui("ttc", ttc_user, coin_text=f"💰 {new_ttc_c:,} xu")
                    self._db_queue.put(("UPDATE ttc_accounts SET coins = ? WHERE ttc_user = ?", (new_ttc_c, ttc_user)))
            if jobs:
                self.success_jobs += jobs

    def update_uptime_loop(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.lbl_status_uptime.configure(text=f"⏱️ UPTIME: {timedelta(seconds=elapsed)} | Job thành công: {self.success_jobs}")
        running_cnt = sum(1 for v in self.single_running_threads.values() if v)
        self.lbl_footer_stats.configure(
            text=f"Tổng Page FB: {len(self.page_rows)} | Acc TTC: {len(self.ttc_accounts)} | Acc IG (XSMM): {len(self.acc_rows)} | Luồng đang chạy: {running_cnt}"
        )
        self.after(1000, self.update_uptime_loop)

    def export_logs(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.txt_log.get("0.0", "end"))
            self.log("💾 Đã xuất file nhật ký thành công!")

    def trigger_kill_switch(self):
        self.is_running = False
        for k in list(self.single_running_threads.keys()):
            self.single_running_threads[k] = False
        for u in self.acc_rows.keys():
            self.queue_row_ui("account", u, status_text="Đã dừng theo lệnh", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")
        for p in self.page_rows.keys():
            self.queue_row_ui("page", p, status_text="Đã dừng theo lệnh", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")
        self.log("🛑 Đã dừng toàn bộ các luồng theo yêu cầu của bạn.")

    # ==========================================================================
    # QUẢN LÝ TÀI KHOẢN TTC & TỰ ĐỘNG HIỂN THỊ PAGE ĐÃ LIÊN KẾT TRÊN WEB
    # ==========================================================================
    def get_ttc_dropdown_values(self):
        vals = [f"TTC: {u}" for u in self.ttc_accounts.keys()]
        return vals if vals else ["-- Chưa thêm Acc TTC --"]

    def refresh_all_ttc_dropdowns(self):
        vals = self.get_ttc_dropdown_values()
        if hasattr(self, "opt_bulk_ttc"):
            self.opt_bulk_ttc.configure(values=vals)
            self.opt_bulk_ttc.set(vals[0])

        for pid, info in self.page_rows.items():
            if "ttc_menu" in info:
                info["ttc_menu"].configure(values=vals)
                curr_v = info["ttc_var"].get()
                if (curr_v not in vals or curr_v.startswith("--")) and vals:
                    info["ttc_var"].set(vals[0])
                    info["data"]["assigned_ttc"] = vals[0]

    def format_ttc_linked_summary(self, ttc_user):
        """Tạo chuỗi hiển thị rõ Acc TTC này đã liên kết những Page nào và đang chọn Page nào"""
        info = self.ttc_accounts.get(ttc_user, {})
        active_pid = str(info.get("active_page_id") or "").strip()
        cfg_map = info.get("configured_pages_map") or {}

        # Đối chiếu với tên Page thực tế trong bảng Page của phần mềm
        matched_names = []
        for pid_k, web_name in cfg_map.items():
            if pid_k in self.page_rows:
                real_n = self.page_rows[pid_k]["data"].get("page_name", web_name)
                matched_names.append(f"{real_n} ({pid_k[-5:]})")
            else:
                matched_names.append(f"{web_name} ({pid_k[-5:]})")

        if active_pid:
            act_name = self.page_rows[active_pid]["data"]["page_name"] if active_pid in self.page_rows else cfg_map.get(active_pid, active_pid)
            return f"🔥 Đang chọn: {act_name} ({active_pid}) | Đã LK: {len(cfg_map)} Page"
        if matched_names:
            return f"📌 Đã LK Web ({len(matched_names)}): " + ", ".join(matched_names[:2])
        return "📌 Chưa quét thấy Page LK (Bấm 🔄 Quét)"

    def update_page_link_badges_from_ttc(self):
        """
        Quét toàn bộ các Page trên bảng và tự động:
        1. Hiển thị rõ ở cột '📌 PAGE ĐÃ LK TRÊN WEB / ĐANG CHỌN LÀM' xem Page đó thuộc Acc TTC nào.
        2. Tự động chọn sẵn đúng Acc TTC đó trong cột Dropdown để bạn không bao giờ bị nhầm!
        """
        for pid, p_info in self.page_rows.items():
            linked_ttc_users = []
            active_on_ttc_user = ""
            for t_user, t_data in self.ttc_accounts.items():
                cfg_map = t_data.get("configured_pages_map") or {}
                if str(pid) in cfg_map:
                    linked_ttc_users.append(t_user)
                if str(t_data.get("active_page_id", "")) == str(pid):
                    active_on_ttc_user = t_user

            if active_on_ttc_user:
                badge_txt = f"🔥 ĐANG CHỌN LÀM ({active_on_ttc_user})"
                badge_col = "#059669"
                target_opt = f"TTC: {active_on_ttc_user}"
                p_info["ttc_var"].set(target_opt)
                p_info["data"]["assigned_ttc"] = target_opt
                self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (target_opt, pid)))
            elif linked_ttc_users:
                first_u = linked_ttc_users[0]
                badge_txt = f"✅ Đã LK Web TTC: {', '.join(linked_ttc_users)}"
                badge_col = "#0284c7"
                target_opt = f"TTC: {first_u}"
                p_info["ttc_var"].set(target_opt)
                p_info["data"]["assigned_ttc"] = target_opt
                self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (target_opt, pid)))
            else:
                curr_assigned = p_info["ttc_var"].get()
                if curr_assigned and curr_assigned.startswith("TTC:"):
                    badge_txt = f"📌 Gán tay -> {curr_assigned}"
                    badge_col = "#475569"
                else:
                    badge_txt = "⚪ Chưa rõ Acc TTC liên kết"
                    badge_col = "#94a3b8"

            self.queue_row_ui("page", pid, link_badge_text=badge_txt, link_badge_color=badge_col)

        # Cập nhật lại dòng trạng thái của từng Acc TTC
        for t_user in self.ttc_accounts.keys():
            summary_txt = self.format_ttc_linked_summary(t_user)
            self.queue_row_ui("ttc", t_user, status_text=summary_txt, status_color="#0284c7")

    def load_ttc_accounts_from_db(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT ttc_user, ttc_token, coins, status, active_page_id, configured_pages FROM ttc_accounts")
            rows = cursor.fetchall()
            conn.close()
            for t_user, t_tok, coins, st, act_pid, cfg_json in rows:
                try:
                    cfg_map = json.loads(cfg_json) if cfg_json else {}
                except Exception:
                    cfg_map = {}
                self.ttc_accounts[t_user] = {
                    "ttc_user": t_user,
                    "ttc_token": t_tok,
                    "coins": coins or 0,
                    "status": st or "Sẵn sàng",
                    "active_page_id": act_pid or "",
                    "configured_pages_map": cfg_map
                }
                self.ttc_account_locks[t_user] = threading.Lock()
                self.add_ttc_row_to_ui(self.ttc_accounts[t_user])
            self.refresh_all_ttc_dropdowns()
        except Exception:
            pass

    def add_ttc_account_action(self):
        raw_input = self.ent_ttc_token.get().strip()
        if not raw_input:
            self.log("⚠️ Vui lòng nhập Access Token Tương Tác Chéo!")
            return

        tokens_list = [t.strip() for t in re.split(r'[,\n;|]+', raw_input) if t.strip()]

        def _do_login_ttc():
            for ttc_tok in tokens_list:
                self.log("🔄 Đang đăng nhập Token TTC & quét danh sách Page đã cấu hình trên web...")
                ttc_client = TuongTacCheoTool(ttc_tok, proxy=self.get_effective_proxy(""))
                ok, uname, sodu, msg = ttc_client.login()
                if ok and uname:
                    self.ttc_clients_cache[uname] = ttc_client
                    act_pid = ttc_client.current_configured_uid
                    cfg_map = ttc_client.configured_pages_map

                    self.ttc_accounts[uname] = {
                        "ttc_user": uname,
                        "ttc_token": ttc_tok,
                        "coins": sodu,
                        "status": f"Đã LK {len(cfg_map)} Page",
                        "active_page_id": act_pid,
                        "configured_pages_map": cfg_map
                    }
                    if uname not in self.ttc_account_locks:
                        self.ttc_account_locks[uname] = threading.Lock()

                    self._db_queue.put((
                        "INSERT OR REPLACE INTO ttc_accounts (ttc_user, ttc_token, coins, status, active_page_id, configured_pages) VALUES (?, ?, ?, ?, ?, ?)",
                        (uname, ttc_tok, sodu, self.ttc_accounts[uname]["status"], act_pid, json.dumps(cfg_map, ensure_ascii=False))
                    ))
                    self.after(0, lambda u=uname: self.add_ttc_row_to_ui(self.ttc_accounts[u]))
                    self.log(f"✅ Đã thêm Acc TTC [{uname}] | Số dư: {sodu:,} xu | Tìm thấy {len(cfg_map)} Page đã cấu hình trên Web!")
                else:
                    ttc_client.close()
                    self.log(f"❌ Đăng nhập TTC thất bại: {msg}")

            self.after(0, lambda: self.ent_ttc_token.delete(0, "end"))
            self.after(0, self.refresh_all_ttc_dropdowns)
            self.after(0, self.update_page_link_badges_from_ttc)

        threading.Thread(target=_do_login_ttc, daemon=True).start()

    def sync_all_ttc_linked_pages_from_web(self):
        """Quét lại toàn bộ các Acc TTC để lấy danh sách Page đã liên kết trên Web và tự khớp với bảng Page"""
        if not self.ttc_accounts:
            self.log("⚠️ Chưa có tài khoản TTC nào trong danh sách!")
            return

        def _do_sync():
            self.log(f"🔄 Đang quét cấu hình Page trên web cho {len(self.ttc_accounts)} tài khoản TTC...")
            for uname, t_info in list(self.ttc_accounts.items()):
                client = self.ttc_clients_cache.get(uname)
                if not client:
                    client = TuongTacCheoTool(t_info["ttc_token"], proxy=self.get_effective_proxy(""))
                    ok, _, sodu, _ = client.login()
                    if ok:
                        self.ttc_clients_cache[uname] = client
                        t_info["coins"] = sodu
                else:
                    client.fetch_configured_pages_on_web()

                t_info["active_page_id"] = client.current_configured_uid
                t_info["configured_pages_map"] = client.configured_pages_map
                self._db_queue.put((
                    "UPDATE ttc_accounts SET coins = ?, active_page_id = ?, configured_pages = ? WHERE ttc_user = ?",
                    (t_info["coins"], t_info["active_page_id"], json.dumps(t_info["configured_pages_map"], ensure_ascii=False), uname)
                ))
                self.log(f"📌 [TTC: {uname}] Đã liên kết {len(client.configured_pages_map)} Page trên web | Nick đang chọn: {client.current_configured_uid or 'Chưa chọn'}")

            self.after(0, self.update_page_link_badges_from_ttc)
            self.log("✨ Hoàn tất khớp tự động Page với các tài khoản TTC!")

        threading.Thread(target=_do_sync, daemon=True).start()

    def add_ttc_row_to_ui(self, ttc_data):
        uname = ttc_data["ttc_user"]
        summary_txt = self.format_ttc_linked_summary(uname)
        if uname in self.ttc_rows_ui:
            self.queue_row_ui("ttc", uname, coin_text=f"💰 {ttc_data['coins']:,} xu", status_text=summary_txt, status_color="#0284c7")
            return

        row = ctk.CTkFrame(self.scroll_ttc_accs, fg_color="#f8fafc", corner_radius=6, border_width=1, border_color="#e2e8f0", height=32)
        row.pack(fill="x", padx=2, pady=2)
        row.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(row, text=f"👤 {uname}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a", width=95, anchor="w").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        lbl_coin = ctk.CTkLabel(row, text=f"💰 {ttc_data['coins']:,} xu", font=ctk.CTkFont(size=10, weight="bold"), text_color="#059669", width=95, anchor="w")
        lbl_coin.grid(row=0, column=1, padx=4, pady=4, sticky="w")

        lbl_st = ctk.CTkLabel(row, text=summary_txt, font=ctk.CTkFont(size=10, weight="bold"), text_color="#0284c7", anchor="w")
        lbl_st.grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        def _del_ttc():
            if uname in self.ttc_accounts:
                del self.ttc_accounts[uname]
            if uname in self.ttc_rows_ui:
                self.ttc_rows_ui[uname]["frame"].destroy()
                del self.ttc_rows_ui[uname]
            self._db_queue.put(("DELETE FROM ttc_accounts WHERE ttc_user = ?", (uname,)))
            self.refresh_all_ttc_dropdowns()
            self.update_page_link_badges_from_ttc()
            self.log(f"🗑️ Đã xóa tài khoản TTC: {uname}")

        ctk.CTkButton(row, text="✕", width=24, height=22, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4, command=_del_ttc).grid(row=0, column=3, padx=4, pady=4)

        self.ttc_rows_ui[uname] = {
            "frame": row,
            "coin_label": lbl_coin,
            "status_label": lbl_st,
            "status_text": summary_txt
        }

    # ==========================================================================
    # QUẢN LÝ CÂY PHÂN CẤP: TÀI KHOẢN FB MẸ -> CÁC PAGE CON
    # ==========================================================================
    def ensure_fb_parent_section(self, fb_uid, fb_name="", cookie="", access_token=""):
        fb_uid = str(fb_uid or "Main").strip()
        if fb_uid in self.fb_parent_sections:
            sec = self.fb_parent_sections[fb_uid]
            if cookie: sec["cookie"] = cookie
            if access_token: sec["access_token"] = access_token
            if fb_name and not fb_name.startswith("FB_"): sec["fb_name"] = fb_name
            has_ck = "✅ Cookie" if sec.get("cookie") else "❌ Cookie"
            has_tk = "✅ Token" if sec.get("access_token") else "❌ Token"
            sec["header_label"].configure(text=f"👤 NICK FB MẸ: {sec['fb_name']} (UID: {fb_uid})   [{has_ck} | {has_tk}]")
            return sec

        container = ctk.CTkFrame(self.scroll_pages, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#cbd5e1")
        container.pack(fill="x", padx=4, pady=5)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(container, fg_color="#eff6ff", corner_radius=6, height=34)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        header.grid_columnconfigure(0, weight=1)

        disp_name = fb_name if fb_name else f"FB_{fb_uid}"
        has_ck = "✅ Cookie" if cookie else "❌ Cookie"
        has_tk = "✅ Token" if access_token else "❌ Token"

        lbl_head = ctk.CTkLabel(
            header,
            text=f"👤 NICK FB MẸ: {disp_name} (UID: {fb_uid})   [{has_ck} | {has_tk}]",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#1e3a8a"
        )
        lbl_head.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        def _select_all_child_pages():
            for pid, pinfo in self.page_rows.items():
                if str(pinfo["data"].get("parent")) == fb_uid:
                    pinfo["var"].set(True)

        def _delete_fb_parent():
            to_del_pids = [pid for pid, pinfo in self.page_rows.items() if str(pinfo["data"].get("parent")) == fb_uid]
            for pid in to_del_pids:
                self.single_running_threads[pid] = False
                self._db_queue.put(("DELETE FROM fb_pages WHERE page_id = ?", (pid,)))
                if pid in self.page_rows:
                    del self.page_rows[pid]
            self._db_queue.put(("DELETE FROM fb_accounts WHERE fb_uid = ?", (fb_uid,)))
            container.destroy()
            if fb_uid in self.fb_parent_sections:
                del self.fb_parent_sections[fb_uid]
            self.log(f"🗑️ Đã xóa Nick FB {disp_name} và {len(to_del_pids)} Page con.")

        ctk.CTkButton(header, text="✓ Tích hết Page của FB này", width=155, height=24, fg_color="#0284c7", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5, command=_select_all_child_pages).grid(row=0, column=1, padx=4, pady=4)
        ctk.CTkButton(header, text="🗑️ Xóa FB", width=75, height=24, fg_color="#dc2626", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5, command=_delete_fb_parent).grid(row=0, column=2, padx=(2, 8), pady=4)

        pages_holder = ctk.CTkFrame(container, fg_color="transparent")
        pages_holder.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        pages_holder.grid_columnconfigure(0, weight=1)

        sec_data = {
            "container": container,
            "header_label": lbl_head,
            "pages_holder": pages_holder,
            "fb_uid": fb_uid,
            "fb_name": disp_name,
            "cookie": cookie,
            "access_token": access_token
        }
        self.fb_parent_sections[fb_uid] = sec_data
        return sec_data

    def load_fb_pages_from_db(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT fb_uid, fb_name, cookie, access_token FROM fb_accounts")
            for f_uid, f_name, f_ck, f_tok in cursor.fetchall():
                self.ensure_fb_parent_section(f_uid, f_name, f_ck, f_tok)

            cursor.execute("SELECT parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc FROM fb_pages")
            rows = cursor.fetchall()
            conn.close()
            for parent, pid, pname, ptok, proxy, status, db_coins, max_j, p_ck, u_tok, ass_ttc in rows:
                page_data = {
                    "parent": parent or "Main",
                    "page_id": str(pid),
                    "page_name": pname,
                    "page_token": ptok,
                    "proxy": proxy,
                    "coins": db_coins or 0,
                    "max_jobs": max_j if max_j is not None else 999999,
                    "parent_cookie": p_ck or "",
                    "user_token": u_tok or "",
                    "assigned_ttc": ass_ttc or ""
                }
                self.add_page_row_to_ui(page_data, status)
            self.update_page_link_badges_from_ttc()
        except Exception:
            pass

    def add_page_row_to_ui(self, page_data, status="Sẵn sàng"):
        pid = str(page_data["page_id"])
        if pid in self.page_rows:
            return

        parent_uid = str(page_data.get("parent") or "Main")
        parent_sec = self.ensure_fb_parent_section(
            parent_uid,
            cookie=page_data.get("parent_cookie", ""),
            access_token=page_data.get("user_token", "")
        )

        row_frame = ctk.CTkFrame(parent_sec["pages_holder"], fg_color="#f8fafc", corner_radius=6, border_width=1, border_color="#e2e8f0", height=38)
        row_frame.pack(fill="x", padx=2, pady=2)
        row_frame.grid_columnconfigure(2, weight=1)

        is_die_init = ("Die" in status or "Hết Hạn" in status)
        var = ctk.BooleanVar(value=not is_die_init)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, fg_color="#0284c7")
        chk.grid(row=0, column=0, padx=(8, 4), pady=5, sticky="w")

        stt_idx = len(self.page_rows) + 1
        ctk.CTkLabel(row_frame, text=str(stt_idx), font=ctk.CTkFont(size=11), text_color="#475569", width=34).grid(row=0, column=1, padx=2, pady=5, sticky="w")

        ctk.CTkLabel(row_frame, text=f"↳ 📘 {page_data['page_name']}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").grid(row=0, column=2, padx=6, pady=5, sticky="w")

        ctk.CTkLabel(row_frame, text=str(pid), font=ctk.CTkFont(family="Consolas", size=10), text_color="#475569", width=125, anchor="w").grid(row=0, column=3, padx=4, pady=5, sticky="w")

        # Cột hiển thị rõ Page này đã liên kết với Acc TTC nào trên Web hoặc đang được chọn chạy
        lbl_link_badge = ctk.CTkLabel(row_frame, text="🔍 Đang kiểm tra LK...", font=ctk.CTkFont(size=10, weight="bold"), text_color="#0284c7", width=230, anchor="w")
        lbl_link_badge.grid(row=0, column=4, padx=4, pady=5, sticky="w")

        avail_vals = self.get_ttc_dropdown_values()
        saved_ttc = page_data.get("assigned_ttc", "")
        default_choice = saved_ttc if (saved_ttc and saved_ttc in avail_vals) else avail_vals[0]
        ttc_var = ctk.StringVar(value=default_choice)

        def _on_change_ttc(choice_val):
            page_data["assigned_ttc"] = choice_val
            self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (choice_val, pid)))
            self.queue_row_ui("page", pid, link_badge_text=f"📌 Đã chọn chạy -> {choice_val}", link_badge_color="#0284c7")

        ttc_menu = ctk.CTkOptionMenu(
            row_frame, variable=ttc_var, values=avail_vals,
            width=150, height=26, fg_color="#1e293b", button_color="#334155",
            font=ctk.CTkFont(size=10, weight="bold"), command=_on_change_ttc
        )
        ttc_menu.grid(row=0, column=5, padx=4, pady=5, sticky="w")

        init_c = page_data.get("coins", 0)
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{init_c:,} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=80, anchor="w")
        lbl_coin.grid(row=0, column=6, padx=4, pady=5, sticky="w")

        text_color_st = "#334155" if status == "Sẵn sàng" else ("#dc2626" if is_die_init else "#059669")
        lbl_status = ctk.CTkLabel(row_frame, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color=text_color_st, width=215, anchor="w")
        lbl_status.grid(row=0, column=7, padx=4, pady=5, sticky="w")

        def toggle_single_page():
            if not self.single_running_threads.get(pid, False):
                self.start_single_page_worker(pid)
            else:
                self.single_running_threads[pid] = False
                self.queue_row_ui("page", pid, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=76, height=26, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=toggle_single_page)
        btn_action.grid(row=0, column=8, padx=8, pady=5, sticky="e")

        self.page_rows[pid] = {
            "frame": row_frame,
            "var": var,
            "ttc_var": ttc_var,
            "ttc_menu": ttc_menu,
            "link_badge": lbl_link_badge,
            "status_label": lbl_status,
            "status_text": status,
            "coin_label": lbl_coin,
            "action_btn": btn_action,
            "coins": init_c,
            "data": page_data
        }

    # ==========================================================================
    # KHỞI CHẠY PAGE TTC VỚI 12 CHẾ ĐỘ (KHÔNG BAO GIỜ TỰ NGẮT LỆNH)
    # ==========================================================================
    def start_single_page_worker(self, pid, stagger_delay=0.0):
        if pid not in self.page_rows:
            return
        info = self.page_rows[pid]
        page_data = info["data"]
        selected_ttc_str = info["ttc_var"].get().strip()

        # Nếu chưa gán hoặc có duy nhất 1 Acc TTC thì tự động lấy Acc TTC đầu tiên
        ttc_user = selected_ttc_str.replace("TTC:", "").strip()
        if ttc_user not in self.ttc_accounts:
            if self.ttc_accounts:
                ttc_user = list(self.ttc_accounts.keys())[0]
                info["ttc_var"].set(f"TTC: {ttc_user}")
            else:
                self.log(f"⚠️ [Page {page_data['page_name']}] Bạn chưa thêm Access Token TTC ở ô số 1!")
                self.queue_row_ui("page", pid, status_text="❌ Chưa thêm Token TTC!", status_color="#dc2626")
                return

        selected_modes = self.get_selected_ttc_modes()
        if not selected_modes:
            self.log("⚠️ Bạn chưa tích chọn chế độ Job nào trong 12 Chế Độ TTC (Ở khung số 3)!")
            self.queue_row_ui("page", pid, status_text="❌ Chưa chọn Job TTC!", status_color="#dc2626")
            return

        self.sync_cache_from_ui()
        self.save_config()
        if not self.start_time:
            self.start_time = time.time()
        self.is_running = True

        self.single_running_threads[pid] = True
        self.queue_row_ui(
            "page", pid,
            status_text=f"🚀 Đang khởi chạy ({ttc_user})...",
            status_color="#0284c7",
            btn_text="Dừng",
            btn_color="#dc2626",
            link_badge_text=f"🔥 ĐANG CHỌN LÀM ({ttc_user})",
            link_badge_color="#059669"
        )
        threading.Thread(
            target=self.worker_ttc_page_loop,
            args=(ttc_user, page_data, stagger_delay),
            daemon=True
        ).start()

    def assign_ttc_to_selected_pages_only(self):
        chosen_ttc = self.opt_bulk_ttc.get()
        selected_pids = [pid for pid, info in self.page_rows.items() if info["var"].get()]
        if not selected_pids or not chosen_ttc or chosen_ttc.startswith("--"):
            self.log("⚠️ Vui lòng tích chọn Page và chọn 1 Acc TTC hợp lệ!")
            return
        for pid in selected_pids:
            info = self.page_rows[pid]
            info["ttc_var"].set(chosen_ttc)
            info["data"]["assigned_ttc"] = chosen_ttc
            self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (chosen_ttc, pid)))
            self.queue_row_ui("page", pid, link_badge_text=f"📌 Đã gán -> {chosen_ttc}", link_badge_color="#0284c7")
        self.log(f"📌 Đã gán {chosen_ttc} cho {len(selected_pids)} Page đã tích.")

    def start_all_checked_ttc_pages(self):
        selected_pids = [pid for pid, info in self.page_rows.items() if info["var"].get()]
        if not selected_pids:
            self.log("⚠️ Vui lòng tích chọn ít nhất 1 Page FB bên dưới để bắt đầu chạy!")
            return
        started = 0
        for idx, pid in enumerate(selected_pids):
            if not self.single_running_threads.get(pid, False):
                self.start_single_page_worker(pid, stagger_delay=idx * 0.25)
                started += 1
        self.log(f"🚀 Đã kích hoạt chạy {started} Page đã tích với {len(self.get_selected_ttc_modes())} chế độ Job TTC!")

    def worker_ttc_page_loop(self, ttc_user, page, stagger_delay=0.0):
        """
        Luồng chạy Page trên Tương Tác Chéo (12 Chế độ Job):
        - Đã loại bỏ hoàn toàn lệnh tự ngắt sau khi liên kết (dat_nick).
        - Tự động hiển thị rõ Page nào đang được chọn làm trên Acc TTC.
        - Quét liên tục qua tất cả các chế độ trong 12 Chế Độ Job bạn đã tích chọn.
        """
        pid = str(page["page_id"]).strip()
        pname = str(page.get("page_name") or pid)
        ptok = str(page.get("page_token") or "")
        p_ck = str(page.get("parent_cookie") or "")

        if stagger_delay > 0:
            if not self.smart_sleep(stagger_delay, pid):
                return

        if ttc_user not in self.ttc_account_locks:
            self.ttc_account_locks[ttc_user] = threading.Lock()
        ttc_lock = self.ttc_account_locks[ttc_user]

        max_jobs = int(page.get("max_jobs") or 999999)
        attempted_jobs = 0
        fb_sess = c_requests.Session()

        try:
            while self.single_running_threads.get(pid, False):
                if attempted_jobs >= max_jobs:
                    self.queue_row_ui("page", pid, status_text=f"🏆 Đã hoàn thành {max_jobs} job", status_color="#059669")
                    break

                # Lấy danh sách 12 chế độ đang được tích chọn trực tiếp (cho phép bạn bật/tắt chế độ ngay khi đang chạy)
                active_modes = self.get_selected_ttc_modes()
                if not active_modes:
                    self.queue_row_ui("page", pid, status_text="⚠️ Hãy tích ít nhất 1 chế độ Job!", status_color="#d97706")
                    if not self.smart_sleep(5, pid):
                        break
                    continue

                self.queue_row_ui("page", pid, status_text=f"⏳ Chờ lượt luồng TTC ({ttc_user})...", status_color="#0284c7")

                with ttc_lock:
                    if not self.single_running_threads.get(pid, False):
                        break

                    ttc_info = self.ttc_accounts.get(ttc_user)
                    if not ttc_info:
                        self.log(f"❌ [Page {pname}] Không tìm thấy Acc TTC '{ttc_user}'")
                        break

                    proxy = self.get_effective_proxy(page.get("proxy", ""))
                    ttc_client = self.ttc_clients_cache.get(ttc_user)
                    if not ttc_client:
                        ttc_client = TuongTacCheoTool(ttc_info["ttc_token"], proxy=proxy)
                        ok_log, _, sodu_init, msg_log = ttc_client.login()
                        if not ok_log:
                            self.log(f"⚠️ [TTC: {ttc_user}] Lỗi đăng nhập ({msg_log}), thử lại sau 8s...")
                            self.queue_row_ui("page", pid, status_text=f"⚠️ Lỗi mạng/Token TTC, chờ 8s...", status_color="#d97706")
                            if not self.smart_sleep(8, pid):
                                break
                            continue
                        self.ttc_clients_cache[ttc_user] = ttc_client

                    # Đặt Nick trên TTC (Nhưng tuyệt đối KHÔNG tự ngắt nếu bạn đã liên kết sẵn trên web)
                    _, dat_msg = ttc_client.dat_nick(pid)
                    ttc_info["active_page_id"] = pid
                    self.queue_row_ui(
                        "ttc", ttc_user,
                        status_text=f"🔥 Đang chạy Page: {pname} ({pid})",
                        status_color="#059669"
                    )
                    self.queue_row_ui(
                        "page", pid,
                        link_badge_text=f"🔥 ĐANG CHỌN LÀM ({ttc_user})",
                        link_badge_color="#059669",
                        status_text=f"🔗 Đã chọn Page -> Quét {len(active_modes)} chế độ...",
                        status_color="#0284c7"
                    )

                    found_any_job = False
                    for mode_key in active_modes:
                        if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs:
                            break

                        mode_cfg = TTC_12_JOB_MODES.get(mode_key, {})
                        mode_name = mode_cfg.get("name", mode_key)
                        action_type = mode_cfg.get("action", "like")

                        self.queue_row_ui("page", pid, status_text=f"🔍 Tìm [{mode_name}]...", status_color="#0284c7")
                        tasks, err_msg = ttc_client.get_tasks(mode_key)
                        if not tasks:
                            continue

                        found_any_job = True
                        self.log(f"📥 [TTC: {ttc_user} | Page: {pname}] Có {len(tasks)} job [{mode_name}]")

                        for nv in tasks:
                            if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs:
                                break

                            delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                            proxy = self.get_effective_proxy(page.get("proxy", ""))
                            task_id = str(nv.get("id", ""))
                            link_job = str(nv.get("target_url", ""))
                            target_id = str(nv.get("target_id", "") or task_id)
                            loaicx = str(nv.get("loaicx") or "LOVE").upper()

                            self.queue_row_ui("page", pid, status_text=f"⚡ Làm {mode_name[:16]} [{task_id[:8]}]...", status_color="#2563eb")
                            success = False
                            fail_reason = "Lỗi FB"

                            try:
                                with self.net_semaphore:
                                    if action_type == "like":
                                        res_raw = fb_page_react_or_like(link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck, target_id=target_id, reaction_type="LIKE")
                                    elif action_type in ["react", "react_cmt"]:
                                        res_raw = fb_page_react_or_like(link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck, target_id=target_id, reaction_type=loaicx)
                                    elif action_type in ["follow", "likepage"]:
                                        res_raw = fb_page_follow(target_id, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    elif action_type == "comment":
                                        cmt_txt = nv.get("msg") or ai_generate_unique_comment()
                                        res_raw = fb_page_comment(target_id, cmt_txt, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    elif action_type == "share":
                                        res_raw = fb_page_share(target_id or link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    else:
                                        res_raw = fb_page_like(link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck, target_id=target_id)

                                    j = json.loads(res_raw)
                                    if j.get("success") or j.get("id"):
                                        success = True
                                    else:
                                        fail_reason = str(j.get("error", "FB từ chối"))
                            except Exception as ex:
                                fail_reason = str(ex)[:25]

                            attempted_jobs += 1
                            if success:
                                wait_coin = random.randint(delay_coin_min, delay_coin_max)
                                self.queue_row_ui("page", pid, status_text=f"⏳ Chờ {wait_coin}s nhận xu...", status_color="#0284c7")
                                if not self.smart_sleep(wait_coin, pid):
                                    break

                                earned, claim_msg = ttc_client.claim_reward(mode_key, task_id, loaicx=loaicx)
                                if earned > 0:
                                    self.update_stats(coins=int(earned), jobs=1, entity_type="page", entity_key=pid, ttc_user=ttc_user)
                                    self.log(f"💰 [TTC: {ttc_user} | {pname}] +{earned} xu ({mode_name} - ID: {task_id})")
                                    self.queue_row_ui("page", pid, status_text=f"✅ +{earned} xu ({attempted_jobs} job)", status_color="#059669")
                                else:
                                    self.log(f"⚠️ [TTC: {ttc_user} | {pname}] Duyệt [{mode_name}] báo: {claim_msg}")
                                    self.queue_row_ui("page", pid, status_text=f"⚠️ {claim_msg[:20]}", status_color="#d97706")
                            else:
                                self.log(f"❌ [Page {pname}] Lỗi {mode_name} [{task_id}]: {fail_reason}")
                                self.queue_row_ui("page", pid, status_text=f"❌ {fail_reason[:18]}", status_color="#dc2626")

                            wait_next = random.randint(delay_min, delay_max)
                            if not self.smart_sleep(wait_next, pid):
                                break

                if self.single_running_threads.get(pid, False) and attempted_jobs < max_jobs:
                    rest_sec = 6 if found_any_job else 8
                    w_txt = f"🔄 Nghỉ {rest_sec}s quét vòng mới..." if found_any_job else f"⏳ Chờ {rest_sec}s tải thêm Job TTC..."
                    self.queue_row_ui("page", pid, status_text=w_txt, status_color="#059669" if found_any_job else "#d97706")
                    if not self.smart_sleep(rest_sec, pid):
                        break
        except Exception as fatal_e:
            self.log(f"⚠️ [Page {pname}] Cảnh báo luồng: {str(fatal_e)[:40]}")
        finally:
            try:
                fb_sess.close()
            except Exception:
                pass

        self.single_running_threads[pid] = False
        self.queue_row_ui("page", pid, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")

    # ==========================================================================
    # CÁC HÀM TIỆN ÍCH FACEBOOK PAGE & INSTAGRAM XSMM
    # ==========================================================================
    def toggle_all_pages(self, select_state):
        for item in self.page_rows.values():
            item["var"].set(select_state)

    def delete_selected_pages(self):
        to_delete = [pid for pid, info in self.page_rows.items() if info["var"].get()]
        for pid in to_delete:
            self.single_running_threads[pid] = False
            self._db_queue.put(("DELETE FROM fb_pages WHERE page_id = ?", (pid,)))
            if pid in self.page_rows:
                self.page_rows[pid]["frame"].destroy()
                del self.page_rows[pid]
        if to_delete:
            self.log(f"🗑️ Đã xóa {len(to_delete)} Page đã chọn.")

    def check_selected_fb_live(self):
        selected = [pid for pid, info in self.page_rows.items() if info["var"].get()] or list(self.page_rows.keys())
        if not selected:
            return

        def _do_check():
            live_c, die_c = 0, 0
            for pid in selected:
                info = self.page_rows.get(pid)
                if not info:
                    continue
                ptok = info["data"].get("page_token", "")
                p_ck = info["data"].get("parent_cookie", "")
                proxy = self.get_effective_proxy(info["data"].get("proxy", ""))
                self.queue_row_ui("page", pid, status_text="🔄 Đang check live...", status_color="#0284c7")
                is_live = False
                try:
                    s = c_requests.Session()
                    if px := format_proxy(proxy):
                        s.proxies = px
                    if ptok and str(ptok).startswith("EAA"):
                        if "id" in s.get(f"https://graph.facebook.com/v18.0/me?access_token={ptok}", timeout=8).json():
                            is_live = True
                    if not is_live and (p_ck or "c_user=" in str(ptok)):
                        raw_ck = p_ck if p_ck else ptok
                        if _get_fb_dtsg(s, _build_page_cookie(raw_ck, pid), pid):
                            is_live = True
                    s.close()
                except Exception:
                    pass
                if is_live:
                    live_c += 1
                    self.queue_row_ui("page", pid, status_text="Live ✅ (Sẵn sàng)", status_color="#059669", var_val=True)
                else:
                    die_c += 1
                    self.queue_row_ui("page", pid, status_text="Die / Hết hạn ❌", status_color="#dc2626", var_val=False)
            self.log(f"✨ Kết quả Check Live Page: {live_c} Live ✅ | {die_c} Die ❌")

        threading.Thread(target=_do_check, daemon=True).start()

    def _parse_fb_line(self, line_str):
        ck, tok, px = "", "", ""
        for part in [p.strip() for p in line_str.split("|") if p.strip()]:
            if part.startswith("EAA"):
                tok = part
            elif "c_user=" in part or "xs=" in part:
                ck = part
            elif ":" in part and not part.startswith("EAA"):
                px = part
            elif not ck:
                ck = part
        return ck, tok, self.get_effective_proxy(px)

    def quick_link_fb_and_scan_pages(self):
        self.sync_cache_from_ui()
        raw_ck = self.txt_fb_cookies.get().strip()
        raw_tok = self.txt_fb_token.get().strip()
        if not raw_ck and not raw_tok:
            self.log("⚠️ Vui lòng dán Cookie FB Mẹ hoặc Token FB!")
            return
        try: max_jobs_val = int(self.max_jobs_fb_entry.get().strip())
        except Exception: max_jobs_val = 999999

        ck, tok, proxy = self._parse_fb_line(raw_ck) if ("|" in raw_ck and not raw_tok) else (raw_ck, raw_tok, self.get_effective_proxy(""))

        def _do_quick_scan():
            self.log("🔍 Đang quét tài khoản FB Mẹ & toàn bộ danh sách Page Con...")
            fb_info, pages = scan_facebook_account_and_pages(cookie=ck, access_token=tok, proxy=proxy)
            f_uid, f_name = fb_info["fb_uid"], fb_info["fb_name"]

            self._db_queue.put((
                "INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status, platform) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_uid, f_name, ck, tok, proxy, "Live ✅", "TTC")
            ))
            self.after(0, lambda: self.ensure_fb_parent_section(f_uid, f_name, ck, tok))

            default_ttc = self.get_ttc_dropdown_values()[0]
            for p in pages:
                pid, pname, ptok = str(p["page_id"]), p["page_name"], p["page_token"]
                self._db_queue.put((
                    "INSERT OR REPLACE INTO fb_pages (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f_uid, pid, pname, ptok, proxy, "Live ✅ (Sẵn sàng)", 0, max_jobs_val, ck, tok, default_ttc, "TTC")
                ))
                page_data = {
                    "parent": f_uid, "page_id": pid, "page_name": pname, "page_token": ptok,
                    "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val,
                    "parent_cookie": ck, "user_token": tok, "assigned_ttc": default_ttc
                }
                self.after(0, lambda pd=page_data: self.add_page_row_to_ui(pd, status="Live ✅ (Sẵn sàng)"))

            self.after(0, lambda: self.txt_fb_cookies.delete(0, "end"))
            self.after(0, lambda: self.txt_fb_token.delete(0, "end"))
            self.after(200, self.update_page_link_badges_from_ttc)
            self.log(f"✅ Đã nạp FB [{f_name}] -> Hiển thị {len(pages)} Page Con & tự khớp với Acc TTC!")

        threading.Thread(target=_do_quick_scan, daemon=True).start()

    def scan_and_import_fb_pages(self):
        modal = ctk.CTkToplevel(self)
        modal.title("📥 Nạp Hàng Loạt Nick FB Mẹ & Quét Page")
        modal.geometry("720x500")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="📋 DÁN DANH SÁCH COOKIE / TOKEN FB (MỖI DÒNG 1 NICK FB)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#0284c7").pack(anchor="w", padx=20, pady=(16, 4))
        txt_batch = ctk.CTkTextbox(modal, height=340, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#f8fafc", border_width=1)
        txt_batch.pack(fill="both", expand=True, padx=20, pady=8)

        def process_scan():
            raw_text = txt_batch.get("1.0", "end").strip()
            if not raw_text:
                return
            try: max_jobs_val = int(self.max_jobs_fb_entry.get().strip())
            except Exception: max_jobs_val = 999999
            lines = [c.strip() for c in raw_text.split("\n") if c.strip()]
            modal.destroy()

            def _do_scan():
                total_pg = 0
                default_ttc = self.get_ttc_dropdown_values()[0]
                for line in lines:
                    ck, tok, proxy = self._parse_fb_line(line)
                    fb_info, pages = scan_facebook_account_and_pages(cookie=ck, access_token=tok, proxy=proxy)
                    f_uid, f_name = fb_info["fb_uid"], fb_info["fb_name"]
                    self._db_queue.put(("INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status, platform) VALUES (?, ?, ?, ?, ?, ?, ?)", (f_uid, f_name, ck, tok, proxy, "Live ✅", "TTC")))
                    self.after(0, lambda u=f_uid, n=f_name, c=ck, t=tok: self.ensure_fb_parent_section(u, n, c, t))
                    for p in pages:
                        pid, pname, ptok = str(p["page_id"]), p["page_name"], p["page_token"]
                        self._db_queue.put(("INSERT OR REPLACE INTO fb_pages (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (f_uid, pid, pname, ptok, proxy, "Live ✅ (Sẵn sàng)", 0, max_jobs_val, ck, tok, default_ttc, "TTC")))
                        pd = {"parent": f_uid, "page_id": pid, "page_name": pname, "page_token": ptok, "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val, "parent_cookie": ck, "user_token": tok, "assigned_ttc": default_ttc}
                        total_pg += 1
                        self.after(0, lambda item=pd: self.add_page_row_to_ui(item, status="Live ✅ (Sẵn sàng)"))
                self.after(300, self.update_page_link_badges_from_ttc)
                self.log(f"✨ Đã quét xong {len(lines)} Nick FB -> Thu được {total_pg} Page Con!")

            threading.Thread(target=_do_scan, daemon=True).start()

        ctk.CTkButton(modal, text="🚀 BẮT ĐẦU QUÉT DÀN PAGE", fg_color="#0284c7", height=40, font=ctk.CTkFont(size=12, weight="bold"), command=process_scan).pack(fill="x", padx=20, pady=12)

    # ==========================================================================
    # KHU VỰC XSMM.NET (IG WORKER ĐỘC LẬP)
    # ==========================================================================
    def load_accounts_from_db(self):
        if not os.path.exists(DB_FILE):
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT username, cookie, proxy, status, coins, max_jobs FROM accounts")
            for ig_user, ck, proxy, status, db_coins, max_j in cursor.fetchall():
                idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"])[1]
                acc_data = {"username": ig_user, "cookie": ck, "proxy": proxy, "id": idfb, "coins": db_coins or 0, "max_jobs": max_j or 999999}
                self.add_account_row_to_ui(acc_data, status)
            conn.close()
        except Exception:
            pass

    def add_account_row_to_ui(self, acc_data, status="Sẵn sàng"):
        ig_user = acc_data["username"]
        if ig_user in self.acc_rows:
            return

        row_frame = ctk.CTkFrame(self.scroll_accs, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#e2e8f0", height=38)
        row_frame.pack(fill="x", padx=4, pady=2)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)

        var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row_frame, text="", variable=var, width=20, fg_color="#2563eb").grid(row=0, column=0, padx=(10, 6), pady=5)
        ctk.CTkLabel(row_frame, text=str(len(self.acc_rows) + 1), width=45).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row_frame, text="XSMM-IG", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2563eb", width=80).grid(row=0, column=2, sticky="w")
        lbl_id = ctk.CTkLabel(row_frame, text=str(acc_data.get("id", "0")), font=ctk.CTkFont(family="Consolas", size=10))
        lbl_id.grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(row_frame, text=f"@{ig_user}", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, sticky="w", padx=6)
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{acc_data.get('coins', 0):,} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=100, anchor="w")
        lbl_coin.grid(row=0, column=5, sticky="w", padx=6)
        lbl_status = ctk.CTkLabel(row_frame, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color="#059669", width=240, anchor="w")
        lbl_status.grid(row=0, column=6, sticky="w", padx=6)

        def toggle_ig():
            if not self.single_running_threads.get(ig_user, False):
                self.sync_cache_from_ui()
                token = self.cfg_cache["token"]
                if not token:
                    self.log("⚠️ Vui lòng nhập XSMM Bearer Token ở thanh trên cùng của Tab XSMM!")
                    return
                jobs = []
                if self.chk_ig_like.get(): jobs.append("instagram_like")
                if self.chk_ig_follow.get(): jobs.append("instagram_follow")
                if self.chk_ig_cmt.get(): jobs.append("instagram_comment")
                self.single_running_threads[ig_user] = True
                self.queue_row_ui("account", ig_user, status_text="Đang chạy XSMM...", status_color="#2563eb", btn_text="Dừng", btn_color="#dc2626")
                threading.Thread(target=self.worker_single_account_loop, args=(token, jobs, acc_data), daemon=True).start()
            else:
                self.single_running_threads[ig_user] = False
                self.queue_row_ui("account", ig_user, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=80, height=26, fg_color="#2563eb", font=ctk.CTkFont(size=10, weight="bold"), command=toggle_ig)
        btn_action.grid(row=0, column=7, padx=10, pady=5, sticky="e")

        self.acc_rows[ig_user] = {"frame": row_frame, "var": var, "id_label": lbl_id, "status_label": lbl_status, "status_text": status, "coin_label": lbl_coin, "action_btn": btn_action, "coins": acc_data.get("coins", 0), "data": acc_data}

    def start_all_checked_xsmm_ig(self):
        self.sync_cache_from_ui()
        token = self.cfg_cache["token"]
        if not token:
            self.log("⚠️ Vui lòng nhập XSMM Bearer Token trước khi chạy!")
            return
        jobs = []
        if self.chk_ig_like.get(): jobs.append("instagram_like")
        if self.chk_ig_follow.get(): jobs.append("instagram_follow")
        if self.chk_ig_cmt.get(): jobs.append("instagram_comment")
        for u, info in self.acc_rows.items():
            if info["var"].get() and not self.single_running_threads.get(u, False):
                self.single_running_threads[u] = True
                self.queue_row_ui("account", u, status_text="Đang chạy XSMM...", status_color="#2563eb", btn_text="Dừng", btn_color="#dc2626")
                threading.Thread(target=self.worker_single_account_loop, args=(token, jobs, info["data"]), daemon=True).start()

    def quick_add_single_account(self):
        ck = self.ent_quick_cookie.get().strip().split("|")[0].strip()
        if not ck:
            return
        proxy = self.get_effective_proxy("")
        try: max_j = int(self.max_jobs_entry.get().strip())
        except Exception: max_j = 999999

        def _add():
            p_data = json.loads(check_cookie_ig(ck, proxy))
            if p_data.get("status_check") == "LIVE":
                u = p_data["form_data"]["username"]
                uid = str(p_data["form_data"].get("id", "0"))
                self._db_queue.put(("INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)", (u, ck, proxy, "Live ✅", 0, max_j)))
                acc_d = {"username": u, "cookie": ck, "proxy": proxy, "id": uid, "coins": 0, "max_jobs": max_j}
                self.after(0, lambda: self.add_account_row_to_ui(acc_d, "Live ✅"))
                self.after(0, lambda: self.ent_quick_cookie.delete(0, "end"))
                self.log(f"✅ Đã thêm IG (XSMM): @{u}")
            else:
                self.log("❌ Cookie IG không hợp lệ hoặc đã Die!")

        threading.Thread(target=_add, daemon=True).start()

    def batch_import_accounts(self):
        modal = ctk.CTkToplevel(self)
        modal.title("📥 Batch Import Cookie IG (XSMM)")
        modal.geometry("680x460")
        modal.grab_set()
        txt_b = ctk.CTkTextbox(modal, height=340, font=ctk.CTkFont(family="Consolas", size=10))
        txt_b.pack(fill="both", expand=True, padx=20, pady=15)

        def _imp():
            lines = [l.strip().split("|")[0].strip() for l in txt_b.get("1.0", "end").split("\n") if l.strip()]
            modal.destroy()
            proxy = self.get_effective_proxy("")
            for ck in lines:
                p_data = json.loads(check_cookie_ig(ck, proxy))
                if p_data.get("status_check") == "LIVE":
                    u = p_data["form_data"]["username"]
                    uid = str(p_data["form_data"].get("id", "0"))
                    self._db_queue.put(("INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)", (u, ck, proxy, "Live ✅", 0, 999999)))
                    acc_d = {"username": u, "cookie": ck, "proxy": proxy, "id": uid, "coins": 0, "max_jobs": 999999}
                    self.after(0, lambda d=acc_d: self.add_account_row_to_ui(d, "Live ✅"))

        ctk.CTkButton(modal, text="🚀 NẠP DANH SÁCH IG", fg_color="#059669", height=38, command=lambda: threading.Thread(target=_imp, daemon=True).start()).pack(fill="x", padx=20, pady=(0, 15))

    def worker_single_account_loop(self, token, listnv, acc):
        username, ck, id_val = acc["username"], acc["cookie"], acc["id"]
        xsmm = XSMMTool(token)
        ig = INSTAGRAM(ck, self.get_effective_proxy(acc.get("proxy", "")))
        try:
            av, fb_dtsg, st_check, ig_uname = ig.GETINFO()
            if st_check in ["DIE", "CHECKPOINT"]:
                self.single_running_threads[username] = False
                self.queue_row_ui("account", username, status_text=f"Cookie {st_check} ❌", status_color="#dc2626", btn_text="Bắt đầu", btn_color="#2563eb")
                return
            xsmm_uid = xsmm.sync_and_get_xsmm_id(ig_uname or username, av or id_val)
            follow_cache = []
            while self.single_running_threads.get(username, False):
                d_min, d_max, dc_min, dc_max = self.get_delay_settings()
                for job in listnv:
                    if not self.single_running_threads.get(username, False):
                        break
                    tasks, _, matched_uid = xsmm.get_tasks(job, xsmm_uid, fallback_uids=[av, username])
                    for nv in (tasks or []):
                        if not self.single_running_threads.get(username, False):
                            break
                        tid = nv.get("id")
                        t_id = nv.get("target_id", "") or nv.get("idorlink", "")
                        t_url = nv.get("target_url", "") or nv.get("link", "")
                        ok = False
                        if job == "instagram_like":
                            ok = ig.LIKE(av, fb_dtsg, t_id, ck, t_url)
                        elif job == "instagram_follow":
                            ok = ig.FOLLOW(fb_dtsg, t_id, t_url, av=av)
                        elif job == "instagram_comment":
                            ok = ig.COMMENT(av, fb_dtsg, t_id, t_url, nv.get("msg") or ai_generate_unique_comment())
                        if ok:
                            if job == "instagram_follow":
                                follow_cache.append(tid)
                                if len(follow_cache) >= 3:
                                    c_res = gui_nhan_xu(job, follow_cache, matched_uid, cookie_check=ck, xsmm_obj=xsmm)
                                    earned, _ = parse_real_earned_points(c_res, 30)
                                    if earned > 0:
                                        self.update_stats(coins=earned, jobs=len(follow_cache), entity_type="account", entity_key=username)
                                    follow_cache = []
                            else:
                                c_res = gui_nhan_xu(job, [tid], matched_uid, cookie_check=ck, xsmm_obj=xsmm)
                                earned, _ = parse_real_earned_points(c_res, 10)
                                if earned > 0:
                                    self.update_stats(coins=earned, jobs=1, entity_type="account", entity_key=username)
                        if not self.smart_sleep(random.randint(d_min, d_max), username):
                            break
                if not self.smart_sleep(8, username):
                    break
        finally:
            ig.close()
            xsmm.close()
        self.single_running_threads[username] = False
        self.queue_row_ui("account", username, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")


if __name__ == "__main__":
    app = MMOApp()
    app.mainloop()
