# Tools & Skrip Kalibrasi

Folder ini berisi kumpulan skrip pembantu untuk mengkalibrasi koordinat papan, menguji akurasi OCR, dan mendiagnosa respons layar aplikasi Sudoku via ADB.

## Daftar Skrip:

1. **`analyze_grid.py`**:
   - Mendeteksi batas grid papan 9x9 menggunakan Canny Edge Detection & Hough Lines.
   - Menyimpan visualisasi garis grid ke `debug_assets/screenshots/grid_lines.png` dan hasil klaster garis ke `debug_assets/dumps/grid_analysis.json`.

2. **`test_ocr.py`**:
   - Memvalidasi pembacaan screenshot real-time via ADB.
   - Menguji deteksi status layar (apakah sedang dalam permainan atau bukan) serta ekstraksi piksel sel.

3. **`test_ocr2.py`**:
   - Menguji akurasi pembacaan 81 sel papan terhadap puzzle acuan untuk mendeteksi false empty atau false filled.

4. **`test_diag.py` & `test_diag2.py`**:
   - Menganalisis ambang batas piksel gelap (dark pixels) dan ukuran margin crop sel untuk memastikan digit terbaca sempurna tanpa terpotong garis grid.
