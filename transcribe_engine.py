"""Ata Studio — yazıya dökme motoru (faster-whisper).

Qt'ye bağımlı değildir:
  • worker_main()  → ayrı süreçte çalışır (atastudio.py --transcribe-worker ...)
                     stdout'a satır başına bir JSON olayı yazar, iptal bayrağı dosyasını ve ana süreci izler.
  • build_paragraphs / render_text / render_srt / save_docx → saf yardımcılar.
"""
import os
import sys
import json
import threading

# Kalite → (model, beam_size, yaklaşık indirme boyutu)
QUALITY_MODELS = {
    "Hızlı":    ("base",   1, "~145 MB"),
    "Dengeli":  ("small",  3, "~480 MB"),
    "Hassas":   ("medium", 3, "~1,5 GB"),
}
PARAGRAPH_GAP = 1.5      # sn — bundan uzun sessizlikte yeni paragraf
PARAGRAPH_SOFT_CHARS = 700   # kesintisiz konuşmada cümle sonunda böl


# ── Saf yardımcılar ──────────────────────────────────────────────────────────
def fmt_hms(sec):
    sec = max(0, int(sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def fmt_srt_time(sec):
    ms = int(round(max(0.0, sec) * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def build_paragraphs(segments, gap=PARAGRAPH_GAP):
    """segments: [(start, end, text)] → [(paragraf_başlangıcı, metin)]"""
    paras = []          # [start, [parçalar]]
    prev_end = None
    for start, end, text in segments:
        text = text.strip()
        if not text:
            continue
        new_para = not paras
        if prev_end is not None and start - prev_end > gap:
            new_para = True
        if (not new_para and sum(len(t) for t in paras[-1][1]) > PARAGRAPH_SOFT_CHARS
                and paras[-1][1][-1].rstrip().endswith((".", "!", "?", "…"))):
            new_para = True
        if new_para:
            paras.append([start, []])
        paras[-1][1].append(text)
        prev_end = end
    return [(s, " ".join(parts)) for s, parts in paras]


def render_text(segments, timestamps=False, gap=PARAGRAPH_GAP):
    out = []
    for start, text in build_paragraphs(segments, gap):
        out.append(f"[{fmt_hms(start)}] {text}" if timestamps else text)
    return "\n\n".join(out)


def render_srt(segments):
    blocks = []
    n = 0
    for start, end, text in segments:
        text = text.strip()
        if not text:
            continue
        n += 1
        blocks.append(f"{n}\n{fmt_srt_time(start)} --> {fmt_srt_time(end)}\n{text}\n")
    return "\n".join(blocks)


def save_docx(path, text):
    from docx import Document
    doc = Document()
    for block in text.replace("\r\n", "\n").split("\n\n"):
        block = block.strip("\n")
        if block.strip():
            doc.add_paragraph(block)
    doc.save(path)


# ── Ayrı süreç: worker ───────────────────────────────────────────────────────
def worker_main(args):
    """args: [ses_dosyası, dil('tr'|'en'|'auto'), model, beam_size, iptal_bayrağı_yolu, ana_pid]"""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    # Pencereli exe'de stdout/stderr None olabilir
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            setattr(sys, name, open(os.devnull, "w"))

    def emit(**kw):
        try:
            os.write(1, (json.dumps(kw, ensure_ascii=True) + "\n").encode("ascii"))
        except OSError:
            pass

    cancel = threading.Event()
    cancel_flag = args[4] if len(args) > 4 else ""
    parent_pid  = int(args[5]) if len(args) > 5 else 0

    def parent_alive():
        if not parent_pid or sys.platform != "win32":
            return True
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x100000, False, parent_pid)   # SYNCHRONIZE
            if not h:
                return False
            try:
                return k32.WaitForSingleObject(h, 0) != 0     # 0 = sonlanmış
            finally:
                k32.CloseHandle(h)
        except Exception:
            return True

    def watch():
        # İptal bayrağı dosyası ya da ebeveyn (ana uygulama) kapandıysa dur.
        # (stdin'de bloke okuma kullanılmaz: native kütüphane import'unu çökertiyor)
        while not cancel.is_set():
            if (cancel_flag and os.path.exists(cancel_flag)) or not parent_alive():
                cancel.set()
                return
            cancel.wait(0.5)

    threading.Thread(target=watch, daemon=True).start()

    stage = "init"
    try:
        audio, lang, size, beam = args[0], args[1], args[2], int(args[3])
        size_txt = next((v[2] for v in QUALITY_MODELS.values() if v[0] == size), "")

        # Modeli bul / indir
        stage = "model"
        from faster_whisper.utils import download_model
        try:
            model_path = download_model(size, local_files_only=True)
        except Exception:
            emit(t="status",
                 m=f"Model indiriliyor, bu işlem bir kez yapılır ({size_txt})...")
            model_path = download_model(size)
        if cancel.is_set():
            emit(t="cancelled")
            return

        emit(t="status", m="Model yükleniyor...")
        from faster_whisper import WhisperModel
        threads = max(2, (os.cpu_count() or 4) // 2)
        model = WhisperModel(model_path, device="cpu", compute_type="int8",
                             cpu_threads=threads)

        stage = "transcribe"
        emit(t="status", m="Yazıya dökülüyor...")
        segments, info = model.transcribe(
            audio,
            language=None if lang == "auto" else lang,
            beam_size=beam,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        emit(t="info", dur=float(info.duration), lang=info.language,
             lp=float(info.language_probability))
        for seg in segments:          # tembel: bellekte biriktirmez
            if cancel.is_set():
                emit(t="cancelled")
                return
            emit(t="seg", s=float(seg.start), e=float(seg.end), x=seg.text.strip())
        emit(t="done")
    except Exception as e:
        kind = "net" if stage == "model" else "other"
        emit(t="err", k=kind, m=f"{type(e).__name__}: {e}")

