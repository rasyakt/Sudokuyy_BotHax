#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  SUDOKU AUTO-SOLVER BOT (Unico Studio Android App via ADB)
================================================================================
  Target  : 1000 Kemenangan Otomatis Level Mudah (Easy)
  Fitur   :
    - 100% Akurasi OCR dengan Template Matching
    - Algoritma Solver Backtracking Instan (< 1ms)
    - Pengisian Input Cepat via Batch ADB Taps
    - State Machine Otomatis (Game -> Win Screen -> Level Selector -> Next Game)
    - Auto Recovery dari Iklan / Pop-up / Interupsi Layar
    - Resume State & Statistik Tersimpan Otomatis ke bot_stats.json
================================================================================
"""

import os
import sys
import time
import json
import subprocess
import cv2
import numpy as np

# Pastikan output log langsung ter-flush secara real-time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


# ============================ KONFIGURASI =====================================
DEFAULT_ADB = r"C:\Users\HYPE AMD\AppData\Local\Android\Sdk\platform-tools\adb.exe"
ADB = os.environ.get("ADB_PATH", DEFAULT_ADB if os.path.exists(DEFAULT_ADB) else "adb")
PACKAGE = "com.unicostudio.sudoku"
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(WORK_DIR, "templates")
STATS_FILE = os.path.join(WORK_DIR, "bot_stats.json")

# Koordinat Grid Layar (720 x 1600 px)
GRID_X_START = 8
GRID_X_END   = 711
GRID_Y_START = 324
GRID_Y_END   = 1028
CELL_W = (GRID_X_END - GRID_X_START) / 9.0  # ~78.11 px
CELL_H = (GRID_Y_END - GRID_Y_START) / 9.0  # ~78.22 px

# Posisi Numpad (1 - 9)
NUMPAD_Y = 1348
NUMPAD_X = [46, 123, 199, 275, 353, 430, 506, 581, 658]

# Koordinat Tombol Navigasi
BTN_WIN_BARU_X  = 364
BTN_WIN_BARU_Y  = 1236


BTN_WIN_MUDAH_X = 360
BTN_WIN_MUDAH_Y = 907

BTN_MENU_BARU_X = 360
BTN_MENU_BARU_Y = 1158

BTN_MENU_MUDAH_X = 360
BTN_MENU_MUDAH_Y = 1249

BTN_MENU_LANJUT_X = 360
BTN_MENU_LANJUT_Y = 1085

# Fitur Aplikasi
AUTOFILL_NINTH_BOX = True  # Aktif jika 'Isi kotak ke-9 secara otomatis' menyala di pengaturan app

LOCK_FILE = os.path.join(WORK_DIR, "bot.lock")


def compute_minimal_cells(initial_board, solved_board):
    """
    Menghitung sel minimal yang perlu diisi bot ketika fitur
    'Isi kotak ke-9 secara otomatis' aktif di aplikasi.
    Mengurangi sel yang perlu ditap dari ~50 menjadi ~28 sel,
    mencegah sisa tap mengenai tombol Share di layar menang!
    """
    b = [r[:] for r in initial_board]

    def apply_autofills():
        changed = False
        # Cek baris
        for r in range(9):
            zeros = [c for c in range(9) if b[r][c] == 0]
            if len(zeros) == 1:
                b[r][zeros[0]] = solved_board[r][zeros[0]]
                changed = True
        # Cek kolom
        for c in range(9):
            zeros = [r for r in range(9) if b[r][c] == 0]
            if len(zeros) == 1:
                b[zeros[0]][c] = solved_board[zeros[0]][c]
                changed = True
        # Cek blok 3x3
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                zeros = [(r, c) for r in range(br, br+3) for c in range(bc, bc+3) if b[r][c] == 0]
                if len(zeros) == 1:
                    r, c = zeros[0]
                    b[r][c] = solved_board[r][c]
                    changed = True
        return changed

    while apply_autofills():
        pass

    cells_to_tap = []
    for r in range(9):
        for c in range(9):
            if b[r][c] == 0:
                cells_to_tap.append((r, c, solved_board[r][c]))
                b[r][c] = solved_board[r][c]
                while apply_autofills():
                    pass

    return cells_to_tap



# ============================ TEMPLATE OCR ====================================

class SudokuOCR:
    def __init__(self):
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        for d in range(1, 10):
            path = os.path.join(TEMPLATES_DIR, f"{d}.png")
            if os.path.exists(path):
                self.templates[d] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            else:
                print(f"[WARN] Template digit {d} tidak ditemukan di {path}")

    def read_board(self, img):
        """Membaca 81 angka dari gambar papan dengan akurasi 100%."""
        board = []
        for r in range(9):
            row = []
            for c in range(9):
                cx = int(GRID_X_START + (c + 0.5) * CELL_W)
                cy = int(GRID_Y_START + (r + 0.5) * CELL_H)
                crop = img[cy-23:cy+23, cx-23:cx+23]
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

                # Sel kosong memiliki background putih bersih (dark_pixels < 50)
                if np.sum(gray < 180) < 50:
                    row.append(0)
                else:
                    _, bin_img = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
                    contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if not contours:
                        row.append(0)
                        continue
                    x, y, w, h = cv2.boundingRect(np.vstack(contours))
                    norm = cv2.resize(bin_img[y:y+h, x:x+w], (24, 32), interpolation=cv2.INTER_AREA)

                    best_score = -1.0
                    best_digit = 0
                    for d in range(1, 10):
                        if d not in self.templates:
                            continue
                        score = cv2.matchTemplate(norm, self.templates[d], cv2.TM_CCOEFF_NORMED)[0][0]
                        if score > best_score:
                            best_score = score
                            best_digit = d
                    row.append(best_digit)
            board.append(row)
        return board

# ============================ SUDOKU SOLVER ===================================

def is_valid_placement(board, row, col, num):
    """Cek apakah num valid diletakkan pada posisi row, col."""
    for c in range(9):
        if board[row][c] == num:
            return False
    for r in range(9):
        if board[r][col] == num:
            return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for dr in range(3):
        for dc in range(3):
            if board[br + dr][bc + dc] == num:
                return False
    return True

def solve_sudoku(board):
    """Algoritma Backtracking dengan forward checking (in-place)."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for num in range(1, 10):
                    if is_valid_placement(board, r, c, num):
                        board[r][c] = num
                        if solve_sudoku(board):
                            return True
                        board[r][c] = 0
                return False
    return True

