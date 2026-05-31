import os
import sys
import subprocess
import json
import asyncio
import time
import urllib.parse
import re
import random

def install_requirements():
    packages = ["requests", "websockets"]
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

import requests
import websockets

C_RED = '\033[91m'
C_GREEN = '\033[92m'
C_YELLOW = '\033[93m'
C_CYAN = '\033[96m'
C_RESET = '\033[0m'

HEADERS_MOBILE = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
}

def print_log(msg, color=C_RESET):
    print(f"{color}{msg}{C_RESET}")

def get_multiline_json():
    print_log("Vui long dan chuoi JSON Token. Nhan Enter sau do nhap 'ok' de xac nhan:", C_CYAN)
    lines = []
    while True:
        line = input()
        if line.strip().lower() == 'ok':
            break
        lines.append(line)
    
    full_str = " ".join(lines)
    try:
        json.loads(full_str)
        return full_str
    except Exception:
        return full_str

def login_game(json_data):
    url = "https://crash.turbogg4u.online/api/common/profile"
    try:
        response = requests.post(url, headers=HEADERS_MOBILE, data=json_data.encode('utf-8'), timeout=15)
        data = response.json()
        if "token" in data and "id" in data:
            return {
                "success": True,
                "player_id": data["sub"],
                "wss_token": data["token"],
                "balance": data.get("balance", 0)
            }
        return {"success": False, "msg": "Khong tim thay token. Kiem tra lai chuoi JSON."}
    except Exception as e:
        return {"success": False, "msg": str(e)}

def basic_auto_logic(history):
    base_target = 1.15
    if len(history) >= 5:
        recent_wins = sum(1 for x in history[-5:] if x >= 1.5)
        if recent_wins >= 2:
            base_target = 1.25
        else:
            base_target = 1.12
    final_target = base_target + random.uniform(0.01, 0.05)
    return round(final_target, 2)

def apply_config(session, config_id):
    cfg = session['configs'][config_id]
    session['current_config_id'] = config_id
    session['base_bet'] = cfg['base_bet']
    session['target_x'] = cfg['target_x']
    session['auto_x'] = cfg['auto_x']
    session['max_bet'] = cfg['max_bet']
    session['skip_win_min'] = cfg['skip_win_min']
    session['skip_win_max'] = cfg['skip_win_max']
    session['skip_loss_min'] = cfg['skip_loss_min']
    session['skip_loss_max'] = cfg['skip_loss_max']

async def radar_tracker_task(session):
    last_x = 1.00
    start_time = time.time()
    print_log(f"\n[CẤU HÌNH {session['current_config_id']}] MÁY BAY KHỞI HÀNH", C_CYAN)
    
    try:
        while session.get('is_betting', False) and session.get('is_running', False):
            current_x = session.get('last_flying_x', 1.00)
            if current_x > last_x:
                sys.stdout.write(f"\r[RADAR] Dang bay: {current_x:.2f}x | Thoi gian: {int(time.time() - start_time)}s")
                sys.stdout.flush()
                last_x = current_x
            await asyncio.sleep(0.1)
            
        crash_x = session.get('last_flying_x', 1.00)
        sys.stdout.write(f"\r[RADAR] BUM! Diem gay: {crash_x:.2f}x                              \n")
        sys.stdout.flush()
    except Exception:
        pass

