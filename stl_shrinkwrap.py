#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# STL ShrinkWrap — Copyright (C) 2026 the STL ShrinkWrap authors.
# Dieses Programm benutzt PyMeshLab (GPL-3.0) und steht daher unter GPL-3.0.
# Siehe LICENSE und THIRD_PARTY_NOTICES.md.
"""
STL ShrinkWrap — kleine Desktop-App zum Alpha-Wrappen von STL-Dateien mit PyMeshLab.

Zwei Betriebsmodi in EINER Datei:
  1) GUI-Modus  (Standard):  python stl_shrinkwrap.py
  2) Worker-Modus (intern):  python stl_shrinkwrap.py --worker <in> <out> <alpha>

Die GUI startet sich selbst im Worker-Modus als Unterprozess. Dadurch bleibt die
Oberflaeche fluessig (die schwere CGAL-Berechnung blockiert nichts) und es
funktioniert identisch, egal ob als .py-Skript oder als gebaute .exe (PyInstaller).

Sprache (DE/EN): Umschalter im Fenster. Startsprache = Datei 'language.txt' neben
dem Skript (Inhalt 'de' oder 'en'), sonst Umgebungsvariable STLSW_LANG, sonst
Betriebssystem-Sprache, sonst Englisch.
"""

import sys
import os
import time


# ---------------------------------------------------------------------------
# Uebersetzungen
# ---------------------------------------------------------------------------
TR = {
    "de": {
        "title": "STL ShrinkWrap — Alpha Wrap",
        "input": "Eingabe-STL:",
        "output": "Ausgabe-STL:",
        "browse": "Durchsuchen…",
        "save_as": "Speichern unter…",
        "alpha": "Alpha-Faktor:",
        "alpha_hint": "  kleiner = mehr Details · größer = stärker geschrumpft",
        "start": "Shrink-Wrap starten",
        "ready": "Bereit.",
        "starting": "Starte…",
        "lang_label": "Sprache:",
        "dlg_open_title": "STL-Datei wählen",
        "dlg_save_title": "Ausgabedatei",
        "ft_stl": "STL-Dateien",
        "ft_all": "Alle Dateien",
        "phase_import": "Lade PyMeshLab…",
        "phase_load": "Lese STL-Datei…",
        "phase_wrap": "Berechne Alpha-Wrap… (das kann dauern)",
        "phase_save": "Speichere Ergebnis…",
        "reading_faces": "Lese STL… (%s Dreiecke)",
        "running": "Berechnung läuft … (läuft seit %s)",
        "done": "Fertig ✔  %s",
        "total_time": "Gesamtdauer: %s",
        "failed": "Abgebrochen / Fehler",
        "err_title": "Fehler",
        "err_wrap_title": "Fehler beim Wrappen",
        "err_input": "Bitte eine gültige Eingabe-STL wählen.",
        "err_output": "Bitte eine Ausgabedatei angeben.",
        "err_alpha_nan": "Alpha-Faktor muss eine Zahl sein.",
        "err_alpha_pos": "Alpha-Faktor muss größer als 0 sein.",
        "err_start": "Konnte Berechnung nicht starten:\n%s",
        "err_unexpected": "Der Berechnungsprozess wurde unerwartet beendet (Code %s).",
        "err_notinstalled": "PyMeshLab konnte nicht geladen werden. "
                            "Bitte 'pip install pymeshlab' ausführen.",
        "err_loadfail": "Die Datei konnte nicht als STL geladen werden. "
                        "Ist sie beschädigt oder kein gültiges STL-Format?",
        "err_empty": "Die Datei enthält keine gültige 3D-Geometrie (0 Dreiecke). "
                     "Ist es wirklich eine STL-Datei?",
    },
    "en": {
        "title": "STL ShrinkWrap — Alpha Wrap",
        "input": "Input STL:",
        "output": "Output STL:",
        "browse": "Browse…",
        "save_as": "Save as…",
        "alpha": "Alpha factor:",
        "alpha_hint": "  smaller = more detail · larger = shrunk more aggressively",
        "start": "Start shrink-wrap",
        "ready": "Ready.",
        "starting": "Starting…",
        "lang_label": "Language:",
        "dlg_open_title": "Choose STL file",
        "dlg_save_title": "Output file",
        "ft_stl": "STL files",
        "ft_all": "All files",
        "phase_import": "Loading PyMeshLab…",
        "phase_load": "Reading STL file…",
        "phase_wrap": "Computing alpha wrap… (this can take a while)",
        "phase_save": "Saving result…",
        "reading_faces": "Reading STL… (%s triangles)",
        "running": "Working … (elapsed %s)",
        "done": "Done ✔  %s",
        "total_time": "Total time: %s",
        "failed": "Cancelled / error",
        "err_title": "Error",
        "err_wrap_title": "Shrink-wrap failed",
        "err_input": "Please choose a valid input STL.",
        "err_output": "Please specify an output file.",
        "err_alpha_nan": "Alpha factor must be a number.",
        "err_alpha_pos": "Alpha factor must be greater than 0.",
        "err_start": "Could not start the computation:\n%s",
        "err_unexpected": "The computation process terminated unexpectedly (code %s).",
        "err_notinstalled": "PyMeshLab could not be loaded. "
                            "Please run 'pip install pymeshlab'.",
        "err_loadfail": "The file could not be loaded as STL. "
                        "Is it corrupt or not a valid STL file?",
        "err_empty": "The file contains no valid 3D geometry (0 triangles). "
                     "Is it really an STL file?",
    },
}


