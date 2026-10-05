from qlib import *

def _ps(): return D['Payslips']
def _act_ids(): return {e['Emp_ID'] for e in D['Employees'] if e['Employment_Status'] == 'Active'}
MS = month_range(dt.date(2025, 4, 1), dt.date(2026, 9, 1))

# ───────────────────────── 3. PAYROLL ─────────────────────────
@q(25, 'Wallet', 'Popular', ['Payslips'])
def _():
    gr = Counter(); nt = Counter(); hc = Counter()
    for p in _ps(): gr[p['Pay_Month']] += p['Gross_Earnings']; nt[p['Pay_Month']] += p['Net_Pay']; hc[p['Pay_Month']] += 1
    g = [round(gr[m]) for m in MS]; nv = [round(nt[m]) for m in MS]
    return dict(
        briefing=f"In Sep 2026 the company paid **{inr(g[-1])}** in gross salary and **{inr(nv[-1])}** took home after deductions — **{pct(g[-1] - nv[-1], g[-1], 0):.0f}%** went to PF, tax and other deductions. Monthly salary cost has grown **{pct(g[-1] - g[0], g[0], 0):.0f}%** since Apr 2025.",
        kpis=[kpi('Gross pay (Sep 2026)', g[-1], 'inr'), kpi('Take-home (Sep 2026)', nv[-1], 'inr', tone='up'), kpi('Employees paid', hc[MS[-1]], sub='Sep 2026'), kpi('Total paid since Apr 2025', sum(nv), 'inr', 'take-home')],
        chart=dict(type='area', categories=[ml(m) for m in MS], series=[dict(name='Gross pay', data=g), dict(name='Take-home pay', data=nv)], fmt='inr'),
        insights=[f"Payroll grew from **{n(hc[MS[0]])}** to **{n(hc[MS[-1]])}** employees paid per month.", "Take-home includes any reimbursements paid through the payslip."])

@q(26, 'PieChart', None, ['Salary_Structure'])
def _():
    act = _act_ids(); S = [s for s in D['Salary_Structure'] if s['Emp_ID'] in act]
    comps = [('Basic salary', 'Basic_Monthly'), ('House rent (HRA)', 'HRA_Monthly'), ('Special allowance', 'Special_Allowance_Monthly'), ('Employer PF', 'Employer_PF_Monthly'), ('Gratuity', 'Gratuity_Monthly'), ('Insurance (employer)', 'Employer_Insurance_Monthly_INR')]
    vals = [(a, mean([s[c] for s in S])) for a, c in comps]; tot = sum(v for _, v in vals); avgm = mean([s['Monthly_CTC_INR'] for s in S])
    return dict(
        briefing=f"A typical employee costs **{inr(avgm)}** a month. **Basic salary** is the largest part (**{pct(vals[0][1], tot, 0):.0f}%**), followed by special allowance and HRA.",
        kpis=[kpi('Average monthly cost', round(avgm), 'inr', 'per employee'), kpi('Basic salary', round(vals[0][1]), 'inr'), kpi('HRA', round(vals[1][1]), 'inr')],
        chart=dict(type='donut', items=[dict(name=a, value=round(v)) for a, v in vals], fmt='inr', centerValue=inr(avgm), centerLabel='per month'),
        insights=["Employer PF, gratuity and insurance are paid by the company on top of take-home — they are part of the CTC, not the salary credited to your bank."])

@q(27, 'Receipt', None, ['Payslips'])
def _():
    cols = [('Provident Fund', 'PF_Employee'), ('Professional tax', 'Professional_Tax'), ('Income tax (TDS)', 'TDS'), ('Other deductions', 'Other_Deductions')]; c = {a: Counter() for a, _ in cols}
    for p in _ps():
        for a, k in cols: c[a][p['Pay_Month']] += p[k]
    ser = [dict(name=a, data=[round(c[a][m]) for m in MS]) for a, _ in cols]; tot = {a: sum(c[a].values()) for a, _ in cols}; T = sum(tot.values())
    return dict(
        briefing=f"Since Apr 2025, **{inr(T)}** has been deducted from salaries. **Income tax (TDS)** is the biggest deduction at **{pct(tot['Income tax (TDS)'], T, 0):.0f}%**, followed by Provident Fund at **{pct(tot['Provident Fund'], T, 0):.0f}%**.",
        kpis=[kpi('Total deductions', T, 'inr'), kpi('Income tax (TDS)', tot['Income tax (TDS)'], 'inr'), kpi('Provident Fund', tot['Provident Fund'], 'inr')],
        chart=dict(type='bar', stacked=True, categories=[ml(m) for m in MS], series=ser, fmt='inr'),
        insights=[f"Employees paid **{inr(tot['Income tax (TDS)'])}** in income tax (TDS) in total, against **{inr(tot['Provident Fund'])}** into Provident Fund.", "PF is calculated at 12% of basic salary up to the ₹15,000 monthly wage ceiling."])

@q(28, 'Banknote', None, ['Salary_Structure', 'Departments'])
def _():
    act = _act_ids(); dn = DN(); g = groupby([s for s in D['Salary_Structure'] if s['Emp_ID'] in act], lambda s: s['Dept_ID'])
    rows = sorted([(dn[d], r1(mean([s['Annual_CTC_INR'] for s in v]) / 1e5)) for d, v in g.items()], key=lambda x: x[1])
    return dict(
        briefing=f"**{rows[-1][0]}** has the highest average salary package (**{lpa(rows[-1][1])} a year**), while **{rows[0][0]}** has the lowest at **{lpa(rows[0][1])}**.",
        kpis=[kpi('Highest average', rows[-1][1], 'lpa', rows[-1][0]), kpi('Lowest average', rows[0][1], 'lpa', rows[0][0])],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Average yearly package', data=[r[1] for r in rows])], fmt='lpa', rank=True),
        insights=["Averages are for current employees and include leadership roles in each team.", "L = Lakh (1 Lakh = ₹1,00,000) per year."])