async def listen_game_server(session):
    ws_url = "wss://crash.turbogg4u.online/ws/gameserver"
    
    while session.get('is_running', False):
        try:
            async with websockets.connect(ws_url, ping_interval=10, ping_timeout=20, max_size=None) as ws_game:
                while session.get('is_running', False):
                    msg = await ws_game.recv()
                    try:
                        if msg.startswith("1,"):
                            sec = msg.split(",")[1]
                            if sec in ["3", "2"] and not session.get('is_betting', False):
                                session['is_betting'] = True
                                
                                if session.get('last_flying_x', 0) > 0:
                                    session['history_x'].append(session['last_flying_x'])
                                    if len(session['history_x']) > 50:
                                        session['history_x'].pop(0)
                                    
                                    if session['observe_count'] < session['observe_target']:
                                        session['observe_count'] += 1
                                        if session['observe_count'] == session['observe_target']:
                                            print_log("[HETHONG] Da thu thap du du lieu. Kich hoat von!", C_GREEN)
                                    elif session.get('pending_summary'):
                                        s = session['pending_summary']
                                        recent_str = " | ".join([f"{x:.2f}" for x in session['history_x'][-5:]])
                                        print_log(f"\n[BAO CAO] Trang thai: {s['text_res']}", C_YELLOW)
                                        print_log(f"Target: {s['target_x']:.2f}x | Thuc te: {session['last_flying_x']:.2f}x", C_RESET)
                                        print_log(f"Loi nhuan vong: {s['profit_round']:.2f} BLD", C_GREEN if s['profit_round'] > 0 else C_RED)
                                        print_log(f"Lich su gan day: {recent_str}", C_CYAN)
                                        print_log(f"TONG QUY HIEN TAI: {s['current_balance']:.2f} BLD\n", C_YELLOW)
                                        session['pending_summary'] = None
                                
                                session['last_flying_x'] = 1.00
                                asyncio.create_task(radar_tracker_task(session))

                                if session['observe_count'] < session['observe_target']:
                                    continue 

                                total_profit = session['current_balance'] - session['initial_balance']
                                
                                if session['take_profit'] > 0 and total_profit >= session['take_profit']:
                                    session['is_running'] = False
                                    print_log(f"\n[🎉 HOÀN THÀNH MỤC TIÊU] Lãi đạt mức x2 tiền cược gốc (+{total_profit:.2f} BLD). Tool tự động nghỉ ngơi để bảo toàn thành quả!", C_GREEN)
                                    break
                                
                                if session['stop_loss'] > 0 and total_profit <= -session['stop_loss']:
                                    session['is_running'] = False
                                    print_log(f"\n[CAT LO] Cham nguong ro rui ({total_profit:.2f} BLD). Dung he thong.", C_RED)
                                    break

                                # Sửa thành số thập phân để có thể đánh lẻ (ví dụ 3.6)
                                bet_amount = round(float(session['current_bet']), 2)
                                
                                if session['current_balance'] < bet_amount:
                                    session['is_running'] = False
                                    print_log(f"[LOI] Quy ({session['current_balance']}) khong du thuc thi lenh ({bet_amount}).", C_RED)
                                    break 

                                if not session.get('auth_connected', False):
                                    print_log(f"\n[BẢO VỆ] Máy chủ xử lý lệnh đang mất kết nối. Đợi ván sau...", C_YELLOW)
                                    session['bet_id'] = None
                                    session['bet_placed'] = False
                                    continue
                                
                                if session.get('is_waiting_for_result', False) or session.get('bet_placed', False):
                                    session['spam_count'] += 1
                                    if session['spam_count'] >= 2:
                                        print_log("\n[DỪNG KHẨN CẤP] Phát hiện kẹt lệnh 2 ván liên tiếp! Tắt hệ thống để bảo vệ vốn.", C_RED)
                                        session['is_running'] = False
                                        break
                                    else:
                                        print_log("\n[CẢNH BÁO MẠNG] Lệnh cũ chưa chốt xong, tạm bỏ qua nhịp này...", C_YELLOW)
                                        continue

                                if session['skip_count'] > 0:
                                    session['skip_count'] -= 1
                                    print_log(f"[BO QUA] Dang bo qua lenh, con lai {session['skip_count']} van.", C_YELLOW)
                                else:
                                    if session['auto_x']:                                      
                                        session['target_x'] = basic_auto_logic(session['history_x'])
                                    
                                    session['is_waiting_for_result'] = True
                                    session['spam_count'] = 0 
                                    
                                    auto_cashout_multiplier = str(session['target_x'])
                                        
                                    bet_payload = {
                                        "type": "placebet", "l": 2, "amount": bet_amount, "coefficient": auto_cashout_multiplier,
                                        "currency": "bld", "index": 0, "metadata": {"subPartnerId": "", "device": "mobile", "manual": True},
                                        "theme": "default", "tag": "a"
                                    }
                                    await session['auth_send_queue'].put(json.dumps(bet_payload))
                                    print_log(f"[VAO LENH - C.HÌNH {session['current_config_id']}] Cuoc: {bet_amount} BLD | Muc tieu: {session['target_x']}x", C_GREEN)

                        elif msg.startswith("4,"):
                            current_x = float(msg.split(",")[1])
                            session['last_flying_x'] = current_x
                            
                        elif msg.startswith("5,"):
                            session['is_betting'] = False
                            parts = msg.split(",")
                            if len(parts) >= 4:
                                session['last_flying_x'] = float(parts[3])
                                
                            if not session.get('bet_placed', False):
                                session['is_waiting_for_result'] = False

                    except ValueError:
                        pass
                    except Exception:
                        pass
        except Exception:
            if session.get('is_running', False):
                await asyncio.sleep(3)

