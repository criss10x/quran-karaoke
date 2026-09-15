# quran-karaoke

Satu video masuk → satu video keluar: murottal + subtitle Al-Quran
(tulisan Arab bersambung RTL + terjemahan Indonesia) dibakar ke dalam video.

```bash
python3 -m qk.cli video.mp4 --surah 112 --qari 05           # Al-Ikhlas, al-Afasy
python3 -m qk.cli video.mp4 --surah 55 --aya 1-13 --qari 03 # Ar-Rahman 1-13, as-Sudais
python3 -m qk.cli --daftar-qari                              # daftar qari yang didukung
```

| opsi | default | keterangan |
|---|---|---|
| `--surah N` | — | nomor surah 1-114 (wajib) |
| `--aya A-B` | seluruh surah | rentang ayat |
| `--qari QQ` | `03` | lihat `--daftar-qari` |
| `--layout` | `portrait` | `portrait` / `landscape` / `square` |
| `--fit` | `audio` | `audio` = panjang ikut murottal (frame terakhir ditahan) |
| `--no-arti` `--no-header` | off | matikan lapisan teks |
| `--gelap F` | `0.62` | peredup video, 0-1 (1 = biarkan terang) |
| `--crf` `--preset` `--scale` | `20` `medium` `1.0` | kualitas & ukuran |

Output: `output/<slug>.mp4` + `work/<video>/sNNN_.../` (`.ass` + `murottal.mp3`, untuk re-render).

## Dari mana timing per katanya

equran.id memberi teks + audio, tapi **bukan** timing. Timing per kata diambil dari dataset
[quran-align](https://github.com/cpfair/quran-align) (CC-BY-4.0, resolusi 10 ms) yang meng-index
kata ke teks Tanzil uthmani. Dua rekaman equran **byte-identik** (dibuktikan lewat MD5 PCM hasil
decode) dengan dataset ini, jadi timing-nya presisi asli:

- `05` Mishari Rashid al-Afasy == `Alafasy_128kbps`
- `03` Abdurrahman as-Sudais == `Abdurrahmaan_As-Sudais_192kbps`

Qari lain tetap jalan, tapi timing-nya dibagi rata antar kata (`bagi rata (perkiraan)`).

Catatan: file Sudais di rilis resmi punya ~150 kB teks crash-log menempel di depan JSON-nya;
loader melewatinya, arraynya sendiri utuh (6236 ayat).

Cache di `~/.cache/quran-karaoke/` (surah JSON, tanzil, quran-align, audio) — re-render tidak
men-download ulang. Font Amiri Quran di-vendor di `fonts/`.

Butuh `ffmpeg` dengan libass + HarfBuzz (untuk shaping Arab/RTL).

## Tulisan Arab putus-putus? Baca ini dulu

Penyebabnya hampir selalu satu angka: `Spacing` bukan `0.0` di style Arab. libass lalu
berhenti pakai complex shaper HarfBuzz dan menggambar tiap huruf terpisah, jadi
sambungan kursifnya putus (`qk/subtitles.py` sudah dipatok `spacing=0.0`). Latin tidak
terpengaruh, itu sebabnya kelihatan seperti masalah font.

Jangan percaya re-render bersih — buktikan di file yang benar-benar dikirim:

```bash
python3 scripts/verify_arabic_joins.py \
  --ass work/user_video/s004_148_05/an-nisa-05.ass \
  --video output/kris_annisa_148.mp4 --fonts fonts --times 1 7 11
```

Exit 0 = video terkirim cocok dengan style benar di **semua** baris. Detail metode,
angka terukurnya, dan cara membuktikan check-nya bisa gagal: `docs/verifying-arabic-joins.md`.

Cek cepat: `python3 tests/test_qalign.py && python3 tests/test_emit.py`
