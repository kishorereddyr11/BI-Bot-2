from qlib import *

def _tk(): return D['Helpdesk_Tickets']

# ───────────────────────── 1. HELPDESK ─────────────────────────
@q(1, 'LifeBuoy', 'Popular', ['Helpdesk_Tickets'])
def _():
    T = _tk(); tot = len(T); res = [t for t in T if t['SLA_Met']]
    met = sum(t['SLA_Met'] == 'Yes' for t in res)
    opn = sum(t['Status'] in ('Open', 'In Progress', 'Waiting on Employee') for t in T)
    cs = [t['CSAT_Rating'] for t in T if t['CSAT_Rating']]; p = pct(met, len(res))
    late = len(res) - met
    return dict(
        briefing=f"Employees raised **{n(tot)}** help requests between Jan 2025 and Sep 2026. **{p}%** of the solved ones were answered within the promised time, and only **{opn}** are still open today.",
        kpis=[kpi('Help requests', tot, sub='Jan 2025 – Sep 2026'), kpi('Solved on time', p, 'pct', 'of solved requests', 'up'), kpi('Still open', opn, sub='right now'), kpi('Avg. rating', r2(mean(cs)), 'rating', 'out of 5')],
        chart=dict(type='gauge', value=p, max=100, fmt='pct', label='Solved on time'),
        insights=[f"**{n(met)}** requests were closed inside their promised time; **{n(late)}** took longer.",
                  f"High-priority requests must be solved in 1 day, medium in 2 days and low in 4 days.",
                  f"Employees who rated the service gave an average of **{r2(mean(cs))} / 5**."])

@q(2, 'TrendingUp', 'Trend', ['Helpdesk_Tickets'])
def _():
    c = Counter(som(t['Created_Date']) for t in _tk()); ms = month_range(dt.date(2025, 1, 1), ASOF)
    vals = [c[m] for m in ms]; pk = max(range(len(ms)), key=lambda i: vals[i])
    full = vals[:-1]
    return dict(
        briefing=f"We get about **{n(mean(full))}** help requests a month. The busiest month was **{ms[pk].strftime('%B %Y')}** with **{n(vals[pk])}** requests.",
        kpis=[kpi('Monthly average', round(mean(full)), sub='full months'), kpi('Busiest month', vals[pk], sub=ms[pk].strftime('%b %Y')), kpi('Last month', vals[-2], sub=ms[-2].strftime('%b %Y'))],
        chart=dict(type='area', categories=[ml(m) for m in ms], series=[dict(name='Help requests', data=vals)], fmt='int'),
        insights=[f"Volume went from **{vals[0]}** in {ml(ms[0])} to **{vals[-2]}** in {ml(ms[-2])} as the company grew.", "The latest month is partial data (up to 30 Sep), so ignore the small dip at the end."])

@q(3, 'ListChecks', None, ['Helpdesk_Tickets'])
def _():
    c = Counter(t['Category'] for t in _tk()); it = counter_items(c); tot = sum(c.values())
    return dict(
        briefing=f"**{it[0]['name']}** questions are the most common, making up **{pct(it[0]['value'], tot)}%** of all requests, followed by **{it[1]['name']}** and **{it[2]['name']}**.",
        kpis=[kpi('Top topic', it[0]['value'], sub=it[0]['name']), kpi('Topics covered', len(it), sub='categories')],
        chart=dict(type='hbar', categories=[i['name'] for i in it], series=[dict(name='Requests', data=[i['value'] for i in it])], fmt='int'),
        insights=[f"Salary-related topics (Payroll + Tax) account for **{pct(c['Payroll'] + c['Tax'], tot)}%** of requests.", f"{it[-1]['name']} is the least asked topic with **{n(it[-1]['value'])}** requests."])