async def listen_auth_server(session):
    safe_player_id = urllib.parse.quote(session['player_id'].replace("@", ":"))
    ws_url = f"wss://crash.turbogg4u.online/ws/v2/game/?playerId={safe_player_id}&token={session['wss_token']}"
    
    while session.get('is_running', False):
        try:
            async with websockets.connect(ws_url, ping_interval=10, ping_timeout=20, max_size=None) as ws_auth:
                session['auth_connected'] = True
                
                async def sender():
                    while session.get('is_running', False) and session.get('auth_connected', False):
                        data_to_send = await session['auth_send_queue'].get()
                        try:
                            await ws_auth.send(data_to_send)
                        except Exception as e:
                            print_log(f"[LỖI GỬI LỆNH] Không thể gửi lệnh tới máy chủ: {e}", C_RED)
                            break
                            
                sender_task = asyncio.create_task(sender())
                try:
                    while session.get('is_running', False):
                        msg = await ws_auth.recv()
                        try:
                            if "balance_ticket" in msg:
                                match = re.search(r'\[([\d\.]+),', msg)
                                if match:
                                    session['current_balance'] = float(match.group(1))

                            if msg.startswith("{"):
                                data = json.loads(msg)
                                if data.get("type") == "placed" and "data" in data:
                                    session['bet_id'] = data["data"].get("id")
                                    session['bet_placed'] = True
                                    
                                if data.get("type") == "result":
                                    if session.get('bet_placed'):
                                        session['is_waiting_for_result'] = False 
                                        
                                        session['total_played'] += 1
                                        res = data.get("result")
                                        payout = float(data.get("payout", 0))
                                        amount = float(data.get("amount", session['current_bet']))
                                        
                                        if res == "won":
                                            profit_round = payout - amount
                                            session['consecutive_losses'] = 0 
                                            session['accumulated_loss'] = 0 # Xóa sổ tiền lỗ khi thắng
                                            
                                            old_cfg = session['current_config_id']
                                            if old_cfg == 1: next_cfg = 3
                                            elif old_cfg == 3: next_cfg = 2
                                            else: next_cfg = 1
                                                
                                            apply_config(session, next_cfg)
                                            session['current_bet'] = session['base_bet'] 
                                            text_res = f"THẮNG (Đổi cấu hình: {old_cfg} -> {next_cfg} | Reset mức cược)"
                                            
                                            if session['skip_win_max'] >= session['skip_win_min']:
                                                diff_win = session['skip_win_max'] - session['skip_win_min']
                                                session['skip_count'] = session['skip_win_min'] if diff_win == 0 else (session['total_played'] % (diff_win + 1)) + session['skip_win_min']
                                        
                                        else:
                                            profit_round = -amount
                                            session['consecutive_losses'] += 1
                                            
                                            # CỘNG DỒN TIỀN LỖ ĐỂ TÍNH TOÁN BÙ LỖ THÔNG MINH
                                            session['accumulated_loss'] += amount 
                                            
                                            if session['consecutive_losses'] >= 3:
                                                old_cfg = session['current_config_id']
                                                available_configs = [c for c in [1, 2, 3] if c != old_cfg]
                                                next_cfg = random.choice(available_configs)
                                                
                                                apply_config(session, next_cfg)
                                                session['consecutive_losses'] = 0 
                                                prefix_text = f"Đổi sang Cấu hình {next_cfg}"
                                            else:
                                                prefix_text = f"Giữ nguyên Cấu hình {session['current_config_id']}"
                                            
                                            if session['max_bet'] > 0 and session['current_bet'] >= session['max_bet']:
                                                print_log(f"\n[BÁO ĐỘNG] ĐÃ CHẠM ĐỈNH MAX BET ({session['max_bet']}) MÀ VẪN THUA!", C_RED)
                                                print_log("[BẢO VỆ VỐN] Cắt đứt chuỗi gồng, reset về cược gốc để tránh cháy tài khoản.", C_YELLOW)
                                                session['current_bet'] = session['base_bet']
                                                session['accumulated_loss'] = 0 # Xả cầu thì cũng xóa sổ nợ luôn
                                                text_res = f"THUA (Chạm đỉnh Max Bet -> Cắt máu về cược gốc | {prefix_text})"
                                            else:
                                                # ==============================================================
                                                # CÔNG THỨC BÙ LỖ THÔNG MINH (Không bị hao hụt dòng tiền)
                                                # Tiền cược ván sau = (Tổng lỗ + Tiền lãi mục tiêu) / (Tọa độ X - 1)
                                                # ==============================================================
                                                target_x_val = float(session['target_x'])
                                                if target_x_val > 1.0:
                                                    calculated_bet = (session['accumulated_loss'] + session['base_bet']) / (target_x_val - 1.0)
                                                    next_bet = round(calculated_bet, 2)
                                                else:
                                                    next_bet = session['base_bet']
                                                
                                                if session['max_bet'] > 0 and next_bet > session['max_bet']:
                                                    session['current_bet'] = session['max_bet']
                                                else:
                                                    session['current_bet'] = next_bet
                                                text_res = f"THUA (Bù lỗ thông minh | {prefix_text})"
                                            
                                            if session['skip_loss_max'] >= session['skip_loss_min']:
                                                diff_loss = session['skip_loss_max'] - session['skip_loss_min']
                                                session['skip_count'] = session['skip_loss_min'] if diff_loss == 0 else (session['total_played'] % (diff_loss + 1)) + session['skip_loss_min']
                                        
                                        session['current_balance'] += profit_round
                                        
                                        session['pending_summary'] = {
                                            "text_res": text_res,
                                            "target_x": session['target_x'],
                                            "profit_round": profit_round,
                                            "current_balance": session['current_balance']
                                        }
                                    
                                    session['bet_id'] = None
                                    session['bet_placed'] = False
                                    session['cashed_out'] = False
                        except json.JSONDecodeError:
                            pass
                        except Exception:
                            pass
                finally:
                    sender_task.cancel()
                    session['auth_connected'] = False 
                    
        except Exception as e:
            session['auth_connected'] = False
            if session.get('is_running', False):
                print_log(f"\n[CẢNH BÁO] Máy chủ Đặt Cược (Auth) đã ngắt kết nối: {e}", C_RED)
                
                if "401" in str(e) or "403" in str(e):
                    print_log("[LỖI CHÍ MẠNG] Token JSON của bạn đã hết hạn! Hãy F5 trình duyệt, copy Token mới và chạy lại tool.", C_RED)
                    session['is_running'] = False
                    break
                    
                await asyncio.sleep(5)

