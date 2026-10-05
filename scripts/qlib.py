"""Shared helpers + registry for the 98 fixed questions."""
import datetime as dt, statistics
from collections import Counter, defaultdict

ASOF = dt.date(2026, 9, 30)
D = {}          # table name -> list[dict]   (filled by build_data.py)
REG = {}        # question number -> dict(meta, fn)

def q(num, icon, badge=None, src=()):
    def deco(fn):
        REG[num] = dict(icon=icon, badge=badge, src=list(src), fn=fn); return fn
    return deco

# ---------- number helpers
def mean(v):
    v = [x for x in v if x is not None]; return sum(v) / len(v) if v else 0
def median(v):
    v = [x for x in v if x is not None]; return statistics.median(v) if v else 0
def r1(x): return round(x, 1)
def r2(x): return round(x, 2)
def n(x): return f"{x:,.0f}"
def pct(a, b, nd=1): return round(100 * a / b, nd) if b else 0
def inr(x):
    a = abs(x)
    if a >= 1e7: return f"₹{x/1e7:.2f} Cr"
    if a >= 1e5: return f"₹{x/1e5:.1f} L"
    if a >= 1e3: return f"₹{x/1e3:.1f}K"
    return f"₹{x:,.0f}"
def lpa(x): return f"₹{x:.1f} L"
def ml(d): return d.strftime("%b '%y")
def som(d): return dt.date(d.year, d.month, 1)
def month_range(a, b):
    out = []; d = som(a)
    while d <= b:
        out.append(d); d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return out
def quarter_ends(a, b):
    out = []; y = a.year
    while True:
        for m, dd in ((3, 31), (6, 30), (9, 30), (12, 31)):
            d = dt.date(y, m, dd)
            if d < a: continue
            if d > b: return out + [b] if out and out[-1] < b else out
            out.append(d)
        y += 1
def qlabel(d): return f"Q{(d.month - 1)//3 + 1} '{d.year % 100:02d}"
def kpi(label, num, fmt='int', sub=None, tone=None):
    return dict(label=label, num=num, fmt=fmt, sub=sub, tone=tone)
def counter_items(c, k=None, tone=None):
    items = c.most_common(k) if k else sorted(c.items(), key=lambda x: -x[1])
    return [dict(name=a, value=b) for a, b in items]
def bucket(vals, edges, labels):
    """edges ascending upper bounds (exclusive) ; last bucket open ended"""
    out = [0] * len(labels)
    for v in vals:
        if v is None: continue
        for i, e in enumerate(edges):
            if v < e: out[i] += 1; break
        else: out[-1] += 1
    return out
WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
LEVELS = ['Intern', 'Fresher', 'Junior', 'Mid', 'Senior', 'Lead']
def groupby(rows, key):
    g = defaultdict(list)
    for r in rows: g[key(r)].append(r)
    return g
def DN(): return {d['Dept_ID']: d['Dept_Name'] for d in D['Departments']}
def short(s, k=46): return s if len(s) <= k else s[:k - 1].rstrip() + '…'