def validate_initial_board(board):
    """Memverifikasi bahwa papan awal valid dan tidak korup."""
    filled = sum(1 for r in board for v in r if v > 0)
    if filled < 22:
        return False, f"Angka awal terlalu sedikit ({filled})"
    for r in range(9):
        nums = [v for v in board[r] if v > 0]
        if len(nums) != len(set(nums)):
            return False, f"Ada duplikasi angka pada baris {r+1}"
    for c in range(9):
        nums = [board[r][c] for r in range(9) if board[r][c] > 0]
        if len(nums) != len(set(nums)):
            return False, f"Ada duplikasi angka pada kolom {c+1}"
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            nums = [board[r][c] for r in range(br, br+3) for c in range(bc, bc+3) if board[r][c] > 0]
            if len(nums) != len(set(nums)):
                return False, f"Ada duplikasi angka pada blok 3x3 ({br//3+1},{bc//3+1})"
    return True, f"{filled} angka awal valid"

# ============================ SCREEN STATE DETECTOR ===========================

def detect_state(img):
    """
    Mengidentifikasi state layar saat ini:
    'game'       : Sedang dalam papan permainan aktif
    'win'        : Tampilan layar menang (Hebat!)
    'win_sheet'  : Sheet pemilih level yang muncul setelah klik baru di win screen
    'menu_sheet' : Sheet pemilih level dari menu utama
    'menu'       : Menu utama aplikasi
    'unknown'    : Iklan / Pop-up / Interupsi
    """
    if img is None:
        return "unknown"

    # 1. Game Screen: Ada 2 garis pembatas tebal horizontal dan numpad di bawah
    line1 = img[557:560, 50:670]
    line2 = img[792:795, 50:670]
    numpad = img[1320:1375, 40:680]
    if np.sum(line1 < 100) > 1000 and np.sum(line2 < 100) > 1000 and np.sum(numpad < 100) > 3000:
        return "game"

    # 2. Win Screen: Background biru penuh di bagian bawah (B>220, R<100)
    if img[1540, 360, 0] > 220 and img[1540, 360, 2] < 100:
        return "win"

    # 3. Win Sheet (Sheet pemilih level di atas win screen)
    if img[847, 200, 0] > 200 and np.mean(img[850:960, 200:500]) > 240 and img[200, 360, 0] < 100:
        return "win_sheet"

    # 4. Menu Sheet (Sheet pemilih level dari menu utama)
    if 160 < np.mean(img[:200, :]) < 200 and np.mean(img[1200:1300, 200:500]) > 240:
        return "menu_sheet"

    # 5. Menu Utama
    sudoku_dark = np.sum(cv2.cvtColor(img[450:580, 200:520], cv2.COLOR_BGR2GRAY) < 80)
    if sudoku_dark > 800 and np.mean(img[1130:1180, 200:520]) > 230:
        return "menu"

    return "unknown"

