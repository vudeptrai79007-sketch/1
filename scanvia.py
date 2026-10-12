import os
import time
import threading
import subprocess
import sys
import random
try:
    import uiautomator2 as u2
except ImportError:
    os.system("pip install uiautomator2")
    import uiautomator2 as u2

STOP_EVENT = threading.Event()

class Colors:
    SUCCESS = "\033[38;2;0;255;127m"
    ERROR = "\033[38;2;255;50;50m"
    WARNING = "\033[38;2;255;200;50m"
    INFO = "\033[38;2;100;255;200m"
    TITLE = "\033[38;2;255;215;0m"
    RESET = "\033[0m"
    
    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"

def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Colors.TITLE}======================================================{Colors.RESET}")
    print(f"{Colors.SUCCESS}       TOOL AUTO APP GOLIKE + INSTAGRAM (ADB)         {Colors.RESET}")
    print(f"{Colors.TITLE}======================================================{Colors.RESET}\n")

def select_devices():
    try:
        out = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        devices = [line.split("\t")[0] for line in out.strip().splitlines()[1:] if "\tdevice" in line]
    except Exception:
        devices = []
        
    if not devices:
        print(Colors.color_text("Không tìm thấy thiết bị! Bật giả lập hoặc cắm cáp ĐT.", Colors.ERROR))
        sys.exit()
        
    print(Colors.color_text("Danh sách thiết bị:", Colors.INFO))
    for i, d in enumerate(devices): 
        print(f"{i + 1}. {d}")
    print(f"{len(devices) + 1}. Chạy tất cả")
    
    while True:
        try:
            choice = int(input("Chọn thiết bị: ").strip())
            if 1 <= choice <= len(devices): return [devices[choice-1]]
            elif choice == len(devices) + 1: return devices
        except ValueError:
            pass