def _base_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.dirname(os.path.abspath(sys.argv[0]))


def detect_lang():
    """Startsprache bestimmen: language.txt > STLSW_LANG > OS-Sprache > en."""
    try:
        cand = os.path.join(_base_dir(), "language.txt")
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                v = f.read().strip().lower()[:2]
            if v in TR:
                return v
    except Exception:  # noqa: BLE001
        pass
    v = (os.environ.get("STLSW_LANG", "") or "").strip().lower()[:2]
    if v in TR:
        return v
    try:
        import locale
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("de"):
            return "de"
    except Exception:  # noqa: BLE001
        pass
    return "en"


# ---------------------------------------------------------------------------
def _alpha_wrap(pymeshlab, ms, alpha):
    """Alpha-Wrap aufrufen — versionsrobust ueber PyMeshLab-Versionen hinweg.

    - PyMeshLab <= 2023.12:  generate_alpha_wrap(alpha_fraction=<float>)
                             (alpha_fraction = Anteil der BBox-Diagonale)
    - PyMeshLab >= 2024/2025: generate_alpha_wrap(alpha=PercentageValue(<prozent>))
                             (alpha als Prozent-Objekt; 0.005 -> 0.5 %)
    """
    try:
        ms.generate_alpha_wrap(alpha_fraction=alpha)
        return
    except Exception:  # noqa: BLE001
        pass
    pct_cls = (getattr(pymeshlab, "PercentageValue", None)
               or getattr(pymeshlab, "Percentage", None))
    if pct_cls is None:
        # Letzter Versuch: roher Wert (falls eine ganz andere API vorliegt)
        ms.generate_alpha_wrap(alpha=alpha)
        return
    ms.generate_alpha_wrap(alpha=pct_cls(alpha * 100.0))


# ---------------------------------------------------------------------------
# WORKER-MODUS  (laeuft headless, gibt Fortschritt zeilenweise auf stdout aus)
# Fehler werden als sprachneutrale Codes gemeldet (ERRCODE <name>), die die GUI
# uebersetzt. Unerwartete Ausnahmen kommen als roher Text (ERROR ...).
# ---------------------------------------------------------------------------
def run_worker(in_path, out_path, alpha):
    def emit(line):
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    try:
        emit("PHASE import")
        import pymeshlab  # erst hier importieren -> schnelle, leichte GUI
    except Exception:  # noqa: BLE001
        emit("ERRCODE notinstalled")
        return 1

    import tempfile
    import shutil

    # PyMeshLab kommt unter Windows mit Nicht-ASCII-Pfaden (Umlaute) nicht
    # zuverlaessig zurecht -> ueber ASCII-Temp-Dateien laden/speichern.
    tmpdir = tempfile.mkdtemp(prefix="stlsw_")
    tmp_in = os.path.join(tmpdir, "in.stl")
    tmp_out = os.path.join(tmpdir, "out.stl")
    try:
        try:
            emit("PHASE load")
            shutil.copyfile(in_path, tmp_in)
            ms = pymeshlab.MeshSet()
            try:
                ms.load_new_mesh(tmp_in)
            except Exception:  # noqa: BLE001
                emit("ERRCODE loadfail")
                return 1

            faces = ms.current_mesh().face_number()
            emit("FACES %d" % faces)
            if faces == 0:
                emit("ERRCODE empty")
                return 1

            emit("PHASE wrap")
            _alpha_wrap(pymeshlab, ms, float(alpha))

            emit("PHASE save")
            ms.save_current_mesh(tmp_out)
            out_dir = os.path.dirname(os.path.abspath(out_path))
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            shutil.move(tmp_out, out_path)

            emit("DONE")
            return 0
        except Exception as e:  # noqa: BLE001
            emit("ERROR " + repr(e))
            return 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# GUI-MODUS