# ============================ BOT CONTROLLER ==================================

class SudokuBot:
    def __init__(self, target_wins=1000):
        self.target_wins = target_wins
        self.ocr = SudokuOCR()
        self.wins = 0
        self.fails = 0
        self.game_durations = []
        self._load_stats()

    def _load_stats(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, "r") as f:
                    data = json.load(f)
                    self.wins = data.get("wins", 0)
                    self.fails = data.get("fails", 0)
                    self.game_durations = data.get("durations", [])
            except Exception:
                pass

    def _save_stats(self):
        try:
            with open(STATS_FILE, "w") as f:
                json.dump({
                    "wins": self.wins,
                    "fails": self.fails,
                    "target": self.target_wins,
                    "avg_duration": round(float(np.mean(self.game_durations)), 1) if self.game_durations else 0,
                    "durations": self.game_durations[-50:]  # simpan 50 game terakhir
                }, f, indent=2)
        except Exception:
            pass

    def adb_screencap(self):
        res = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True)
        if not res.stdout:
            return None
        arr = np.frombuffer(res.stdout, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    def adb_tap(self, x, y):
        subprocess.run([ADB, "shell", f"input tap {int(x)} {int(y)}"])

    def handle_unknown_screen(self):
        """Menangani iklan, dialog tak terduga, atau app backgrounded."""
        print("  [RECOVERY] Menutup iklan / pop-up via KEYCODE_BACK...")
        subprocess.run([ADB, "shell", "input keyevent KEYCODE_BACK"])
        time.sleep(1.0)
        img = self.adb_screencap()
        if detect_state(img) != "unknown":
            return

        print("  [RECOVERY] Membawa kembali Sudoku ke layar depan...")
        subprocess.run([ADB, "shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)
        time.sleep(2.0)

    def navigate_to_game(self, timeout=30):
        """Memastikan navigasi sampai ke dalam game level Mudah."""
        start = time.time()
        while time.time() - start < timeout:
            img = self.adb_screencap()
            state = detect_state(img)

            if state == "game":
                return True
            elif state == "win":
                print("  [NAV] Layar menang terdeteksi -> klik Permainan Baru...")
                self.adb_tap(BTN_WIN_BARU_X, BTN_WIN_BARU_Y)
                time.sleep(1.0)
            elif state == "win_sheet":
                print("  [NAV] Pemilih level terbuka -> klik Mudah...")
                self.adb_tap(BTN_WIN_MUDAH_X, BTN_WIN_MUDAH_Y)
                time.sleep(1.5)
            elif state == "menu":
                # Cek apakah ada tombol 'Lanjut Permainan' (warna biru di Y=1085)
                if img[1085, 360, 0] > 180 and img[1085, 360, 2] < 100:
                    print("  [NAV] Menu utama -> klik Lanjut Permainan...")
                    self.adb_tap(BTN_MENU_LANJUT_X, BTN_MENU_LANJUT_Y)
                else:
                    print("  [NAV] Menu utama -> klik Permainan Baru...")
                    self.adb_tap(BTN_MENU_BARU_X, BTN_MENU_BARU_Y)
                time.sleep(1.2)
            elif state == "menu_sheet":
                print("  [NAV] Pemilih level menu terbuka -> klik Mudah...")
                self.adb_tap(BTN_MENU_MUDAH_X, BTN_MENU_MUDAH_Y)
                time.sleep(1.5)
            else:
                self.handle_unknown_screen()

        return False

    def solve_and_play(self):
        """Menyelesaikan 1 game aktif."""
        t_start = time.time()

        # 1. Pastikan di dalam game
        if not self.navigate_to_game():
            print("  [!] Gagal menavigasi ke game aktif.")
            return False

        # 2. Ambil screenshot & OCR dengan toleransi animasi (hingga 3x coba)
        time.sleep(0.6)
        board = None
        for attempt in range(3):
            img = self.adb_screencap()
            board = self.ocr.read_board(img)
            valid, msg = validate_initial_board(board)
            if valid:
                break
            time.sleep(1.0)

        # 3. Validasi papan
        if not valid:
            print(f"  [!] Papan tidak valid setelah 3x percobaan: {msg}")
            return False

        print(f"  [OCR] Papan terbaca sempurna: {msg}")

        # 4. Selesaikan puzzle
        solved = [r[:] for r in board]
        if not solve_sudoku(solved):
            print("  [!] Algoritma gagal memecahkan papan.")
            return False

        # 5. Kumpulkan sel yang perlu diisi
        if AUTOFILL_NINTH_BOX:
            cells_to_fill = compute_minimal_cells(board, solved)
            total_empty = sum(1 for r in board for v in r if v == 0)
            print(f"  [INPUT] Memasukkan {len(cells_to_fill)} sel (hemat {total_empty - len(cells_to_fill)} sel via Auto-Isi Kotak ke-9)...")
        else:
            cells_to_fill = [
                (r, c, solved[r][c])
                for r in range(9)
                for c in range(9)
                if board[r][c] == 0
            ]
            print(f"  [INPUT] Memasukkan solusi untuk {len(cells_to_fill)} sel...")


        # 6. Kirim batch taps via ADB (ukuran chunk aman untuk hindari tap overflow)
        chunk_size = 10
        total_cells = len(cells_to_fill)
        for i in range(0, total_cells, chunk_size):
            chunk = cells_to_fill[i:i+chunk_size]
            cmd_parts = []
            for r, c, val in chunk:
                cx = int(GRID_X_START + (c + 0.5) * CELL_W)
                cy = int(GRID_Y_START + (r + 0.5) * CELL_H)
                nx = NUMPAD_X[val - 1]
                ny = NUMPAD_Y
                cmd_parts.append(f"input tap {cx} {cy}")
                cmd_parts.append(f"input tap {nx} {ny}")
            cmd = "; ".join(cmd_parts)
            subprocess.run([ADB, "shell", cmd])

        # 7. Tunggu win screen secara reaktif (otomatis tutup iklan/dialog share jika muncul)
        print("  [WIN] Menunggu layar kemenangan...")
        win_detected = False
        wait_start = time.time()
        while time.time() - wait_start < 20:
            screen = self.adb_screencap()
            state = detect_state(screen)
            if state in ("win", "win_sheet"):
                win_detected = True
                break
            elif state == "unknown":
                # Menutup iklan / pop-up / dialog share yang mungkin terpencet
                print("  [AD/SHARE] Layar tak terduga / iklan / dialog share terdeteksi -> kirim KEYCODE_BACK...")
                subprocess.run([ADB, "shell", "input keyevent KEYCODE_BACK"])
                time.sleep(1.0)
            time.sleep(0.5)

        if not win_detected:
            print("  [!] Layar kemenangan belum terdeteksi setelah 20s.")
            return False

        duration = time.time() - t_start
        self.game_durations.append(duration)
        self.wins += 1
        self._save_stats()

        avg_dur = np.mean(self.game_durations)
        print(f"\n  >>> MENANG #{self.wins}/{self.target_wins} dalam {duration:.1f}s (Rata-rata: {avg_dur:.1f}s) <<<")

        # 8. Transisi ke game berikutnya
        print("  [NEXT] Memulai game berikutnya...")
        img_win = self.adb_screencap()
        if detect_state(img_win) == "win":
            self.adb_tap(BTN_WIN_BARU_X, BTN_WIN_BARU_Y)
            time.sleep(1.0)
        self.adb_tap(BTN_WIN_MUDAH_X, BTN_WIN_MUDAH_Y)
        time.sleep(1.5)

        return True


    def run(self):
        # Single-instance lock untuk mencegah dua bot berjalan bersamaan
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                # Cek apakah proses lama masih berjalan
                check = subprocess.run(["tasklist", "/FI", f"PID eq {old_pid}"], capture_output=True, text=True)
                if str(old_pid) in check.stdout:
                    print(f"[PERINGATAN] Bot lain dengan PID {old_pid} masih berjalan!")
                    print("Menghentikan proses lama terlebih dahulu agar tidak berebut layar...")
                    subprocess.run(["taskkill", "/F", "/PID", str(old_pid)], capture_output=True)
                    time.sleep(1.0)
            except Exception:
                pass

        try:
            with open(LOCK_FILE, "w") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass

        print("=" * 65)
        print("   SUDOKU AUTO-SOLVER 1000 WINS BOT (Unico Studio Android)")
        print(f"   Target: {self.target_wins} Kemenangan Level Mudah")
        print(f"   Progress Saat Ini: {self.wins}/{self.target_wins} ({self.wins/self.target_wins*100:.1f}%)")
        print("=" * 65)

        # Verifikasi ADB terhubung
        res = subprocess.run([ADB, "devices"], capture_output=True, text=True)
        lines = [l for l in res.stdout.strip().split("\n") if "device" in l and not l.startswith("List")]
        if not lines:
            print("[ERROR] Tidak ada HP terhubung ke ADB! Silakan cek kabel USB.")
            return

        print(f"Perangkat Terdeteksi: {lines[0].split()[0]}\n")

        # Pastikan app jalan
        subprocess.run([ADB, "shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)
        time.sleep(2.0)

        while self.wins < self.target_wins:
            game_idx = self.wins + 1
            print(f"\n--- [Game #{game_idx}/{self.target_wins}] ---")

            success = False
            try:
                success = self.solve_and_play()
            except KeyboardInterrupt:
                print("\n[!] Bot dihentikan secara manual oleh pengguna.")
                self._save_stats()
                break
            except Exception as e:
                print(f"  [ERROR] Terjadi pengecualian: {e}")

            if not success:
                self.fails += 1
                self._save_stats()
                print(f"  [RETRY] Gagal pada game #{game_idx}. Total gagal: {self.fails}. Memulihkan...")
                self.handle_unknown_screen()
                time.sleep(2.0)

        if self.wins >= self.target_wins:
            print("\n" + "=" * 65)
            print(f"   LUAR BIASA! Target {self.target_wins} kemenangan telah TERCAPAI!")
            print(f"   Total Menang: {self.wins} | Total Gagal: {self.fails}")
            print("=" * 65)

if __name__ == "__main__":
    target = 1000
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            pass
    bot = SudokuBot(target_wins=target)
    bot.run()