@q(29, 'CalendarMinus', None, ['Payslips'])
def _():
    lop = Counter(); emp = Counter()
    for p in _ps():
        if p['LOP_Days']: lop[p['Pay_Month']] += p['LOP_Days']; emp[p['Pay_Month']] += 1
    d = [round(lop[m]) for m in MS]; e = [emp[m] for m in MS]
    return dict(
        briefing=f"Employees lost **{n(sum(d))} days of pay** (Loss of Pay) since Apr 2025 — about **{n(mean(d))}** days a month, affecting around **{n(mean(e))}** people each month.",
        kpis=[kpi('LOP days in total', sum(d)), kpi('Avg. per month', round(mean(d)), 'int', 'days'), kpi('Employees affected / month', round(mean(e)))],
        chart=dict(type='combo', categories=[ml(m) for m in MS], series=[dict(name='Pay-less days', data=d, kind='bar', axis=0, fmt='int'), dict(name='Employees affected', data=e, kind='line', axis=1, fmt='int')], fmt='int', yNames=['Days', 'Employees']),
        insights=["Loss of Pay happens when leave is taken without balance or an employee is absent without approval."])

@q(30, 'BadgeCheck', None, ['Payslips', 'Payroll_Calendar'])
def _():
    cal = {c['Pay_Month']: c['Salary_Credit_Date'] for c in D['Payroll_Calendar']}; on = Counter(); tot = Counter(); late_days = []
    for p in _ps():
        t = cal.get(p['Pay_Month']); tot[p['Pay_Month']] += 1
        if t and p['Payment_Date'] <= t: on[p['Pay_Month']] += 1
        elif t: late_days.append((p['Payment_Date'] - t).days)
    pt = sum(on.values()); tt = sum(tot.values()); pc = [pct(on[m], tot[m]) for m in MS]
    return dict(
        briefing=f"**{pct(pt, tt)}%** of all salaries ({n(pt)} of {n(tt)}) were credited on or before the planned salary date. Every payslip has been paid.",
        kpis=[kpi('Paid on time', pct(pt, tt), 'pct', tone='up'), kpi('Payslips paid', tt), kpi('Paid late', tt - pt, tone='down' if tt - pt else None)],
        chart=dict(type='gauge', value=pct(pt, tt), max=100, fmt='pct', label='Paid on time'),
        insights=[f"Salary is credited on the last working day of the month; the payslip is released the same day." if tt - pt == 0 else f"Late payments were delayed by **{r1(mean(late_days))} days** on average."])

@q(31, 'BarChart3', 'Key', ['Salary_Structure'])
def _():
    act = _act_ids(); v = [s['Annual_CTC_INR'] / 1e5 for s in D['Salary_Structure'] if s['Emp_ID'] in act]
    labs = ['Under ₹3 L', '₹3–5 L', '₹5–8 L', '₹8–12 L', '₹12–20 L', '₹20–40 L', 'Over ₹40 L']; bk = bucket(v, [3, 5, 8, 12, 20, 40], labs); i = bk.index(max(bk))
    return dict(
        briefing=f"Most employees (**{n(bk[i])}**, {pct(bk[i], len(v), 0):.0f}%) earn in the **{labs[i]}** range. The average package is **{lpa(mean(v))}** and the middle value is **{lpa(median(v))}** a year.",
        kpis=[kpi('Average package', r1(mean(v)), 'lpa'), kpi('Middle value', r1(median(v)), 'lpa', 'median'), kpi('Highest', r1(max(v)), 'lpa')],
        chart=dict(type='bar', categories=labs, series=[dict(name='Employees', data=bk)], fmt='int', gradient=True),
        insights=[f"**{pct(sum(bk[:3]), len(v), 0):.0f}%** of employees earn under ₹8 L a year, while **{n(bk[-1] + bk[-2])}** earn above ₹20 L.", "L = Lakh per year (CTC)."])

@q(32, 'TrendingUp', None, ['Salary_Revisions'])
def _():
    cyc = ['Apr-2024', 'Apr-2025', 'Apr-2026']; g = groupby(D['Salary_Revisions'], lambda r: r['Revision_Cycle'])
    avg = [r1(mean([r['Increment_Pct'] * 100 for r in g[c]])) for c in cyc]; cnt = [len(g[c]) for c in cyc]
    return dict(
        briefing=f"The average pay raise in the **April 2026** cycle was **{avg[2]}%** for **{n(cnt[2])}** employees, compared with **{avg[1]}%** in 2025 and **{avg[0]}%** in 2024.",
        kpis=[kpi('2026 average raise', avg[2], 'pct', f'{n(cnt[2])} employees'), kpi('2025 average raise', avg[1], 'pct'), kpi('2024 average raise', avg[0], 'pct')],
        chart=dict(type='bar', categories=['April 2024', 'April 2025', 'April 2026'], series=[dict(name='Average raise %', data=avg)], fmt='pct', gradient=True),
        insights=[f"The number of employees receiving a revision grew from **{cnt[0]}** to **{cnt[2]}** as the company expanded."])

@q(33, 'Award', None, ['Salary_Revisions'])
def _():
    g = groupby(D['Salary_Revisions'], lambda r: r['Performance_Rating']); rs = [1, 2, 3, 4, 5]
    avg = [r1(mean([r['Increment_Pct'] * 100 for r in g[k]])) for k in rs]
    return dict(
        briefing=f"Yes — better performers get bigger raises. Employees rated **5** received **{avg[4]}%** on average, while those rated **1** received **{avg[0]}%**.",
        kpis=[kpi('Top performers (5 ★)', avg[4], 'pct', 'avg raise', 'up'), kpi('Average (3 ★)', avg[2], 'pct', 'avg raise'), kpi('Lowest rated (1 ★)', avg[0], 'pct', 'avg raise', 'down')],
        chart=dict(type='bar', categories=[f'Rating {k}' for k in rs], series=[dict(name='Average raise %', data=avg)], fmt='pct', pointTones=['bad', 'warn', 'neutral', 'good', 'brand']),
        insights=["Policy guideline: raises of 0%, 4%, 8%, 12% and 18% for ratings 1 to 5.", f"Number of employees at each rating: " + ', '.join(f"**{k}★** {len(g[k])}" for k in rs) + '.'])

