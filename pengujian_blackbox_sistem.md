# Pengujian Sistem (Black Box Testing)
**Sistem Pendukung Keputusan Prediksi Harga Rumah - Sapphire Residence**

Dokumen ini berisi skenario pengujian fungsionalitas sistem menggunakan metode *Black Box Testing*. Pengujian difokuskan pada *input* dan *output* sistem tanpa melihat struktur kode di dalamnya.

---

## 1. Modul Prediksi Harga & Simulasi KPR
Pengujian pada form input utama dan hasil keluaran prediksi (Halaman Utama / Index).

| No | Skenario Pengujian | Data Input (Test Data) | Hasil yang Diharapkan (Expected Result) | Status |
|:---|:---|:---|:---|:---|
| **1.1** | Submit data spesifikasi rumah dengan format yang valid dan lengkap. | Blok: A1, LB: 36, LT: 72, KT: 2, KM: 1, DP: 20%, Tenor: 15 Thn, Gaji: Rp 10 Juta, Eksisting: Rp 1.5 Juta | Sistem memproses data dan menampilkan 3 hasil prediksi harga (LBFGS, Adam, SGD) beserta perhitungan cicilan KPR dan DSR. | LULUS |
| **1.2** | Mengosongkan form yang berstatus *required* (wajib). | Form "Luas Bangunan" dikosongkan, lalu klik submit. | Browser menolak *submit* dan menampilkan peringatan (validasi HTML5). | LULUS |
| **1.3** | Menguji perhitungan DSR dengan hasil batas aman (LAYAK). | Gaji: Rp 20.000.000, Total Cicilan Baru + Eksisting < Rp 6.000.000 | Sistem menampilkan *badge* warna Hijau dengan status "LAYAK". | LULUS |
| **1.4** | Menguji perhitungan DSR dengan hasil melebihi batas DSR 30% - 40%. | Gaji: Rp 5.000.000, Total Cicilan > Rp 2.000.000 | Sistem menampilkan *badge* warna Merah dengan status "TIDAK LAYAK". | LULUS |
| **1.5** | Menginput nilai penghasilan/gaji 0 (Nol). | Gaji: 0 atau dikosongkan. | Sistem KPR tidak memproses DSR dan menampilkan status kuning "DATA TIDAK LENGKAP". | LULUS |

---

## 2. Modul Ekspor Data (Excel & PDF)
Pengujian pada fitur cetak dan ekspor laporan yang di-*generate* oleh sistem.

| No | Skenario Pengujian | Data Input (Test Data) | Hasil yang Diharapkan (Expected Result) | Status |
|:---|:---|:---|:---|:---|
| **2.1** | Tombol Ekspor Excel pada halaman Prediksi. | Klik "Export Excel" setelah hasil prediksi muncul. | Browser mengunduh file `.xlsx` berisi ringkasan spesifikasi, hasil prediksi, cicilan sesuai tenor pilihan, dan status DSR. | LULUS |
| **2.2** | Tombol Ekspor Excel pada halaman Dashboard. | Klik "Export Excel" pada halaman Dashboard. | Browser mengunduh file `.xlsx` yang memuat tabel Perbandingan Metrik Evaluasi (MAE & R2 Score) antar optimizer. | LULUS |
| **2.3** | Tombol Ekspor Excel pada halaman Analisis. | Klik "Export Excel" pada halaman Analisis. | Browser mengunduh file `.xlsx` berisi tabel Statistik Deskriptif dan persentase tipe rumah. | LULUS |
| **2.4** | Fungsi "Cetak PDF" / Print Browser. | Klik tombol "Cetak PDF". | Membuka jendela dialog *Print* bawaan browser, tombol navigasi tidak ikut tercetak (tersembunyi karena class `no-print`). | LULUS |

---

## 3. Modul Dashboard (Perbandingan Metrik)
Pengujian visualisasi data dan komparasi algoritma ANN.

| No | Skenario Pengujian | Data Input (Test Data) | Hasil yang Diharapkan (Expected Result) | Status |
|:---|:---|:---|:---|:---|
| **3.1** | Navigasi ke halaman Dashboard. | Klik menu "Dashboard" | Sistem merender halaman yang menampilkan R2 Score dan MAE dari file konfigurasi JSON secara cepat. | LULUS |
| **3.2** | Penanda otomatis "Optimizer Terbaik". | Akses Dashboard. | Sistem mampu membaca nilai metrik terbaik (misal: LBFGS) dan secara otomatis memberi label/sorotan warna Hijau pada baris tersebut. | LULUS |
| **3.3** | Merender grafik batang (Chart.js). | Akses Dashboard. | Grafik R2 Score dan MAE tampil dengan ukuran *responsive*, nilai yang tertampil sesuai dengan tabel perbandingan. | LULUS |

---

## 4. Modul Analisis Statistik
Pengujian pada halaman ringkasan data historis dan uji linear berganda.

| No | Skenario Pengujian | Data Input (Test Data) | Hasil yang Diharapkan (Expected Result) | Status |
|:---|:---|:---|:---|:---|
| **4.1** | Navigasi ke halaman Analisis. | Klik menu "Analisis". | Sistem merender tabel distribusi tipe unit dan status kelayakan data. | LULUS |
| **4.2** | Tampilan Statistik Deskriptif. | Scroll ke bagian Deskriptif. | Menampilkan perhitungan *Mean, Std Dev, Min, Max* untuk variabel Luas, Kamar, Harga KPR, dan variabel baru yaitu "Blok Kavling". | LULUS |
| **4.3** | Tabel Uji Simultan (Uji F) & Uji Parsial (Uji t). | Scroll ke bagian Analisis Inferensial. | Nilai P-Value dan koefisien ditampilkan secara rapi beserta label kesimpulan (SIGNIFIKAN / TIDAK SIGNIFIKAN). | LULUS |

---

### Kesimpulan Pengujian
Semua skenario pengujian *Black Box* untuk fungsionalitas inti Sistem Prediksi Sapphire Residence menunjukkan status **LULUS** (*Passed*). Sistem mampu menerima *input* sesuai batas (*boundary*), melakukan perhitungan bisnis (DSR & KPR) dengan benar, dan menghasilkan keluaran ekspor (Excel) yang dapat diandalkan tanpa ada fitur yang *crash* (berhenti berfungsi).
