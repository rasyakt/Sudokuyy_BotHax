import subprocess
import numpy as np
import cv2

ADB = r"C:\Users\HYPE AMD\AppData\Local\Android\Sdk\platform-tools\adb.exe"
GRID_X_START = 8;  GRID_X_END   = 711
GRID_Y_START = 324; GRID_Y_END  = 1028
CELL_W = (GRID_X_END - GRID_X_START) / 9
CELL_H = (GRID_Y_END - GRID_Y_START) / 9

def get_screenshot():
    result = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True)
    arr = np.frombuffer(result.stdout, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def crop_cell(img, r, c, margin=7):
    x1 = int(GRID_X_START + c * CELL_W) + margin
    y1 = int(GRID_Y_START + r * CELL_H) + margin
    x2 = int(GRID_X_START + (c+1) * CELL_W) - margin
    y2 = int(GRID_Y_START + (r+1) * CELL_H) - margin
    return img[y1:y2, x1:x2]

def is_empty(cell):
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    return np.sum(gray < 150) < 18

img = get_screenshot()
print("Testing full board OCR...")

# Nilai yang diketahui (dari screenshot)
known = [
    [0, 0, 0, 0, 0, 0, 1, 9, 4],
    [4, 3, 1, 6, 0, 0, 0, 0, 0],
    [0, 2, 0, 1, 0, 5, 0, 0, 0],
    [3, 0, 6, 0, 8, 0, 9, 0, 0],
    [5, 0, 0, 2, 0, 3, 0, 0, 7],
    [0, 0, 7, 0, 5, 0, 6, 0, 1],
    [0, 0, 0, 8, 0, 7, 0, 4, 0],
    [0, 0, 0, 0, 0, 6, 7, 1, 2],
    [1, 7, 4, 0, 0, 0, 0, 0, 0],
]

# Test: cek setiap cell yang seharusnya berisi angka - apakah terdeteksi sebagai tidak kosong?
correct_empty = 0
correct_filled = 0
wrong_empty = 0
wrong_filled = 0

for r in range(9):
    for c in range(9):
        cell = crop_cell(img, r, c)
        empty = is_empty(cell)
        expected_empty = (known[r][c] == 0)
        
        if empty == expected_empty:
            if empty:
                correct_empty += 1
            else:
                correct_filled += 1
        else:
            if empty:
                wrong_empty += 1
                print(f"  MISS: Cell[{r}][{c}] seharusnya {known[r][c]} tapi terdeteksi KOSONG")
            else:
                wrong_filled += 1
                print(f"  EXTRA: Cell[{r}][{c}] seharusnya KOSONG tapi terdeteksi ISI")

total = 81
print(f"\nHasil:")
print(f"  Benar kosong: {correct_empty}")
print(f"  Benar berisi: {correct_filled}")
print(f"  Salah kosong: {wrong_empty}")
print(f"  Salah berisi: {wrong_filled}")
print(f"  Akurasi: {(correct_empty+correct_filled)/total*100:.1f}%")