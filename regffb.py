#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FB REG + OTP (metaking.top EMAIL | bamboommo.com EMAIL | autosms.site SMS)
Flow: Thuê Email/SĐT -> Reg FB -> Spam OTP -> Poll OTP -> Verify -> Check LIVE UID -> Save
"""

import base64
import json
import logging
import os
import random
import re
import string
import sys
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import nacl.utils
import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from nacl.public import PublicKey, SealedBox

# ============================================================
# CẤU HÌNH EMAIL OTP (metaking.top)
# ============================================================
EMAIL_API_KEY = "b1e15f70b39efbc652eadedd5672a5f6a5db4c10a254417ab1ff789ccdaca254"
EMAIL_BASE_URL = "https://metaking.top/api"
EMAIL_SERVER = 1
EMAIL_DOMAIN = "gmail.com"
EMAIL_SERVICE_CODE = "facebook"

# ============================================================
# CẤU HÌNH EMAIL OTP (bamboommo.com)
# ============================================================
BAMBOO_API_KEY = ""
BAMBOO_BASE_URL = "https://api.bamboommo.com"
BAMBOO_SERVER = 1
BAMBOO_TYPE_MAIL = "GM"     # GM | GW | HM | SM
BAMBOO_CODE_SERVICE = "FB"  # Facebook

# ============================================================
# CẤU HÌNH SMS OTP (autosms.site)
# ============================================================
SMS_API_KEY = ""
SMS_BASE_URL = "https://autosms.site/api"
SMS_COUNTRY = "us"
SMS_SERVICE = "facebook"

# ============================================================
# TERMINAL COLOR HELPERS
# ============================================================
class T:
    GREEN = "\033[92m"
    LGREEN = "\033[38;5;46m"
    WHITE = "\033[97m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

_dyn_state = {"len": 0}

def _term_width() -> int:
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80

def status_line(msg: str, color: str = ""):
    msg = msg[:_term_width() - 1]
    pad = " " * max(0, _dyn_state["len"] - len(msg))
    sys.stdout.write(f"\r{color}{msg}{pad}{T.RESET}")
    sys.stdout.flush()
    _dyn_state["len"] = len(msg)

def status_clear():
    if _dyn_state["len"] > 0:
        sys.stdout.write("\r" + " " * _dyn_state["len"] + "\r")
        sys.stdout.flush()
        _dyn_state["len"] = 0

def status_final(msg: str, color: str = ""):
    status_clear()
    print(f"{color}{msg}{T.RESET}" if color else msg)

def cprint(msg: str = "", color: str = ""):
    if color:
        print(f"{color}{msg}{T.RESET}")
    else:
        print(msg)

def print_step(step: str, detail: str = ""):
    if detail:
        print(f"{T.GREEN}{T.BOLD}{step}{T.RESET} {T.WHITE}{detail}{T.RESET}")
    else:
        print(f"{T.GREEN}{T.BOLD}{step}{T.RESET}")

def print_box(title: str):
    w = 50
    print()
    print(f"{T.GREEN}╔{'═' * w}╗{T.RESET}")
    pad = (w - len(title)) // 2
    line = f"{T.GREEN}║{T.RESET}{' ' * pad}{T.GREEN}{T.BOLD}{title}{T.RESET}" \
           f"{' ' * (w - pad - len(title))}{T.GREEN}║{T.RESET}"
    print(line)
    print(f"{T.GREEN}╚{'═' * w}╝{T.RESET}")

def print_kv(key: str, value: str, key_width: int = 9):
    print(f"{T.GRAY}{key.ljust(key_width)}{T.RESET}{T.WHITE}{value}{T.RESET}")

# ============================================================
# LOG
# ============================================================
LOG_DIR = Path("reg/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("FBReg")
log.setLevel(logging.INFO)
log.propagate = False
_fh = logging.FileHandler(LOG_DIR / "reg.log", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
log.addHandler(_fh)

for _noisy in ("httpx", "httpcore", "urllib3", "requests"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


@dataclass
class Config:
    output_dir: Path = Path("reg")
    register_delay_min: float = 20.0
    register_delay_max: float = 45.0
    between_accounts_min: float = 5.0
    between_accounts_max: float = 10.0
    http_timeout: float = 45.0
    nestproxy_cooldown: int = 60
    otp_wait_timeout: int = 300
    otp_poll_interval: int = 4
    rent_retries: int = 3
    otp_spam_count: int = 4
    otp_spam_delay: float = 1.5
    key_retry_count: int = 3
    key_retry_delay: float = 2.0
    live_check_retries: int = 3
    live_check_delay: float = 2.0

    def ensure_dirs(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)


CFG = Config()
CFG.ensure_dirs()


# ============================================================
# EXCEPTIONS
# ============================================================
class FBRegError(Exception): pass
class CheckpointError(FBRegError): pass
class OTPError(FBRegError): pass
class RegistrationFailedError(FBRegError): pass
class ProxyError(FBRegError): pass
class EmailRentError(FBRegError): pass
class SmsRentError(FBRegError): pass

CHECKPOINT_282_ID = "1501092823525282"
OTP_SOFT_BLOCK_ERROR_CODE = "3252001"


# ============================================================
# UTILS
# ============================================================
def rand_str(length: int) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_uuid() -> str:
    return str(uuid.uuid4())

def strip_for_json(text: str) -> str:
    return text[9:] if text.startswith("for (;;);") else text

def save_line(filename: str, line: str):
    path = CFG.output_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")

def is_checkpoint_282(location: str) -> bool:
    return "/checkpoint/" in location and CHECKPOINT_282_ID in location


# ============================================================
# IP CHECKER
# ============================================================
class IPChecker:
    ENDPOINTS = [
        "https://api.ipify.org?format=json",
        "https://ipinfo.io/json",
        "https://api.my-ip.io/ip.json",
    ]

    @staticmethod
    def get_public_ip(client: httpx.Client) -> Optional[str]:
        for url in IPChecker.ENDPOINTS:
            try:
                r = client.get(url, timeout=10,
                               headers={"user-agent": random.choice(USER_AGENTS)})
                if r.status_code != 200:
                    continue
                try:
                    data = r.json()
                    ip = data.get("ip") or data.get("query")
                    if ip:
                        return str(ip).strip()
                except Exception:
                    txt = r.text.strip()
                    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", txt):
                        return txt
            except Exception:
                continue
        return None

    @staticmethod
    def get_ip_info(ip: str) -> Dict[str, str]:
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=8)
            if r.status_code == 200:
                return r.json() or {}
        except Exception:
            pass
        return {}

    @staticmethod
    def format_ip_display(ip: str, info: Optional[Dict] = None) -> str:
        if not ip:
            return "unknown"
        info = info or {}
        country = info.get("country", "")
        city = info.get("city", "")
        org = info.get("org", "")
        parts = [ip]
        loc = ", ".join(x for x in [city, country] if x)
        if loc:
            parts.append(f"[{loc}]")
        if org:
            parts.append(f"({org})")
        return " ".join(parts)


# ============================================================
# FACEBOOK LIVE CHECKER
# ============================================================
class FacebookChecker:
    @staticmethod
    def check_uid(uid: str) -> Tuple[str, Optional[Dict]]:
        try:
            url = f"https://graph.facebook.com/{uid}/picture?redirect=false"
            headers = {
                "authority": "graph.facebook.com",
                "accept": "*/*",
                "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
                "origin": "https://2fa.cn",
                "referer": "https://2fa.cn/",
                "sec-ch-ua": '"(Not(A:Brand";v="99", "Google Chrome";v="134", "Chromium";v="134"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site",
                "user-agent": (
                    "Mozilla/5.0 (Linux; Android 10.1; Magnet_G30) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/134.0.7079.100 Mobile Safari/537.36"
                ),
            }
            response = requests.get(url, headers=headers, timeout=10)
            try:
                data = response.json()
            except json.JSONDecodeError:
                data = None
            if response.status_code == 200 and data:
                if "data" in data and "height" in data["data"] and "width" in data["data"]:
                    return "alive", data
            return "die", data
        except requests.exceptions.RequestException as e:
            log.error(f"[LiveCheck] Lỗi kết nối khi check UID {uid}: {e}")
            return "error", None

    @staticmethod
    def check_uid_with_retry(uid: str, retries: int = None, delay: float = None) -> Tuple[str, Optional[Dict]]:
        retries = retries if retries is not None else CFG.live_check_retries
        delay = delay if delay is not None else CFG.live_check_delay
        last_status, last_data = "error", None
        for i in range(1, retries + 1):
            status, data = FacebookChecker.check_uid(uid)
            last_status, last_data = status, data
            if status in ("alive", "die"):
                return status, data
            time.sleep(delay)
        return last_status, last_data


# ============================================================
# BASE OTP MANAGER
# ============================================================
class BaseOTPManager:
    current_identifier: Optional[str] = None
    def rent(self, retries: Optional[int] = None) -> Optional[Dict]: raise NotImplementedError
    def poll_otp(self, timeout=None, interval=None) -> Optional[str]: raise NotImplementedError
    def cancel(self) -> bool: return False
    def reset(self): raise NotImplementedError


# ============================================================
# EMAIL OTP MANAGER (metaking.top)
# ============================================================
_GLOBAL_API_LOCK = threading.Lock()
_GLOBAL_LAST_CALL = [0.0]


class EmailOTPManager(BaseOTPManager):
    def __init__(self, api_key: str, server: int = 1, domain: str = "gmail.com",
                 service_code: str = "facebook"):
        self.api_key = api_key
        self.server = server
        self.domain = domain
        self.service_code = service_code
        self.service_id: Optional[int] = None
        self.current_rental_id: Optional[str] = None
        self.current_email: Optional[str] = None

    @property
    def current_identifier(self) -> Optional[str]:
        return self.current_email

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _throttle(self):
        with _GLOBAL_API_LOCK:
            elapsed = time.time() - _GLOBAL_LAST_CALL[0]
            wait = random.uniform(2.0, 3.0) - elapsed
            if wait > 0:
                time.sleep(wait)
            _GLOBAL_LAST_CALL[0] = time.time()

    def _req(self, method: str, path: str, *, params=None, json_body=None) -> Optional[Dict]:
        self._throttle()
        url = f"{EMAIL_BASE_URL}{path}"
        try:
            if method == "GET":
                r = requests.get(url, headers=self._headers(), params=params, timeout=CFG.http_timeout)
            else:
                r = requests.post(url, headers=self._headers(), params=params,
                                  json=json_body, timeout=CFG.http_timeout)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text}
            if r.status_code >= 400:
                msg = data.get("message") or data.get("error") or data.get("_raw", "")
                log.error(f"[Email] HTTP {r.status_code}: {msg}")
                return {"_error": r.status_code, "_message": msg, "_data": data}
            return data
        except requests.exceptions.RequestException as e:
            log.error(f"[Email] Request error: {e}")
            return None

    def find_service_id(self) -> Optional[int]:
        if self.service_id:
            return self.service_id
        data = self._req("GET", "/email-otp/services", params={"server": self.server})
        if not data or not data.get("success"):
            log.error(f"[Email] Không lấy được danh sách service: {data}")
            return None
        services = data.get("data") or []
        for sv in services:
            if str(sv.get("code", "")).lower() == self.service_code.lower():
                self.service_id = sv.get("id")
                log.info(f"[Email] Service {self.service_code} -> id={self.service_id} ({sv.get('name')})")
                return self.service_id
        return None

    def get_prices(self) -> Optional[List[Dict]]:
        if not self.service_id:
            if not self.find_service_id():
                return None
        data = self._req("GET", "/email-otp/prices",
                         params={"service_id": self.service_id, "server": self.server})
        if not data or not data.get("success"):
            return None
        return data.get("data") or []

    def rent(self, retries: Optional[int] = None) -> Optional[Dict]:
        if not self.service_id:
            if not self.find_service_id():
                return None
        retries = retries if retries is not None else CFG.rent_retries
        for attempt in range(1, retries + 1):
            body = {"service_id": self.service_id, "domain": self.domain, "server": self.server}
            data = self._req("POST", "/email-otp/rent", json_body=body)
            if data is None:
                time.sleep(3)
                continue
            if data.get("_error"):
                err = data["_error"]
                if err in (402, 404, 403, 401):
                    return None
                time.sleep(3)
                continue
            if data.get("success"):
                d = data.get("data", {}) or {}
                self.current_rental_id = (
                    d.get("id") or d.get("rental_id") or d.get("rentalId")
                    or d.get("order_id") or d.get("orderId")
                )
                self.current_email = (
                    d.get("email_address") or d.get("email") or d.get("address")
                )
                log.info(f"[Email] Thuê OK: {self.current_email} | rental_id={self.current_rental_id}")
                if not self.current_rental_id:
                    return None
                return d
            time.sleep(3)
        return None

    def status(self) -> Optional[Dict]:
        if not self.current_rental_id:
            return None
        data = self._req("GET", f"/email-otp/rentals/{self.current_rental_id}/status")
        if not data or not data.get("success"):
            return None
        return data.get("data", {})

    def request_next(self) -> bool:
        if not self.current_rental_id:
            return False
        data = self._req("POST", f"/email-otp/rentals/{self.current_rental_id}/next")
        return bool(data and data.get("success"))

    def spam_request(self, count: Optional[int] = None, delay: Optional[float] = None):
        count = count if count is not None else CFG.otp_spam_count
        delay = delay if delay is not None else CFG.otp_spam_delay
        if count <= 1:
            return
        ok = 0
        for i in range(1, count + 1):
            if self.request_next():
                ok += 1
            status_line(f"  🔥 Spam /next {i}/{count}...", T.YELLOW)
            if i < count:
                time.sleep(delay)
        status_final(f"  🔥 Spam /next xong: {ok}/{count}", T.YELLOW)

    def _extract_code(self, codes: List) -> Optional[str]:
        for c in reversed(codes):
            if c is None:
                continue
            if isinstance(c, dict):
                for k in ("code", "otp", "value", "raw"):
                    v = c.get(k)
                    if v:
                        m = re.search(r"\b(\d{5,6})\b", str(v))
                        if m:
                            return m.group(1)
            elif isinstance(c, str):
                m = re.search(r"\b(\d{5,6})\b", c)
                if m:
                    return m.group(1)
        return None

    def poll_otp(self, timeout: Optional[int] = None, interval: Optional[int] = None) -> Optional[str]:
        if not self.current_rental_id:
            raise EmailRentError("Chưa thuê email.")

        try:
            self.spam_request()
        except Exception as e:
            log.warning(f"[Email] Spam request lỗi: {e}")

        timeout = timeout or CFG.otp_wait_timeout
        interval = max(interval or CFG.otp_poll_interval, 3)
        start = time.time()
        attempt = 0
        while time.time() - start < timeout:
            attempt += 1
            st = self.status()
            elapsed = time.time() - start
            if st:
                codes = st.get("codes") or []
                code = self._extract_code(codes)
                status = st.get("status", "")
                if code:
                    status_final(f"  ✓ OTP sau {elapsed:.1f}s (attempt #{attempt}): {T.GREEN}{code}", T.WHITE)
                    return code
                status_line(f"  ⏳ Chờ OTP... attempt #{attempt} | status={status} ({elapsed:.1f}s)", T.GRAY)
                if status in ("refunded", "cancelled", "failed"):
                    status_final(f"  ✗ Rental bị {status}", T.RED)
                    return None
            else:
                status_line(f"  ⏳ Chờ OTP... attempt #{attempt} ({elapsed:.1f}s)", T.GRAY)
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                break
            time.sleep(min(interval, remaining))
        status_final(f"  ✗ Hết {timeout}s, không nhận OTP", T.RED)
        return None

    def cancel(self) -> bool:
        if not self.current_rental_id:
            return False
        data = self._req("POST", f"/email-otp/rentals/{self.current_rental_id}/cancel")
        if data and data.get("success"):
            self.reset()
            return True
        return False

    def reset(self):
        self.current_rental_id = None
        self.current_email = None


# ============================================================
# EMAIL OTP MANAGER (bamboommo.com)
# ============================================================
class BambooEmailOTPManager(BaseOTPManager):
    """API email OTP của bamboommo.com — tương thích interface BaseOTPManager."""

    def __init__(self, api_key: str, server: int = 1,
                 code_type_mail: str = "GM", code_service: str = "FB"):
        self.api_key = api_key
        self.server = int(server)
        self.code_type_mail = code_type_mail
        self.code_service = code_service
        self.current_email: Optional[str] = None
        self.current_rental_id: Optional[str] = None
        self.current_status: Optional[str] = None

    @property
    def current_identifier(self) -> Optional[str]:
        return self.current_email

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, path: str, body: Dict) -> Optional[Dict]:
        url = f"{BAMBOO_BASE_URL}{path}"
        try:
            r = requests.post(url, headers=self._headers(), json=body, timeout=CFG.http_timeout)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text}
            if r.status_code >= 400 and isinstance(data, dict) and not data.get("resourceKey"):
                return {"_error": r.status_code, "_data": data}
            return data
        except requests.exceptions.RequestException as e:
            log.error(f"[Bamboo] POST {path} error: {e}")
            return None

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{BAMBOO_BASE_URL}{path}"
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=CFG.http_timeout)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text}
            if r.status_code >= 400 and isinstance(data, dict) and not data.get("resourceKey"):
                return {"_error": r.status_code, "_data": data}
            return data
        except requests.exceptions.RequestException as e:
            log.error(f"[Bamboo] GET {path} error: {e}")
            return None

    # ---------- INFO APIs ----------
    def get_balance(self) -> Optional[Dict]:
        data = self._post("/api/account/get-balance-apikey", {"apiKey": self.api_key})
        if not data or not data.get("isSuccessStatusCode"):
            return None
        return data.get("responseData", {}) or {}

    def get_type_mail(self) -> List[Dict]:
        data = self._get("/api/mail/get-type-mail")
        if not data or not data.get("isSuccessStatusCode"):
            return []
        return data.get("responseData", []) or []

    def get_rental_service(self, code: str) -> List[Dict]:
        data = self._get("/api/mail/get-rental-service", params={"Code": code})
        if not data or not data.get("isSuccessStatusCode"):
            return []
        return data.get("responseData", []) or []

    # ---------- RENT ----------
    def rent(self, retries: Optional[int] = None) -> Optional[Dict]:
        retries = retries if retries is not None else CFG.rent_retries
        body = {
            "apiKey": self.api_key,
            "server": self.server,
            "codeTypeMail": self.code_type_mail,
            "codeService": self.code_service,
        }
        for attempt in range(1, retries + 1):
            data = self._post("/api/mail/get-mail-apikey", body)
            if data is None:
                time.sleep(3)
                continue
            if not data.get("isSuccessStatusCode"):
                rk = data.get("resourceKey", "")
                msg = data.get("message", "")
                log.warning(f"[Bamboo] Rent fail #{attempt}: {rk} - {msg}")
                # Lỗi không nên retry
                if rk in ("API_FALSE", "NON_MAIL", "NO_MONEY",
                          "USER_NOT_FOUND", "INVALID_RENT_COST",
                          "ACTIVE_RENT_BALANCE_EXCEEDED"):
                    return None
                time.sleep(3)
                continue

            email = data.get("responseData")
            header = data.get("responseHeader") or {}
            self.current_email = email
            self.current_rental_id = header.get("rentalId")
            self.current_status = header.get("status")
            log.info(f"[Bamboo] Thuê OK: {self.current_email} | rental_id={self.current_rental_id} | status={self.current_status}")
            if not self.current_email:
                return None
            return {"email": email, **header}
        return None

    # ---------- GET CODE ----------
    def get_code(self) -> Tuple[str, Optional[str]]:
        """Trả (state, otp).
        state: 'otp' | 'wait' | 'expired' | 'error'
        """
        body = {
            "apiKey": self.api_key,
            "server": self.server,
            "Mail": self.current_email,
        }
        if self.current_rental_id:
            body["rentalId"] = self.current_rental_id

        data = self._post("/api/mail/get-code-apikey", body)
        if data is None:
            return "error", None
        if not data.get("isSuccessStatusCode"):
            rk = data.get("resourceKey", "")
            if rk == "NON_OTP":
                return "wait", None
            if rk == "NON_MAIL":
                return "expired", None
            if rk == "API_FALSE":
                return "error", None
            return "wait", None

        otp = data.get("responseData")
        if otp:
            m = re.search(r"\b(\d{4,8})\b", str(otp))
            if m:
                return "otp", m.group(1)
        return "wait", None

    def poll_otp(self, timeout: Optional[int] = None, interval: Optional[int] = None) -> Optional[str]:
        if not self.current_email:
            raise EmailRentError("Chưa thuê email.")

        timeout = timeout or CFG.otp_wait_timeout
        interval = max(interval or CFG.otp_poll_interval, 3)
        start = time.time()
        attempt = 0
        while time.time() - start < timeout:
            attempt += 1
            state, otp = self.get_code()
            elapsed = time.time() - start
            if state == "otp":
                status_final(f"  ✓ OTP sau {elapsed:.1f}s (attempt #{attempt}): {T.GREEN}{otp}", T.WHITE)
                return otp
            if state == "expired":
                status_final(f"  ✗ Rental đã hết hạn hoặc không tồn tại", T.RED)
                return None
            status_line(f"  ⏳ Chờ OTP... attempt #{attempt} ({elapsed:.1f}s)", T.GRAY)
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                break
            time.sleep(min(interval, remaining))
        status_final(f"  ✗ Hết {timeout}s, không nhận OTP", T.RED)
        return None

    def cancel(self) -> bool:
        # Không có endpoint hủy chính thức — chỉ reset nội bộ
        self.reset()
        return True

    def reset(self):
        self.current_email = None
        self.current_rental_id = None
        self.current_status = None


# ============================================================
# SMS OTP MANAGER (autosms.site)
# ============================================================
class SMSOTPManager(BaseOTPManager):
    def __init__(self, api_key: str, country: str = "us", service: str = "facebook"):
        self.api_key = api_key
        self.country = country
        self.service = service
        self.current_order_id: Optional[str] = None
        self.current_phone: Optional[str] = None
        self.current_price: Optional[int] = None

    @property
    def current_identifier(self) -> Optional[str]:
        return self.current_phone

    def get_balance(self) -> Optional[Dict]:
        try:
            r = requests.get(f"{SMS_BASE_URL}/balance",
                             params={"key": self.api_key},
                             timeout=CFG.http_timeout)
            data = r.json()
            if data.get("success"):
                return data.get("data", {}) or {}
        except Exception as e:
            log.error(f"[SMS] Balance error: {e}")
        return None

    def rent(self, retries: Optional[int] = None) -> Optional[Dict]:
        retries = retries if retries is not None else CFG.rent_retries
        url = f"{SMS_BASE_URL}/buy-number/{self.country}/{self.service}"
        for attempt in range(1, retries + 1):
            try:
                r = requests.get(url, params={"key": self.api_key}, timeout=CFG.http_timeout)
                data = r.json()
            except Exception:
                time.sleep(3)
                continue
            if data.get("success"):
                d = data.get("data", {}) or {}
                self.current_order_id = d.get("order_id")
                self.current_phone = d.get("phone")
                self.current_price = d.get("price")
                log.info(f"[SMS] Thuê OK: {self.current_phone} | order_id={self.current_order_id}")
                if not self.current_order_id or not self.current_phone:
                    return None
                return d
            time.sleep(3)
        return None

    def status(self) -> Optional[Dict]:
        if not self.current_order_id:
            return None
        try:
            r = requests.get(f"{SMS_BASE_URL}/orders/{self.current_order_id}",
                             params={"key": self.api_key},
                             timeout=CFG.http_timeout)
            data = r.json()
            if data.get("success"):
                return data.get("data", {}) or {}
        except Exception as e:
            log.debug(f"[SMS] status error: {e}")
        return None

    def spam_request(self, count: Optional[int] = None, delay: Optional[float] = None):
        count = count if count is not None else CFG.otp_spam_count
        delay = delay if delay is not None else CFG.otp_spam_delay
        if count <= 1:
            return
        for i in range(1, count + 1):
            st = self.status()
            if st and st.get("code"):
                status_final(f"  🔥 Spam #{i}: Đã có OTP ngay!", T.YELLOW)
                return
            status_line(f"  🔥 Spam check {i}/{count}...", T.YELLOW)
            if i < count:
                time.sleep(delay)
        status_final(f"  🔥 Spam check xong", T.YELLOW)

    def poll_otp(self, timeout: Optional[int] = None, interval: Optional[int] = None) -> Optional[str]:
        if not self.current_order_id:
            raise SmsRentError("Chưa thuê số SMS.")

        try:
            self.spam_request()
        except Exception as e:
            log.warning(f"[SMS] Spam request lỗi: {e}")

        timeout = timeout or CFG.otp_wait_timeout
        interval = max(interval or CFG.otp_poll_interval, 3)
        start = time.time()
        attempt = 0
        while time.time() - start < timeout:
            attempt += 1
            st = self.status()
            elapsed = time.time() - start
            if st:
                code = st.get("code")
                status = st.get("status", "")
                if code:
                    m = re.search(r"\b(\d{4,8})\b", str(code))
                    if m:
                        status_final(f"  ✓ OTP sau {elapsed:.1f}s (attempt #{attempt}): {T.GREEN}{m.group(1)}", T.WHITE)
                        return m.group(1)
                status_line(f"  ⏳ Chờ OTP... attempt #{attempt} | status={status} ({elapsed:.1f}s)", T.GRAY)
                if status in ("cancel", "cancelled", "failed", "expired"):
                    status_final(f"  ✗ Order bị {status}", T.RED)
                    return None
            else:
                status_line(f"  ⏳ Chờ OTP... attempt #{attempt} ({elapsed:.1f}s)", T.GRAY)
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                break
            time.sleep(min(interval, remaining))
        status_final(f"  ✗ Hết {timeout}s, không nhận OTP", T.RED)
        return None

    def cancel(self) -> bool:
        self.reset()
        return True

    def reset(self):
        self.current_order_id = None
        self.current_phone = None
        self.current_price = None


# ============================================================
# HTTP HEADERS
# ============================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36",
]


def _build_headers(extra=None, referer=None, lsd=None, friendly_name=None, user_agent=None):
    ua = user_agent or random.choice(USER_AGENTS)
    h = {
        "accept": "*/*",
        "accept-language": "vi-VN,vi;q=0.9,en-US;q=0.6,en;q=0.5",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.facebook.com",
        "user-agent": ua,
        "x-asbd-id": "359341",
    }
    if "Chrome" in ua or "Edge" in ua:
        h.update({
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"10.0.0"',
        })
    if "Edge" in ua:
        h["sec-ch-ua"] = '"Microsoft Edge";v="131", "Chromium";v="131", "Not A(Brand";v="24"'
    h.update({"sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin"})
    if referer: h["referer"] = referer
    if lsd: h["x-fb-lsd"] = lsd
    if friendly_name: h["x-fb-friendly-name"] = friendly_name
    if extra: h.update(extra)
    return h


# ============================================================
# PROXY MANAGER
# ============================================================
class ProxyManager:
    def __init__(self, proxy_type="none", nestproxy_keys=None, static_proxies=None):
        self.proxy_type = proxy_type
        self.nestproxy_keys = nestproxy_keys or []
        self.static_proxies = static_proxies or []
        self.lock = threading.Lock()
        self.proxy_ip_cache = {}
        self.key_last_fetch = {}

    def _fetch_nestproxy_ip(self, key: str) -> Optional[str]:
        try:
            r = requests.get("https://nestproxy.com/api/client/proxy/available",
                             params={"proxy_key": key}, timeout=30)
            if r.status_code != 200:
                return None
            data = r.json()
            if isinstance(data, dict):
                for k in ("proxy", "ip_port", "proxy_address", "address", "server"):
                    if data.get(k):
                        return str(data[k]).strip()
                if data.get("ip"):
                    return f"{data['ip']}:{data.get('port', '')}" if data.get("port") else str(data["ip"])
                if isinstance(data.get("data"), dict) and data["data"].get("proxy"):
                    return str(data["data"]["proxy"]).strip()
            elif isinstance(data, str) and ":" in data:
                return data.strip()
        except Exception:
            pass
        return None

    def _wait_for_cooldown(self, key: str):
        if key in self.key_last_fetch:
            elapsed = time.time() - self.key_last_fetch[key]
            if elapsed < CFG.nestproxy_cooldown:
                time.sleep(CFG.nestproxy_cooldown - elapsed)

    def get_proxy_for_token(self, token_idx: int, force_new: bool = False) -> Optional[str]:
        with self.lock:
            if self.proxy_type == "none":
                return None
            if self.proxy_type == "static":
                if not self.static_proxies:
                    return None
                return self.static_proxies[token_idx % len(self.static_proxies)]
            if self.proxy_type == "nestproxy":
                if not self.nestproxy_keys:
                    return None
                key = self.nestproxy_keys[token_idx % len(self.nestproxy_keys)]
                if not force_new and key in self.proxy_ip_cache:
                    cached = self.proxy_ip_cache[key]
                    if cached.get("ip"):
                        return cached["ip"]
                self._wait_for_cooldown(key)
                ip = self._fetch_nestproxy_ip(key)
                if ip:
                    self.proxy_ip_cache[key] = {"ip": ip, "timestamp": time.time()}
                    self.key_last_fetch[key] = time.time()
                    return ip
                return None
            return None

    def build_client(self, proxy_str: Optional[str]) -> httpx.Client:
        kwargs = {"timeout": CFG.http_timeout, "follow_redirects": False, "http2": False, "verify": False}
        if proxy_str:
            if not proxy_str.startswith("http"):
                if "@" in proxy_str:
                    up, hp = proxy_str.split("@", 1)
                    proxy_str = f"http://{up}@{hp}"
                elif proxy_str.count(":") == 3:
                    ip, port, user, pwd = proxy_str.split(":")
                    proxy_str = f"http://{user}:{pwd}@{ip}:{port}"
                else:
                    proxy_str = f"http://{proxy_str}"
            kwargs["mounts"] = {
                "http://": httpx.HTTPTransport(proxy=proxy_str, verify=False),
                "https://": httpx.HTTPTransport(proxy=proxy_str, verify=False),
            }
        return httpx.Client(**kwargs)


# ============================================================
# ENCRYPT PASSWORD
# ============================================================
def encrypt_password(public_key_data: Dict, password: str) -> Optional[str]:
    try:
        ts = str(int(time.time()))
        key_id = int(public_key_data["keyId"])
        pub = bytes.fromhex(public_key_data["publicKey"])
        if len(pub) != 32:
            raise ValueError("Invalid PublicKey length")
        key = nacl.utils.random(32)
        aes = AESGCM(key)
        enc = aes.encrypt(bytes(12), password.encode(), ts.encode())
        sealed = SealedBox(PublicKey(pub)).encrypt(key)
        buf = bytearray(4 + len(sealed) + len(enc))
        buf[0] = 1
        buf[1] = key_id
        buf[2:4] = len(sealed).to_bytes(2, "little")
        buf[4:4 + len(sealed)] = sealed
        buf[4 + len(sealed):4 + len(sealed) + 16] = enc[-16:]
        buf[4 + len(sealed) + 16:] = enc[:-16]
        return f"#PWD_BROWSER:5:{ts}:{base64.b64encode(bytes(buf)).decode()}"
    except Exception as e:
        log.error(f"Lỗi mã hóa mật khẩu: {e}")
        return None


# ============================================================
# OTP VERIFIER
# ============================================================
def _extract_error_code(resp_obj):
    if not isinstance(resp_obj, dict): return ""
    err = resp_obj.get("error")
    return str(err) if err is not None else ""

def _resp_to_text(resp_obj):
    try:
        if isinstance(resp_obj, (dict, list)):
            return json.dumps(resp_obj, ensure_ascii=False)
        return str(resp_obj)
    except Exception:
        return ""

def _is_otp_soft_block(resp_obj):
    if _extract_error_code(resp_obj) == OTP_SOFT_BLOCK_ERROR_CODE:
        return True
    text = _resp_to_text(resp_obj).lower()
    return any(k in text for k in [
        "tạm thời đã bị chặn", "dùng nhầm tính năng", "sử dụng quá nhanh",
        "temporarily blocked", "misused this feature", "too quickly",
    ])

def _is_graphql_final(resp_obj):
    if not isinstance(resp_obj, dict): return False
    ext = resp_obj.get("extensions")
    if not isinstance(ext, dict): return False
    return ext.get("is_final") is True


class OTPVerifier:
    CONFIRM_URL = "https://www.facebook.com/confirmemail.php?next=https%3A%2F%2Fwww.facebook.com%2F%3Flocale%3Dvi_VN"
    GRAPHQL_URL = "https://www.facebook.com/api/graphql/"
    GRAPHQL_DOC_ID = "24050931851170558"
    GRAPHQL_FRIENDLY_NAME = "useCAAFBConfirmationFormSubmitMutation"

    def __init__(self, client, user_agent):
        self.client = client
        self.ua = user_agent

    def visit_confirm_page(self):
        try:
            r = self.client.get(self.CONFIRM_URL, headers=_build_headers(
                extra={
                    "upgrade-insecure-requests": "1",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                },
                referer="https://www.facebook.com/",
                user_agent=self.ua,
            ), follow_redirects=False)
            return FacebookRegistrar._parse_form(r.text)
        except Exception as e:
            log.warning(f"Không thể truy cập trang xác nhận: {e}")
            return {}

    def verify(self, otp, identifier, uid, fb_dtsg, lsd, jazoest, spin_r, spin_t):
        tokens = {"fb_dtsg": fb_dtsg, "lsd": lsd, "jazoest": jazoest}
        form_data = {}
        try:
            form_data = self.visit_confirm_page()
            for k in ("fb_dtsg", "lsd", "jazoest"):
                if form_data.get(k):
                    tokens[k] = form_data[k]
            spin_r = form_data.get("__spin_r") or spin_r
            spin_t = form_data.get("__spin_t") or spin_t
        except Exception:
            pass

        client_mutation_id = str(uuid.uuid4())
        variables = {
            "input": {
                "actor_id": str(uid),
                "client_mutation_id": client_mutation_id,
                "conf_code": {"sensitive_string_value": str(otp)},
                "ig_reg_data": None,
                "machine_id": None,
            }
        }

        gql_data = {
            "av": str(uid), "__user": str(uid), "__a": "1", "__req": "3",
            "__hs": "20712.HYP:comet_plat_default_pkg.2.1...0",
            "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": str(form_data.get("rev", "1047643939")),
            "__s": form_data.get("s", "hx7ogn:yhufto:9exuip"),
            "__hsi": form_data.get("hsi", ""),
            "__dyn": form_data.get("dyn", ""),
            "__csr": form_data.get("csr", ""),
            "__hsdp": form_data.get("hsdp", ""),
            "__hblp": form_data.get("hblp", ""),
            "__comet_req": "102",
            "fb_dtsg": tokens["fb_dtsg"],
            "jazoest": tokens["jazoest"],
            "lsd": tokens["lsd"],
            "__spin_r": str(spin_r or form_data.get("__spin_r", "")),
            "__spin_b": "trunk",
            "__spin_t": str(spin_t or form_data.get("__spin_t", "")),
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": self.GRAPHQL_FRIENDLY_NAME,
            "server_timestamps": "true",
            "variables": json.dumps(variables, separators=(",", ":")),
            "doc_id": self.GRAPHQL_DOC_ID,
        }

        headers = _build_headers(
            extra={
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-fb-friendly-name": self.GRAPHQL_FRIENDLY_NAME,
                "x-fb-lsd": tokens["lsd"],
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "origin": "https://www.facebook.com",
            },
            referer=self.CONFIRM_URL,
            lsd=tokens["lsd"],
            user_agent=self.ua,
        )

        try:
            r = self.client.post(self.GRAPHQL_URL, headers=headers, data=gql_data,
                                 follow_redirects=False)
            if r.status_code in (301, 302, 303, 307, 308):
                location = r.headers.get("location", "")
                if is_checkpoint_282(location):
                    return False, tokens, "checkpoint_282"
            if r.status_code != 200:
                return False, tokens, f"HTTP {r.status_code}"

            text = strip_for_json(r.text)
            try:
                resp = json.loads(text)
            except Exception:
                return False, tokens, "bad_json"

            if _is_graphql_final(resp):
                errors = resp.get("errors")
                data = resp.get("data", {}) or {}
                submit = data.get("xfb_caa_registration_confirmation_submit", {}) or {}
                if errors and not _is_otp_soft_block({"errors": errors}):
                    return False, tokens, "graphql_error"
                return True, tokens, "success"

            if _is_otp_soft_block(resp):
                return True, tokens, "soft_block_success"

            errors = resp.get("errors")
            if errors:
                if _is_otp_soft_block({"errors": errors}):
                    return True, tokens, "soft_block_success"
                return False, tokens, "graphql_error"

            data = resp.get("data", {}) or {}
            submit = data.get("xfb_caa_registration_confirmation_submit", {}) or {}
            if submit.get("created_user_id") or submit.get("user_id"):
                return True, tokens, "success"

            return False, tokens, "otp_rejected"
        except Exception as e:
            return False, tokens, f"exception:{e}"


# ============================================================
# FACEBOOK REGISTRAR
# ============================================================
class FacebookRegistrar:
    REG_PAGE = "https://www.facebook.com/r.php?entry_point=login"
    REG_POST = "https://www.facebook.com/ajax/register.php"

    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.ua = random.choice(USER_AGENTS)

    def _get_public_key(self, client):
        for retry in range(CFG.key_retry_count):
            try:
                r = client.get("https://www.facebook.com/", headers=_build_headers(
                    extra={
                        "upgrade-insecure-requests": "1",
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "sec-fetch-dest": "document",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-user": "?1",
                    },
                    user_agent=self.ua,
                ), follow_redirects=True)
            except Exception:
                time.sleep(CFG.key_retry_delay)
                continue

            if r.status_code != 200:
                time.sleep(CFG.key_retry_delay)
                continue

            m = re.search(r'"encryption_data":\{"key_id":(\d+),"public_key":"([a-fA-F0-9]+)"\}', r.text)
            if m:
                return {"publicKey": m.group(2), "keyId": int(m.group(1))}, r.text

            pk = re.search(r'"public_key":"([a-fA-F0-9]+)"', r.text) or \
                 re.search(r'"publicKey":"([a-fA-F0-9]+)"', r.text)
            kid = re.search(r'"key_id":(\d+)', r.text) or \
                  re.search(r'"keyId":(\d+)', r.text)
            if pk and kid:
                return {"publicKey": pk.group(1), "keyId": int(kid.group(1))}, r.text

            time.sleep(CFG.key_retry_delay)
        return None, None

    @staticmethod
    def _parse_form(text: str) -> Dict[str, str]:
        soup = BeautifulSoup(text, "html.parser")
        data = {}
        for tag in soup.find_all("input", {"type": "hidden"}):
            name = tag.get("name")
            if name:
                data[name] = tag.get("value", "")

        def _re(p, d=""):
            m = re.search(p, text)
            return m.group(1) if m else d

        data["lsd"] = _re(r'["\']LSD["\']\s*,\s*\[\s*\]\s*,\s*\{["\']token["\']\s*:\s*["\']([^"\']+)["\']\}') or data.get("lsd", "")
        data["jazoest"] = _re(r'["\']jazoest["\']\s*[:=]\s*["\']?(\d+)["\']?') or _re(r'jazoest=(\d+)') or data.get("jazoest", "")
        data["__spin_r"] = _re(r'"__spin_r":(\d+)') or data.get("__spin_r", "")
        data["__spin_t"] = _re(r'"__spin_t":(\d+)') or data.get("__spin_t", "")
        data["hsi"] = _re(r'"hsi":"(\d+)"', "7453027861273714271")
        data["fb_dtsg"] = (
            _re(r'["\']fbdtsg["\']\s*,\s*\[\s*\]\s*,\s*\{["\']token["\']\s*:\s*["\']([^"\']+)["\']\}')
            or _re(r'["\']DTSGInitialData["\']\s*,\s*\[\s*\]\s*,\s*\{["\']token["\']\s*:\s*["\']([^"\']+)["\']\}')
            or data.get("fb_dtsg", "")
        )
        data["dyn"] = _re(r'"(?:__)?dyn":"([^"]+)"')
        data["hsdp"] = _re(r'"hsdp":"([^"]+)"')
        data["hblp"] = _re(r'"hblp":"([^"]+)"')
        data["s"] = _re(r'"(?:__)?s":"([^"]+)"', "lxucyo:t0561u:xdnp5s")
        data["csr"] = _re(r'"(?:__)?csr":"([^"]+)"')
        data["rev"] = _re(r'"(?:__)?rev":(\d+)', "1019085267")
        data["ri"] = _re(r'["\']ri["\']\s*:\s*["\']([^"\']+)["\']') or data.get("ri", "")
        data["reg_instance"] = _re(r'["\']reg_instance["\']\s*:\s*["\']([^"\']+)["\']') or data.get("reg_instance", "")
        return data

    def register(self, ho, ten, identifier, password, sex, token_idx=0,
                 otp_mgr: Optional[BaseOTPManager] = None,
                 verify_method: str = "email"):
        proxy_str = self.proxy_manager.get_proxy_for_token(token_idx, force_new=True)
        if proxy_str:
            log.info(f"Proxy: {proxy_str}")

        client = self.proxy_manager.build_client(proxy_str)
        try:
            status_line("  🌐 Đang kiểm tra IP công khai...", T.GRAY)
            public_ip = IPChecker.get_public_ip(client)
            if public_ip:
                info = IPChecker.get_ip_info(public_ip)
                display = IPChecker.format_ip_display(public_ip, info)
                if proxy_str:
                    status_final(f"  🌐 IP (qua PROXY): {T.GREEN}{display}{T.RESET}", T.WHITE)
                else:
                    status_final(f"  🌐 IP (DIRECT): {T.CYAN}{display}{T.RESET}", T.WHITE)
                log.info(f"[IP] public_ip={display} | proxy={proxy_str or 'none'}")
            else:
                status_final(f"  🌐 Không lấy được IP công khai", T.YELLOW)

            return self._run_registration(client, ho, ten, identifier, password, sex,
                                          otp_mgr, verify_method)
        except Exception as e:
            log.error(f"Lỗi tổng quát: {e}")
            log.debug(traceback.format_exc())
            return "GENERAL_ERROR"
        finally:
            client.close()

    def _live_check(self, uid: str) -> str:
        if not uid:
            return "unknown"
        print_step("Bước 5:", "Check LIVE UID...")
        status, data = FacebookChecker.check_uid_with_retry(uid)
        if status == "alive":
            status_final(f"  ✓ UID {uid} {T.GREEN}ALIVE (SỐNG){T.RESET}", T.WHITE)
        elif status == "die":
            status_final(f"  ✗ UID {uid} {T.RED}DIE (CHẾT){T.RESET}", T.WHITE)
        else:
            status_final(f"  ? UID {uid} không xác định (lỗi mạng)", T.YELLOW)
        return status

    def _run_registration(self, client, ho, ten, identifier, password, sex,
                          otp_mgr: Optional[BaseOTPManager],
                          verify_method: str) -> str:
        form = {}
        text = ""
        for attempt in range(2):
            print_step("Bước 1:", "Lấy key + form đăng ký")
            pub_data, _ = self._get_public_key(client)
            if not pub_data:
                status_final("  ✗ Không lấy được public key", T.RED)
                return "KEY_EXTRACTION_FAILED"
            enc_pass = encrypt_password(pub_data, password)
            if not enc_pass:
                status_final("  ✗ Mã hoá password thất bại", T.RED)
                return "PASSWORD_ENCRYPTION_FAILED"

            r2 = client.get(self.REG_PAGE, headers=_build_headers(
                extra={
                    "upgrade-insecure-requests": "1",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-user": "?1",
                },
                user_agent=self.ua,
            ), follow_redirects=True)
            form = self._parse_form(r2.text)

            delay = random.uniform(CFG.register_delay_min, CFG.register_delay_max) if attempt == 0 else random.uniform(2, 5)
            step_end = time.time() + delay
            while True:
                remain = step_end - time.time()
                if remain <= 0:
                    break
                status_line(f"  ⏱  Chờ {remain:.1f}s trước khi POST...", T.GRAY)
                time.sleep(min(0.5, remain))
            status_clear()

            post_data = {
                "jazoest": form.get("jazoest", ""),
                "lsd": form.get("lsd", ""),
                "lastname": ho,
                "firstname": ten,
                "birthday_day": str(random.randint(1, 28)),
                "birthday_month": str(random.randint(1, 12)),
                "birthday_year": str(random.randint(1988, 2006)),
                "birthday_age": "",
                "did_use_age": "false",
                "sex": str(sex),
                "reg_email__": identifier,
                "reg_email_confirmation__": identifier,
                "reg_passwd__": enc_pass,
                "terms": "on",
                "ns": "0",
                "ri": form.get("ri") or get_uuid(),
                "reg_instance": form.get("reg_instance") or get_uuid(),
                "captcha_persist_data": form.get("captcha_persist_data", ""),
                "captcha_response": "",
                "locale": "vi_VN",
                "ignore": "captcha|reg_email_confirmation__",
                "__user": "0",
                "__a": "1",
                "__req": "6",
                "fb_dtsg": form.get("fb_dtsg", ""),
                "dpr": "1",
                "__ccg": "EXCELLENT",
                "__rev": form.get("rev", ""),
                "__s": form.get("s", ""),
                "__hsi": form.get("hsi", ""),
                "__dyn": form.get("dyn", ""),
                "__csr": form.get("csr", ""),
                "__spin_r": form.get("__spin_r", ""),
                "__spin_b": "trunk",
                "__spin_t": form.get("__spin_t", ""),
            }

            r_post = client.post(self.REG_POST, headers=_build_headers(
                extra={
                    "x-fb-lsd": form.get("lsd", ""),
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                },
                referer=self.REG_PAGE,
                user_agent=self.ua,
            ), data=post_data, follow_redirects=False)

            if r_post.status_code in (301, 302, 303, 307, 308):
                location = r_post.headers.get("location", "")
                if is_checkpoint_282(location):
                    status_final("  ✗ Checkpoint 282", T.RED)
                    return "CHECKPOINT_282"

            if r_post.status_code != 200:
                return "REQUEST_FAILED"

            text = r_post.text
            if "checkpoint" in text.lower() and CHECKPOINT_282_ID in text:
                return "CHECKPOINT_282"

            if "registration_succeeded" not in text:
                err_type = self._classify_reg_error(text)
                if err_type == "REG_INSTANCE_ERROR_1351050" and attempt < 1:
                    status_final(f"  ⚠ Lỗi reg_instance, thử lại...", T.YELLOW)
                    client.cookies.clear()
                    continue
                return err_type
            break

        resp = json.loads(text.replace("for (;;);", ""))
        if not resp.get("payload", {}).get("registration_succeeded"):
            return "REGISTRATION_FAILED"

        cookies = client.cookies
        cookie_str = "".join(f"{n}={v};" for n, v in cookies.items())
        c_user = cookies.get("c_user", "")
        if not c_user:
            m = re.search(r"c_user=([^;]+)", cookie_str)
            c_user = m.group(1) if m else ""

        full_name = f"{ten} {ho}".strip()
        status_final(f"  ✓ Đăng ký thành công! UID: {T.GREEN}{c_user}{T.RESET}", T.WHITE)

        if otp_mgr is None:
            return f"{c_user}|VERIFY_FAILED|NO_OTP_MGR"

        print_step("Bước 3:", f"Chờ OTP từ {'SĐT' if verify_method == 'sms' else 'Email'}...")
        otp = otp_mgr.poll_otp(timeout=CFG.otp_wait_timeout, interval=CFG.otp_poll_interval)
        if not otp:
            save_line("verify_failed.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|OTP_TIMEOUT")
            return f"{c_user}|VERIFY_FAILED|TIMEOUT"

        print_step("Bước 4:", "Verify OTP qua GraphQL...")
        verifier = OTPVerifier(client, self.ua)
        ok, _, reason = verifier.verify(
            otp, identifier, c_user,
            form.get("fb_dtsg", ""), form.get("lsd", ""), form.get("jazoest", ""),
            form.get("__spin_r", ""), form.get("__spin_t", ""),
        )

        if not ok:
            if reason == "checkpoint_282":
                save_line("checkpoint.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|CHECKPOINT_282")
                status_final("  ✗ Checkpoint 282", T.RED)
                return f"{c_user}|CHECKPOINT"
            save_line("verify_failed.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|FAIL_{reason}")
            status_final(f"  ✗ Verify fail: {reason}", T.RED)
            return f"{c_user}|VERIFY_FAILED"
        status_final(f"  ✓ OTP verified", T.WHITE)

        live_status = self._live_check(c_user)

        if live_status == "die":
            save_line("die.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|DIED")
            save_line("verify_failed.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|DIED")
            return f"{c_user}|DIED"

        if reason == "soft_block_success":
            save_line("success.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|SOFT_BLOCK|LIVE={live_status.upper()}")
            save_line("verified.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|VERIFIED_SOFT_BLOCK|LIVE={live_status.upper()}")
            return f"{c_user}|SUCCESS|VERIFIED|SOFT_BLOCK|LIVE={live_status.upper()}"

        save_line("verified.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|VERIFIED|LIVE={live_status.upper()}")
        save_line("success.txt", f"{c_user}|{password}|{cookie_str}|{identifier}|{full_name}|LIVE={live_status.upper()}")
        return f"{c_user}|SUCCESS|VERIFIED|LIVE={live_status.upper()}"

    @staticmethod
    def _classify_reg_error(text: str) -> str:
        t = text.lower()
        if "captcha" in t: return "CAPTCHA_REQUIRED"
        if "1351050" in text or "reg_instance" in t: return "REG_INSTANCE_ERROR_1351050"
        if "3252001" in text or "block" in t or "1357053" in text: return "BLOCKED_IP_OR_CHECKPOINT"
        if "checkpoint" in t and CHECKPOINT_282_ID in text: return "CHECKPOINT_282_DETECTED"
        if "email" in t and "invalid" in t: return "INVALID_EMAIL"
        if "rate" in t or "limit" in t: return "RATE_LIMITED"
        if "spam" in t: return "SPAM_DETECTED"
        return "REGISTRATION_FAILED"


# ============================================================
# STATS
# ============================================================
@dataclass
class Stats:
    total: int = 0
    success: int = 0
    verified: int = 0
    checkpoint: int = 0
    failed: int = 0
    died: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, result: str):
        with self._lock:
            self.total += 1
            if "DIED" in result:
                self.died += 1
            elif "SUCCESS|VERIFIED" in result:
                self.success += 1
                self.verified += 1
            elif "CHECKPOINT" in result:
                self.checkpoint += 1
            else:
                self.failed += 1

    def print_summary(self):
        print()
        print(f"{T.GREEN}{'═' * 50}{T.RESET}")
        print(f"{T.GREEN}{T.BOLD}              THỐNG KÊ{T.RESET}")
        print(f"{T.GREEN}{'═' * 50}{T.RESET}")
        print_kv("Tổng:", str(self.total))
        print_kv("Thành công:", f"{T.GREEN}{self.success}{T.RESET} (verified: {self.verified})")
        print_kv("Checkpoint:", f"{T.YELLOW}{self.checkpoint}{T.RESET}")
        print_kv("Died:", f"{T.RED}{self.died}{T.RESET}")
        print_kv("Thất bại:", f"{T.RED}{self.failed}{T.RESET}")
        print(f"{T.GREEN}{'═' * 50}{T.RESET}")


# ============================================================
# MAIN
# ============================================================
def main():
    print()
    print(f"{T.GREEN}{T.BOLD}{'═' * 50}{T.RESET}")
    print(f"{T.GREEN}{T.BOLD}  FB REG + OTP (metaking | bamboommo | autosms){T.RESET}")
    print(f"{T.GREEN}{T.BOLD}{'═' * 50}{T.RESET}")

    print(f"\n{T.WHITE}CHỌN PHƯƠNG THỨC VERIFY:{T.RESET}")
    print("[1] Email OTP (metaking.top)")
    print("[2] Email OTP (bamboommo.com)")
    print("[3] SMS   OTP (autosms.site)")
    method_choice = input("Chọn (1-3, mặc định 1): ").strip() or "1"

    if method_choice == "2":
        verify_method = "email_bamboo"
    elif method_choice == "3":
        verify_method = "sms"
    else:
        verify_method = "email_metaking"

    # ----- Cấu hình theo provider -----
    email_api_key = ""
    email_domain = EMAIL_DOMAIN
    bamboo_api_key = ""
    bamboo_server = BAMBOO_SERVER
    bamboo_type_mail = BAMBOO_TYPE_MAIL
    bamboo_service = BAMBOO_CODE_SERVICE
    sms_api_key = ""
    sms_country = SMS_COUNTRY
    sms_service = SMS_SERVICE

    if verify_method == "email_metaking":
        email_api_key = EMAIL_API_KEY.strip()
        if not email_api_key:
            email_api_key = input("Nhập X-API-KEY metaking.top: ").strip()
            if not email_api_key:
                print(f"{T.RED}Thiếu API key!{T.RESET}")
                return

        print(f"\n{T.WHITE}CHỌN DOMAIN EMAIL:{T.RESET}")
        print("[1] gmail.com  [2] icloud.com  [3] hotmail.com  [4] outlook.com")
        dom_choice = input("Chọn (1-4, mặc định 1): ").strip() or "1"
        email_domain = {"1": "gmail.com", "2": "icloud.com",
                        "3": "hotmail.com", "4": "outlook.com"}.get(dom_choice, "gmail.com")

        pre = EmailOTPManager(email_api_key, server=EMAIL_SERVER,
                              domain=email_domain, service_code=EMAIL_SERVICE_CODE)
        if not pre.find_service_id():
            print(f"{T.RED}Không tìm thấy service Facebook.{T.RESET}")
            return
        prices = pre.get_prices()
        if prices:
            match = next((p for p in prices if p.get("domain") == email_domain), None)
            if match:
                print(f"  {T.GRAY}Giá {email_domain}:{T.RESET} {T.GREEN}{match.get('price')} VND{T.RESET} "
                      f"{T.GRAY}(còn {match.get('quantity')}){T.RESET}")

    elif verify_method == "email_bamboo":
        bamboo_api_key = BAMBOO_API_KEY.strip()
        if not bamboo_api_key:
            bamboo_api_key = input("Nhập API key bamboommo.com: ").strip()
            if not bamboo_api_key:
                print(f"{T.RED}Thiếu API key!{T.RESET}")
                return

        pre = BambooEmailOTPManager(bamboo_api_key, server=bamboo_server,
                                    code_type_mail=bamboo_type_mail,
                                    code_service=bamboo_service)
        bal = pre.get_balance()
        if bal:
            print(f"  {T.GRAY}Balance:{T.RESET} {T.GREEN}{bal.get('balanceVnd')} VND{T.RESET}")

        types = pre.get_type_mail()
        if types:
            print(f"\n{T.WHITE}CHỌN LOẠI MAIL (bamboommo):{T.RESET}")
            for i, t in enumerate(types, 1):
                mark = " (mặc định)" if t.get("code") == "GM" else ""
                print(f"[{i}] {t.get('code')} - {t.get('name')}{mark}")
            tc = input(f"Chọn (1-{len(types)}, Enter=mặc định): ").strip()
            if tc.isdigit() and 1 <= int(tc) <= len(types):
                bamboo_type_mail = types[int(tc) - 1].get("code")

        services = pre.get_rental_service(bamboo_type_mail)
        if services:
            print(f"\n{T.WHITE}CHỌN DỊCH VỤ (bamboommo):{T.RESET}")
            for i, s in enumerate(services, 1):
                mark = " (mặc định)" if s.get("code") == "FB" else ""
                print(f"[{i}] {s.get('code')} - {s.get('name')}{mark}")
            sc = input(f"Chọn (1-{len(services)}, Enter=mặc định): ").strip()
            if sc.isdigit() and 1 <= int(sc) <= len(services):
                bamboo_service = services[int(sc) - 1].get("code")

        try:
            sv_in = input(f"\nServer (1 hoặc 2, mặc định {bamboo_server}): ").strip()
            if sv_in in ("1", "2"):
                bamboo_server = int(sv_in)
        except ValueError:
            pass

    else:  # sms
        sms_api_key = SMS_API_KEY.strip()
        if not sms_api_key:
            sms_api_key = input("Nhập API key autosms.site: ").strip()
            if not sms_api_key:
                print(f"{T.RED}Thiếu API key!{T.RESET}")
                return
        sms_country = input(f"Mã quốc gia (mặc định {SMS_COUNTRY}): ").strip() or SMS_COUNTRY
        sms_service = input(f"Mã service (mặc định {SMS_SERVICE}): ").strip() or SMS_SERVICE

        pre = SMSOTPManager(sms_api_key, country=sms_country, service=sms_service)
        bal = pre.get_balance()
        if bal:
            print(f"  {T.GRAY}Balance:{T.RESET} {T.GREEN}{bal.get('balance')}{T.RESET}")

    # ----- Proxy -----
    print(f"\n{T.WHITE}CHỌN PROXY:{T.RESET}")
    print("[1] NestProxy  [2] Proxy tĩnh  [3] Không dùng (mặc định)")
    proxy_choice = input("Chọn (1-3): ").strip() or "3"
    proxy_type = "none"
    nestproxy_keys = []
    static_proxies = []
    if proxy_choice == "1":
        proxy_type = "nestproxy"
        print("Nhập NestProxy keys (Enter trống để kết thúc):")
        while True:
            k = input(f"Key #{len(nestproxy_keys) + 1}: ").strip()
            if not k: break
            nestproxy_keys.append(k)
        if not nestproxy_keys: proxy_type = "none"
    elif proxy_choice == "2":
        proxy_type = "static"
        print("Nhập proxy tĩnh (Enter trống để kết thúc):")
        while True:
            p = input(f"Proxy #{len(static_proxies) + 1}: ").strip()
            if not p: break
            static_proxies.append(p)
        if not static_proxies: proxy_type = "none"

    try:
        num_accounts = int(input("\nSố tài khoản (mặc định 1): ").strip() or "1")
    except ValueError:
        num_accounts = 1
    try:
        num_threads = int(input("Số luồng (mặc định 1): ").strip() or "1")
    except ValueError:
        num_threads = 1

    try:
        spam_in = input(f"Số lần spam OTP (mặc định {CFG.otp_spam_count}): ").strip()
        if spam_in:
            CFG.otp_spam_count = max(1, int(spam_in))
    except ValueError:
        pass

    proxy_manager = ProxyManager(proxy_type, nestproxy_keys, static_proxies)
    stats = Stats()

    thread_local = threading.local()

    def get_thread_otp_mgr() -> BaseOTPManager:
        if not hasattr(thread_local, "mgr"):
            if verify_method == "sms":
                thread_local.mgr = SMSOTPManager(sms_api_key, country=sms_country, service=sms_service)
            elif verify_method == "email_bamboo":
                thread_local.mgr = BambooEmailOTPManager(
                    api_key=bamboo_api_key, server=bamboo_server,
                    code_type_mail=bamboo_type_mail, code_service=bamboo_service,
                )
            else:
                thread_local.mgr = EmailOTPManager(
                    api_key=email_api_key, server=EMAIL_SERVER,
                    domain=email_domain, service_code=EMAIL_SERVICE_CODE,
                )
        return thread_local.mgr

    def create_one(idx: int) -> str:
        print_box(f"TÀI KHOẢN {idx + 1}/{num_accounts}")

        mgr = get_thread_otp_mgr()
        mgr.reset()

        try:
            rent_data = mgr.rent()
            if not rent_data:
                print(f"  {T.RED}✗ Không thuê được email/SĐT{T.RESET}")
                return "RENT_FAILED"
            identifier = mgr.current_identifier
            if not identifier:
                return "RENT_FAILED"
        except Exception as e:
            log.error(f"Lỗi thuê: {e}")
            return "RENT_FAILED"

        HO_LIST = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"]
        TEN_LIST = ["An", "Bình", "Châu", "Dũng", "Hà", "Hùng", "Khánh", "Linh", "Minh",
                    "Nam", "Phương", "Quân", "Sơn", "Thảo", "Tuấn", "Vy", "Yến", "Long", "Trang", "Nhi"]
        ho = random.choice(HO_LIST)
        ten = random.choice(TEN_LIST)
        full_name = f"{ho} {ten}"
        sex = random.choice([1, 2])
        password = "".join(random.choices(string.ascii_letters + string.digits, k=15))

        src = "SĐT" if verify_method == "sms" else "Email"
        print_kv(f"{src}:", identifier)
        print_kv("Họ tên:", full_name)
        print_kv("Sex:", "Nữ" if sex == 1 else "Nam")
        print_kv("Pass:", password)
        print_kv("Proxy:", proxy_type if proxy_type != "none" else "none")
        print()

        local_registrar = FacebookRegistrar(proxy_manager)
        result = local_registrar.register(
            ho, ten, identifier, password, sex,
            token_idx=idx % max(1, len(nestproxy_keys) or 1),
            otp_mgr=mgr, verify_method=("sms" if verify_method == "sms" else "email"),
        )

        if "SUCCESS" not in result and "CHECKPOINT" not in result and "DIED" not in result:
            try: mgr.cancel()
            except Exception: pass

        if "DIED" in result:
            print(f"  → {T.RED}{T.BOLD}KẾT QUẢ: DIED (UID chết){T.RESET}")
        elif "SUCCESS|VERIFIED" in result:
            print(f"  → {T.GREEN}{T.BOLD}KẾT QUẢ: ✓ THÀNH CÔNG{T.RESET}")
        elif "CHECKPOINT" in result:
            print(f"  → {T.YELLOW}{T.BOLD}KẾT QUẢ: CHECKPOINT{T.RESET}")
        else:
            print(f"  → {T.RED}{T.BOLD}KẾT QUẢ: THẤT BẠI ({result}){T.RESET}")
        print()

        return result

    try:
        if num_threads == 1:
            for i in range(num_accounts):
                try:
                    r = create_one(i)
                    stats.record(r)
                    if i < num_accounts - 1:
                        w = random.uniform(CFG.between_accounts_min, CFG.between_accounts_max)
                        time.sleep(w)
                except KeyboardInterrupt:
                    print(f"\n{T.YELLOW}Dừng bởi user!{T.RESET}")
                    break
        else:
            with ThreadPoolExecutor(max_workers=num_threads) as ex:
                futs = {ex.submit(create_one, i): i for i in range(num_accounts)}
                for fut in as_completed(futs):
                    try:
                        r = fut.result()
                        stats.record(r)
                    except Exception as e:
                        log.error(f"Thread error: {e}")
                        stats.record("THREAD_ERROR")
    finally:
        stats.print_summary()
        print(f"\n{T.GRAY}File kết quả:{T.RESET}")
        for f in ["success.txt", "verified.txt", "die.txt", "checkpoint.txt", "verify_failed.txt"]:
            print(f"  {T.GRAY}•{T.RESET} reg/{f}")


if __name__ == "__main__":
    try:
        os.system("cls" if os.name == "nt" else "clear")
        main()
    except KeyboardInterrupt:
        print(f"\n\n{T.YELLOW}[!] Đã dừng bởi người dùng!{T.RESET}")
    except Exception as e:
        print(f"\n{T.RED}[!] Lỗi: {e}{T.RESET}")
        traceback.print_exc()