@q(34, 'ListChecks', None, ['Salary_Revisions'])
def _():
    c = Counter(r['Revision_Type'] for r in D['Salary_Revisions']); tot = sum(c.values()); tone = {'Annual Increment': 'brand', 'Merit Increment (High Performer)': 'good', 'No Increment': 'warn'}
    return dict(
        briefing=f"**{pct(c['Annual Increment'], tot, 0):.0f}%** of salary changes were the normal yearly increment. **{c['Merit Increment (High Performer)']}** high performers earned an extra merit increment and **{c['No Increment']}** employees got no raise.",
        kpis=[kpi('Yearly increments', c['Annual Increment']), kpi('Merit increments', c['Merit Increment (High Performer)'], tone='up'), kpi('No increment', c['No Increment'], tone='down')],
        chart=dict(type='donut', items=[dict(name=k, value=v, tone=tone.get(k)) for k, v in c.most_common()], fmt='int', centerValue=n(tot), centerLabel='revisions'),
        insights=["Policy guideline: raises of 0%, 4%, 8%, 12% and 18% for performance ratings 1 to 5."])

@q(35, 'CalendarDays', None, ['Payroll_Calendar'])
def _():
    C = sorted(D['Payroll_Calendar'], key=lambda c: c['Pay_Month']); f = lambda d: d.strftime('%d %b %Y')
    rows = [[c['Pay_Month'].strftime('%B %Y'), f(c['Attendance_Cutoff_Date']), f(c['Reimbursement_Cutoff_Date']), f(c['Salary_Credit_Date']), f(c['Payslip_Release_Date']), c['Status']] for c in C]
    nxt = [c for c in C if c['Salary_Credit_Date'] > ASOF][0]
    return dict(
        briefing=f"Salary is credited on the **last working day** of every month. The next salary date is **{nxt['Salary_Credit_Date'].strftime('%d %b %Y')}**; attendance and reimbursement claims must be in by **{nxt['Attendance_Cutoff_Date'].strftime('%d %b')}**.",
        kpis=[kpi('Next salary date', (nxt['Salary_Credit_Date'] - ASOF).days, 'days', nxt['Salary_Credit_Date'].strftime('%d %b %Y') + ' — days to go'), kpi('Cut-off day', '25th', 'text', 'of every month')],
        chart=dict(type='table', columns=['Payroll month', 'Attendance cut-off', 'Claims cut-off', 'Salary credit', 'Payslip release', 'Status'], rows=rows),
        insights=["Claims submitted after the cut-off are paid in the next month's payroll."])

@q(36, 'HandCoins', None, ['Payslips'])
def _():
    r = Counter(); e = Counter()
    for p in _ps():
        if p['Reimbursement_INR']: r[p['Pay_Month']] += p['Reimbursement_INR']; e[p['Pay_Month']] += 1
    rv = [round(r[m]) for m in MS]; ev = [e[m] for m in MS]; tot = sum(rv); allnet = sum(p['Net_Pay'] for p in _ps())
    return dict(
        briefing=f"Reimbursements added **{inr(tot)}** to employees' pay since Apr 2025 — about **{pct(tot, allnet)}%** of all take-home. In Sep 2026, **{n(ev[-1])}** people received **{inr(rv[-1])}** extra.",
        kpis=[kpi('Reimbursed through payslips', tot, 'inr'), kpi('Sep 2026', rv[-1], 'inr'), kpi('People reimbursed (Sep 2026)', ev[-1])],
        chart=dict(type='combo', categories=[ml(m) for m in MS], series=[dict(name='Reimbursement paid', data=rv, kind='bar', axis=0, fmt='inr'), dict(name='Employees reimbursed', data=ev, kind='line', axis=1, fmt='int')], fmt='inr', yNames=['Amount', 'Employees']),
        insights=["Approved claims are paid together with salary in the payroll month they are approved for."])

# ───────────────────────── 4. BENEFITS ─────────────────────────
def _en(): return D['Benefit_Enrollments']
def _act(e): return e['Status'] == 'Active'

@q(37, 'HeartPulse', 'Popular', ['Benefit_Plans'])
def _():
    P = D['Benefit_Plans']
    rows = [[p['Plan_Name'], p['Category'], p['Coverage_Details'], f"₹{p['Employer_Contribution_Monthly_INR']:,}" if p['Employer_Contribution_Monthly_INR'] else '—', f"₹{p['Employee_Contribution_Monthly_INR']:,}" if p['Employee_Contribution_Monthly_INR'] else 'Free', p['Eligibility']] for p in P]
    return dict(
        briefing=f"Employees can choose from **{len(P)} benefit plans** across insurance, retirement, allowances, wellness and learning. Most are paid fully by the company.",
        kpis=[kpi('Benefit plans', len(P)), kpi('Insurance plans', sum(p['Category'] == 'Insurance' for p in P)), kpi('Free for employees', sum(not p['Employee_Contribution_Monthly_INR'] for p in P))],
        chart=dict(type='table', columns=['Benefit', 'Type', 'What it covers', 'Company pays / month', 'You pay / month', 'Who can join'], rows=rows),
        insights=["Health insurance covers self, spouse and up to 2 children; parents can be added through the Parental Top-up."])

@q(38, 'Users2', 'Key', ['Benefit_Enrollments'])
def _():
    c = Counter(e['Plan_Name'] for e in _en() if _act(e)); it = counter_items(c)[::-1]; t = c.most_common()
    return dict(
        briefing=f"**{t[0][0]}** and the other core plans cover all **{n(t[0][1])}** active full-time employees. Among optional benefits, **{[x for x in t if x[0] in ('Meal Card','Parental Health Top-up','NPS Employer Contribution')][0][0]}** is the most popular.",
        kpis=[kpi('Employees in core plans', t[0][1]), kpi('Meal Card members', c['Meal Card']), kpi('Parental top-up', c['Parental Health Top-up']), kpi('NPS members', c['NPS Employer Contribution'])],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Members', data=[i['value'] for i in it])], fmt='int', rank=True),
        insights=["Health, life, accident and PF are automatic for every full-time employee.", "Wellness check-ups, counselling and the learning budget don't need enrolment, so they are not counted here."])