class GoLikeAppWorker(threading.Thread):
    def __init__(self, serial, max_jobs):
        super().__init__()
        self.serial = serial
        self.max_jobs = max_jobs
        self.golike_pkg = "net.golike"
        self.ig_pkg = "com.instagram.android"
        
    def run(self):
        try:
            d = u2.connect(self.serial)
            d.implicitly_wait(5.0)
            size = d.window_size()
            print(f"{Colors.color_text(f'[{self.serial}] Đã kết nối thiết bị!', Colors.SUCCESS)}")
            
            jobs_done = 0
            empty_count = 0
            
            # Khởi động sẵn GoLike
            d.app_start(self.golike_pkg)
            time.sleep(3)
            
            while jobs_done < self.max_jobs:
                if STOP_EVENT.is_set(): break
                print(f"\n{Colors.color_text(f'[{self.serial}] --- BẮT ĐẦU JOB {jobs_done + 1} ---', Colors.TITLE)}")
                
                # 1. KIỂM TRA CAPTCHA
                if d(textMatches=r"(?i).*Xác minh Captcha.*|.*Tôi không phải là.*|.*BỎ QUA.*").exists(timeout=2):
                    print(f"{Colors.color_text(f'[{self.serial}] DÍNH CAPTCHA! Tạm dừng 20s để bạn giải tay...', Colors.WARNING)}")
                    time.sleep(20)
                    continue

                # 2. BẤM NHẬN JOB
                btn_nhan_job = d(textMatches=r"(?i).*Nhận Job.*|.*Kiếm tiền ngay.*")
                if btn_nhan_job.exists(timeout=3):
                    btn_nhan_job.click()
                    print(f"{Colors.color_text(f'[{self.serial}] Đã bấm Nhận Job...', Colors.INFO)}")
                    empty_count = 0
                    time.sleep(2)
                else:
                    empty_count += 1
                    print(f"{Colors.color_text(f'[{self.serial}] Chưa thấy nút Nhận Job ({empty_count}/5)...', Colors.WARNING)}")
                    if empty_count >= 5:
                        print(f"{Colors.color_text(f'[{self.serial}] Hết Job hoặc kẹt màn hình. Đợi 30s...', Colors.ERROR)}")
                        time.sleep(30)
                        empty_count = 0
                        d.app_stop(self.golike_pkg)
                        time.sleep(1)
                        d.app_start(self.golike_pkg) # Khởi động lại app cho hết kẹt
                    time.sleep(3)
                    continue

                # 3. BẤM LÀM VIỆC (CHUYỂN SANG INSTAGRAM)
                # App GoLike thường có nút IG màu hồng/đỏ ghi Instagram hoặc Làm việc
                btn_lam_viec = d(textMatches=r"(?i).*Instagram.*|.*Làm việc.*")
                if btn_lam_viec.exists(timeout=5):
                    btn_lam_viec.click()
                    print(f"{Colors.color_text(f'[{self.serial}] Mở ứng dụng Instagram...', Colors.INFO)}")
                else:
                    d.click(size[0]*0.5, size[1]*0.6) # Tọa độ dự phòng giữa màn hình
                
                # 4. CHỜ VÀ THAO TÁC TRÊN INSTAGRAM
                print(f"{Colors.color_text(f'[{self.serial}] Chờ IG load bài viết...', Colors.INFO)}")
                time.sleep(random.uniform(4.0, 6.0))
                
                # Kiểm tra Action Block (Giới hạn tài khoản IG)
                if d(textMatches=r"(?i).*Thử lại sau.*|.*Try Again Later.*").exists(timeout=1):
                    print(f"{Colors.color_text(f'[{self.serial}] LỖI: Instagram bị block tính năng! Vui lòng đổi acc.', Colors.ERROR)}")
                    break

                btn_follow = d(textMatches=r"(?i)^Theo dõi$|^Follow$")
                btn_following = d(textMatches=r"(?i)^Đang theo dõi$|^Following$|^Requested$")
                
                if btn_follow.exists(timeout=2):
                    btn_follow.click()
                    print(f"{Colors.color_text(f'[{self.serial}] Đã bấm FOLLOW!', Colors.SUCCESS)}")
                elif btn_following.exists(timeout=1):
                    print(f"{Colors.color_text(f'[{self.serial}] Đã Follow từ trước.', Colors.WARNING)}")
                else:
                    print(f"{Colors.color_text(f'[{self.serial}] Không có nút Follow -> Thả tim (Click đúp).', Colors.INFO)}")
                    d.double_click(size[0]*0.5, size[1]*0.5, 0.1)
                
                time.sleep(random.uniform(1.5, 2.5))

                # 5. CHUYỂN LẠI APP GOLIKE
                print(f"{Colors.color_text(f'[{self.serial}] Chuyển lại App GoLike...', Colors.INFO)}")
                d.app_start(self.golike_pkg)
                time.sleep(random.uniform(2.5, 4.0))

                # 6. BẤM HOÀN THÀNH
                btn_hoan_thanh = d(textMatches=r"(?i).*Hoàn thành.*")
                if btn_hoan_thanh.exists(timeout=5):
                    btn_hoan_thanh.click()
                    print(f"{Colors.color_text(f'[{self.serial}] Gửi xác nhận Hoàn thành Job!', Colors.SUCCESS)}")
                    jobs_done += 1
                else:
                    d.swipe(size[0]*0.5, size[1]*0.7, size[0]*0.5, size[1]*0.4) # Vuốt lên lòi nút ra
                    if btn_hoan_thanh.exists(timeout=2): btn_hoan_thanh.click()
                    else: d.click(size[0]*0.5, size[1]*0.8) # Bấm tọa độ dự phòng

                # Nghỉ ngơi giữa các Job
                delay = random.uniform(6, 12)
                print(f"{Colors.color_text(f'[{self.serial}] Nghỉ {int(delay)}s trước job tiếp theo...', Colors.INFO)}")
                time.sleep(delay)

            print(f"\n{Colors.color_text(f'[{self.serial}] KẾT THÚC! Đã làm {jobs_done} Jobs.', Colors.TITLE)}")
            
        except Exception as e:
            print(f"{Colors.color_text(f'[{self.serial}] Văng luồng (Crash): {e}', Colors.ERROR)}")

if __name__ == "__main__":
    banner()
    devices = select_devices()
    try:
        max_j = int(input(f"{Colors.INFO}Nhập số Job muốn làm mỗi nick [VD: 50]: {Colors.RESET}"))
    except:
        max_j = 50
    
    threads = []
    for dev in devices:
        t = GoLikeAppWorker(dev, max_j)
        threads.append(t)
        t.start()
        
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        STOP_EVENT.set()
        print(Colors.color_text("\n[!] Dừng Tool an toàn.", Colors.ERROR))
        sys.exit()