# ---------------------------------------------------------------------------
def run_gui():
    import threading
    import queue
    import subprocess
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    lang = [detect_lang()]

    def T(key):
        return TR[lang[0]].get(key, TR["en"].get(key, key))

    def fmt(sec):
        if sec is None or sec < 0:
            return "--:--"
        sec = int(round(sec))
        return "%02d:%02d" % (sec // 60, sec % 60)

    state = {
        "proc": None,
        "reader": None,
        "q": queue.Queue(),
        "start": 0.0,
        "phase": "",
        "running": False,
    }

    root = tk.Tk()
    root.title(T("title"))
    try:
        _icon = os.path.join(_base_dir(), "icon.ico")
        if os.path.exists(_icon):
            root.iconbitmap(_icon)
    except Exception:  # noqa: BLE001
        pass
    root.minsize(580, 0)
    try:
        root.tk.call("tk", "scaling", 1.2)
    except Exception:  # noqa: BLE001
        pass

    pad = {"padx": 10, "pady": 5}
    frm = ttk.Frame(root, padding=12)
    frm.grid(sticky="nsew")
    root.columnconfigure(0, weight=1)
    frm.columnconfigure(1, weight=1)

    in_var = tk.StringVar()
    out_var = tk.StringVar()
    alpha_var = tk.StringVar(value="0.005")

    def pick_in():
        p = filedialog.askopenfilename(
            title=T("dlg_open_title"),
            filetypes=[(T("ft_stl"), "*.stl"), (T("ft_all"), "*.*")])
        if p:
            in_var.set(p)
            if not out_var.get():
                stem, _ = os.path.splitext(p)
                out_var.set(stem + " wrap.stl")

    def pick_out():
        init = out_var.get() or (os.path.splitext(in_var.get())[0] + " wrap.stl"
                                 if in_var.get() else "")
        p = filedialog.asksaveasfilename(
            title=T("dlg_save_title"),
            defaultextension=".stl",
            initialfile=os.path.basename(init) if init else "wrap.stl",
            initialdir=os.path.dirname(init) if init else None,
            filetypes=[(T("ft_stl"), "*.stl")])
        if p:
            out_var.set(p)

    # --- Kopfzeile mit Sprach-Umschalter ---
    top = ttk.Frame(frm)
    top.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 2))
    lang_combo = ttk.Combobox(top, state="readonly", width=10,
                              values=["Deutsch", "English"])
    lang_combo.current(0 if lang[0] == "de" else 1)
    lang_combo.pack(side="right")
    lbl_lang = ttk.Label(top, text=T("lang_label"))
    lbl_lang.pack(side="right", padx=(0, 6))

    # --- Eingabe ---
    lbl_in = ttk.Label(frm, text=T("input"))
    lbl_in.grid(row=1, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=in_var).grid(row=1, column=1, sticky="ew", **pad)
    btn_in = ttk.Button(frm, text=T("browse"), command=pick_in)
    btn_in.grid(row=1, column=2, **pad)

    # --- Ausgabe ---
    lbl_out = ttk.Label(frm, text=T("output"))
    lbl_out.grid(row=2, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=out_var).grid(row=2, column=1, sticky="ew", **pad)
    btn_out = ttk.Button(frm, text=T("save_as"), command=pick_out)
    btn_out.grid(row=2, column=2, **pad)

    # --- Alpha ---
    lbl_alpha = ttk.Label(frm, text=T("alpha"))
    lbl_alpha.grid(row=3, column=0, sticky="w", **pad)
    alpha_row = ttk.Frame(frm)
    alpha_row.grid(row=3, column=1, columnspan=2, sticky="ew", **pad)
    ttk.Spinbox(alpha_row, textvariable=alpha_var, from_=0.0005, to=0.5,
                increment=0.0005, width=10, format="%.4f").pack(side="left")
    lbl_hint = ttk.Label(alpha_row, text=T("alpha_hint"), foreground="#666")
    lbl_hint.pack(side="left")

    # --- Laufanzeige ---
    bar = ttk.Progressbar(frm, mode="indeterminate")
    bar.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)

    status_var = tk.StringVar(value=T("ready"))
    ttk.Label(frm, textvariable=status_var).grid(row=5, column=0, columnspan=3,
                                                 sticky="w", **pad)
    time_var = tk.StringVar(value="")
    ttk.Label(frm, textvariable=time_var, foreground="#444").grid(
        row=6, column=0, columnspan=3, sticky="w", **pad)

    start_btn = ttk.Button(frm, text=T("start"))
    start_btn.grid(row=7, column=0, columnspan=3, sticky="ew", **pad)

    def relabel():
        root.title(T("title"))
        lbl_lang.config(text=T("lang_label"))
        lbl_in.config(text=T("input"))
        lbl_out.config(text=T("output"))
        lbl_alpha.config(text=T("alpha"))
        lbl_hint.config(text=T("alpha_hint"))
        btn_in.config(text=T("browse"))
        btn_out.config(text=T("save_as"))
        start_btn.config(text=T("start"))
        if not state["running"]:
            status_var.set(T("ready"))

    def on_lang(_evt=None):
        lang[0] = "de" if lang_combo.current() == 0 else "en"
        relabel()

    lang_combo.bind("<<ComboboxSelected>>", on_lang)

    def reader_thread(proc, q):
        try:
            for line in proc.stdout:
                q.put(line.rstrip("\n"))
        finally:
            q.put("__EOF__")

    def start():
        in_path = in_var.get().strip()
        out_path = out_var.get().strip()
        if not in_path or not os.path.isfile(in_path):
            messagebox.showerror(T("err_title"), T("err_input"))
            return
        if not out_path:
            messagebox.showerror(T("err_title"), T("err_output"))
            return
        try:
            alpha = float(alpha_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror(T("err_title"), T("err_alpha_nan"))
            return
        if alpha <= 0:
            messagebox.showerror(T("err_title"), T("err_alpha_pos"))
            return

        state["start"] = time.time()

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--worker", in_path, out_path, repr(alpha)]
        else:
            # -s: kein User-Site-Verzeichnis · -E: PYTHON*-Umgebungsvariablen
            # ignorieren -> der Worker nutzt GARANTIERT das mitgelieferte
            # PyMeshLab und nicht eine evtl. neuere Version auf dem Host-System.
            cmd = [sys.executable, "-s", "-E", os.path.abspath(__file__),
                   "--worker", in_path, out_path, repr(alpha)]

        creationflags = 0
        if os.name == "nt":
            creationflags = 0x08000000  # CREATE_NO_WINDOW

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=creationflags)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(T("err_title"), T("err_start") % e)
            return

        state["proc"] = proc
        state["q"] = queue.Queue()
        t = threading.Thread(target=reader_thread, args=(proc, state["q"]),
                             daemon=True)
        t.start()
        state["reader"] = t
        state["running"] = True
        state["phase"] = "start"

        start_btn.config(state="disabled")
        lang_combo.config(state="disabled")
        bar.start(12)
        status_var.set(T("starting"))
        root.after(100, tick)

    def finish(success, message):
        state["running"] = False
        start_btn.config(state="normal")
        lang_combo.config(state="readonly")
        bar.stop()
        if success:
            elapsed = time.time() - state["start"]
            status_var.set(T("done") % message)
            time_var.set(T("total_time") % fmt(elapsed))
        else:
            status_var.set(T("failed"))
            time_var.set("")
            messagebox.showerror(T("err_wrap_title"), message)

    def tick():
        if not state["running"]:
            return
        q = state["q"]
        done = False
        try:
            while True:
                line = q.get_nowait()
                if line == "__EOF__":
                    rc = state["proc"].poll()
                    if rc not in (0, None) and state["phase"] != "done":
                        finish(False, T("err_unexpected") % rc)
                        return
                    done = True
                    break
                elif line.startswith("PHASE "):
                    ph = line[6:].strip()
                    state["phase"] = ph
                    status_var.set(T("phase_" + ph))
                elif line.startswith("FACES "):
                    status_var.set(T("reading_faces") % line[6:].strip())
                elif line == "DONE":
                    state["phase"] = "done"
                    finish(True, os.path.basename(out_var.get()))
                    return
                elif line.startswith("ERRCODE "):
                    state["phase"] = "error"
                    finish(False, T("err_" + line[8:].strip()))
                    return
                elif line.startswith("ERROR "):
                    state["phase"] = "error"
                    finish(False, line[6:].strip())
                    return
        except queue.Empty:
            pass

        if done:
            return

        elapsed = time.time() - state["start"]
        time_var.set(T("running") % fmt(elapsed))
        root.after(200, tick)

    start_btn.config(command=start)
    root.mainloop()


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--worker":
        _, _, in_path, out_path, alpha = sys.argv[:5]
        sys.exit(run_worker(in_path, out_path, alpha))
    else:
        run_gui()


if __name__ == "__main__":
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except Exception:  # noqa: BLE001
        pass
    main()
