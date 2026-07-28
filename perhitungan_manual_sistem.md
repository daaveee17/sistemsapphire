# Perhitungan Manual Sistem Prediksi & Simulasi KPR Sapphire

Berikut adalah penjabaran proses perhitungan manual (di balik layar) tentang bagaimana sistem memproses input pengguna, dari prediksi harga hingga analisis kelayakan kredit.

---

### Skenario Contoh (Input Pengguna)

**1. Spesifikasi Unit (Untuk Prediksi Harga):**
*   **Blok Kavling:** A1
*   **Luas Bangunan (m2):** 36
*   **Luas Tanah (m2):** 72
*   **Kamar Tidur:** 2
*   **Kamar Mandi:** 1
*   **Posisi Kavling:** Standard
*   **Smart Door Lock:** Ya (1)

**2. Data Finansial (Untuk Simulasi KPR):**
*   **Uang Muka (DP):** 20%
*   **Tenor Kredit:** 15 Tahun
*   **Bunga:** 8% per tahun (0.08)
*   **Penghasilan Bulanan:** Rp 10.000.000
*   **Cicilan Eksisting:** Rp 1.500.000

---

## Langkah 1: Prediksi Harga Menggunakan Model ANN
Sistem menggunakan *Artificial Neural Network* (ANN). Karena ini adalah model Machine Learning yang kompleks, perhitungannya tidak sesederhana perkalian biasa, namun prosesnya adalah:
1.  **Encoding:** Nilai teks seperti "A1" dan "Standard" diubah menjadi angka menggunakan `LabelEncoder`.
2.  **Scaling:** Semua input angka diseragamkan skalanya menggunakan `StandardScaler` agar model ANN bisa memprosesnya dengan optimal.
3.  **Forward Pass (ANN):** Data yang sudah disesuaikan dimasukkan ke *input layer*, diteruskan ke *hidden layers* dengan bobot (weights) tertentu dan fungsi aktivasi ReLU, lalu menghasilkan output.
4.  **Denormalisasi:** Output tersebut dikembalikan ke bentuk Rupiah asli.

> **Asumsi Hasil Keluaran Model (Estimasi Harga): Rp 450.000.000**

---

## Langkah 2: Perhitungan Uang Muka (DP) & Plafon Kredit
Setelah harga didapatkan, sistem menghitung komponen hutang:

*   **Menghitung DP (Uang Muka)**
    *   Rumus: `Harga Prediksi × Persentase DP`
    *   Perhitungan: `Rp 450.000.000 × 20%`
    *   **Hasil DP = Rp 90.000.000**

*   **Menghitung Plafon Kredit (Pokok Hutang ke Bank)**
    *   Rumus: `Harga Prediksi - DP`
    *   Perhitungan: `Rp 450.000.000 - Rp 90.000.000`
    *   **Hasil Plafon = Rp 360.000.000**

---

## Langkah 3: Perhitungan Cicilan KPR per Bulan
Sistem menggunakan rumus Bunga Anuitas standar bank untuk menghitung KPR *fixed rate*.
Rumus Anuitas: **Cicilan = P × (r × (1 + r)^n) / ((1 + r)^n - 1)**

Di mana:
*   `P` = Plafon Kredit = Rp 360.000.000
*   `r` = Bunga per bulan = 8% / 12 = 0.08 / 12 = 0.006666...
*   `n` = Total bulan (Tenor) = 15 Tahun × 12 bulan = 180 bulan

**Proses Penyelesaian Matematika:**
1.  `(1 + r)^n` = `(1 + 0.006666...)^180` ≈ `3.30692`
2.  `P × r` = `360.000.000 × 0.006666...` = `2.400.000`
3.  `Pembilang` = `2.400.000 × 3.30692` ≈ `7.936.608`
4.  `Penyebut` = `3.30692 - 1` = `2.30692`
5.  `Cicilan` = `7.936.608 / 2.30692` ≈ **Rp 3.440.348 / bulan**

---

## Langkah 4: Analisis Kelayakan (Debt Service Ratio / DSR)
DSR digunakan untuk melihat kemampuan bayar. Bank umumnya mengizinkan rasio maksimal di angka 30%.
Rumus: **DSR = ((Cicilan KPR Baru + Cicilan Eksisting) / Penghasilan Bulanan) × 100**

**Proses Penyelesaian:**
1.  `Total Cicilan` = `Rp 3.440.348 (KPR)` + `Rp 1.500.000 (Eksisting)` = `Rp 4.940.348`
2.  `Rasio` = `(Rp 4.940.348 / Rp 10.000.000) × 100`
3.  **Hasil DSR = 49.4%**

---

## Langkah 5: Penentuan Status Kelayakan
Sistem ini menggunakan logika bersyarat (IF-ELSE) terhadap nilai DSR dengan 3 ambang batas:

*   **< 30%** : Status **LAYAK**
*   **30% - 40%** : Status **PERTIMBANGKAN KEMBALI**
*   **> 40%** : Status **TIDAK LAYAK**

Karena DSR pada kasus di atas adalah **49.4%** (Lebih besar dari 40%), maka output akhir di layar akan menjadi:
*   **Status Kelayakan:** TIDAK LAYAK
*   **Pesan Saran:** "Rasio cicilan terhadap penghasilan Anda sebesar 49.4%, jauh melebihi batas aman DSR 30%. Disarankan untuk melunasi hutang eksisting, menambah uang muka, atau memilih unit yang lebih terjangkau."
