"""Chart templates for every engine's output: data -> analysis question -> visual.

Dependency-free SVG rendering (no matplotlib), assembled into one self-contained HTML report with
light/dark theming, a legend for every multi-series chart, hover tooltips and a table view per chart.
Palette and mark specs follow the data-viz method: thin marks with rounded data-ends, 2px surface
gaps, one hue for magnitude, fixed categorical order, diverging blue<->red with a gray midpoint.

    from finmodel import charts
    charts.report_for("three_statement", result, "out/report.html")
    charts.CATALOG  # -> the template: which charts describe which data, and why
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ----------------------------------------------------------------------------- palette (reference instance)
CAT_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
CAT_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
DIV_NEG, DIV_MID, DIV_POS = "#e34948", "#f0efec", "#2a78d6"
GOOD, CRITICAL = "#0ca30c", "#d03b3b"

CSS = """
.viz-root{color-scheme:light;--surface:#fcfcfb;--plane:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#4a3aa7;--s8:#e34948;--neg:#e34948;--pos:#2a78d6;--mid:#f0efec;
font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--plane);color:var(--ink);margin:0;padding:24px}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;--neg:#e66767;--pos:#3987e5;--mid:#383835}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;--neg:#e66767;--pos:#3987e5;--mid:#383835}
.viz-root h1{font-size:22px;margin:0 0 4px}.viz-root .sub{color:var(--ink2);margin:0 0 20px;font-size:14px}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:0 0 20px}.tile{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 16px;min-width:150px}
.tile .l{font-size:12px;color:var(--ink2)}.tile .v{font-size:26px;font-weight:600;margin-top:2px}.tile .d{font-size:12px;color:var(--ink2)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px;margin:0 0 16px;max-width:1100px}
.card h2{font-size:15px;margin:0 0 2px}.card .q{font-size:12px;color:var(--ink2);margin:0 0 10px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--ink2);margin:6px 0 0}.legend span i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
svg{max-width:100%;height:auto;display:block}svg text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--ink2);font-size:11px}
svg .t{fill:var(--ink)}svg .axis{stroke:var(--axis);stroke-width:1}svg .grid{stroke:var(--grid);stroke-width:1}svg .mark:hover{opacity:.8}
details{margin-top:8px;font-size:12px}details summary{cursor:pointer;color:var(--ink2)}table{border-collapse:collapse;font-variant-numeric:tabular-nums;margin-top:6px}
td,th{padding:3px 10px;border-bottom:1px solid var(--grid);text-align:right;font-size:12px}th:first-child,td:first-child{text-align:left}
.tip{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);border:1px solid var(--border);border-radius:6px;padding:6px 8px;font-size:12px;display:none;box-shadow:0 2px 8px rgba(0,0,0,.15)}
"""
JS = """
document.addEventListener('DOMContentLoaded',()=>{const tip=document.createElement('div');tip.className='tip';document.body.appendChild(tip);
document.querySelectorAll('[data-tip]').forEach(el=>{el.addEventListener('mousemove',e=>{tip.style.display='block';tip.textContent=el.getAttribute('data-tip');tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px';});
el.addEventListener('mouseleave',()=>tip.style.display='none');});});
"""


def _fmt(v: float, kind: str = "num") -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)): return "–"
    if kind == "pct": return f"{v*100:+.1f}%" if v < 0 else f"{v*100:.1f}%"
    if kind == "x": return f"{v:.1f}x"
    a = abs(v)
    if a >= 1e9: s = f"{v/1e9:.1f}B"
    elif a >= 1e6: s = f"{v/1e6:.1f}M"
    elif a >= 1e4: s = f"{v/1e3:.1f}K"
    elif a >= 100: s = f"{v:,.0f}"
    else: s = f"{v:,.2f}"
    return s


def _wrap_label(s: str, max_chars: int) -> List[str]:
    """Greedily wrap onto at most 2 lines at word boundaries; ellipsize an overlong second line."""
    if len(s) <= max_chars:
        return [s]
    words = s.split(); line1 = ""
    for w in words:
        if len((line1 + " " + w).strip()) > max_chars:
            break
        line1 = (line1 + " " + w).strip()
    line1 = line1 or s[:max_chars]
    rest = s[len(line1):].strip()
    if not rest:
        return [line1]
    if len(rest) > max_chars:
        rest = rest[: max(1, max_chars - 1)].rstrip() + "…"
    return [line1, rest]


def _nice_ticks(lo: float, hi: float, n: int = 5) -> List[float]:
    if hi == lo: hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(abs(raw))) if raw else 1
    step = min((s for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=10) * mag
    start = math.floor(lo / step) * step
    return [start + i * step for i in range(int((hi - start) / step) + 2)]


class SVG:
    def __init__(self, w=760, h=300):
        self.w, self.h, self.parts = w, h, []
    def add(self, s): self.parts.append(s)
    def render(self) -> str:
        return f'<svg viewBox="0 0 {self.w} {self.h}" role="img">' + "".join(self.parts) + "</svg>"


def _frame(svg: SVG, x0, y0, x1, y1, vmin, vmax, fmt="num"):
    """Draw hairline gridlines + left tick labels; return y-scaler."""
    ticks = _nice_ticks(vmin, vmax)
    ticks = [t for t in ticks if vmin - 1e-9 <= t <= vmax + 1e-9] or [vmin, vmax]
    lo, hi = min(ticks[0], vmin), max(ticks[-1], vmax)
    def sy(v): return y1 - (v - lo) / (hi - lo) * (y1 - y0) if hi != lo else y1
    for t in ticks:
        y = sy(t); svg.add(f'<line class="grid" x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"/>')
        svg.add(f'<text x="{x0-6}" y="{y+4:.1f}" text-anchor="end">{_fmt(t, fmt)}</text>')
    if lo <= 0 <= hi:
        svg.add(f'<line class="axis" x1="{x0}" y1="{sy(0):.1f}" x2="{x1}" y2="{sy(0):.1f}"/>')
    return sy


def _rounded_top(x, y, w, h, r=4):
    """Bar path with 4px rounded data-end, square at the baseline (h may be negative -> rounded bottom)."""
    if h >= 0:
        r = min(r, w / 2, h)
        return f"M{x},{y+h} V{y+r} Q{x},{y} {x+r},{y} H{x+w-r} Q{x+w},{y} {x+w},{y+r} V{y+h} Z"
    h = -h; r = min(r, w / 2, h)
    return f"M{x},{y} V{y+h-r} Q{x},{y+h} {x+r},{y+h} H{x+w-r} Q{x+w},{y+h} {x+w},{y+h-r} V{y} Z"


# ----------------------------------------------------------------------------- chart primitives
def column_chart(categories: Sequence, series: Dict[str, Sequence[float]], fmt="num", stacked=False, w=760, h=300, colors=None) -> str:
    svg = SVG(w, h); L, R, T, B = 64, 16, 14, 34
    names = list(series); k = len(names); n = len(categories)
    vals = [list(series[s]) for s in names]
    if stacked:
        pos = [sum(v[i] for v in vals if v[i] > 0) for i in range(n)]; neg = [sum(v[i] for v in vals if v[i] < 0) for i in range(n)]
        vmax, vmin = max(pos + [0]), min(neg + [0])
    else:
        allv = [x for v in vals for x in v]; vmax, vmin = max(allv + [0]), min(allv + [0])
    sy = _frame(svg, L, T, w - R, h - B, vmin, vmax, fmt)
    slot = (w - L - R) / max(n, 1); colors = colors or CAT_LIGHT
    for i, cat in enumerate(categories):
        cx = L + slot * i
        if stacked:
            bw = min(24, slot * 0.6); x = cx + (slot - bw) / 2; up = down = 0.0
            for j, s in enumerate(names):
                v = vals[j][i]
                if v == 0: continue
                if v > 0:
                    y0, y1 = sy(up + v), sy(up); up += v
                else:
                    y0, y1 = sy(down), sy(down + v); down += v
                y_top, hh = (y0, y1 - y0) if v > 0 else (y0, y1 - y0)
                svg.add(f'<rect class="mark" x="{x:.1f}" y="{min(y0,y1)+1:.1f}" width="{bw:.1f}" height="{max(abs(y1-y0)-2,0):.1f}" rx="2" fill="{colors[j%8]}" data-tip="{html.escape(str(cat))} · {html.escape(s)}: {_fmt(v, fmt)}"/>')
        else:
            bw = min(24, slot * 0.7 / k); gap = 2; total = k * bw + (k - 1) * gap; x = cx + (slot - total) / 2
            for j, s in enumerate(names):
                v = vals[j][i]; y = sy(max(v, 0)); hh = sy(0) - sy(v)
                svg.add(f'<path class="mark" d="{_rounded_top(x + j*(bw+gap), y if v >= 0 else sy(0), bw, hh if v >= 0 else -(sy(v)-sy(0)))}" fill="{colors[j%8]}" data-tip="{html.escape(str(cat))} · {html.escape(s)}: {_fmt(v, fmt)}"/>')
        svg.add(f'<text x="{cx+slot/2:.1f}" y="{h-12}" text-anchor="middle">{html.escape(str(cat))}</text>')
    return svg.render()


def line_chart(categories: Sequence, series: Dict[str, Sequence[float]], fmt="num", w=760, h=300, colors=None, emphasis: Optional[str] = None) -> str:
    names = list(series); n = len(categories); colors = colors or CAT_LIGHT
    longest = max((len(f"{s} {_fmt(series[s][-1], fmt)}") for s in names if series[s]), default=10)
    R = min(int(longest * 6.4) + 16, 260)
    svg = SVG(w, h); L, T, B = 64, 14, 34
    allv = [x for s in names for x in series[s] if x is not None and not (isinstance(x, float) and math.isnan(x))]
    vmax, vmin = max(allv + [0]) if allv else 1, min(allv + [0]) if allv else 0
    sy = _frame(svg, L, T, w - R, h - B, vmin, vmax, fmt)
    sx = lambda i: L + (w - L - R) * (i / max(n - 1, 1))
    for j, s in enumerate(names):
        col = colors[j % 8] if emphasis is None or s == emphasis else "#898781"
        pts = [(sx(i), sy(v)) for i, v in enumerate(series[s]) if v is not None]
        if not pts: continue
        svg.add(f'<polyline fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>')
        for i, (x, y) in enumerate(pts):
            svg.add(f'<circle class="mark" cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{col}" stroke="var(--surface)" stroke-width="2" data-tip="{html.escape(str(categories[i]))} · {html.escape(s)}: {_fmt(series[s][i], fmt)}"/>')
        x, y = pts[-1]; placed = svg.__dict__.setdefault("_end_labels", [])
        while any(abs(y - py) < 13 for py in placed): y += 13
        placed.append(y)
        svg.add(f'<text x="{x+8:.1f}" y="{y+4:.1f}">{html.escape(s)} {_fmt(series[s][-1], fmt)}</text>')
    for i, cat in enumerate(categories):
        svg.add(f'<text x="{sx(i):.1f}" y="{h-12}" text-anchor="middle">{html.escape(str(cat))}</text>')
    return svg.render()


def waterfall(steps: Sequence[Tuple[str, float]], totals: Sequence[int] = (), fmt="num", w=760, h=340) -> str:
    """steps: (label, delta) ...; indices in `totals` are drawn as full bars from zero (subtotals)."""
    svg = SVG(w, h); L, R, T, B = 64, 16, 22, 66
    run = 0.0; levels = []
    for i, (lab, v) in enumerate(steps):
        if i in totals: levels.append((0.0, v)); run = v
        else: levels.append((run, run + v)); run += v
    vmax = max([b for a, b in levels] + [a for a, b in levels] + [0]); vmin = min([b for a, b in levels] + [a for a, b in levels] + [0])
    sy = _frame(svg, L, T, w - R, h - B, vmin, vmax, fmt)
    slot = (w - L - R) / len(steps); bw = min(28, slot * 0.6)
    for i, ((lab, v), (a, b)) in enumerate(zip(steps, levels)):
        x = L + slot * i + (slot - bw) / 2
        col = "var(--ink2)" if i in totals else (DIV_POS if v >= 0 else DIV_NEG)
        y0, y1 = sy(max(a, b)), sy(min(a, b))
        svg.add(f'<rect class="mark" x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1-y0,1):.1f}" rx="3" fill="{col}" data-tip="{html.escape(lab)}: {_fmt(v, fmt)}"/>')
        if i + 1 < len(steps) and (i + 1) not in totals:
            svg.add(f'<line class="grid" x1="{x+bw:.1f}" y1="{sy(b):.1f}" x2="{x+slot:.1f}" y2="{sy(b):.1f}"/>')
        if v != 0 or i in totals:
            svg.add(f'<text class="t" x="{x+bw/2:.1f}" y="{y0-5:.1f}" text-anchor="middle">{_fmt(v if i not in totals else b, fmt)}</text>')
        maxc = max(7, int(slot / 6.2)); words = lab.split(); lines: List[str] = []; cur = ""
        for wd in words:
            if cur and len(cur) + 1 + len(wd) > maxc: lines.append(cur); cur = wd
            else: cur = (cur + " " + wd).strip()
        if cur: lines.append(cur)
        for k, ln in enumerate(lines[:4]):
            svg.add(f'<text x="{x+bw/2:.1f}" y="{h-B+14+k*13}" text-anchor="middle" style="font-size:10px">{html.escape(ln)}</text>')
    return svg.render()


def heatmap(row_labels: Sequence, col_labels: Sequence, table: Sequence[Sequence[float]], fmt="pct", w=760, diverging_center: Optional[float] = None) -> str:
    n, m = len(row_labels), len(col_labels); cw, ch, L, T = min(90, (w - 120) / max(m, 1)), 34, 110, 30
    h = T + n * ch + 12; svg = SVG(w, h)
    flat = [v for row in table for v in row if v is not None and not math.isnan(v)]
    lo, hi = (min(flat), max(flat)) if flat else (0, 1)
    def color(v):
        if v is None or math.isnan(v): return "var(--mid)"
        if diverging_center is not None:
            span = max(abs(hi - diverging_center), abs(lo - diverging_center)) or 1
            t = (v - diverging_center) / span
            return _mix(DIV_MID, DIV_POS, t) if t >= 0 else _mix(DIV_MID, DIV_NEG, -t)
        t = (v - lo) / (hi - lo) if hi != lo else 0.5
        return SEQ[min(len(SEQ) - 1, int(t * (len(SEQ) - 1)))]
    for j, c in enumerate(col_labels):
        svg.add(f'<text class="t" x="{L + j*cw + cw/2:.1f}" y="{T-10}" text-anchor="middle">{html.escape(str(c))}</text>')
    for i, r in enumerate(row_labels):
        svg.add(f'<text class="t" x="{L-8}" y="{T + i*ch + ch/2 + 4:.1f}" text-anchor="end">{html.escape(str(r))}</text>')
        for j in range(m):
            v = table[i][j]; fill = color(v)
            svg.add(f'<rect class="mark" x="{L + j*cw + 1:.1f}" y="{T + i*ch + 1:.1f}" width="{cw-2:.1f}" height="{ch-2:.1f}" rx="3" fill="{fill}" data-tip="{html.escape(str(r))} × {html.escape(str(c))}: {_fmt(v, fmt)}"/>')
            ink = "#ffffff" if _lum(fill) < 0.45 else "#0b0b0b"
            svg.add(f'<text x="{L + j*cw + cw/2:.1f}" y="{T + i*ch + ch/2 + 4:.1f}" text-anchor="middle" style="fill:{ink}">{_fmt(v, fmt)}</text>')
    return svg.render()


def range_bars(items: Sequence[Tuple[str, float, float]], marker: Optional[float] = None, marker_label="", fmt="num", w=760) -> str:
    """Football field: horizontal low-high bars per valuation method with an optional current-price marker.
    The left margin is sized to the longest label (capped so the bars keep most of the width); a label that would
    still overflow the cap wraps onto a second line instead of being clipped."""
    R, T, char_px, row_h = 20, 16, 6.2, 30
    L_cap = min(360, w * 0.42)
    L = max(140, min(L_cap, max((len(lab) * char_px + 16 for lab, _, _ in items), default=140)))
    max_chars = max(8, int((L - 16) / char_px))
    rows = [(_wrap_label(lab, max_chars), a, b, lab) for lab, a, b in items]
    row_heights = [row_h + 14 * (len(lines) - 1) for lines, _, _, _ in rows]
    n_h = sum(row_heights); h = T + n_h + 40; svg = SVG(w, h)
    lo = min([a for _, a, b, _ in rows] + ([marker] if marker is not None else [])); hi = max([b for _, a, b, _ in rows] + ([marker] if marker is not None else []))
    pad = (hi - lo) * 0.08 or 1; lo -= pad; hi += pad
    sx = lambda v: L + (v - lo) / (hi - lo) * (w - L - R)
    for t in _nice_ticks(lo, hi, 6):
        if lo <= t <= hi:
            svg.add(f'<line class="grid" x1="{sx(t):.1f}" y1="{T}" x2="{sx(t):.1f}" y2="{T+n_h}"/><text x="{sx(t):.1f}" y="{T+n_h+16}" text-anchor="middle">{_fmt(t, fmt)}</text>')
    y_cur = T
    for (lines, a, b, lab), rh in zip(rows, row_heights):
        y = y_cur + (rh - 18) / 2
        for li, line in enumerate(lines):
            svg.add(f'<text class="t" x="{L-8}" y="{y+13-(len(lines)-1-li)*13:.1f}" text-anchor="end">{html.escape(line)}</text>')
        svg.add(f'<rect class="mark" x="{sx(a):.1f}" y="{y:.1f}" width="{max(sx(b)-sx(a),2):.1f}" height="18" rx="4" fill="{CAT_LIGHT[0]}" data-tip="{html.escape(lab)}: {_fmt(a, fmt)} – {_fmt(b, fmt)}"/>')
        svg.add(f'<text x="{sx(a)-4:.1f}" y="{y+13:.1f}" text-anchor="end">{_fmt(a, fmt)}</text><text x="{sx(b)+4:.1f}" y="{y+13:.1f}">{_fmt(b, fmt)}</text>')
        y_cur += rh
    if marker is not None:
        svg.add(f'<line x1="{sx(marker):.1f}" y1="{T-4}" x2="{sx(marker):.1f}" y2="{T+n_h+4}" stroke="{CAT_LIGHT[1]}" stroke-width="2" stroke-dasharray="4 3"/><text class="t" x="{sx(marker)+5:.1f}" y="{T+n_h+30}">{html.escape(marker_label)} {_fmt(marker, fmt)}</text>')
    return svg.render()


def _hex(c): return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
def _mix(a, b, t):
    ca, cb = _hex(a), _hex(b); return "#" + "".join(f"{int(round(x + (y - x) * t)):02x}" for x, y in zip(ca, cb))
def _lum(c):
    if not c.startswith("#"): return 0.9
    r, g, b = [x / 255 for x in _hex(c)]; return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ----------------------------------------------------------------------------- report assembly
def _table(categories, series: Dict[str, Sequence[float]], fmt="num") -> str:
    head = "<tr><th></th>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in categories) + "</tr>"
    rows = "".join(f"<tr><td>{html.escape(k)}</td>" + "".join(f"<td>{_fmt(v, fmt)}</td>" for v in vs) + "</tr>" for k, vs in series.items())
    return f"<details><summary>Table view</summary><table>{head}{rows}</table></details>"


def card(title: str, question: str, svg: str, legend: Sequence[str] = (), table_html: str = "", colors=None) -> str:
    colors = colors or CAT_LIGHT
    leg = ""
    if len(legend) >= 2:
        leg = '<div class="legend">' + "".join(f'<span><i style="background:{colors[i%8]}"></i>{html.escape(l)}</span>' for i, l in enumerate(legend)) + "</div>"
    return f'<div class="card"><h2>{html.escape(title)}</h2><p class="q">{html.escape(question)}</p>{svg}{leg}{table_html}</div>'


def tiles(items: Sequence[Tuple[str, Any, str]]) -> str:
    return '<div class="kpis">' + "".join(f'<div class="tile"><div class="l">{html.escape(l)}</div><div class="v">{html.escape(str(v))}</div><div class="d">{html.escape(d)}</div></div>' for l, v, d in items) + "</div>"


def report(title: str, subtitle: str, body: str) -> str:
    return (f"<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title><style>{CSS}</style><div class='viz-root'><h1>{html.escape(title)}</h1><p class='sub'>{html.escape(subtitle)}</p>{body}</div><script>{JS}</script>")


# ----------------------------------------------------------------------------- chart templates per engine
ChartFn = Callable[[Dict[str, Any]], str]


def _three_statement(res: Dict[str, Any]) -> str:
    yrs = [str(y) for y in res["years"]]; R = res["rows"]; nh = res["n_hist"]
    margin = [a / b if b else 0 for a, b in zip(R["Net Earnings"], R["Revenue"])]
    out = tiles([("Revenue (final year)", _fmt(R["Revenue"][-1]), f"CAGR {((R['Revenue'][-1]/R['Revenue'][0])**(1/(len(yrs)-1))-1)*100:.1f}%"),
                 ("Net margin (final)", _fmt(margin[-1], "pct"), "net earnings / revenue"),
                 ("Cash (final)", _fmt(R["Cash"][-1]), "closing cash"), ("Balance check", "OK" if res["balanced"] else "ERROR", "assets = liabilities + equity")])
    out += card("Revenue and net earnings", "Is the business growing, and how much of each revenue dollar reaches the bottom line?",
                column_chart(yrs, {"Revenue": R["Revenue"], "Net Earnings": R["Net Earnings"]}), ["Revenue", "Net Earnings"], _table(yrs, {"Revenue": R["Revenue"], "Net Earnings": R["Net Earnings"], "Net margin": margin}))
    out += card("Margin structure", "Gross vs net margin over time: where does profitability come from and where is it lost?",
                line_chart(yrs, {"Gross margin": [a / b for a, b in zip(R["Gross Profit"], R["Revenue"])], "Net margin": margin}, fmt="pct"), ["Gross margin", "Net margin"])
    cf = {"Operations": R["Cash from Operations"], "Investing": [-x for x in R["Cash from Investing"]], "Financing": R["Cash from Financing"]}
    out += card("Cash flow by activity", "Does operating cash cover investment, and how is the balance financed?", column_chart(yrs, cf, stacked=True), list(cf), _table(yrs, {**cf, "Net change": R["Net Increase (decrease) in Cash"]}))
    last = len(yrs) - 1
    out += card(f"Cash bridge {yrs[last]}", "From opening to closing cash: which activities added and consumed cash in the final year?",
                waterfall([("Opening cash", R["Opening Cash Balance"][last]), ("Cash from operations", R["Cash from Operations"][last]), ("Capex", -R["Cash from Investing"][last]),
                           ("Financing", R["Cash from Financing"][last]), ("Closing cash", R["Closing Cash Balance"][last])], totals=(0, 4)))
    bs = {"Cash": R["Cash"], "Receivables": R["Accounts Receivable"], "Inventory": R["Inventory"], "PP&E": R["Property & Equipment"]}
    out += card("Asset composition", "How is capital deployed: working capital vs fixed assets vs idle cash?", column_chart(yrs, bs, stacked=True), list(bs), _table(yrs, bs))
    wc = {"AR days": res["assumptions"]["AR Days"], "Inventory days": res["assumptions"]["Inventory Days"], "AP days": res["assumptions"]["AP Days"]}
    out += card("Working-capital days", "Cash conversion: how long is cash tied up in receivables and inventory versus financed by suppliers?", line_chart(yrs, wc), list(wc), _table(yrs, wc))
    lev = {"Debt / equity": [d / e if e else 0 for d, e in zip(R["Debt"], R["Shareholder's Equity"])], "Interest cover (EBT+int)/int": [(e + i) / i if i else 0 for e, i in zip(R["Earnings Before Tax"], R["Interest"])]}
    out += card("Leverage and coverage", "Is the balance sheet de-risking as debt is repaid and earnings grow?", line_chart(yrs, lev, fmt="x"), list(lev), _table(yrs, lev, "x"))
    return out


def _dcf(res: Dict[str, Any]) -> str:
    yrs = [str(y) for y in res["years"]]
    out = tiles([("Enterprise value", _fmt(res["enterprise_value"]), "XNPV of UFCF + terminal value"), ("Equity value / share", _fmt(res["equity_value_per_share"], "num"), f"vs price {_fmt(res['market']['price'])}"),
                 ("Upside", _fmt(res["target_price_upside"], "pct"), "intrinsic vs market"), ("IRR", _fmt(res["irr"], "pct"), "buy at market EV, receive FCF + TV")])
    fcf = {"EBIT": res["ebit"], "Cash taxes": [-x for x in res["cash_taxes"]], "D&A": res["da"], "Capex": [-x for x in res["capex"]], "Change in NWC": [-x for x in res["change_nwc"]]}
    out += card("Unlevered free cash flow build", "What drives free cash flow: operating profit, taxes, reinvestment?", column_chart(yrs, fcf, stacked=True), list(fcf), _table(yrs, {**fcf, "UFCF": res["ufcf"]}))
    tv = res["terminal_value"]; pv_flows = res["valuation_flows"]
    out += card("Enterprise value bridge", "How much of value sits in the forecast period versus the terminal value, and what bridges EV to equity?",
                waterfall([("PV of forecast FCF", res["enterprise_value"] - _pv_tv(res)), ("PV of terminal value", _pv_tv(res)), ("Enterprise value", res["enterprise_value"]),
                           ("Plus cash", res["plus_cash"]), ("Less debt", -res["less_debt"]), ("Equity value", res["equity_value"])], totals=(2, 5)))
    out += card("Terminal value cross-check", "Do the perpetuity-growth and exit-multiple methods agree?", column_chart(["Perpetuity growth", "EV/EBITDA multiple", "Used"], {"Terminal value": [tv["perpetuity_growth"], tv["ev_ebitda"], tv["used"]]}))
    if "sensitivity" in res:
        s = res["sensitivity"]
        out += card("Sensitivity: value per share", "How robust is the valuation to the discount rate (rows) and perpetual growth (columns)?",
                    heatmap([f"WACC {r*100:.0f}%" for r in s["rows"]], [f"g {c*100:.1f}%" for c in s["cols"]], s["table"], fmt="num", diverging_center=res["market"]["price"]))
    lo, hi = min(tv["perpetuity_growth"], tv["ev_ebitda"]), max(tv["perpetuity_growth"], tv["ev_ebitda"])
    ev_lo, ev_hi = res["enterprise_value"] - _pv_tv(res) + lo * _pv_tv(res) / tv["used"], res["enterprise_value"] - _pv_tv(res) + hi * _pv_tv(res) / tv["used"]
    per = lambda ev: (ev + res["plus_cash"] - res["less_debt"]) / (res["equity_value"] / res["equity_value_per_share"])
    out += card("Football field", "Where does the intrinsic value range sit relative to the market price?",
                range_bars([("DCF (perpetuity ↔ multiple)", per(ev_lo), per(ev_hi)), ("DCF (WACC ±1%)", *(sorted([per(v) for v in _ev_at(res, (-0.01, 0.01))]))), ("Market price", res["market"]["price"] * 0.95, res["market"]["price"] * 1.05)],
                           marker=res["market"]["price"], marker_label="Current price"))
    return out


def _pv_tv(res):
    from .fin import xnpv
    flows = [0.0] * (len(res["valuation_flows"]) - 1) + [res["valuation_flows"][-1]]
    dates = res["dates"] + [res["dates"][-1]]
    return xnpv(res["discount_rate"], flows, dates)


def _ev_at(res, deltas):
    from .fin import xnpv
    out = []
    for d in deltas:
        r = res["discount_rate"] + d
        out.append(xnpv(r, res["valuation_flows"], res["dates"] + [res["dates"][-1]]))
    return out


def _lbo(res: Dict[str, Any]) -> str:
    yrs = [f"Y{y}" for y in res["years"]]; IS, BS, R, D = res["income_statement"], res["balance_sheet"], res["returns"], res["debt_schedule"]
    out = tiles([("Sponsor IRR", _fmt(R["sponsor"]["irr"], "pct"), f"MOIC {R['sponsor']['moic']:.2f}x"), ("Exit equity value", _fmt(R["exit_equity_value"]), f"{R['exit_multiple']:.1f}x EBITDA"),
                 ("Entry EV / EBITDA", f"{res['entry']['ev_ebitda']:.1f}x", f"debt {res['entry']['debt_ebitda']:.1f}x EBITDA, equity {res['entry']['equity_pct']*100:.0f}% of uses"), ("Balance check", "OK" if res["balanced"] else "ERROR", "")])
    src = {k: v for k, v in res["sources"].items() if k != "total"}; use = {k: v for k, v in res["uses"].items() if k != "total"}
    out += card("Sources and uses", "How is the purchase funded, and what does the money pay for?", column_chart(["Sources", "Uses"], {**{k: [v, 0] for k, v in src.items()}, **{k: [0, v] for k, v in use.items()}}, stacked=True), list(src) + list(use))
    tr = {k: v["Ending"] for k, v in D.items() if k != "Revolver"}; tr["Revolver"] = D["Revolver"]["Ending"]
    out += card("Debt paydown", "How quickly does free cash flow de-lever the capital structure?", column_chart(yrs, tr, stacked=True), list(tr), _table(yrs, {**tr, "Cash": BS["Cash"]}))
    ebitda = IS["EBITDA"]; lev = [sum(v[i] for v in tr.values()) / ebitda[i] if ebitda[i] else 0 for i in range(len(yrs))]
    out += card("EBITDA and leverage", "Is EBITDA growth outpacing debt so that leverage falls?", column_chart(yrs, {"EBITDA": ebitda, "Net income": IS["Net Income"]}), ["EBITDA", "Net income"], _table(yrs, {"EBITDA": ebitda, "Total debt / EBITDA": lev}))
    out += card("Leverage multiple", "Total debt ÷ EBITDA by year.", line_chart(yrs, {"Debt / EBITDA": lev}, fmt="x"))
    # returns attribution: EBITDA growth, multiple expansion, deleveraging
    entry_mult = res["entry"]["ev_ebitda"]; exit_mult = R["exit_multiple"]; ebitda0 = res["entry"]["ebitda"]; ebitda1 = R["exit_ebitda"]
    debt0 = sum(v for k, v in res["sources"].items() if k not in ("equity", "total")); debt1 = -R["less_debt"]
    eq0 = res["sources"]["equity"]; eq1 = R["exit_equity_value"]
    out += card("Returns attribution", "Where did the equity gain come from: EBITDA growth, multiple expansion, or debt paydown (deleveraging)?",
                waterfall([("Equity invested", eq0), ("EBITDA growth", (ebitda1 - ebitda0) * entry_mult), ("Multiple expansion", (exit_mult - entry_mult) * ebitda1),
                           ("Deleveraging & cash", (debt0 - debt1) + R["plus_cash"] - res["closing_balance_sheet"]["cash"] - res["uses"]["transaction_expenses"] - res["uses"]["financing_fees"]), ("Exit equity value", eq1)], totals=(0, 4)))
    if "sensitivity" in res:
        s = res["sensitivity"]
        out += card("Sensitivity: sponsor IRR", "How do revenue scenarios (rows) and exit multiples (columns) move the IRR?",
                    heatmap(list(s["table"]), [f"{m:.1f}x" for m in s["exit_multiples"]], [s["table"][k] for k in s["table"]], fmt="pct"))
    return out


def _merger(res: Dict[str, Any]) -> str:
    out = ""
    if "deal" in res:
        d = res["deal"]
        out += tiles([("Accretion / (dilution)", _fmt(d["accretion_dilution_pct"], "pct"), f"EPS {d['acquirer']['eps']:.2f} → {d['combined']['eps']:.2f}"), ("Offer premium", _fmt(d["purchase_equity_value"] / d["target"]["equity_value"] - 1, "pct"), f"offer {_fmt(d['offer_price_per_share'])}/share"),
                      ("Purchase EV / EBITDA", _fmt(d["purchase_ev_ebitda"], "x"), "target"), ("New shares", _fmt(d["new_shares_issued"]), f"target holders own {d['ownership']['target_holders']*100:.1f}%")])
        out += card("Standalone vs combined EPS", "Does the deal add to or dilute the acquirer's earnings per share?",
                    column_chart(["Acquirer", "Target", "Combined"], {"EPS": [d["acquirer"]["eps"], d["target"]["eps"], d["combined"]["eps"]]}, fmt="num"))
        contrib = {"Acquirer": [d["acquirer"]["ebitda"], d["acquirer"]["net_income"], d["ownership"]["acquirer_holders"] * 100], "Target": [d["target"]["ebitda"], d["target"]["net_income"], d["ownership"]["target_holders"] * 100]}
        out += card("Contribution analysis", "Who brings the earnings versus who ends up owning the combined company?", column_chart(["EBITDA", "Net income", "Ownership %"], contrib, stacked=True), list(contrib))
        f = d["funding"]
        out += card("Funding mix", "Cash, debt or stock: each carries a different cost (foregone interest, interest, dilution).", column_chart(["Consideration"], {"Cash": [f["cash"]], "Debt": [f["debt"]], "Stock": [f["stock"]]}, stacked=True), ["Cash", "Debt", "Stock"])
        out += card("Multiples: standalone vs combined", "Does the combination re-rate the acquirer's valuation multiples?", column_chart(["EV/EBITDA", "P/E"], {"Acquirer": [d["acquirer"]["ev_ebitda"], d["acquirer"]["pe"]], "Target (at offer)": [d["purchase_ev_ebitda"], d["purchase_equity_value"] / d["target"]["net_income"] if d["target"]["net_income"] else 0], "Combined": [d["combined"]["ev_ebitda"], d["combined"]["pe"]]}, fmt="x"), ["Acquirer", "Target (at offer)", "Combined"])
    if "deal_sensitivity" in res:
        s = res["deal_sensitivity"]
        out += card("Sensitivity: accretion / (dilution)", "Offer premium (rows) versus % stock consideration (columns): where does the deal stay accretive?",
                    heatmap([f"{p*100:.0f}% premium" for p in s["rows"]], [f"{c*100:.0f}% stock" for c in s["cols"]], s["table"], fmt="pct", diverging_center=0.0))
    if "pro_forma" in res:
        pf = res["pro_forma"]; yrs = [f"Y{y}" for y in pf["years"]]; IS = pf["income_statement"]; ppa = pf["purchase_price_allocation"]
        out += card("Pro forma accretion / (dilution) by year", "Reported versus adjusted (ex one-off costs and write-up D&A): does dilution fade as synergies ramp?",
                    column_chart(yrs, {"Reported": IS["Accretion / (Dilution) %"], "Adjusted": IS["Adjusted accretion / (dilution) %"]}, fmt="pct"), ["Reported", "Adjusted"], _table(yrs, {"Standalone EPS": IS["Acquirer standalone EPS"], "Pro forma EPS": IS["Pro forma EPS"], "Adjusted EPS": IS["Adjusted EPS (ex one-offs & write-up D&A)"]}))
        out += card("Purchase price allocation", "How much of the price is tangible book value, write-ups and goodwill?",
                    waterfall([("Purchase equity value", ppa["purchase_equity_value"]), ("Seller book value", ppa["less_seller_book_value"]), ("Existing goodwill written off", ppa["plus_existing_goodwill_written_off"]),
                               ("PP&E write-up", ppa["less_ppe_writeup"]), ("Intangibles write-up", ppa["less_intangibles_writeup"]), ("New deferred tax liability", ppa["plus_new_dtl"]), ("Goodwill", ppa["goodwill"])], totals=(0, 6)))
        drivers = {"Cost synergies": IS["Cost synergies (realised)"], "Integration costs": IS["Integration costs"], "Write-up D&A": [a + b for a, b in zip(IS["Amortization of new intangibles"], IS["Depreciation of PP&E write-up"])], "Deal financing cost": [a + b + c for a, b, c in zip(IS["Foregone interest on cash"], IS["Interest on new debt"], IS["Amortization of debt issuance fees"])]}
        out += card("Pre-tax deal effects", "Synergies against the costs of the deal: which lines drive accretion?", column_chart(yrs, drivers, stacked=True), list(drivers), _table(yrs, drivers))
        ds = pf["debt_schedule"]
        out += card("Acquisition debt", "Repayment profile of the new debt.", column_chart(yrs, {"Closing balance": ds["Closing"], "Interest": ds["Interest"]}), ["Closing balance", "Interest"])
    return out


def _comps(res: Dict[str, Any]) -> str:
    out = ""
    ff = res.get("football_field"); iv = res.get("implied_from_comps"); c = res.get("comps"); pr = res.get("precedents")
    if ff:
        lo = min(i["low"] for i in ff["items"]); hi = max(i["high"] for i in ff["items"])
        out += tiles([("Current price", _fmt(ff["current_price"]), ff["target"]), ("Implied range (all methods)", f"{_fmt(lo)} – {_fmt(hi)}", "low of lows to high of highs"),
                      ("Peers", str(len(c["peers"])) if c else "–", "trading comps set"), ("Precedent deals", str(len(pr["deals"])) if pr else "–", "transaction comps set")])
        out += card("Football field", "Where does the current price sit against every valuation method's implied range?",
                    range_bars([(i["method"], i["low"], i["high"]) for i in ff["items"]], marker=ff["current_price"], marker_label="Current"))
    if c:
        labels = [l for l in c["peers"][0]["multiples"] if c["summary"][l]["n"]]
        ev_labels = [l for l in labels if l.startswith("EV")]; eq_labels = [l for l in labels if not l.startswith("EV")]
        names = [p["ticker"] or p["name"] for p in c["peers"]]
        for group, title, why in ((ev_labels, "Peer EV multiples", "Enterprise-value multiples per peer: who trades rich, who trades cheap? (NM multiples are omitted.)"),
                                  (eq_labels, "Peer equity multiples", "P/E per peer: earnings-based pricing, sensitive to leverage and one-offs.")):
            if not group: continue
            series = {l: [p["multiples"][l] if isinstance(p["multiples"][l], (int, float)) else 0 for p in c["peers"]] for l in group[:4]}
            out += card(title, why, column_chart(names, series, fmt="x"), list(series), _table(names, series, fmt="x"))
        stat_rows = {k: [c["summary"][l][k] for l in labels] for k in ("min", "p25", "median", "p75", "max")}
        out += card("Multiple statistics", "Max / 75th / median / 25th / min per multiple: the range that gets applied to the target.",
                    range_bars([(l, c["summary"][l]["p25"], c["summary"][l]["p75"]) for l in labels], fmt="x"), (), _table(labels, stat_rows, fmt="x"))
    if iv:
        rows = [r for r in iv["rows"] if r["implied"]]
        out += card("Implied share price by multiple", "25th–75th percentile implied price per multiple, with the median marked in the table.",
                    range_bars([(r["multiple"], r["implied"].get("p25", r["implied"].get("min"))["share_price"], r["implied"].get("p75", r["implied"].get("max"))["share_price"]) for r in rows], marker=iv["current_price"], marker_label="Current"),
                    (), _table([r["multiple"] for r in rows], {k: [r["implied"][k]["share_price"] if k in r["implied"] else 0 for r in rows] for k in ("min", "p25", "median", "p75", "max") if any(k in r["implied"] for r in rows)}))
        b = iv["bridge"]
        if b:
            out += card("Enterprise value to equity value bridge", "Cash, non-core assets and NOLs add; debt, preferred, NCI, pensions and leases subtract.",
                        waterfall([(k.replace("_", " ").title(), v) for k, v in b.items() if v] + [("Bridge total", iv["bridge_total"])], totals=(len([v for v in b.values() if v]),)))
    if pr:
        names = [d["target"] for d in pr["deals"]]
        series = {l: [d["multiples"].get(l) if isinstance(d["multiples"].get(l), (int, float)) else 0 for d in pr["deals"]] for l in pr["summary"]}
        out += card("Precedent transaction multiples", "Deal multiples include a control premium, so they usually sit above trading comps.", column_chart(names, series, fmt="x"), list(series), _table(names, series, fmt="x"))
        if pr["premium_summary"]:
            prem = {l: [d["premiums"].get(l, 0) for d in pr["deals"]] for l in pr["premium_summary"]}
            out += card("Offer premiums to undisturbed price", "Premium paid over the 1-day, 1-week and 1-month prior share price.", column_chart(names, prem, fmt="pct"), list(prem))
    return out


def _projection(res: Dict[str, Any]) -> str:
    yrs = [str(y) for y in res["years"]]; IS, BS, CF = res["income_statement"], res["balance_sheet"], res["cash_flow"]
    out = tiles([("Revenue (final)", _fmt(IS["Revenue"][-1]), ""), ("EBIT margin (final)", _fmt(IS["EBIT"][-1] / IS["Revenue"][-1] if IS["Revenue"][-1] else 0, "pct"), ""), ("Closing cash", _fmt(BS["Cash"][-1]), ""), ("Balance check", "OK" if res["balanced"] else "ERROR", "")])
    prod = {k: v["revenue"] for k, v in res["sales"].items()}
    out += card("Revenue by product", "Which products drive growth, and is the mix shifting?", column_chart(yrs, prod, stacked=True), list(prod), _table(yrs, prod))
    opex = {k: v for k, v in res["opex"].items()}; opex["Wages and Benefits"] = IS["Wages and Benefits"]
    top = dict(sorted(opex.items(), key=lambda kv: -sum(kv[1]))[:7]); rest = [sum(v[i] for k, v in opex.items() if k not in top) for i in range(len(yrs))]
    if any(rest): top["Other"] = rest
    out += card("Operating expenses", "Where does the cost base sit, and how does it scale with revenue?", column_chart(yrs, top, stacked=True), list(top), _table(yrs, top))
    pay = {t: v["headcount"] for t, v in res["payroll"]["types"].items()}
    out += card("Headcount by type", "How does staffing grow against the revenue plan?", column_chart(yrs, pay, stacked=True), list(pay))
    out += card("Profitability", "Gross, operating and net margin trend.", line_chart(yrs, {"Gross margin": [a / b for a, b in zip(IS["Gross Margin"], IS["Revenue"])], "EBIT margin": [a / b for a, b in zip(IS["EBIT"], IS["Revenue"])], "Net margin": [a / b for a, b in zip(IS["Net Earnings"], IS["Revenue"])]}, fmt="pct"), ["Gross margin", "EBIT margin", "Net margin"])
    cf = {"Operations": CF["Cash from Operations"], "Investing": [-x for x in CF["Cash from Investing"]], "Financing": CF["Cash from Financing"]}
    out += card("Cash flow by activity", "Is the plan self-funding?", column_chart(yrs, cf, stacked=True), list(cf), _table(yrs, {**cf, "Closing cash": CF["Closing Cash Balance"]}))
    flat = [{k: v for k, v in _flat(r).items()} for r in res["ratios"]]
    liq = {"Current ratio": [f["liquidity.current_ratio"] for f in flat], "Quick ratio": [f["liquidity.quick_ratio"] for f in flat], "Debt / equity": [f["leverage.debt_to_equity"] for f in flat]}
    out += card("Liquidity and leverage ratios", "Can the business meet short-term obligations, and how geared is it?", line_chart(yrs, liq, fmt="x"), list(liq), _table(yrs, liq, "x"))
    return out


def _flat(r):
    from .ratios import flatten
    return flatten(r)


CATALOG: Dict[str, Dict[str, Any]] = {
    "three_statement": {"builder": _three_statement, "charts": [
        ("KPI tiles", "revenue, net margin, cash, balance check", "headline numbers, not a chart"),
        ("Revenue and net earnings", "IS rows", "grouped columns: growth vs bottom line"),
        ("Margin structure", "gross / net margin", "lines: profitability trend"),
        ("Cash flow by activity", "CFO / CFI / CFF", "stacked columns: self-funding?"),
        ("Cash bridge", "opening → closing cash", "waterfall: what moved cash"),
        ("Asset composition", "cash, AR, inventory, PP&E", "stacked columns: capital deployment"),
        ("Working-capital days", "AR / inventory / AP days", "lines: cash conversion"),
        ("Leverage and coverage", "debt/equity, interest cover", "lines: de-risking")]},
    "dcf": {"builder": _dcf, "charts": [
        ("KPI tiles", "EV, value/share, upside, IRR", "headline numbers"),
        ("UFCF build", "EBIT, taxes, D&A, capex, ΔNWC", "stacked columns: what drives FCF"),
        ("EV bridge", "PV forecast, PV terminal, cash, debt", "waterfall: forecast vs terminal, EV → equity"),
        ("Terminal value cross-check", "perpetuity vs multiple", "columns: do the methods agree"),
        ("Sensitivity heatmap", "WACC × g grid", "diverging heatmap centred on market price"),
        ("Football field", "valuation ranges vs price", "range bars: where does value sit")]},
    "lbo": {"builder": _lbo, "charts": [
        ("KPI tiles", "IRR, MOIC, exit equity, entry multiple", "headline numbers"),
        ("Sources and uses", "equity, tranches vs uses", "stacked columns: funding structure"),
        ("Debt paydown", "tranche balances by year", "stacked columns: deleveraging"),
        ("EBITDA and leverage", "EBITDA, NI, debt/EBITDA", "columns + line"),
        ("Returns attribution", "EBITDA growth, multiple expansion, deleveraging", "waterfall: source of equity gain"),
        ("IRR sensitivity", "scenario × exit multiple", "heatmap (the workbook's data table)")]},
    "merger": {"builder": _merger, "charts": [
        ("KPI tiles", "accretion %, premium, purchase multiple, new shares", "headline numbers"),
        ("EPS standalone vs combined", "acquirer / target / combined EPS", "columns: accretion / dilution"),
        ("Contribution analysis", "EBITDA, NI, ownership", "stacked columns: who contributes vs who owns"),
        ("Funding mix", "cash / debt / stock", "stacked column"),
        ("Multiples", "EV/EBITDA, P/E", "grouped columns: re-rating"),
        ("Accretion sensitivity", "premium × % stock", "diverging heatmap centred on zero"),
        ("Pro forma accretion by year", "reported vs adjusted", "columns"),
        ("Purchase price allocation", "book value, write-ups, DTL, goodwill", "waterfall"),
        ("Pre-tax deal effects", "synergies vs deal costs", "stacked columns"),
        ("Acquisition debt", "balance and interest", "columns")]},
    "comps": {"builder": _comps, "charts": [
        ("KPI tiles", "current price, implied range, peer / deal counts", "headline numbers"),
        ("Football field", "low–high implied price per method + current price", "range bars"),
        ("Peer EV multiples", "EV/Revenue, EV/EBITDA per peer", "grouped columns"),
        ("Peer equity multiples", "P/E per peer", "grouped columns"),
        ("Multiple statistics", "25th–75th percentile per multiple", "range bars + stats table"),
        ("Implied share price by multiple", "p25–p75 implied price", "range bars vs current"),
        ("EV to equity bridge", "cash, NOLs, debt, NCI …", "waterfall"),
        ("Precedent multiples", "EV/Revenue, EV/EBITDA, EV/EBIT per deal", "grouped columns"),
        ("Offer premiums", "1-day / 1-week / 1-month", "grouped columns")]},
    "projection": {"builder": _projection, "charts": [
        ("KPI tiles", "revenue, EBIT margin, cash, balance check", "headline numbers"),
        ("Revenue by product", "product revenue", "stacked columns: mix"),
        ("Operating expenses", "opex by category (top 7 + Other)", "stacked columns"),
        ("Headcount by type", "payroll headcount", "stacked columns"),
        ("Profitability", "gross / EBIT / net margin", "lines"),
        ("Cash flow by activity", "CFO / CFI / CFF", "stacked columns"),
        ("Liquidity and leverage ratios", "current, quick, D/E", "lines")]},
}


def report_for(engine: str, result: Dict[str, Any], path: str | Path, title: Optional[str] = None, subtitle: str = "") -> Path:
    spec = CATALOG[engine]
    body = spec["builder"](result)
    html_out = report(title or f"{engine.replace('_', ' ').title()} — charts", subtitle or "Generated by financial-analysis-toolkit (finmodel.charts)", body)
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(html_out)
    return p


def catalog_markdown() -> str:
    out = ["# Chart templates: data → analysis → visual", "", "Every engine output has a fixed set of charts; each row says what data feeds it, what question it answers, and the form used.", ""]
    for eng, spec in CATALOG.items():
        out += [f"## {eng}", "", "| chart | data | analysis / form |", "|---|---|---|"]
        out += [f"| {a} | {b} | {c} |" for a, b, c in spec["charts"]]
        out.append("")
    return "\n".join(out)
