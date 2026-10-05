from qlib import *

# ───────────────────────── 7. POLICIES & FAQs ─────────────────────────
def _pol(): return D['HR_Policies']
def _faq(): return D['HR_FAQs']

@q(65, 'BookOpen', 'Popular', ['HR_Policies'])
def _():
    P = _pol(); c = Counter(p['Category'] for p in P); it = counter_items(c)
    return dict(
        briefing=f"HR has **{len(P)} approved policies** across **{len(c)}** areas. **Benefits** has the most (**{c['Benefits']}**), covering health, life, provident fund and wellbeing. The AI helpdesk answers only from these approved policies.",
        kpis=[kpi('Approved policies', sum(p['Approval_Status'] == 'Approved' for p in P), tone='up'), kpi('Policy areas', len(c)), kpi('Latest update', max(p['Effective_Date'] for p in P).strftime('%b %Y'), 'text', 'Data Privacy policy')],
        chart=dict(type='donut', items=it, fmt='int', centerValue=str(len(P)), centerLabel='policies'),
        insights=["Every policy has an owner department, a version number and a yearly review date."])

@q(66, 'CalendarClock', None, ['HR_Policies'])
def _():
    P = sorted(_pol(), key=lambda p: p['Review_Due_Date']); od = [p for p in P if p['Review_Overdue'] == 'Yes']; dn = DN()
    st = lambda p: 'Overdue' if p['Review_Overdue'] == 'Yes' else ('Due within 90 days' if (p['Review_Due_Date'] - ASOF).days <= 90 else 'On track')
    rows = [[p['Policy_Name'], p['Category'], p['Version'], p['Last_Reviewed'].strftime('%d %b %Y'), p['Review_Due_Date'].strftime('%d %b %Y'), st(p)] for p in P]
    return dict(
        briefing=f"**{len(od)}** of {len(P)} policies are overdue for their yearly review: **{', '.join(p['Policy_Name'] for p in od)}**. The rest are up to date.",
        kpis=[kpi('Overdue for review', len(od), tone='down'), kpi('On track', len(P) - len(od), tone='up'), kpi('Due within 90 days', sum(st(p) == 'Due within 90 days' for p in P))],
        chart=dict(type='table', columns=['Policy', 'Area', 'Version', 'Last reviewed', 'Next review due', 'Status'], rows=rows),
        insights=["Policies are reviewed every 12 months. Overdue ones should be re-approved so the AI helpdesk keeps giving current answers."])

@q(67, 'Eye', None, ['HR_FAQs'])
def _():
    F = sorted(_faq(), key=lambda f: -f['Views_Last_90_Days'])[:10][::-1]; tot = sum(f['Views_Last_90_Days'] for f in _faq())
    return dict(
        briefing=f"The most-read question in the last 90 days is “**{F[-1]['Question']}**” with **{n(F[-1]['Views_Last_90_Days'])} views**. The top 10 questions make up **{pct(sum(f['Views_Last_90_Days'] for f in F), tot, 0):.0f}%** of all FAQ views.",
        kpis=[kpi('FAQ views (90 days)', tot), kpi('Most-read FAQ', F[-1]['Views_Last_90_Days'], 'int', F[-1]['Category']), kpi('FAQs available', len(_faq()))],
        chart=dict(type='hbar', categories=[short(f['Question'], 52) for f in F], series=[dict(name='Views in last 90 days', data=[f['Views_Last_90_Days'] for f in F])], fmt='int', rank=True, fullNames=[f['Question'] for f in F]),
        insights=[f"Topics of the top 10: " + ', '.join(sorted({f['Category'] for f in F})) + '.'])