async def run_crash_bot(session):
    session['auth_send_queue'] = asyncio.Queue()
    print_log("[HETHONG] Khoi dong ket noi may chu...", C_CYAN)
    try:
        await asyncio.gather(
            listen_game_server(session),
            listen_auth_server(session)
        )
    except Exception as e:
        print_log(f"[LOI] Mat ket noi module tac chien: {e}", C_RED)
    finally:
        session['is_running'] = False

def start_async_loop(session):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_crash_bot(session))
    except KeyboardInterrupt:
        session['is_running'] = False
        print_log("\n[HETHONG] Da dung thu cong.", C_YELLOW)

def main():
    os.system('clear')
    print_log("CRASHX ADMIN XD-BOT - BÙ LỖ THÔNG MINH (CHỐNG HAO HỤT)", C_CYAN)
    
    json_data = get_multiline_json()
    print_log("\n[HETHONG] Dang xac thuc...", C_YELLOW)
    
    auth_res = login_game(json_data)
    if not auth_res["success"]:
        print_log(f"[LOI] Tu choi truy cap: {auth_res['msg']}", C_RED)
        return
        
    print_log(f"[THANH CONG] Truy cap hop le. Quy: {auth_res['balance']} BLD", C_GREEN)
    
    session = {
        "player_id": auth_res["player_id"],
        "wss_token": auth_res["wss_token"],
        "is_running": True,
        "bet_id": None,
        "bet_placed": False,
        "cashed_out": False,
        "is_betting": False,
        "auth_send_queue": None,
        "initial_balance": auth_res['balance'],
        "current_balance": auth_res['balance'],
        "total_played": 0,
        "history_x": [],
        "last_flying_x": 1.00,
        "pending_summary": None,
        "observe_count": 0,
        "consecutive_losses": 0,
        "accumulated_loss": 0, # Biến theo dõi tổng nợ cần gỡ
        "configs": {},
        "auth_connected": False,
        "is_waiting_for_result": False,
        "spam_count": 0
    }

    try:
        for i in range(1, 4):
            print_log(f"\n--- NHẬP THÔNG SỐ CHO CẤU HÌNH {i} ---", C_YELLOW)
            cfg = {}
            # Tiền cược gốc giờ có thể nhập số thập phân (VD: 3.6)
            cfg['base_bet'] = float(input(f"{C_CYAN}Nhap so tien cuoc goc (VD: 3.6): {C_RESET}"))
            
            target_input = input(f"{C_CYAN}Nhap Toa Do X (VD: 1.5): {C_RESET}").strip().lower()
            if target_input == 'auto':
                cfg['auto_x'] = True
                cfg['target_x'] = 1.15
            else:
                cfg['auto_x'] = False
                cfg['target_x'] = float(target_input)
                
            skip_win = input(f"{C_CYAN}Bo qua sau khi THANG (VD: 0-0 hoac 1-2): {C_RESET}").split('-')
            cfg['skip_win_min'], cfg['skip_win_max'] = int(skip_win[0]), int(skip_win[1])
            
            skip_loss = input(f"{C_CYAN}Bo qua sau khi THUA (VD: 0-0 hoac 1-2): {C_RESET}").split('-')
            cfg['skip_loss_min'], cfg['skip_loss_max'] = int(skip_loss[0]), int(skip_loss[1])
            
            # ĐÃ XÓA KHAI BÁO HỆ SỐ GẤP THẾP VÌ TOOL ĐÃ TỰ ĐỘNG TÍNH TOÁN
            
            cfg['max_bet'] = float(input(f"{C_CYAN}Gioi han cuoc khi gap thep (0 = khong gioi han): {C_RESET}"))
            
            session['configs'][i] = cfg
        
        print_log(f"\n--- THÔNG SỐ CHUNG CHO HỆ THỐNG ---", C_YELLOW)
        
        # Tự động chốt lời = Cược gốc cấu hình 1 nhân 2
        session['take_profit'] = session['configs'][1]['base_bet'] * 2
        print_log(f"[*] Đã TỰ ĐỘNG thiết lập Chốt Lời: {session['take_profit']} BLD (Gấp đôi mức cược gốc)", C_GREEN)
        
        stop_loss_input = input(f"{C_CYAN}Nhap Cat Lo (VD: 5000, go 0 de bo qua): {C_RESET}")
        session['stop_loss'] = int(stop_loss_input) if stop_loss_input.strip() else 0
        
        session['observe_target'] = int(input(f"{C_CYAN}Theo doi truoc khi vao lenh (So van, VD: 0): {C_RESET}"))
        session['skip_count'] = 0
        
        apply_config(session, 1)
        session['current_bet'] = session['base_bet']
        
    except ValueError:
        print_log("[LOI] Sai dinh dang thong so. Vui long chay lai va nhap so hop le.", C_RED)
        return

    print_log("\n[HETHONG] BANG DIEU KHIEN SAN SANG!", C_GREEN)
    start_async_loop(session)

if __name__ == "__main__":
    main()
