"""
Script analisis grid untuk mendapatkan koordinat tepat setiap sel Sudoku
"""
import subprocess
import cv2
import numpy as np
from PIL import Image
import json

import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = r"C:\Users\HYPE AMD\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def screenshot(filename="screen.png"):
    out_path = os.path.join(ROOT_DIR, "debug_assets", "screenshots", filename)
    subprocess.run([ADB, "shell", "screencap", "-p", f"/sdcard/{filename}"], capture_output=True)
    subprocess.run([ADB, "pull", f"/sdcard/{filename}", out_path], capture_output=True)
    return cv2.imread(out_path)

img = screenshot("s3.png")
print(f"Image size: {img.shape}")  # height, width, channels

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Tampilkan pixel values di sekitar grid untuk mencari batas
# Grid kelihatan ada di sekitar y=300-1050, x=10-710

# Cari garis-garis grid dengan edge detection
edges = cv2.Canny(gray, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)

horizontal_lines = []
vertical_lines = []

if lines is not None:
    for line in lines:
        line_flat = line.flatten()
        x1, y1, x2, y2 = line_flat[0], line_flat[1], line_flat[2], line_flat[3]
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        angle = abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
        
        if angle < 5 or angle > 175:  # horizontal
            horizontal_lines.append((y1+y2)//2)
        elif 85 < angle < 95:  # vertical
            vertical_lines.append((x1+x2)//2)

horizontal_lines = sorted(set([h for h in horizontal_lines]))
vertical_lines = sorted(set([v for v in vertical_lines]))

print(f"Horizontal lines Y positions: {horizontal_lines}")
print(f"Vertical lines X positions: {vertical_lines}")

# Cluster lines yang berdekatan
def cluster(lines, threshold=15):
    if not lines:
        return []
    clusters = [[lines[0]]]
    for l in lines[1:]:
        if l - clusters[-1][-1] < threshold:
            clusters[-1].append(l)
        else:
            clusters.append([l])
    return [int(np.mean(c)) for c in clusters]

h_clustered = cluster(horizontal_lines)
v_clustered = cluster(vertical_lines)

print(f"Horizontal clustered: {h_clustered}")
print(f"Vertical clustered: {v_clustered}")

# Simpan hasil analisis
analysis = {
    "image_size": {"height": img.shape[0], "width": img.shape[1]},
    "horizontal_lines": h_clustered,
    "vertical_lines": v_clustered
}

json_path = os.path.join(ROOT_DIR, "debug_assets", "dumps", "grid_analysis.json")
with open(json_path, "w") as f:
    json.dump(analysis, f, indent=2)

print(f"\nAnalysis saved to {json_path}")
print(f"\nExpected 10 horizontal lines (top + 9 rows) and 10 vertical lines (left + 9 cols)")
print(f"Got {len(h_clustered)} horizontal and {len(v_clustered)} vertical lines")

# Visualisasi
vis = img.copy()
for y in h_clustered:
    cv2.line(vis, (0, y), (img.shape[1], y), (0, 255, 0), 2)
for x in v_clustered:
    cv2.line(vis, (x, 0), (x, img.shape[0]), (255, 0, 0), 2)
vis_path = os.path.join(ROOT_DIR, "debug_assets", "screenshots", "grid_lines.png")
cv2.imwrite(vis_path, vis)
print(f"Grid visualization saved to {vis_path}")