@q(4, 'Rocket', 'New', ['Helpdesk_Tickets'])
def _():
    ms = month_range(dt.date(2025, 1, 1), ASOF); chans = ['Email', 'Portal', 'Teams Chat', 'AI Copilot']
    c = Counter((som(t['Created_Date']), t['Channel']) for t in _tk())
    ser = [dict(name=ch, data=[c[(m, ch)] for m in ms]) for ch in chans]
    last = ms[-1]; ai = c[(last, 'AI Copilot')]; tot = sum(c[(last, ch)] for ch in chans); first = min(m for m in ms if c[(m, 'AI Copilot')] > 0)
    totai = sum(c[(m, 'AI Copilot')] for m in ms)
    return dict(
        briefing=f"The AI Copilot went live in **{first.strftime('%B %Y')}** and already handles **{pct(ai, tot, 0):.0f}%** of all requests in {last.strftime('%b %Y')} — **{n(totai)}** conversations in total.",
        kpis=[kpi('AI Copilot requests', totai, sub='since launch'), kpi('Share this month', pct(ai, tot), 'pct', last.strftime('%b %Y'), 'up')],
        chart=dict(type='bar', stacked=True, categories=[ml(m) for m in ms], series=ser, fmt='int'),
        insights=["Adoption grew every month after launch, mostly at the cost of Email and Portal requests.", "Employees now prefer a quick chat over waiting for an email reply."])

@q(5, 'Bot', 'Popular', ['Helpdesk_Tickets'])
def _():
    T = [t for t in _tk() if t['Created_Date'] >= dt.date(2026, 3, 1)]; tot = len(T)
    ai = sum(t['Resolved_By'] == 'AI Copilot' for t in T); hr = sum(t['Resolved_By'] == 'HR Team' for t in T); un = tot - ai - hr
    return dict(
        briefing=f"Since launch, the AI Copilot has fully solved **{n(ai)}** of **{n(tot)}** requests (**{pct(ai, tot)}%**) without needing an HR person, saving the HR team a lot of effort.",
        kpis=[kpi('Solved by AI Copilot', ai, sub=f'{pct(ai, tot)}% of requests', tone='up'), kpi('Solved by HR team', hr), kpi('Requests since launch', tot, sub='from March 2026')],
        chart=dict(type='donut', items=[dict(name='AI Copilot', value=ai, tone='brand'), dict(name='HR Team', value=hr, tone='neutral')] + ([dict(name='Not yet solved', value=un, tone='warn')] if un else []), fmt='int', centerValue=f"{pct(ai, tot, 0):.0f}%", centerLabel='solved by AI'),
        insights=[f"The AI answers instantly, while the HR team needs about **{r1(mean([t['Resolution_Days'] for t in T if t['Resolved_By'] == 'HR Team']))} days** on average.", "Policy, leave and payslip questions are the easiest for the Copilot to handle."])

@q(6, 'Zap', None, ['Helpdesk_Tickets'])
def _():
    T = _tk(); chans = ['AI Copilot', 'Teams Chat', 'Portal', 'Email']; g = groupby(T, lambda t: t['Channel'])
    fr = [r1(mean([t['First_Response_Min'] for t in g[c]])) for c in chans]; rd = [r2(mean([t['Resolution_Days'] for t in g[c]])) for c in chans]
    cs = [r2(mean([t['CSAT_Rating'] for t in g[c]])) for c in chans]
    b = min(range(4), key=lambda i: rd[i])
    return dict(
        briefing=f"**{chans[b]}** is the fastest way to get help — solved in **{rd[b]} days** on average, versus **{max(rd)} days** for the slowest channel.",
        kpis=[kpi(c, v, 'min', 'first reply') for c, v in zip(chans, fr)],
        chart=dict(type='combo', categories=chans, series=[dict(name='Wait for first reply (min)', data=fr, kind='bar', axis=0, fmt='min'), dict(name='Days to solve', data=rd, kind='line', axis=1, fmt='days')], fmt='dec1', yNames=['Minutes', 'Days']),
        insights=[f"Average rating by channel: " + ', '.join(f"{c} **{v}**" for c, v in zip(chans, cs)) + '.'])

@q(7, 'CheckCircle2', None, ['Helpdesk_Tickets'])
def _():
    g = groupby([t for t in _tk() if t['SLA_Met']], lambda t: t['Category'])
    rows = sorted([(k, pct(sum(t['SLA_Met'] == 'Yes' for t in v), len(v))) for k, v in g.items()], key=lambda x: x[1])
    return dict(
        briefing=f"**{rows[-1][0]}** requests are solved on time most often (**{rows[-1][1]}%**), while **{rows[0][0]}** needs attention at **{rows[0][1]}%**.",
        kpis=[kpi('Best topic', rows[-1][1], 'pct', rows[-1][0], 'up'), kpi('Needs attention', rows[0][1], 'pct', rows[0][0], 'down')],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Solved on time', data=[r[1] for r in rows])], fmt='pct', rank=True),
        insights=[f"The gap between best and weakest topic is **{r1(rows[-1][1] - rows[0][1])} points**."])