@q(68, 'MessageCircleQuestion', None, ['HR_FAQs'])
def _():
    c = Counter()
    for f in _faq(): c[f['Category']] += f['Views_Last_90_Days']
    it = counter_items(c); tot = sum(c.values())
    return dict(
        briefing=f"Employees read about **{it[0]['name']}** the most (**{pct(it[0]['value'], tot, 0):.0f}%** of FAQ views), followed by **{it[1]['name']}** and **{it[2]['name']}**.",
        kpis=[kpi('Top topic', it[0]['value'], 'int', it[0]['name']), kpi('Topics', len(it))],
        chart=dict(type='donut', items=it, fmt='int', centerValue=n(tot), centerLabel='views'),
        insights=["Payroll and leave questions drive most of the demand — good candidates for the AI Copilot to answer instantly."])

@q(69, 'Library', None, ['HR_FAQs'])
def _():
    c = Counter(f['Policy_Name'] for f in _faq()); it = c.most_common(10)[::-1]
    return dict(
        briefing=f"**{it[-1][0]}** has the most FAQs (**{it[-1][1]}**), so employees can find answers to many questions there without contacting HR.",
        kpis=[kpi('Total FAQs', len(_faq())), kpi('Policies with FAQs', len(c)), kpi('Most FAQs', it[-1][1], 'int', it[-1][0])],
        chart=dict(type='hbar', categories=[short(k, 44) for k, _ in it], series=[dict(name='FAQs', data=[v for _, v in it])], fmt='int', rank=True, fullNames=[k for k, _ in it]),
        insights=["Top 10 policies shown."])

@q(70, 'Landmark', None, ['HR_Policies', 'Departments'])
def _():
    dn = DN(); c = Counter(dn[p['Owner_Dept_ID']] for p in _pol()); it = c.most_common()
    return dict(
        briefing=f"**{it[0][0]}** owns the most policies (**{it[0][1]}** of {len(_pol())}), including leave, documents and employment rules.",
        kpis=[kpi('Owner departments', len(c)), kpi(it[0][0], it[0][1], 'int', 'policies owned')],
        chart=dict(type='bar', categories=[k for k, _ in it], series=[dict(name='Policies owned', data=[v for _, v in it])], fmt='int', gradient=True),
        insights=["Each policy has one accountable department that keeps it updated."])

@q(71, 'History', None, ['HR_Policies'])
def _():
    c = Counter(som(p['Last_Reviewed']) for p in _pol()); ms = month_range(min(c), max(c))
    return dict(
        briefing=f"Most policies (**{c[dt.date(2026,4,1)]}**) were last reviewed in **April 2026**. The oldest review was **{min(p['Last_Reviewed'] for p in _pol()).strftime('%B %Y')}**.",
        kpis=[kpi('Reviewed in 2026', sum(p['Last_Reviewed'].year == 2026 for p in _pol())), kpi('Reviewed in 2025', sum(p['Last_Reviewed'].year == 2025 for p in _pol()))],
        chart=dict(type='bar', categories=[ml(m) for m in ms], series=[dict(name='Policies reviewed', data=[c[m] for m in ms])], fmt='int', gradient=True),
        insights=["Annual review keeps policies in line with changing laws such as tax and PF rules."])

@q(72, 'ShieldCheck', 'Key', ['HR_Policies'])
def _():
    rows = [['Company policies and FAQs (e.g. leave rules)', '✔ Yes', '✔ Yes', '✔ Yes'],
            ['Your own leave balance, payslips and claims', '✔ Own data only', '✖ No', '✔ Yes'],
            ['Your own benefits and document requests', '✔ Own data only', '✖ No', '✔ Yes'],
            ['Leave and claim approvals of the team', '✖ No', '✔ Direct reports only', '✔ Yes'],
            ['Salary and personal data of other employees', '✖ No', '✖ No', '✔ Yes'],
            ['Every personal-data answer is recorded in a log', '✔ Logged', '✔ Logged', '✔ Logged']]
    return dict(
        briefing="The AI helpdesk follows a simple privacy rule: **policy answers are open to everyone**, while **personal data** is only shown to the employee it belongs to. Managers see their own team's approvals, and HR admins see everything.",
        kpis=[kpi('Access levels', 3), kpi('Governing policy', 'P20', 'text', 'Data Privacy & Access')],
        chart=dict(type='table', columns=['What you want to see', 'Employee', 'Manager', 'HR admin'], rows=rows),
        insights=["Source: Employee Data Privacy and Helpdesk Access Policy (P20, v1.2, effective 1 Mar 2026)."])