@q(39, 'Heart', None, ['Benefit_Enrollments'])
def _():
    c = Counter(e['Coverage_Type'] for e in _en() if _act(e) and e['Plan_ID'] == 'BP01'); tot = sum(c.values()); it = counter_items(c)
    return dict(
        briefing=f"**{pct(c['Self'], tot, 0):.0f}%** of employees cover only themselves under health insurance. **{n(tot - c['Self'])}** have added their spouse, children or parents.",
        kpis=[kpi('Self only', c['Self']), kpi('With family', c['Self + Spouse'] + c['Self + Spouse + Children']), kpi('Parents added', c['Parents (1)'] + c['Parents (2)'])],
        chart=dict(type='donut', items=it, fmt='int', centerValue=n(tot), centerLabel='insured'),
        insights=["Health insurance (Medisure) is automatic; employees choose the coverage type when they join."])

@q(40, 'Scale', None, ['Benefit_Enrollments'])
def _():
    g = defaultdict(lambda: [0, 0])
    for e in _en():
        if _act(e): g[e['Plan_Name']][0] += e['Employer_Contribution_Monthly_INR']; g[e['Plan_Name']][1] += e['Employee_Contribution_Monthly_INR']
    rows = [(k, v) for k, v in g.items() if v[0] or v[1]]; rows.sort(key=lambda x: -(x[1][0] + x[1][1]))
    eo = sum(v[0] for k, v in rows); ee = sum(v[1] for k, v in rows)
    return dict(
        briefing=f"The company pays **{inr(eo)}** a month towards benefits, while employees contribute **{inr(ee)}**. That means the company covers **{pct(eo, eo + ee, 0):.0f}%** of the total cost.",
        kpis=[kpi('Company pays / month', eo, 'inr', tone='up'), kpi('Employees pay / month', ee, 'inr'), kpi('Company share', pct(eo, eo + ee), 'pct')],
        chart=dict(type='bar', stacked=True, categories=[k for k, _ in rows], series=[dict(name='Company pays', data=[round(v[0]) for _, v in rows]), dict(name='Employees pay', data=[round(v[1]) for _, v in rows])], fmt='inr'),
        insights=["Group health insurance and Provident Fund are the biggest company costs.", "Only plans with a monthly contribution are shown."])

@q(41, 'CircleDollarSign', None, ['Benefit_Enrollments'])
def _():
    qs = quarter_ends(dt.date(2020, 3, 31), ASOF); vals = []
    for d in qs: vals.append(round(sum(e['Employer_Contribution_Monthly_INR'] for e in _en() if e['Enrolled_Date'] <= d and (not e['End_Date'] or e['End_Date'] > d))))
    return dict(
        briefing=f"The company now spends **{inr(vals[-1])}** every month on employee benefits — up from **{inr(vals[0])}** in {qlabel(qs[0])}.",
        kpis=[kpi('Monthly benefits spend', vals[-1], 'inr'), kpi('Yearly (estimate)', vals[-1] * 12, 'inr'), kpi('Up vs a year ago', pct(vals[-1] - vals[-5], vals[-5], 0), 'pct', tone='up')],
        chart=dict(type='area', categories=[qlabel(d) for d in qs], series=[dict(name='Company benefits spend / month', data=vals)], fmt='inr'),
        insights=["Spend grows in line with headcount as every new full-time employee joins health insurance and PF."])

@q(42, 'Baby', None, ['Dependents'])
def _():
    A = [d for d in D['Dependents'] if d['Status'] == 'Active']; c = Counter(d['Relation'] for d in A)
    return dict(
        briefing=f"**{n(len(A))}** family members are covered today. **Spouses** ({n(c['Spouse'])}) and **children** ({n(c['Child'])}) make up most of them; **{n(c['Father'] + c['Mother'])}** are parents.",
        kpis=[kpi('Family members covered', len(A)), kpi('Spouses', c['Spouse']), kpi('Children', c['Child']), kpi('Parents', c['Father'] + c['Mother'])],
        chart=dict(type='donut', items=counter_items(c), fmt='int', centerValue=n(len(A)), centerLabel='covered'),
        insights=[f"Another **{n(sum(d['Status'] == 'Removed' for d in D['Dependents']))}** dependents were removed (for example after an employee left)."])

@q(43, 'Cake', None, ['Dependents'])
def _():
    A = [d for d in D['Dependents'] if d['Status'] == 'Active']; labs = ['0–5', '6–12', '13–18', '19–30', '31–45', '46–60', '60+']; ed = [6, 13, 19, 31, 46, 61]
    rel = [('Spouse', ['Spouse']), ('Child', ['Child']), ('Parents', ['Father', 'Mother'])]
    ser = [dict(name=a, data=bucket([d['Age_Years'] for d in A if d['Relation'] in r], ed, labs)) for a, r in rel]; ages = [d['Age_Years'] for d in A]
    return dict(
        briefing=f"Covered family members are on average **{r1(mean(ages))} years** old. **{pct(sum(1 for a in ages if a <= 12), len(ages), 0):.0f}%** are children under 13, and **{pct(sum(1 for a in ages if a > 60), len(ages), 0):.0f}%** are over 60.",
        kpis=[kpi('Average age', r1(mean(ages)), 'text', 'years'), kpi('Under 13', sum(1 for a in ages if a <= 12)), kpi('Over 60', sum(1 for a in ages if a > 60))],
        chart=dict(type='bar', stacked=True, categories=labs, series=ser, fmt='int'),
        insights=["Insurers price risk by age, so this helps plan premium costs for parents and seniors."])