@q(8, 'Timer', None, ['Helpdesk_Tickets'])
def _():
    T = _tk(); labs = ['Instant', 'Under 15 min', '15–60 min', '1–4 hours', '4–12 hours', 'Over 12 hours']; ed = [1, 15, 60, 240, 720]
    ai = [t['First_Response_Min'] for t in T if t['Resolved_By'] == 'AI Copilot']; hr = [t['First_Response_Min'] for t in T if t['Resolved_By'] != 'AI Copilot']
    allv = [t['First_Response_Min'] for t in T]
    return dict(
        briefing=f"Half of all requests get a first reply within **{round(median(allv))} minutes**. The average wait is **{r1(mean(allv))} minutes**; AI Copilot replies are **instant**, while HR-team replies take about **{r1(mean(hr))} minutes**.",
        kpis=[kpi('Typical wait', round(median(allv)), 'min', 'median'), kpi('Average wait', r1(mean(allv)), 'min'), kpi('HR team wait', r1(mean(hr)), 'min', 'average'), kpi('AI Copilot wait', 0, 'min', 'instant', 'up')],
        chart=dict(type='bar', stacked=True, categories=labs, series=[dict(name='Solved by AI Copilot', data=bucket(ai, ed, labs)), dict(name='Solved by HR team', data=bucket(hr, ed, labs))], fmt='int'),
        insights=[f"**{pct(sum(1 for v in allv if v <= 60), len(allv), 0):.0f}%** of requests get a first reply within an hour."])

@q(9, 'Smile', 'Popular', ['Helpdesk_Tickets'])
def _():
    cs = [t['CSAT_Rating'] for t in _tk() if t['CSAT_Rating']]; c = Counter(cs); tot = len(cs); good = c[4] + c[5]
    return dict(
        briefing=f"Employees rate our help **{r2(mean(cs))} out of 5** on average, and **{pct(good, tot, 0):.0f}%** gave 4 or 5 stars ({n(tot)} ratings).",
        kpis=[kpi('Average rating', r2(mean(cs)), 'rating', 'out of 5', 'up'), kpi('Happy (4–5 ★)', pct(good, tot), 'pct'), kpi('Unhappy (1–2 ★)', pct(c[1] + c[2], tot), 'pct', tone='down')],
        chart=dict(type='bar', categories=['1 ★', '2 ★', '3 ★', '4 ★', '5 ★'], series=[dict(name='Ratings', data=[c[i] for i in range(1, 6)])], fmt='int', pointTones=['bad', 'warn', 'neutral', 'good', 'brand']),
        insights=[f"5-star is the most common rating with **{n(c[5])}** votes.", f"Only **{pct(c[1], tot)}%** of employees gave a 1-star rating."])

@q(10, 'Building2', None, ['Helpdesk_Tickets', 'Departments'])
def _():
    dn = DN(); c = Counter(dn[t['Dept_ID']] for t in _tk()); it = counter_items(c); tot = sum(c.values())
    return dict(
        briefing=f"**{it[0]['name']}** raises the most help requests (**{pct(it[0]['value'], tot)}%**), mainly because it is the biggest team. Hover over a block to see the exact count.",
        kpis=[kpi('Most requests', it[0]['value'], sub=it[0]['name']), kpi('Departments', len(it))],
        chart=dict(type='treemap', items=it, fmt='int'),
        insights=[f"Top 3 teams — {', '.join(i['name'] for i in it[:3])} — raise **{pct(sum(i['value'] for i in it[:3]), tot, 0):.0f}%** of requests."])

@q(11, 'Flame', None, ['Helpdesk_Tickets'])
def _():
    T = _tk(); pr = ['High', 'Medium', 'Low']; g = groupby(T, lambda t: t['Priority']); opn = ('Open', 'In Progress', 'Waiting on Employee')
    ser = [dict(name='Closed', data=[sum(t['Status'] == 'Closed' for t in g[p]) for p in pr], tone='good'),
           dict(name='Resolved', data=[sum(t['Status'] == 'Resolved' for t in g[p]) for p in pr], tone='brand'),
           dict(name='Still open', data=[sum(t['Status'] in opn for t in g[p]) for p in pr], tone='bad')]
    o = sum(ser[2]['data'])
    return dict(
        briefing=f"**{pct(len(g['High']), len(T), 0):.0f}%** of requests are high priority. Only **{o}** of all {n(len(T))} requests are still open — almost everything gets closed.",
        kpis=[kpi('High priority', len(g['High'])), kpi('Medium priority', len(g['Medium'])), kpi('Low priority', len(g['Low'])), kpi('Still open', o, tone='down')],
        chart=dict(type='bar', stacked=True, categories=pr, series=ser, fmt='int'),
        insights=[f"Open requests: **{ser[2]['data'][0]}** high, **{ser[2]['data'][1]}** medium, **{ser[2]['data'][2]}** low priority."])