# ───────────────────────── 8. OUR PEOPLE ─────────────────────────
def _emp(): return D['Employees']
def _active(): return [e for e in _emp() if e['Employment_Status'] == 'Active']

@q(73, 'Users', 'Popular', ['Employees'])
def _():
    E = _emp(); a = len(_active()); x = len(E) - a; y1 = dt.date(2025, 10, 1)
    ex12 = sum(1 for e in E if e['Exit_Date'] and e['Exit_Date'] >= y1 and e['Exit_Date'] <= ASOF); hc12 = (a + len([e for e in E if e['Date_of_Joining'] < y1 and (not e['Exit_Date'] or e['Exit_Date'] >= y1)])) / 2
    return dict(
        briefing=f"**{n(a)}** people work at the company today. **{n(x)}** have left since 2020. In the last 12 months **{ex12}** people left, an attrition rate of about **{pct(ex12, hc12, 0):.0f}%**.",
        kpis=[kpi('Working today', a, tone='up'), kpi('Have left', x), kpi('Left in last 12 months', ex12), kpi('Yearly attrition', pct(ex12, hc12), 'pct', 'approx.', 'down')],
        chart=dict(type='donut', items=[dict(name='Currently working', value=a, tone='good'), dict(name='Have left', value=x, tone='neutral')], fmt='int', centerValue=n(a), centerLabel='employees'),
        insights=[f"Joined in the last 12 months: **{n(sum(1 for e in E if e['Date_of_Joining'] >= y1))}** people."])

@q(74, 'TrendingUp', 'Trend', ['Employees'])
def _():
    qs = quarter_ends(dt.date(2020, 3, 31), ASOF); E = _emp()
    v = [sum(1 for e in E if e['Date_of_Joining'] <= d and (not e['Exit_Date'] or e['Exit_Date'] > d)) for d in qs]
    return dict(
        briefing=f"The company has grown from **{n(v[0])}** people in early 2020 to **{n(v[-1])}** today — **{v[-1] / v[0]:.0f}×** larger. Growth was fastest in **{qlabel(qs[max(range(1, len(v)), key=lambda i: v[i] - v[i - 1])])}**.",
        kpis=[kpi('Today', v[-1]), kpi('Early 2020', v[0]), kpi('Added in last year', v[-1] - v[-5], tone='up')],
        chart=dict(type='area', categories=[qlabel(d) for d in qs], series=[dict(name='People working', data=v)], fmt='int'),
        insights=["Headcount counts everyone who had joined and not yet left at the end of each quarter."])

@q(75, 'Network', 'Key', ['Employees', 'Departments'])
def _():
    dn = DN(); c = Counter(dn[e['Dept_ID']] for e in _active()); it = counter_items(c); tot = sum(c.values())
    return dict(
        briefing=f"**{it[0]['name']}** is the largest team with **{n(it[0]['value'])}** people (**{pct(it[0]['value'], tot, 0):.0f}%** of the company), followed by **{it[1]['name']}** and **{it[2]['name']}**.",
        kpis=[kpi('Departments', len(it)), kpi('Largest team', it[0]['value'], 'int', it[0]['name']), kpi('Smallest team', it[-1]['value'], 'int', it[-1]['name'])],
        chart=dict(type='treemap', items=it, fmt='int'),
        insights=[f"Tech teams together make up **{pct(sum(c[k] for k in ('Engineering','Quality Assurance','DevOps & Cloud','Data & Analytics','Information Security','AI / ML')), tot, 0):.0f}%** of all employees."])

