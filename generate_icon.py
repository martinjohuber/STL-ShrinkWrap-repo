# -*- coding: utf-8 -*-
"""Erzeugt icon.ico (Shrink-Wrap-Motiv) mit Pillow."""
import sys
from PIL import Image, ImageDraw

S = 256
SS = 4                      # Supersampling fuer glatte Kanten
W = S * SS
img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

GREEN = (34, 158, 79, 255)
GREEN_D = (24, 120, 60, 255)
WHITE = (255, 255, 255, 255)

def rrect(box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)

# Hintergrund: gruenes abgerundetes Quadrat
m = 10 * SS
rrect([m, m, W - m, W - m], 48 * SS, GREEN)
# leichter dunklerer Rand unten fuer Tiefe
rrect([m, m, W - m, W - m], 48 * SS, None)

def scale(pts):
    return [(x * SS, y * SS) for (x, y) in pts]

# Isometrischer Wuerfel (Mittelpunkt ~128,132)
cx, cy = 128, 134
hw = 52      # halbe Breite
dh = 26      # Tiefenversatz
top_h = 30   # Hoehe der oberen Flaeche
# Eckpunkte
tF = (cx, cy - 44)                      # vordere obere Spitze (Raute oben)
top = [(cx, cy - 64), (cx + hw, cy - 64 + dh), (cx, cy - 64 + 2*dh), (cx - hw, cy - 64 + dh)]
# Wuerfel als Raute-oben + zwei Seiten
hcube = 70
top_y = cy - 60
top_pts = [(cx, top_y - dh), (cx + hw, top_y), (cx, top_y + dh), (cx - hw, top_y)]
left_pts = [(cx - hw, top_y), (cx, top_y + dh), (cx, top_y + dh + hcube), (cx - hw, top_y + hcube)]
right_pts = [(cx + hw, top_y), (cx, top_y + dh), (cx, top_y + dh + hcube), (cx + hw, top_y + hcube)]

d.polygon(scale(top_pts), fill=WHITE)
d.polygon(scale(left_pts), fill=(225, 240, 230, 255))
d.polygon(scale(right_pts), fill=(200, 225, 210, 255))
# Kanten betonen
lw = 3 * SS
for poly in (top_pts, left_pts, right_pts):
    d.line(scale(poly + [poly[0]]), fill=GREEN_D, width=lw, joint="curve")

# Vier nach innen zeigende Pfeile (Schrumpfen) in den vier Ecken
import math
def arrow(tipx, tipy, dx, dy):
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    L = 34
    bx, by = tipx - dx * L, tipy - dy * L
    d.line(scale([(bx, by), (tipx, tipy)]), fill=WHITE, width=6 * SS)
    px, py = -dy, dx
    a = (tipx - dx * 18 + px * 13, tipy - dy * 18 + py * 13)
    b = (tipx - dx * 18 - px * 13, tipy - dy * 18 - py * 13)
    d.polygon(scale([(tipx, tipy), a, b]), fill=WHITE)

# Spitzen nahe der Wuerfel-Mitte, Schaft zeigt aus der jeweiligen Ecke nach innen
arrow(58, 58,  1,  1)    # oben-links  -> Mitte
arrow(198, 58, -1,  1)   # oben-rechts -> Mitte
arrow(58, 200,  1, -1)   # unten-links -> Mitte
arrow(198, 200, -1, -1)  # unten-rechts-> Mitte

img = img.resize((S, S), Image.LANCZOS)
out = sys.argv[1] if len(sys.argv) > 1 else "icon.ico"
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                     (128, 128), (256, 256)])
print("Icon gespeichert:", out)
