#!/usr/bin/env python3
"""Render extrusion moves of a multi-extruder BambuStudio gcode with matplotlib.

Colors per active extruder/tool. H2D uses M1020 S{0,1} to switch extruders.
"""
import argparse, re, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.collections import LineCollection

# Bambu's published filament colors (PLA Basic green / TPU 85A light-blue)
COLORS = {0: "#00AE42", 1: "#76D9F4"}
LABELS = {0: "T0 PLA", 1: "T1 TPU"}

RE_M1020 = re.compile(r"^M1020\s+S(\d+)")
RE_G = re.compile(r"^G[01]\b")
RE_NUM = lambda c: re.compile(r"\b" + c + r"(-?\d+(?:\.\d+)?)")
RX = RE_NUM("X"); RY = RE_NUM("Y"); RZ = RE_NUM("Z"); RE = RE_NUM("E")

def parse(path):
    """Yield (tool, x0, y0, z0, x1, y1, z1) extrusion segments."""
    x = y = z = 0.0
    e_abs = 0.0
    abs_e = True  # M82 absolute / M83 relative
    tool = 0
    segs = {0: [], 1: []}
    with open(path) as f:
        for line in f:
            s = line.lstrip()
            if not s or s.startswith(";"):
                continue
            m = RE_M1020.match(s)
            if m:
                tool = int(m.group(1))
                continue
            if s.startswith("M82"): abs_e = True; continue
            if s.startswith("M83"): abs_e = False; continue
            if not RE_G.match(s):
                continue
            mx = RX.search(s); my = RY.search(s); mz = RZ.search(s); me = RE.search(s)
            nx = float(mx.group(1)) if mx else x
            ny = float(my.group(1)) if my else y
            nz = float(mz.group(1)) if mz else z
            extruding = False
            if me:
                ev = float(me.group(1))
                de = (ev - e_abs) if abs_e else ev
                if de > 1e-6:
                    extruding = True
                if abs_e: e_abs = ev
            if extruding and (nx, ny) != (x, y):
                segs[tool].append(((x, y, z), (nx, ny, nz)))
            x, y, z = nx, ny, nz
    return segs

def render(segs, out_prefix):
    # 2D top-down
    fig, ax = plt.subplots(figsize=(8, 7), dpi=140)
    for tool in (0, 1):
        ss = segs[tool]
        if not ss: continue
        lc = LineCollection([((a[0], a[1]), (b[0], b[1])) for a, b in ss],
                            colors=COLORS[tool], linewidths=0.25, alpha=0.85,
                            label=f"{LABELS[tool]} ({len(ss):,} moves)")
        ax.add_collection(lc)
    ax.set_aspect("equal"); ax.autoscale_view()
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
    ax.set_title(f"Top-down (XY) — {out_prefix.name}")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(f"{out_prefix}.xy.png"); plt.close(fig)

    # 3D iso
    fig = plt.figure(figsize=(8, 7), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    for tool in (0, 1):
        ss = segs[tool]
        if not ss: continue
        lc = Line3DCollection(ss, colors=COLORS[tool], linewidths=0.15, alpha=0.55,
                              label=LABELS[tool])
        ax.add_collection3d(lc)
    pts = np.array([p for ss in segs.values() for ab in ss for p in ab])
    ax.set_xlim(pts[:, 0].min(), pts[:, 0].max())
    ax.set_ylim(pts[:, 1].min(), pts[:, 1].max())
    ax.set_zlim(pts[:, 2].min(), pts[:, 2].max())
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z (mm)")
    ax.set_title(f"Iso 3D — {out_prefix.name}")
    ax.view_init(elev=22, azim=-60)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{out_prefix}.iso.png"); plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("gcode")
    ap.add_argument("out_prefix")
    a = ap.parse_args()
    segs = parse(a.gcode)
    for t in (0, 1):
        print(f"{LABELS[t]}: {len(segs[t]):,} extrusion segments")
    render(segs, Path(a.out_prefix))
    print("wrote", a.out_prefix + ".xy.png", "and", a.out_prefix + ".iso.png")