@q(76, 'Users', None, ['Employees', 'Departments'])
def _():
    dn = DN(); g = groupby(_active(), lambda e: dn[e['Dept_ID']]); order = sorted(g, key=lambda k: len(g[k]))
    ser = [dict(name=s, data=[sum(e['Gender'] == s for e in g[k]) for k in order], tone={'Male': 'brand', 'Female': 'accent', 'Other': 'warn'}[s]) for s in ('Male', 'Female', 'Other')]
    A = _active(); f = sum(e['Gender'] == 'Female' for e in A); fp = {k: pct(sum(e['Gender'] == 'Female' for e in g[k]), len(g[k])) for k in g}
    return dict(
        briefing=f"**{pct(f, len(A), 0):.0f}%** of employees are women. **{max(fp, key=fp.get)}** has the highest share of women (**{max(fp.values())}%**) and **{min(fp, key=fp.get)}** the lowest (**{min(fp.values())}%**).",
        kpis=[kpi('Men', sum(e['Gender'] == 'Male' for e in A)), kpi('Women', f), kpi('Share of women', pct(f, len(A)), 'pct')],
        chart=dict(type='bar', orient='h', stacked=True, categories=order, series=ser, fmt='int'),
        insights=[f"{sum(e['Gender'] == 'Other' for e in A)} employees identify as other."])

@q(77, 'GraduationCap', None, ['Employees'])
def _():
    c = Counter(e['Experience_Level'] for e in _active()); it = [dict(name=l, value=c[l]) for l in LEVELS]; tot = sum(c.values())
    return dict(
        briefing=f"**{pct(c['Fresher'] + c['Intern'], tot, 0):.0f}%** of the team are freshers or interns and **{pct(c['Senior'] + c['Lead'], tot, 0):.0f}%** are senior or lead, so the company has a young workforce.",
        kpis=[kpi('Interns & freshers', c['Intern'] + c['Fresher']), kpi('Junior & mid-level', c['Junior'] + c['Mid']), kpi('Senior & lead', c['Senior'] + c['Lead'])],
        chart=dict(type='donut', items=it, fmt='int', centerValue=n(tot), centerLabel='people'),
        insights=["Experience level is the level at which a person was hired."])

@q(78, 'MapPin', None, ['Employees', 'Employee_HR_Profile', 'Locations'])
def _():
    loc = {l['Location_ID']: l['Location_Name'] for l in D['Locations']}; wm = {p['Emp_ID']: p['Work_Mode'] for p in D['Employee_HR_Profile']}; A = _active()
    c = Counter((loc[e['Location_ID']], wm[e['Emp_ID']]) for e in A); locs = sorted({k[0] for k in c}, key=lambda l: -sum(v for k, v in c.items() if k[0] == l)); modes = ['Onsite', 'Hybrid', 'Remote']
    ser = [dict(name=m, data=[c[(l, m)] for l in locs]) for m in modes]; mc = Counter(wm[e['Emp_ID']] for e in A)
    return dict(
        briefing=f"**{pct(mc['Hybrid'], len(A), 0):.0f}%** of people work in a hybrid mode. **{locs[0]}** is the biggest office with **{n(sum(c[(locs[0], m)] for m in modes))}** people.",
        kpis=[kpi('Hybrid', mc['Hybrid']), kpi('Onsite', mc['Onsite']), kpi('Remote', mc['Remote'])],
        chart=dict(type='bar', categories=locs, series=ser, fmt='int'),
        insights=["Work mode is the arrangement recorded in each employee's HR profile."])