@q(12, 'CalendarClock', None, ['Helpdesk_Tickets'])
def _():
    T = _tk(); cats = [k for k, _ in Counter(t['Category'] for t in T).most_common()]; c = Counter((t['Created_Date'].weekday(), t['Category']) for t in T)
    data = [[x, y, c[(x, cat)]] for y, cat in enumerate(cats) for x in range(7)]
    byd = Counter(t['Created_Date'].weekday() for t in T); bd = max(byd, key=byd.get)
    top = max(data, key=lambda d: d[2])
    return dict(
        briefing=f"**{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][bd]}** is the busiest day with **{n(byd[bd])}** requests. The hottest spot is **{cats[top[1]]}** on **{WEEK[top[0]]}**.",
        kpis=[kpi('Busiest day', byd[bd], sub=WEEK[bd]), kpi('Quietest day', min(byd.values()), sub=WEEK[min(byd, key=byd.get)])],
        chart=dict(type='heatmap', xs=WEEK, ys=cats, data=data, fmt='int'),
        insights=["Darker blocks mean more requests — useful for planning when HR staff should be available."])

# ───────────────────────── 2. LEAVE ─────────────────────────
def _lv(): return D['Leave_Requests']

@q(13, 'CalendarRange', None, ['Leave_Types'])
def _():
    L = D['Leave_Types']
    rows = [[l['Leave_Name'], l['Annual_Quota_Days'], l['Intern_Quota_Days'], l['Carry_Forward_Max_Days'] or '—', 'Paid' if l['Is_Paid'] == 'Yes' else 'Unpaid', l['Applicable_To'], l['Max_Consecutive_Days']] for l in L]
    return dict(
        briefing="A full-time employee gets **12 Casual**, **12 Sick** and **18 Earned** leave days every year. Interns get 6 Casual and 6 Sick days. Special leaves like Maternity and Marriage come on top.",
        kpis=[kpi('Casual leave', 12, 'days', 'per year'), kpi('Sick leave', 12, 'days', 'per year'), kpi('Earned leave', 18, 'days', 'per year'), kpi('Leave types', len(L))],
        chart=dict(type='table', columns=['Leave type', 'Days per year', 'Interns get', 'Carry forward (max)', 'Paid?', 'Who can take it', 'Max days at a stretch'], rows=rows),
        insights=["Casual and Sick leave expire on 31 December; up to 15 unused Earned Leave days carry forward.", "Leave taken without balance is treated as Loss of Pay."])

@q(14, 'CalendarCheck', 'Popular', ['Leave_Requests'])
def _():
    c = Counter(l['Status'] for l in _lv()); tot = sum(c.values())
    tone = dict(Approved='good', Rejected='bad', Pending='warn', Cancelled='neutral')
    return dict(
        briefing=f"Out of **{n(tot)}** leave requests, **{pct(c['Approved'], tot)}%** were approved. **{n(c['Rejected'])}** were rejected and **{c['Pending']}** are still waiting for a decision.",
        kpis=[kpi('Approved', c['Approved'], tone='up'), kpi('Rejected', c['Rejected'], tone='down'), kpi('Waiting', c['Pending']), kpi('Cancelled', c['Cancelled'])],
        chart=dict(type='donut', items=[dict(name=k, value=v, tone=tone[k]) for k, v in c.most_common()], fmt='int', centerValue=f"{pct(c['Approved'], tot, 0):.0f}%", centerLabel='approved'),
        insights=[f"Only **{pct(c['Rejected'], tot)}%** of requests get rejected — managers rarely say no."])

