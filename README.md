# 🧩 Sudoku Auto-Solver Bot (Android ADB)

Bot otomatisasi untuk menyelesaikan teka-teki permainan Android **Sudoku** (karya Unico Studio) secara otomatis menggunakan koneksi Android Debug Bridge (ADB), OpenCV OCR Template Matching, dan algoritma pemecah *Backtracking* instan.

Dirancang untuk mencapai target ratusan hingga ribuan kemenangan berturut-turut pada tingkat kesulitan **Mudah (Easy)** secara stabil, cepat, dan mandiri (*autonomous*).

---

## 🌟 Fitur Utama

- **100% Akurasi OCR**: Menggunakan *Template Matching* biner beresolusi terkalibrasi untuk mengenali seluruh angka 1–9 di atas papan 9x9 tanpa ketergantungan pada pustaka OCR berat seperti Tesseract.
- **Solver Backtracking Instan (< 1 ms)**: Memecahkan papan 9x9 yang valid dalam hitungan milidetik secara *in-place*.
- **Auto-Fill Kotak ke-9 Cerdas**: Memanfaatkan fitur bawaan game ("*Isi kotak ke-9 secara otomatis*") untuk memangkas jumlah sel yang perlu diklik dari ~50 menjadi ~28 sel, mempercepat penyelesaian dan mencegah sisa ketukan mengenai tombol *Share* pada layar kemenangan.
- **Batch Tap Input ADB**: Mengirimkan perintah sentuhan sel dan numpad secara berkelompok (*chunk*) untuk memaksimalkan kecepatan input tanpa membuat buffer input perangkat kewalahan.
- **Finite State Machine (FSM) & Navigasi Penuh**: Secara otomatis mendeteksi apakah layar berada di dalam permainan (`game`), layar menang (`win`), lembar pemilih level (`win_sheet` / `menu_sheet`), atau menu utama (`menu`).
- **Auto-Recovery Iklan & Dialog**: Jika terjadi interupsi layar tak terduga, dialog rating, atau iklan yang muncul di sela permainan, bot secara otomatis mengirimkan `KEYCODE_BACK` dan meluncurkan ulang aktivitas game.
- **Pencatatan Statistik Real-Time**: Menyimpan riwayat jumlah kemenangan (`wins`), kegagalan (`fails`), target kemenangan, dan durasi rata-rata per game ke dalam file `bot_stats.json`.
- **Single-Instance Lock**: Mencegah benturan proses jika bot dijalankan dua kali secara bersamaan melalui mekanisme `bot.lock`.

---

## 📁 Struktur Direktori Proyek

Proyek ini telah ditata dengan struktur rapi dan terorganisir:

```text
Sudoku/
├── debug_assets/              # Arsip aset pengujian dan kalibrasi
│   ├── cells/                 # 81 sampel potongan sel (r0c0 s/d r8c8)
│   ├── dumps/                 # File dump data (grid_analysis.json, ui.xml, dll.)
│   ├── screenshots/           # Arsip screenshot pengujian antarmuka & grid
│   └── README.md              # Dokumentasi arsip debug
├── templates/                 # Template digit OCR 1–9
│   ├── 1.png
│   ├── ...
│   └── 9.png
├── tools/                     # Skrip pembantu, diagnosa & kalibrasi
│   ├── analyze_grid.py        # Kalibrasi koordinat grid dan deteksi garis
│   ├── test_diag.py           # Analisis piksel gelap sel
│   ├── test_diag2.py          # Analisis batas margin sel
│   ├── test_ocr.py            # Uji coba pembacaan OCR & status layar
│   ├── test_ocr2.py           # Uji coba akurasi pembacaan 81 sel papan
│   └── README.md              # Panduan penggunaan skrip tools
├── .gitignore                 # Konfigurasi file yang diabaikan Git
├── bot_stats.json             # Catatan statistik & progress kemenangan bot
├── requirements.txt           # Daftar dependensi Python
├── sudoku_bot.py              # Script utama bot otomatisasi
└── README.md                  # Dokumentasi proyek
```

---

## ⚙️ Persyaratan Sistem

1. **Python**: Versi 3.8 atau lebih baru.
2. **Android Device / Emulator**:
   - Resolusi layar target bot saat ini terkalibrasi pada **720 x 1600 piksel**.
   - Mode Pengembang (*Developer Options*) dan **USB Debugging** aktif.
3. **Android Platform Tools (ADB)** terinstal di komputer.
4. Game **Sudoku (Unico Studio)** terinstal di perangkat Android.

---

## 🚀 Instalasi & Persiapan

1. Pasang dependensi pustaka Python yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

2. Pastikan perangkat Android terhubung dan terdeteksi oleh ADB:
   ```bash
   adb devices
   ```
   *(Pastikan status perangkat terdaftar sebagai `device`, bukan `unauthorized` atau `offline`)*.

3. *(Opsional)* Jika lokasi `adb.exe` Anda berbeda dengan nilai bawaan pada script, Anda dapat menyetel variabel *environment*:
   ```powershell
   $env:ADB_PATH = "C:\path\ke\adb.exe"
   ```

---

## 🎮 Cara Menjalankan Bot

Jalankan script utama `sudoku_bot.py`:

```bash
python sudoku_bot.py
```

Secara default, bot akan mengejar target 1000 kemenangan. Anda juga dapat menentukan target kemenangan khusus melalui argumen baris perintah:

```bash
# Menjalankan dengan target 500 kemenangan
python sudoku_bot.py 500
```

Untuk menghentikan bot secara aman kapan saja, tekan **`Ctrl + C`** di terminal. Statistik dan pencapaian terakhir akan langsung tersimpan ke `bot_stats.json`.

---

## 📊 File Statistik (`bot_stats.json`)

Contoh data yang tersimpan pada `bot_stats.json`:
```json
{
  "wins": 192,
  "fails": 3,
  "target": 200,
  "avg_duration": 56.8,
  "durations": [
    27.5,
    60.8,
    26.5
  ]
}
```
Progress kemenangan tersimpan secara persisten, sehingga Anda dapat melanjutkan sesi bot kapan saja tanpa mengulang dari angka nol.