@q(79, 'UserCheck', None, ['Employee_HR_Profile'])
def _():
    act = {e['Emp_ID'] for e in _active()}; c = Counter(p['Confirmation_Status'] for p in D['Employee_HR_Profile'] if p['Emp_ID'] in act); tot = sum(c.values())
    tone = {'Confirmed': 'good', 'On Probation': 'brand', 'Extended': 'warn', 'Not Applicable': 'neutral'}
    return dict(
        briefing=f"**{pct(c['Confirmed'], tot, 0):.0f}%** of employees are confirmed. **{n(c['On Probation'])}** are still on probation and **{c['Extended']}** had their probation extended.",
        kpis=[kpi('Confirmed', c['Confirmed'], tone='up'), kpi('On probation', c['On Probation']), kpi('Probation extended', c['Extended'], tone='down')],
        chart=dict(type='donut', items=[dict(name=k if k != 'Not Applicable' else 'Interns (no probation)', value=v, tone=tone[k]) for k, v in c.most_common()], fmt='int', centerValue=n(tot), centerLabel='employees'),
        insights=["Probation is 6 months for full-time employees; interns have no probation."])

@q(80, 'Hourglass', None, ['Employee_HR_Profile'])
def _():
    act = {e['Emp_ID'] for e in _active()}; v = [p['Tenure_Years'] for p in D['Employee_HR_Profile'] if p['Emp_ID'] in act]
    labs = ['Under 1 year', '1–2 years', '2–3 years', '3–4 years', '4–5 years', '5+ years']; bk = bucket(v, [1, 2, 3, 4, 5], labs)
    return dict(
        briefing=f"The average employee has been here **{r1(mean(v))} years**. **{pct(bk[0], len(v), 0):.0f}%** joined in the last year, while **{n(bk[-1])}** people have more than 5 years of service.",
        kpis=[kpi('Average tenure', r1(mean(v)), 'text', 'years'), kpi('New (under 1 year)', bk[0]), kpi('5+ years', bk[-1], tone='up')],
        chart=dict(type='bar', categories=labs, series=[dict(name='Employees', data=bk)], fmt='int', gradient=True),
        insights=["The company has hired heavily in the last two years, so many employees are still new."])

@q(81, 'Star', None, ['Employee_HR_Profile'])
def _():
    act = {e['Emp_ID'] for e in _active()}; v = [p['Last_Appraisal_Rating'] for p in D['Employee_HR_Profile'] if p['Emp_ID'] in act and p['Last_Appraisal_Rating']]; c = Counter(v)
    return dict(
        briefing=f"Of **{n(len(v))}** employees with an appraisal, **{pct(c[3], len(v), 0):.0f}%** meet expectations (rating 3) and **{pct(c[4] + c[5], len(v), 0):.0f}%** score 4 or 5. Only **{pct(c[1], len(v))}%** are rated 1.",
        kpis=[kpi('Average rating', r2(mean(v)), 'rating', 'out of 5'), kpi('Top performers (4–5)', c[4] + c[5], tone='up'), kpi('Below expectations (1–2)', c[1] + c[2], tone='down')],
        chart=dict(type='bar', categories=[f'Rating {k}' for k in range(1, 6)], series=[dict(name='Employees', data=[c[k] for k in range(1, 6)])], fmt='int', pointTones=['bad', 'warn', 'neutral', 'good', 'brand']),
        insights=["Interns and employees who joined recently have no rating yet, so they are not counted."])

@q(82, 'Landmark', None, ['Employee_HR_Profile'])
def _():
    act = {e['Emp_ID'] for e in _active()}; c = Counter(p['Tax_Regime'] for p in D['Employee_HR_Profile'] if p['Emp_ID'] in act); tot = sum(c.values())
    return dict(
        briefing=f"**{pct(c['New'], tot, 0):.0f}%** of employees have chosen the **new tax regime** and **{pct(c['Old'], tot, 0):.0f}%** stay on the old regime, which allows deductions such as 80C and HRA.",
        kpis=[kpi('New regime', c['New']), kpi('Old regime', c['Old'])],
        chart=dict(type='donut', items=[dict(name='New tax regime', value=c['New'], tone='brand'), dict(name='Old tax regime', value=c['Old'], tone='accent')], fmt='int', centerValue=n(tot), centerLabel='employees'),
        insights=["Employees choose their regime in the HR portal at the start of each financial year; the new regime is the default."])
