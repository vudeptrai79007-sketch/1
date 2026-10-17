import os
import re
import sys
import json
import time
import base64
import random
import sqlite3
import threading
import queue
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests
import urllib3
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# CẤU HÌNH HỆ THỐNG & DATABASE (mmo_fb_ig_accounts_v6.db)
# ==============================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = "mmo_fb_ig_accounts_v6.db"
db_lock = threading.Lock()
MAX_CONCURRENT_THREADS = 15
worker_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)


def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_database():
    with db_lock:
        conn = get_db_connection()
        c = conn.cursor()

        # 1. Bảng tài khoản Instagram (Chạy XSMM)
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            cookie TEXT,
            proxy TEXT,
            status TEXT DEFAULT 'Stopped',
            coins INTEGER DEFAULT 0,
            max_jobs INTEGER DEFAULT 100
        )''')

        # 2. Bảng tài khoản Facebook gốc (Quản lý Cookie / Token để quét Fanpage)
        c.execute('''CREATE TABLE IF NOT EXISTS fb_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fb_uid TEXT UNIQUE,
            fb_name TEXT,
            cookie TEXT,
            access_token TEXT,
            proxy TEXT,
            status TEXT DEFAULT 'Ready'
        )''')

        # 3. Bảng tài khoản Tương Tác Chéo (Lưu danh sách Token TTC)
        c.execute('''CREATE TABLE IF NOT EXISTS ttc_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ttc_user TEXT,
            ttc_token TEXT UNIQUE,
            coins INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Ready'
        )''')

        # 4. Bảng Fanpage / Profile FB chạy Job (Dùng chung cho XSMM và TTC)
        c.execute('''CREATE TABLE IF NOT EXISTS fb_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_username TEXT,
            page_id TEXT UNIQUE,
            page_name TEXT,
            page_token TEXT,
            proxy TEXT,
            status TEXT DEFAULT 'Stopped',
            coins INTEGER DEFAULT 0,
            max_jobs INTEGER DEFAULT 100,
            parent_cookie TEXT DEFAULT '',
            user_token TEXT DEFAULT '',
            assigned_ttc TEXT DEFAULT '',
            platform TEXT DEFAULT 'TTC'
        )''')

        # Tự động migrate cột nếu file DB từ phiên bản cũ
        existing_cols = [col[1] for col in c.execute("PRAGMA table_info(fb_pages)").fetchall()]
        migration_cols = [
            ("parent_cookie", "TEXT DEFAULT ''"),
            ("user_token", "TEXT DEFAULT ''"),
            ("assigned_ttc", "TEXT DEFAULT ''"),
            ("platform", "TEXT DEFAULT 'TTC'")
        ]
        for col_name, col_def in migration_cols:
            if col_name not in existing_cols:
                try:
                    c.execute(f"ALTER TABLE fb_pages ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass

        # 5. Bảng Nhật ký hệ thống (Logs)
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            action TEXT,
            status TEXT
        )''')

        conn.commit()
        conn.close()


def log_to_db(username, action, status):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with db_lock:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO logs (timestamp, username, action, status) VALUES (?, ?, ?, ?)",
                (now_str, str(username), str(action), str(status))
            )
            conn.commit()
            conn.close()
    except Exception:
        pass


def format_proxies(proxy_str):
    if not proxy_str or not str(proxy_str).strip():
        return None
    p = str(proxy_str).strip()
    if not p.startswith("http"):
        parts = p.split(":")
        if len(parts) == 4:
            p = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        else:
            p = f"http://{p}"
    return {"http": p, "https": p}


# ==============================================================================
# CLASS 1: INSTAGRAM AUTOMATION (PHỤC VỤ TAB INSTAGRAM XSMM)
# ==============================================================================
class INSTAGRAM:
    def __init__(self, cookies, proxy=None):
        self.cookies = (cookies or "").strip()
        self.proxies = format_proxies(proxy)
        self.session = requests.Session()
        self.session.verify = False
        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.csrf_token = self._extract_cookie_val("csrftoken")
        self.ds_user_id = self._extract_cookie_val("ds_user_id")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-CSRFToken": self.csrf_token,
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": self.cookies,
            "Origin": "https://www.instagram.com",
            "Referer": "https://www.instagram.com/"
        }

    def _extract_cookie_val(self, key):
        m = re.search(rf"{key}=([^;]+)", self.cookies)
        return m.group(1).strip() if m else ""

    def GETINFO(self):
        try:
            url = "https://www.instagram.com/api/v1/accounts/edit/web_form_data/"
            r = self.session.get(url, headers=self.headers, timeout=15)
            if r.status_code == 200 and "form_data" in r.text:
                data = r.json()
                username = data.get("form_data", {}).get("username", "")
                if username:
                    return True, username
            # Fallback trang chủ
            r2 = self.session.get("https://www.instagram.com/", headers=self.headers, timeout=15)
            m = re.search(r'"username":"([^"]+)"', r2.text)
            if m:
                return True, m.group(1)
            if self.ds_user_id:
                return True, f"IG_{self.ds_user_id}"
            return False, "Cookie IG die hoặc hết hạn"
        except Exception as e:
            return False, f"Lỗi mạng IG: {e}"

    def _shortcode_to_media_id(self, shortcode):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        media_id = 0
        for char in shortcode:
            if char in alphabet:
                media_id = media_id * 64 + alphabet.index(char)
        return str(media_id)

    def resolve_media_id(self, target):
        target = str(target).strip()
        if target.isdigit():
            return target
        m = re.search(r"/(?:p|reel|tv)/([A-Za-z0-9_-]+)", target)
        if m:
            return self._shortcode_to_media_id(m.group(1))
        return target

    def resolve_user_id(self, target):
        target = str(target).strip()
        if target.isdigit():
            return target
        username = target.rstrip("/").split("/")[-1].split("?")[0]
        try:
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            r = self.session.get(url, headers=self.headers, timeout=15)
            if r.status_code == 200:
                uid = r.json().get("data", {}).get("user", {}).get("id", "")
                if uid:
                    return str(uid)
        except Exception:
            pass
        return target

    def FOLLOW(self, target_user):
        uid = self.resolve_user_id(target_user)
        if not uid.isdigit():
            return False, f"Không lấy được UID từ {target_user}"
        try:
            url = f"https://www.instagram.com/api/v1/friendships/create/{uid}/"
            r = self.session.post(url, headers=self.headers, timeout=15)
            if r.status_code == 200 and ('"status":"ok"' in r.text or '"following":true' in r.text):
                return True, f"Follow thành công {uid}"
            return False, f"Follow thất bại ({r.status_code})"
        except Exception as e:
            return False, str(e)

    def LIKE(self, target_post):
        media_id = self.resolve_media_id(target_post)
        if not media_id.isdigit():
            return False, f"Không lấy được MediaID từ {target_post}"
        try:
            url = f"https://www.instagram.com/api/v1/web/likes/{media_id}/like/"
            r = self.session.post(url, headers=self.headers, timeout=15)
            if r.status_code == 200 and '"status":"ok"' in r.text:
                return True, f"Like thành công {media_id}"
            return False, f"Like thất bại ({r.status_code})"
        except Exception as e:
            return False, str(e)

    def COMMENT(self, target_post, comment_text):
        media_id = self.resolve_media_id(target_post)
        if not media_id.isdigit():
            return False, f"Không lấy được MediaID từ {target_post}"
        try:
            url = f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/"
            r = self.session.post(url, data={"comment_text": comment_text}, headers=self.headers, timeout=15)
            if r.status_code == 200 and '"status":"ok"' in r.text:
                return True, f"Comment thành công {media_id}"
            return False, f"Comment thất bại ({r.status_code})"
        except Exception as e:
            return False, str(e)