@q(44, 'TrendingUp', 'Trend', ['Benefit_Enrollments'])
def _():
    qs = quarter_ends(dt.date(2020, 3, 31), ASOF); plans = ['Group Health Insurance', 'Meal Card', 'Parental Health Top-up', 'NPS Employer Contribution']
    ser = [dict(name=p, data=[sum(1 for e in _en() if e['Plan_Name'] == p and e['Enrolled_Date'] <= d and (not e['End_Date'] or e['End_Date'] > d)) for d in qs]) for p in plans]
    return dict(
        briefing=f"Health insurance members grew from **{n(ser[0]['data'][0])}** to **{n(ser[0]['data'][-1])}** since 2020. Among optional plans, **{n(ser[1]['data'][-1])}** use the Meal Card today.",
        kpis=[kpi('Health insurance members', ser[0]['data'][-1]), kpi('Meal Card members', ser[1]['data'][-1]), kpi('Parental top-up', ser[2]['data'][-1]), kpi('NPS members', ser[3]['data'][-1])],
        chart=dict(type='area', stacked=True, categories=[qlabel(d) for d in qs], series=ser, fmt='int'),
        insights=["Membership drops when employees leave, so the lines follow headcount."])

@q(45, 'Medal', None, ['Benefit_Enrollments', 'Departments'])
def _():
    dn = DN(); act = {e['Emp_ID']: e['Dept_ID'] for e in D['Employees'] if e['Employment_Status'] == 'Active'}; hc = Counter(act.values()); opt = set()
    for e in _en():
        if _act(e) and e['Plan_ID'] in ('BP02', 'BP06', 'BP07') and e['Emp_ID'] in act: opt.add(e['Emp_ID'])
    oc = Counter(act[e] for e in opt); rows = sorted([(dn[d], pct(oc[d], hc[d])) for d in hc], key=lambda x: x[1])
    return dict(
        briefing=f"**{pct(len(opt), len(act), 0):.0f}%** of employees use at least one optional benefit (Meal Card, Parental Top-up or NPS). **{rows[-1][0]}** leads with **{rows[-1][1]}%**.",
        kpis=[kpi('Using optional benefits', len(opt), sub=f'{pct(len(opt), len(act), 0):.0f}% of employees'), kpi('Highest team', rows[-1][1], 'pct', rows[-1][0]), kpi('Lowest team', rows[0][1], 'pct', rows[0][0])],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Employees using optional benefits', data=[r[1] for r in rows])], fmt='pct', rank=True),
        insights=["Optional benefits need the employee to opt in, so this shows who is making use of them."])

@q(46, 'ClipboardList', None, ['Benefit_Enrollments'])
def _():
    st = ['Active', 'Pending', 'Ceased']; g = groupby(_en(), lambda e: e['Plan_Name']); order = sorted(g, key=lambda k: -len(g[k]))[::-1]; c = Counter(e['Status'] for e in _en())
    ser = [dict(name={'Ceased': 'Ended', 'Active': 'Active', 'Pending': 'Pending'}[s], data=[sum(e['Status'] == s for e in g[k]) for k in order], tone={'Active': 'good', 'Pending': 'warn', 'Ceased': 'neutral'}[s]) for s in st]
    return dict(
        briefing=f"Of **{n(len(_en()))}** benefit enrolments, **{n(c['Active'])}** are active, **{c['Pending']}** are waiting to start and **{n(c['Ceased'])}** have ended (mostly when employees left).",
        kpis=[kpi('Active', c['Active'], tone='up'), kpi('New / pending', c['Pending']), kpi('Ended', c['Ceased'])],
        chart=dict(type='bar', orient='h', stacked=True, categories=order, series=ser, fmt='int'),
        insights=["Pending enrolments become active after the waiting period (e.g. 30 days for the parental top-up)."])

# ───────────────────────── 5. REIMBURSEMENTS ─────────────────────────
def _cl(): return D['Reimbursement_Claims']
CM = month_range(dt.date(2025, 4, 1), dt.date(2026, 9, 1))

@q(47, 'ReceiptText', 'Popular', ['Reimbursement_Claims'])
def _():
    C = _cl(); tot = len(C); ap = sum(c['Status'] in ('Approved', 'Paid') for c in C); pd = sum(c['Status'] == 'Paid' for c in C)
    claimed = sum(c['Claimed_Amount_INR'] for c in C); paid = sum(c['Approved_Amount_INR'] or 0 for c in C if c['Status'] in ('Paid', 'Approved'))
    return dict(
        briefing=f"Employees raised **{n(tot)}** expense claims worth **{inr(claimed)}**. **{pct(ap, tot, 0):.0f}%** were approved and **{inr(paid)}** has been approved or paid out.",
        kpis=[kpi('Claims raised', tot), kpi('Amount claimed', claimed, 'inr'), kpi('Approved / paid', paid, 'inr', tone='up'), kpi('Approval rate', pct(ap, tot), 'pct')],
        chart=dict(type='funnel', items=[dict(name='Claims raised', value=tot), dict(name='Approved', value=ap), dict(name='Paid to employees', value=pd)], fmt='int'),
        insights=[f"**{n(sum(c['Status'] == 'Rejected' for c in C))}** claims were rejected and **{sum(c['Status'] in ('Submitted','Under Review','Query Raised') for c in C)}** are still being reviewed."])

@q(48, 'LineChart', 'Trend', ['Reimbursement_Claims'])
def _():
    cl = Counter(); ap = Counter()
    for c in _cl(): cl[c['Claim_Month']] += c['Claimed_Amount_INR']; ap[c['Claim_Month']] += (c['Approved_Amount_INR'] or 0) if c['Status'] in ('Paid', 'Approved') else 0
    a = [round(cl[m]) for m in CM]; b = [round(ap[m]) for m in CM]
    return dict(
        briefing=f"Employees now claim about **{inr(mean(a[-4:-1]))}** a month, up from **{inr(a[0])}** in Apr 2025. Around **{pct(sum(b), sum(a), 0):.0f}%** of the money claimed is approved.",
        kpis=[kpi('Claimed in Sep 2026', a[-1], 'inr'), kpi('Approved in Sep 2026', b[-1], 'inr'), kpi('Total approved', sum(b), 'inr')],
        chart=dict(type='area', categories=[ml(m) for m in CM], series=[dict(name='Amount claimed', data=a), dict(name='Amount approved', data=b)], fmt='inr'),
        insights=["Claims grow with headcount, because most are monthly benefits like internet and mobile."])

