# Debug Assets Archive

Folder ini berisi arsip aset pengujian, tangkapan layar (screenshot), dan dump data yang dikumpulkan selama proses riset, kalibrasi koordinat, dan pengujian bot Sudoku.

## Struktur Folder:
- **`screenshots/`**: Berisi tangkapan layar antarmuka permainan, deteksi status layar (menu, game, win, dialog), dan visualisasi grid.
- **`cells/`**: Kumpulan sampel potongan sel Sudoku (81 sel `r0c0.png` s/d `r8c8.png`) untuk kalibrasi ekstraksi OCR.
- **`dumps/`**: File data pengujian seperti `grid_analysis.json`, `tap_test.bin`, `ui.xml`, dan log pengujian.