@q(15, 'Palmtree', 'Trend', ['Leave_Requests'])
def _():
    A = [l for l in _lv() if l['Status'] == 'Approved']; M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    ser = []
    for y in (2025, 2026):
        c = Counter(l['From_Date'].month for l in A if l['From_Date'].year == y); ser.append(dict(name=str(y), data=[r1(sum(l['Days'] for l in A if l['From_Date'].year == y and l['From_Date'].month == m)) for m in range(1, 13)]))
    d25 = ser[0]['data']; pk = max(range(12), key=lambda i: d25[i])
    return dict(
        briefing=f"In 2025 people took the most leave in **{M[pk]}** (**{n(d25[pk])} days**). Monthly leave in 2026 is higher than in 2025 because the company is bigger. Oct–Dec 2026 only show leave approved so far.",
        kpis=[kpi('Leave days in 2025', round(sum(d25)), sub='approved'), kpi('Leave days in 2026', round(sum(ser[1]['data'])), sub='taken + upcoming'), kpi('Peak month 2025', round(d25[pk]), sub=M[pk])],
        chart=dict(type='line', categories=M, series=ser, fmt='int', smooth=True),
        insights=[f"Leave days per month in Jan–Sep 2026 are about **{pct(sum(ser[1]['data'][:9]), sum(ser[0]['data'][:9]), 0):.0f}%** of the same months in 2025.", f"October 2025 was the busiest month (festival season), with **{n(d25[9])}** leave days."])

@q(16, 'Layers', None, ['Leave_Requests'])
def _():
    c = Counter(); [c.update({l['Leave_Name']: l['Days']}) for l in _lv() if l['Status'] == 'Approved']; tot = sum(c.values()); it = [dict(name=k, value=round(v)) for k, v in c.most_common()]
    return dict(
        briefing=f"**{it[0]['name']}** is the most used leave type (**{pct(it[0]['value'], tot, 0):.0f}%** of all days), followed by **{it[1]['name']}** and **{it[2]['name']}**.",
        kpis=[kpi('Total leave days', round(tot), sub='approved'), kpi(it[0]['name'], it[0]['value'], 'int', 'days')],
        chart=dict(type='donut', items=it, fmt='int', centerValue=n(tot), centerLabel='leave days'),
        insights=[f"Special leaves (marriage, maternity, paternity, bereavement) together use **{round(sum(i['value'] for i in it if i['name'] in ('Marriage Leave','Maternity Leave','Paternity Leave','Bereavement Leave')))}** days."])

@q(17, 'Users', None, ['Leave_Requests', 'Employees'])
def _():
    dn = DN(); y0, y1 = dt.date(2025, 1, 1), dt.date(2025, 12, 31); py = Counter()
    for e in D['Employees']:
        a = max(e['Date_of_Joining'], y0); b = min(e['Exit_Date'] or y1, y1)
        if b >= a: py[e['Dept_ID']] += ((b - a).days + 1) / 365
    days = Counter()
    for l in _lv():
        if l['Status'] == 'Approved' and l['From_Date'].year == 2025 and l['Leave_Name'] in ('Casual Leave', 'Sick Leave', 'Earned Leave'): days[l['Dept_ID']] += l['Days']
    rows = sorted([(dn[d], r1(days[d] / py[d])) for d in py if py[d] > 5], key=lambda x: x[1])
    return dict(
        briefing=f"In 2025, **{rows[-1][0]}** took the most regular leave (Casual, Sick, Earned) per person (**{rows[-1][1]} days a year**) and **{rows[0][0]}** the least (**{rows[0][1]} days**). Numbers are per employee-year, so team size and joining dates do not skew the picture.",
        kpis=[kpi('Highest', rows[-1][1], 'days', rows[-1][0]), kpi('Lowest', rows[0][1], 'days', rows[0][0]), kpi('Company average', r1(sum(days.values()) / sum(py.values())), 'days', 'per person-year')],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Leave days per person (2025)', data=[r[1] for r in rows])], fmt='dec1', rank=True),
        insights=[f"Spread between the highest and lowest team is **{r1(rows[-1][1] - rows[0][1])} days** per person."])

