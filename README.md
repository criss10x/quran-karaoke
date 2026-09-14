# quran-karaoke

Satu video masuk → satu video keluar: murottal + subtitle Al-Quran bergaya karaoke
(highlight per kata, Arab + Latin + terjemahan) dibakar ke dalam video.

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
| `--no-karaoke` `--no-latin` `--no-arti` `--no-header` | off | matikan lapisan teks |
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

Cek cepat: `python3 tests/test_qalign.py`
