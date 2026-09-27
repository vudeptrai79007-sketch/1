#!/usr/bin/env python3
# Gmail Reader - IMAP
# Chỉ dùng với tài khoản Gmail mà bạn sở hữu/có quyền truy cập.

import email
import getpass
import imaplib
import os
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime

HOST = "imap.gmail.com"
PORT = 993
ATTACH_DIR = "gmail_attachments"


def decode_mime(value):
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def clean_filename(name):
    name = decode_mime(name)
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return name.strip() or "attachment"


def get_text(msg):
    """Lấy text/plain hoặc text/html (nếu chỉ có HTML)."""
    plain = []
    html = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if ctype == "text/plain":
                plain.append(text)
            elif ctype == "text/html":
                html.append(text)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/plain":
                plain.append(text)
            else:
                html.append(text)

    if plain:
        return "\n".join(plain).strip()

    if html:
        # Chuyển HTML cơ bản thành text dễ đọc
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", "\n".join(html))
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</p\s*>", "\n\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    return "(Không có nội dung text đọc được.)"


def list_attachments(msg):
    items = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                name = part.get_filename()
                if name:
                    items.append((part, clean_filename(name)))
    return items


def show_message(msg, uid=None):
    subject = decode_mime(msg.get("Subject", "(Không có tiêu đề)"))
    sender = decode_mime(msg.get("From", "(Không rõ người gửi)"))
    to = decode_mime(msg.get("To", ""))
    date = msg.get("Date", "")

    print("\n" + "=" * 72)
    if uid is not None:
        print(f"UID: {uid}")
    print(f"From: {sender}")
    print(f"To:   {to}")
    print(f"Date: {date}")
    print(f"Subject: {subject}")
    print("-" * 72)
    print(get_text(msg))

    attachments = list_attachments(msg)
    if attachments:
        print("\n[File đính kèm]")
        for i, (_, name) in enumerate(attachments, 1):
            print(f"  {i}. {name}")
    print("=" * 72)


def fetch_message(mail, uid):
    status, data = mail.uid("fetch", uid, "(RFC822)")
    if status != "OK" or not data:
        return None

    raw = None
    for item in data:
        if isinstance(item, tuple):
            raw = item[1]
            break

    return email.message_from_bytes(raw) if raw else None


def get_uids(mail, criteria="ALL"):
    status, data = mail.uid("search", None, criteria)
    if status != "OK":
        return []
    return data[0].split()


def select_inbox(mail):
    status, _ = mail.select("INBOX", readonly=True)
    return status == "OK"


def read_latest(mail):
    uids = get_uids(mail)
    if not uids:
        print("Inbox không có mail.")
        return

    uid = uids[-1]
    msg = fetch_message(mail, uid)
    if msg:
        show_message(msg, uid.decode())


def read_all(mail):
    uids = get_uids(mail)
    if not uids:
        print("Inbox không có mail.")
        return

    print(f"Tìm thấy {len(uids)} mail. Đang đọc...\n")
    for uid in reversed(uids):
        msg = fetch_message(mail, uid)
        if msg:
            show_message(msg, uid.decode())


def search_mail(mail):
    print("\nTìm kiếm:")
    print("1. Theo người gửi")
    print("2. Theo tiêu đề")
    print("3. Theo nội dung")
    choice = input("Chọn: ").strip()

    keyword = input("Nhập từ khóa: ").strip()
    if not keyword:
        return

    # IMAP SEARCH hỗ trợ FROM/SUBJECT/TEXT.
    if choice == "1":
        criteria = f'FROM "{keyword}"'
    elif choice == "2":
        criteria = f'SUBJECT "{keyword}"'
    elif choice == "3":
        criteria = f'TEXT "{keyword}"'
    else:
        print("Lựa chọn không hợp lệ.")
        return

    uids = get_uids(mail, criteria)
    print(f"\nTìm thấy {len(uids)} mail.")

    for uid in reversed(uids):
        msg = fetch_message(mail, uid)
        if msg:
            show_message(msg, uid.decode())


def download_attachments(mail):
    uids = get_uids(mail)
    if not uids:
        print("Inbox không có mail.")
        return

    os.makedirs(ATTACH_DIR, exist_ok=True)

    # Hiển thị tối đa 30 mail gần nhất để chọn.
    recent = list(reversed(uids[-30:]))
    print("\nMail gần nhất:")
    for i, uid in enumerate(recent, 1):
        msg = fetch_message(mail, uid)
        if not msg:
            continue
        subject = decode_mime(msg.get("Subject", "(Không có tiêu đề)"))
        sender = decode_mime(msg.get("From", ""))
        print(f"[{i}] {subject} | {sender}")

    try:
        n = int(input("Chọn mail: ").strip())
        uid = recent[n - 1]
    except (ValueError, IndexError):
        print("Lựa chọn không hợp lệ.")
        return

    msg = fetch_message(mail, uid)
    if not msg:
        print("Không đọc được mail.")
        return

    attachments = list_attachments(msg)
    if not attachments:
        print("Mail này không có file đính kèm.")
        return

    print("\nFile đính kèm:")
    for i, (_, name) in enumerate(attachments, 1):
        print(f"[{i}] {name}")

    choice = input("Nhập số file (hoặc A để tải tất cả): ").strip().lower()

    selected = attachments if choice == "a" else []
    if choice != "a":
        try:
            selected = [attachments[int(choice) - 1]]
        except (ValueError, IndexError):
            print("Lựa chọn không hợp lệ.")
            return

    for part, name in selected:
        path = os.path.join(ATTACH_DIR, name)

        # Tránh ghi đè file trùng tên
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = f"{base}_{counter}{ext}"
            counter += 1

        payload = part.get_payload(decode=True)
        if payload is None:
            print(f"Không tải được: {name}")
            continue

        with open(path, "wb") as f:
            f.write(payload)

        print(f"Đã lưu: {path}")