@q(18, 'Hourglass', None, ['Leave_Requests'])
def _():
    v = [l['Approval_TAT_Days'] for l in _lv() if l['Approval_TAT_Days'] is not None]; labs = ['Same day', '1 day', '2 days', '3 days', '4 days', '5+ days']
    b = bucket(v, [1, 2, 3, 4, 5], labs); tot = len(v)
    return dict(
        briefing=f"Managers decide on a leave request in **{r1(mean(v))} days** on average. **{pct(sum(1 for x in v if x <= 2), tot, 0):.0f}%** of requests are decided within 2 days.",
        kpis=[kpi('Average wait', r1(mean(v)), 'days'), kpi('Within 2 days', pct(sum(1 for x in v if x <= 2), tot), 'pct', tone='up'), kpi('Slower than 5 days', pct(b[-1], tot), 'pct', tone='down')],
        chart=dict(type='bar', categories=labs, series=[dict(name='Leave requests', data=b)], fmt='int', gradient=True),
        insights=[f"The most common wait is **{labs[b.index(max(b))]}**."])

@q(19, 'PiggyBank', None, ['Leave_Balances'])
def _():
    B = [b for b in D['Leave_Balances'] if b['Leave_Year'] == 2026]; names = {'LT01': 'Casual Leave', 'LT02': 'Sick Leave', 'LT03': 'Earned Leave'}; g = groupby(B, lambda b: b['Leave_Type_ID']); ks = ['LT01', 'LT02', 'LT03']
    def avg(f): return [r1(mean([f(b) for b in g[k]])) for k in ks]
    used, up, pe, av = avg(lambda b: b['Used_Days']), avg(lambda b: b['Upcoming_Approved_Days']), avg(lambda b: b['Pending_Approval_Days']), avg(lambda b: b['Available_Balance'])
    return dict(
        briefing=f"An employee still has about **{av[0]} Casual**, **{av[1]} Sick** and **{av[2]} Earned** leave days left for 2026, after using **{used[0]}**, **{used[1]}** and **{used[2]}** so far.",
        kpis=[kpi('Casual left', av[0], 'days', 'avg per person'), kpi('Sick left', av[1], 'days', 'avg per person'), kpi('Earned left', av[2], 'days', 'avg per person')],
        chart=dict(type='bar', stacked=True, categories=[names[k] for k in ks], series=[dict(name='Used', data=used, tone='brand'), dict(name='Upcoming (approved)', data=up, tone='accent'), dict(name='Waiting for approval', data=pe, tone='warn'), dict(name='Available', data=av, tone='good')], fmt='dec1'),
        insights=["Casual and Sick leave expire at year-end, so remaining days should be used before 31 December."])

@q(20, 'Gauge', 'Key', ['Leave_Balances', 'Departments'])
def _():
    dn = DN(); g = defaultdict(lambda: [0, 0])
    for b in D['Leave_Balances']:
        if b['Leave_Year'] == 2026: g[b['Dept_ID']][0] += b['Used_Days']; g[b['Dept_ID']][1] += b['Opening_Balance'] + b['Credited_Days']
    rows = sorted([(dn[d], pct(u, t)) for d, (u, t) in g.items() if t], key=lambda x: x[1]); tu = sum(u for u, t in g.values()); tt = sum(t for u, t in g.values())
    return dict(
        briefing=f"So far in 2026, the company has used **{pct(tu, tt)}%** of all leave. **{rows[-1][0]}** leads at **{rows[-1][1]}%**, while **{rows[0][0]}** has used only **{rows[0][1]}%**.",
        kpis=[kpi('Company average', pct(tu, tt), 'pct', 'of leave used'), kpi('Highest', rows[-1][1], 'pct', rows[-1][0]), kpi('Lowest', rows[0][1], 'pct', rows[0][0])],
        chart=dict(type='hbar', categories=[r[0] for r in rows], series=[dict(name='Leave used', data=[r[1] for r in rows])], fmt='pct', rank=True),
        insights=["Teams with low usage may need a nudge to take a break before leave lapses."])

@q(21, 'AlertTriangle', None, ['Leave_Balances'])
def _():
    tot = defaultdict(float)
    for b in D['Leave_Balances']:
        if b['Leave_Year'] == 2026: tot[b['Emp_ID']] += b['Available_Balance']
    v = list(tot.values()); labs = ['Below 3 days', '3–5 days', '6–10 days', '11–20 days', '21–30 days', 'Over 30 days']; bk = bucket(v, [3, 6, 11, 21, 31], labs); low = bk[0] + bk[1]
    return dict(
        briefing=f"**{n(low)}** employees ({pct(low, len(v), 0):.0f}% of {n(len(v))}) have fewer than 6 leave days left across all leave types, while **{n(bk[-1])}** still have more than 30.",
        kpis=[kpi('Almost out of leave', low, sub='under 6 days left', tone='down'), kpi('Average days left', r1(mean(v)), 'days')],
        chart=dict(type='bar', categories=labs, series=[dict(name='Employees', data=bk)], fmt='int', pointTones=['bad', 'warn', 'neutral', 'good', 'good', 'brand']),
        insights=["Employees with very low balances are at risk of taking Loss-of-Pay leave."])

