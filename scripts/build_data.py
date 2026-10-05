#!/usr/bin/env python3
"""Excel -> JSON for the BI Bot website.
   python3 scripts/build_data.py
 Reads data/HR_Recruitment_and_Helpdesk_Tracker.xlsx and QUESTION_LIBRARY.md, writes:
   public/data/<Table>.json   (one per table, loaded on demand by the Dataset tab)
   src/data/tables.json       (Dataset sidebar manifest)
   src/data/answers.json      (98 fixed Q&A: chart spec + explanation)
   src/data/dashboard.json    (15 dashboard charts + KPI strip)
"""
import os, re, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
import openpyxl, qlib
from load import load, SRC
from qlib import *
import q_helpdesk, q_pay, q_people, q_hiring  # noqa: registers questions

CAT_META = {  # icon + accent per category (order = library order)
    1: ('LifeBuoy', 'blue'), 2: ('Palmtree', 'cyan'), 3: ('Wallet', 'violet'), 4: ('HeartPulse', 'rose'), 5: ('Receipt', 'amber'),
    6: ('FileText', 'emerald'), 7: ('BookOpen', 'indigo'), 8: ('Users', 'sky'), 9: ('Briefcase', 'orange'), 10: ('Mic', 'fuchsia')}
KIND = dict(bar='Bar chart', hbar='Ranked bars', line='Line chart', area='Area chart', donut='Donut chart', gauge='Gauge', funnel='Funnel', heatmap='Heatmap',
            treemap='Treemap', combo='Combo chart', sankey='Flow diagram', table='Table', scatter='Scatter plot')

def parse_library():
    cats, qs, cur = [], {}, None
    for line in open('QUESTION_LIBRARY.md', encoding='utf-8'):
        if line.startswith('## Dashboard'): break
        m = re.match(r'^## (\d+)\. (.+?) \((\d+)\)\s*$', line)
        if m: cur = int(m.group(1)); cats.append(dict(id=cur, name=m.group(2), count=int(m.group(3)))); continue
        m = re.match(r'^(\d+)\. (.+)$', line)
        if m and cur: qs[int(m.group(1))] = (cur, m.group(2).strip())
    return cats, qs

def jsonable(v):
    if isinstance(v, (dt.datetime, dt.date)): return v.strftime('%Y-%m-%d')
    if isinstance(v, dt.time): return v.strftime('%H:%M')
    if isinstance(v, float): return round(v, 4) if v != int(v) else int(v)
    return v

def main():
    T = load()
    for k, (h, b) in T.items(): qlib.D[k] = [dict(zip(h, r)) for r in b]

    # ---- tables
    os.makedirs('public/data', exist_ok=True); os.makedirs('src/data', exist_ok=True)
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True); purpose = {}
    for r in wb['README'].iter_rows(values_only=True):
        if r[0] in T and r[1] in ('Master', 'Core', 'Config') and isinstance(r[3], str): purpose.setdefault(r[0], r[3])
    groups = [('Helpdesk & Payroll', 'LifeBuoy', ['Helpdesk_Tickets', 'Leave_Requests', 'Leave_Balances', 'Payslips', 'Reimbursement_Claims', 'Benefit_Enrollments', 'Dependents', 'Document_Requests', 'Salary_Structure', 'Salary_Revisions', 'Employee_HR_Profile']),
              ('Policies & Reference', 'BookOpen', ['HR_Policies', 'HR_FAQs', 'Leave_Types', 'Holiday_Calendar', 'Payroll_Calendar', 'Benefit_Plans', 'Reimbursement_Policy', 'Document_Types']),
              ('Recruitment', 'Briefcase', ['Job_Requisitions', 'Candidates', 'Applications', 'Interviews', 'Interview_Panel', 'Offers', 'Sources', 'Rounds', 'Round_Plan', 'Rejection_Reasons', 'Roles', 'Experience_Levels']),
              ('Company', 'Building2', ['Employees', 'Departments', 'Locations'])]
    assert sorted(sum((g[2] for g in groups), [])) == sorted(T), set(T) ^ set(sum((g[2] for g in groups), []))
    manifest = []
    for gname, gicon, names in groups:
        items = []
        for nme in names:
            h, b = T[nme]
            json.dump(dict(columns=h, rows=[[jsonable(c) for c in r] for r in b]), open(f'public/data/{nme}.json', 'w'), separators=(',', ':'), ensure_ascii=False)
            items.append(dict(name=nme, rows=len(b), cols=len(h), about=purpose.get(nme, '')))
        manifest.append(dict(group=gname, icon=gicon, tables=items))
    json.dump(manifest, open('src/data/tables.json', 'w'), indent=1, ensure_ascii=False)

    # ---- questions
    cats, texts = parse_library()
    assert len(texts) == 98 and set(texts) == set(REG), (len(texts), set(texts) ^ set(REG))
    out = []
    for num in sorted(REG):
        meta = REG[num]; res = meta['fn'](); cat, text = texts[num]
        assert {'briefing', 'kpis', 'chart', 'insights'} <= set(res), num
        out.append(dict(id=num, cat=cat, q=text, icon=meta['icon'], badge=meta['badge'], src=meta['src'], kind=KIND[res['chart']['type']], **res))
    cj = [dict(c, icon=CAT_META[c['id']][0], accent=CAT_META[c['id']][1]) for c in cats]
    assert all(sum(1 for o in out if o['cat'] == c['id']) == c['count'] for c in cats)
    json.dump(dict(categories=cj, questions=out, asOf='2026-09-30', rows={k: len(v[1]) for k, v in T.items()}), open('src/data/answers.json', 'w'), separators=(',', ':'), ensure_ascii=False, default=str)

    # ---- dashboard
    json.dump(build_dashboard(), open('src/data/dashboard.json', 'w'), separators=(',', ':'), ensure_ascii=False, default=str)
    print('questions:', len(out), '| tables:', sum(len(g['tables']) for g in manifest))