CONFIG_FILE = ".gmail_reader_config"


def generate_dot_variants(gmail):
    """Tạo các biến thể dấu chấm của Gmail và lưu vào <gmail>.txt."""
    local, sep, domain = gmail.rpartition("@")
    if not sep or domain.lower() != "gmail.com":
        print("Chỉ hỗ trợ địa chỉ @gmail.com.")
        return

    if "." in local:
        print("Hãy nhập Gmail gốc không có dấu chấm.")
        return

    # Gmail bỏ qua dấu chấm trong phần local-part.
    variants = []
    if local:
        for mask in range(1 << max(0, len(local) - 1)):
            value = local[0]
            for i in range(1, len(local)):
                if mask & (1 << (i - 1)):
                    value += "."
                value += local[i]
            variants.append(value + "@" + domain)

    filename = gmail + ".txt"
    existing = set()

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing = {line.strip() for line in f if line.strip()}
        except OSError:
            pass

    added = [x for x in variants if x not in existing]
    if added:
        with open(filename, "a", encoding="utf-8") as f:
            for x in added:
                f.write(x + "\n")

    print(f"Đã lưu biến thể vào: {filename}")
    print(f"Tổng biến thể: {len(variants)} | Thêm mới: {len(added)}")


def save_login(gmail, app_password):
    """Lưu thông tin đăng nhập cục bộ để lần sau không phải nhập lại."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(gmail + "\n")
        f.write(app_password + "\n")


def load_login():
    """Đọc thông tin đăng nhập đã lưu."""
    if not os.path.exists(CONFIG_FILE):
        return None, None

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        if len(lines) >= 2 and lines[0].strip() and lines[1].strip():
            return lines[0].strip(), lines[1].strip()
    except OSError:
        pass

    return None, None


def login_flow():
    """Hỏi dùng tài khoản cũ hay nhập tài khoản mới."""
    old_gmail, old_password = load_login()

    if old_gmail and old_password:
        print(f"\nĐã có tài khoản lưu: {old_gmail}")
        choice = input("Có muốn kiểm tra mail bằng tài khoản này không? [Y/N]: ").strip().lower()

        if choice in ("y", "yes"):
            return old_gmail, old_password

    gmail = input("\nNhập Gmail mới: ").strip()
    app_password = getpass.getpass("Nhập App Password mới: ").replace(" ", "")

    if not gmail or not app_password:
        print("Thiếu Gmail hoặc App Password.")
        return None, None

    # Tự động tạo biến thể ngay sau khi nhập đủ Gmail + App Password.
    generate_dot_variants(gmail)

    # Lưu để những lần sau có thể dùng lại.
    save_login(gmail, app_password)
    print("Đã lưu tài khoản cho lần sử dụng sau.")

    return gmail, app_password


def main():
    print("=" * 72)
    print("                    GMAIL READER")
    print("=" * 72)
    print("Dùng Gmail + App Password, không dùng mật khẩu Gmail chính.\n")

    gmail, app_password = login_flow()

    if not gmail or not app_password:
        return

    mail = imaplib.IMAP4_SSL(HOST, PORT)

    try:
        print("\nĐang đăng nhập...")
        mail.login(gmail, app_password)

        if not select_inbox(mail):
            print("Không mở được Inbox.")
            return

        print("Đăng nhập thành công!")

        while True:
            print("\n" + "=" * 40)
            print("[1] Đọc mail mới nhất")
            print("[2] Đọc toàn bộ Inbox")
            print("[3] Tìm mail")
            print("[4] Tải file đính kèm")
            print("[0] Thoát")
            print("=" * 40)

            choice = input("Chọn: ").strip()

            try:
                if choice == "1":
                    read_latest(mail)
                elif choice == "2":
                    read_all(mail)
                elif choice == "3":
                    search_mail(mail)
                elif choice == "4":
                    download_attachments(mail)
                elif choice == "0":
                    break
                else:
                    print("Lựa chọn không hợp lệ.")
            except Exception as e:
                print(f"Lỗi: {e}")

    except imaplib.IMAP4.error as e:
        print("\nĐăng nhập thất bại.")
        print("Kiểm tra Gmail, App Password và IMAP.")
        print(f"Chi tiết: {e}")
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    finally:
        try:
            mail.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
