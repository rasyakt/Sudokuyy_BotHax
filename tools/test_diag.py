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

img = get_screenshot()

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

print("Dark pixel counts (threshold=150):")
print("EMPTY cells:")
for r in range(9):
    for c in range(9):
        if known[r][c] == 0:
            cell = crop_cell(img, r, c)
            gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
            dark = np.sum(gray < 150)
            print(f"  [{r}][{c}]: {dark} dark px, mean={np.mean(gray):.0f}")

print("\nFILLED cells:")
for r in range(9):
    for c in range(9):
        if known[r][c] > 0:
            cell = crop_cell(img, r, c)
            gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
            dark = np.sum(gray < 150)
            print(f"  [{r}][{c}]={known[r][c]}: {dark} dark px, mean={np.mean(gray):.0f}")