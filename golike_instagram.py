
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import re
import secrets
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import sys
from urllib.parse import quote, unquote, urlencode, urlsplit

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import requests
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    raise SystemExit("Thiếu thư viện. Chạy: python -m pip install requests cryptography")

GATEWAY = "https://gateway.golike.net/api"
SECURITY = "https://api.golike.net"
ORIGIN = "https://app.golike.net"
IG_ORIGIN = "https://www.instagram.com"
SOLVER = "https://solvercf.com/token/extension"
VERSION = "26.09.17.1"
CLIENT = "109096667105508"
GOLIKE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Version/17.6 "
             "Mobile/15E148 Safari/604.1")
IG_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
TIMEOUT = (10, 30)
MAX_ERRORS = 5
MAX_EMPTY = 5
RECEIVE_DELAY = (15, 20)
COMPLETE_DELAY = (10, 15)


class StopRun(Exception):
    """Lỗi cần dừng: xác thực, captcha, hạn chế, hoặc kết quả không rõ."""


class SkipJob(Exception):
    """Đích/job không hỗ trợ; chưa có thao tác thành công."""


def compact(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def first(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
            return str(value).strip()
    return ""


def numeric(value: str) -> int | str:
    return int(value) if re.fullmatch(r"\d+", value) else value


def amount(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
        return result if result.is_finite() and result >= 0 else Decimal(0)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)


def accepted(root: dict) -> bool:
    if root.get("success") is False or root.get("status") in ("error", "fail", "failed"):
        return False
    return root.get("success") is True or root.get("status") in (200, "200", "success", "ok")


def obj_data(root: dict) -> dict:
    data = root.get("data")
    return data if isinstance(data, dict) else root


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False 
    return session


def request_json(session, method: str, url: str, *, label: str,
                 uncertain: bool = False, captcha_response: bool = False,
                 allow_status: tuple[int, ...] = (), **kwargs) -> dict:
    """Không tự retry POST. Không in exception chứa URL/body/credential."""
    try:
        response = session.request(method, url, timeout=TIMEOUT, allow_redirects=False, **kwargs)
    except requests.RequestException:
        detail = "Kết quả chưa rõ; không gửi lại để tránh làm trùng." if uncertain else "Kiểm tra kết nối rồi thử lại."
        raise StopRun(f"{label}: lỗi kết nối. {detail}") from None
    try:
        root = response.json()
    except ValueError:
        raise StopRun(f"{label}: phản hồi không phải JSON; dừng kiểm tra phiên.") from None
    if not isinstance(root, dict):
        raise StopRun(f"{label}: cấu trúc phản hồi không hợp lệ.")
    if not 200 <= response.status_code < 300:
        if response.status_code in allow_status:
            return root
        actions = [first(x, k).lower() for x in (root, obj_data(root)) for k in ("action", "reason")]
        if not (captcha_response and response.status_code == 403 and "captcha" in actions):
            detail = " Dừng để tránh gửi trùng." if uncertain else ""
            msg = first(root, "message", "error")
            detail_msg = f" ({msg})" if msg else ""
            raise StopRun(f"{label}: HTTP {response.status_code}{detail_msg}.{detail}")
    return root


def triple_t() -> str:
    result = str(int(time.time())).encode()
    for _ in range(3):
        result = base64.b64encode(result)
    return result.decode()


def parse_signing_key(value: str) -> bytes:
    try:
        if re.fullmatch(r"[0-9a-fA-F]{64}", value):
            key = bytes.fromhex(value)
        else:
            key = base64.b64decode(value, validate=True)
        if len(key) != 32:
            raise ValueError
        return key
    except (ValueError, TypeError):
        raise StopRun("GoLike trả signing key không hợp lệ.") from None


def gweb_auth(key: bytes, scheme: str, device: str, user: int, method: str,
              path: str, body: str, *, timestamp: int | None = None,
              nonce: bytes | None = None, iv: bytes | None = None) -> str:
    """AES-GCM: version|iv|tag|ciphertext, AAD=gweb-v2/v3."""
    masks = {
        "gweb-v2": "b73a158cf39f8825a2ab95c5c90e54b475a900271d5ab4c23fa82dabbccbfd8a",
        "gweb-v3": "ad51dd3affdce8070210c36571decebdd5a37dd47396c31bf5b4adb711ab6713",
    }
    if scheme not in masks or len(key) != 32:
        raise StopRun("GoLike chưa được hỗ trợ; ")
    version = int(scheme[-1])
    salt = f"glk-gweb-sig-v{version}-2026q3"
    ikm = bytes(a ^ b for a, b in zip(key, bytes.fromhex(masks[scheme])))
    prk = hmac.digest(salt.encode(), ikm, "sha256")
    aes_key = hmac.digest(prk, f"aes-gcm-key-gweb-v{version}".encode() + b"\x01", "sha256")
    now = int(time.time() * 1000) if timestamp is None else timestamp
    nonce = secrets.token_bytes(16) if nonce is None else nonce
    iv = secrets.token_bytes(12) if iv is None else iv
    digest = hashlib.sha256(body.encode()).hexdigest()
    method = method.upper()
    proof = hashlib.sha256(f"{scheme}:{salt}:{now}:{user}:{method}:{path}:{digest}".encode()).hexdigest()[8:32]
    payload = {"t": now, "x": base64.urlsafe_b64encode(nonce).decode().rstrip("="),
               "d": device, "u": user, "n": method, "k": path, "q": digest, "w": proof}
    ciphertext_tag = AESGCM(aes_key).encrypt(iv, compact(payload).encode(), scheme.encode())
    wire = bytes([version]) + iv + ciphertext_tag[-16:] + ciphertext_tag[:-16]
    return base64.urlsafe_b64encode(wire).decode().rstrip("=")


def drag_points(geometry: dict) -> list[list[float | int]]:
    coordinates = []
    for name in ("start", "waypoint", "target"):
        point = geometry.get(name)
        if not isinstance(point, dict):
            raise StopRun("Captcha kéo thiếu geometry; không đoán tọa độ.")
        try:
            xy = (float(point["x"]), float(point["y"]))
            if any(not math.isfinite(v) or abs(v) > 10000 for v in xy):
                raise ValueError
        except (KeyError, ValueError, TypeError):
            raise StopRun("Tọa độ captcha không hợp lệ.") from None
        coordinates.append(xy)
    points = []
    elapsed = 0
    for start, end, count, step in ((coordinates[0], coordinates[1], 45, 16),
                                    (coordinates[1], coordinates[2], 50, 15)):
        for index in range(count):
            fraction = index / (count - 1)
            elapsed += step
            xy = [math.floor((start[i] + (end[i] - start[i]) * fraction) * 100 + 0.5) / 100 for i in (0, 1)]
            points.append([elapsed, *xy])
    for _ in range(5):
        elapsed += 20
        points.append([elapsed, *(math.floor(v * 100 + 0.5) / 100 for v in coordinates[2])])
    return points


class SolverCF:
    def __init__(self, key: str, session=None):
        self.key = key.strip()
        self.session = session if session is not None else new_session()

    def close(self):
        self.session.close()

    def call(self, endpoint: str, payload: dict) -> dict:
        root = request_json(self.session, "POST", f"{SOLVER}/{endpoint}", label="SolverCF",
                            json={"clientKey": self.key, **payload})
        if root.get("errorId") not in (0, "0"):
            raise StopRun("SolverCF từ chối yêu cầu; kiểm tra API key/số dư hoặc dịch vụ.")
        return root

    def balance(self) -> Decimal:
        root = self.call("getBalance", {})
        if "balance" not in root:
            raise StopRun("SolverCF không trả số dư.")
        return amount(root["balance"])

    def turnstile(self, site_key: str, user_agent: str, budget: float = 45) -> tuple[str, str]:
        if not site_key or not self.key:
            raise StopRun("Turnstile cần API key SolverCF và site key; nhập ở mục 4.")
        
        root = self.call("createTask", {"task": {"type": "TurnstileTask", "websiteUrl": ORIGIN,
                                               "websiteKey": site_key, "userAgent": user_agent}})
        task_id = root.get("taskId")
        if not isinstance(task_id, (str, int)) or not task_id:
            raise StopRun("SolverCF không trả taskId; không tự tạo thêm tác vụ có phí.")
        deadline = time.monotonic() + budget
        for _ in range(max(1, math.ceil(budget / 1.5))):
            if time.monotonic() >= deadline:
                break
            time.sleep(min(1.5, max(0, deadline - time.monotonic())))
            if time.monotonic() >= deadline:
                break
            result = self.call("getTaskResult", {"taskId": task_id})
            status = result.get("status")
            if status in ("ready", "success"):
                solution = result.get("solution")
                if not isinstance(solution, dict) or not first(solution, "token"):
                    raise StopRun("SolverCF trả kết quả thiếu token.")
                return first(solution, "token"), first(solution, "userAgent") or user_agent
            if status not in ("created", "processing"):
                raise StopRun("Tác vụ SolverCF thất bại/hết hạn hoặc trả trạng thái lạ.")
        raise StopRun("SolverCF chưa giải xong trong thời gian chờ; không tự tạo thêm tác vụ.")


@dataclass
class Job:
    job_id: str
    kind: str
    object_id: str = ""
    link: str = ""
    text: str = ""
    comment_id: str = ""
    price: Decimal = Decimal(0)
    raw_type: str = ""

    @classmethod
    def parse(cls, data: dict) -> Job:
        job_id = first(data, "id", "job_id")
        raw = first(data, "type", "job_type").lower()
        if not job_id or not raw:
            raise StopRun("Job thiếu ID/loại; không mặc định thành follow.")
        normalized = raw.removeprefix("instagram_").removesuffix("_instagram")
        kind = {"follow": "follow", "like": "like", "comment": "comment", "likecmt": "like_comment",
                "like_comment": "like_comment", "comment_like": "like_comment"}.get(normalized, "unsupported")
        message = first(data, "message", "comment", "comment_text", "commentText", "content")
        if not message and isinstance(data.get("data"), dict):
            message = first(data["data"], "message", "comment", "comment_text", "content")
        price = next((amount(data[k]) for k in ("fix_coin_job", "price_after_cost", "price", "coin")
                      if amount(data.get(k)) > 0), Decimal(0))
        return cls(job_id, kind, first(data, "object_id", "target_id", "uid"),
                   first(data, "link", "url"), message, first(data, "comment_id"), price, raw)


class GoLike:
    def __init__(self, token: str, session=None):
        self.token = re.sub(r"^Bearer\s+", "", token.strip(), flags=re.I)
        if not self.token or re.search(r"\s", self.token):
            raise StopRun("Token GoLike trống hoặc chứa khoảng trắng.")
        self.session = session if session is not None else new_session()
        self.device = str(uuid.uuid4())
        self.user_id = 0
        self.username = ""
        self.name = ""
        self.coin: Decimal = Decimal(0)
        self.temp_coin: Decimal = Decimal(0)
        self.key = b""
        self.expires = 0.0
        self.scheme = "gweb-v3"
        self.events = secrets.randbelow(3) + 2
        self.solver: SolverCF | None = None
        self.handled: set[str] = set()  

    def close(self):
        self.session.close()

    def format_balance(self) -> str:
        coin = amount(self.coin)
        temp = amount(self.temp_coin)
        s = f"Số dư: {coin:,.0f}đ"
        if temp > 0:
            s += f" (Chờ duyệt: {temp:,.0f}đ)"
        return s

    def format_info(self) -> str:
        u = str(self.username) if isinstance(self.username, str) else ""
        n = str(self.name) if isinstance(self.name, str) else ""
        uid = str(self.user_id) if isinstance(self.user_id, (int, str)) and str(self.user_id).isdigit() else ""
        name_str = f" ({n})" if n and n != u else ""
        uid_str = f" [UID: {uid}]" if uid else ""
        return f"@{u}{name_str}{uid_str} | {self.format_balance()}"

    def headers(self) -> dict:
        headers = {"Accept": "application/json, text/plain, */*", "Authorization": "Bearer " + self.token,
                   "Content-Type": "application/json;charset=utf-8", "Origin": ORIGIN,
                   "Referer": ORIGIN + "/", "User-Agent": GOLIKE_UA, "g-device-id": self.device,
                   "g-version": VERSION, "g-client": CLIENT, "t": triple_t(),
                   "Accept-Language": "vi,en-US;q=0.9,en;q=0.8", "Cache-Control": "no-cache",
                   "Pragma": "no-cache", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
                   "Sec-Fetch-Site": "same-site"}
        if self.username:
            headers["g-username"] = quote(self.username, safe="")
        return headers

    def verify(self):
        root = request_json(self.session, "GET", GATEWAY + "/users/me", label="Đăng nhập GoLike", headers=self.headers())
        profile = obj_data(root)
        uid = first(profile, "id", "user_id")
        if not accepted(root) or not uid.isdigit() or int(uid) <= 0:
            raise StopRun("Không xác minh được tài khoản GoLike; kiểm tra token.")
        self.user_id = int(uid)
        self.username = first(profile, "username", "name")
        self.name = first(profile, "name", "username")
        self.coin = amount(profile.get("coin", 0))
        self.temp_coin = amount(profile.get("temp_coin", 0))
        if not self.username:
            raise StopRun("GoLike chưa trả đủ thông tin phiên đăng nhập.")

    def ensure_key(self):
        if self.key and time.time() < self.expires - 60:
            return
        if not self.user_id:
            self.verify()
        root = request_json(self.session, "POST", SECURITY + "/api/v1/security/session",
                            label="Phiên bảo mật GoLike", data="{}", headers={**self.headers(), "g-scheme": self.scheme})
        data = obj_data(root)
        self.guard_action(root, data)
        key = parse_signing_key(first(data, "signing_key"))
        scheme = first(data, "schemeVersion", "scheme_version") or "gweb-v3"
        scheme = {"2": "gweb-v2", "3": "gweb-v3"}.get(scheme, scheme)
        if scheme not in ("gweb-v2", "gweb-v3"):
            raise StopRun("GoLike yêu cầu phiên bản ký mới; cần cập nhật source.")
        try:
            expiry = float(data["exp"])
            if not math.isfinite(expiry) or expiry <= time.time() + 60:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise StopRun("GoLike trả phiên bảo mật thiếu/sai hạn dùng.") from None
        self.key, self.expires, self.scheme = key, expiry, scheme

    @staticmethod
    def guard_action(root: dict, data: dict):
        actions = [first(x, key).lower() for x in (root, data) for key in ("action", "reason")]
        if any(action in ("update", "update_required", "retry", "rejected", "blocked") for action in actions):
            raise StopRun("GoLike từ chối phiên hoặc yêu cầu cập nhật; không bỏ qua xác thực.")
        if "captcha" not in actions and any(
                x.get("success") is False or ("status" in x and x["status"] not in (200, "200", "success", "ok"))
                for x in (root, data)):
            raise StopRun("GoLike trả lỗi bảo mật; không sử dụng token từ phản hồi lỗi.")

    def signed_security(self, path: str, body: str, ua: str = "") -> dict:
        auth = gweb_auth(self.key, self.scheme, self.device, self.user_id, "POST", path, body)
        headers = {**self.headers(), "g-scheme": self.scheme, "g-auth": auth}
        if ua:
            headers["User-Agent"] = ua
        return request_json(self.session, "POST", SECURITY + path, label="Bảo mật GoLike", data=body, headers=headers,
                            captcha_response=path == "/api/v1/security/token")

    def solve_captcha(self):
        print("\n[!] GoLike yêu cầu xác minh Captcha!", flush=True)
        root = self.signed_security("/api/v1/security/captcha/challenge", "{}")
        data = obj_data(root)
        challenge = data.get("challenge", data)
        if not isinstance(challenge, dict):
            raise StopRun("GoLike không trả challenge hợp lệ.")
        cid = first(challenge, "challengeId", "challenge_id", "id")
        if not cid:
            raise StopRun("Captcha thiếu challengeId.")
        site_key = first(challenge, "siteKey", "site_key")
        ua = ""
        if site_key or first(challenge, "kind").lower() == "turnstile":
            if self.solver is None:
                raise StopRun("Gặp Turnstile: nhập API key SolverCF ở mục 4 trước.")
            print(" -> Đang giải Cloudflare Turnstile qua SolverCF...", flush=True)
            solved, ua = self.solver.turnstile(site_key, GOLIKE_UA)
            payload = {"challengeId": cid, "token": solved}
        else:
            print(" -> Đang tự động giải Captcha kéo", flush=True)
            geometry = challenge.get("geometry", challenge)
            if not isinstance(geometry, dict):
                raise StopRun("Loại captcha chưa hỗ trợ.")
            points = drag_points(geometry)
            time.sleep(points[-1][0] / 1000)
            payload = {"challengeId": cid, "points": points}
        result = self.signed_security("/api/v1/security/captcha/verify", compact(payload), ua)
        verified = obj_data(result)
        self.guard_action(result, verified)
        if verified.get("ok") is not True and verified.get("success") is not True:
            raise StopRun("GoLike không chấp nhận kết quả captcha; đã dừng.")
        print("[✓] Xác minh Captcha thành công! Tiếp tục làm job...", flush=True)

    def mint(self, method: str, path_query: str, body: str, price: Decimal) -> str:
        self.ensure_key()
        parts = urlsplit(path_query)
        path = parts.path if parts.path.startswith("/api/") else "/api/" + parts.path.lstrip("/")
        tel = {"trg": "click", "aut": 0, "idle": 25 + secrets.randbelow(71),
               "iev": self.events, "vis": 1, "foc": 1}
        self.events += secrets.randbelow(3) + 1
        if price > 0:
            tel["val"] = int(price)
        payload = {"plt": "instagram", "act": "get_job" if method == "GET" else "complete_job",
                   "req": {"method": method, "path": path, "query": parts.query, "body": body}, "tel": tel}
        exact = compact(payload)
        for attempt in range(2):
            root = self.signed_security("/api/v1/security/token", exact)
            data = obj_data(root)
            self.guard_action(root, data)
            actions = [first(x, "action").lower() for x in (root, data)]
            reasons = [first(x, "reason").lower() for x in (root, data)]
            if "captcha" in actions + reasons:
                if attempt:
                    raise StopRun("GoLike vẫn yêu cầu captcha sau verify; đã dừng.")
                self.solve_captcha()
                continue  
            sig = first(data, "token", "sig")
            if not sig:
                raise StopRun("GoLike không trả sig; không gửi job thiếu xác thực.")
            return sig
        raise StopRun("Không cấp được sig GoLike.")

    def gateway(self, method: str, path: str, payload: dict | None = None,
                *, signed: bool = False, price: Decimal = Decimal(0),
                allow_status: tuple[int, ...] = (), check_accepted: bool = True) -> dict:
        body = compact(payload) if payload is not None else ""
        headers = self.headers()
        if signed:
            headers["sig"] = self.mint(method, path, body, price)
        root = request_json(self.session, method, GATEWAY + "/" + path.lstrip("/"),
                            label="GoLike", uncertain=method == "POST",
                            headers=headers, data=body if method == "POST" else None,
                            allow_status=allow_status)
        if check_accepted and not accepted(root):
            msg = first(root, "message", "error")
            detail = f" ({msg})" if msg else ""
            raise StopRun(f"GoLike từ chối yêu cầu{detail}. Kiểm tra phiên/liên kết hoặc tình trạng máy chủ.")
        return root

    def linked_account(self, username: str, uid: str) -> str:
        root = self.gateway("GET", "instagram-account?limit=200")
        rows = root.get("data")
        if isinstance(rows, dict):
            rows = next((rows[k] for k in ("data", "list", "accounts") if isinstance(rows.get(k), list)), None)
        if not isinstance(rows, list):
            raise StopRun("GoLike trả danh sách liên kết không hợp lệ.")
        matches = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            handle = first(row, "instagram_username", "username", "unique_id", "account_name").lstrip("@")
            row_uid = first(row, "instagram_id", "instagram_uid", "uid")
            account_id = first(row, "id", "_id", "instagram_account_id", "account_id")
            if not account_id:
                continue
            matched = False
            if uid and row_uid and str(row_uid) == str(uid):
                matched = True
            elif username and handle and handle.lower() == username.lower():
                matched = True
            if matched:
                if row_uid and uid and str(row_uid) != str(uid):
                    raise StopRun("UID IG không khớp tài khoản liên kết trên GoLike.")
                matches.append((str(account_id), handle))
        if len({acc_id for acc_id, _ in matches}) != 1:
            raise StopRun("IG chưa liên kết hoặc dữ liệu bị trùng. Liên kết đúng nick trên web GoLike trước.")
        acc_id, handle = matches[0]
        self.last_matched_username = handle
        return acc_id

    def auto_link(self, instagram: Instagram) -> str:
        if not getattr(instagram, "username", ""):
            if hasattr(instagram, "verify"):
                try:
                    instagram.verify()
                except Exception:
                    pass
        handle = (getattr(instagram, "username", "") or "").lstrip("@").strip()
        uid = getattr(instagram, "uid", "")
        name = f"@{handle}" if handle else f"UID {uid}"
        print(f"\n[!] Nick {name} chưa có liên kết trên GoLike. Đang tiến hành tự động liên kết...", flush=True)

        root = self.gateway("GET", "instagram-account?limit=200")
        link_verify = root.get("link_verify_follow") or root.get("link") or ""
        target_follow = "james111119999"
        if link_verify:
            clean = re.sub(r"^https?://(?:www\.)?instagram\.com/", "", str(link_verify).strip(), flags=re.I)
            clean = clean.split("/")[0].replace("@", "").strip()
            if clean:
                target_follow = clean

        print(f"  -> Đang follow kênh xác minh @{target_follow} trên Instagram...", flush=True)
        if hasattr(instagram, "perform"):
            try:
                job = Job(job_id="verify_link", kind="follow", object_id=target_follow,
                          link=f"https://www.instagram.com/{target_follow}/")
                instagram.perform(job)
                print(f"  [✓] Đã follow @{target_follow} thành công! Chờ 5s để GoLike đồng bộ...", flush=True)
                time.sleep(5)
            except Exception as exc:
                print(f"  [!] Lưu ý khi follow @{target_follow}: {exc}", flush=True)

        target_name = handle or uid
        print(f"  -> Đang gửi yêu cầu xác minh liên kết @{target_name} lên GoLike...", flush=True)
        candidates = [
            ("instagram-account/verify-account", {"object_id": target_name}),
            ("instagram-account/verify-account-id", {"unique_id": target_name}),
            ("instagram-account", {"instagram_username": target_name, "link": f"https://www.instagram.com/{target_name}/"}),
        ]
        last_msg = ""
        for path, payload in candidates:
            try:
                res = self.gateway("POST", path, payload, allow_status=(200, 201, 400, 422), check_accepted=False)
                msg = first(res, "message", "error") or first(obj_data(res), "message", "error") or ""
                if accepted(res) or res.get("status") in (200, 201, "200", "201") or any(
                    k in str(res) for k in ("thành công", "phê duyệt", "đã tồn tại", "đã được thêm")
                ):
                    break
                if msg:
                    last_msg = msg
            except Exception as e:
                last_msg = str(e)

        time.sleep(2)
        try:
            account_id = self.linked_account(handle, uid)
            print(f"  [✓] TỰ ĐỘNG LIÊN KẾT THÀNH CÔNG! Account ID GoLike: {account_id}\n", flush=True)
            return account_id
        except Exception:
            pass

        err_detail = f" ({last_msg})" if last_msg else ""
        raise StopRun(f"Tự động liên kết {name} thất bại{err_detail}. Vui lòng liên kết thủ công trên web GoLike.")

    def get_job(self, account_id: str) -> Job | None:
        path = "advertising/publishers/instagram/jobs?" + urlencode(
            {"instagram_account_id": account_id, "data": "null", "_": int(time.time() * 1000)})
        root = self.gateway("GET", path, signed=True)
        if "data" not in root:
            raise StopRun("GoLike trả job thiếu data; không tính là hết job.")
        data = root["data"]
        if data is None or data == [] or data == {}:
            return None
        if isinstance(data, dict):
            for key in ("job", "data"):
                if isinstance(data.get(key), dict) and not first(data, "id", "job_id"):
                    data = data[key]
        if not isinstance(data, dict):
            raise StopRun("Định dạng job GoLike chưa hỗ trợ.")
        return Job.parse(data)

    def complete(self, job: Job, account_id: str) -> Decimal:
        root = self.gateway("POST", "advertising/publishers/instagram/complete-jobs", {
            "instagram_users_advertising_id": numeric(job.job_id), "instagram_account_id": numeric(account_id),
            "ads_id": numeric(job.job_id), "account_id": numeric(account_id), "async": True, "data": None,
        }, signed=True, price=job.price, allow_status=(400, 422), check_accepted=False)
        if not accepted(root) or root.get("status") in (400, 422, "400", "422"):
            msg = first(root, "message", "error") or first(obj_data(root), "message", "error")
            status_code = root.get("status")
            detail = f"{msg}" if msg else (f"mã {status_code}" if status_code else "bị từ chối")
            raise SkipJob(f"GoLike từ chối hoàn thành ({detail})")
        data = obj_data(root)
        keys = ("price_after_cost", "price_after", "priceAfterCost", "prices", "price", "coin", "money", "reward", "amount")
        earned = next((amount(data[k]) for k in keys if k in data and amount(data[k]) > 0), Decimal(0))
        if earned <= 0 and isinstance(root, dict):
            earned = next((amount(root[k]) for k in keys if k in root and amount(root[k]) > 0), Decimal(0))
        if earned <= 0 and job.price > 0:
            earned = job.price
        return earned

    def skip(self, job: Job, account_id: str):
        self.gateway("POST", "advertising/publishers/instagram/skip-jobs", {
            "ads_id": numeric(job.job_id), "account_id": numeric(account_id),
            "object_id": job.object_id or job.link, "type": job.raw_type,
        }, allow_status=(400, 422), check_accepted=False)


def parse_ig_cookie(cookie: str) -> tuple[dict[str, str], str]:
    cookie = re.sub(r"^cookie:\s*", "", cookie.strip(), flags=re.I)
    if "\n" in cookie or "\r" in cookie:
        raise StopRun("Cookie phải nằm trên một dòng.")
    result = {}
    for part in cookie.split(";"):
        name, separator, value = part.strip().partition("=")
        if separator and re.fullmatch(r"[A-Za-z0-9_-]+", name) and value.strip():
            result[name] = value.strip()
    if "sessionid" not in result:
        raise StopRun("Thiếu sessionid Instagram. c_user/xs là cookie Facebook, không dùng ở đây.")
    uid = result.get("ds_user_id") or result.get("ig-u-ds-user-id") or unquote(result["sessionid"]).split(":")[0]
    if not uid.isdigit():
        raise StopRun("Cookie IG thiếu UID hợp lệ.")
    result.setdefault("ds_user_id", uid)
    result.setdefault("csrftoken", secrets.token_hex(16))
    return result, uid


def ig_url(link: str) -> str:
    if not link:
        return ""
    try:
        parts = urlsplit(link)
        port = parts.port
    except ValueError:
        raise SkipJob("Link đích không hợp lệ.") from None
    if parts.scheme != "https" or parts.hostname not in ("www.instagram.com", "instagram.com"):
        raise SkipJob("Link đích không phải HTTPS Instagram.")
    if parts.username or parts.password or port not in (None, 443):
        raise SkipJob("Link đích không hợp lệ.")
    return IG_ORIGIN + parts.path


class Instagram:
    def __init__(self, cookie: str, session=None):
        self.raw_cookie = cookie
        fields, self.uid = parse_ig_cookie(cookie)
        self.session = session if session is not None else new_session()
        for key, value in fields.items():
            self.session.cookies.set(key, value, domain=".instagram.com", path="/", secure=True)
        self.username = ""
        self.dtsg = ""
        self.lsd = ""

    def close(self):
        self.session.close()

    def headers(self, referer: str = "") -> dict:
        csrf = next((c.value for c in reversed(list(self.session.cookies)) if c.name == "csrftoken"), "")
        return {"User-Agent": IG_UA, "Accept": "*/*", "Origin": IG_ORIGIN,
                "Referer": ig_url(referer) if referer else IG_ORIGIN + "/",
                "X-IG-App-ID": "936619743392459", "X-ASBD-ID": "359341", "X-CSRFToken": csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Language": "en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7",
                "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin",
                "X-Bloks-Version-Id": "61fc9465e13b77eaa110f317859102ba7fb93a0a2bcc08c46473da6713640739"}

    def read_response(self, method: str, path: str, *, referer: str = "", extra_headers=None, **kwargs):
        try:
            response = self.session.request(method, IG_ORIGIN + path, headers={**self.headers(referer), **(extra_headers or {})},
                                            timeout=TIMEOUT, allow_redirects=False, **kwargs)
        except requests.RequestException:
            if method == "POST":
                raise StopRun("IG mất kết nối khi thao tác: kết quả chưa rõ, không làm lại/báo hoàn thành.") from None
            raise StopRun("Không kết nối được Instagram.") from None
        if response.status_code in (301, 302, 303, 307, 308, 401, 403, 429):
            raise StopRun("IG yêu cầu đăng nhập/xác minh hoặc đang hạn chế. Dừng tài khoản.")
        if response.status_code >= 500:
            raise StopRun("IG lỗi máy chủ; kết quả chưa rõ nên đã dừng.")
        return response

    @staticmethod
    def decode(response) -> dict:
        try:
            text = response.text.removeprefix("for (;;);").strip()
            root = json.loads(text)
        except (ValueError, TypeError):
            raise StopRun("IG trả dữ liệu không hợp lệ; không coi HTTP 200 là thành công.") from None
        if not isinstance(root, dict):
            raise StopRun("IG trả cấu trúc dữ liệu lạ.")
       
        message = compact({k: root[k] for k in ("message", "error", "errors", "error_type", "feedback_message") if k in root}).lower()
        if any(code in message for code in ("login_required", "challenge_required", "checkpoint_required",
                                            "feedback_required", "please wait a few minutes", "spam")):
            raise StopRun("IG yêu cầu xác minh hoặc hạn chế thao tác; đã dừng tài khoản.")
        return root

    def verify(self):
        paths = ("/api/v1/accounts/current_user/?edit=true", "/api/v1/accounts/current_user/")
        for path in paths:
            response = self.read_response("GET", path)
            if response.status_code in (404, 405):
                continue
            root = self.decode(response)
            user = root.get("user", root.get("form_data"))
            if response.status_code != 200 or root.get("status") == "fail" or not isinstance(user, dict):
                raise StopRun("Không xác minh được phiên đăng nhập IG; không dùng profile công khai để báo Live.")
            if first(user, "pk", "id") != self.uid or not first(user, "username"):
                raise StopRun("Thông tin tài khoản IG không khớp cookie.")
            self.username = first(user, "username")
            self.sync_tokens()
            return
        raise StopRun("API xác minh IG không khả dụng; cần cập nhật trước khi chạy.")

    def sync_tokens(self):
        html = ""
        try:
            response = self.read_response("GET", "/")
            if response.status_code == 200:
                html = response.text
        except Exception:
            pass
        if not html:
            try:
                headers = {**self.headers(), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
                res = self.session.get(IG_ORIGIN + "/", headers=headers, timeout=TIMEOUT, allow_redirects=True)
                if res.status_code == 200:
                    html = res.text
            except Exception:
                pass
        if html:
            for pattern in (r'"DTSGInitialData"[^}]*"token"\s*:\s*"([^"\\]+)"',
                            r'DTSGInitialData[^}]*"token":"([^"]+)"',
                            r'"fb_dtsg"\s*:\s*"([^"\\]+)"'):
                m = re.search(pattern, html)
                if m:
                    self.dtsg = m.group(1)
                    break
            for pattern in (r'"LSD"[^}]*"token"\s*:\s*"([^"\\]+)"',
                            r'"lsd"\s*:\s*"([^"\\]+)"'):
                m = re.search(pattern, html)
                if m:
                    self.lsd = m.group(1)
                    break
        if not self.lsd:
            self.lsd = "9zei3OjvTBQ-9YG6E0OMzm"

    def graphql(self, friendly: str, doc_id: str, variables: dict, referer: str = "", *, comment=False) -> dict:
        form = {"av": self.uid if comment else "178414" + self.uid, "__d": "www", "__user": "0",
                "__a": "1", "__req": "10" if comment else "1j", "__hs": "20519.HYP:instagram_web_pkg.2.1...0",
                "dpr": "1", "__ccg": "EXCELLENT", "__hsi": str(int(time.time() * 1000)), "__comet_req": "7",
                "jazoest": "26312" if comment else "26738", "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": friendly, "variables": compact(variables),
                "server_timestamps": "true", "doc_id": doc_id}
        if self.dtsg:
            form["fb_dtsg"] = self.dtsg
        if self.lsd:
            form["lsd"] = self.lsd
        headers = {"X-FB-Friendly-Name": friendly}
        if "Follow" in friendly:
            headers["X-Root-Field-Name"] = "xdt_create_friendship"
        if self.lsd:
            headers["X-FB-LSD"] = self.lsd
        if self.dtsg:
            headers["X-FB-DTSG"] = self.dtsg
        response = self.read_response("POST", "/graphql/query", referer=referer, extra_headers=headers, data=form)
        if response.status_code in (404, 405):
            raise SkipJob("IG không hỗ trợ endpoint thao tác này; cần cập nhật source.")
        root = self.decode(response)
        if response.status_code != 200:
            raise StopRun("IG từ chối thao tác; dừng kiểm tra, không thử POST khác.")
        return root

    def target_user(self, job: Job) -> str:
        link = ig_url(job.link or (job.object_id if job.object_id.startswith("https://") else ""))
        if not link and not job.object_id.isdigit() and re.fullmatch(r"@?[A-Za-z0-9_.]{1,30}", job.object_id):
            link = IG_ORIGIN + "/" + job.object_id.lstrip("@") + "/"
        if link:
            parts = urlsplit(link).path.strip("/").split("/")
            if len(parts) != 1 or not re.fullmatch(r"[A-Za-z0-9_.]{1,30}", parts[0]) or parts[0] in ("p", "reel", "tv", "accounts"):
                raise SkipJob("Job follow không có link profile hợp lệ.")
            username = parts[0]
            
            try:
                response = self.read_response("GET", "/api/v1/users/web_profile_info/?" + urlencode({"username": username}))
                if response.status_code == 200:
                    root = self.decode(response)
                    user = obj_data(root).get("user")
                    uid = first(user, "id", "pk") if isinstance(user, dict) else ""
                    if uid.isdigit():
                        if job.object_id.isdigit() and job.object_id != uid:
                            raise SkipJob("UID đích và link profile không khớp.")
                        return uid
                elif response.status_code == 404:
                    raise SkipJob("Profile đích không tồn tại.")
            except SkipJob:
                raise
            except Exception:
                pass
           
            if job.object_id.isdigit():
                return job.object_id
           
            try:
                headers = {**self.headers(), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
                res = self.session.get(f"{IG_ORIGIN}/{username}/", headers=headers, timeout=TIMEOUT, allow_redirects=True)
                if res.status_code == 200:
                    match = re.search(r'"(?:profile_id|user_id|id|pk)"\s*:\s*"?(\d+)"?', res.text)
                    if match and match.group(1).isdigit():
                        return match.group(1)
            except Exception:
                pass
            raise SkipJob(f"Không lấy được UID của @{username}.")
        if job.object_id.isdigit():
            return job.object_id
        raise SkipJob("Job follow thiếu UID/link profile.")

    @staticmethod
    def media_id(job: Job) -> str:
        link = ig_url(job.link)  
        value = job.object_id.split("_")[0]
        if re.fullmatch(r"\d{8,}", value):
            return value
        if not link and job.object_id.startswith("https://"):
            link = ig_url(job.object_id)
        elif not link and re.fullmatch(r"[A-Za-z0-9_-]{5,20}", job.object_id):
            link = IG_ORIGIN + "/p/" + job.object_id + "/"
        match = re.search(r"^/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?", urlsplit(link).path)
        if not match:
            raise SkipJob("Job thiếu ID/link bài viết Instagram hợp lệ.")
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        number = 0
        for char in match[1]:
            number = number * 64 + alphabet.index(char)
        if not number:
            raise SkipJob("Shortcode bài viết không hợp lệ.")
        return str(number)

    def perform(self, job: Job):
        if job.kind == "unsupported":
            raise SkipJob("Loại job chưa hỗ trợ trong bản IG.")
        if job.kind == "follow":
            uid = self.target_user(job)
            if uid == self.uid:
                raise SkipJob("Không follow chính tài khoản đang đăng nhập.")
            root = self.graphql("usePolarisFollowMutation", "9740159112729312", {
                "target_user_id": uid, "container_module": "profile",
                "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start,PolarisProfilePostsTabRoot:profilePage:3:unexpected",
            }, job.link)
            node = obj_data(root).get("xdt_create_friendship")
            if not isinstance(node, dict):
                
                try:
                    fb_root = self.graphql("usePolarisFollowMutation", "9663809173698092", {
                        "target_user_id": uid, "container_module": "profile",
                        "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start,PolarisProfilePostsTabRoot:profilePage:3:unexpected",
                    }, job.link)
                    fb_node = obj_data(fb_root).get("xdt_create_friendship")
                    if isinstance(fb_node, dict):
                        root, node = fb_root, fb_node
                except Exception:
                    pass
            status = node.get("friendship_status", {}) if isinstance(node, dict) else {}
            ok = (isinstance(status, dict) and (status.get("following") is True or status.get("outgoing_request") is True)) or (
                isinstance(node, dict) and bool(first(node, "id"))) or root.get("status") == "ok"
            if not ok:
                errors = root.get("errors") if isinstance(root, dict) else []
                err_text = ""
                if isinstance(errors, list) and errors and isinstance(errors[0], dict):
                    err_text = (first(errors[0], "message", "description", "summary") or "").lower()
                if "already" in err_text or "following" in err_text:
                    ok = True
                elif any(k in err_text for k in ("action_blocked", "feedback_required", "sentry_block", "please wait", "spam")):
                    raise StopRun("Tài khoản IG bị giới hạn tính năng Follow tạm thời (Action Block). Dừng tài khoản.")
                else:
                    raise SkipJob(f"IG không nhận follow hoặc bị nhả follow ({err_text or 'nick đích hạn chế'}); bỏ qua job.")
        elif job.kind == "like_comment":
            cid = job.comment_id or job.object_id
            if not job.comment_id and re.fullmatch(r"\d+_\d+", cid):
                cid = cid.split("_")[-1]
            if not cid.isdigit():
                raise SkipJob("Job thiếu comment ID.")
            root = self.graphql("usePolarisLikeCommentLikeMutation", "7358156687612196",
                                {"comment_id": cid, "container_module": "self_comments_v2"}, job.link)
            node = obj_data(root).get("xdt_like_comment")
            ok = isinstance(node, dict) and bool(first(node, "id"))
        elif job.kind == "comment":
            if not job.text.strip():
                raise SkipJob("Job không có nội dung bình luận; không tự bịa comment.")
            media = self.media_id(job)
            connection = ('client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection'
                          '(data:{},media_id:"' + media + '",sort_order:"popular")')
            root = self.graphql("PolarisPostCommentInputRevampedMutation", "27261905640092552",
                                {"connections": [connection], "data": {"comment_text": job.text, "media_id": media}},
                                job.link, comment=True)
            node = obj_data(root).get("xdt_create_comment")
            ok = isinstance(node, dict) and bool(first(node, "id"))
        else:
            media = self.media_id(job)
            if self.dtsg:
                root = self.graphql("usePolarisLikeMediaLikeMutation", "9595477160535898",
                                    {"media_id": media, "container_module": "feed_timeline"}, job.link)
                data = obj_data(root)
                node = data.get("xdt_like_media", {})
                alternate = data.get("xig_media_like", {})
                media_node = alternate.get("media", {}) if isinstance(alternate, dict) else {}
                ok = (isinstance(node, dict) and node.get("viewer_has_liked") is True) or (
                    isinstance(media_node, dict) and media_node.get("has_liked") is True)
            else:
                response = self.read_response("POST", f"/web/likes/{media}/like/", referer=job.link, data={})
                
                if response.status_code in (404, 405):
                    response = self.read_response("POST", f"/api/v1/web/likes/{media}/like/", referer=job.link, data={})
                root = self.decode(response)
                ok = response.status_code == 200 and root.get("status") == "ok"
        if not ok:
            raise StopRun("IG chưa xác nhận thao tác thành công; dừng, không báo hoàn thành hoặc làm lại.")


@dataclass
class Progress:
    completed: int = 0
    errors: int = 0
    empty: int = 0
    earned: Decimal = field(default_factory=lambda: Decimal(0))


def parse_delay(val: str, default: tuple[int, int]) -> tuple[int, int]:
    val = val.strip()
    if not val:
        return default
    if "-" in val:
        parts = [p.strip() for p in val.split("-", 1)]
        if parts[0].isdigit() and parts[1].isdigit():
            a, b = int(parts[0]), int(parts[1])
            return (min(a, b), max(a, b))
    elif val.isdigit():
        v = int(val)
        return (v, v)
    return default


def random_wait(interval: tuple[int, int], label: str = ""):
    low = min(interval[0], interval[1])
    high = max(interval[0], interval[1])
    diff = high - low
    sec = low + (secrets.randbelow(diff + 1) if diff > 0 else 0)
    if sec <= 0:
        return
    for remaining in range(sec, 0, -1):
        if label:
            print(f"\r  ⏳ {label}: còn {remaining}s... ", end="", flush=True)
        else:
            print(f"\r  ⏳ Đang chờ: còn {remaining}s... ", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 45 + "\r", end="", flush=True)


def run_jobs(golike: GoLike, instagram: Instagram, maximum: int, max_errors: int = MAX_ERRORS,
             receive_delay: tuple[int, int] = RECEIVE_DELAY,
             complete_delay: tuple[int, int] = COMPLETE_DELAY, *, progress=None):
    progress = progress if progress is not None else Progress()
    if maximum < 1:
        raise StopRun("Giới hạn thành công phải lớn hơn 0.")
    if max_errors < 1:
        raise StopRun("Giới hạn lỗi phải lớn hơn 0.")
    golike.verify()
    if hasattr(instagram, "sync_tokens"):
        try:
            instagram.sync_tokens()
        except Exception:
            pass
    try:
        account_id = golike.linked_account(instagram.username, instagram.uid)
    except StopRun as exc:
        if "chưa liên kết" in str(exc).lower():
            account_id = golike.auto_link(instagram)
        else:
            raise
    if not instagram.username and getattr(golike, "last_matched_username", ""):
        instagram.username = golike.last_matched_username
    target_name = f"@{instagram.username}" if instagram.username else f"UID {instagram.uid}"
    rcv_str = f"{receive_delay[0]}-{receive_delay[1]}s" if receive_delay[0] != receive_delay[1] else f"{receive_delay[0]}s"
    cpl_str = f"{complete_delay[0]}-{complete_delay[1]}s" if complete_delay[0] != complete_delay[1] else f"{complete_delay[0]}s"
    print(f"Chạy {target_name}. Mục tiêu: {maximum} job | Dừng nếu lỗi liên tiếp: {max_errors} | Delay nhận: {rcv_str} | Delay hoàn thành: {cpl_str}")
    while progress.completed < maximum and progress.errors < max_errors and progress.empty < MAX_EMPTY:
        print(f"\n[1/3] Đang chờ {rcv_str} để lấy job từ GoLike...", flush=True)
        random_wait(receive_delay, "Chờ nhận job")
        job = golike.get_job(account_id)
        if job is None:
            progress.empty += 1
            print(f"[-] Chưa có job mới ({progress.empty}/{MAX_EMPTY}). Hệ thống sẽ tự tìm lại...", flush=True)
            continue
        progress.empty = 0
        handled_key = f"{account_id}:{job.job_id}"
        if handled_key in golike.handled:
            raise StopRun("GoLike cấp lại job đã xử lý trong phiên; dừng để tránh thao tác trùng.")
        golike.handled.add(handled_key)
        print(f"[2/3] Nhận job {job.job_id} (loại: {job.kind.upper()}) | Đang thực hiện trên IG...", flush=True)
        try:
            instagram.perform(job)
        except SkipJob as exc:
            golike.skip(job, account_id) 
            progress.errors += 1
            print(f"[!] Bỏ qua job: {exc} | Số lỗi liên tiếp {progress.errors}/{max_errors}", flush=True)
            continue
        except StopRun as exc:
            if "chưa xác nhận thao tác thành công" in str(exc) or "bị nhả" in str(exc):
                try:
                    golike.skip(job, account_id)
                except StopRun:
                    raise
                except Exception:
                    pass
                progress.errors += 1
                print(f"[!] Thao tác thất bại / bỏ qua job: {exc} | Số lỗi liên tiếp {progress.errors}/{max_errors}", flush=True)
                continue
            raise
        print(f"[3/3] Đã thao tác IG xong, đang chờ {cpl_str} xác nhận hoàn thành với GoLike...", flush=True)
        random_wait(complete_delay, "Chờ hoàn thành")
        try:
            reward = golike.complete(job, account_id)
        except SkipJob as exc:
            try:
                golike.skip(job, account_id)
            except Exception:
                pass
            progress.errors += 1
            print(f"[!] Bỏ qua job: {exc} | Số lỗi liên tiếp {progress.errors}/{max_errors}", flush=True)
            continue
        progress.completed += 1
        progress.errors = 0  # Đã hoàn thành job 
        progress.earned += reward
        print(f"[+] THÀNH CÔNG! Job {job.job_id} | +{reward:,.0f}đ | Đã làm: {progress.completed}/{maximum} (Tổng kiếm: {progress.earned:,.0f}đ)", flush=True)
    if progress.completed >= maximum:
        print(f"\n[✓] Đã hoàn thành đủ mục tiêu {maximum} job!", flush=True)
    elif progress.errors >= max_errors:
        print(f"\n[!] Dừng phiên: Đã chạm giới hạn {max_errors} lỗi liên tiếp.", flush=True)
    elif progress.empty >= MAX_EMPTY:
        print(f"\n[-] Dừng phiên: Hệ thống GoLike tạm thời hết job.", flush=True)
    return progress


def run_multi_accounts(golike: GoLike, accounts: list[Instagram], maximum_per_acc: int,
                       max_errors: int = MAX_ERRORS,
                       receive_delay: tuple[int, int] = RECEIVE_DELAY,
                       complete_delay: tuple[int, int] = COMPLETE_DELAY,
                       rounds: int = 1, *, progress: Progress | None = None) -> Progress:
    total_progress = progress if progress is not None else Progress()
    if not accounts:
        raise StopRun("Danh sách tài khoản Instagram trống.")
    if maximum_per_acc < 1:
        raise StopRun("Giới hạn thành công mỗi nick phải lớn hơn 0.")
    if max_errors < 1:
        raise StopRun("Giới hạn lỗi mỗi nick phải lớn hơn 0.")

    golike.verify()
    total_acc = len(accounts)
    round_idx = 0
    is_infinite = (rounds == 0)

    print(f"\n=======================================================")
    print(f"BẮT ĐẦU CHẠY {total_acc} TÀI KHOẢN INSTAGRAM")
    print(f"Mục tiêu: {maximum_per_acc} job/nick | Lỗi chuyển nick: {max_errors} | Số vòng: {'Vô hạn' if is_infinite else rounds}")
    print(f"=======================================================\n", flush=True)

    while is_infinite or round_idx < rounds:
        round_idx += 1
        if is_infinite or rounds > 1:
            print(f"\n>>>>>>>>>> VÒNG {round_idx} / {'VÔ HẠN' if is_infinite else rounds} <<<<<<<<<<", flush=True)

        for idx, acc in enumerate(accounts, 1):
            name = f"@{acc.username}" if getattr(acc, "username", "") else f"UID {getattr(acc, 'uid', '')}"
            print(f"\n{'='*20} [{idx}/{total_acc}] Chạy nick {name} {'='*20}", flush=True)
            acc_progress = Progress()
            stop_reason = ""
            try:
                run_jobs(golike, acc, maximum_per_acc, max_errors,
                         receive_delay=receive_delay, complete_delay=complete_delay,
                         progress=acc_progress)
            except StopRun as exc:
                stop_reason = str(exc)
                print(f"[!] Nick {name} dừng ({stop_reason}). Bỏ qua chuyển sang nick tiếp theo...", flush=True)
            finally:
                total_progress.completed += acc_progress.completed
                total_progress.earned += acc_progress.earned
                total_progress.errors += acc_progress.errors

            if not stop_reason:
                if acc_progress.completed >= maximum_per_acc:
                    print(f"[✓] Nick {name} đã hoàn thành đủ chỉ tiêu ({acc_progress.completed}/{maximum_per_acc} job).", flush=True)
                elif acc_progress.errors >= max_errors:
                    print(f"[!] Nick {name} đạt giới hạn lỗi ({acc_progress.errors}/{max_errors}).", flush=True)
                elif acc_progress.empty >= MAX_EMPTY:
                    print(f"[-] Nick {name} tạm hết job trên GoLike.", flush=True)

            if idx < total_acc:
                print(f"  -> Đang chuyển sang nick tiếp theo...", flush=True)
                time.sleep(3)

        if (is_infinite or round_idx < rounds) and total_acc > 1:
            print(f"\n[✓] Đã hoàn thành vòng {round_idx}. Nghỉ 10s trước khi sang vòng tiếp theo...", flush=True)
            time.sleep(10)

    return total_progress


def parse_cookie_input(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("+"):
        raw = raw[1:].strip()
    if raw.endswith(".txt") and Path(raw).is_file():
        try:
            with open(raw, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        except Exception:
            pass
    return [p.strip() for p in re.split(r"[\r\n|]+", raw) if p.strip()]


CONFIG_PATH = Path(__file__).resolve().parent / "golike_config.json"


def load_config() -> dict:
    if CONFIG_PATH.is_file():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(key: str, value: Any):
    try:
        data = load_config()
        data[key] = value
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def credential_input(prompt: str) -> str:
    
    return input(prompt).strip()


def main():
    golike = instagram = solver = None
    instagram_accounts = []
    saved = load_config()
    if saved.get("golike_token"):
        try:
            golike = GoLike(saved["golike_token"])
            try:
                golike.verify()
            except Exception:
                pass
        except Exception:
            golike = None

    saved_ig_list = saved.get("ig_cookies")
    if not isinstance(saved_ig_list, list) or not saved_ig_list:
        if saved.get("ig_cookie"):
            saved_ig_list = [saved["ig_cookie"]]
        else:
            saved_ig_list = []
    for c in saved_ig_list:
        if isinstance(c, str) and c.strip():
            try:
                acc = Instagram(c.strip())
                instagram_accounts.append(acc)
            except Exception:
                pass
    instagram = instagram_accounts[0] if instagram_accounts else None

    if saved.get("solver_key"):
        try:
            solver = SolverCF(saved["solver_key"])
        except Exception:
            solver = None
    if golike is not None and solver is not None:
        golike.solver = solver

    print("GoLike Instagram — Tự động ghi nhớ Token / Cookie để không phải nhập lại mỗi lần mở.")
    if golike or instagram_accounts or solver:
        print("Đã tải cấu hình lưu sẵn:")
        if golike:
            if isinstance(getattr(golike, "username", None), str) and golike.username and hasattr(golike, "format_info"):
                print(f"  • GoLike: {golike.format_info()}")
            else:
                print("  • Token GoLike: [Đã có sẵn]")
        if instagram_accounts:
            if len(instagram_accounts) == 1:
                print(f"  • Cookie IG: [UID: {instagram_accounts[0].uid}]")
            else:
                names = [f"UID {a.uid}" for a in instagram_accounts[:3]]
                more = f"... (+{len(instagram_accounts)-3})" if len(instagram_accounts) > 3 else ""
                print(f"  • Cookie IG: [{len(instagram_accounts)} tài khoản: {', '.join(names)}{more}]")
        if solver:
            print("  • SolverCF: [Đã có sẵn]")
        rcv_s = saved.get("receive_delay", f"{RECEIVE_DELAY[0]}-{RECEIVE_DELAY[1]}")
        cpl_s = saved.get("complete_delay", f"{COMPLETE_DELAY[0]}-{COMPLETE_DELAY[1]}")
        print(f"  • Cấu hình delay: Chờ nhận [{rcv_s}s] | Chờ hoàn thành [{cpl_s}s]")
    try:
        while True:
            if golike and isinstance(getattr(golike, "username", None), str) and golike.username:
                coin_val = amount(getattr(golike, "coin", 0))
                label_gl = f" [@{golike.username} | {coin_val:,.0f}đ]"
            elif golike:
                label_gl = " [Đã lưu]"
            else:
                label_gl = ""
            if len(instagram_accounts) > 1:
                label_ig = f" [{len(instagram_accounts)} nick]"
            elif len(instagram_accounts) == 1:
                label_ig = f" [UID: {instagram_accounts[0].uid}]"
            else:
                label_ig = ""
            label_cf = " [Đã lưu]" if solver else ""
            print(f"\n1. Nhập token GoLike{label_gl}\n2. Nhập cookie IG{label_ig}\n3. Chạy job\n4. Nhập API key SolverCF{label_cf}\n0. Thoát")
            try:
                choice = input("Chọn: ").strip()
                if choice == "0":
                    break
                if choice == "1":
                    raw_token = credential_input("Token GoLike: ")
                    candidate = GoLike(raw_token)
                    try:
                        candidate.verify()
                    except BaseException:
                        candidate.close()
                        raise
                    if golike is not None:
                        golike.close()
                    golike = candidate
                    golike.solver = solver
                    save_config("golike_token", raw_token)
                    info_str = f": {golike.format_info()}" if (hasattr(golike, "format_info") and isinstance(getattr(golike, "username", None), str) and golike.username) else ""
                    print(f"Đã xác minh tài khoản GoLike{info_str} (đã lưu tự động).")
                elif choice == "2":
                    if instagram_accounts:
                        print(f"\nHiện có {len(instagram_accounts)} nick IG đã lưu:")
                        for i, a in enumerate(instagram_accounts, 1):
                            uname = f"@{a.username}" if getattr(a, "username", "") else f"UID {getattr(a, 'uid', '')}"
                            print(f"  {i}. {uname}")
                        print("  • Nhập cookie mới để thêm/cập nhật vào danh sách.")
                        print("  • Gõ 'clear' để xóa danh sách làm lại từ đầu.")

                    while True:
                        raw_cookie = credential_input("Cookie IG: ")
                        if not raw_cookie:
                            if instagram_accounts:
                                break
                            raise StopRun("Cookie không được để trống.")
                        if raw_cookie.lower() in ("clear", "xoa", "reset"):
                            for a in instagram_accounts:
                                if hasattr(a, "close"):
                                    a.close()
                            instagram_accounts.clear()
                            instagram = None
                            save_config("ig_cookies", [])
                            save_config("ig_cookie", "")
                            print("Đã xóa toàn bộ cookie IG đã lưu.")
                            more = input("Nhập cookie mới ngay bây giờ? (y/n) [y]: ").strip().lower()
                            if more in ("n", "no"):
                                break
                            continue
                        if raw_cookie.lower() in ("list", "xem"):
                            if instagram_accounts:
                                for i, a in enumerate(instagram_accounts, 1):
                                    uname = f"@{a.username}" if getattr(a, "username", "") else f"UID {getattr(a, 'uid', '')}"
                                    print(f"  {i}. {uname}")
                            else:
                                print("Chưa có nick nào.")
                            break

                        cookie_list = parse_cookie_input(raw_cookie)
                        if not cookie_list:
                            raise StopRun("Không tìm thấy cookie hợp lệ.")

                        for ck in cookie_list:
                            try:
                                cand = Instagram(ck)
                                existing_idx = next((i for i, a in enumerate(instagram_accounts) if getattr(a, "uid", None) == cand.uid), None)
                                if existing_idx is not None:
                                    if hasattr(instagram_accounts[existing_idx], "close"):
                                        instagram_accounts[existing_idx].close()
                                    instagram_accounts[existing_idx] = cand
                                    print(f"[✓] Đã cập nhật nick UID {cand.uid} (Hiện có: {len(instagram_accounts)} nick).")
                                else:
                                    instagram_accounts.append(cand)
                                    print(f"[✓] Đã thêm nick UID {cand.uid} (Hiện có: {len(instagram_accounts)} nick).")
                            except Exception as e:
                                print(f"[!] Bỏ qua cookie lỗi: {e}")

                        if not instagram_accounts:
                            raise StopRun("Không nạp được tài khoản IG nào.")

                        instagram = instagram_accounts[0]
                        raw_list = [getattr(a, "raw_cookie", "") for a in instagram_accounts if getattr(a, "raw_cookie", "")]
                        save_config("ig_cookies", raw_list)
                        save_config("ig_cookie", raw_list[0] if raw_list else "")

                        more = input("Bạn có muốn nhập thêm nick khác không? (y/n) [n]: ").strip().lower()
                        if more not in ("y", "yes"):
                            print(f"Đã lưu thành công {len(instagram_accounts)} tài khoản IG. Trở về menu chính.")
                            break
                elif choice == "3":
                    if golike is None or not instagram_accounts:
                        raise StopRun("Nhập token GoLike và cookie IG ở mục 1, 2 trước.")
                    try:
                        if hasattr(golike, "verify"):
                            golike.verify()
                    except Exception:
                        pass
                    if isinstance(getattr(golike, "username", None), str) and golike.username and hasattr(golike, "format_balance"):
                        print(f"Tài khoản GoLike: @{golike.username} | {golike.format_balance()}")
                    saved = load_config()

                    if len(instagram_accounts) > 1:
                        def_count = str(saved.get("max_jobs") or "20")
                        count = input(f"Giới hạn job mỗi nick [{def_count}]: ").strip() or def_count
                    else:
                        def_count = str(saved.get("max_jobs") or "100")
                        count = input(f"Giới hạn job thành công [{def_count}]: ").strip() or def_count
                    if not count.isdigit() or not 1 <= int(count) <= 100000:
                        raise StopRun("Nhập giới hạn từ 1 tới 100000.")
                    save_config("max_jobs", int(count))

                    def_err = str(saved.get("max_errors") or MAX_ERRORS)
                    max_err = input(f"Số lỗi liên tiếp để dừng [{def_err}]: ").strip() or def_err
                    if not max_err.isdigit() or not 1 <= int(max_err) <= 1000:
                        raise StopRun("Nhập số lỗi từ 1 tới 1000.")
                    save_config("max_errors", int(max_err))

                    def_rcv = str(saved.get("receive_delay") or f"{RECEIVE_DELAY[0]}-{RECEIVE_DELAY[1]}")
                    raw_rcv = input(f"Thời gian chờ nhận job (giây, vd: 15-20 hoặc 15) [{def_rcv}]: ").strip() or def_rcv
                    rcv_delay = parse_delay(raw_rcv, RECEIVE_DELAY)
                    save_config("receive_delay", raw_rcv)

                    def_cpl = str(saved.get("complete_delay") or f"{COMPLETE_DELAY[0]}-{COMPLETE_DELAY[1]}")
                    raw_cpl = input(f"Thời gian chờ hoàn thành (giây, vd: 10-15 hoặc 10) [{def_cpl}]: ").strip() or def_cpl
                    cpl_delay = parse_delay(raw_cpl, COMPLETE_DELAY)
                    save_config("complete_delay", raw_cpl)

                    progress = Progress()
                    try:
                        if len(instagram_accounts) == 1:
                            run_jobs(golike, instagram_accounts[0], int(count), int(max_err),
                                     receive_delay=rcv_delay, complete_delay=cpl_delay, progress=progress)
                        else:
                            def_rounds = str(saved.get("rounds") or "1")
                            raw_rounds = input(f"Số vòng lặp danh sách nick (vd: 1, 2... hoặc 0 để lặp vô hạn) [{def_rounds}]: ").strip() or def_rounds
                            rounds = int(raw_rounds) if raw_rounds.isdigit() else 1
                            save_config("rounds", raw_rounds)
                            run_multi_accounts(golike, instagram_accounts, int(count), int(max_err),
                                               receive_delay=rcv_delay, complete_delay=cpl_delay,
                                               rounds=rounds, progress=progress)
                    finally:
                        try:
                            if hasattr(golike, "verify"):
                                golike.verify()
                            bal_str = f" | {golike.format_balance()}" if hasattr(golike, "format_balance") else ""
                        except Exception:
                            bal_str = ""
                        acc_note = f" ({len(instagram_accounts)} nick)" if len(instagram_accounts) > 1 else ""
                        max_target = count if len(instagram_accounts) == 1 else f"{int(count) * len(instagram_accounts)}"
                        print(f"Kết quả phiên{acc_note}: hoàn thành {progress.completed}/{max_target}, lỗi {progress.errors}/{max_err}, "
                              f"hết job {progress.empty}/{MAX_EMPTY}, thu nhập xác nhận {progress.earned:,.0f}đ{bal_str}.")
                elif choice.lower() in ("info", "sodu", "vi", "balance"):
                    if golike is None:
                        print("Chưa có token GoLike. Nhập ở mục 1 trước.")
                    else:
                        try:
                            if hasattr(golike, "verify"):
                                golike.verify()
                        except Exception as e:
                            print(f"[!] Không thể làm mới từ server: {e}")
                        u_str = getattr(golike, "username", "")
                        n_str = getattr(golike, "name", "")
                        uid_str = getattr(golike, "user_id", "")
                        coin_str = f"{amount(getattr(golike, 'coin', 0)):,.0f}đ"
                        temp_str = f"{amount(getattr(golike, 'temp_coin', 0)):,.0f}đ"
                        print("\n" + "=" * 45)
                        print("          THÔNG TIN TÀI KHOẢN GOLIKE")
                        print("=" * 45)
                        print(f"  • Tên đăng nhập : @{u_str}")
                        if n_str:
                            print(f"  • Họ và tên    : {n_str}")
                        print(f"  • ID người dùng : {uid_str}")
                        print(f"  • Số dư ví     : {coin_str}")
                        print(f"  • Tiền chờ duyệt: {temp_str}")
                        print("=" * 45 + "\n")
                elif choice.lower() in ("nicks", "accounts", "danhsach"):
                    if not instagram_accounts:
                        print("Chưa có tài khoản Instagram nào được lưu.")
                    else:
                        print(f"\nDanh sách {len(instagram_accounts)} tài khoản Instagram đã lưu:")
                        for i, a in enumerate(instagram_accounts, 1):
                            uname = f"@{a.username}" if getattr(a, "username", "") else f"UID {getattr(a, 'uid', '')}"
                            print(f"  {i}. {uname}")
                elif choice == "4":
                    key = credential_input("API key SolverCF (trống để tắt): ")
                    candidate = SolverCF(key) if key else None
                    if candidate is not None:
                        try:
                            balance = candidate.balance()
                        except BaseException:
                            candidate.close()
                            raise
                        print(f"Đã xác minh SolverCF, số dư: {balance}. Turnstile có thể tốn phí.")
                    if solver is not None:
                        solver.close()
                    solver = candidate
                    if golike is not None:
                        golike.solver = solver
                    save_config("solver_key", key)
                    if solver is None:
                        print("Đã tắt SolverCF; captcha kéo vẫn hoạt động.")
                else:
                    print("Chọn 1, 2, 3, 4 hoặc 0.")
            except StopRun as exc:
                print(f"Đã dừng: {exc}")
            except KeyboardInterrupt:
                print("\nĐã dừng. Job đang dở không tự làm lại. Trở về menu.")
            except EOFError:
                break
    finally:
        if golike is not None:
            golike.close()
        if solver is not None:
            solver.close()
        for client in instagram_accounts:
            if client is not None and hasattr(client, "close"):
                client.close()
        if instagram is not None and instagram not in instagram_accounts:
            if hasattr(instagram, "close"):
                instagram.close()
    print("Đã thoát.")


if __name__ == "__main__":
    main()
