# 🚘 Mr.Isuzu - Sales Assistant

Proyek ini adalah aplikasi asisten virtual berbasis AI untuk membantu pelanggan memahami dan membandingkan mobil-mobil Isuzu secara interaktif. Asisten ini dapat menjawab berbagai pertanyaan seperti:

- Menampilkan jumlah dan jenis mobil yang tersedia
- Menjelaskan spesifikasi dan fitur unggulan masing-masing mobil
- Memberikan perbandingan antar mobil lengkap dengan ringkasan
- Menampilkan gambar mobil dan memberikan akses download brosur
- Menggunakan bahasa yang sopan dan informatif dalam Bahasa Indonesia

## Fitur yang Dipenuhi
- [x] Mengetahui jumlah produk
- [x] Menjelaskan spesifikasi produk
- [x] Memberikan perbandingan antar produk
- [x] Menyertakan sumber brosur tiap mobil
- [x] Menampilkan gambar mobil

## Tools & Teknologi yang Digunakan
- Streamlit — untuk antarmuka pengguna
- Google Gemini API — untuk menjawab pertanyaan berbasis konteks
- HuggingFace Sentence Transformers — untuk membuat embedding semantik
- FAISS — untuk pencarian berbasis similarity
- Python 3.10+

## Struktur Dataset
Dataset disusun secara manual dan terdiri dari beberapa field berikut:
- `nama`: nama mobil
- `spesifikasi`: penjelasan teknis
- `keunggulan`: kelebihan dan fitur utama
- `perbedaan`: detail untuk perbandingan antar mobil
- `gambar`: path lokal gambar mobil
- `brosur`: path lokal brosur
- `url brosur`: Link menuju brosur mobil

## Cara Menjalankan Aplikasi
1. Clone repository ini dan masuk ke folder proyek.
2. Install semua dependency:
   pip install -r requirements.txt
3. Jalankan aplikasi menggunakan Streamlit:
   streamlit run app.py
   
## Dokumentasi Test Cases
📄 [Testing Documentation](TESTING.md)

### ✍️ Catatan Pengembang

Proyek ini dirancang dengan fokus pada fungsionalitas, skalabilitas, dan kemudahan pengembangan ke depan. Beberapa pendekatan teknis yang digunakan:

- **Strategi pencarian gabungan**: Sistem memprioritaskan pencocokan nama mobil secara eksplisit terlebih dahulu. Jika tidak ditemukan, akan digunakan pencarian berbasis embedding menggunakan FAISS untuk menangani variasi input dari pengguna.

- **Prompt engineering**: Instruksi untuk model Gemini ditulis agar dapat menyesuaikan konteks pertanyaan pengguna, baik untuk pertanyaan umum, spesifik produk, maupun perbandingan. Format jawaban diatur agar tetap informatif dan mudah dibaca.

- **Modularitas**: Struktur aplikasi disusun agar proses embedding, pemanggilan model, dan tampilan UI dapat dipisah jika ingin dikembangkan lebih lanjut.

- **Efisiensi sumber daya**: Seluruh sistem dibangun menggunakan layanan gratis dan dijalankan secara lokal. Hal ini mempertimbangkan keterbatasan lingkungan pengembangan sambil menjaga fungsionalitas utama tetap berjalan dengan baik.

- **Kesiapan ekspansi**: Sistem ini memungkinkan penambahan data baru (mobil, spesifikasi, gambar, dan brosur) tanpa perlu mengubah struktur utama aplikasi.

Tujuan dari pendekatan ini adalah agar aplikasi tidak hanya dapat digunakan pada skala kecil, tetapi juga cukup fleksibel untuk dikembangkan lebih lanjut sesuai kebutuhan.


---
Dibuat oleh: Muhamad Dwriziqy Wimbassa

Tahun: 2025