@q(49, 'Coins', 'Key', ['Reimbursement_Claims'])
def _():
    c = Counter()
    for r in _cl():
        if r['Status'] in ('Paid', 'Approved'): c[r['Claim_Category']] += r['Approved_Amount_INR'] or 0
    it = [dict(name=k, value=round(v)) for k, v in c.most_common()]; tot = sum(c.values())
    return dict(
        briefing=f"**{it[0]['name']}** is the biggest expense (**{inr(it[0]['value'])}**, {pct(it[0]['value'], tot, 0):.0f}%), followed by **{it[1]['name']}** and **{it[2]['name']}**.",
        kpis=[kpi('Total reimbursed', tot, 'inr'), kpi('Top category', it[0]['value'], 'inr', it[0]['name']), kpi('Categories', len(it))],
        chart=dict(type='treemap', items=it, fmt='inr'),
        insights=[f"Small recurring claims (internet, mobile, gym) add up to **{pct(sum(c[k] for k in ('Internet / Broadband','Mobile Recharge','Wellness / Gym')), tot, 0):.0f}%** of all money paid out."])

@q(50, 'ThumbsUp', None, ['Reimbursement_Claims'])
def _():
    g = groupby(_cl(), lambda r: r['Claim_Category']); rows = []
    for k, v in g.items():
        a = sum(r['Status'] in ('Approved', 'Paid') for r in v); rj = sum(r['Status'] == 'Rejected' for r in v); rows.append((k, pct(a, len(v)), pct(rj, len(v)), round(100 - pct(a, len(v)) - pct(rj, len(v)), 1), len(v)))
    rows.sort(key=lambda x: x[1]); worst = min(rows, key=lambda x: x[1]); best = max(rows, key=lambda x: x[1])
    return dict(
        briefing=f"**{best[0]}** claims are approved most often (**{best[1]}%**). **{worst[0]}** claims have the most rejections (**{worst[2]}%** rejected).",
        kpis=[kpi('Best approval rate', best[1], 'pct', best[0], 'up'), kpi('Most rejections', max(r[2] for r in rows), 'pct', max(rows, key=lambda x: x[2])[0], 'down')],
        chart=dict(type='bar', orient='h', stacked=True, percent=True, categories=[r[0] for r in rows], series=[dict(name='Approved / paid', data=[r[1] for r in rows], tone='good'), dict(name='Rejected', data=[r[2] for r in rows], tone='bad'), dict(name='In review', data=[r[3] for r in rows], tone='warn')], fmt='pct'),
        insights=["Higher-value claims (travel, relocation) go through manager + finance approval and are checked more strictly."])

@q(51, 'XCircle', None, ['Reimbursement_Claims'])
def _():
    c = Counter(r['Rejection_Reason'] for r in _cl() if r['Status'] == 'Rejected' and r['Rejection_Reason']); it = counter_items(c)[::-1]; tot = sum(c.values()); t = c.most_common()
    return dict(
        briefing=f"Out of **{n(tot)}** rejected claims, **{pct(t[0][1], tot, 0):.0f}%** were rejected for \"**{t[0][0].lower()}**\" and **{pct(t[1][1], tot, 0):.0f}%** for \"**{t[1][0].lower()}**\". Both are easy to avoid.",
        kpis=[kpi('Rejected claims', tot, tone='down'), kpi(t[0][0], t[0][1]), kpi(t[1][0], t[1][1])],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Rejected claims', data=[i['value'] for i in it])], fmt='int', rank=True, tone='bad'),
        insights=["Submit within the allowed window and always attach the receipt for claims above the receipt limit."])

@q(52, 'Timer', None, ['Reimbursement_Claims'])
def _():
    g = groupby([r for r in _cl() if r['Decision_TAT_Days'] is not None], lambda r: r['Claim_Category']); rows = sorted([(k, r1(mean([r['Decision_TAT_Days'] for r in v]))) for k, v in g.items()], key=lambda x: x[1]); allv = [r['Decision_TAT_Days'] for v in g.values() for r in v]
    return dict(
        briefing=f"A claim is decided in **{r1(mean(allv))} days** on average. **{rows[0][0]}** is the quickest (**{rows[0][1]} days**) and **{rows[-1][0]}** the slowest (**{rows[-1][1]} days**).",
        kpis=[kpi('Average decision time', r1(mean(allv)), 'days'), kpi('Fastest', rows[0][1], 'days', rows[0][0], 'up'), kpi('Slowest', rows[-1][1], 'days', rows[-1][0], 'down')],
        chart=dict(type='bar', categories=[r[0] for r in rows], series=[dict(name='Days to decide', data=[r[1] for r in rows])], fmt='dec1', gradient=True),
        insights=[f"Decision times are consistent across categories, between **{rows[0][1]}** and **{rows[-1][1]}** days."])

@q(53, 'Clock', None, ['Reimbursement_Claims'])
def _():
    C = _cl(); late = [c for c in C if c['Within_Window'] == 'No']; ok = len(C) - len(late); g = Counter(c['Claim_Category'] for c in late)
    return dict(
        briefing=f"**{n(len(late))}** claims ({pct(len(late), len(C))}%) were submitted after the allowed window. **{pct(ok, len(C))}%** of claims are submitted on time.",
        kpis=[kpi('Submitted on time', pct(ok, len(C)), 'pct', tone='up'), kpi('Submitted late', len(late), tone='down'), kpi('Money in late claims', sum(c['Claimed_Amount_INR'] for c in late), 'inr')],
        chart=dict(type='gauge', value=pct(ok, len(C)), max=100, fmt='pct', label='Submitted on time'),
        insights=[f"Most late claims are in **{g.most_common(1)[0][0]}** (**{g.most_common(1)[0][1]}** claims).", "Submit claims within 30 days (15 days for travel and entertainment) of the expense."])

