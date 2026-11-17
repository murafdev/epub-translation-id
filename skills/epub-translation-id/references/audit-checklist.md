# Checklist Audit Terjemahan

Gunakan checklist ini setelah draf pertama selesai. Audit dilakukan per kelompok chapter, bukan hanya sekali di akhir.

## A. Audit paragraf

Untuk setiap paragraf:
- [ ] Subjek dan objek benar.
- [ ] Pronomina “dia/ia/mereka” merujuk pada orang yang sama dengan sumber.
- [ ] Negasi tidak terbalik (tidak/bukan/belum/tanpa).
- [ ] Modalitas benar: harus, perlu, bisa, mungkin, pasti, seharusnya.
- [ ] Sebab-akibat benar: karena, sehingga, jadi, lalu.
- [ ] Tidak ada informasi yang hilang atau ditambahkan.
- [ ] Idiom diterjemahkan sesuai maksud, bukan kata per kata.
- [ ] Nama, gelar, angka, dan tempat tidak berubah.
- [ ] Dialog tetap milik penutur yang benar.

## B. Audit kalimat

- [ ] Pecah kalimat sumber dan terjemahan; bandingkan jumlah klausa utama.
- [ ] Pertanyaan tetap pertanyaan; perintah tetap perintah; ejekan tetap ejekan.
- [ ] “If anything” → malah/sebaliknya, bukan “kalau ada”.
- [ ] “If nothing else” → setidaknya.
- [ ] “Must have” → pasti, bukan mungkin.
- [ ] “Would I?” → apakah aku akan melakukannya, bukan haruskah.
- [ ] “Getting the boot” → diusir, bukan ditendang.
- [ ] “Settle the score” → menyelesaikan perhitungan lama.
- [ ] “Make good on an investment” → mendapatkan imbal hasil.
- [ ] “Talked myself up” → membanggakan diri.
- [ ] “You do!” → kau memang …, bukan sekadar hinaan.
- [ ] “Mid-thirties” → pertengahan tiga puluhan.
- [ ] “One another again” → bertemu lagi, bukan saling menguntungkan.
- [ ] “Never see one another again” tidak diterjemahkan menjadi “tidak saling menguntungkan”.

## C. Audit nama dan istilah

Buat daftar istilah tetap untuk buku yang sedang diterjemahkan. Contoh kategori (sesuaikan dengan dunia dan gaya buku):

| Sumber | Terjemahan | Catatan |
|---|---|---|
| demon | iblis | konsisten di seluruh buku |
| beastfolk | beastfolk | pertahankan istilah |
| magic armor | armor sihir | |
| mercenary band | kelompok tentara bayaran | |
| church | gereja | |
| holy country | negara suci | |
| temple knights | ksatria kuil | |
| blessed child | anak terberkati | |
| nama tempat | tetap | jangan diterjemahkan tanpa alasan |
| nama tokoh | tetap | jangan diterjemahkan tanpa alasan |

Jangan memaksakan istilah dari buku lain. Periksa variasi ejaan nama tokoh/tempat: buat daftar sendiri dan pastikan satu nama hanya punya satu ejaan.

## D. Audit teknis

- [ ] Jumlah baris `src` = jumlah baris `id` untuk setiap section.
- [ ] Penanda `{i}...{/i}` dan `{b}...{/b}` tidak hilang atau berubah pasangan.
- [ ] Jumlah `<img>` di XHTML final = sumber.
- [ ] Setiap gambar inline berada di indeks paragraf yang benar (dicek validator).
- [ ] Hash gambar final = hash asli.
- [ ] Tidak ada gambar yang masih memakai `height:100%`.
- [ ] Semua XHTML/XML valid.
- [ ] Semua link internal ada.
- [ ] `mimetype` adalah entri pertama dan tidak dikompresi.
- [ ] Cover tampil (bukan SVG kosong).
- [ ] Tidak ada gambar yang hanya ada di folder tetapi tidak direferensikan.
- [ ] `validate_epub.py` keluar dengan kode 0 dan `validation.txt` tidak berisi issue.
- [ ] TOC/NCX memakai judul terjemahan.
- [ ] Label halaman gambar (Color Inserts, Title Page, Copyrights, Character Design) sudah diterjemahkan.

## E. Audit akhir

- [ ] Tidak ada sisa kata fungsi Inggris yang tidak disengaja.
- [ ] About the Author, Newsletter, afterword, dan halaman teks tambahan sudah diterjemahkan.
- [ ] Halaman promosi/watermark sudah diterjemahkan lewat `auxiliary.json` atau padanan bawaan.
- [ ] Tidak ada paragraf kosong atau duplikat yang tidak berasal dari sumber.
- [ ] Tidak ada scene break yang hilang.
- [ ] Jumlah chapter dan judul sesuai.
- [ ] File TXT per chapter bisa dibuka dan berisi teks lengkap.
- [ ] Perkiraan durasi TTS ada di setiap chapter dan `daftar-isi.txt`.
- [ ] Total durasi di `daftar-isi.txt` masuk akal untuk kecepatan `--wpm` yang dipakai.
- [ ] Laporan validasi ditulis.