# ==============================================================================
# CLASS 2: XSMM API TOOL (PHỤC VỤ TAB INSTAGRAM & FANPAGE XSMM)
# ==============================================================================
class XSMMTool:
    def __init__(self, api_token, proxy=None):
        self.token = (api_token or "").strip()
        self.base_url = "https://xsmm.net/api/taskapi"
        self.session = requests.Session()
        self.session.verify = False
        proxies = format_proxies(proxy)
        if proxies:
            self.session.proxies.update(proxies)

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
            "Authorization": f"Bearer {self.token}" if self.token and not self.token.startswith("Bearer") else self.token
        }

    def get_tasks(self, social="instagram", account_uid=""):
        try:
            url = f"{self.base_url}/tasks2"
            params = {"social": social, "account": account_uid, "token": self.token}
            r = self.session.get(url, params=params, headers=self.headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("data") or data.get("tasks") or []
        except Exception:
            pass
        return []

    def claim_reward(self, task_id, account_uid=""):
        try:
            url = f"{self.base_url}/tasks2/complete"
            payload = {"task_id": task_id, "account": account_uid, "token": self.token}
            r = self.session.post(url, json=payload, headers=self.headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                ok = data.get("status") in (True, "success", 200, "ok") or data.get("success") is True
                reward = int(data.get("reward", data.get("coins", 1)))
                msg = data.get("message", "Hoàn thành job XSMM")
                return ok, msg, reward
        except Exception as e:
            return False, str(e), 0
        return False, "Lỗi claim XSMM", 0


# ==============================================================================
# CLASS 3: TUONGTACCHEO TOOL (BỘ LÕI TTC FACEBOOK CHUẨN SMALI MTOOLV2)
# ==============================================================================
class TuongTacCheoTool:
    BASE_URL = "https://tuongtaccheo.com"
    USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"

    # Đầy đủ 12 Chế Độ Job TTC Facebook khớp với APK MToolv2
    JOB_MODES = {
        "like_vip": {
            "name": "Like Bài Viết VIP",
            "paths": ["/kiemtien/likepostvipcheo"],
            "action": "LIKE"
        },
        "like_re": {
            "name": "Like Bài Viết Rẻ/Thường",
            "paths": ["/kiemtien/likepostvipre", "/kiemtien"],
            "action": "LIKE"
        },
        "camxuc_vip": {
            "name": "Cảm Xúc VIP",
            "paths": ["/kiemtien/camxucvipcheo"],
            "action": "REACT"
        },
        "camxuc_re": {
            "name": "Cảm Xúc Rẻ/Thường",
            "paths": ["/kiemtien/camxucvipre", "/kiemtien/camxuccheo"],
            "action": "REACT"
        },
        "sub_vip": {
            "name": "Theo Dõi (Sub) VIP",
            "paths": ["/kiemtien/subcheo"],
            "action": "FOLLOW"
        },
        "sub_re": {
            "name": "Theo Dõi (Sub) Rẻ",
            "paths": ["/kiemtien/subcheore", "/kiemtien/subcheo"],
            "action": "FOLLOW"
        },
        "cmt_vip": {
            "name": "Comment VIP",
            "paths": ["/kiemtien/cmtcheo"],
            "action": "COMMENT"
        },
        "cmt_re": {
            "name": "Comment Rẻ/Thường",
            "paths": ["/kiemtien/cmtcheore", "/kiemtien/cmtcheo"],
            "action": "COMMENT"
        },
        "likepage_vip": {
            "name": "Like Fanpage VIP",
            "paths": ["/kiemtien/likepagecheo"],
            "action": "LIKE_PAGE"
        },
        "likepage_re": {
            "name": "Like Fanpage Rẻ",
            "paths": ["/kiemtien/likepagecheore", "/kiemtien/likepagecheo"],
            "action": "LIKE_PAGE"
        },
        "share": {
            "name": "Chia Sẻ (Share)",
            "paths": ["/kiemtien/sharecheo"],
            "action": "SHARE"
        },
        "camxuc_cmt": {
            "name": "Cảm Xúc Comment",
            "paths": ["/kiemtien/camxuccmtcheo", "/kiemtien/camxuccmtcheore"],
            "action": "REACT_CMT"
        }
    }

    REACTION_CODE_MAP = {
        "LIKE": 1,
        "LOVE": 2,
        "WOW": 3,
        "HAHA": 4,
        "SAD": 7,
        "ANGRY": 8,
        "CARE": 16,
        "THUONG": 16,
        "THƯƠNG THƯƠNG": 16
    }

    def __init__(self, ttc_token, proxy=None):
        self.ttc_token = (ttc_token or "").strip()
        self.proxies = format_proxies(proxy)
        self.session = requests.Session()
        self.session.verify = False
        if self.proxies:
            self.session.proxies.update(self.proxies)

        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        })

        self.logged_in = False
        self.ttc_user = ""
        self.coins = 0
        self.configured_uid = ""
        self.fb_dtsg_cache = {}  # page_id -> fb_dtsg

    # --------------------------------------------------------------------------
    # 1. ĐĂNG NHẬP TOKEN TTC -> GIỮ PHPSESSID TRONG SESSION
    # --------------------------------------------------------------------------
    def login(self):
        try:
            url = f"{self.BASE_URL}/logintoken.php"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/"
            }
            resp = self.session.post(url, data={"access_token": self.ttc_token}, headers=headers, timeout=20)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    return False, f"Phản hồi TTC không phải JSON: {resp.text[:80]}"

                if str(data.get("status", "")).lower() == "success":
                    info = data.get("data", {})
                    self.ttc_user = str(info.get("user", "TTC_User"))
                    self.coins = int(info.get("sodu", 0))
                    self.logged_in = True
                    return True, f"Login TTC thành công: {self.ttc_user} | Số dư: {self.coins:,} xu"
                else:
                    return False, str(data.get("mess", "Token TTC không hợp lệ hoặc chờ 60s login lại"))
            return False, f"Lỗi HTTP {resp.status_code} khi đăng nhập TTC"
        except Exception as e:
            return False, f"Lỗi kết nối TTC: {e}"

    # --------------------------------------------------------------------------
    # 2. LẤY DANH SÁCH NICK FB ĐÃ THÊM TRONG CẤU HÌNH TTC
    # --------------------------------------------------------------------------
    def get_configured_nicks(self):
        if not self.logged_in:
            ok, _ = self.login()
            if not ok:
                return []
        try:
            url = f"{self.BASE_URL}/cauhinh/facebook.php"
            resp = self.session.get(url, timeout=20)
            html = resp.text
            # Tìm các checkbox/id cấu hình nick fb trên trang cauhinh/facebook.php
            uids = re.findall(r'value=["\'](\d{6,25})["\']', html)
            if not uids:
                uids = re.findall(r'id=["\'](\d{10,25})["\']', html)
            return list(dict.fromkeys(uids))
        except Exception:
            return []

    # --------------------------------------------------------------------------
    # 3. ĐẶT NICK FACEBOOK LÀM NICK CHẠY CHÍNH (BẮT BUỘC TRƯỚC KHI QUÉT JOB)
    # --------------------------------------------------------------------------
    def dat_nick(self, fb_uid):
        fb_uid = str(fb_uid).strip()
        if not self.logged_in:
            ok, msg = self.login()
            if not ok:
                return False, msg

        try:
            url = f"{self.BASE_URL}/cauhinh/datnick.php"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/cauhinh/facebook.php"
            }
            payload = {
                "iddat[]": fb_uid,
                "loai": "fb"
            }
            resp = self.session.post(url, data=payload, headers=headers, timeout=20)
            raw = resp.text.strip()
            if raw == "1" or '"1"' in raw or raw == "true":
                self.configured_uid = fb_uid
                return True, f"Đặt cấu hình thành công cho UID/Page {fb_uid}"

            # Kiểm tra xem UID đã có trong danh sách cấu hình của web chưa
            configured_list = self.get_configured_nicks()
            if configured_list and fb_uid not in configured_list:
                return False, f"UID {fb_uid} chưa được thêm vào trang Cấu hình trên tuongtaccheo.com! (Đang có: {', '.join(configured_list[:5])})"

            return False, f"Đặt nick thất bại (Phản hồi: {raw}). Hãy thêm UID {fb_uid} vào Cấu hình Facebook trên web TTC!"
        except Exception as e:
            return False, f"Lỗi gọi datnick.php: {e}"

    # --------------------------------------------------------------------------
    # 4. QUÉT JOB THEO MỤC (GETPOST.PHP - CHUẨN HEADER XMLHTTPREQUEST MTOOLV2)
    # --------------------------------------------------------------------------
    def get_tasks(self, job_key):
        """
        Trả về: (list_jobs, status_message, countdown_seconds)
        """
        cfg = self.JOB_MODES.get(job_key)
        if not cfg:
            return [], f"Không hỗ trợ mục {job_key}", 0

        for sub_path in cfg["paths"]:
            url = f"{self.BASE_URL}{sub_path}/getpost.php"
            headers = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.BASE_URL}{sub_path}/"
            }
            try:
                resp = self.session.get(url, headers=headers, timeout=20)
                raw = resp.text.strip()
                if not raw:
                    continue

                # Kiểm tra nếu trả về Object báo countdown hoặc lỗi
                if raw.startswith("{"):
                    try:
                        obj = json.loads(raw)
                        if "countdown" in obj:
                            cd = int(obj.get("countdown") or 5)
                            return [], f"Mục {cfg['name']} bị countdown {cd}s", cd
                        if "error" in obj or "mess" in obj:
                            err_str = obj.get("error") or obj.get("mess")
                            return [], f"TTC báo ({cfg['name']}): {err_str}", 5
                    except Exception:
                        pass
                    continue

                # Parse danh sách Job dạng JSON Array
                if raw.startswith("["):
                    arr = json.loads(raw)
                    jobs = []
                    for item in arr:
                        if not isinstance(item, dict):
                            continue
                        idpost = str(item.get("idpost") or item.get("id") or "").strip()
                        link = str(item.get("link") or "").strip()
                        loaicx = str(item.get("loaicx") or "LIKE").strip().upper()
                        nd = item.get("nd", "")
                        if idpost:
                            jobs.append({
                                "idpost": idpost,
                                "link": link,
                                "loaicx": loaicx,
                                "nd": nd,
                                "sub_path": sub_path,
                                "job_key": job_key,
                                "job_name": cfg["name"],
                                "action": cfg["action"]
                            })
                    if jobs:
                        return jobs, f"Quét được {len(jobs)} job {cfg['name']}", 0
            except Exception:
                continue

        return [], f"Hết nhiệm vụ {cfg['name']}", 0

    # --------------------------------------------------------------------------
    # 5. NHẬN XU SAU KHI HOÀN THÀNH JOB (NHANTIEN.PHP)
    # --------------------------------------------------------------------------
    def claim_reward(self, job_key, idpost, sub_path=None):
        cfg = self.JOB_MODES.get(job_key, {})
        if not sub_path:
            sub_path = cfg.get("paths", ["/kiemtien/likepostvipcheo"])[0]

        url = f"{self.BASE_URL}{sub_path}/nhantien.php"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}{sub_path}/"
        }
        try:
            resp = self.session.post(url, data={"id": str(idpost).strip()}, headers=headers, timeout=20)
            raw = resp.text.strip()
            if not raw:
                return False, "Phản hồi nhận tiền rỗng", self.coins

            data = json.loads(raw)
            if "mess" in data:
                if "sodu" in data:
                    try:
                        self.coins = int(data["sodu"])
                    except Exception:
                        pass
                return True, str(data["mess"]), self.coins
            if "error" in data:
                return False, str(data["error"]), self.coins
            return False, raw[:100], self.coins
        except Exception as e:
            return False, f"Lỗi nhận tiền: {e}", self.coins

    # --------------------------------------------------------------------------
    # 6. THỰC THI TƯƠNG TÁC TRÊN FACEBOOK (CHUẨN GRAPHQL MTOOLV2 + GRAPH API)
    # --------------------------------------------------------------------------
    def _build_page_cookie(self, parent_cookie, actor_id):
        if not parent_cookie:
            return ""
        actor_id = str(actor_id).strip()
        c_user_m = re.search(r"c_user=(\d+)", parent_cookie)
        c_user = c_user_m.group(1) if c_user_m else ""
        cleaned = re.sub(r"i_user=\d+;?\s*", "", parent_cookie).strip().rstrip(";")
        if c_user and actor_id and c_user != actor_id:
            return f"{cleaned}; i_user={actor_id};"
        return cleaned

    def get_fb_dtsg(self, page_id, parent_cookie):
        page_id = str(page_id).strip()
        if page_id in self.fb_dtsg_cache and self.fb_dtsg_cache[page_id]:
            return self.fb_dtsg_cache[page_id]

        eff_cookie = self._build_page_cookie(parent_cookie, page_id)
        if not eff_cookie:
            return ""

        headers = {
            "User-Agent": self.USER_AGENT,
            "Cookie": eff_cookie,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        urls = [
            "https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed",
            "https://mbasic.facebook.com/home.php",
            "https://www.facebook.com/"
        ]
        patterns = [
            r'name=\\"fb_dtsg\\" value=\\"([^\\"]+)\\"',
            r'name="fb_dtsg" value="([^"]+)"',
            r'"DTSGInitialData",\[\],\{"token":"([^"]+)"',
            r'"dtsg":\{"token":"([^"]+)"'
        ]
        for u in urls:
            try:
                r = requests.get(u, headers=headers, proxies=self.proxies, timeout=15, verify=False)
                for pat in patterns:
                    m = re.search(pat, r.text)
                    if m:
                        token = m.group(1)
                        self.fb_dtsg_cache[page_id] = token
                        return token
            except Exception:
                continue
        return ""

    def _call_fb_graphql(self, page_id, parent_cookie, friendly_name, doc_id, variables_dict):
        fb_dtsg = self.get_fb_dtsg(page_id, parent_cookie)
        if not fb_dtsg:
            return False, "Không lấy được fb_dtsg từ Cookie"

        eff_cookie = self._build_page_cookie(parent_cookie, page_id)
        headers = {
            "User-Agent": self.USER_AGENT,
            "Cookie": eff_cookie,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/"
        }
        payload = {
            "av": str(page_id),
            "__user": str(page_id),
            "__a": "1",
            "fb_dtsg": fb_dtsg,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": friendly_name,
            "variables": json.dumps(variables_dict, ensure_ascii=False),
            "doc_id": str(doc_id)
        }
        try:
            r = requests.post(
                "https://www.facebook.com/api/graphql/",
                data=payload,
                headers=headers,
                proxies=self.proxies,
                timeout=20,
                verify=False
            )
            txt = r.text
            if r.status_code == 200 and '"error":' not in txt and '"errorSummary"' not in txt:
                return True, "GraphQL thành công"
            # Nếu token dtsg hết hạn thì xóa cache để lần sau lấy lại
            if "1357004" in txt or "dtsg" in txt.lower():
                self.fb_dtsg_cache.pop(str(page_id), None)
            return False, f"GraphQL lỗi: {txt[:90]}"
        except Exception as e:
            return False, f"Lỗi mạng GraphQL: {e}"

    def _extract_target_id(self, idpost, link):
        target = str(idpost).strip()
        if "_" in target:
            parts = target.split("_")
            if parts[-1].isdigit():
                return parts[-1]
        if target.isdigit():
            return target
        # Bóc từ link nếu idpost chứa ký tự lạ
        for pat in [
            r"story_fbid=(\d+)",
            r"fbid=(\d+)",
            r"/posts/(\d+)",
            r"/videos/(\d+)",
            r"id=(\d+)",
            r"/(\d{10,25})"
        ]:
            m = re.search(pat, str(link))
            if m:
                return m.group(1)
        return target

    def do_fb_action(self, page_id, page_token, parent_cookie, job):
        """
        Thực thi đầy đủ 12 loại nhiệm vụ TTC FB:
        - Ưu tiên 1: Facebook GraphQL với Cookie + i_user=page_id (chuẩn MToolv2, hỗ trợ đủ 7 cảm xúc, Follow, Like Page, Share, Cmt)
        - Ưu tiên 2: Facebook Graph API với page_token
        """
        action = job.get("action", "LIKE")
        raw_id = job.get("idpost", "")
        link = job.get("link", "")
        loaicx = str(job.get("loaicx", "LIKE")).upper()
        nd_raw = job.get("nd", "")
        target_id = self._extract_target_id(raw_id, link)

        # ----------------------------------------------------------------------
        # NHÓM 1: LIKE & THẢ CẢM XÚC BÀI VIẾT / COMMENT
        # ----------------------------------------------------------------------
        if action in ("LIKE", "REACT", "REACT_CMT"):
            react_type = "LIKE" if action == "LIKE" else loaicx
            react_code = self.REACTION_CODE_MAP.get(react_type, 1)

            if parent_cookie:
                b64_feedback = base64.b64encode(f"feedback:{target_id}".encode("utf-8")).decode("utf-8")
                vars_dict = {
                    "input": {
                        "feedback_id": b64_feedback,
                        "feedback_reaction": react_code,
                        "actor_id": str(page_id),
                        "client_mutation_id": str(random.randint(1, 9))
                    }
                }
                ok, msg = self._call_fb_graphql(
                    page_id, parent_cookie,
                    "CometUFIFeedbackReactMutation",
                    "4769042373179384",
                    vars_dict
                )
                if ok:
                    return True, f"Đã thả {react_type} bài {target_id} (GraphQL)"

            if page_token:
                try:
                    for obj_id in (raw_id, target_id):
                        url = f"https://graph.facebook.com/v18.0/{obj_id}/likes"
                        r = requests.post(
                            url,
                            data={"access_token": page_token},
                            proxies=self.proxies,
                            timeout=15,
                            verify=False
                        )
                        if r.status_code == 200 and "true" in r.text.lower():
                            return True, f"Đã Like {obj_id} (Graph API)"
                except Exception:
                    pass

            return False, f"Không thể {react_type} ID {target_id}"

        # ----------------------------------------------------------------------
        # NHÓM 2: THEO DÕI (SUB / FOLLOW)
        # ----------------------------------------------------------------------
        elif action == "FOLLOW":
            if parent_cookie:
                vars_dict = {
                    "input": {
                        "subscribe_location": "PROFILE",
                        "subscribee_id": str(target_id),
                        "actor_id": str(page_id),
                        "client_mutation_id": "1"
                    }
                }
                ok, msg = self._call_fb_graphql(
                    page_id, parent_cookie,
                    "CometUserFollowMutation",
                    "4451435638222552",
                    vars_dict
                )
                if ok:
                    return True, f"Đã Follow UID {target_id} (GraphQL)"
            return False, f"Follow thất bại UID {target_id}"

        # ----------------------------------------------------------------------
        # NHÓM 3: LIKE FANPAGE
        # ----------------------------------------------------------------------
        elif action == "LIKE_PAGE":
            if parent_cookie:
                vars_dict = {
                    "input": {
                        "is_tracking_encrypted": True,
                        "page_id": str(target_id),
                        "source": "page_profile",
                        "actor_id": str(page_id),
                        "client_mutation_id": "1"
                    }
                }
                ok, msg = self._call_fb_graphql(
                    page_id, parent_cookie,
                    "CometPageLikeMutation",
                    "4911670272228290",
                    vars_dict
                )
                if ok:
                    return True, f"Đã Like Fanpage {target_id} (GraphQL)"
            return False, f"Like Fanpage thất bại ID {target_id}"

        # ----------------------------------------------------------------------
        # NHÓM 4: BÌNH LUẬN (COMMENT)
        # ----------------------------------------------------------------------
        elif action == "COMMENT":
            cmt_text = "Tuyệt vời quá!"
            if nd_raw:
                try:
                    if str(nd_raw).strip().startswith("["):
                        arr = json.loads(nd_raw)
                        if arr:
                            cmt_text = str(random.choice(arr))
                    else:
                        cmt_text = str(nd_raw)
                except Exception:
                    cmt_text = str(nd_raw)

            if parent_cookie:
                b64_feedback = base64.b64encode(f"feedback:{target_id}".encode("utf-8")).decode("utf-8")
                vars_dict = {
                    "input": {
                        "actor_id": str(page_id),
                        "feedback_id": b64_feedback,
                        "message": {"text": cmt_text},
                        "client_mutation_id": "1"
                    }
                }
                ok, msg = self._call_fb_graphql(
                    page_id, parent_cookie,
                    "CometUFICreateCommentMutation",
                    "4700064693380460",
                    vars_dict
                )
                if ok:
                    return True, f"Đã Comment: {cmt_text[:25]}"

            if page_token:
                try:
                    url = f"https://graph.facebook.com/v18.0/{target_id}/comments"
                    r = requests.post(
                        url,
                        data={"message": cmt_text, "access_token": page_token},
                        proxies=self.proxies,
                        timeout=15,
                        verify=False
                    )
                    if r.status_code == 200 and '"id"' in r.text:
                        return True, f"Đã Comment (Graph API): {cmt_text[:25]}"
                except Exception:
                    pass

            return False, f"Comment thất bại bài {target_id}"

        # ----------------------------------------------------------------------
        # NHÓM 5: CHIA SẺ BÀI VIẾT (SHARE)
        # ----------------------------------------------------------------------
        elif action == "SHARE":
            share_url = link if link and link.startswith("http") else f"https://www.facebook.com/{target_id}"
            if parent_cookie:
                scrape_data = json.dumps({
                    "share_type": 100,
                    "share_params": {"urlInfo": {"canonical": share_url}}
                })
                vars_dict = {
                    "input": {
                        "actor_id": str(page_id),
                        "attachment": {"share_scrape_data": scrape_data},
                        "audience": {"privacy": {"base_state": "EVERYONE"}},
                        "client_mutation_id": "1"
                    }
                }
                ok, msg = self._call_fb_graphql(
                    page_id, parent_cookie,
                    "ComposerStoryCreateMutation",
                    "5136685823015775",
                    vars_dict
                )
                if ok:
                    return True, f"Đã Share bài {target_id} (GraphQL)"

            if page_token:
                try:
                    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                    r = requests.post(
                        url,
                        data={"link": share_url, "access_token": page_token},
                        proxies=self.proxies,
                        timeout=15,
                        verify=False
                    )
                    if r.status_code == 200 and '"id"' in r.text:
                        return True, f"Đã Share bài {target_id} (Graph API)"
                except Exception:
                    pass

            return False, f"Share thất bại bài {target_id}"

        return False, f"Chưa hỗ trợ action {action}"
# ==============================================================================
# PHẦN 2: GIAO DIỆN CHÍNH MMOAPP (ĐẦY ĐỦ 4 TAB & CÁC LUỒNG WORKER TỰ ĐỘNG)
# ==============================================================================
class MMOApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MMO Automation Suite Pro v6 - Instagram XSMM & Tương Tác Chéo Facebook (MToolv2 Engine)")
        self.geometry("1440x880")

        init_database()

        # Quản lý trạng thái chạy đa luồng
        self.running_ig = {}          # username -> bool
        self.running_xsmm_pages = {}  # page_id -> bool
        self.running_ttc_pages = {}   # page_id -> bool
        self.page_locks = {}          # page_id -> threading.Lock
        self.ig_locks = {}            # username -> threading.Lock

        # Hàng đợi cập nhật UI an toàn luồng
        self.ui_queue = queue.Queue()

        # Biến lưu 12 Checkbox chế độ Job TTC
        self.ttc_job_vars = {}

        # Khởi tạo toàn bộ giao diện 4 Tab
        self.setup_ui()
        self.refresh_all_tables()
        self.after(150, self.process_ui_queue)

    # ==========================================================================
    # KHỞI TẠO CẤU TRÚC 4 TAB CHÍNH
    # ==========================================================================
    def setup_ui(self):
        # Thanh Header Thống kê nhanh
        self.header_frame = ctk.CTkFrame(self, height=48, corner_radius=8)
        self.header_frame.pack(fill="x", padx=10, pady=(8, 2))

        self.lbl_stat_ig = ctk.CTkLabel(self.header_frame, text="📸 Nick IG: 0", font=("Arial", 13, "bold"), text_color="#38bdf8")
        self.lbl_stat_ig.pack(side="left", padx=18, pady=8)

        self.lbl_stat_fb = ctk.CTkLabel(self.header_frame, text="👤 Nick FB Gốc: 0", font=("Arial", 13, "bold"), text_color="#a78bfa")
        self.lbl_stat_fb.pack(side="left", padx=18, pady=8)

        self.lbl_stat_pages = ctk.CTkLabel(self.header_frame, text="🚩 Tổng Fanpage/Profile: 0", font=("Arial", 13, "bold"), text_color="#4ade80")
        self.lbl_stat_pages.pack(side="left", padx=18, pady=8)

        self.lbl_stat_ttc = ctk.CTkLabel(self.header_frame, text="🔥 Tài Khoản TTC: 0", font=("Arial", 13, "bold"), text_color="#fb923c")
        self.lbl_stat_ttc.pack(side="left", padx=18, pady=8)

        self.lbl_stat_running = ctk.CTkLabel(self.header_frame, text="⚡ Luồng Đang Chạy: 0", font=("Arial", 13, "bold"), text_color="#facc15")
        self.lbl_stat_running.pack(side="right", padx=18, pady=8)

        # Tabview chính tách biệt hoàn toàn XSMM và Tương Tác Chéo
        self.tabview = ctk.CTkTabview(self, width=1420, height=800)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_ttc = self.tabview.add("🔥 Tương Tác Chéo (TTC FB)")
        self.tab_fb_pages = self.tabview.add("🚩 Quản Lý Nick FB & Quét Page (XSMM/TTC)")
        self.tab_accounts = self.tabview.add("📸 Quản Lý Instagram (XSMM)")
        self.tab_dashboard = self.tabview.add("📊 Nhật Ký Hệ Thống (Logs)")

        self.setup_tab_ttc()
        self.setup_tab_fb_pages()
        self.setup_tab_accounts()
        self.setup_tab_dashboard()

    # ==========================================================================
    # TAB 1: TƯƠNG TÁC CHÉO FACEBOOK (12 CHẾ ĐỘ JOB + QUẢN LÝ TOKEN TTC + WORKER)
    # ==========================================================================
    def setup_tab_ttc(self):
        # --- Phần A: Quản lý danh sách Token TTC & Gắn cho Page ---
        top_pane = ctk.CTkFrame(self.tab_ttc)
        top_pane.pack(fill="x", padx=6, pady=4)

        left_ttc = ctk.CTkFrame(top_pane)
        left_ttc.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(left_ttc, text="🔑 Token Tương Tác Chéo:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.ent_ttc_token = ctk.CTkEntry(left_ttc, width=260, placeholder_text="Dán Access Token TTC vào đây...")
        self.ent_ttc_token.grid(row=0, column=1, padx=5, pady=4)

        ctk.CTkButton(left_ttc, text="➕ Thêm / Check Token TTC", width=165, fg_color="#16a34a", command=self.add_or_check_ttc_token).grid(row=0, column=2, padx=4, pady=4)
        ctk.CTkButton(left_ttc, text="🗑️ Xóa Token TTC", width=120, fg_color="#dc2626", command=self.delete_selected_ttc_token).grid(row=0, column=3, padx=4, pady=4)

        # Bảng nhỏ hiển thị danh sách tài khoản TTC
        cols_ttc_acc = ("ttc_user", "ttc_token", "coins", "status")
        self.tree_ttc_accounts = ttk.Treeview(left_ttc, columns=cols_ttc_acc, show="headings", height=3)
        for col, title, w in [
            ("ttc_user", "User TTC", 130),
            ("ttc_token", "Access Token TTC", 210),
            ("coins", "Số Dư Xu", 100),
            ("status", "Trạng Thái", 130)
        ]:
            self.tree_ttc_accounts.heading(col, text=title)
            self.tree_ttc_accounts.column(col, width=w, anchor="center")
        self.tree_ttc_accounts.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=5, pady=4)

        # Khung phải: Gắn Token TTC & Thêm nhanh Nick/Page chạy TTC
        right_ttc = ctk.CTkFrame(top_pane)
        right_ttc.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(right_ttc, text="🔗 Chọn Token TTC gắn cho Page:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.cmb_assign_ttc = ctk.CTkComboBox(right_ttc, width=210, values=["-- Chưa có Token TTC --"])
        self.cmb_assign_ttc.grid(row=0, column=1, padx=5, pady=4)
        ctk.CTkButton(right_ttc, text="Gắn Cho Page Đã Chọn", fg_color="#d97706", width=155, command=self.assign_ttc_to_selected_pages).grid(row=0, column=2, padx=4, pady=4)
        ctk.CTkButton(right_ttc, text="Gắn Cho Tất Cả Page", fg_color="#b45309", width=145, command=self.assign_ttc_to_all_pages).grid(row=0, column=3, padx=4, pady=4)

        # Thêm nhanh 1 Nick/Page trực tiếp tại Tab TTC
        ctk.CTkLabel(right_ttc, text="⚡ Thêm nhanh UID/Page:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=5, pady=4, sticky="w")
        self.ent_quick_uid = ctk.CTkEntry(right_ttc, width=140, placeholder_text="UID / Page ID (Để trống tự tách)")
        self.ent_quick_uid.grid(row=1, column=1, padx=5, pady=4, sticky="w")
        self.ent_quick_name = ctk.CTkEntry(right_ttc, width=145, placeholder_text="Tên gợi nhớ...")
        self.ent_quick_name.grid(row=1, column=2, padx=4, pady=4)
        ctk.CTkButton(right_ttc, text="➕ Lưu Vào Bảng TTC", fg_color="#0284c7", width=145, command=self.quick_add_ttc_page).grid(row=1, column=3, padx=4, pady=4)

        ctk.CTkLabel(right_ttc, text="🍪 Cookie FB (c_user, xs):").grid(row=2, column=0, padx=5, pady=4, sticky="w")
        self.ent_quick_cookie = ctk.CTkEntry(right_ttc, width=310, placeholder_text="Dán Cookie Facebook cầm Nick/Page vào đây...")
        self.ent_quick_cookie.grid(row=2, column=1, columnspan=2, padx=5, pady=4, sticky="we")
        self.ent_quick_proxy = ctk.CTkEntry(right_ttc, width=145, placeholder_text="Proxy (ip:port:u:p)")
        self.ent_quick_proxy.grid(row=2, column=3, padx=4, pady=4)

        # --- Phần B: 12 Chế Độ Job TTC Facebook & Cấu Hình Delay ---
        modes_frame = ctk.CTkFrame(self.tab_ttc)
        modes_frame.pack(fill="x", padx=6, pady=4)

        ctk.CTkLabel(modes_frame, text="☑️ TÍCH CHỌN 12 CHẾ ĐỘ NHIỆM VỤ TTC FACEBOOK:", font=("Arial", 12, "bold"), text_color="#38bdf8").grid(
            row=0, column=0, columnspan=2, padx=8, pady=4, sticky="w"
        )
        ctk.CTkButton(modes_frame, text="Chọn Tất Cả", width=95, height=24, command=lambda: self.toggle_all_ttc_modes(True)).grid(row=0, column=2, padx=4, pady=4, sticky="w")
        ctk.CTkButton(modes_frame, text="Bỏ Chọn Hết", width=95, height=24, fg_color="#475569", command=lambda: self.toggle_all_ttc_modes(False)).grid(row=0, column=3, padx=4, pady=4, sticky="w")

        ctk.CTkLabel(modes_frame, text="Delay Min-Max (giây):").grid(row=0, column=4, padx=4, pady=4, sticky="e")
        delay_box = ctk.CTkFrame(modes_frame, fg_color="transparent")
        delay_box.grid(row=0, column=5, padx=4, pady=4, sticky="w")
        self.ent_ttc_delay_min = ctk.CTkEntry(delay_box, width=50)
        self.ent_ttc_delay_min.insert(0, "6")
        self.ent_ttc_delay_min.pack(side="left", padx=2)
        ctk.CTkLabel(delay_box, text="-").pack(side="left")
        self.ent_ttc_delay_max = ctk.CTkEntry(delay_box, width=50)
        self.ent_ttc_delay_max.insert(0, "10")
        self.ent_ttc_delay_max.pack(side="left", padx=2)

        mode_list = [
            ("like_vip", "1. Like Post VIP"),
            ("like_re", "2. Like Post Rẻ"),
            ("camxuc_vip", "3. Cảm Xúc VIP"),
            ("camxuc_re", "4. Cảm Xúc Rẻ"),
            ("sub_vip", "5. Theo Dõi (Sub) VIP"),
            ("sub_re", "6. Theo Dõi (Sub) Rẻ"),
            ("cmt_vip", "7. Comment VIP"),
            ("cmt_re", "8. Comment Rẻ"),
            ("likepage_vip", "9. Like Fanpage VIP"),
            ("likepage_re", "10. Like Fanpage Rẻ"),
            ("share", "11. Chia Sẻ (Share)"),
            ("camxuc_cmt", "12. Cảm Xúc Cmt")
        ]
        for idx, (m_key, m_label) in enumerate(mode_list):
            default_checked = m_key in ("like_vip", "like_re", "camxuc_vip", "camxuc_re", "sub_vip", "likepage_vip")
            var = ctk.BooleanVar(value=default_checked)
            self.ttc_job_vars[m_key] = var
            r = (idx // 6) + 1
            c = idx % 6
            cb = ctk.CTkCheckBox(modes_frame, text=m_label, variable=var, font=("Arial", 12))
            cb.grid(row=r, column=c, padx=10, pady=4, sticky="w")

        # --- Phần C: Thanh công cụ Điều Khiển Chạy / Dừng / Kiểm Tra Cấu Hình ---
        ctrl_bar = ctk.CTkFrame(self.tab_ttc)
        ctrl_bar.pack(fill="x", padx=6, pady=4)

        ctk.CTkButton(ctrl_bar, text="▶️ CHẠY PAGE ĐÃ CHỌN", fg_color="#16a34a", width=175, command=self.start_selected_ttc_pages).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="⏹️ DỪNG PAGE ĐÃ CHỌN", fg_color="#dc2626", width=175, command=self.stop_selected_ttc_pages).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="🚀 CHẠY TẤT CẢ PAGE TTC", fg_color="#2563eb", width=190, command=self.start_all_ttc_pages).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="🛑 DỪNG TẤT CẢ", fg_color="#7f1d1d", width=135, command=self.stop_all_ttc_pages).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="⚙️ Test Đặt Cấu Hình & Check fb_dtsg", fg_color="#7c3aed", width=230, command=self.test_datnick_selected_page).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="🗑️ Xóa Page Chọn", fg_color="#475569", width=130, command=self.delete_selected_ttc_pages).pack(side="right", padx=5, pady=5)
        ctk.CTkButton(ctrl_bar, text="🔄 Làm Mới", width=105, command=self.refresh_all_tables).pack(side="right", padx=5, pady=5)

        # --- Phần D: Bảng Danh Sách Fanpage / Nick Chạy TTC ---
        tbl_frame = ctk.CTkFrame(self.tab_ttc)
        tbl_frame.pack(fill="both", expand=True, padx=6, pady=4)

        cols_ttc_page = ("id", "parent", "page_id", "page_name", "assigned_ttc", "proxy", "coins", "max_jobs", "status")
        self.tree_ttc_pages = ttk.Treeview(tbl_frame, columns=cols_ttc_page, show="headings", height=10, selectmode="extended")
        col_specs = [
            ("id", "ID", 45),
            ("parent", "Nick Gốc", 110),
            ("page_id", "UID / Page ID", 145),
            ("page_name", "Tên Fanpage / Nick FB", 190),
            ("assigned_ttc", "Tài Khoản TTC Gắn Kèm", 160),
            ("proxy", "Proxy", 130),
            ("coins", "Xu TTC", 100),
            ("max_jobs", "Max Jobs", 75),
            ("status", "Trạng Thái Hoạt Động Chi Tiết", 410)
        ]
        for col, text, w in col_specs:
            self.tree_ttc_pages.heading(col, text=text)
            self.tree_ttc_pages.column(col, width=w, anchor="w" if col in ("page_name", "status") else "center")

        self.tree_ttc_pages.pack(side="left", fill="both", expand=True)
        sb_ttc = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree_ttc_pages.yview)
        self.tree_ttc_pages.configure(yscroll=sb_ttc.set)
        sb_ttc.pack(side="right", fill="y")

        # --- Phần E: Khung Nhật Ký Trực Tiếp Tại Tab TTC ---
        log_box = ctk.CTkFrame(self.tab_ttc, height=135)
        log_box.pack(fill="x", padx=6, pady=4)
        self.txt_ttc_live_log = ctk.CTkTextbox(log_box, height=125, font=("Consolas", 12))
        self.txt_ttc_live_log.pack(fill="both", expand=True, padx=4, pady=4)

    # ==========================================================================
    # TAB 2: QUẢN LÝ NICK FACEBOOK GỐC & QUÉT FANPAGE (HỖ TRỢ CẢ XSMM & TTC)
    # ==========================================================================
    def setup_tab_fb_pages(self):
        input_frame = ctk.CTkFrame(self.tab_fb_pages)
        input_frame.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(input_frame, text="🍪 Cookie FB Mẹ:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=6, pady=5, sticky="e")
        self.ent_fb_cookie = ctk.CTkEntry(input_frame, width=380, placeholder_text="c_user=...; xs=...; (Dùng để làm job & quét Page không cần Token)")
        self.ent_fb_cookie.grid(row=0, column=1, columnspan=2, padx=6, pady=5, sticky="we")

        ctk.CTkLabel(input_frame, text="🔑 Token EAAG/EAAB (Nếu có):").grid(row=0, column=3, padx=6, pady=5, sticky="e")
        self.ent_fb_token = ctk.CTkEntry(input_frame, width=280, placeholder_text="EAAG... (Quét Page qua Graph API)")
        self.ent_fb_token.grid(row=0, column=4, padx=6, pady=5, sticky="we")

        ctk.CTkLabel(input_frame, text="🌐 Proxy:").grid(row=1, column=0, padx=6, pady=5, sticky="e")
        self.ent_fb_proxy = ctk.CTkEntry(input_frame, width=200, placeholder_text="ip:port:user:pass")
        self.ent_fb_proxy.grid(row=1, column=1, padx=6, pady=5, sticky="w")

        ctk.CTkLabel(input_frame, text="🎯 Nền tảng mặc định khi quét:").grid(row=1, column=2, padx=6, pady=5, sticky="e")
        self.cmb_scan_platform = ctk.CTkComboBox(input_frame, width=140, values=["TTC", "XSMM"])
        self.cmb_scan_platform.set("TTC")
        self.cmb_scan_platform.grid(row=1, column=3, padx=6, pady=5, sticky="w")

        ctk.CTkLabel(input_frame, text="🔑 XSMM API Token (Nếu chạy XSMM):").grid(row=1, column=4, padx=6, pady=5, sticky="w")
        self.ent_xsmm_page_api = ctk.CTkEntry(input_frame, width=220, placeholder_text="Nhập API Token xsmm.net...")
        self.ent_xsmm_page_api.grid(row=1, column=5, padx=6, pady=5)

        btn_row = ctk.CTkFrame(self.tab_fb_pages)
        btn_row.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(btn_row, text="🔍 Lưu Nick FB & Tự Động Quét Toàn Bộ Fanpage (Cookie + GraphAPI)", fg_color="#2563eb", width=410, command=self.add_fb_and_scan_pages).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(btn_row, text="➕ Chỉ Thêm Chính Nick FB Này Làm Nick Chạy TTC", fg_color="#16a34a", width=310, command=self.add_main_fb_as_worker_page).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(btn_row, text="▶️ Chạy Page XSMM Đã Chọn", fg_color="#d97706", width=190, command=self.start_selected_xsmm_pages).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(btn_row, text="⏹️ Dừng Page XSMM", fg_color="#dc2626", width=150, command=self.stop_selected_xsmm_pages).pack(side="left", padx=6, pady=6)

        # Bảng 1: Danh sách Tài khoản Facebook gốc
        ctk.CTkLabel(self.tab_fb_pages, text="📌 DANH SÁCH TÀI KHOẢN FACEBOOK GỐC:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        fb_acc_frame = ctk.CTkFrame(self.tab_fb_pages)
        fb_acc_frame.pack(fill="x", padx=8, pady=4)

        cols_fb = ("id", "fb_uid", "fb_name", "proxy", "status")
        self.tree_fb_accounts = ttk.Treeview(fb_acc_frame, columns=cols_fb, show="headings", height=5)
        for c, t, w in [
            ("id", "ID", 50),
            ("fb_uid", "UID Facebook Gốc", 200),
            ("fb_name", "Tên Tài Khoản FB", 260),
            ("proxy", "Proxy", 220),
            ("status", "Trạng Thái", 350)
        ]:
            self.tree_fb_accounts.heading(c, text=t)
            self.tree_fb_accounts.column(c, width=w, anchor="center")
        self.tree_fb_accounts.pack(fill="x", expand=True)

        # Bảng 2: Tất cả Fanpage đã liên kết
        ctk.CTkLabel(self.tab_fb_pages, text="🚩 TẤT CẢ FANPAGE / PROFILE ĐÃ QUÉT TRONG DATABASE:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        all_page_frame = ctk.CTkFrame(self.tab_fb_pages)
        all_page_frame.pack(fill="both", expand=True, padx=8, pady=4)

        cols_all_p = ("id", "parent", "page_id", "page_name", "platform", "coins", "status")
        self.tree_all_pages = ttk.Treeview(all_page_frame, columns=cols_all_p, show="headings", height=11)
        for c, t, w in [
            ("id", "ID", 50),
            ("parent", "Nick FB Mẹ", 160),
            ("page_id", "Page ID / UID", 180),
            ("page_name", "Tên Fanpage", 250),
            ("platform", "Nền Tảng", 100),
            ("coins", "Xu Tích Lũy", 120),
            ("status", "Trạng Thái", 420)
        ]:
            self.tree_all_pages.heading(c, text=t)
            self.tree_all_pages.column(c, width=w, anchor="center")
        self.tree_all_pages.pack(fill="both", expand=True)

    # ==========================================================================
    # TAB 3: QUẢN LÝ INSTAGRAM (CHẠY XSMM)
    # ==========================================================================
    def setup_tab_accounts(self):
        top_ig = ctk.CTkFrame(self.tab_accounts)
        top_ig.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(top_ig, text="🔑 XSMM API Key:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.ent_ig_xsmm_token = ctk.CTkEntry(top_ig, width=240, placeholder_text="Token xsmm.net...")
        self.ent_ig_xsmm_token.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(top_ig, text="🍪 Cookie Instagram:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        self.ent_ig_cookie = ctk.CTkEntry(top_ig, width=320, placeholder_text="sessionid=...; csrftoken=...; ds_user_id=...")
        self.ent_ig_cookie.grid(row=0, column=3, padx=6, pady=6)

        ctk.CTkLabel(top_ig, text="🌐 Proxy:").grid(row=0, column=4, padx=6, pady=6, sticky="e")
        self.ent_ig_proxy = ctk.CTkEntry(top_ig, width=160, placeholder_text="ip:port:user:pass")
        self.ent_ig_proxy.grid(row=0, column=5, padx=6, pady=6)

        ctk.CTkLabel(top_ig, text="Max Jobs:").grid(row=0, column=6, padx=6, pady=6, sticky="e")
        self.ent_ig_maxjobs = ctk.CTkEntry(top_ig, width=70)
        self.ent_ig_maxjobs.insert(0, "100")
        self.ent_ig_maxjobs.grid(row=0, column=7, padx=6, pady=6)

        ig_btns = ctk.CTkFrame(self.tab_accounts)
        ig_btns.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(ig_btns, text="➕ Thêm & Check Nick IG", fg_color="#16a34a", command=self.add_ig_account).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ig_btns, text="📂 Import File Cookie IG", fg_color="#0284c7", command=self.import_ig_file).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ig_btns, text="▶️ Chạy Nick IG Đã Chọn", fg_color="#2563eb", command=self.start_selected_ig).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ig_btns, text="⏹️ Dừng Nick IG Đã Chọn", fg_color="#dc2626", command=self.stop_selected_ig).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(ig_btns, text="🗑️ Xóa Nick IG", fg_color="#475569", command=self.delete_selected_ig).pack(side="right", padx=5, pady=5)

        ig_tbl_frame = ctk.CTkFrame(self.tab_accounts)
        ig_tbl_frame.pack(fill="both", expand=True, padx=8, pady=6)

        cols_ig = ("id", "username", "proxy", "coins", "max_jobs", "status")
        self.tree_ig = ttk.Treeview(ig_tbl_frame, columns=cols_ig, show="headings", height=18)
        for c, t, w in [
            ("id", "ID", 50),
            ("username", "Username Instagram", 200),
            ("proxy", "Proxy", 200),
            ("coins", "Coins Đã Kiếm", 130),
            ("max_jobs", "Max Jobs", 100),
            ("status", "Trạng Thái Hoạt Động", 520)
        ]:
            self.tree_ig.heading(c, text=t)
            self.tree_ig.column(c, width=w, anchor="center")
        self.tree_ig.pack(fill="both", expand=True)

    # ==========================================================================
    # TAB 4: DASHBOARD & NHẬT KÝ HỆ THỐNG (LOGS)
    # ==========================================================================
    def setup_tab_dashboard(self):
        top_dash = ctk.CTkFrame(self.tab_dashboard)
        top_dash.pack(fill="x", padx=8, pady=6)

        ctk.CTkLabel(top_dash, text="📜 NHẬT KÝ HOẠT ĐỘNG CHI TIẾT TOÀN HỆ THỐNG", font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=6)
        ctk.CTkButton(top_dash, text="🧹 Xóa Sạch Nhật Ký", fg_color="#dc2626", width=160, command=self.clear_all_logs).pack(side="right", padx=10, pady=6)
        ctk.CTkButton(top_dash, text="🔄 Tải Lại Nhật Ký DB", width=160, command=self.load_db_logs_to_view).pack(side="right", padx=10, pady=6)

        self.txt_system_log = ctk.CTkTextbox(self.tab_dashboard, font=("Consolas", 12))
        self.txt_system_log.pack(fill="both", expand=True, padx=8, pady=6)

    # ==========================================================================
    # ĐỒNG BỘ GIAO DIỆN & HÀNG ĐỢI UI THREAD-SAFE
    # ==========================================================================
    def emit_log(self, actor_name, action_text, status_text="OK"):
        now_str = datetime.now().strftime("%H:%M:%S")
        line = f"[{now_str}] [{actor_name}] {action_text} -> {status_text}\n"
        self.ui_queue.put(("live_log", line))
        log_to_db(actor_name, action_text, status_text)

    def update_ttc_page_ui(self, page_id, status_text=None, coins=None):
        self.ui_queue.put(("ttc_page_row", (str(page_id), status_text, coins)))

    def update_ig_ui(self, username, status_text=None, coins=None):
        self.ui_queue.put(("ig_row", (str(username), status_text, coins)))

    def process_ui_queue(self):
        try:
            while not self.ui_queue.empty():
                kind, data = self.ui_queue.get_nowait()
                if kind == "live_log":
                    self.txt_ttc_live_log.insert("end", data)
                    self.txt_ttc_live_log.see("end")
                    self.txt_system_log.insert("end", data)
                    self.txt_system_log.see("end")
                elif kind == "ttc_page_row":
                    pid, st_text, coins_val = data
                    for tree in (self.tree_ttc_pages, self.tree_all_pages):
                        for item_id in tree.get_children():
                            vals = list(tree.item(item_id, "values"))
                            if str(vals[2]) == pid:
                                if coins_val is not None:
                                    vals[6 if tree == self.tree_ttc_pages else 5] = coins_val
                                if st_text is not None:
                                    vals[-1] = st_text
                                tree.item(item_id, values=vals)
                                break
                elif kind == "ig_row":
                    uname, st_text, coins_val = data
                    for item_id in self.tree_ig.get_children():
                        vals = list(self.tree_ig.item(item_id, "values"))
                        if str(vals[1]) == uname:
                            if coins_val is not None:
                                vals[3] = coins_val
                            if st_text is not None:
                                vals[5] = st_text
                            self.tree_ig.item(item_id, values=vals)
                            break
        except Exception:
            pass

        # Cập nhật số luồng đang chạy
        active_cnt = (
            sum(1 for v in self.running_ttc_pages.values() if v)
            + sum(1 for v in self.running_ig.values() if v)
            + sum(1 for v in self.running_xsmm_pages.values() if v)
        )
        self.lbl_stat_running.configure(text=f"⚡ Luồng Đang Chạy: {active_cnt}")
        self.after(150, self.process_ui_queue)

    def refresh_all_tables(self):
        with db_lock:
            conn = get_db_connection()
            c = conn.cursor()

            # 1. Bảng Tài khoản TTC
            for i in self.tree_ttc_accounts.get_children():
                self.tree_ttc_accounts.delete(i)
            ttc_rows = c.execute("SELECT ttc_user, ttc_token, coins, status FROM ttc_accounts").fetchall()
            ttc_map = {}
            combo_items = []
            for u, tk, coins, st in ttc_rows:
                self.tree_ttc_accounts.insert("", "end", values=(u, tk, f"{coins:,}", st))
                ttc_map[tk] = (u, coins)
                combo_items.append(f"{u} | {tk[:10]}...")

            if combo_items:
                self.cmb_assign_ttc.configure(values=combo_items)
                self.cmb_assign_ttc.set(combo_items[0])
            else:
                self.cmb_assign_ttc.configure(values=["-- Chưa có Token TTC --"])
                self.cmb_assign_ttc.set("-- Chưa có Token TTC --")

            # 2. Bảng Fanpage TTC & Bảng Tất cả Fanpage
            for i in self.tree_ttc_pages.get_children():
                self.tree_ttc_pages.delete(i)
            for i in self.tree_all_pages.get_children():
                self.tree_all_pages.delete(i)

            page_rows = c.execute(
                "SELECT id, parent_username, page_id, page_name, assigned_ttc, proxy, coins, max_jobs, status, platform FROM fb_pages"
            ).fetchall()
            for r in page_rows:
                rid, parent_u, pid, pname, ass_tk, prx, coins, mjobs, st, plat = r
                ttc_label = "Chưa gắn TTC"
                if ass_tk and ass_tk in ttc_map:
                    ttc_label = f"{ttc_map[ass_tk][0]} ({ass_tk[:6]}..)"
                    coins = ttc_map[ass_tk][1]
                elif ass_tk:
                    ttc_label = f"{ass_tk[:10]}..."

                self.tree_ttc_pages.insert(
                    "", "end",
                    values=(rid, parent_u, pid, pname, ttc_label, prx or "None", coins, mjobs, st)
                )
                self.tree_all_pages.insert(
                    "", "end",
                    values=(rid, parent_u, pid, pname, plat or "TTC", coins, st)
                )

            # 3. Bảng Tài khoản FB gốc
            for i in self.tree_fb_accounts.get_children():
                self.tree_fb_accounts.delete(i)
            fb_rows = c.execute("SELECT id, fb_uid, fb_name, proxy, status FROM fb_accounts").fetchall()
            for r in fb_rows:
                self.tree_fb_accounts.insert("", "end", values=r)

            # 4. Bảng Tài khoản Instagram
            for i in self.tree_ig.get_children():
                self.tree_ig.delete(i)
            ig_rows = c.execute("SELECT id, username, proxy, coins, max_jobs, status FROM accounts").fetchall()
            for r in ig_rows:
                self.tree_ig.insert("", "end", values=r)

            conn.close()

        # Cập nhật thanh Header
        self.lbl_stat_ig.configure(text=f"📸 Nick IG: {len(ig_rows)}")
        self.lbl_stat_fb.configure(text=f"👤 Nick FB Gốc: {len(fb_rows)}")
        self.lbl_stat_pages.configure(text=f"🚩 Tổng Fanpage/Profile: {len(page_rows)}")
        self.lbl_stat_ttc.configure(text=f"🔥 Tài Khoản TTC: {len(ttc_rows)}")

    # ==========================================================================
    # CÁC HÀM XỬ LÝ SỰ KIỆN TAB TƯƠNG TÁC CHÉO (TTC FB)
    # ==========================================================================
    def toggle_all_ttc_modes(self, state_bool):
        for var in self.ttc_job_vars.values():
            var.set(state_bool)

    def get_checked_ttc_modes(self):
        return [k for k, var in self.ttc_job_vars.items() if var.get()]

    def add_or_check_ttc_token(self):
        tk_str = self.ent_ttc_token.get().strip()
        if not tk_str:
            messagebox.showwarning("Thiếu Token", "Vui lòng dán Access Token Tương Tác Chéo vào ô!")
            return

        def _worker():
            ttc = TuongTacCheoTool(tk_str)
            ok, msg = ttc.login()
            if ok:
                with db_lock:
                    conn = get_db_connection()
                    conn.execute(
                        "INSERT OR REPLACE INTO ttc_accounts (ttc_user, ttc_token, coins, status) VALUES (?, ?, ?, ?)",
                        (ttc.ttc_user, tk_str, ttc.coins, "Active")
                    )
                    conn.commit()
                    conn.close()
                self.emit_log(ttc.ttc_user, "Đăng nhập Token TTC", msg)
                self.after(0, self.refresh_all_tables)
            else:
                self.emit_log("TTC_ERROR", "Đăng nhập Token TTC thất bại", msg)

        threading.Thread(target=_worker, daemon=True).start()

    def delete_selected_ttc_token(self):
        sel = self.tree_ttc_accounts.selection()
        if not sel:
            return
        with db_lock:
            conn = get_db_connection()
            for item in sel:
                tk = str(self.tree_ttc_accounts.item(item, "values")[1])
                conn.execute("DELETE FROM ttc_accounts WHERE ttc_token=?", (tk,))
            conn.commit()
            conn.close()
        self.refresh_all_tables()

    def _resolve_selected_ttc_token(self):
        with db_lock:
            conn = get_db_connection()
            rows = conn.execute("SELECT ttc_user, ttc_token FROM ttc_accounts").fetchall()
            conn.close()
        if not rows:
            return ""
        chosen = self.cmb_assign_ttc.get()
        for u, tk in rows:
            if chosen.startswith(f"{u} |"):
                return tk
        return rows[0][1]

    def assign_ttc_to_selected_pages(self):
        sel = self.tree_ttc_pages.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn Page", "Hãy chọn ít nhất 1 dòng Page trong bảng bên dưới!")
            return
        tk = self._resolve_selected_ttc_token()
        if not tk:
            messagebox.showwarning("Chưa có Token TTC", "Hãy thêm Token TTC trước!")
            return
        with db_lock:
            conn = get_db_connection()
            for item in sel:
                pid = str(self.tree_ttc_pages.item(item, "values")[2])
                conn.execute("UPDATE fb_pages SET assigned_ttc=?, platform='TTC' WHERE page_id=?", (tk, pid))
            conn.commit()
            conn.close()
        self.refresh_all_tables()
        self.emit_log("HỆ THỐNG", f"Gắn Token TTC cho {len(sel)} Page", "Thành công")

    def assign_ttc_to_all_pages(self):
        tk = self._resolve_selected_ttc_token()
        if not tk:
            messagebox.showwarning("Chưa có Token TTC", "Hãy thêm Token TTC trước!")
            return
        with db_lock:
            conn = get_db_connection()
            conn.execute("UPDATE fb_pages SET assigned_ttc=?, platform='TTC'", (tk,))
            conn.commit()
            conn.close()
        self.refresh_all_tables()
        self.emit_log("HỆ THỐNG", "Gắn Token TTC cho toàn bộ Page", "Thành công")

    def quick_add_ttc_page(self):
        uid = self.ent_quick_uid.get().strip()
        name = self.ent_quick_name.get().strip()
        cookie = self.ent_quick_cookie.get().strip()
        proxy = self.ent_quick_proxy.get().strip()

        if not uid and cookie:
            m_i = re.search(r"i_user=(\d+)", cookie)
            m_c = re.search(r"c_user=(\d+)", cookie)
            uid = m_i.group(1) if m_i else (m_c.group(1) if m_c else "")

        if not uid or not cookie:
            messagebox.showwarning("Thiếu dữ liệu", "Cần nhập Cookie Facebook (có c_user) và UID/Page ID!")
            return

        if not name:
            name = f"FB_{uid[-5:]}"

        default_ttc = self._resolve_selected_ttc_token()
        with db_lock:
            conn = get_db_connection()
            conn.execute('''INSERT OR REPLACE INTO fb_pages
                (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform)
                VALUES (?, ?, ?, '', ?, 'Ready', 0, 500, ?, '', ?, 'TTC')''',
                (name, uid, name, proxy, cookie, default_ttc)
            )
            conn.commit()
            conn.close()

        self.refresh_all_tables()
        self.emit_log(name, f"Thêm nhanh UID/Page {uid}", "Sẵn sàng chạy TTC")

    def delete_selected_ttc_pages(self):
        sel = self.tree_ttc_pages.selection()
        if not sel:
            return
        with db_lock:
            conn = get_db_connection()
            for item in sel:
                pid = str(self.tree_ttc_pages.item(item, "values")[2])
                self.running_ttc_pages[pid] = False
                conn.execute("DELETE FROM fb_pages WHERE page_id=?", (pid,))
            conn.commit()
            conn.close()
        self.refresh_all_tables()

    def test_datnick_selected_page(self):
        sel = self.tree_ttc_pages.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn Page", "Hãy chọn 1 dòng Page trong bảng để kiểm tra đặt cấu hình!")
            return
        pid = str(self.tree_ttc_pages.item(sel[0], "values")[2])

        def _test():
            with db_lock:
                conn = get_db_connection()
                row = conn.execute(
                    "SELECT page_name, proxy, parent_cookie, assigned_ttc FROM fb_pages WHERE page_id=?",
                    (pid,)
                ).fetchone()
                conn.close()
            if not row:
                return
            pname, prx, pcookie, ass_ttc = row
            if not ass_ttc:
                ass_ttc = self._resolve_selected_ttc_token()
            if not ass_ttc:
                self.emit_log(pname, "Test Cấu Hình", "Chưa có Token TTC!")
                return

            ttc = TuongTacCheoTool(ass_ttc, proxy=prx)
            ok_lg, msg_lg = ttc.login()
            if not ok_lg:
                self.update_ttc_page_ui(pid, status_text=f"❌ {msg_lg}")
                self.emit_log(pname, "Login TTC", msg_lg)
                return

            dtsg = ttc.get_fb_dtsg(pid, pcookie)
            dtsg_status = f"OK ({dtsg[:10]}...)" if dtsg else "LỖI (Kiểm tra lại Cookie FB!)"

            ok_dat, msg_dat = ttc.dat_nick(pid)
            final_st = f"{'✅' if ok_dat else '❌'} {msg_dat} | fb_dtsg: {dtsg_status}"
            self.update_ttc_page_ui(pid, status_text=final_st, coins=ttc.coins)
            self.emit_log(pname, "Test Đặt Nick & Cookie", final_st)

        threading.Thread(target=_test, daemon=True).start()

    # ==========================================================================
    # QUÉT FANPAGE TỰ ĐỘNG TỪ COOKIE (GRAPHQL) HOẶC TOKEN (GRAPH API)
    # ==========================================================================
    def add_main_fb_as_worker_page(self):
        cookie = self.ent_fb_cookie.get().strip()
        token = self.ent_fb_token.get().strip()
        proxy = self.ent_fb_proxy.get().strip()
        plat = self.cmb_scan_platform.get()

        m = re.search(r"c_user=(\d+)", cookie)
        if not m:
            messagebox.showwarning("Cookie thiếu c_user", "Vui lòng nhập Cookie Facebook hợp lệ có chứa c_user=...")
            return
        uid = m.group(1)
        default_ttc = self._resolve_selected_ttc_token()

        with db_lock:
            conn = get_db_connection()
            conn.execute(
                "INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status) VALUES (?, ?, ?, ?, ?, 'Active')",
                (uid, f"FB_{uid}", cookie, token, proxy)
            )
            conn.execute('''INSERT OR REPLACE INTO fb_pages
                (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform)
                VALUES (?, ?, ?, ?, ?, 'Ready', 0, 500, ?, ?, ?, ?)''',
                (f"FB_{uid}", uid, f"NickChinh_{uid}", token, proxy, cookie, token, default_ttc, plat)
            )
            conn.commit()
            conn.close()

        self.refresh_all_tables()
        self.emit_log(f"FB_{uid}", "Thêm Nick FB chính vào danh sách chạy Job", "Thành công")

    def add_fb_and_scan_pages(self):
        cookie = self.ent_fb_cookie.get().strip()
        utoken = self.ent_fb_token.get().strip()
        proxy = self.ent_fb_proxy.get().strip()
        plat = self.cmb_scan_platform.get()

        if not cookie and not utoken:
            messagebox.showwarning("Thiếu thông tin", "Hãy nhập Cookie Facebook hoặc Access Token EAAG...")
            return

        def _scan_worker():
            proxies = format_proxies(proxy)
            uid_m = re.search(r"c_user=(\d+)", cookie)
            fb_uid = uid_m.group(1) if uid_m else f"FB_{random.randint(1000,9999)}"
            fb_name = f"FB_{fb_uid}"
            scanned_pages = []

            # Cách 1: Quét qua Graph API nếu có Token EAAG/EAAB
            if utoken:
                try:
                    r_me = requests.get(
                        "https://graph.facebook.com/v18.0/me",
                        params={"fields": "id,name", "access_token": utoken},
                        proxies=proxies, timeout=15, verify=False
                    )
                    if r_me.status_code == 200 and "id" in r_me.json():
                        fb_uid = r_me.json()["id"]
                        fb_name = r_me.json().get("name", fb_name)

                    r_acc = requests.get(
                        "https://graph.facebook.com/v18.0/me/accounts",
                        params={"fields": "id,name,access_token", "limit": 100, "access_token": utoken},
                        proxies=proxies, timeout=20, verify=False
                    )
                    for item in r_acc.json().get("data", []):
                        scanned_pages.append({
                            "page_id": str(item["id"]),
                            "page_name": item.get("name", str(item["id"])),
                            "page_token": item.get("access_token", "")
                        })
                except Exception as e:
                    self.emit_log(fb_name, "Quét Page qua Graph API lỗi", str(e))

            # Cách 2: Quét trực tiếp bằng Cookie qua GraphQL (Nếu không có Token EAAG)
            if not scanned_pages and cookie:
                try:
                    ttc_helper = TuongTacCheoTool("", proxy=proxy)
                    dtsg = ttc_helper.get_fb_dtsg(fb_uid, cookie)
                    if dtsg:
                        headers = {
                            "User-Agent": TuongTacCheoTool.USER_AGENT,
                            "Cookie": cookie,
                            "Content-Type": "application/x-www-form-urlencoded"
                        }
                        payload = {
                            "av": fb_uid,
                            "__user": fb_uid,
                            "__a": "1",
                            "fb_dtsg": dtsg,
                            "fb_api_req_friendly_name": "CometProfileSwitchListQuery",
                            "variables": '{"scale":1}',
                            "doc_id": "6235234266562296"
                        }
                        r_gql = requests.post(
                            "https://www.facebook.com/api/graphql/",
                            data=payload, headers=headers, proxies=proxies, timeout=20, verify=False
                        )
                        matches = re.findall(r'"profile":\{"id":"(\d+)","name":"([^"]+)"', r_gql.text)
                        seen_ids = set()
                        for pid, pname in matches:
                            if pid != fb_uid and pid not in seen_ids:
                                seen_ids.add(pid)
                                try:
                                    pname_clean = bytes(pname, "utf-8").decode("unicode_escape")
                                except Exception:
                                    pname_clean = pname
                                scanned_pages.append({
                                    "page_id": pid,
                                    "page_name": pname_clean,
                                    "page_token": ""
                                })
                except Exception as e:
                    self.emit_log(fb_name, "Quét Page qua Cookie GraphQL", str(e))

            # Luôn thêm cả chính UID gốc nếu không tìm thấy Page con nào
            if not scanned_pages and fb_uid.isdigit():
                scanned_pages.append({
                    "page_id": fb_uid,
                    "page_name": f"Profile_{fb_uid}",
                    "page_token": utoken
                })

            default_ttc = self._resolve_selected_ttc_token()
            with db_lock:
                conn = get_db_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO fb_accounts (fb_uid, fb_name, cookie, access_token, proxy, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (fb_uid, fb_name, cookie, utoken, proxy, f"Đã quét {len(scanned_pages)} Page")
                )
                for p in scanned_pages:
                    conn.execute('''INSERT OR REPLACE INTO fb_pages
                        (parent_username, page_id, page_name, page_token, proxy, status, coins, max_jobs, parent_cookie, user_token, assigned_ttc, platform)
                        VALUES (?, ?, ?, ?, ?, 'Ready', 0, 500, ?, ?, ?, ?)''',
                        (fb_name, p["page_id"], p["page_name"], p["page_token"], proxy, cookie, utoken, default_ttc, plat)
                    )
                conn.commit()
                conn.close()

            self.emit_log(fb_name, f"Quét và lưu {len(scanned_pages)} Fanpage/Profile", "Hoàn tất")
            self.after(0, self.refresh_all_tables)

        threading.Thread(target=_scan_worker, daemon=True).start()

    # ==========================================================================
    # ĐIỀU KHIỂN & LUỒNG WORKER TTC FACEBOOK (CHUẨN SMALI MTOOLV2)
    # ==========================================================================
    def start_selected_ttc_pages(self):
        sel = self.tree_ttc_pages.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn Page", "Vui lòng bôi đen ít nhất 1 Page trong bảng để chạy!")
            return
        if not self.get_checked_ttc_modes():
            messagebox.showwarning("Chưa chọn loại Job", "Hãy tích chọn ít nhất 1 trong 12 chế độ Job TTC!")
            return
        for item in sel:
            pid = str(self.tree_ttc_pages.item(item, "values")[2])
            self._spawn_ttc_page_thread(pid)

    def start_all_ttc_pages(self):
        if not self.get_checked_ttc_modes():
            messagebox.showwarning("Chưa chọn loại Job", "Hãy tích chọn ít nhất 1 trong 12 chế độ Job TTC!")
            return
        for item in self.tree_ttc_pages.get_children():
            pid = str(self.tree_ttc_pages.item(item, "values")[2])
            self._spawn_ttc_page_thread(pid)

    def stop_selected_ttc_pages(self):
        for item in self.tree_ttc_pages.selection():
            pid = str(self.tree_ttc_pages.item(item, "values")[2])
            self.running_ttc_pages[pid] = False
            self.update_ttc_page_ui(pid, status_text="⏹️ Đang dừng...")

    def stop_all_ttc_pages(self):
        for pid in list(self.running_ttc_pages.keys()):
            self.running_ttc_pages[pid] = False
            self.update_ttc_page_ui(pid, status_text="⏹️ Đã gửi lệnh dừng")

    def _spawn_ttc_page_thread(self, page_id):
        if self.running_ttc_pages.get(page_id, False):
            return
        if page_id not in self.page_locks:
            self.page_locks[page_id] = threading.Lock()
        self.running_ttc_pages[page_id] = True
        t = threading.Thread(target=self.worker_ttc_page_loop, args=(page_id,), daemon=True)
        t.start()

    def worker_ttc_page_loop(self, page_id):
        lock = self.page_locks[page_id]
        if not lock.acquire(blocking=False):
            return

        try:
            with db_lock:
                conn = get_db_connection()
                row = conn.execute(
                    "SELECT page_name, page_token, proxy, max_jobs, parent_cookie, user_token, assigned_ttc FROM fb_pages WHERE page_id=?",
                    (page_id,)
                ).fetchone()
                if not row:
                    conn.close()
                    return
                page_name, page_token, proxy, max_jobs, parent_cookie, user_token, assigned_ttc = row
                if not assigned_ttc:
                    t_row = conn.execute("SELECT ttc_token FROM ttc_accounts LIMIT 1").fetchone()
                    if t_row:
                        assigned_ttc = t_row[0]
                        conn.execute("UPDATE fb_pages SET assigned_ttc=? WHERE page_id=?", (assigned_ttc, page_id))
                        conn.commit()
                conn.close()

            if not assigned_ttc:
                self.update_ttc_page_ui(page_id, status_text="❌ Lỗi: Chưa gắn Token TTC!")
                self.emit_log(page_name, "Khởi chạy TTC", "Dừng vì chưa có Token TTC")
                self.running_ttc_pages[page_id] = False
                return

            # 1. Đăng nhập Token TTC -> Giữ Cookie PHPSESSID xuyên suốt
            ttc = TuongTacCheoTool(assigned_ttc, proxy=proxy)
            self.update_ttc_page_ui(page_id, status_text="🔄 Đang đăng nhập Token TTC...")
            ok_lg, msg_lg = ttc.login()
            if not ok_lg:
                self.update_ttc_page_ui(page_id, status_text=f"❌ {msg_lg}")
                self.emit_log(page_name, "Đăng nhập TTC lỗi", msg_lg)
                self.running_ttc_pages[page_id] = False
                return

            self.update_ttc_page_ui(page_id, status_text=f"✅ Login TTC ({ttc.ttc_user})", coins=ttc.coins)
            self.emit_log(page_name, "Login TTC", msg_lg)

            # 2. Kiểm tra fb_dtsg của Cookie Facebook trước khi chạy
            if parent_cookie:
                self.update_ttc_page_ui(page_id, status_text="🔑 Đang lấy fb_dtsg từ Cookie Facebook...")
                dtsg = ttc.get_fb_dtsg(page_id, parent_cookie)
                if dtsg:
                    self.emit_log(page_name, f"Khởi tạo phiên FB UID {page_id}", f"Lấy fb_dtsg thành công ({dtsg[:10]}...)")
                else:
                    self.emit_log(page_name, f"Cảnh báo Cookie UID {page_id}", "Không lấy được fb_dtsg (Kiểm tra lại Cookie!)")

            # 3. Đặt cấu hình Nick/Page trên TTC (Bắt buộc trả về '1' mới quét ra job)
            self.update_ttc_page_ui(page_id, status_text=f"⚙️ Đang đặt cấu hình UID {page_id} trên TTC...")
            ok_dat, msg_dat = ttc.dat_nick(page_id)
            if not ok_dat:
                self.update_ttc_page_ui(page_id, status_text=f"❌ {msg_dat}")
                self.emit_log(page_name, "Đặt cấu hình TTC thất bại", msg_dat)
                self.running_ttc_pages[page_id] = False
                return

            self.emit_log(page_name, "Đặt cấu hình TTC", msg_dat)

            completed_jobs = 0
            max_jobs = int(max_jobs or 500)

            # 4. Vòng lặp quét & làm nhiệm vụ qua các mục đã tích
            while self.running_ttc_pages.get(page_id, False) and completed_jobs < max_jobs:
                active_modes = self.get_checked_ttc_modes()
                if not active_modes:
                    self.update_ttc_page_ui(page_id, status_text="⏸️ Chưa tích chọn chế độ Job nào!")
                    time.sleep(3)
                    continue

                found_job_in_round = False

                for job_key in active_modes:
                    if not self.running_ttc_pages.get(page_id, False) or completed_jobs >= max_jobs:
                        break

                    mode_name = TuongTacCheoTool.JOB_MODES.get(job_key, {}).get("name", job_key)
                    self.update_ttc_page_ui(page_id, status_text=f"🔍 Đang quét {mode_name}...")

                    with worker_semaphore:
                        jobs, scan_msg, cd_sec = ttc.get_tasks(job_key)

                    if not jobs:
                        if cd_sec > 0:
                            self._sleep_with_status(page_id, cd_sec, f"⏳ Countdown {mode_name}")
                        else:
                            self._sleep_with_status(page_id, 3, f"Chuyển mục ({mode_name} hết job)")
                        continue

                    found_job_in_round = True
                    self.emit_log(page_name, f"Quét {mode_name}", f"Tìm thấy {len(jobs)} nhiệm vụ!")

                    # Làm từng job trong danh sách trả về
                    for idx, job in enumerate(jobs, start=1):
                        if not self.running_ttc_pages.get(page_id, False) or completed_jobs >= max_jobs:
                            break

                        idpost = job["idpost"]
                        self.update_ttc_page_ui(
                            page_id,
                            status_text=f"⚡ [{idx}/{len(jobs)}] Đang làm {mode_name} -> ID: {idpost}"
                        )

                        with worker_semaphore:
                            fb_ok, fb_msg = ttc.do_fb_action(page_id, page_token, parent_cookie, job)

                        if not fb_ok:
                            self.emit_log(page_name, f"Bỏ qua {mode_name} ({idpost})", fb_msg)
                            self._sleep_with_status(page_id, 2, "⚠️ Lỗi thao tác FB, chuyển job kế")
                            continue

                        # Chờ 2.5s để Facebook cập nhật trạng thái trước khi bấm nhận tiền trên TTC
                        time.sleep(2.5)

                        with worker_semaphore:
                            claim_ok, claim_msg, updated_coins = ttc.claim_reward(
                                job_key, idpost, sub_path=job.get("sub_path")
                            )

                        if claim_ok:
                            completed_jobs += 1
                            with db_lock:
                                conn = get_db_connection()
                                conn.execute("UPDATE ttc_accounts SET coins=? WHERE ttc_token=?", (updated_coins, assigned_ttc))
                                conn.execute("UPDATE fb_pages SET coins=? WHERE page_id=?", (updated_coins, page_id))
                                conn.commit()
                                conn.close()

                            self.update_ttc_page_ui(
                                page_id,
                                status_text=f"💰 +{claim_msg} | Đã làm: {completed_jobs}/{max_jobs}",
                                coins=updated_coins
                            )
                            self.emit_log(page_name, f"Nhận xu [{mode_name}]", f"{claim_msg} (Tổng: {updated_coins:,} xu)")
                        else:
                            self.emit_log(page_name, f"Nhận xu thất bại ({idpost})", claim_msg)
                            # Nếu văng cấu hình hoặc hết phiên thì tự login + đặt lại nick
                            if "cấu hình" in claim_msg.lower() or "đăng nhập" in claim_msg.lower():
                                ttc.login()
                                ttc.dat_nick(page_id)

                        # Delay ngẫu nhiên trong khoảng Min - Max
                        try:
                            d_min = max(2, int(self.ent_ttc_delay_min.get().strip()))
                            d_max = max(d_min, int(self.ent_ttc_delay_max.get().strip()))
                        except Exception:
                            d_min, d_max = 6, 10
                        wait_s = random.randint(d_min, d_max)
                        self._sleep_with_status(page_id, wait_s, f"⏳ Nghỉ {wait_s}s giãn cách")

                if not found_job_in_round and self.running_ttc_pages.get(page_id, False):
                    self._sleep_with_status(page_id, 10, "🔄 Quét hết các mục đều trống, chờ 10s quét vòng mới")

        except Exception as e:
            self.emit_log(page_id, "Lỗi luồng TTC", str(e))
        finally:
            self.running_ttc_pages[page_id] = False
            self.update_ttc_page_ui(page_id, status_text="⏹️ Đã dừng")
            lock.release()

    def _sleep_with_status(self, page_id, seconds, prefix):
        for rem in range(int(seconds), 0, -1):
            if not self.running_ttc_pages.get(page_id, False):
                break
            self.update_ttc_page_ui(page_id, status_text=f"{prefix} ({rem}s)...")
            time.sleep(1)

    # ==========================================================================
    # LUỒNG WORKER XSMM CHO FANPAGE & INSTAGRAM (GIỮ ĐẦY ĐỦ TÍNH NĂNG CŨ)
    # ==========================================================================
    def start_selected_xsmm_pages(self):
        api_key = self.ent_xsmm_page_api.get().strip()
        if not api_key:
            messagebox.showwarning("Thiếu XSMM Token", "Hãy nhập XSMM API Token ở ô phía trên!")
            return
        for item in self.tree_all_pages.selection():
            pid = str(self.tree_all_pages.item(item, "values")[2])
            if not self.running_xsmm_pages.get(pid, False):
                self.running_xsmm_pages[pid] = True
                threading.Thread(target=self.worker_single_page_loop, args=(pid, api_key), daemon=True).start()

    def stop_selected_xsmm_pages(self):
        for item in self.tree_all_pages.selection():
            pid = str(self.tree_all_pages.item(item, "values")[2])
            self.running_xsmm_pages[pid] = False
            self.update_ttc_page_ui(pid, status_text="⏹️ Đã dừng XSMM")

    def worker_single_page_loop(self, page_id, xsmm_api_key):
        try:
            with db_lock:
                conn = get_db_connection()
                row = conn.execute(
                    "SELECT page_name, page_token, proxy, coins, max_jobs, parent_cookie FROM fb_pages WHERE page_id=?",
                    (page_id,)
                ).fetchone()
                conn.close()
            if not row:
                return
            pname, ptoken, proxy, coins, max_jobs, pcookie = row
            xsmm = XSMMTool(xsmm_api_key, proxy=proxy)
            ttc_fb_executor = TuongTacCheoTool("", proxy=proxy)
            done = 0

            while self.running_xsmm_pages.get(page_id, False) and done < int(max_jobs or 100):
                self.update_ttc_page_ui(page_id, status_text="🔍 Đang lấy job Facebook XSMM...")
                tasks = xsmm.get_tasks(social="facebook", account_uid=page_id)
                if not tasks:
                    self.update_ttc_page_ui(page_id, status_text="⏳ Hết job XSMM, chờ 10s...")
                    time.sleep(10)
                    continue

                for t in tasks:
                    if not self.running_xsmm_pages.get(page_id, False):
                        break
                    tid = t.get("id") or t.get("task_id")
                    link = t.get("link") or t.get("target_url") or ""
                    jtype = str(t.get("type", "like")).upper()
                    fake_job = {
                        "idpost": link,
                        "link": link,
                        "loaicx": "LIKE",
                        "nd": t.get("comment", "Tuyệt vời"),
                        "action": "FOLLOW" if "FOLLOW" in jtype or "SUB" in jtype else "LIKE"
                    }
                    ok, msg = ttc_fb_executor.do_fb_action(page_id, ptoken, pcookie, fake_job)
                    if ok:
                        time.sleep(2)
                        c_ok, c_msg, rew = xsmm.claim_reward(tid, account_uid=page_id)
                        if c_ok:
                            coins += rew
                            done += 1
                            with db_lock:
                                conn = get_db_connection()
                                conn.execute("UPDATE fb_pages SET coins=? WHERE page_id=?", (coins, page_id))
                                conn.commit()
                                conn.close()
                            self.update_ttc_page_ui(page_id, status_text=f"💰 +{rew} xu XSMM ({done} job)", coins=coins)
                    time.sleep(6)
        finally:
            self.running_xsmm_pages[page_id] = False
            self.update_ttc_page_ui(page_id, status_text="⏹️ Đã dừng XSMM")

    # ==========================================================================
    # QUẢN LÝ & WORKER INSTAGRAM (XSMM)
    # ==========================================================================
    def add_ig_account(self):
        cookie = self.ent_ig_cookie.get().strip()
        proxy = self.ent_ig_proxy.get().strip()
        max_j = self.ent_ig_maxjobs.get().strip() or "100"
        if not cookie:
            messagebox.showwarning("Thiếu Cookie", "Hãy dán Cookie Instagram vào ô!")
            return

        def _check():
            ig = INSTAGRAM(cookie, proxy=proxy)
            ok, uname = ig.GETINFO()
            if ok:
                with db_lock:
                    conn = get_db_connection()
                    conn.execute(
                        "INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, 'Ready', 0, ?)",
                        (uname, cookie, proxy, int(max_j))
                    )
                    conn.commit()
                    conn.close()
                self.emit_log(uname, "Thêm tài khoản Instagram", "Check Live OK")
                self.after(0, self.refresh_all_tables)
            else:
                self.emit_log("IG_ERROR", "Check Cookie IG thất bại", uname)

        threading.Thread(target=_check, daemon=True).start()

    def import_ig_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]
        with db_lock:
            conn = get_db_connection()
            for idx, ln in enumerate(lines):
                parts = ln.split("|")
                ck = parts[0].strip()
                prx = parts[1].strip() if len(parts) > 1 else ""
                m = re.search(r"ds_user_id=(\d+)", ck)
                uname = f"IG_{m.group(1)}" if m else f"IG_Import_{idx+1}"
                conn.execute(
                    "INSERT OR REPLACE INTO accounts (username, cookie, proxy, status, coins, max_jobs) VALUES (?, ?, ?, 'Imported', 0, 100)",
                    (uname, ck, prx)
                )
            conn.commit()
            conn.close()
        self.refresh_all_tables()
        self.emit_log("HỆ THỐNG", f"Import {len(lines)} Cookie IG từ file", "Thành công")

    def start_selected_ig(self):
        api_key = self.ent_ig_xsmm_token.get().strip()
        if not api_key:
            messagebox.showwarning("Thiếu XSMM API Key", "Hãy nhập XSMM API Key ở Tab Instagram!")
            return
        for item in self.tree_ig.selection():
            uname = str(self.tree_ig.item(item, "values")[1])
            if not self.running_ig.get(uname, False):
                self.running_ig[uname] = True
                threading.Thread(target=self.worker_single_account_loop, args=(uname, api_key), daemon=True).start()

    def stop_selected_ig(self):
        for item in self.tree_ig.selection():
            uname = str(self.tree_ig.item(item, "values")[1])
            self.running_ig[uname] = False
            self.update_ig_ui(uname, status_text="⏹️ Đã dừng")

    def delete_selected_ig(self):
        sel = self.tree_ig.selection()
        if not sel:
            return
        with db_lock:
            conn = get_db_connection()
            for item in sel:
                uname = str(self.tree_ig.item(item, "values")[1])
                self.running_ig[uname] = False
                conn.execute("DELETE FROM accounts WHERE username=?", (uname,))
            conn.commit()
            conn.close()
        self.refresh_all_tables()

    def worker_single_account_loop(self, username, xsmm_api_key):
        try:
            with db_lock:
                conn = get_db_connection()
                row = conn.execute("SELECT cookie, proxy, coins, max_jobs FROM accounts WHERE username=?", (username,)).fetchone()
                conn.close()
            if not row:
                return
            cookie, proxy, coins, max_jobs = row
            ig = INSTAGRAM(cookie, proxy=proxy)
            xsmm = XSMMTool(xsmm_api_key, proxy=proxy)
            done = 0

            while self.running_ig.get(username, False) and done < int(max_jobs or 100):
                self.update_ig_ui(username, status_text="🔍 Đang lấy job IG từ XSMM...")
                tasks = xsmm.get_tasks(social="instagram", account_uid=username)
                if not tasks:
                    self.update_ig_ui(username, status_text="⏳ Hết job IG, chờ 10s...")
                    time.sleep(10)
                    continue

                for t in tasks:
                    if not self.running_ig.get(username, False):
                        break
                    tid = t.get("id") or t.get("task_id")
                    target = t.get("link") or t.get("target") or ""
                    jtype = str(t.get("type", "follow")).lower()

                    if "like" in jtype:
                        ok, msg = ig.LIKE(target)
                    elif "comment" in jtype:
                        ok, msg = ig.COMMENT(target, t.get("comment", "Nice!"))
                    else:
                        ok, msg = ig.FOLLOW(target)

                    if ok:
                        time.sleep(2)
                        c_ok, c_msg, rew = xsmm.claim_reward(tid, account_uid=username)
                        if c_ok:
                            coins += rew
                            done += 1
                            with db_lock:
                                conn = get_db_connection()
                                conn.execute("UPDATE accounts SET coins=? WHERE username=?", (coins, username))
                                conn.commit()
                                conn.close()
                            self.update_ig_ui(username, status_text=f"💰 +{rew} coins ({done}/{max_jobs})", coins=coins)
                            self.emit_log(username, f"IG Job {jtype}", f"+{rew} coins")
                    time.sleep(7)
        finally:
            self.running_ig[username] = False
            self.update_ig_ui(username, status_text="⏹️ Đã dừng")

    # ==========================================================================
    # QUẢN LÝ NHẬT KÝ HỆ THỐNG (TAB DASHBOARD)
    # ==========================================================================
    def load_db_logs_to_view(self):
        self.txt_system_log.delete("1.0", "end")
        with db_lock:
            conn = get_db_connection()
            rows = conn.execute("SELECT timestamp, username, action, status FROM logs ORDER BY id DESC LIMIT 300").fetchall()
            conn.close()
        for ts, u, act, st in reversed(rows):
            self.txt_system_log.insert("end", f"[{ts}] [{u}] {act} -> {st}\n")
        self.txt_system_log.see("end")

    def clear_all_logs(self):
        with db_lock:
            conn = get_db_connection()
            conn.execute("DELETE FROM logs")
            conn.commit()
            conn.close()
        self.txt_system_log.delete("1.0", "end")
        self.txt_ttc_live_log.delete("1.0", "end")


if __name__ == "__main__":
    app = MMOApp()
    app.mainloop()