@q(54, 'Ruler', None, ['Reimbursement_Claims', 'Reimbursement_Policy'])
def _():
    g = groupby(_cl(), lambda r: r['Claim_Category']); pol = {p['Claim_Category']: p for p in D['Reimbursement_Policy']}; rows = []
    for k, v in g.items(): rows.append((k, round(mean([r['Claimed_Amount_INR'] for r in v])), pol[k]['Limit_Amount_INR'], pol[k]['Limit_Period'], pct(sum(r['Claimed_Amount_INR'] > r['Policy_Limit_INR'] for r in v), len(v))))
    rows.sort(key=lambda x: -x[2]); over = sum(r['Claimed_Amount_INR'] > r['Policy_Limit_INR'] for r in _cl())
    return dict(
        briefing=f"Most claims stay within policy: only **{n(over)}** of {n(len(_cl()))} claims ({pct(over, len(_cl()))}%) asked for more than the limit. **{max(rows, key=lambda x: x[4])[0]}** has the most over-limit claims (**{max(r[4] for r in rows)}%** of its claims).",
        kpis=[kpi('Claims above limit', over, tone='down'), kpi('Within limit', pct(len(_cl()) - over, len(_cl())), 'pct', tone='up')],
        chart=dict(type='bar', categories=[r[0] for r in rows], series=[dict(name='Average claim', data=[r[1] for r in rows]), dict(name='Policy limit', data=[r[2] for r in rows])], fmt='inr'),
        insights=["Limits apply per month, per claim, per year or once — depending on the category (see the policy table).", "Amounts above the limit are not paid; only the limit amount is approved."])

@q(55, 'Building', None, ['Reimbursement_Claims', 'Departments'])
def _():
    dn = DN(); c = Counter()
    for r in _cl():
        if r['Status'] in ('Paid', 'Approved'): c[dn[r['Dept_ID']]] += r['Approved_Amount_INR'] or 0
    it = [(k, round(v)) for k, v in c.items()]; it.sort(key=lambda x: x[1]); tot = sum(v for _, v in it)
    return dict(
        briefing=f"**{it[-1][0]}** claims the most (**{inr(it[-1][1])}**, {pct(it[-1][1], tot, 0):.0f}% of the total) simply because it is the largest team. Hover to see all departments.",
        kpis=[kpi('Highest claiming team', it[-1][1], 'inr', it[-1][0]), kpi('Total approved', tot, 'inr')],
        chart=dict(type='hbar', categories=[i[0] for i in it], series=[dict(name='Approved amount', data=[i[1] for i in it])], fmt='inr', rank=True),
        insights=["Sales and Customer Success have extra categories like client entertainment and travel."])

@q(56, 'ScrollText', None, ['Reimbursement_Policy'])
def _():
    P = D['Reimbursement_Policy']; rows = [[p['Claim_Category'], f"₹{p['Limit_Amount_INR']:,}", p['Limit_Period'], f"₹{p['Receipt_Required_Above_INR']:,}" if p['Receipt_Required_Above_INR'] else 'Always', f"{p['Submission_Window_Days']} days", p['Approver_Level'], p['Eligibility']] for p in P]
    return dict(
        briefing=f"There are **{len(P)} claim types**, each with its own limit, submission window and approver. Small monthly claims (internet, mobile, gym) are approved by your manager; big ones also need Finance.",
        kpis=[kpi('Claim types', len(P)), kpi('Highest limit', 50000, 'inr', 'Relocation'), kpi('Manager-only approval', sum(p['Approver_Level'] == 'Manager' for p in P))],
        chart=dict(type='table', columns=['Expense type', 'Limit', 'Limit applies', 'Receipt needed above', 'Submit within', 'Approved by', 'Who can claim'], rows=rows),
        insights=["Claims above the receipt threshold must have a receipt attached, or they will be rejected."])

# ───────────────────────── 6. DOCUMENTS ─────────────────────────
def _dr(): return D['Document_Requests']

@q(57, 'FileText', 'Popular', ['Document_Requests'])
def _():
    c = Counter(d['Doc_Name'] for d in _dr()); it = counter_items(c)[::-1]; t = c.most_common(); tot = sum(c.values())
    return dict(
        briefing=f"**{n(tot)}** documents were requested. **{t[0][0]}** is asked for most (**{n(t[0][1])}**), then **{t[1][0]}** and **{t[2][0]}**.",
        kpis=[kpi('Requests', tot), kpi('Top document', t[0][1], 'int', t[0][0]), kpi('Document types', len(c))],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Requests', data=[i['value'] for i in it])], fmt='int', rank=True),
        insights=["Letters for exiting employees (Relieving, Experience) are the most requested documents."])

@q(58, 'FileCheck', 'Key', ['Document_Requests'])
def _():
    g = groupby([d for d in _dr() if d['SLA_Met']], lambda d: d['Doc_Name']); rows = sorted([(k, pct(sum(d['SLA_Met'] == 'Yes' for d in v), len(v))) for k, v in g.items()], key=lambda x: x[1]); allv = [d for v in g.values() for d in v]; ok = sum(d['SLA_Met'] == 'Yes' for d in allv)
    return dict(
        briefing=f"**{pct(ok, len(allv), 0):.0f}%** of documents were delivered within the promised time. **{rows[-1][0]}** is the most reliable (**{rows[-1][1]}%**) and **{rows[0][0]}** the least (**{rows[0][1]}%**).",
        kpis=[kpi('Delivered on time', pct(ok, len(allv)), 'pct', tone='up'), kpi('Delivered late', len(allv) - ok, tone='down'), kpi('Documents issued', len(allv))],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Delivered on time', data=[r[1] for r in rows])], fmt='pct', rank=True),
        insights=[f"Promised times range from **1 day** (payslip copy) to **7 days** (relieving letter)."])

