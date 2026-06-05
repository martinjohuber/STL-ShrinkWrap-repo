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
"""

import sys
import os
import time
import json


# ---------------------------------------------------------------------------
# WORKER-MODUS  (laeuft headless, gibt Fortschritt zeilenweise auf stdout aus)
# ---------------------------------------------------------------------------
def run_worker(in_path, out_path, alpha):
    def emit(line):
        # Sofort schreiben, damit die GUI live mitlesen kann.
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    try:
        emit("PHASE import")
        import pymeshlab  # erst hier importieren -> schnelle, leichte GUI
    except Exception as e:  # noqa: BLE001
        emit("ERROR PyMeshLab ist nicht installiert oder konnte nicht geladen "
             "werden. Bitte 'pip install pymeshlab' ausfuehren.  Details: " + repr(e))
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
                emit("ERROR Die Datei konnte nicht als STL geladen werden. "
                     "Ist sie beschaedigt oder kein gueltiges STL-Format?")
                return 1

            faces = ms.current_mesh().face_number()
            emit("FACES %d" % faces)
            if faces == 0:
                emit("ERROR Die Datei enthaelt keine gueltige 3D-Geometrie "
                     "(0 Dreiecke). Ist es wirklich eine STL-Datei?")
                return 1

            emit("PHASE wrap")
            ms.generate_alpha_wrap(alpha_fraction=float(alpha))

            emit("PHASE save")
            ms.save_current_mesh(tmp_out)
            # erst jetzt an den (evtl. Umlaut-)Zielpfad verschieben
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

    def fmt(sec):
        if sec is None or sec < 0:
            return "--:--"
        sec = int(round(sec))
        return "%02d:%02d" % (sec // 60, sec % 60)

    # ---- Zustand ----
    state = {
        "proc": None,
        "reader": None,
        "q": queue.Queue(),
        "start": 0.0,
        "phase": "",
        "running": False,
    }

    # ---- Fenster ----
    root = tk.Tk()
    root.title("STL ShrinkWrap — Alpha Wrap")
    try:
        _icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(_icon):
            root.iconbitmap(_icon)
    except Exception:  # noqa: BLE001
        pass
    root.minsize(560, 0)
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
            title="STL-Datei waehlen",
            filetypes=[("STL-Dateien", "*.stl"), ("Alle Dateien", "*.*")])
        if p:
            in_var.set(p)
            if not out_var.get():
                stem, _ = os.path.splitext(p)
                out_var.set(stem + " wrap.stl")

    def pick_out():
        init = out_var.get() or (os.path.splitext(in_var.get())[0] + " wrap.stl"
                                 if in_var.get() else "")
        p = filedialog.asksaveasfilename(
            title="Ausgabedatei",
            defaultextension=".stl",
            initialfile=os.path.basename(init) if init else "wrap.stl",
            initialdir=os.path.dirname(init) if init else None,
            filetypes=[("STL-Dateien", "*.stl")])
        if p:
            out_var.set(p)

    # Zeile: Eingabe
    ttk.Label(frm, text="Eingabe-STL:").grid(row=0, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=in_var).grid(row=0, column=1, sticky="ew", **pad)
    ttk.Button(frm, text="Durchsuchen…", command=pick_in).grid(row=0, column=2, **pad)

    # Zeile: Ausgabe
    ttk.Label(frm, text="Ausgabe-STL:").grid(row=1, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=out_var).grid(row=1, column=1, sticky="ew", **pad)
    ttk.Button(frm, text="Speichern unter…", command=pick_out).grid(row=1, column=2, **pad)

    # Zeile: Alpha
    ttk.Label(frm, text="Alpha-Faktor:").grid(row=2, column=0, sticky="w", **pad)
    alpha_row = ttk.Frame(frm)
    alpha_row.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)
    ttk.Spinbox(alpha_row, textvariable=alpha_var, from_=0.0005, to=0.5,
                increment=0.0005, width=10, format="%.4f").pack(side="left")
    ttk.Label(alpha_row,
              text="  kleiner = mehr Details · groesser = staerker geschrumpft",
              foreground="#666").pack(side="left")

    # "Sanduhr": unbestimmter Balken, der nur anzeigt, dass etwas laeuft
    bar = ttk.Progressbar(frm, mode="indeterminate")
    bar.grid(row=4, column=0, columnspan=3, sticky="ew", **pad)

    status_var = tk.StringVar(value="Bereit.")
    ttk.Label(frm, textvariable=status_var).grid(row=5, column=0, columnspan=3,
                                                 sticky="w", **pad)

    time_var = tk.StringVar(value="")
    ttk.Label(frm, textvariable=time_var, foreground="#444").grid(
        row=6, column=0, columnspan=3, sticky="w", **pad)

    start_btn = ttk.Button(frm, text="Shrink-Wrap starten")
    start_btn.grid(row=7, column=0, columnspan=3, sticky="ew", **pad)

    PHASE_TEXT = {
        "import": "Lade PyMeshLab…",
        "load": "Lese STL-Datei…",
        "wrap": "Berechne Alpha-Wrap… (das kann dauern)",
        "save": "Speichere Ergebnis…",
    }

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
            messagebox.showerror("Fehler", "Bitte eine gueltige Eingabe-STL waehlen.")
            return
        if not out_path:
            messagebox.showerror("Fehler", "Bitte eine Ausgabedatei angeben.")
            return
        try:
            alpha = float(alpha_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Fehler", "Alpha-Faktor muss eine Zahl sein.")
            return
        if alpha <= 0:
            messagebox.showerror("Fehler", "Alpha-Faktor muss groesser als 0 sein.")
            return

        state["start"] = time.time()

        # Eigene Programmzeile bestimmen (.py vs gebaute .exe)
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--worker", in_path, out_path, repr(alpha)]
        else:
            cmd = [sys.executable, os.path.abspath(__file__), "--worker",
                   in_path, out_path, repr(alpha)]

        creationflags = 0
        if os.name == "nt":
            creationflags = 0x08000000  # CREATE_NO_WINDOW -> kein schwarzes Fenster

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=creationflags)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Fehler", "Konnte Berechnung nicht starten:\n%r" % e)
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
        bar.start(12)          # Sanduhr: laufender Balken
        status_var.set("Starte…")
        root.after(100, tick)

    def finish(success, message):
        state["running"] = False
        start_btn.config(state="normal")
        bar.stop()
        if success:
            elapsed = time.time() - state["start"]
            status_var.set("Fertig ✔  " + message)
            time_var.set("Gesamtdauer: " + fmt(elapsed))
        else:
            status_var.set("Abgebrochen / Fehler")
            time_var.set("")
            messagebox.showerror("Fehler beim Wrappen", message)

    def tick():
        if not state["running"]:
            return
        q = state["q"]
        done = False
        try:
            while True:
                line = q.get_nowait()
                if line == "__EOF__":
                    # Prozess-Ende ohne DONE -> pruefen
                    rc = state["proc"].poll()
                    if rc not in (0, None) and state["phase"] != "done":
                        finish(False, "Der Berechnungsprozess wurde unerwartet "
                                      "beendet (Code %s)." % rc)
                        return
                    done = True
                    break
                elif line.startswith("PHASE "):
                    ph = line[6:].strip()
                    state["phase"] = ph
                    status_var.set(PHASE_TEXT.get(ph, ph))
                elif line.startswith("FACES "):
                    status_var.set("Lese STL… (%s Dreiecke)" % line[6:].strip())
                elif line == "DONE":
                    state["phase"] = "done"
                    finish(True, os.path.basename(out_var.get()))
                    return
                elif line.startswith("ERROR "):
                    state["phase"] = "error"
                    finish(False, line[6:].strip())
                    return
        except queue.Empty:
            pass

        if done:
            return

        # Nur Hinweis, dass etwas laeuft (+ verstrichene Zeit)
        elapsed = time.time() - state["start"]
        time_var.set("Berechnung laeuft … (laeuft seit %s)" % fmt(elapsed))

        root.after(200, tick)

    start_btn.config(command=start)
    root.mainloop()


# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--worker":
        # python stl_shrinkwrap.py --worker <in> <out> <alpha>
        _, _, in_path, out_path, alpha = sys.argv[:5]
        sys.exit(run_worker(in_path, out_path, alpha))
    else:
        run_gui()


if __name__ == "__main__":
    # Wichtig fuer gebaute .exe, falls multiprocessing genutzt wuerde:
    try:
        import multiprocessing
        multiprocessing.freeze_support()
    except Exception:  # noqa: BLE001
        pass
    main()
