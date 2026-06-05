# Drittanbieter-Komponenten / Third-Party Notices

Diese App bündelt (im Ordner `STL-ShrinkWrap-Portable\python\`) einen
Python-Interpreter sowie mehrere Bibliotheken. Beim Weitergeben des Bundles
werden diese Komponenten mitverteilt. Ihre Lizenzen:

| Komponente | Lizenz | Quelle |
|---|---|---|
| **PyMeshLab** | **GPL-3.0** | https://github.com/cnr-isti-vclab/PyMeshLab |
| **MeshLab** (in PyMeshLab enthalten) | GPL-3.0 | https://github.com/cnr-isti-vclab/meshlab |
| **CGAL** (für `generate_alpha_wrap`, in PyMeshLab) | GPL-3.0 (Alpha Wrap 3) | https://github.com/CGAL/cgal |
| **Qt 5** (DLLs, von PyMeshLab mitgeliefert) | LGPL-3.0 | https://www.qt.io/ |
| **CPython** (Interpreter) | PSF License Agreement | https://docs.python.org/3/license.html |
| **NumPy** | BSD-3-Clause | https://github.com/numpy/numpy |

## Bedeutung für die Weitergabe

- **PyMeshLab / MeshLab / CGAL stehen unter GPL-3.0.** Weil diese App PyMeshLab
  benutzt und (im portablen Bundle) mitverteilt, steht **das gesamte verteilte
  Werk unter GPL-3.0** — siehe `LICENSE`. Der vollständige, korrespondierende
  Quelltext dieser Komponenten ist öffentlich unter den oben genannten Links
  verfügbar (sie werden unverändert mitgeliefert).
- **Qt 5 (LGPL-3.0)** wird als separate DLLs dynamisch geladen. Das erfüllt die
  LGPL; die Qt-DLLs liegen offen im Ordner und können durch eigene, kompatible
  Versionen ersetzt werden. Der LGPLv3-Text liegt als `LICENSE-LGPL-3.0.txt` bei
  (zusammen mit dem GPLv3-Text in `LICENSE`). Qt-Quelltext: https://download.qt.io/
- **CPython (PSF)** und **NumPy (BSD)** sind permissiv; ihre vollständigen
  Lizenztexte liegen im Bundle unter
  `python\LICENSE.txt` bzw. `python\Lib\site-packages\numpy-*.dist-info\`.

> Hinweis: Diese Übersicht ist eine Hilfestellung, keine Rechtsberatung. Bei
> kommerzieller/abgewandelter Weitergabe im Zweifel die jeweiligen
> Original-Lizenztexte prüfen.
