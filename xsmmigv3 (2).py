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

CONFIG_FILE = "config_mmo_fb_ig_v6.json"
DB_FILE = "mmo_fb_ig_accounts_v6.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEC_CH_UA_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def init_database():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    cursor = conn.cursor()
    # Bật chế độ WAL giúp đọc/ghi đa luồng cực nhanh, không bị khóa Database
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
                        status TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ttc_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ttc_user TEXT UNIQUE,
                        ttc_token TEXT,
                        coins INTEGER DEFAULT 0,
                        status TEXT
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
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        level TEXT,
                        message TEXT
                    )''')

    for col_sql in [
        "ALTER TABLE accounts ADD COLUMN max_jobs INTEGER DEFAULT 999999;",
        "ALTER TABLE accounts ADD COLUMN coins INTEGER DEFAULT 0;",
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
    if "://" in proxy_str: scheme, proxy_str = proxy_str.split("://", 1)
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
    """Tách chuỗi cookie thành dictionary."""
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
    """Hỗ trợ nhập cả Link bài viết (/p/, /reel/, /tv/), Shortcode hoặc Media ID trực tiếp."""
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
                    if v_int > 0: return v_int, "Thành công"
                except: pass

        if isinstance(response_data.get("data"), dict):
            for key in ['points', 'coins', 'xu', 'reward', 'success_count']:
                val = response_data["data"].get(key)
                if val is not None:
                    try:
                        v_int = int(float(val))
                        if v_int > 0:
                            return (v_int * default_points if key == 'success_count' else v_int), "Thành công"
                    except: pass

        success_cnt = response_data.get('success_count')
        if success_cnt is not None:
            try:
                v_cnt = int(success_cnt)
                if v_cnt > 0: return v_cnt * default_points, "Thành công"
            except: pass

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

class INSTAGRAM:
    """
    Class xử lý Instagram tối ưu hiệu năng:
    Tái sử dụng 1 phiên c_requests.Session() duy nhất cho mỗi tài khoản để tiết kiệm RAM & CPU.
    """
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
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
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
                    j_prof = r_prof.json()
                    uid_found = j_prof.get("data", {}).get("user", {}).get("id")
                    if uid_found and str(uid_found).isdigit():
                        return str(uid_found)
            except Exception:
                pass

        url_to_fetch = target_url if (target_url and target_url.startswith("http")) else (f"https://www.instagram.com/{uname}/" if uname else "")
        if url_to_fetch:
            try:
                html = self.session.get(url_to_fetch, headers={'cookie': self.cookies_str, 'user-agent': USER_AGENT}, impersonate="chrome120", timeout=10, max_redirects=5).text
                m = re.search(r'"profile_id":"(\d+)"', html) or re.search(r'"user_id":"(\d+)"', html) or re.search(r'profilePage_(\d+)', html) or re.search(r'"pk":"(\d+)"', html)
                if m:
                    return m.group(1)
            except Exception:
                pass
        return ""

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd_token=""):
        media_id = self.resolve_media_id_full(post_id, link)
        if not media_id or not str(media_id).isdigit():
            self.last_error = f"Không lấy được media_id từ ({post_id} | {link})"
            return False

        ref_url = link if (link and link.startswith("http")) else "https://www.instagram.com/"
        headers = get_ig_headers(self.cookies_str, self.csrftoken, ref_url)

        try:
            res_v1 = self.session.post(
                f"https://www.instagram.com/api/v1/web/likes/{media_id}/like/",
                headers=headers,
                data={},
                impersonate="chrome120",
                timeout=12
            )
            if res_v1.status_code == 200:
                j1 = res_v1.json()
                if j1.get("status") == "ok":
                    return True
                self.last_error = j1.get("message") or str(j1)[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        try:
            actor_id = str(av or self.ds_user_id or "0")
            variables = {
                "input": {
                    "actor_id": actor_id,
                    "client_mutation_id": str(random.randint(1000000, 9999999)),
                    "container_module": "single_post",
                    "media_id": str(media_id)
                }
            }
            gql_data = {
                "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
                "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
                "__rev": "1046913831", "__comet_req": "7",
                "fb_dtsg": dtsg, "jazoest": self.jazoest, "lsd": self.lsd,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
                "server_timestamps": "true",
                "doc_id": "27182485238052618",
                "variables": json.dumps(variables)
            }
            res_gql = self.session.post(
                "https://www.instagram.com/api/graphql",
                headers=headers,
                data=gql_data,
                impersonate="chrome120",
                timeout=12
            )
            if res_gql.status_code == 200:
                jg = res_gql.json()
                if "errors" not in jg and ("data" in jg or jg.get("status") == "ok"):
                    return True
                self.last_error = str(jg.get("errors") or jg.get("message") or "GraphQL Like Block")[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        try:
            mob_headers = {
                'User-Agent': 'Instagram 269.0.0.18.75 Android (28/9; 480dpi; 1080x1920; Xiaomi; Redmi Note 7; lavender; qcom; sm6150; en_US; 317822529)',
                'Accept-Language': 'vi-VN, en-US',
                'X-IG-Capabilities': '3brTvx0=',
                'X-IG-Connection-Type': 'WIFI',
                'X-IG-App-ID': '1217981644879628',
                'X-CSRFToken': self.csrftoken,
                'Cookie': self.cookies_str,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            }
            res_mob = self.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/like/",
                headers=mob_headers,
                data={'module_name': 'feed_timeline', 'media_id': str(media_id)},
                impersonate="chrome120",
                timeout=12
            )
            if res_mob.status_code == 200 and res_mob.json().get("status") == "ok":
                return True
        except Exception:
            pass

        return False

    def FOLLOW(self, dtsg, target_user_id, target_url="", av=""):
        target_uid = self.resolve_user_id_full(target_user_id, target_url)
        if not target_uid or not str(target_uid).isdigit():
            self.last_error = f"Không lấy được UID từ ({target_user_id} | {target_url})"
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
                headers=headers,
                data=data_v1,
                impersonate="chrome120",
                timeout=12
            )
            if res_v1.status_code == 200:
                j1 = res_v1.json()
                f_status = j1.get("friendship_status", {})
                if j1.get("status") == "ok" and (f_status.get("following") is True or f_status.get("outgoing_request") is True or "friendship_status" in j1):
                    return True
                self.last_error = j1.get("message") or str(j1)[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        try:
            actor_id = str(av or self.ds_user_id or "0")
            variables = {
                "target_user_id": str(target_uid),
                "container_module": "profile",
                "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link"
            }
            gql_data = {
                "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
                "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
                "__rev": "1046917461", "__comet_req": "7",
                "fb_dtsg": dtsg, "jazoest": self.jazoest, "lsd": self.lsd,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "usePolarisFollowMutation",
                "server_timestamps": "true",
                "doc_id": "26508036048874888",
                "variables": json.dumps(variables)
            }
            res_gql = self.session.post(
                "https://www.instagram.com/api/graphql",
                headers=headers,
                data=gql_data,
                impersonate="chrome120",
                timeout=12
            )
            if res_gql.status_code == 200:
                jg = res_gql.json()
                if "errors" not in jg and ("data" in jg or jg.get("status") == "ok"):
                    return True
                self.last_error = str(jg.get("errors") or jg.get("message") or "GraphQL Follow Block")[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        return False

    def COMMENT(self, av, dtsg, target_id, target_url, comment_content):
        media_id = self.resolve_media_id_full(target_id, target_url)
        if not media_id or not str(media_id).isdigit():
            self.last_error = f"Không lấy được media_id từ ({target_id} | {target_url})"
            return False

        ref_url = target_url if (target_url and target_url.startswith("http")) else "https://www.instagram.com/"
        headers = get_ig_headers(self.cookies_str, self.csrftoken, ref_url)

        try:
            res_v1 = self.session.post(
                f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/",
                headers=headers,
                data={"comment_text": comment_content},
                impersonate="chrome120",
                timeout=12
            )
            if res_v1.status_code == 200:
                j1 = res_v1.json()
                if j1.get("status") == "ok":
                    return True
                self.last_error = j1.get("message") or str(j1)[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        try:
            actor_id = str(av or self.ds_user_id or "0")
            variables = {
                "connections": [
                    f'client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:"{media_id}",sort_order:"popular")'
                ],
                "data": {"comment_text": comment_content, "media_id": str(media_id)}
            }
            gql_data = {
                "av": actor_id, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
                "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
                "__rev": "1046917461", "__comet_req": "7",
                "fb_dtsg": dtsg, "jazoest": self.jazoest, "lsd": self.lsd,
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
                "server_timestamps": "true",
                "doc_id": "27261905640092552",
                "variables": json.dumps(variables, ensure_ascii=False)
            }
            res_gql = self.session.post(
                "https://www.instagram.com/api/graphql",
                headers=headers,
                data=gql_data,
                impersonate="chrome120",
                timeout=12
            )
            if res_gql.status_code == 200:
                jg = res_gql.json()
                if "errors" not in jg and ("data" in jg or jg.get("status") == "ok"):
                    return True
                self.last_error = str(jg.get("errors") or jg.get("message") or "GraphQL Comment Block")[:40]
        except Exception as e:
            self.last_error = str(e)[:40]

        return False

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

    def get_user_info(self):
        url = f"{self.base_url}/user"
        try:
            response = self.session.get(url, timeout=20)
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
            response = self.session.post(url, json=payload, timeout=20)
            res_json = response.json()
            if response.status_code in [200, 201] and ("id" in res_json or "account_id" in res_json or res_json.get("success")):
                return True
        except: pass
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
            link_account = f"https://www.instagram.com/{clean_user}"
            payload = {
                "type": "instagram",
                "link_account": link_account
            }
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
                (f"{self.base_url}/tasks2", {"type": job_type, "account_id": curr_uid, "typejob": typejob}),
                (f"{self.base_url}/{job_type}", {"uid": curr_uid})
            ]

            for url, params in endpoints_to_try:
                try:
                    response = self.session.get(url, params=params, timeout=12)
                    res = response.json()

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

        return [], (last_error_msg if last_error_msg else "Hết job hoặc tài khoản chưa liên kết trên web"), str(uid)

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
            return {"is_timeout": True, "message": f"Đã gửi duyệt {len(payload['task_id'])} job thành công"}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Thất bại"}


class TuongTacCheoTool:
    """
    Class xử lý chuyên sâu Tương Tác Chéo (tuongtaccheo.com) cho Facebook Page:
    - Đăng nhập bằng access_token (logintoken.php)
    - Đặt cấu hình Nick/Page chạy (cauhinh/datnick.php)
    - Lấy job & Nhận tiền: Like post, Like Page, Follow/Sub, Comment, Share
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

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass

    def login(self):
        """Đăng nhập TTC qua Access Token để lấy PHPSESSID"""
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
                return True, self.username, self.coins, "OK"
            return False, "", 0, str(j.get("mess") or "Token TTC không hợp lệ")
        except Exception as e:
            return False, "", 0, f"Lỗi kết nối TTC: {str(e)[:35]}"

    def dat_nick(self, page_id):
        """Đặt Page ID làm nick chạy chính trên TTC (cauhinh/datnick.php)"""
        page_id_str = str(page_id).strip()
        if self.current_configured_uid == page_id_str:
            return True, "Đã cấu hình sẵn"
        try:
            res = self.session.post(
                f"{self.base_url}/cauhinh/datnick.php",
                headers=self.headers,
                data={"iddat[]": page_id_str, "loai": "fb"},
                impersonate="chrome120",
                timeout=12
            )
            txt = res.text.strip()
            if txt == "1" or '"1"' in txt or "success" in txt.lower():
                self.current_configured_uid = page_id_str
                return True, "Đặt nick thành công"
            return False, f"Chưa thêm Page {page_id_str} vào Cấu hình TTC (Mã: {txt[:20]})"
        except Exception as e:
            return False, str(e)[:35]

    def get_tasks(self, job_type):
        """
        Lấy danh sách nhiệm vụ từ TTC theo loại:
        - facebook_like: /kiemtien/getpost.php
        - facebook_likepage: /kiemtien/likepagecheo/getpost.php
        - facebook_follow: /kiemtien/subcheo/getpost.php
        - facebook_comment: /kiemtien/cmtcheo/getpost.php
        - facebook_share: /kiemtien/sharecheo/getpost.php
        """
        endpoint_map = {
            "facebook_like": "/kiemtien/getpost.php",
            "facebook_likepage": "/kiemtien/likepagecheo/getpost.php",
            "facebook_follow": "/kiemtien/subcheo/getpost.php",
            "facebook_comment": "/kiemtien/cmtcheo/getpost.php",
            "facebook_share": "/kiemtien/sharecheo/getpost.php"
        }
        ep = endpoint_map.get(job_type, "/kiemtien/getpost.php")
        try:
            res = self.session.get(
                f"{self.base_url}{ep}",
                headers=self.headers,
                impersonate="chrome120",
                timeout=12
            )
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                norm_tasks = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    tid = str(item.get("idpost") or item.get("id") or "")
                    link = str(item.get("link") or tid)
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
                        "msg": cmt_msg,
                        "points": 300 if "like" in job_type else 600
                    })
                return norm_tasks, "OK"
            return [], "Hết job hoặc đang countdown"
        except Exception as e:
            return [], str(e)[:30]

    def claim_reward(self, job_type, task_id):
        """Gửi nhận xu trên TTC cho từng loại job"""
        claim_map = {
            "facebook_like": "/kiemtien/nhantien.php",
            "facebook_likepage": "/kiemtien/likepagecheo/nhantien.php",
            "facebook_follow": "/kiemtien/subcheo/nhantien.php",
            "facebook_comment": "/kiemtien/cmtcheo/nhantien.php",
            "facebook_share": "/kiemtien/sharecheo/nhantien.php"
        }
        ep = claim_map.get(job_type, "/kiemtien/nhantien.php")
        id_val = ",".join(str(x) for x in task_id) if isinstance(task_id, list) else str(task_id)
        try:
            res = self.session.post(
                f"{self.base_url}{ep}",
                headers=self.headers,
                data={"id": id_val},
                impersonate="chrome120",
                timeout=15
            )
            j = res.json()
            if isinstance(j, dict):
                if "mess" in j and ("thành công" in str(j["mess"]).lower() or "cộng" in str(j["mess"]).lower()):
                    m_xu = re.search(r'(\d+)\s*xu', str(j["mess"]).replace(",", "").replace(".", ""), re.I)
                    earned = int(m_xu.group(1)) if m_xu else 300
                    if j.get("sodu"):
                        self.coins = int(j["sodu"])
                    return earned, str(j["mess"])
                if j.get("sodu"):
                    self.coins = int(j["sodu"])
                    return 300, "Nhận xu thành công"
                return 0, str(j.get("error") or j.get("mess") or "Từ chối duyệt")
            return 0, "Phản hồi TTC không hợp lệ"
        except Exception as e:
            return 0, str(e)[:35]


def check_cookie_ig(cookie, proxy=None):
    """Hàm Check Live Cookie IG chuẩn xác bằng curl_cffi"""
    if not cookie or not cookie.strip():
        return json.dumps({"status_check": "DIE", "error": "Cookie trống"})

    ig_client = INSTAGRAM(cookie, proxy)
    try:
        uid, fb_dtsg, status_code_str, uname = ig_client.GETINFO()
    finally:
        ig_client.close()

    if status_code_str == "LIVE" and uid and uname:
        return json.dumps({
            "status_check": "LIVE",
            "form_data": {"username": uname, "id": str(uid), "fb_dtsg": fb_dtsg}
        })
    elif status_code_str == "CHECKPOINT":
        return json.dumps({"status_check": "CHECKPOINT", "error": "Checkpoint / Challenge"})
    elif status_code_str == "PROXY_ERR":
        return json.dumps({"status_check": "PROXY_ERR", "error": "Lỗi kết nối Proxy / Mạng"})

    return json.dumps({"status_check": "DIE", "error": "Cookie Die"})


def scan_facebook_account_and_pages(cookie="", access_token="", proxy=None):
    """
    Quét thông tin Tài khoản FB Mẹ & Toàn bộ danh sách Page Con từ cả Cookie và Token (EAAG/EAAD/...).
    Trả về: (fb_info_dict, pages_list)
    """
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
        # 1. Nếu có Access Token (EAAG/EAAD/...), ưu tiên quét qua Graph API để lấy Page Token chuẩn
        if access_token:
            try:
                r_me = session.get(
                    f"https://graph.facebook.com/v18.0/me?fields=id,name&access_token={access_token}",
                    timeout=10
                ).json()
                if r_me.get("id"):
                    fb_uid = str(r_me["id"])
                    fb_name = str(r_me.get("name") or fb_name)

                r_acc = session.get(
                    f"https://graph.facebook.com/v18.0/me/accounts?fields=id,name,access_token&limit=100&access_token={access_token}",
                    timeout=12
                ).json()
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

        # 2. Nếu có Cookie, quét thêm trên giao diện Web để lấy đủ các Page Profile (New Pages Experience)
        if cookie:
            try:
                res = session.get(
                    "https://www.facebook.com/bookmarks/pages",
                    headers={"User-Agent": USER_AGENT, "Cookie": cookie},
                    impersonate="chrome120",
                    timeout=12,
                    max_redirects=5
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

                # Quét thêm các Profile Page (additional_profile_plus)
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
        "status": "Live ✅" if (fb_uid and (pages_dict or cookie or access_token)) else "Chưa rõ"
    }
    return fb_info, list(pages_dict.values())


def scan_facebook_pages(cookie, proxy=None):
    _, pages_list = scan_facebook_account_and_pages(cookie=cookie, access_token="", proxy=proxy)
    return pages_list


def _build_page_cookie(parent_cookie, page_id):
    """Gắn i_user={page_id} vào Cookie FB Mẹ để thao tác dưới tư cách Page Profile"""
    base_ck = re.sub(r';?\s*i_user=\d+', '', (parent_cookie or "").strip()).strip(';')
    if base_ck and page_id:
        return f"{base_ck}; i_user={page_id}"
    return base_ck


def _get_fb_dtsg(session, page_cookie, page_id):
    """Lấy fb_dtsg dưới quyền Page Profile (i_user)"""
    try:
        html = session.get(
            "https://m.facebook.com/",
            headers={"User-Agent": USER_AGENT, "Cookie": page_cookie},
            impersonate="chrome120",
            timeout=10
        ).text
        m = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"\}', html) or re.search(r'name="fb_dtsg" value="([^"]+)"', html)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def fb_page_like(target_url, page_token, proxy=None, session=None, page_id="", parent_cookie="", target_id=""):
    """Thực hiện Like bài viết / Like Fanpage bằng Token Graph API hoặc Cookie i_user GraphQL"""
    own_sess = session is None
    sess = session or c_requests.Session()
    if proxies := format_proxy(proxy):
        sess.proxies = proxies

    obj_id = str(target_id or "").strip()
    if not obj_id and target_url:
        m = re.search(r'(?:posts/|videos/|photo\.php\?fbid=|story_fbid=|/)(\d{8,})', str(target_url))
        if m:
            obj_id = m.group(1)

    try:
        # Tầng 1: Graph API nếu có Token EAA...
        if page_token and str(page_token).startswith("EAA"):
            target_ep = f"https://graph.facebook.com/v18.0/{obj_id}/likes" if obj_id else "https://graph.facebook.com/v18.0/me/likes"
            payload = {"access_token": page_token}
            if not obj_id:
                payload["object"] = target_url
            res = sess.post(target_ep, data=payload, timeout=10)
            if "true" in res.text.lower() or '"success":true' in res.text.lower() or '"id"' in res.text.lower():
                return json.dumps({"success": True})

        # Tầng 2: Cookie Web GraphQL với i_user=page_id
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
                        "feedback_reaction": 1,
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

        return json.dumps({"error": "Không thể Like (Kiểm tra Token/Cookie Page)"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try: sess.close()
            except: pass


def fb_page_follow(target_id, page_token, proxy=None, session=None, page_id="", parent_cookie=""):
    """Thực hiện Follow / Like Page bằng Token Graph API hoặc Cookie i_user GraphQL"""
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
        # Tầng 1: Graph API
        if page_token and str(page_token).startswith("EAA") and clean_tid:
            res = sess.post(
                f"https://graph.facebook.com/v18.0/{clean_tid}/subscribers",
                data={"access_token": page_token},
                timeout=10
            )
            if "true" in res.text.lower() or '"success":true' in res.text.lower():
                return json.dumps({"success": True})

        # Tầng 2: Cookie Web GraphQL ActorSubscribeMutation / PageLike
        raw_ck = parent_cookie if parent_cookie else (page_token if "c_user=" in str(page_token) else "")
        if raw_ck and page_id and clean_tid:
            pg_ck = _build_page_cookie(raw_ck, page_id)
            dtsg = _get_fb_dtsg(sess, pg_ck, page_id)
            if dtsg:
                variables = {
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
                        "variables": json.dumps(variables)
                    },
                    impersonate="chrome120",
                    timeout=10
                )
                if gql_res.status_code == 200 and '"errors"' not in gql_res.text:
                    return json.dumps({"success": True})

        return json.dumps({"error": "Follow/Sub thất bại"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try: sess.close()
            except: pass


def fb_page_comment(target_id_or_post, comment_text, page_token, proxy=None, session=None, page_id="", parent_cookie=""):
    """Thực hiện Comment bằng Token Graph API hoặc Cookie i_user GraphQL"""
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
        # Tầng 1: Graph API
        if page_token and str(page_token).startswith("EAA") and clean_tid:
            res = sess.post(
                f"https://graph.facebook.com/v18.0/{clean_tid}/comments",
                data={"access_token": page_token, "message": comment_text},
                timeout=10
            )
            if '"id"' in res.text:
                return json.dumps({"id": clean_tid, "success": True})

        # Tầng 2: Cookie Web GraphQL
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
                    impersonate="chrome120",
                    timeout=10
                )
                if gql_res.status_code == 200 and '"errors"' not in gql_res.text:
                    return json.dumps({"id": clean_tid, "success": True})

        return json.dumps({"error": "Comment thất bại"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if own_sess:
            try: sess.close()
            except: pass


def follow(target_id, cookie, csrftoken, profile_url="", proxy=None, dtsg=""):
    ig_client = INSTAGRAM(cookie, proxy)
    try:
        ok = ig_client.FOLLOW(dtsg, target_id, profile_url)
        return json.dumps({"status": "ok"}) if ok else json.dumps({"error": ig_client.last_error or "IG Follow Failed"})
    finally:
        ig_client.close()

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None, av="", dtsg=""):
    ig_client = INSTAGRAM(cookie, proxy)
    try:
        ok = ig_client.LIKE(av, dtsg, mediaid, cookie, link_job, "")
        return json.dumps({"status": "ok"}) if ok else json.dumps({"status": "error", "message": ig_client.last_error or "IG Like Failed"})
    finally:
        ig_client.close()

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None, av="", dtsg=""):
    ig_client = INSTAGRAM(cookie, proxy)
    try:
        ok = ig_client.COMMENT(av, dtsg, mediaid, link_job, text)
        return json.dumps({"status": "ok"}) if ok else json.dumps({"error": ig_client.last_error or "IG Comment Failed"})
    finally:
        ig_client.close()
class MMOApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Enterprise Automation Pro - MMO Console (IG / XSMM / Tương Tác Chéo Page Engine)")
        self.geometry("1460x880")
        self.configure(fg_color="#f8fafc")

        init_database()
        self.is_running = False
        self.total_coins = 0
        self.success_jobs = 0
        self.start_time = None
        self.lock = threading.Lock()

        self.acc_rows = {}
        self.page_rows = {}
        self.fb_parent_sections = {}
        self.ttc_accounts = {}
        self.ttc_rows_ui = {}
        # Khoá độc quyền theo từng Acc TTC: Đảm bảo 1 Acc TTC chỉ chạy đúng 1 luồng FB duy nhất
        self.ttc_account_locks = {}
        self.ttc_clients_cache = {}
        self.single_running_threads = {}

        # Bộ nhớ đệm cấu hình thuần Python (RAM Cache)
        self.cfg_cache = {
            "token": "",
            "global_proxy": "",
            "delay_min": 10,
            "delay_max": 15,
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

        self.btn_tab_fb = ctk.CTkButton(self.top_nav, text="📱 Quản lý Instagram", fg_color="#2563eb", hover_color="#1d4ed8", text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("accounts"))
        self.btn_tab_fb.grid(row=0, column=0, padx=10, pady=9, sticky="w")

        self.btn_tab_page = ctk.CTkButton(self.top_nav, text="📘 FB & Page (Tương Tác Chéo / XSMM)", fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("pages"))
        self.btn_tab_page.grid(row=0, column=1, padx=4, pady=9, sticky="w")

        self.btn_tab_coin = ctk.CTkButton(self.top_nav, text="📊 Dashboard & Logs", fg_color="#f1f5f9", hover_color="#e2e8f0", text_color="#475569", font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8, command=lambda: self.switch_tab("dashboard"))
        self.btn_tab_coin.grid(row=0, column=2, padx=4, pady=9, sticky="w")

        self.frame_top_proxy = ctk.CTkFrame(self.top_nav, fg_color="transparent")
        self.frame_top_proxy.grid(row=0, column=3, padx=12, pady=9, sticky="e")

        ctk.CTkLabel(self.frame_top_proxy, text="🌐 Proxy xoay chung:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").pack(side="left", padx=(0, 6))
        self.ent_global_proxy = ctk.CTkEntry(
            self.frame_top_proxy,
            placeholder_text="ip:port:user:pass (Dùng chung cho mọi Cookie)...",
            width=280,
            height=34,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#f8fafc",
            border_color="#cbd5e1"
        )
        self.ent_global_proxy.pack(side="left", padx=(0, 6))
        self.ent_global_proxy.bind("<KeyRelease>", lambda e: self._sync_proxy_cache_from_top_bar())
        self.ent_global_proxy.bind("<FocusOut>", lambda e: self._sync_proxy_cache_from_top_bar())

        ctk.CTkButton(
            self.frame_top_proxy,
            text="💾 Lưu Proxy",
            width=85,
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            command=self.apply_global_proxy_now
        ).pack(side="left")

        self.btn_config_chung = ctk.CTkButton(self.top_nav, text="⚙️ Cấu hình chung", fg_color="#0f172a", hover_color="#1e293b", text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), height=36, corner_radius=8, command=self.open_config_modal)
        self.btn_config_chung.grid(row=0, column=4, padx=(4, 16), pady=9, sticky="e")

        # ---------------- MAIN CONTENT AREA ----------------
        self.main_content = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

        # Các biến lưu trữ cấu hình
        self.ent_token = ctk.CTkEntry(self)
        self.ent_delay = ctk.CTkEntry(self)
        self.ent_delay_min = ctk.CTkEntry(self)
        self.ent_delay_max = ctk.CTkEntry(self)
        self.ent_delay_coin_min = ctk.CTkEntry(self)
        self.ent_delay_coin_max = ctk.CTkEntry(self)
        self.ent_threads = ctk.CTkEntry(self)

        self.chk_ig_like = ctk.CTkCheckBox(self, text="Like")
        self.chk_ig_follow = ctk.CTkCheckBox(self, text="Follow")
        self.chk_ig_cmt = ctk.CTkCheckBox(self, text="Comment")
        self.chk_ig_like.select(); self.chk_ig_follow.select(); self.chk_ig_cmt.select()

        self.chk_fb_like = ctk.CTkCheckBox(self, text="Like Post")
        self.chk_fb_likepage = ctk.CTkCheckBox(self, text="Like Page")
        self.chk_fb_follow = ctk.CTkCheckBox(self, text="Follow/Sub")
        self.chk_fb_cmt = ctk.CTkCheckBox(self, text="Comment")
        self.chk_fb_like.select(); self.chk_fb_likepage.select(); self.chk_fb_follow.select(); self.chk_fb_cmt.select()

        self.ent_delay.insert(0, "10")
        self.ent_delay_min.insert(0, "10")
        self.ent_delay_max.insert(0, "15")
        self.ent_delay_coin_min.insert(0, "3")
        self.ent_delay_coin_max.insert(0, "5")
        self.ent_threads.insert(0, "5")

        self.setup_tab_accounts()
        self.setup_tab_fb_pages()
        self.setup_tab_dashboard()

        # ---------------- BOTTOM STATUS BAR ----------------
        self.status_bar = ctk.CTkFrame(self, height=36, fg_color="#ffffff", corner_radius=0, border_width=1, border_color="#e2e8f0")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(3, weight=1)

        self.lbl_footer_stats = ctk.CTkLabel(self.status_bar, text="Tổng tài khoản: 0 | Đang chạy: 0 | Live: 0 | Die: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155")
        self.lbl_footer_stats.grid(row=0, column=0, padx=16, pady=6, sticky="w")

        self.lbl_xsmm_balance = ctk.CTkLabel(self.status_bar, text="💰 TỔNG XU KIẾM ĐƯỢC: 0 XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669")
        self.lbl_xsmm_balance.grid(row=0, column=1, padx=16, pady=6, sticky="w")

        self.lbl_status_uptime = ctk.CTkLabel(self.status_bar, text="⏱️ UPTIME: 00:00:00 | Phím tắt: Ctrl+F5 (Start), Ctrl+F6 (Kill)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b")
        self.lbl_status_uptime.grid(row=0, column=3, padx=16, pady=6, sticky="e")

        self.load_config()
        self.sync_cache_from_ui()
        self.load_accounts_from_db()
        self.load_ttc_accounts_from_db()
        self.load_fb_pages_from_db()
        self.update_uptime_loop()
        self._process_ui_queue_loop()
        self.init_global_hotkeys()
        self.switch_tab("pages")

    # ---------------- HỆ THỐNG ĐỒNG BỘ GIAO DIỆN & DB BẤT ĐỒNG BỘ ----------------
    def _sync_proxy_cache_from_top_bar(self):
        try:
            self.cfg_cache["global_proxy"] = self.ent_global_proxy.get().strip()
        except Exception:
            pass

    def sync_cache_from_ui(self):
        try: d_min = max(1, int(self.ent_delay_min.get().strip()))
        except: d_min = 10
        try: d_max = max(d_min, int(self.ent_delay_max.get().strip()))
        except: d_max = max(d_min, 15)
        try: dc_min = max(1, int(self.ent_delay_coin_min.get().strip()))
        except: dc_min = 3
        try: dc_max = max(dc_min, int(self.ent_delay_coin_max.get().strip()))
        except: dc_max = max(dc_min, 5)
        try: th_cnt = max(1, min(50, int(self.ent_threads.get().strip())))
        except: th_cnt = 5

        old_th = self.cfg_cache.get("threads", 5)
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

    def queue_row_ui(self, row_type, key, status_text=None, status_color=None, coin_text=None, btn_text=None, btn_color=None, var_val=None, id_text=None):
        if row_type == "account":
            row_dict = self.acc_rows
        elif row_type == "page":
            row_dict = self.page_rows
        else:
            row_dict = self.ttc_rows_ui

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
            self._pending_ui_updates[composite_key] = cur

    def _process_ui_queue_loop(self):
        logs_batch = []
        while not self._log_queue.empty():
            try:
                logs_batch.append(self._log_queue.get_nowait())
            except queue.Empty:
                break

        if logs_batch:
            try:
                self.txt_log.insert("end", "".join(logs_batch))
                line_count = int(self.txt_log.index("end-1c").split(".")[0])
                if line_count > 600:
                    self.txt_log.delete("1.0", f"{line_count - 500}.0")
                self.txt_log.see("end")
            except Exception:
                pass

        if self._balance_dirty:
            self._balance_dirty = False
            try:
                self.lbl_xsmm_balance.configure(text=f"💰 TỔNG XU KIẾM ĐƯỢC: {self.total_coins} XU")
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
                if row_type == "account":
                    row_dict = self.acc_rows
                elif row_type == "page":
                    row_dict = self.page_rows
                else:
                    row_dict = self.ttc_rows_ui

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
        if global_px:
            return global_px
        return (account_proxy or "").strip()

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
        if g_px:
            self.log(f"🌐 Đã lưu và áp dụng Proxy xoay chung cho tất cả tài khoản: {g_px}")
        else:
            self.log("🌐 Đã xóa Proxy xoay chung (Chạy mạng trực tiếp hoặc proxy riêng).")

    def get_delay_settings(self):
        return (
            self.cfg_cache.get("delay_min", 10),
            self.cfg_cache.get("delay_max", 15),
            self.cfg_cache.get("delay_coin_min", 3),
            self.cfg_cache.get("delay_coin_max", 5)
        )

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
        modal.title("⚙️ Cấu hình chung & Chọn loại Job (IG / TTC FB Page)")
        modal.geometry("620x780")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="🔑 XSMM ACCESS TOKEN (DÙNG KHI CHẠY CHẾ ĐỘ XSMM)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(14, 4))
        ent_t = ctk.CTkEntry(modal, placeholder_text="Nhập Bearer Token XSMM...", height=34, font=ctk.CTkFont(size=11), fg_color="#f8fafc", border_color="#cbd5e1")
        ent_t.pack(fill="x", padx=24, pady=(0, 8))
        try:
            if current_t := self.ent_token.get(): ent_t.insert(0, current_t)
        except: pass

        ctk.CTkLabel(modal, text="🌐 PROXY XOAY DÙNG CHUNG (ÁP DỤNG CHO TẤT CẢ COOKIES)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669").pack(anchor="w", padx=24, pady=(4, 4))
        ent_g_proxy = ctk.CTkEntry(modal, placeholder_text="VD: ip:port:user:pass (Để trống nếu không dùng)", height=34, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#f8fafc", border_color="#cbd5e1")
        ent_g_proxy.pack(fill="x", padx=24, pady=(0, 8))
        try:
            if current_gp := self.ent_global_proxy.get().strip():
                ent_g_proxy.insert(0, current_gp)
        except: pass

        ctk.CTkLabel(modal, text="🎯 CHỌN LOẠI JOB INSTAGRAM & FACEBOOK PAGE (TTC / XSMM)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(4, 4))
        frame_job_choices = ctk.CTkFrame(modal, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#e2e8f0")
        frame_job_choices.pack(fill="x", padx=24, pady=(0, 8))
        frame_job_choices.grid_columnconfigure((0, 1), weight=1)

        modal_chk_like = ctk.CTkCheckBox(frame_job_choices, text="IG Like", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_like.grid(row=0, column=0, sticky="w", padx=16, pady=6)
        if self.chk_ig_like.get(): modal_chk_like.select()

        modal_chk_follow = ctk.CTkCheckBox(frame_job_choices, text="IG Follow (Gom 3 job)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_follow.grid(row=1, column=0, sticky="w", padx=16, pady=6)
        if self.chk_ig_follow.get(): modal_chk_follow.select()

        modal_chk_cmt = ctk.CTkCheckBox(frame_job_choices, text="IG Comment", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#2563eb")
        modal_chk_cmt.grid(row=2, column=0, sticky="w", padx=16, pady=6)
        if self.chk_ig_cmt.get(): modal_chk_cmt.select()

        modal_fb_like = ctk.CTkCheckBox(frame_job_choices, text="FB Page: Like Bài Viết", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0284c7")
        modal_fb_like.grid(row=0, column=1, sticky="w", padx=16, pady=6)
        if self.chk_fb_like.get(): modal_fb_like.select()

        modal_fb_likepage = ctk.CTkCheckBox(frame_job_choices, text="FB Page: Like Fanpage (TTC)", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0284c7")
        modal_fb_likepage.grid(row=1, column=1, sticky="w", padx=16, pady=6)
        if self.chk_fb_likepage.get(): modal_fb_likepage.select()

        modal_fb_follow = ctk.CTkCheckBox(frame_job_choices, text="FB Page: Follow / Sub Chéo", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0284c7")
        modal_fb_follow.grid(row=2, column=1, sticky="w", padx=16, pady=6)
        if self.chk_fb_follow.get(): modal_fb_follow.select()

        modal_fb_cmt = ctk.CTkCheckBox(frame_job_choices, text="FB Page: Bình Luận Chéo", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0284c7")
        modal_fb_cmt.grid(row=3, column=1, sticky="w", padx=16, pady=(6, 10))
        if self.chk_fb_cmt.get(): modal_fb_cmt.select()

        ctk.CTkLabel(modal, text="⏱️ CẤU HÌNH DELAY THAO TÁC & NHẬN XU (GIÂY)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(4, 4))

        row_action_delay = ctk.CTkFrame(modal, fg_color="transparent")
        row_action_delay.pack(fill="x", padx=24, pady=4)
        row_action_delay.grid_columnconfigure((0, 1), weight=1)

        fa1 = ctk.CTkFrame(row_action_delay, fg_color="transparent")
        fa1.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(fa1, text="Delay thao tác Tối thiểu (Min - giây):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155").pack(anchor="w")
        ent_d_min = ctk.CTkEntry(fa1, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_d_min.pack(fill="x", pady=(2, 0))
        ent_d_min.insert(0, self.ent_delay_min.get())

        fa2 = ctk.CTkFrame(row_action_delay, fg_color="transparent")
        fa2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(fa2, text="Delay thao tác Tối đa (Max - giây):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155").pack(anchor="w")
        ent_d_max = ctk.CTkEntry(fa2, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_d_max.pack(fill="x", pady=(2, 0))
        ent_d_max.insert(0, self.ent_delay_max.get())

        row_coin_delay = ctk.CTkFrame(modal, fg_color="transparent")
        row_coin_delay.pack(fill="x", padx=24, pady=6)
        row_coin_delay.grid_columnconfigure((0, 1), weight=1)

        fc1 = ctk.CTkFrame(row_coin_delay, fg_color="transparent")
        fc1.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        ctk.CTkLabel(fc1, text="Delay nhận xu Tối thiểu (Min - giây):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#059669").pack(anchor="w")
        ent_dc_min = ctk.CTkEntry(fc1, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_dc_min.pack(fill="x", pady=(2, 0))
        ent_dc_min.insert(0, self.ent_delay_coin_min.get())

        fc2 = ctk.CTkFrame(row_coin_delay, fg_color="transparent")
        fc2.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(fc2, text="Delay nhận xu Tối đa (Max - giây):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#059669").pack(anchor="w")
        ent_dc_max = ctk.CTkEntry(fc2, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_dc_max.pack(fill="x", pady=(2, 0))
        ent_dc_max.insert(0, self.ent_delay_coin_max.get())

        row_threads = ctk.CTkFrame(modal, fg_color="transparent")
        row_threads.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(row_threads, text="Số luồng chạy & Check Live đồng thời (Threads):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#334155").pack(anchor="w")
        ent_th = ctk.CTkEntry(row_threads, height=34, fg_color="#f8fafc", border_color="#cbd5e1")
        ent_th.pack(fill="x", pady=(2, 0))
        ent_th.insert(0, self.ent_threads.get())

        def save_modal():
            try: d_min_v = max(1, int(ent_d_min.get().strip()))
            except: d_min_v = 10
            try: d_max_v = max(d_min_v, int(ent_d_max.get().strip()))
            except: d_max_v = max(d_min_v, 15)
            try: dc_min_v = max(1, int(ent_dc_min.get().strip()))
            except: dc_min_v = 3
            try: dc_max_v = max(dc_min_v, int(ent_dc_max.get().strip()))
            except: dc_max_v = max(dc_min_v, 5)

            self.ent_token.delete(0, "end"); self.ent_token.insert(0, ent_t.get().strip())
            self.ent_global_proxy.delete(0, "end"); self.ent_global_proxy.insert(0, ent_g_proxy.get().strip())
            self.ent_delay.delete(0, "end"); self.ent_delay.insert(0, str(d_min_v))
            self.ent_delay_min.delete(0, "end"); self.ent_delay_min.insert(0, str(d_min_v))
            self.ent_delay_max.delete(0, "end"); self.ent_delay_max.insert(0, str(d_max_v))
            self.ent_delay_coin_min.delete(0, "end"); self.ent_delay_coin_min.insert(0, str(dc_min_v))
            self.ent_delay_coin_max.delete(0, "end"); self.ent_delay_coin_max.insert(0, str(dc_max_v))
            self.ent_threads.delete(0, "end"); self.ent_threads.insert(0, ent_th.get().strip() or "5")

            for src_chk, dst_chk in [
                (modal_chk_like, self.chk_ig_like),
                (modal_chk_follow, self.chk_ig_follow),
                (modal_chk_cmt, self.chk_ig_cmt),
                (modal_fb_like, self.chk_fb_like),
                (modal_fb_likepage, self.chk_fb_likepage),
                (modal_fb_follow, self.chk_fb_follow),
                (modal_fb_cmt, self.chk_fb_cmt)
            ]:
                if src_chk.get(): dst_chk.select()
                else: dst_chk.deselect()

            self.apply_global_proxy_now()
            modal.destroy()
            self.log(f"⚙️ Đã lưu cấu hình! Delay thao tác: {d_min_v}-{d_max_v}s | Delay nhận xu: {dc_min_v}-{dc_max_v}s")

        ctk.CTkButton(modal, text="💾 Lưu Cấu Hình", fg_color="#059669", hover_color="#047857", height=40, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8, command=save_modal).pack(fill="x", padx=24, pady=12)

    def setup_tab_accounts(self):
        self.frame_acc_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_acc_tab.grid_rowconfigure(3, weight=1)
        self.frame_acc_tab.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f8fafc", height=58, corner_radius=8, border_width=1, border_color="#e2e8f0")
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top_bar.grid_columnconfigure(0, weight=1)

        self.ent_quick_cookie = ctk.CTkEntry(top_bar, placeholder_text="Nhập Cookie IG (Tự động Check Live & dùng Proxy xoay chung)...", height=36, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.ent_quick_cookie.grid(row=0, column=0, padx=(12, 6), pady=10, sticky="ew")

        self.max_jobs_entry = ctk.CTkEntry(top_bar, placeholder_text="Max Job (Mặc định vô hạn)", width=130, height=36, font=ctk.CTkFont(size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.max_jobs_entry.grid(row=0, column=1, padx=6, pady=10)
        self.max_jobs_entry.insert(0, "999999")

        ctk.CTkButton(top_bar, text="➕ Thêm Acc", width=110, height=36, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, command=self.quick_add_single_account).grid(row=0, column=2, padx=6, pady=10)
        ctk.CTkButton(top_bar, text="📥 Batch Import", width=120, height=36, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, command=self.batch_import_accounts).grid(row=0, column=3, padx=(6, 12), pady=10)

        tool_tbl = ctk.CTkFrame(self.frame_acc_tab, fg_color="transparent", height=42)
        tool_tbl.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        tool_tbl.grid_columnconfigure(6, weight=1)

        ctk.CTkButton(tool_tbl, text="✓ Chọn Tất Cả", width=100, height=28, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_accounts(True)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(tool_tbl, text="✗ Bỏ Chọn", width=85, height=28, fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_accounts(False)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Đã Chọn", width=110, height=28, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_selected_accounts).grid(row=0, column=2, padx=2)
        ctk.CTkButton(tool_tbl, text="🔄 Check Live/Die", width=120, height=28, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.check_selected_ig_live).grid(row=0, column=3, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Acc Die", width=110, height=28, fg_color="#7f1d1d", hover_color="#991b1b", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_die_accounts).grid(row=0, column=4, padx=2)

        tbl_head = ctk.CTkFrame(self.frame_acc_tab, fg_color="#f1f5f9", height=36, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))
        tbl_head.grid_columnconfigure(3, weight=1)
        tbl_head.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=35).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=45).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="MODE", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=70).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(tbl_head, text="UID / INSTAGRAM ID", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TÊN USERNAME", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=4, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="SỐ XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=90, anchor="w").grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=240, anchor="w").grid(row=0, column=6, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=90, anchor="e").grid(row=0, column=7, sticky="e", padx=12)

        self.scroll_accs = ctk.CTkScrollableFrame(self.frame_acc_tab, fg_color="#f8fafc", corner_radius=8)
        self.scroll_accs.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.scroll_accs.grid_columnconfigure(0, weight=1)

    def setup_tab_fb_pages(self):
        """
        Thiết kế Tab Quản lý FB & Page tối ưu cho Tương Tác Chéo (TTC) & XSMM:
        - Khung trên chia 2 cột:
          + Trái: Danh sách Tài khoản Tương Tác Chéo (TTC) - mỗi Acc TTC tự động khoá 1 luồng FB duy nhất.
          + Phải: Liên kết Tài khoản FB Mẹ (nhập cả Cookie & Token EAAG/EAAD) -> tự động quét và sổ các Page Con ngay bên dưới từng Acc FB Mẹ.
        - Khung dưới: Cây phân cấp [Tài khoản FB Mẹ] -> [Danh sách các Page Con bên dưới], tích chọn Page + chọn Acc TTC là chạy.
        """
        self.frame_page_tab = ctk.CTkFrame(self.main_content, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e2e8f0")
        self.frame_page_tab.grid_rowconfigure(3, weight=1)
        self.frame_page_tab.grid_columnconfigure(0, weight=1)

        # --- KHUNG TRÊN: 2 PANEL (TRÁI: TÀI KHOẢN TTC | PHẢI: LIÊN KẾT FB COOKIE + TOKEN) ---
        top_split = ctk.CTkFrame(self.frame_page_tab, fg_color="transparent")
        top_split.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        top_split.grid_columnconfigure(0, weight=5)
        top_split.grid_columnconfigure(1, weight=7)

        # Panel Trái: Quản lý Tài khoản Tương Tác Chéo (TTC)
        ttc_box = ctk.CTkFrame(top_split, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#cbd5e1")
        ttc_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttc_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ttc_box, text="🎯 DANH SÁCH TÀI KHOẢN TƯƠNG TÁC CHÉO (MỖI ACC TTC = 1 LUỒNG FB)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        ttc_input_row = ctk.CTkFrame(ttc_box, fg_color="transparent")
        ttc_input_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        ttc_input_row.grid_columnconfigure(0, weight=1)

        self.ent_ttc_token = ctk.CTkEntry(ttc_input_row, placeholder_text="Nhập Access Token TươngTácChéo...", height=32, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.ent_ttc_token.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(ttc_input_row, text="➕ Thêm Acc TTC", width=115, height=32, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.add_ttc_account_action).grid(row=0, column=1)

        self.scroll_ttc_accs = ctk.CTkScrollableFrame(ttc_box, height=92, fg_color="#ffffff", corner_radius=6)
        self.scroll_ttc_accs.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        self.scroll_ttc_accs.grid_columnconfigure(0, weight=1)

        # Panel Phải: Liên kết Tài khoản Facebook Mẹ (Cookie + Token)
        fb_link_box = ctk.CTkFrame(top_split, fg_color="#f8fafc", corner_radius=8, border_width=1, border_color="#cbd5e1")
        fb_link_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        fb_link_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(fb_link_box, text="📘 LIÊN KẾT TÀI KHOẢN FB MẸ (COOKIE + TOKEN) & TỰ ĐỘNG HIỆN PAGE CON", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0284c7").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        fb_row1 = ctk.CTkFrame(fb_link_box, fg_color="transparent")
        fb_row1.grid(row=1, column=0, sticky="ew", padx=10, pady=3)
        fb_row1.grid_columnconfigure(0, weight=1)

        self.txt_fb_cookies = ctk.CTkEntry(fb_row1, placeholder_text="🍪 Nhập Cookie Facebook Mẹ (c_user=...; xs=...)...", height=32, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.txt_fb_cookies.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.max_jobs_fb_entry = ctk.CTkEntry(fb_row1, placeholder_text="Max Job", width=90, height=32, font=ctk.CTkFont(size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.max_jobs_fb_entry.grid(row=0, column=1)
        self.max_jobs_fb_entry.insert(0, "999999")

        fb_row2 = ctk.CTkFrame(fb_link_box, fg_color="transparent")
        fb_row2.grid(row=2, column=0, sticky="ew", padx=10, pady=(3, 8))
        fb_row2.grid_columnconfigure(0, weight=1)

        self.txt_fb_token = ctk.CTkEntry(fb_row2, placeholder_text="🔑 Nhập Token FB (EAAG... / EAAD... - Có thể nhập cùng Cookie hoặc để trống)...", height=32, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#ffffff", border_color="#cbd5e1")
        self.txt_fb_token.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(fb_row2, text="🔍 Thêm FB & Quét Page", width=150, height=32, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.quick_link_fb_and_scan_pages).grid(row=0, column=1, padx=(0, 4))
        ctk.CTkButton(fb_row2, text="📥 Nạp Hàng Loạt", width=115, height=32, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.scan_and_import_fb_pages).grid(row=0, column=2)

        # --- THANH CÔNG CỤ ĐIỀU KHIỂN PAGE & GÁN NHANH ACC TTC ---
        tool_tbl = ctk.CTkFrame(self.frame_page_tab, fg_color="transparent", height=40)
        tool_tbl.grid(row=1, column=0, sticky="ew", padx=12, pady=2)
        tool_tbl.grid_columnconfigure(8, weight=1)

        ctk.CTkButton(tool_tbl, text="✓ Chọn Tất Cả Page", width=115, height=28, fg_color="#059669", hover_color="#047857", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(True)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(tool_tbl, text="✗ Bỏ Chọn", width=80, height=28, fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=lambda: self.toggle_all_pages(False)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Page Chọn", width=110, height=28, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_selected_pages).grid(row=0, column=2, padx=2)
        ctk.CTkButton(tool_tbl, text="🔄 Check Live Page", width=115, height=28, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.check_selected_fb_live).grid(row=0, column=3, padx=2)
        ctk.CTkButton(tool_tbl, text="🗑️ Xóa Page Die", width=105, height=28, fg_color="#7f1d1d", hover_color="#991b1b", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.delete_die_pages).grid(row=0, column=4, padx=2)

        # Bộ chọn gán nhanh tài khoản TTC cho các Page đang tích chọn
        ctk.CTkLabel(tool_tbl, text=" | Gán Acc TTC cho Page đã tích:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#0f172a").grid(row=0, column=5, padx=(8, 4))
        self.opt_bulk_ttc = ctk.CTkOptionMenu(tool_tbl, values=["-- Chọn Acc TTC --"], width=150, height=28, fg_color="#0f172a", button_color="#1e293b", font=ctk.CTkFont(size=10, weight="bold"))
        self.opt_bulk_ttc.grid(row=0, column=6, padx=2)

        ctk.CTkButton(tool_tbl, text="⚡ Áp dụng & Chạy Page Đã Chọn", width=190, height=28, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=self.assign_ttc_and_run_selected_pages).grid(row=0, column=7, padx=4)

        # --- HEADER BẢNG PHÂN CẤP FB MẸ -> PAGE CON ---
        tbl_head = ctk.CTkFrame(self.frame_page_tab, fg_color="#f1f5f9", height=34, corner_radius=6)
        tbl_head.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 4))
        tbl_head.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(tbl_head, text=" □", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=35).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="STT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=40).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(tbl_head, text="TÀI KHOẢN FB MẸ  ↳  TÊN FACEBOOK PAGE CON", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155").grid(row=0, column=2, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="PAGE ID", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=130, anchor="w").grid(row=0, column=3, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="NỀN TẢNG / ACC TTC CHẠY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb", width=195, anchor="w").grid(row=0, column=4, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="SỐ XU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=85, anchor="w").grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="TRẠNG THÁI", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=220, anchor="w").grid(row=0, column=6, sticky="w", padx=6)
        ctk.CTkLabel(tbl_head, text="ACTION", font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155", width=85, anchor="e").grid(row=0, column=7, sticky="e", padx=12)

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

        self.btn_toggle = ctk.CTkButton(top_control, text="🚀 START ALL (CHẠY TẤT CẢ)", fg_color="#059669", hover_color="#047857", text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=40, width=260, corner_radius=8, command=self.toggle_run_all)
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
                    if "token" in data:
                        self.ent_token.delete(0, "end")
                        self.ent_token.insert(0, decrypt_local_data(data["token"]))
                    if "global_proxy" in data:
                        self.ent_global_proxy.delete(0, "end")
                        self.ent_global_proxy.insert(0, str(data["global_proxy"]))
                    if "delay_min" in data:
                        self.ent_delay_min.delete(0, "end")
                        self.ent_delay_min.insert(0, str(data["delay_min"]))
                        self.ent_delay.delete(0, "end")
                        self.ent_delay.insert(0, str(data["delay_min"]))
                    if "delay_max" in data:
                        self.ent_delay_max.delete(0, "end")
                        self.ent_delay_max.insert(0, str(data["delay_max"]))
                    if "delay_coin_min" in data:
                        self.ent_delay_coin_min.delete(0, "end")
                        self.ent_delay_coin_min.insert(0, str(data["delay_coin_min"]))
                    if "delay_coin_max" in data:
                        self.ent_delay_coin_max.delete(0, "end")
                        self.ent_delay_coin_max.insert(0, str(data["delay_coin_max"]))
                    if "threads" in data:
                        self.ent_threads.delete(0, "end")
                        self.ent_threads.insert(0, str(data["threads"]))
                    for k_cfg, chk_w in [
                        ("ig_like", self.chk_ig_like),
                        ("ig_follow", self.chk_ig_follow),
                        ("ig_cmt", self.chk_ig_cmt),
                        ("fb_like", self.chk_fb_like),
                        ("fb_likepage", self.chk_fb_likepage),
                        ("fb_follow", self.chk_fb_follow),
                        ("fb_cmt", self.chk_fb_cmt)
                    ]:
                        if k_cfg in data:
                            if data[k_cfg]: chk_w.select()
                            else: chk_w.deselect()
            except: pass

    def save_config(self):
        try:
            self.sync_cache_from_ui()
            d_min, d_max, dc_min, dc_max = self.get_delay_settings()
            data = {
                "token": encrypt_local_data(self.cfg_cache["token"]),
                "global_proxy": self.cfg_cache["global_proxy"],
                "delay_min": d_min,
                "delay_max": d_max,
                "delay_coin_min": dc_min,
                "delay_coin_max": dc_max,
                "threads": str(self.cfg_cache["threads"]),
                "ig_like": bool(self.chk_ig_like.get()),
                "ig_follow": bool(self.chk_ig_follow.get()),
                "ig_cmt": bool(self.chk_ig_cmt.get()),
                "fb_like": bool(self.chk_fb_like.get()),
                "fb_likepage": bool(self.chk_fb_likepage.get()),
                "fb_follow": bool(self.chk_fb_follow.get()),
                "fb_cmt": bool(self.chk_fb_cmt.get())
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except: pass

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._log_queue.put(f"[{timestamp}] {message}\n")

    def update_stats(self, coins=0, jobs=0, entity_type="account", entity_key="", ttc_user=""):
        with self.lock:
            if coins:
                self.total_coins += coins
                self._balance_dirty = True
                if entity_type == "account" and entity_key in self.acc_rows:
                    self.acc_rows[entity_key]["coins"] += coins
                    c_val = self.acc_rows[entity_key]["coins"]
                    self.queue_row_ui("account", entity_key, coin_text=f"+{c_val} xu")
                    self.update_db_coins(entity_key, c_val, is_page=False)
                elif entity_type == "page" and entity_key in self.page_rows:
                    self.page_rows[entity_key]["coins"] += coins
                    c_val = self.page_rows[entity_key]["coins"]
                    self.queue_row_ui("page", entity_key, coin_text=f"+{c_val} xu")
                    self.update_db_coins(entity_key, c_val, is_page=True)
                if ttc_user and ttc_user in self.ttc_accounts:
                    self.ttc_accounts[ttc_user]["coins"] += coins
                    new_ttc_c = self.ttc_accounts[ttc_user]["coins"]
                    self.queue_row_ui("ttc", ttc_user, coin_text=f"💰 {new_ttc_c:,} xu")
                    self._db_queue.put(("UPDATE ttc_accounts SET coins = ? WHERE ttc_user = ?", (new_ttc_c, ttc_user)))

            if jobs:
                self.success_jobs += jobs

    def update_db_coins(self, key, coins, is_page=False):
        if is_page:
            self._db_queue.put(("UPDATE fb_pages SET coins = ? WHERE page_id = ?", (coins, key)))
        else:
            self._db_queue.put(("UPDATE accounts SET coins = ? WHERE username = ?", (coins, key)))

    def update_uptime_loop(self):
        if self.is_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            td_str = str(timedelta(seconds=elapsed))
            self.lbl_status_uptime.configure(text=f"⏱️ UPTIME: {td_str} | Phím tắt: Ctrl+F5 (Start All), Ctrl+F6 (Kill Switch)")
        self.update_account_counter_ui()
        self.after(1000, self.update_uptime_loop)

    def update_account_counter_ui(self):
        total_ig = len(self.acc_rows)
        total_pg = len(self.page_rows)
        running_count = sum(1 for status in self.single_running_threads.values() if status)
        total_all = total_ig + total_pg

        live_count = 0
        die_count = 0
        for item in list(self.acc_rows.values()) + list(self.page_rows.values()):
            st_txt = item.get("status_text", "Sẵn sàng")
            if "Die" in st_txt or "Checkpoint" in st_txt or "Hết Hạn" in st_txt:
                die_count += 1
            else:
                live_count += 1

        self.lbl_footer_stats.configure(
            text=f"Tổng Acc/Page: {total_all} (TTC: {len(self.ttc_accounts)}) | Đang chạy: {running_count} | Live: {live_count} | Die/CP: {die_count}"
        )

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
        for u in self.acc_rows.keys():
            self.queue_row_ui("account", u, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")
        for p in self.page_rows.keys():
            self.queue_row_ui("page", p, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")
        for tu in self.ttc_rows_ui.keys():
            self.queue_row_ui("ttc", tu, status_text="Đã dừng", status_color="#d97706")
        self.log("🛡️ KÍCH HOẠT KILL SWITCH (Ctrl+F6): Đã ngắt toàn bộ luồng hệ thống!")

    # ---------------- QUẢN LÝ TÀI KHOẢN TƯƠNG TÁC CHÉO (TTC) ----------------
    def get_ttc_dropdown_values(self):
        vals = [f"TTC: {u}" for u in self.ttc_accounts.keys()]
        vals.append("XSMM (Bearer Token)")
        return vals

    def refresh_all_ttc_dropdowns(self):
        vals = self.get_ttc_dropdown_values()
        bulk_vals = [f"TTC: {u}" for u in self.ttc_accounts.keys()] + ["XSMM (Bearer Token)"]
        if hasattr(self, "opt_bulk_ttc"):
            self.opt_bulk_ttc.configure(values=bulk_vals)
            if bulk_vals:
                self.opt_bulk_ttc.set(bulk_vals[0])

        for pid, info in self.page_rows.items():
            if "ttc_menu" in info:
                info["ttc_menu"].configure(values=vals)
                curr_v = info["ttc_var"].get()
                if curr_v not in vals and vals:
                    info["ttc_var"].set(vals[0])

    def load_ttc_accounts_from_db(self):
        if not os.path.exists(DB_FILE): return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT ttc_user, ttc_token, coins, status FROM ttc_accounts")
            rows = cursor.fetchall()
            conn.close()
            for t_user, t_tok, coins, st in rows:
                self.ttc_accounts[t_user] = {"ttc_user": t_user, "ttc_token": t_tok, "coins": coins or 0, "status": st or "Sẵn sàng"}
                self.ttc_account_locks[t_user] = threading.Lock()
                self.add_ttc_row_to_ui(self.ttc_accounts[t_user])
            self.refresh_all_ttc_dropdowns()
        except Exception:
            pass

    def add_ttc_account_action(self):
        ttc_tok = self.ent_ttc_token.get().strip()
        if not ttc_tok:
            self.log("⚠️ Vui lòng nhập Access Token Tương Tác Chéo!")
            return

        def _do_login_ttc():
            self.log("🔄 Đang đăng nhập kiểm tra Token Tương Tác Chéo...")
            ttc_client = TuongTacCheoTool(ttc_tok, proxy=self.get_effective_proxy(""))
            ok, uname, sodu, msg = ttc_client.login()
            if ok and uname:
                self.ttc_clients_cache[uname] = ttc_client
                self.ttc_accounts[uname] = {"ttc_user": uname, "ttc_token": ttc_tok, "coins": sodu, "status": "Live ✅ (1 Luồng)"}
                if uname not in self.ttc_account_locks:
                    self.ttc_account_locks[uname] = threading.Lock()
                self._db_queue.put((
                    "INSERT OR REPLACE INTO ttc_accounts (ttc_user, ttc_token, coins, status) VALUES (?, ?, ?, ?)",
                    (uname, ttc_tok, sodu, "Live ✅ (1 Luồng)")
                ))
                self.after(0, lambda: self.add_ttc_row_to_ui(self.ttc_accounts[uname]))
                self.after(0, lambda: self.ent_ttc_token.delete(0, "end"))
                self.after(0, self.refresh_all_ttc_dropdowns)
                self.log(f"✅ Đã thêm tài khoản TTC: [{uname}] | Số dư: {sodu:,} xu")
            else:
                ttc_client.close()
                self.log(f"❌ Đăng nhập TTC thất bại: {msg}")

        threading.Thread(target=_do_login_ttc, daemon=True).start()

    def add_ttc_row_to_ui(self, ttc_data):
        uname = ttc_data["ttc_user"]
        if uname in self.ttc_rows_ui:
            self.queue_row_ui("ttc", uname, coin_text=f"💰 {ttc_data['coins']:,} xu", status_text=ttc_data["status"], status_color="#059669")
            return

        row = ctk.CTkFrame(self.scroll_ttc_accs, fg_color="#f8fafc", corner_radius=6, border_width=1, border_color="#e2e8f0", height=32)
        row.pack(fill="x", padx=2, pady=2)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=f"👤 {uname}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a").grid(row=0, column=0, padx=8, pady=4, sticky="w")

        lbl_coin = ctk.CTkLabel(row, text=f"💰 {ttc_data['coins']:,} xu", font=ctk.CTkFont(size=10, weight="bold"), text_color="#059669")
        lbl_coin.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        lbl_st = ctk.CTkLabel(row, text=ttc_data.get("status", "Rảnh (0/1 luồng)"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#2563eb", width=155, anchor="w")
        lbl_st.grid(row=0, column=2, padx=6, pady=4, sticky="w")

        def _del_ttc():
            if uname in self.ttc_accounts:
                del self.ttc_accounts[uname]
            if uname in self.ttc_rows_ui:
                self.ttc_rows_ui[uname]["frame"].destroy()
                del self.ttc_rows_ui[uname]
            self._db_queue.put(("DELETE FROM ttc_accounts WHERE ttc_user = ?", (uname,)))
            self.refresh_all_ttc_dropdowns()
            self.log(f"🗑️ Đã xóa tài khoản TTC: {uname}")

        ctk.CTkButton(row, text="✕", width=26, height=22, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4, command=_del_ttc).grid(row=0, column=3, padx=6, pady=4)

        self.ttc_rows_ui[uname] = {
            "frame": row,
            "coin_label": lbl_coin,
            "status_label": lbl_st,
            "status_text": ttc_data.get("status", "Sẵn sàng")
        }

    # ---------------- QUẢN LÝ CÂY PHÂN CẤP: TÀI KHOẢN FB MẸ -> CÁC PAGE CON ----------------
    def ensure_fb_parent_section(self, fb_uid, fb_name="", cookie="", access_token=""):
        """Tạo khung tiêu đề Tài khoản FB Mẹ và khung chứa các Page Con ngay bên dưới"""
        fb_uid = str(fb_uid or "Main").strip()
        if fb_uid in self.fb_parent_sections:
            sec = self.fb_parent_sections[fb_uid]
            if cookie: sec["cookie"] = cookie
            if access_token: sec["access_token"] = access_token
            if fb_name and not fb_name.startswith("FB_"): sec["fb_name"] = fb_name
            has_ck = "✅ Cookie" if sec.get("cookie") else "❌ Cookie"
            has_tk = "✅ Token" if sec.get("access_token") else "❌ Token"
            sec["header_label"].configure(text=f"👤 TÀI KHOẢN FB: {sec['fb_name']} (UID: {fb_uid})   [{has_ck} | {has_tk}]")
            return sec

        container = ctk.CTkFrame(self.scroll_pages, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#cbd5e1")
        container.pack(fill="x", padx=4, pady=6)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(container, fg_color="#eff6ff", corner_radius=6, height=36)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        header.grid_columnconfigure(0, weight=1)

        disp_name = fb_name if fb_name else f"FB_{fb_uid}"
        has_ck = "✅ Cookie" if cookie else "❌ Cookie"
        has_tk = "✅ Token" if access_token else "❌ Token"

        lbl_head = ctk.CTkLabel(
            header,
            text=f"👤 TÀI KHOẢN FB: {disp_name} (UID: {fb_uid})   [{has_ck} | {has_tk}]",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1e3a8a"
        )
        lbl_head.grid(row=0, column=0, padx=10, pady=6, sticky="w")

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
            self.log(f"🗑️ Đã xóa Tài khoản FB {disp_name} và {len(to_del_pids)} Page con.")

        ctk.CTkButton(header, text="✓ Chọn hết Page của FB này", width=155, height=24, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5, command=_select_all_child_pages).grid(row=0, column=1, padx=4, pady=4)
        ctk.CTkButton(header, text="🗑️ Xóa FB", width=75, height=24, fg_color="#dc2626", hover_color="#b91c1c", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=5, command=_delete_fb_parent).grid(row=0, column=2, padx=(2, 8), pady=4)

        pages_holder = ctk.CTkFrame(container, fg_color="transparent")
        pages_holder.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 6))
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
                acc_data = {"username": ig_user, "cookie": ck, "proxy": proxy, "id": idfb, "coins": db_coins or 0, "max_jobs": max_j if max_j is not None else 999999}
                self.add_account_row_to_ui(acc_data, status)
        except Exception: pass

    def load_fb_pages_from_db(self):
        if not os.path.exists(DB_FILE): return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT fb_uid, fb_name, cookie, access_token FROM fb_accounts")
            fb_Rows = cursor.fetchall()
            for f_uid, f_name, f_ck, f_tok in fb_Rows:
                self.ensure_fb_parent_section(f_uid, f_name, f_ck, f_tok)

            cursor.execute("SELECT parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform FROM fb_pages")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                parent, pid, pname, ptok, proxy, status, db_coins, max_j, p_ck, u_tok, ass_ttc, plat = row
                page_data = {
                    "parent": parent or "Main",
                    "page_id": pid,
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
        except Exception:
            pass

    def add_account_row_to_ui(self, acc_data, status="Sẵn sàng"):
        ig_user = acc_data["username"]
        if ig_user in self.acc_rows: return

        row_frame = ctk.CTkFrame(self.scroll_accs, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#e2e8f0", height=40)
        row_frame.pack(fill="x", padx=4, pady=3)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)

        is_die_init = ("Die" in status or "Checkpoint" in status)
        var = ctk.BooleanVar(value=not is_die_init)
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
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{init_c} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=90, anchor="w")
        lbl_coin.grid(row=0, column=5, padx=6, pady=6, sticky="w")

        text_color_st = "#334155" if status == "Sẵn sàng" else ("#dc2626" if is_die_init else "#059669")
        lbl_status = ctk.CTkLabel(row_frame, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color=text_color_st, width=240, anchor="w")
        lbl_status.grid(row=0, column=6, padx=6, pady=6, sticky="w")

        def toggle_single_acc():
            is_currently_running = self.single_running_threads.get(ig_user, False)
            if not is_currently_running:
                self.sync_cache_from_ui()
                token = self.cfg_cache["token"]
                if not token:
                    self.log("✖ Vui lòng nhập XSMM Access Token trong phần ⚙️ Cấu hình chung!")
                    self.queue_row_ui("account", ig_user, status_text="❌ Thiếu Token XSMM", status_color="#dc2626")
                    return
                self.save_config()
                delay_cfg = self.get_delay_settings()

                chosen_ig_jobs = []
                if self.chk_ig_like.get(): chosen_ig_jobs.append('instagram_like')
                if self.chk_ig_follow.get(): chosen_ig_jobs.append('instagram_follow')
                if self.chk_ig_cmt.get(): chosen_ig_jobs.append('instagram_comment')

                if not chosen_ig_jobs:
                    self.log(f"✖ [IG - @{ig_user}] Chưa chọn loại job Instagram!")
                    return

                self.single_running_threads[ig_user] = True
                self.queue_row_ui("account", ig_user, status_text="Đang kết nối & lấy phiên...", status_color="#2563eb", btn_text="Dừng", btn_color="#dc2626")
                threading.Thread(target=self.worker_single_account_loop, args=(token, chosen_ig_jobs, delay_cfg, acc_data, btn_action, lbl_status), daemon=True).start()
            else:
                self.single_running_threads[ig_user] = False
                self.queue_row_ui("account", ig_user, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=80, height=26, fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=toggle_single_acc)
        btn_action.grid(row=0, column=7, padx=10, pady=6, sticky="e")

        self.acc_rows[ig_user] = {
            "frame": row_frame,
            "var": var,
            "stt_label": lbl_stt,
            "id_label": lbl_id,
            "user_label": lbl_user,
            "status_label": lbl_status,
            "status_text": status,
            "coin_label": lbl_coin,
            "action_btn": btn_action,
            "coins": init_c,
            "data": acc_data
        }

    def add_page_row_to_ui(self, page_data, status="Sẵn sàng"):
        pid = str(page_data["page_id"])
        if pid in self.page_rows: return

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
        lbl_stt = ctk.CTkLabel(row_frame, text=str(stt_idx), font=ctk.CTkFont(size=11), text_color="#475569", width=38)
        lbl_stt.grid(row=0, column=1, padx=4, pady=5, sticky="w")

        lbl_name = ctk.CTkLabel(row_frame, text=f"↳ 📘 {page_data['page_name']}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#0f172a")
        lbl_name.grid(row=0, column=2, padx=6, pady=5, sticky="w")

        lbl_id = ctk.CTkLabel(row_frame, text=str(pid), font=ctk.CTkFont(family="Consolas", size=10), text_color="#475569", width=130, anchor="w")
        lbl_id.grid(row=0, column=3, padx=6, pady=5, sticky="w")

        # Menu chọn Tài khoản TTC (hoặc XSMM) cho từng Page
        avail_vals = self.get_ttc_dropdown_values()
        saved_ttc = page_data.get("assigned_ttc", "")
        default_choice = saved_ttc if (saved_ttc and saved_ttc in avail_vals) else (avail_vals[0] if avail_vals else "XSMM (Bearer Token)")
        ttc_var = ctk.StringVar(value=default_choice)

        def _on_change_ttc(choice_val):
            page_data["assigned_ttc"] = choice_val
            self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (choice_val, pid)))

        ttc_menu = ctk.CTkOptionMenu(
            row_frame,
            variable=ttc_var,
            values=avail_vals,
            width=185,
            height=26,
            fg_color="#1e293b",
            button_color="#334155",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=_on_change_ttc
        )
        ttc_menu.grid(row=0, column=4, padx=6, pady=5, sticky="w")

        init_c = page_data.get("coins", 0)
        lbl_coin = ctk.CTkLabel(row_frame, text=f"+{init_c} xu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669", width=85, anchor="w")
        lbl_coin.grid(row=0, column=5, padx=6, pady=5, sticky="w")

        text_color_st = "#334155" if status == "Sẵn sàng" else ("#dc2626" if is_die_init else "#059669")
        lbl_status = ctk.CTkLabel(row_frame, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color=text_color_st, width=220, anchor="w")
        lbl_status.grid(row=0, column=6, padx=6, pady=5, sticky="w")

        def toggle_single_page():
            is_currently_running = self.single_running_threads.get(pid, False)
            if not is_currently_running:
                self.start_single_page_worker(pid)
            else:
                self.single_running_threads[pid] = False
                self.queue_row_ui("page", pid, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")

        btn_action = ctk.CTkButton(row_frame, text="Bắt đầu", width=80, height=26, fg_color="#0284c7", hover_color="#0369a1", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6, command=toggle_single_page)
        btn_action.grid(row=0, column=7, padx=10, pady=5, sticky="e")

        self.page_rows[pid] = {
            "frame": row_frame,
            "var": var,
            "ttc_var": ttc_var,
            "ttc_menu": ttc_menu,
            "status_label": lbl_status,
            "status_text": status,
            "coin_label": lbl_coin,
            "action_btn": btn_action,
            "coins": init_c,
            "data": page_data
        }

    def start_single_page_worker(self, pid, stagger_delay=0.0):
        if pid not in self.page_rows:
            return
        info = self.page_rows[pid]
        page_data = info["data"]
        selected_mode = info["ttc_var"].get()
        page_data["assigned_ttc"] = selected_mode

        self.sync_cache_from_ui()
        self.save_config()
        delay_cfg = self.get_delay_settings()

        list_fb_jobs = []
        if self.chk_fb_like.get(): list_fb_jobs.append("facebook_like")
        if self.chk_fb_likepage.get(): list_fb_jobs.append("facebook_likepage")
        if self.chk_fb_follow.get(): list_fb_jobs.append("facebook_follow")
        if self.chk_fb_cmt.get(): list_fb_jobs.append("facebook_comment")
        if not list_fb_jobs:
            list_fb_jobs = ["facebook_like", "facebook_likepage", "facebook_follow", "facebook_comment"]

        if selected_mode.startswith("TTC:"):
            ttc_user = selected_mode.replace("TTC:", "").strip()
            if ttc_user not in self.ttc_accounts:
                self.log(f"✖ [Page {page_data['page_name']}] Tài khoản TTC '{ttc_user}' không tồn tại!")
                return
            self.single_running_threads[pid] = True
            self.queue_row_ui("page", pid, status_text=f"Đang chờ luồng TTC ({ttc_user})...", status_color="#0284c7", btn_text="Dừng", btn_color="#dc2626")
            threading.Thread(
                target=self.worker_ttc_page_loop,
                args=(ttc_user, list_fb_jobs, delay_cfg, page_data, stagger_delay),
                daemon=True
            ).start()
        else:
            token = self.cfg_cache["token"]
            if not token:
                self.log("✖ Vui lòng nhập XSMM Access Token hoặc thêm & chọn Tài khoản TTC!")
                return
            self.single_running_threads[pid] = True
            self.queue_row_ui("page", pid, status_text="Đang chạy XSMM...", status_color="#0284c7", btn_text="Dừng", btn_color="#dc2626")
            threading.Thread(
                target=self.worker_single_page_loop,
                args=(token, list_fb_jobs, delay_cfg, page_data, info["action_btn"], info["status_label"], stagger_delay),
                daemon=True
            ).start()

    def assign_ttc_and_run_selected_pages(self):
        """Gán tài khoản TTC đang chọn trên thanh công cụ cho các Page đã tích và khởi chạy"""
        chosen_ttc = self.opt_bulk_ttc.get()
        selected_pids = [pid for pid, info in self.page_rows.items() if info["var"].get()]
        if not selected_pids:
            self.log("⚠️ Vui lòng tích chọn ít nhất 1 Page để gán Acc TTC và chạy!")
            return

        for idx, pid in enumerate(selected_pids):
            info = self.page_rows[pid]
            if chosen_ttc and chosen_ttc != "-- Chọn Acc TTC --":
                info["ttc_var"].set(chosen_ttc)
                info["data"]["assigned_ttc"] = chosen_ttc
                self._db_queue.put(("UPDATE fb_pages SET assigned_ttc = ? WHERE page_id = ?", (chosen_ttc, pid)))
            if not self.single_running_threads.get(pid, False):
                self.start_single_page_worker(pid, stagger_delay=idx * 0.2)

    def toggle_all_accounts(self, select_state):
        for item in self.acc_rows.values(): item["var"].set(select_state)

    def toggle_all_pages(self, select_state):
        for item in self.page_rows.values(): item["var"].set(select_state)

    def delete_selected_accounts(self):
        to_delete = [u for u, info in self.acc_rows.items() if info["var"].get()]
        if not to_delete: return
        for ig_user in to_delete:
            self.single_running_threads[ig_user] = False
            self._db_queue.put(("DELETE FROM accounts WHERE username = ?", (ig_user,)))
            if ig_user in self.acc_rows:
                self.acc_rows[ig_user]["frame"].destroy()
                del self.acc_rows[ig_user]
        self.log(f"🗑️ Đã xóa {len(to_delete)} tài khoản IG đã chọn.")

    def delete_die_accounts(self):
        to_delete = [u for u, info in self.acc_rows.items() if ("Die" in info.get("status_text", "") or "Checkpoint" in info.get("status_text", ""))]
        if not to_delete:
            self.log("💡 Không có tài khoản IG nào ở trạng thái Die/Checkpoint để xóa.")
            return
        for ig_user in to_delete:
            self.single_running_threads[ig_user] = False
            self._db_queue.put(("DELETE FROM accounts WHERE username = ?", (ig_user,)))
            if ig_user in self.acc_rows:
                self.acc_rows[ig_user]["frame"].destroy()
                del self.acc_rows[ig_user]
        self.log(f"🗑️ Đã dọn sạch {len(to_delete)} tài khoản IG Die/Checkpoint!")

    def delete_selected_pages(self):
        to_delete = [pid for pid, info in self.page_rows.items() if info["var"].get()]
        if not to_delete: return
        for pid in to_delete:
            self.single_running_threads[pid] = False
            self._db_queue.put(("DELETE FROM fb_pages WHERE page_id = ?", (pid,)))
            if pid in self.page_rows:
                self.page_rows[pid]["frame"].destroy()
                del self.page_rows[pid]
        self.log(f"🗑️ Đã xóa {len(to_delete)} Page Facebook đã chọn.")

    def delete_die_pages(self):
        to_delete = [pid for pid, info in self.page_rows.items() if ("Die" in info.get("status_text", "") or "Hết Hạn" in info.get("status_text", ""))]
        if not to_delete:
            self.log("💡 Không có Page FB nào ở trạng thái Die để xóa.")
            return
        for pid in to_delete:
            self.single_running_threads[pid] = False
            self._db_queue.put(("DELETE FROM fb_pages WHERE page_id = ?", (pid,)))
            if pid in self.page_rows:
                self.page_rows[pid]["frame"].destroy()
                del self.page_rows[pid]
        self.log(f"🗑️ Đã dọn sạch {len(to_delete)} Page FB Die!")

    def check_selected_ig_live(self):
        self.sync_cache_from_ui()
        selected = [u for u, info in self.acc_rows.items() if info["var"].get()] or list(self.acc_rows.keys())
        if not selected:
            self.log("💡 Danh sách tài khoản IG đang trống.")
            return

        max_workers = max(1, min(15, self.cfg_cache.get("threads", 5)))

        def _check_one(ig_user):
            if ig_user not in self.acc_rows:
                return ig_user, "SKIP", None, None
            info = self.acc_rows[ig_user]
            ck = info["data"]["cookie"]
            proxy = self.get_effective_proxy(info["data"].get("proxy", ""))
            self.queue_row_ui("account", ig_user, status_text="🔄 Đang check live...", status_color="#2563eb")
            try:
                p_data = json.loads(check_cookie_ig(ck, proxy))
                st_code = p_data.get("status_check", "DIE")
                if st_code == "LIVE" and p_data.get("form_data", {}).get("username"):
                    real_user = p_data["form_data"]["username"]
                    real_id = str(p_data["form_data"].get("id") or info["data"].get("id", "0"))
                    return ig_user, "LIVE", real_user, real_id
                elif st_code == "CHECKPOINT":
                    return ig_user, "CHECKPOINT", None, None
                elif st_code == "PROXY_ERR":
                    return ig_user, "PROXY_ERR", None, None
                else:
                    return ig_user, "DIE", None, None
            except Exception:
                return ig_user, "PROXY_ERR", None, None

        def _do_check_all():
            self.log(f"🔄 Đang Check Live/Die đa luồng ({max_workers} threads) cho {len(selected)} tài khoản IG...")
            live_count, die_count, cp_count, err_count = 0, 0, 0, 0

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_check_one, u) for u in selected]
                for fut in as_completed(futures):
                    ig_user, result_st, real_user, real_id = fut.result()
                    if ig_user not in self.acc_rows:
                        continue
                    info = self.acc_rows[ig_user]
                    if result_st == "LIVE":
                        live_count += 1
                        if real_id and real_id != "0":
                            info["data"]["id"] = real_id
                        status_str = "Live ✅ (Sẵn sàng)"
                        self.queue_row_ui("account", ig_user, status_text=status_str, status_color="#059669", var_val=True, id_text=str(real_id) if (real_id and real_id != "0") else None)
                        self.mark_account_status_db(ig_user, status_str)
                    elif result_st == "CHECKPOINT":
                        cp_count += 1
                        status_str = "Checkpoint / Challenge ⚠️"
                        self.queue_row_ui("account", ig_user, status_text=status_str, status_color="#d97706", var_val=False)
                        self.mark_account_status_db(ig_user, status_str)
                    elif result_st == "PROXY_ERR":
                        err_count += 1
                        self.queue_row_ui("account", ig_user, status_text="Lỗi Proxy / Mạng ⚠️", status_color="#d97706")
                    else:
                        die_count += 1
                        status_str = "Cookie Die ❌"
                        self.queue_row_ui("account", ig_user, status_text=status_str, status_color="#dc2626", var_val=False)
                        self.mark_account_status_db(ig_user, status_str)

            self.log(f"✨ Kết quả Check IG: {live_count} Live ✅ | {die_count} Die ❌ | {cp_count} Checkpoint ⚠️ | {err_count} Lỗi Mạng/Proxy")

        threading.Thread(target=_do_check_all, daemon=True).start()

    def check_selected_fb_live(self):
        self.sync_cache_from_ui()
        selected = [pid for pid, info in self.page_rows.items() if info["var"].get()] or list(self.page_rows.keys())
        if not selected:
            self.log("💡 Danh sách Page FB đang trống.")
            return

        def _do_check():
            self.log(f"🔄 Đang tiến hành check Live/Die cho {len(selected)} Page FB...")
            live_count, die_count = 0, 0
            for pid in selected:
                info = self.page_rows[pid]
                ptok = info["data"].get("page_token", "")
                p_ck = info["data"].get("parent_cookie", "")
                proxy = self.get_effective_proxy(info["data"].get("proxy", ""))
                self.queue_row_ui("page", pid, status_text="🔄 Đang check...", status_color="#0284c7")
                is_live = False
                try:
                    session = c_requests.Session()
                    if proxies := format_proxy(proxy): session.proxies = proxies
                    if ptok and str(ptok).startswith("EAA"):
                        res = session.get(f"https://graph.facebook.com/v18.0/me?access_token={ptok}", timeout=8)
                        if "id" in res.json():
                            is_live = True
                    if not is_live and (p_ck or "c_user=" in str(ptok)):
                        raw_ck = p_ck if p_ck else ptok
                        dtsg = _get_fb_dtsg(session, _build_page_cookie(raw_ck, pid), pid)
                        if dtsg:
                            is_live = True
                    session.close()
                except: pass

                if is_live:
                    self.queue_row_ui("page", pid, status_text="Live ✅ (Sẵn sàng)", status_color="#059669", var_val=True)
                    self._db_queue.put(("UPDATE fb_pages SET status = ? WHERE page_id = ?", ("Live ✅ (Sẵn sàng)", pid)))
                    live_count += 1
                else:
                    self.queue_row_ui("page", pid, status_text="Die / Hết Hạn ❌", status_color="#dc2626", var_val=False)
                    self._db_queue.put(("UPDATE fb_pages SET status = ? WHERE page_id = ?", ("Die / Hết Hạn ❌", pid)))
                    die_count += 1
            self.log(f"✨ Hoàn tất check FB Page: {live_count} Live ✅ | {die_count} Die ❌")

        threading.Thread(target=_do_check, daemon=True).start()

    def quick_add_single_account(self):
        self.sync_cache_from_ui()
        line = self.ent_quick_cookie.get().strip()
        if not line: return
        try: max_jobs_val = int(self.max_jobs_entry.get().strip())
        except: max_jobs_val = 999999

        def process_quick():
            parts = line.split("|")
            ck = parts[0].strip()
            raw_proxy = parts[1].strip() if len(parts) > 1 else ""
            proxy = self.get_effective_proxy(raw_proxy)
            idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"])[1]
            self.log("🔍 Đang Check Live Cookie IG vừa nhập...")
            try:
                p_data = json.loads(check_cookie_ig(ck, proxy))
                st_code = p_data.get("status_check", "DIE")
                if st_code == "LIVE" and p_data.get('form_data', {}).get('username'):
                    ig_user = p_data['form_data']['username']
                    if idfb == "0" or p_data['form_data'].get('id'):
                        idfb = str(p_data['form_data'].get('id', idfb))

                    self._db_queue.put((
                        "INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)",
                        (ig_user, ck, proxy, "Live ✅ (Sẵn sàng)", 0, max_jobs_val)
                    ))

                    acc_data = {"cookie": ck, "id": idfb, "username": ig_user, "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val}
                    self.after(0, lambda: self.add_account_row_to_ui(acc_data, status="Live ✅ (Sẵn sàng)"))
                    self.after(0, lambda: self.ent_quick_cookie.delete(0, "end"))
                    self.log(f"✔ Check Live thành công & đã thêm acc IG: @{ig_user} (UID: {idfb})")
                elif st_code == "CHECKPOINT":
                    self.log("⚠️ Cookie IG này đang bị Checkpoint / Challenge!")
                elif st_code == "PROXY_ERR":
                    self.log("⚠️ Lỗi kết nối Proxy khi kiểm tra Cookie IG!")
                else:
                    self.log("✖ Cookie IG đã Die hoặc hết hạn phiên đăng nhập!")
            except Exception as e:
                self.log(f"✖ Lỗi khi kiểm tra Cookie IG: {str(e)}")

        threading.Thread(target=process_quick, daemon=True).start()

    def batch_import_accounts(self):
        self.sync_cache_from_ui()
        modal = ctk.CTkToplevel(self)
        modal.title("📥 Batch Import - Nạp hàng loạt tài khoản Instagram")
        modal.geometry("750x550")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="📋 DÁN DANH SÁCH COOKIE INSTAGRAM VÀO ĐÂY (MỖI DÒNG 1 COOKIE)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2563eb").pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(modal, text="💡 Hệ thống sẽ tự động Check Live đa luồng & gắn Proxy xoay chung cho tất cả Cookie!", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669").pack(anchor="w", padx=24, pady=(0, 8))
        txt_batch = ctk.CTkTextbox(modal, height=340, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#f8fafc", border_color="#cbd5e1", border_width=1)
        txt_batch.pack(fill="both", expand=True, padx=24, pady=(0, 15))

        def process_import():
            raw_text = txt_batch.get("1.0", "end").strip()
            if not raw_text: return
            try: max_jobs_val = int(self.max_jobs_entry.get().strip())
            except: max_jobs_val = 999999
            max_workers = max(1, min(15, self.cfg_cache.get("threads", 5)))

            lines = [c.strip() for c in raw_text.split("\n") if c.strip()]
            modal.destroy()
            self.log(f"🔄 Đang tiến hành Check Live & nạp {len(lines)} Cookie IG ({max_workers} luồng)...")

            def _verify_line(line_str):
                parts = line_str.split("|")
                ck = parts[0].strip()
                raw_proxy = parts[1].strip() if len(parts) > 1 else ""
                proxy = self.get_effective_proxy(raw_proxy)
                idfb = (re.search(r'ds_user_id=(\d+)', ck) or [None, "0"])[1]
                try:
                    p_data = json.loads(check_cookie_ig(ck, proxy))
                    st_code = p_data.get("status_check", "DIE")
                    if st_code == "LIVE" and p_data.get('form_data', {}).get('username'):
                        ig_user = p_data['form_data']['username']
                        if idfb == "0" or p_data['form_data'].get('id'):
                            idfb = str(p_data['form_data'].get('id', idfb))
                        return "LIVE", {"cookie": ck, "id": idfb, "username": ig_user, "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val}
                    return st_code, None
                except Exception:
                    return "DIE", None

            def _do_import():
                new_added, die_cnt, cp_cnt = 0, 0, 0
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(_verify_line, l) for l in lines]
                    for fut in as_completed(futures):
                        st_code, acc_data = fut.result()
                        if st_code == "LIVE" and acc_data:
                            self._db_queue.put((
                                "INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, ?, ?, ?)",
                                (acc_data["username"], acc_data["cookie"], acc_data["proxy"], "Live ✅ (Sẵn sàng)", 0, max_jobs_val)
                            ))
                            new_added += 1
                            self.after(0, lambda a=acc_data: self.add_account_row_to_ui(a, status="Live ✅ (Sẵn sàng)"))
                        elif st_code == "CHECKPOINT":
                            cp_cnt += 1
                        else:
                            die_cnt += 1
                self.log(f"✨ Batch Import hoàn tất: {new_added} Live ✅ | {die_cnt} Die ❌ | {cp_cnt} Checkpoint ⚠️")

            threading.Thread(target=_do_import, daemon=True).start()

        ctk.CTkButton(modal, text="🚀 TIẾN HÀNH CHECK LIVE & NẠP DANH SÁCH", fg_color="#059669", hover_color="#047857", height=42, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8, command=process_import).pack(fill="x", padx=24, pady=(0, 24))

    def _parse_fb_line(self, line_str):
        """Tách thông minh dòng nhập FB hỗ trợ cả Cookie, Token (EAA...), hoặc Cookie|Token|Proxy"""
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
        """Liên kết nhanh 1 Tài khoản FB Mẹ (từ ô Cookie + ô Token) và hiển thị các Page con bên dưới"""
        self.sync_cache_from_ui()
        raw_ck = self.txt_fb_cookies.get().strip()
        raw_tok = self.txt_fb_token.get().strip()
        if not raw_ck and not raw_tok:
            self.log("⚠️ Vui lòng nhập Cookie FB hoặc Token FB (EAAG/EAAD)!")
            return
        try: max_jobs_val = int(self.max_jobs_fb_entry.get().strip())
        except: max_jobs_val = 999999

        if "|" in raw_ck and not raw_tok:
            ck, tok, proxy = self._parse_fb_line(raw_ck)
        else:
            ck, tok, proxy = raw_ck, raw_tok, self.get_effective_proxy("")

        def _do_quick_scan():
            self.log("🔍 Đang liên kết Tài khoản FB Mẹ & quét danh sách Page Con...")
            fb_info, pages = scan_facebook_account_and_pages(cookie=ck, access_token=tok, proxy=proxy)
            f_uid, f_name = fb_info["fb_uid"], fb_info["fb_name"]

            self._db_queue.put((
                "INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status) VALUES (?, ?, ?, ?, ?, ?)",
                (f_uid, f_name, ck, tok, proxy, "Live ✅")
            ))
            self.after(0, lambda: self.ensure_fb_parent_section(f_uid, f_name, ck, tok))

            default_ttc = self.get_ttc_dropdown_values()[0] if self.get_ttc_dropdown_values() else ""
            for p in pages:
                pid, pname, ptok = p["page_id"], p["page_name"], p["page_token"]
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
            self.log(f"✅ Đã liên kết FB [{f_name} - {f_uid}] -> Tìm thấy {len(pages)} Page Con!")

        threading.Thread(target=_do_quick_scan, daemon=True).start()

    def scan_and_import_fb_pages(self):
        self.sync_cache_from_ui()
        modal = ctk.CTkToplevel(self)
        modal.title("🔍 Nạp hàng loạt Tài khoản Facebook (Cookie / Token) & Quét Page")
        modal.geometry("760x560")
        modal.grab_set()
        modal.configure(fg_color="#ffffff")

        ctk.CTkLabel(modal, text="📋 DÁN DANH SÁCH TÀI KHOẢN FB VÀO ĐÂY (MỖI DÒNG 1 ACC FB)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0284c7").pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(modal, text="💡 Hỗ trợ định dạng: Cookie | Token (EAAG/EAAD) | Proxy  (Hoặc chỉ Cookie, hoặc chỉ Token)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#059669").pack(anchor="w", padx=24, pady=(0, 8))
        txt_batch = ctk.CTkTextbox(modal, height=340, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#f8fafc", border_color="#cbd5e1", border_width=1)
        txt_batch.pack(fill="both", expand=True, padx=24, pady=(0, 15))

        single_cookie = self.txt_fb_cookies.get().strip()
        if single_cookie: txt_batch.insert("1.0", single_cookie)

        def process_scan():
            raw_text = txt_batch.get("1.0", "end").strip()
            if not raw_text: return
            try: max_jobs_val = int(self.max_jobs_fb_entry.get().strip())
            except: max_jobs_val = 999999

            lines = [c.strip() for c in raw_text.split("\n") if c.strip()]
            modal.destroy()

            def _do_scan():
                total_scanned_pages = 0
                default_ttc = self.get_ttc_dropdown_values()[0] if self.get_ttc_dropdown_values() else ""

                for line in lines:
                    ck, tok, proxy = self._parse_fb_line(line)
                    self.log("🔍 Đang quét Tài khoản FB & danh sách Page con...")
                    fb_info, pages = scan_facebook_account_and_pages(cookie=ck, access_token=tok, proxy=proxy)
                    f_uid, f_name = fb_info["fb_uid"], fb_info["fb_name"]

                    self._db_queue.put((
                        "INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status) VALUES (?, ?, ?, ?, ?, ?)",
                        (f_uid, f_name, ck, tok, proxy, "Live ✅")
                    ))
                    self.after(0, lambda u=f_uid, n=f_name, c=ck, t=tok: self.ensure_fb_parent_section(u, n, c, t))

                    for p in pages:
                        pid, pname, ptok = p["page_id"], p["page_name"], p["page_token"]
                        self._db_queue.put((
                            "INSERT OR REPLACE INTO fb_pages (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (f_uid, pid, pname, ptok, proxy, "Live ✅ (Sẵn sàng)", 0, max_jobs_val, ck, tok, default_ttc, "TTC")
                        ))
                        page_data = {
                            "parent": f_uid, "page_id": pid, "page_name": pname, "page_token": ptok,
                            "proxy": proxy, "coins": 0, "max_jobs": max_jobs_val,
                            "parent_cookie": ck, "user_token": tok, "assigned_ttc": default_ttc
                        }
                        total_scanned_pages += 1
                        self.after(0, lambda pd=page_data: self.add_page_row_to_ui(pd, status="Live ✅ (Sẵn sàng)"))

                self.log(f"✨ Đã nạp {len(lines)} Tài khoản FB & quét thành công {total_scanned_pages} Page con.")

            threading.Thread(target=_do_scan, daemon=True).start()

        ctk.CTkButton(modal, text="🚀 BẮT ĐẦU LIÊN KẾT FB & QUÉT PAGE ĐỒNG LOẠT", fg_color="#0284c7", hover_color="#0369a1", height=42, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8, command=process_scan).pack(fill="x", padx=24, pady=(0, 24))

    def toggle_run_all(self):
        if not self.is_running:
            self.sync_cache_from_ui()
            self.save_config()
            delay_cfg = self.get_delay_settings()

            selected_ig = [info for info in self.acc_rows.values() if info["var"].get()]
            selected_pg = [pid for pid, info in self.page_rows.items() if info["var"].get()]

            if not selected_ig and not selected_pg:
                self.log("⚠️ Vui lòng tích chọn ít nhất 1 tài khoản IG hoặc Page FB để chạy!")
                return

            chosen_ig_jobs = []
            if self.chk_ig_like.get(): chosen_ig_jobs.append('instagram_like')
            if self.chk_ig_follow.get(): chosen_ig_jobs.append('instagram_follow')
            if self.chk_ig_cmt.get(): chosen_ig_jobs.append('instagram_comment')

            self.is_running = True
            self.start_time = time.time()
            self.btn_toggle.configure(text="🛑 STOP ALL (DỪNG TẤT CẢ)", fg_color="#dc2626", hover_color="#b91c1c")
            self.lbl_status_conn.configure(text="● SYSTEM: MULTI-THREAD ACTIVE", text_color="#059669")

            token = self.cfg_cache["token"]
            for idx, info in enumerate(selected_ig):
                if not token:
                    self.log("⚠️ Bỏ qua IG vì chưa nhập XSMM Access Token.")
                    break
                acc_data = info["data"]
                ig_user = acc_data["username"]
                if not self.single_running_threads.get(ig_user, False):
                    self.single_running_threads[ig_user] = True
                    self.queue_row_ui("account", ig_user, status_text="Đang kết nối & lấy phiên...", status_color="#2563eb", btn_text="Dừng", btn_color="#dc2626")
                    threading.Thread(
                        target=self.worker_single_account_loop,
                        args=(token, chosen_ig_jobs, delay_cfg, acc_data, info["action_btn"], info["status_label"], idx * 0.15),
                        daemon=True
                    ).start()

            for idx, pid in enumerate(selected_pg):
                if not self.single_running_threads.get(pid, False):
                    self.start_single_page_worker(pid, stagger_delay=idx * 0.2)
        else:
            self.trigger_kill_switch()

    def mark_account_status_db(self, username, status_text):
        self._db_queue.put(("UPDATE accounts SET status = ? WHERE username = ?", (status_text, username)))

    # ---------------- WORKER 1: LUỒNG CHẠY TƯƠNG TÁC CHÉO (TTC) CHO FB PAGE (1 ACC TTC = 1 LUỒNG FB) ----------------
    def worker_ttc_page_loop(self, ttc_user, listnv, delay_cfg, page, stagger_delay=0.0):
        """
        Luồng chạy Page trên Tương Tác Chéo:
        Sử dụng self.ttc_account_locks[ttc_user] để cam kết mỗi Acc TTC chỉ chạy đúng 1 luồng FB duy nhất.
        Nếu nhiều Page cùng chọn 1 Acc TTC, các Page sẽ lần lượt vào phiên làm việc của Acc TTC đó mà không xung đột datnick.php!
        """
        pid, pname, ptok = str(page["page_id"]), page["page_name"], page.get("page_token", "")
        p_ck = page.get("parent_cookie", "")
        if stagger_delay > 0:
            if not self.smart_sleep(stagger_delay, pid):
                return

        if ttc_user not in self.ttc_account_locks:
            self.ttc_account_locks[ttc_user] = threading.Lock()
        ttc_lock = self.ttc_account_locks[ttc_user]

        max_jobs = page.get("max_jobs", 999999)
        attempted_jobs = 0
        fb_sess = c_requests.Session()

        try:
            while self.single_running_threads.get(pid, False):
                if attempted_jobs >= max_jobs:
                    self.queue_row_ui("page", pid, status_text=f"Đã hoàn thành {max_jobs} job", status_color="#059669")
                    break

                self.queue_row_ui("page", pid, status_text=f"⏳ Chờ lượt luồng TTC ({ttc_user})...", status_color="#d97706")

                # KHOÁ ĐỘC QUYỀN THEO TÀI KHOẢN TTC: Đảm bảo 1 Acc TTC chỉ thực thi 1 luồng FB tại 1 thời điểm
                with ttc_lock:
                    if not self.single_running_threads.get(pid, False):
                        break

                    ttc_info = self.ttc_accounts.get(ttc_user)
                    if not ttc_info:
                        self.log(f"✖ [Page {pname}] Không tìm thấy Acc TTC {ttc_user}")
                        break

                    proxy = self.get_effective_proxy(page.get("proxy", ""))
                    ttc_client = self.ttc_clients_cache.get(ttc_user)
                    if not ttc_client:
                        ttc_client = TuongTacCheoTool(ttc_info["ttc_token"], proxy=proxy)
                        ok_log, _, sodu_init, msg_log = ttc_client.login()
                        if not ok_log:
                            self.log(f"❌ [TTC: {ttc_user}] Lỗi đăng nhập: {msg_log}")
                            self.queue_row_ui("ttc", ttc_user, status_text=f"❌ {msg_log[:18]}", status_color="#dc2626")
                            self.queue_row_ui("page", pid, status_text=f"❌ Lỗi Token TTC ({ttc_user})", status_color="#dc2626")
                            break
                        self.ttc_clients_cache[ttc_user] = ttc_client

                    # Đặt cấu hình Page ID lên TTC (datnick.php)
                    self.queue_row_ui("ttc", ttc_user, status_text=f"Đang chạy Page: {pname[:14]}", status_color="#059669")
                    self.queue_row_ui("page", pid, status_text=f"🔗 Đang đặt cấu hình TTC ({ttc_user})...", status_color="#0284c7")

                    ok_dat, msg_dat = ttc_client.dat_nick(pid)
                    if not ok_dat:
                        self.log(f"⚠️ [TTC: {ttc_user} -> Page {pname} ({pid})] {msg_dat}")
                        self.queue_row_ui("page", pid, status_text=f"⚠️ {msg_dat[:26]}", status_color="#dc2626")
                        self.single_running_threads[pid] = False
                        break

                    self.log(f"✅ [TTC: {ttc_user}] Đã đặt cấu hình chạy Page: {pname} ({pid})")

                    # Thực hiện 1 phiên quét các loại job đã chọn cho Page này trước khi nhường Lock (nếu có Page khác cùng Acc TTC)
                    found_any_job = False
                    for rand_job in listnv:
                        if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs:
                            break

                        delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                        job_short = rand_job.replace("facebook_", "TTC_")
                        self.queue_row_ui("page", pid, status_text=f"🔍 Tìm job {job_short} ({ttc_user})...", status_color="#0284c7")

                        tasks, err_msg = ttc_client.get_tasks(rand_job)
                        if not tasks:
                            continue

                        found_any_job = True
                        self.log(f"📥 [TTC: {ttc_user} | Page: {pname}] Lấy được {len(tasks)} job {job_short}")

                        for nv in tasks:
                            if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs:
                                break

                            delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                            proxy = self.get_effective_proxy(page.get("proxy", ""))
                            task_id = nv.get("id", "")
                            link_job = nv.get("target_url", "")
                            target_id = nv.get("target_id", "") or task_id

                            self.queue_row_ui("page", pid, status_text=f"Đang làm {job_short} [{task_id[:10]}]...", status_color="#2563eb")
                            success = False
                            fail_reason = "Lỗi thao tác FB"

                            with self.net_semaphore:
                                if rand_job in ["facebook_like", "facebook_likepage"]:
                                    res_raw = fb_page_like(link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck, target_id=target_id)
                                    j = json.loads(res_raw)
                                    if j.get("success") or j.get("id"):
                                        success = True
                                    else:
                                        fail_reason = str(j.get("error", "Block Like"))
                                elif rand_job == "facebook_follow":
                                    res_raw = fb_page_follow(target_id, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    j = json.loads(res_raw)
                                    if j.get("success"):
                                        success = True
                                    else:
                                        fail_reason = str(j.get("error", "Block Follow"))
                                elif rand_job == "facebook_comment":
                                    cmt_txt = nv.get("msg") or ai_generate_unique_comment()
                                    res_raw = fb_page_comment(target_id, cmt_txt, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    j = json.loads(res_raw)
                                    if j.get("success") or j.get("id"):
                                        success = True
                                    else:
                                        fail_reason = str(j.get("error", "Block Cmt"))

                            attempted_jobs += 1
                            if success:
                                if not self.smart_sleep(random.randint(delay_coin_min, delay_coin_max), pid):
                                    break
                                earned, claim_msg = ttc_client.claim_reward(rand_job, task_id)
                                if earned > 0:
                                    self.update_stats(coins=int(earned), jobs=1, entity_type="page", entity_key=pid, ttc_user=ttc_user)
                                    self.log(f"💰 [TTC: {ttc_user} | {pname}] +{earned} xu ({job_short} - {task_id})")
                                    self.queue_row_ui("page", pid, status_text=f"✅ +{earned} xu ({attempted_jobs}/{max_jobs})", status_color="#059669")
                                else:
                                    self.log(f"⚠️ [TTC: {ttc_user} | {pname}] Duyệt {job_short} báo: {claim_msg}")
                                    self.queue_row_ui("page", pid, status_text=f"⚠️ {claim_msg[:18]} ({attempted_jobs})", status_color="#d97706")
                            else:
                                self.log(f"❌ [Page {pname}] Lỗi {job_short} [{task_id}]: {fail_reason[:30]}")
                                self.queue_row_ui("page", pid, status_text=f"❌ {fail_reason[:15]} ({attempted_jobs})", status_color="#dc2626")

                            if not self.smart_sleep(random.randint(delay_min, delay_max), pid):
                                break

                    self.queue_row_ui("ttc", ttc_user, status_text="Rảnh (Chờ phiên kế)", status_color="#2563eb")

                if self.single_running_threads.get(pid, False) and attempted_jobs < max_jobs:
                    w_txt = "Live ✅ (Nghỉ 8s chờ job TTC)" if found_any_job else "⚠️ Hết job TTC, chờ 10s..."
                    self.queue_row_ui("page", pid, status_text=w_txt, status_color="#059669" if found_any_job else "#d97706")
                    if not self.smart_sleep(8 if found_any_job else 10, pid):
                        break
        finally:
            try: fb_sess.close()
            except: pass

        self.single_running_threads[pid] = False
        self.queue_row_ui("page", pid, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")

    # ---------------- WORKER 2: LUỒNG CHẠY INSTAGRAM (XSMM) ----------------
    def worker_single_account_loop(self, token, listnv, delay_cfg, acc, btn_action, lbl_status, stagger_delay=0.0):
        username, ck, id_val = acc["username"], acc["cookie"], acc["id"]
        if stagger_delay > 0:
            if not self.smart_sleep(stagger_delay, username):
                return

        xsmm = XSMMTool(token)
        proxy = self.get_effective_proxy(acc.get("proxy", ""))
        max_jobs = acc.get("max_jobs", 999999)
        attempted_jobs = 0
        consecutive_fails = 0

        delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
        ig = INSTAGRAM(ck, proxy)

        try:
            with self.net_semaphore:
                av, fb_dtsg, st_check, ig_uname = ig.GETINFO()

            if st_check in ["DIE", "CHECKPOINT"]:
                err_label = "Checkpoint / Challenge ⚠️" if st_check == "CHECKPOINT" else "Cookie Die ❌"
                self.log(f"✖ [@{username}] Không thể chạy do {err_label}")
                self.mark_account_status_db(username, err_label)
                self.single_running_threads[username] = False
                self.queue_row_ui("account", username, status_text=err_label, status_color="#dc2626", btn_text="Bắt đầu", btn_color="#2563eb", var_val=False)
                return

            if not av or av is False:
                av = str(id_val if id_val and str(id_val) != "0" else ig.ds_user_id)
            if not ig_uname or ig_uname is False:
                ig_uname = username
            if not fb_dtsg or fb_dtsg is False:
                fb_dtsg = ""

            with self.net_semaphore:
                xsmm_uid = xsmm.sync_and_get_xsmm_id(ig_uname, av)
            self.log(f"🔗 [@{username}] Đã kết nối XSMM (XSMM_UID: {xsmm_uid} | IG_ID: {av}) -> Bắt đầu tìm job!")

            follow_cache_ids = []
            active_claim_uid = xsmm_uid

            while self.single_running_threads.get(username, False):
                if attempted_jobs >= max_jobs:
                    self.queue_row_ui("account", username, status_text=f"Đã hoàn thành {max_jobs} job", status_color="#059669")
                    break

                delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                ig.update_proxy(self.get_effective_proxy(acc.get("proxy", "")))

                found_any_task_in_cycle = False

                for rand_job in [j for j in listnv if 'instagram' in j]:
                    if not self.single_running_threads.get(username, False) or attempted_jobs >= max_jobs:
                        break

                    self.queue_row_ui("account", username, status_text=f"Đang tìm job {rand_job.replace('instagram_', '')}...", status_color="#2563eb")
                    with self.net_semaphore:
                        tasks, err_msg, matched_uid = xsmm.get_tasks(rand_job, xsmm_uid, fallback_uids=[av, ig_uname, username])

                    if not tasks or not isinstance(tasks, list):
                        self.log(f"⚠️ [@{username}] Không có job [{rand_job}]: {err_msg}")
                        self.queue_row_ui("account", username, status_text=f"⚠️ {err_msg[:25]}", status_color="#d97706")
                        continue

                    found_any_task_in_cycle = True
                    active_claim_uid = matched_uid
                    self.log(f"📥 [@{username}] Tìm thấy {len(tasks)} job [{rand_job}] (UID: {active_claim_uid})")

                    for nv in tasks:
                        if not self.single_running_threads.get(username, False) or attempted_jobs >= max_jobs:
                            break

                        delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                        ig.update_proxy(self.get_effective_proxy(acc.get("proxy", "")))

                        task_id = nv.get('id')
                        target_id = nv.get('target_id', '') or nv.get('target_id2', '')
                        target_url = nv.get('target_url', '') or nv.get('link', '')
                        idorlink = nv.get('idorlink') or target_url or target_id or ""
                        default_p = int(nv.get('points', 10))
                        comment_content = nv.get('msg') or nv.get('comment') or ai_generate_unique_comment()

                        job_label = "Follow" if rand_job == 'instagram_follow' else ("Like" if rand_job == 'instagram_like' else "Comment")
                        self.queue_row_ui("account", username, status_text=f"Đang {job_label} [{task_id}]...", status_color="#2563eb")

                        is_done = False
                        with self.net_semaphore:
                            if rand_job == 'instagram_like':
                                is_done = ig.LIKE(av, fb_dtsg, target_id, ck, target_url or idorlink, "")
                            elif rand_job == 'instagram_follow':
                                follow_target = target_id if target_id else idorlink
                                is_done = ig.FOLLOW(fb_dtsg, follow_target, target_url or idorlink, av=av)
                            elif rand_job == 'instagram_comment':
                                is_done = ig.COMMENT(av, fb_dtsg, target_id, target_url or idorlink, comment_content)

                        attempted_jobs += 1

                        if is_done:
                            consecutive_fails = 0
                            if rand_job in ['instagram_like', 'instagram_comment']:
                                with self.net_semaphore:
                                    c_res = gui_nhan_xu(rand_job, [task_id], active_claim_uid, cookie_check=ck, xsmm_obj=xsmm)
                                    earned, claim_msg = parse_real_earned_points(c_res, default_points=default_p)
                                    if earned == 0 and str(active_claim_uid) != str(av):
                                        c_res = gui_nhan_xu(rand_job, [task_id], av, cookie_check=ck, xsmm_obj=xsmm)
                                        earned, claim_msg = parse_real_earned_points(c_res, default_points=default_p)

                                if earned > 0:
                                    self.update_stats(coins=int(earned), jobs=1, entity_type="account", entity_key=username)
                                    self.log(f"✅ [@{username}] Xong {job_label} [{task_id}] -> +{earned} xu")
                                    self.queue_row_ui("account", username, status_text=f"✅ Xong {job_label} ({attempted_jobs}/{max_jobs})", status_color="#059669")
                                else:
                                    self.log(f"⚠️ [@{username}] Đã {job_label} [{task_id}] nhưng duyệt báo: {c_res}")
                                    self.queue_row_ui("account", username, status_text=f"⚠️ Duyệt: {claim_msg[:16]} ({attempted_jobs})", status_color="#d97706")

                                delay_coin = random.randint(delay_coin_min, delay_coin_max)
                                if not self.smart_sleep(delay_coin, username):
                                    break

                            elif rand_job == 'instagram_follow':
                                follow_cache_ids.append(task_id)
                                cache_len = len(follow_cache_ids)
                                self.log(f"✅ [@{username}] Follow thành công [{task_id}] -> Tích lũy: {cache_len}/3")
                                self.queue_row_ui("account", username, status_text=f"✅ Đã gom Follow [{cache_len}/3] ({attempted_jobs})", status_color="#059669")

                                if len(follow_cache_ids) >= 3 or attempted_jobs >= max_jobs:
                                    batch_size = len(follow_cache_ids)
                                    self.queue_row_ui("account", username, status_text=f"Đang gửi duyệt {batch_size} Follow...", status_color="#2563eb")
                                    with self.net_semaphore:
                                        c_res = gui_nhan_xu(rand_job, follow_cache_ids, active_claim_uid, cookie_check=ck, xsmm_obj=xsmm)
                                        earned, claim_msg = parse_real_earned_points(c_res, default_points=default_p * batch_size)
                                        if earned == 0 and str(active_claim_uid) != str(av):
                                            c_res = gui_nhan_xu(rand_job, follow_cache_ids, av, cookie_check=ck, xsmm_obj=xsmm)
                                            earned, claim_msg = parse_real_earned_points(c_res, default_points=default_p * batch_size)

                                    if earned > 0:
                                        self.update_stats(coins=int(earned), jobs=batch_size, entity_type="account", entity_key=username)
                                        self.log(f"💰 [@{username}] Nhận xu {batch_size} job Follow thành công: +{earned} xu")
                                    else:
                                        self.log(f"⚠️ [@{username}] Phản hồi duyệt {batch_size} Follow: {c_res}")
                                    follow_cache_ids = []

                                    delay_coin = random.randint(delay_coin_min, delay_coin_max)
                                    if not self.smart_sleep(delay_coin, username):
                                        break
                        else:
                            consecutive_fails += 1
                            err_detail = ig.last_error or "Thao tác bị chặn"
                            self.log(f"❌ [@{username}] Lỗi {job_label} [{task_id}]: {err_detail}")
                            self.queue_row_ui("account", username, status_text=f"❌ Lỗi {job_label} ({attempted_jobs})", status_color="#dc2626")

                            if consecutive_fails >= 5:
                                with self.net_semaphore:
                                    _, new_dtsg, recheck_st, _ = ig.GETINFO()
                                if recheck_st in ["DIE", "CHECKPOINT"]:
                                    err_label = "Checkpoint khi chạy ⚠️" if recheck_st == "CHECKPOINT" else "Cookie Die khi chạy ❌"
                                    self.log(f"✖ [@{username}] Tự động dừng: {err_label}")
                                    self.mark_account_status_db(username, err_label)
                                    self.single_running_threads[username] = False
                                    self.queue_row_ui("account", username, status_text=err_label, status_color="#dc2626", btn_text="Bắt đầu", btn_color="#2563eb", var_val=False)
                                    return
                                elif new_dtsg:
                                    fb_dtsg = new_dtsg
                                consecutive_fails = 0

                        delay_action = random.randint(delay_min, delay_max)
                        if not self.smart_sleep(delay_action, username):
                            break

                    if rand_job == 'instagram_follow' and len(follow_cache_ids) >= 3:
                        batch_size = len(follow_cache_ids)
                        with self.net_semaphore:
                            c_res = gui_nhan_xu(rand_job, follow_cache_ids, active_claim_uid, cookie_check=ck, xsmm_obj=xsmm)
                        earned, _ = parse_real_earned_points(c_res, default_points=10 * batch_size)
                        if earned > 0:
                            self.update_stats(coins=int(earned), jobs=batch_size, entity_type="account", entity_key=username)
                        follow_cache_ids = []

                if self.single_running_threads.get(username, False) and attempted_jobs < max_jobs:
                    wait_msg = "Live ✅ (Chờ job mới 10s)" if found_any_task_in_cycle else "⚠️ Chờ 10s quét lại job..."
                    self.queue_row_ui("account", username, status_text=wait_msg, status_color="#059669" if found_any_task_in_cycle else "#d97706")
                if not self.smart_sleep(10, username):
                    break
        finally:
            ig.close()
            xsmm.close()

        self.single_running_threads[username] = False
        self.queue_row_ui("account", username, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#2563eb")

    # ---------------- WORKER 3: LUỒNG CHẠY FB PAGE TRÊN XSMM ----------------
    def worker_single_page_loop(self, token, listnv, delay_cfg, page, btn_action, lbl_status, stagger_delay=0.0):
        pid, pname, ptok = page["page_id"], page["page_name"], page["page_token"]
        p_ck = page.get("parent_cookie", "")
        if stagger_delay > 0:
            if not self.smart_sleep(stagger_delay, pid):
                return

        xsmm = XSMMTool(token)
        fb_sess = c_requests.Session()
        max_jobs = page.get("max_jobs", 999999)
        attempted_jobs = 0

        try:
            with self.net_semaphore:
                xsmm.add_social_account(pname, "facebook")

            while self.single_running_threads.get(pid, False):
                if attempted_jobs >= max_jobs:
                    self.queue_row_ui("page", pid, status_text=f"Đã hoàn thành {max_jobs} job", status_color="#059669")
                    break

                delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()

                for rand_job in [j for j in listnv if j in ['facebook_like', 'facebook_follow', 'facebook_comment']]:
                    if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs: break
                    with self.net_semaphore:
                        tasks, err_msg, _ = xsmm.get_tasks(rand_job, pid)
                    if not tasks or not isinstance(tasks, list):
                        self.queue_row_ui("page", pid, status_text="⚠️ Hết job Page (XSMM)", status_color="#d97706")
                        continue

                    for nv in tasks:
                        if not self.single_running_threads.get(pid, False) or attempted_jobs >= max_jobs: break
                        delay_min, delay_max, delay_coin_min, delay_coin_max = self.get_delay_settings()
                        proxy = self.get_effective_proxy(page.get("proxy", ""))

                        task_id, link_job = nv.get('id', ''), nv.get('target_url', '')
                        default_p = int(nv.get('points', 10))
                        success = False
                        fail_reason_detail = "Lỗi FB API"

                        fb_job_desc = "FB Like" if 'like' in rand_job else ("FB Follow" if 'follow' in rand_job else "FB Cmt")
                        self.queue_row_ui("page", pid, status_text=f"Đang {fb_job_desc} [{task_id}]...", status_color="#0284c7")

                        with self.net_semaphore:
                            if rand_job == 'facebook_like':
                                try:
                                    res_raw = fb_page_like(link_job, ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck, target_id=nv.get('target_id', ''))
                                    j = json.loads(res_raw)
                                    if "success" in j or j.get("id"): success = True
                                    else: fail_reason_detail = str(j.get("error", "Block"))
                                except Exception: pass
                            elif rand_job == 'facebook_follow':
                                try:
                                    res_raw = fb_page_follow(nv.get('target_id', ''), ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    j = json.loads(res_raw)
                                    if "success" in j: success = True
                                    else: fail_reason_detail = str(j.get("error", "Block"))
                                except Exception: pass
                            elif rand_job == 'facebook_comment':
                                try:
                                    res_raw = fb_page_comment(nv.get('target_id', '') or link_job, nv.get('msg') or nv.get('comment') or ai_generate_unique_comment(), ptok, proxy, session=fb_sess, page_id=pid, parent_cookie=p_ck)
                                    j = json.loads(res_raw)
                                    if "id" in j or j.get("success"): success = True
                                    else: fail_reason_detail = str(j.get("error", "Block"))
                                except Exception: pass

                        attempted_jobs += 1
                        if success:
                            with self.net_semaphore:
                                c_res = gui_nhan_xu(rand_job, [task_id], pid, cookie_check=ptok, xsmm_obj=xsmm)
                            earned, _ = parse_real_earned_points(c_res, default_points=default_p)
                            if earned > 0:
                                self.update_stats(coins=int(earned), jobs=1, entity_type="page", entity_key=pid)
                                self.queue_row_ui("page", pid, status_text=f"✅ Xong {fb_job_desc} ({attempted_jobs}/{max_jobs})", status_color="#059669")
                            if not self.smart_sleep(random.randint(delay_coin_min, delay_coin_max), pid):
                                break
                        else:
                            self.queue_row_ui("page", pid, status_text=f"❌ Lỗi: {fail_reason_detail[:15]} ({attempted_jobs})", status_color="#dc2626")
                        if not self.smart_sleep(random.randint(delay_min, delay_max), pid):
                            break

                if self.single_running_threads.get(pid, False) and attempted_jobs < max_jobs:
                    self.queue_row_ui("page", pid, status_text="Live (Chờ job)", status_color="#059669")
                if not self.smart_sleep(3, pid):
                    break
        finally:
            try: fb_sess.close()
            except: pass
            xsmm.close()

        self.single_running_threads[pid] = False
        self.queue_row_ui("page", pid, status_text="Đã dừng", status_color="#d97706", btn_text="Bắt đầu", btn_color="#0284c7")

if __name__ == "__main__":
    app = MMOApp()
    app.mainloop()