@q(22, 'Grid3x3', 'Key', ['Leave_Requests'])
def _():
    A = [l for l in _lv() if l['Status'] == 'Approved' and l['From_Date'].year == 2025]; types = ['Casual Leave', 'Sick Leave', 'Earned Leave', 'Special Leaves']
    sp = ('Marriage Leave', 'Maternity Leave', 'Paternity Leave', 'Bereavement Leave'); M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    c = Counter()
    for l in A:
        k = l['Leave_Name'] if l['Leave_Name'] in types[:3] else ('Special Leaves' if l['Leave_Name'] in sp else None)
        if k: c[(l['From_Date'].month - 1, k)] += l['Days']
    data = [[x, y, round(c[(x, t)])] for y, t in enumerate(types) for x in range(12)]; mt = Counter()
    for x, y, v in data: mt[x] += v
    pk = max(mt, key=mt.get); top = max(data, key=lambda d: d[2])
    return dict(
        briefing=f"The heaviest leave month in 2025 was **{M[pk]}** (**{n(mt[pk])} days**). The single busiest combination is **{types[top[1]]}** in **{M[top[0]]}** with **{n(top[2])} days**.",
        kpis=[kpi('Busiest month', mt[pk], 'int', M[pk] + ' 2025'), kpi('Quietest month', min(mt.values()), 'int', M[min(mt, key=mt.get)])],
        chart=dict(type='heatmap', xs=M, ys=types, data=data, fmt='int'),
        insights=["Plan project deadlines around the darker months to avoid staffing gaps."])

@q(23, 'CalendarPlus', None, ['Leave_Requests'])
def _():
    v = [l['Notice_Days'] for l in _lv() if l['Status'] != 'Cancelled']; labs = ['Same day / after', '1–3 days', '4–7 days', '8–14 days', '15–30 days', 'Over 30 days']; bk = bucket(v, [1, 4, 8, 15, 31], labs)
    return dict(
        briefing=f"Employees apply **{r1(mean(v))} days** ahead on average. **{pct(bk[0] + bk[1], len(v), 0):.0f}%** of requests come with 3 days notice or less, usually sick or emergency leave.",
        kpis=[kpi('Average notice', r1(mean(v)), 'days'), kpi('Planned 2+ weeks ahead', pct(bk[4] + bk[5], len(v)), 'pct', tone='up'), kpi('Last-minute (≤3 days)', pct(bk[0] + bk[1], len(v)), 'pct')],
        chart=dict(type='bar', categories=labs, series=[dict(name='Leave requests', data=bk)], fmt='int', gradient=True),
        insights=["Longer leaves (Earned, Marriage, Maternity) are planned weeks in advance."])

@q(24, 'PartyPopper', None, ['Holiday_Calendar'])
def _():
    H = sorted([h for h in D['Holiday_Calendar'] if h['Holiday_Date'].year == 2026], key=lambda h: h['Holiday_Date'])
    rows = [[h['Holiday_Date'].strftime('%d %b %Y'), h['Holiday_Date'].strftime('%A'), h['Holiday_Name'], h['Holiday_Type'], 'Done' if h['Holiday_Date'] <= ASOF else 'Upcoming'] for h in H]; up = [h for h in H if h['Holiday_Date'] > ASOF]
    return dict(
        briefing=f"The company has **{len(H)}** public holidays in 2026. **{len(up)}** are still to come — the next one is **{up[0]['Holiday_Name']}** on **{up[0]['Holiday_Date'].strftime('%d %b')}**.",
        kpis=[kpi('Holidays in 2026', len(H)), kpi('Still to come', len(up)), kpi('Next holiday', (up[0]['Holiday_Date'] - ASOF).days, 'days', up[0]['Holiday_Name'] + ' — days to go')],
        chart=dict(type='table', columns=['Date', 'Day', 'Holiday', 'Type', 'Status'], rows=rows),
        insights=["Holidays that fall on weekends are not counted as leave days."])