def build_dashboard():
    TK = D['Helpdesk_Tickets']; ms = month_range(dt.date(2025, 1, 1), ASOF); E = D['Employees']
    qs = quarter_ends(dt.date(2023, 12, 31), ASOF)
    hc = [sum(1 for e in E if e['Date_of_Joining'] <= d and (not e['Exit_Date'] or e['Exit_Date'] > d)) for d in qs]
    cnt = Counter(som(t['Created_Date']) for t in TK)
    sla = []
    for m in ms:
        r = [t for t in TK if som(t['Created_Date']) == m and t['SLA_Met']]; sla.append(pct(sum(t['SLA_Met'] == 'Yes' for t in r), len(r)))
    ai = []
    for m in ms[-8:]:
        r = [t for t in TK if som(t['Created_Date']) == m]; ai.append(pct(sum(t['Channel'] == 'AI Copilot' for t in r), len(r)))
    pm = month_range(dt.date(2025, 4, 1), dt.date(2026, 9, 1)); gr = Counter()
    for p in D['Payslips']: gr[p['Pay_Month']] += p['Gross_Earnings']
    R = D['Job_Requisitions']; op = [sum(1 for r in R if r['Req_Open_Date'] <= d and (not r['Req_Closed_Date'] or r['Req_Closed_Date'] > d) and r['Req_Status'] != 'Cancelled') for d in qs]
    def dl(a, b): return dict(pct=round(100 * (a - b) / b, 1) if b else 0, up=a >= b)
    kp = [dict(label='People working here', num=hc[-1], fmt='int', sub='vs last quarter', delta=dl(hc[-1], hc[-2]), spark=hc, icon='Users', accent='blue'),
          dict(label='Help requests this month', num=cnt[ms[-1]], fmt='int', sub='Sep 2026', delta=dl(cnt[ms[-1]], cnt[ms[-2]]), spark=[cnt[m] for m in ms], icon='LifeBuoy', accent='cyan'),
          dict(label='Solved on time', num=sla[-1], fmt='pct', sub='of solved requests', delta=dl(sla[-1], sla[-2]), spark=sla, icon='CheckCircle2', accent='emerald'),
          dict(label='Answered by AI Copilot', num=ai[-1], fmt='pct', sub='of requests this month', delta=dl(ai[-1], ai[-2]), spark=ai, icon='Bot', accent='violet'),
          dict(label='Monthly salary cost', num=round(gr[pm[-1]]), fmt='inr', sub='Sep 2026 gross', delta=dl(gr[pm[-1]], gr[pm[-2]]), spark=[round(gr[m]) for m in pm], icon='Wallet', accent='amber'),
          dict(label='Open job openings', num=op[-1], fmt='int', sub='being hired for', delta=dl(op[-1], op[-2]), spark=op, icon='Briefcase', accent='rose')]
    ch = [(4, 'Help requests & AI Copilot growth', 'Monthly requests by channel — AI Copilot launched in March 2026', 'wide'),
          (7, 'Which requests are solved on time?', 'Share of requests answered within the promised time', 'normal'),
          (9, 'How happy are employees?', 'Ratings given after a request is solved', 'normal'),
          (5, 'Requests solved by the AI Copilot', 'Since the launch in March 2026', 'normal'),
          (20, 'Leave used, team by team', 'Share of the 2026 leave quota already used', 'normal'),
          (22, 'When do people take leave?', 'Leave days by month and leave type (2025)', 'wide'),
          (31, 'How are salaries spread?', 'Employees by yearly package', 'normal'),
          (25, 'Monthly salary cost', 'Gross pay vs take-home pay', 'normal'),
          (38, 'Benefit plan members', 'Employees enrolled in each plan', 'normal'),
          (58, 'Documents delivered on time', 'Promised time met, by document', 'normal'),
          (84, 'The hiring funnel', 'From application to joining', 'normal'),
          (49, 'Where does reimbursement money go?', 'Approved claims by expense type', 'normal'),
          (75, 'People in each department', 'Current headcount by team', 'normal'),
          (86, 'Best hiring sources', 'People hired and hire rate by source', 'wide'),
          (96, 'What happens to job offers?', 'Outcome of every offer released', 'normal')]
    return dict(kpis=kp, charts=[dict(qid=a, title=b, subtitle=c, span=d) for a, b, c, d in ch])

if __name__ == '__main__': main()
