import os
import subprocess
import numpy as np
import cv2
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = r"C:\Users\HYPE AMD\AppData\Local\Android\Sdk\platform-tools\adb.exe"
GRID_X_START = 8
GRID_X_END   = 711
GRID_Y_START = 324
GRID_Y_END   = 1028
CELL_W = (GRID_X_END - GRID_X_START) / 9
CELL_H = (GRID_Y_END - GRID_Y_START) / 9

def get_screenshot():
    result = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True)
    if not result.stdout:
        return None
    arr = np.frombuffer(result.stdout, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

img = get_screenshot()
print("Screenshot shape:", img.shape if img is not None else "None")

if img is not None:
    # Test detect_state
    grid_roi = img[GRID_Y_START:GRID_Y_END, GRID_X_START:GRID_X_END]
    grid_gray = cv2.cvtColor(grid_roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(grid_gray, 30, 100)
    edge_dens = np.sum(edges > 0) / edges.size
    
    np_roi = img[1280:1430, 0:720]
    np_gray = cv2.cvtColor(np_roi, cv2.COLOR_BGR2GRAY)
    _, np_bin = cv2.threshold(np_gray, 180, 255, cv2.THRESH_BINARY_INV)
    np_dens = np.sum(np_bin > 0) / np_bin.size
    
    print(f"Edge density: {edge_dens:.4f}")
    print(f"Numpad density: {np_dens:.4f}")
    
    if edge_dens > 0.015 and np_dens > 0.008:
        print("STATE: GAME")
    else:
        print("STATE: NOT GAME")
    
    # Test OCR satu cell
    r, c = 0, 6  # Row 0, Col 6 = angka 1
    x1 = int(GRID_X_START + c * CELL_W) + 7
    y1 = int(GRID_Y_START + r * CELL_H) + 7
    x2 = int(GRID_X_START + (c+1) * CELL_W) - 7
    y2 = int(GRID_Y_START + (r+1) * CELL_H) - 7
    
    cell = img[y1:y2, x1:x2]
    print(f"Cell [0][6] size: {cell.shape}")
    
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    dark_px = np.sum(gray < 150)
    print(f"Dark pixels in cell[0][6]: {dark_px} (expected: angka 1)")
    
    cv2.imwrite(os.path.join(ROOT_DIR, "debug_assets", "screenshots", "test_cell.png"), cell)
    cv2.imwrite(os.path.join(ROOT_DIR, "debug_assets", "screenshots", "live_screen2.png"), img)
    print("Saved test images to debug_assets/screenshots/")