@q(59, 'LineChart', 'Trend', ['Document_Requests'])
def _():
    ms = month_range(dt.date(2025, 1, 1), ASOF); c = Counter(d['Request_Month'] for d in _dr()); v = [c[m] for m in ms]; full = v[:-1]
    return dict(
        briefing=f"HR receives about **{round(mean(full))}** document requests a month. The busiest month was **{ms[v.index(max(v))].strftime('%B %Y')}** with **{max(v)}** requests.",
        kpis=[kpi('Monthly average', round(mean(full))), kpi('Busiest month', max(v), 'int', ms[v.index(max(v))].strftime('%b %Y')), kpi('Total requests', sum(v))],
        chart=dict(type='line', categories=[ml(m) for m in ms], series=[dict(name='Document requests', data=v)], fmt='int', smooth=True),
        insights=[f"Monthly requests grew from about **{round(mean(v[:6]))}** in early 2025 to about **{round(mean(v[-7:-1]))}** in the latest six full months."])

@q(60, 'Hourglass', None, ['Document_Requests'])
def _():
    g = groupby([d for d in _dr() if d['TAT_Working_Days'] is not None], lambda d: d['Doc_Name']); rows = sorted([(k, r1(mean([d['TAT_Working_Days'] for d in v])), v[0]['SLA_Working_Days']) for k, v in g.items()], key=lambda x: x[2])
    allv = [d['TAT_Working_Days'] for v in g.values() for d in v]
    return dict(
        briefing=f"On average HR issues a document in **{r1(mean(allv))} working days**. Compare the actual time with the promised time for each document below.",
        kpis=[kpi('Average time taken', r1(mean(allv)), 'days', 'working days'), kpi('Fastest', min(r[1] for r in rows), 'days'), kpi('Slowest', max(r[1] for r in rows), 'days')],
        chart=dict(type='bar', categories=[r[0] for r in rows], series=[dict(name='Actual days taken', data=[r[1] for r in rows]), dict(name='Promised days', data=[r[2] for r in rows])], fmt='dec1'),
        insights=["Documents needing HR Business Partner approval take longer than portal downloads."])

@q(61, 'Inbox', None, ['Document_Requests'])
def _():
    O = [d for d in _dr() if d['Status'] not in ('Issued', 'Rejected')]; en = {e['Emp_ID']: e['Emp_Name'] for e in D['Employees']}; O.sort(key=lambda d: -(d['Open_Age_Days'] or 0))
    rows = [[d['Request_ID'], d['Doc_Name'], d['Requested_Date'].strftime('%d %b %Y'), d['Status'], f"{d['Open_Age_Days']} working days", en.get(d['Assigned_To_Emp_ID'], 'Unassigned')] for d in O]
    return dict(
        briefing=f"**{len(O)}** document requests are still open. The oldest has been waiting **{O[0]['Open_Age_Days']} working days**; the average wait is **{r1(mean([d['Open_Age_Days'] for d in O]))} days**.",
        kpis=[kpi('Open requests', len(O)), kpi('Oldest', O[0]['Open_Age_Days'], 'days', 'working days waiting', 'down'), kpi('Average wait', r1(mean([d['Open_Age_Days'] for d in O])), 'days')],
        chart=dict(type='table', columns=['Request', 'Document', 'Asked on', 'Status', 'Waiting', 'Handled by'], rows=rows),
        insights=["Only a handful of requests are open — almost everything is delivered quickly."])

@q(62, 'Target', None, ['Document_Requests'])
def _():
    c = Counter(d['Purpose'] for d in _dr()); it = counter_items(c, 10)[::-1]; t = c.most_common(); tot = sum(c.values())
    return dict(
        briefing=f"The top reason for asking a document is **{t[0][0].lower()}** (**{pct(t[0][1], tot, 0):.0f}%** of requests), followed by **{t[1][0].lower()}** and **{t[2][0].lower()}**.",
        kpis=[kpi('Top reason', t[0][1], 'int', t[0][0]), kpi('Loan-related', sum(v for k, v in c.items() if 'loan' in k.lower())), kpi('Visa-related', sum(v for k, v in c.items() if 'visa' in k.lower()))],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Requests', data=[i['value'] for i in it])], fmt='int', rank=True),
        insights=["Top 10 reasons shown. Employees leaving the company account for the largest share."])

@q(63, 'Send', None, ['Document_Requests'])
def _():
    c = Counter(d['Delivery_Mode'] for d in _dr() if d['Delivery_Mode']); tot = sum(c.values())
    return dict(
        briefing=f"**{pct(c['Email (PDF)'], tot, 0):.0f}%** of documents are sent as an email PDF and **{pct(c['Portal download'], tot, 0):.0f}%** are downloaded from the portal. Only **{c['Courier (hard copy)']}** needed a hard copy by courier.",
        kpis=[kpi('By email', c['Email (PDF)']), kpi('Portal download', c['Portal download']), kpi('Courier', c['Courier (hard copy)'])],
        chart=dict(type='donut', items=counter_items(c), fmt='int', centerValue=n(tot), centerLabel='documents'),
        insights=["Digital delivery is instant and free — hard copies are only sent when specifically requested."])

@q(64, 'UserCog', None, ['Document_Requests', 'Employees'])
def _():
    en = {e['Emp_ID']: e['Emp_Name'] for e in D['Employees']}; c = Counter(en.get(d['Assigned_To_Emp_ID']) for d in _dr() if d['Assigned_To_Emp_ID']); it = counter_items(c, 10)[::-1]; t = c.most_common()
    return dict(
        briefing=f"**{t[0][0]}** handled the most document requests (**{t[0][1]}**). Work is shared among **{len(c)}** HR team members.",
        kpis=[kpi('HR team members', len(c)), kpi('Most requests handled', t[0][1], 'int', t[0][0]), kpi('Avg. per person', round(mean(list(c.values()))))],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Requests handled', data=[i['value'] for i in it])], fmt='int', rank=True),
        insights=["Top 10 team members shown."])
