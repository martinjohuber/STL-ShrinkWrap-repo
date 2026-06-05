#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Winziger Starter fuer die portable STL-ShrinkWrap-App.
Startet den mitgelieferten Python (Ordner 'python\\pythonw.exe') mit der GUI.
Laedt selbst KEIN PyMeshLab -> kann nicht abstuerzen.
"""
import os
import sys
import subprocess
import ctypes


def main():
    base = os.path.dirname(os.path.abspath(sys.executable))
    pyw = os.path.join(base, "python", "pythonw.exe")
    script = os.path.join(base, "stl_shrinkwrap.py")

    if not os.path.exists(pyw) or not os.path.exists(script):
        ctypes.windll.user32.MessageBoxW(
            0,
            "Diese .exe muss zusammen mit dem Ordner 'python' und der Datei "
            "'stl_shrinkwrap.py' im selben Verzeichnis liegen.\n\n"
            "Bitte den GANZEN Ordner kopieren/entpacken, nicht nur die .exe.",
            "STL ShrinkWrap", 0x10)
        return 1

    subprocess.Popen([pyw, script], cwd=base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
