from qlib import *

def _rq(): return D['Job_Requisitions']
def _ap(): return D['Applications']
def SRC(): return {s['Source_ID']: s['Source_Name'] for s in D['Sources']}
def REQ(): return {r['Req_ID']: r for r in _rq()}

# ───────────────────────── 9. HIRING ─────────────────────────
@q(83, 'Briefcase', 'Popular', ['Job_Requisitions'])
def _():
    R = _rq(); c = Counter(r['Req_Status'] for r in R); openings = sum(r['No_of_Openings'] for r in R if r['Req_Status'] != 'Cancelled'); filled = sum(r['Positions_Filled'] for r in R if r['Req_Status'] != 'Cancelled')
    tone = {'Closed - Filled': 'good', 'Open': 'brand', 'Cancelled': 'neutral', 'On Hold': 'warn', 'Closed - Partially Filled': 'accent'}
    return dict(
        briefing=f"There have been **{n(len(R))}** job openings since 2020. **{c['Open']}** are open right now and **{n(c['Closed - Filled'])}** were fully filled. Overall **{pct(filled, openings, 0):.0f}%** of the positions we opened have been filled.",
        kpis=[kpi('Job openings', len(R)), kpi('Open now', c['Open'], tone='up'), kpi('Positions filled', filled), kpi('Fill rate', pct(filled, openings), 'pct')],
        chart=dict(type='donut', items=[dict(name=k, value=v, tone=tone.get(k)) for k, v in c.most_common()], fmt='int', centerValue=n(len(R)), centerLabel='job openings'),
        insights=[f"**{c['Cancelled']}** openings were cancelled before being filled.", f"Open positions are mostly in **Engineering** and **AI / ML**."])

@q(84, 'Filter', 'Key', ['Applications', 'Interviews', 'Offers'])
def _():
    A = _ap(); tot = len(A); sl = sum(a['Shortlist_Status'] == 'Shortlisted' for a in A); iv = len({i['Application_ID'] for i in D['Interviews'] if i['Interview_Status'] == 'Completed'})
    O = D['Offers']; off = len(O); acc = sum(o['Offer_Status'] == 'Accepted' for o in O); jn = sum(o['Joining_Status'] == 'Joined' for o in O)
    items = [dict(name='Applied', value=tot), dict(name='Shortlisted', value=sl), dict(name='Interviewed', value=iv), dict(name='Got an offer', value=off), dict(name='Accepted the offer', value=acc), dict(name='Joined', value=jn)]
    return dict(
        briefing=f"Of **{n(tot)}** applications, **{pct(sl, tot, 0):.0f}%** were shortlisted, **{pct(off, tot)}%** received an offer and **{n(jn)}** people (**{pct(jn, tot)}%**) finally joined. That is about **1 hire for every {round(tot / jn)} applications**.",
        kpis=[kpi('Applications', tot), kpi('Interviewed', iv), kpi('Offers made', off), kpi('Joined', jn, tone='up')],
        chart=dict(type='funnel', items=items, fmt='int'),
        insights=[f"**{pct(acc, off, 0):.0f}%** of offers were accepted and **{pct(jn, acc, 0):.0f}%** of those who accepted actually joined."])

@q(85, 'TrendingUp', 'Trend', ['Applications'])
def _():
    ms = month_range(dt.date(2020, 1, 1), ASOF); c = Counter(a['Applied_Month'] for a in _ap()); v = [c[m] for m in ms]; yr = Counter()
    for m in ms: yr[m.year] += c[m]
    pk = max(range(len(ms)), key=lambda i: v[i])
    return dict(
        briefing=f"Applications have grown from **{n(yr[2020])}** in 2020 to **{n(yr[2025])}** in 2025. The busiest month ever was **{ms[pk].strftime('%B %Y')}** with **{n(v[pk])}** applications.",
        kpis=[kpi('Total applications', sum(v)), kpi('Busiest month', v[pk], 'int', ms[pk].strftime('%b %Y')), kpi('Last full month', v[-2], 'int', ms[-2].strftime('%b %Y'))],
        chart=dict(type='area', categories=[ml(m) for m in ms], series=[dict(name='Applications', data=v)], fmt='int'),
        insights=[f"Applications per year: " + ', '.join(f"{y}: **{n(yr[y])}**" for y in sorted(yr)) + ' (2026 is till September).'])

@q(86, 'Handshake', 'Key', ['Applications', 'Sources'])
def _():
    sn = SRC(); g = groupby(_ap(), lambda a: a['Source_ID']); rows = []
    for k, v in g.items(): h = sum(a['Overall_Status'] == 'Hired' for a in v); rows.append((sn[k], h, pct(h, len(v), 2), len(v)))
    rows.sort(key=lambda x: -x[1]); best = max(rows, key=lambda x: x[2]); tot = sum(r[1] for r in rows)
    return dict(
        briefing=(f"**{rows[0][0]}** is both our biggest source (**{n(rows[0][1])}** hires) and our best-quality one — **{best[2]}%** of its applicants get hired." if best[0] == rows[0][0] else f"**{rows[0][0]}** brings the most hires (**{n(rows[0][1])}**), but **{best[0]}** has the best quality — **{best[2]}%** of its applicants get hired."),
        kpis=[kpi('Most hires', rows[0][1], 'int', rows[0][0]), kpi('Best hire rate', best[2], 'pct', best[0], 'up'), kpi('Total hires', tot)],
        chart=dict(type='combo', categories=[r[0] for r in rows], series=[dict(name='People hired', data=[r[1] for r in rows], kind='bar', axis=0, fmt='int'), dict(name='Hire rate (% of applicants)', data=[r[2] for r in rows], kind='line', axis=1, fmt='pct')], fmt='int', yNames=['Hires', 'Hire rate %']),
        insights=[f"Hire rate = hires ÷ applicants. Job boards convert only about **{r1(mean([r[2] for r in rows if r[0] in ('LinkedIn','Naukri','Indeed','Other Job Portals')]))}%**, far below referrals and campus drives."])

@q(87, 'BadgeIndianRupee', None, ['Applications', 'Sources', 'Offers'])
def _():
    S = {s['Source_ID']: s for s in D['Sources']}; lv = {l['Level_Code']: l['Referral_Bonus_INR'] for l in D['Experience_Levels']}; R = REQ(); offers = {o['Application_ID']: o for o in D['Offers']}
    g = defaultdict(list)
    for a in _ap():
        if a['Overall_Status'] != 'Hired': continue
        s = S[a['Source_ID']]; o = offers.get(a['Application_ID']); cost = s['Fixed_Cost_Per_Hire_INR']
        if s['Agency_Fee_Pct'] and o: cost += o['Offered_CTC_LPA'] * 1e5 * s['Agency_Fee_Pct'] / 100
        if s['Source_ID'] == 'S02': cost += lv.get(R[a['Req_ID']]['Experience_Level'], 0)
        g[s['Source_Name']].append(cost)
    rows = sorted([(k, round(mean(v)), len(v)) for k, v in g.items()], key=lambda x: x[1]); tot = sum(r[1] * r[2] for r in rows)
    return dict(
        briefing=f"Hiring through **{rows[0][0]}** is the cheapest (**{inr(rows[0][1])} per hire**). **{rows[-1][0]}** is the most expensive at **{inr(rows[-1][1])}** per hire. Total estimated sourcing cost is **{inr(tot)}**.",
        kpis=[kpi('Cheapest source', rows[0][1], 'inr', rows[0][0], 'up'), kpi('Costliest source', rows[-1][1], 'inr', rows[-1][0], 'down'), kpi('Avg. cost per hire', round(tot / sum(r[2] for r in rows)), 'inr')],
        chart=dict(type='bar', categories=[r[0] for r in rows], series=[dict(name='Cost per hire', data=[r[1] for r in rows])], fmt='inr', gradient=True),
        insights=["Cost = subscription or drive fees per hire, agency fee (8.33% of CTC) or referral bonus based on the hire's level."])

@q(88, 'Clock', None, ['Job_Requisitions', 'Roles'])
def _():
    rn = {r['Role_ID']: r['Role_Name'] for r in D['Roles']}; g = groupby([r for r in _rq() if r['Req_Status'] == 'Closed - Filled'], lambda r: rn[r['Role_ID']])
    rows = sorted([(k, round(mean([r['Days_Open'] for r in v])), len(v)) for k, v in g.items() if len(v) >= 5], key=lambda x: x[1])
    allv = [r['Days_Open'] for v in g.values() for r in v]
    return dict(
        briefing=f"A role takes **{round(mean(allv))} days** to fill on average. **{rows[-1][0]}** is the hardest to fill (**{rows[-1][1]} days**) and **{rows[0][0]}** the quickest (**{rows[0][1]} days**).",
        kpis=[kpi('Average time to fill', round(mean(allv)), 'days'), kpi('Slowest role', rows[-1][1], 'days', rows[-1][0], 'down'), kpi('Quickest role', rows[0][1], 'days', rows[0][0], 'up')],
        chart=dict(type='hbar', categories=[r[0] for r in rows[-12:]], series=[dict(name='Days to fill', data=[r[1] for r in rows[-12:]])], fmt='int', rank=True),
        insights=["Top 12 slowest roles shown. Senior and specialist roles take longer than entry-level ones."])

@q(89, 'AlarmClock', None, ['Job_Requisitions'])
def _():
    R = [r for r in _rq() if r['Req_Status'] != 'Cancelled']; br = sum(r['Target_Breached'] == 'Yes' for r in R); ok = len(R) - br
    return dict(
        briefing=f"**{n(br)}** of {n(len(R))} job openings ({pct(br, len(R), 0):.0f}%) took longer than the planned closing date. **{pct(ok, len(R), 0):.0f}%** were filled on time.",
        kpis=[kpi('Closed on time', pct(ok, len(R)), 'pct', tone='up'), kpi('Took too long', br, tone='down'), kpi('Avg. days over target', r1(mean([(( r['Req_Closed_Date'] or ASOF) - r['Target_Close_Date']).days for r in R if r['Target_Breached'] == 'Yes'])), 'days')],
        chart=dict(type='gauge', value=pct(ok, len(R)), max=100, fmt='pct', label='Filled by target date'),
        insights=["Each opening has a target close date set when it is approved; delays usually come from hard-to-find skills."])

@q(90, 'GitBranch', 'Key', ['Applications', 'Rejection_Reasons'])
def _():
    rr = {r['Reason_ID']: r['Reason'] for r in D['Rejection_Reasons']}; A = [a for a in _ap() if a['Overall_Status'] == 'Rejected' and a['Rejected_At_Stage'] and a['Rejection_Reason_ID']]
    stages = ['Resume Screening', 'HR Screening', 'Technical Round 1', 'Technical Round 2', 'Techno-Managerial Round', 'HR Interview']; A = [a for a in A if a['Rejected_At_Stage'] in stages]
    rc = Counter(rr[a['Rejection_Reason_ID']] for a in A); top = [k for k, _ in rc.most_common(8)]
    c = Counter((a['Rejected_At_Stage'], rr[a['Rejection_Reason_ID']] if rr[a['Rejection_Reason_ID']] in top else 'Other reasons') for a in A)
    stg = Counter(a['Rejected_At_Stage'] for a in A); links = [dict(source=s, target=r, value=v) for (s, r), v in c.items()]
    nodes = [dict(name=s, side='left') for s in stages] + [dict(name=r, side='right') for r in top + ['Other reasons']]
    tot = len(A)
    return dict(
        briefing=f"**{pct(stg['Resume Screening'], tot, 0):.0f}%** of rejections happen at resume screening. The top reason is \"**{rc.most_common(1)[0][0]}**\" (**{pct(rc.most_common(1)[0][1], tot, 0):.0f}%**), followed by \"**{rc.most_common(2)[1][0]}**\".",
        kpis=[kpi('Applications rejected', tot), kpi('Rejected at screening', stg['Resume Screening']), kpi('Rejected after interviews', tot - stg['Resume Screening'] - stg['HR Screening'])],
        chart=dict(type='sankey', nodes=nodes, links=links, fmt='int'),
        insights=["Read left to right: where in the process candidates were rejected, and why.", "Candidates who withdrew or declined offers are not counted here."])

@q(91, 'UserPlus', None, ['Applications', 'Job_Requisitions', 'Departments'])
def _():
    dn = DN(); R = REQ(); c = Counter(dn[R[a['Req_ID']]['Dept_ID']] for a in _ap() if a['Overall_Status'] == 'Hired'); it = c.most_common()[::-1]; tot = sum(c.values())
    return dict(
        briefing=f"**{it[-1][0]}** has hired the most people (**{n(it[-1][1])}**, {pct(it[-1][1], tot, 0):.0f}% of all hires), followed by **{it[-2][0]}** and **{it[-3][0]}**.",
        kpis=[kpi('Total hires', tot), kpi('Top hiring team', it[-1][1], 'int', it[-1][0])],
        chart=dict(type='hbar', categories=[k for k, _ in it], series=[dict(name='People hired', data=[v for _, v in it])], fmt='int', rank=True),
        insights=["Counts everyone hired through the recruitment process since 2020."])

@q(92, 'IndianRupee', None, ['Candidates'])
def _():
    labs = ['0–1 yr', '1–3 yrs', '3–5 yrs', '5–8 yrs', '8–12 yrs', '12+ yrs']; ed = [1, 3, 5, 8, 12]; C = [c for c in D['Candidates'] if c['Current_CTC_LPA']]
    g = defaultdict(list)
    for c in C:
        for i, e in enumerate(ed):
            if c['Total_Exp_Yrs'] < e: g[i].append(c); break
        else: g[5].append(c)
    cur = [r1(mean([c['Current_CTC_LPA'] for c in g[i]])) for i in range(6)]; ex = [r1(mean([c['Expected_CTC_LPA'] for c in g[i]])) for i in range(6)]; hk = [round(100 * (ex[i] / cur[i] - 1), 1) if cur[i] else 0 for i in range(6)]
    allh = [c['Expected_Hike_Pct'] * 100 for c in C]
    return dict(
        briefing=f"Candidates expect a **{r1(mean(allh))}%** salary jump on average, and the ask is similar at every experience level. In rupees it differs a lot: a 12+ year candidate expects **{lpa(ex[5])}** a year versus **{lpa(ex[0])}** for a 0–1 year candidate.",
        kpis=[kpi('Average expected hike', r1(mean(allh)), 'pct'), kpi('Average current pay', r1(mean([c['Current_CTC_LPA'] for c in C])), 'lpa'), kpi('Average expected pay', r1(mean([c['Expected_CTC_LPA'] for c in C])), 'lpa')],
        chart=dict(type='combo', categories=labs, series=[dict(name='Current pay (L / year)', data=cur, kind='bar', axis=0, fmt='lpa'), dict(name='Expected pay (L / year)', data=ex, kind='bar', axis=0, fmt='lpa'), dict(name='Expected hike %', data=hk, kind='line', axis=1, fmt='pct')], fmt='lpa', yNames=['Lakhs per year', 'Hike %']),
        insights=["Based on candidates who are currently employed (current pay above zero).", "L = Lakh per year."])

# ───────────────────────── 10. INTERVIEWS & OFFERS ─────────────────────────
ROUNDS = ['HR Screening', 'Technical Round 1', 'Technical Round 2', 'Techno-Managerial Round', 'HR Interview']

@q(93, 'ClipboardCheck', 'Popular', ['Interviews'])
def _():
    I = [i for i in D['Interviews'] if i['Interview_Status'] == 'Completed' and i['Result'] in ('Selected', 'Rejected')]; g = groupby(I, lambda i: i['Round_Name'])
    sel = [sum(i['Result'] == 'Selected' for i in g[r]) for r in ROUNDS]; rej = [sum(i['Result'] == 'Rejected' for i in g[r]) for r in ROUNDS]; pr = [pct(a, a + b) for a, b in zip(sel, rej)]
    return dict(
        briefing=f"**{pr[0]}%** of candidates pass the HR screening, but only **{pr[1]}%** clear Technical Round 1. The strictest round is **{ROUNDS[pr.index(min(pr))]}** with a **{min(pr)}%** pass rate.",
        kpis=[kpi(r, p, 'pct', 'pass rate') for r, p in zip(ROUNDS[:4], pr[:4])],
        chart=dict(type='combo', categories=ROUNDS, series=[dict(name='Passed', data=sel, kind='bar', axis=0, stack='a', tone='good'), dict(name='Not passed', data=rej, kind='bar', axis=0, stack='a', tone='bad'), dict(name='Pass rate %', data=pr, kind='line', axis=1, fmt='pct')], fmt='int', yNames=['Interviews', 'Pass rate %']),
        insights=[f"Based on **{n(len(I))}** completed interviews with a result."])

@q(94, 'Timer', None, ['Interviews'])
def _():
    I = D['Interviews']; g = groupby([i for i in I if i['Days_Since_Prev_Round'] is not None], lambda i: i['Round_Name']); wait = [r1(mean([i['Days_Since_Prev_Round'] for i in g[r]])) for r in ROUNDS]
    tg = [{i['Round_Name']: i['Target_Gap_Days'] for i in I}[r] for r in ROUNDS]; fb = [i['Feedback_TAT_Days'] for i in I if i['Feedback_TAT_Days'] is not None]; br = [i['Gap_SLA_Breached'] for i in I if i['Gap_SLA_Breached']]
    return dict(
        briefing=f"Candidates wait **{r1(mean([i['Days_Since_Prev_Round'] for v in g.values() for i in v]))} days** on average between steps, and **{pct(sum(b == 'Yes' for b in br), len(br), 0):.0f}%** of interviews happen later than planned. Feedback is shared **{r1(mean(fb))} days** after the interview.",
        kpis=[kpi('Average wait between rounds', r1(mean([i['Days_Since_Prev_Round'] for v in g.values() for i in v])), 'days'), kpi('Later than planned', pct(sum(b == 'Yes' for b in br), len(br)), 'pct', tone='down'), kpi('Feedback after interview', r1(mean(fb)), 'days')],
        chart=dict(type='bar', categories=ROUNDS, series=[dict(name='Actual wait (days)', data=wait), dict(name='Target wait (days)', data=tg)], fmt='dec1'),
        insights=["Wait = days since the previous step (shortlisting or the earlier round)."])

@q(95, 'Mic', None, ['Interview_Panel'])
def _():
    c = Counter(p['Interviewer_Name'] for p in D['Interview_Panel']); it = c.most_common(10)[::-1]; tot = len(D['Interview_Panel'])
    return dict(
        briefing=f"**{it[-1][0]}** has taken the most interviews (**{n(it[-1][1])}**). The top 10 interviewers together handled **{pct(sum(v for _, v in it), tot, 0):.0f}%** of all panel slots.",
        kpis=[kpi('Interviewers', len(c)), kpi('Most interviews', it[-1][1], 'int', it[-1][0]), kpi('Avg. per interviewer', round(mean(list(c.values()))))],
        chart=dict(type='hbar', categories=[k for k, _ in it], series=[dict(name='Interviews taken', data=[v for _, v in it])], fmt='int', rank=True),
        insights=["Counts every time someone sat on an interview panel."])

@q(96, 'PartyPopper', 'Popular', ['Offers'])
def _():
    O = D['Offers']; c = Counter()
    for o in O:
        if o['Offer_Status'] == 'Accepted': c[{'Joined': 'Joined', 'Did Not Join': 'Accepted but did not join', 'Pending': 'Accepted, yet to join'}.get(o['Joining_Status'], 'Accepted, yet to join')] += 1
        elif o['Offer_Status'] == 'Declined': c['Declined by candidate'] += 1
        elif o['Offer_Status'] == 'Revoked': c['Withdrawn by company'] += 1
        else: c['Waiting for reply'] += 1
    tone = {'Joined': 'good', 'Accepted, yet to join': 'brand', 'Accepted but did not join': 'warn', 'Declined by candidate': 'bad', 'Withdrawn by company': 'neutral', 'Waiting for reply': 'accent'}; tot = len(O)
    return dict(
        briefing=f"Out of **{n(tot)}** offers, **{pct(c['Joined'], tot, 0):.0f}%** ended with the person joining. **{pct(c['Declined by candidate'], tot, 0):.0f}%** of candidates declined and **{c['Accepted but did not join']}** accepted but never turned up.",
        kpis=[kpi('Offers made', tot), kpi('Joined', c['Joined'], tone='up'), kpi('Declined', c['Declined by candidate'], tone='down'), kpi('Did not turn up', c['Accepted but did not join'])],
        chart=dict(type='donut', items=[dict(name=k, value=v, tone=tone[k]) for k, v in c.most_common()], fmt='int', centerValue=f"{pct(c['Joined'], tot, 0):.0f}%", centerLabel='joined'),
        insights=[f"Acceptance rate: **{pct(sum(1 for o in O if o['Offer_Status'] == 'Accepted'), tot, 0):.0f}%** of offers were accepted."])

@q(97, 'TrendingUp', None, ['Offers'])
def _():
    O = [o for o in D['Offers'] if o['CTC_Hike_Pct'] is not None]; v = [o['CTC_Hike_Pct'] * 100 for o in O]; labs = ['Below 0%', '0–10%', '10–20%', '20–30%', '30–50%', '50–100%', 'Over 100%']; bk = bucket(v, [0, 10, 20, 30, 50, 100], labs)
    wb = [o for o in D['Offers'] if o['Within_Budget']]; ok = sum(o['Within_Budget'] == 'Yes' for o in wb)
    return dict(
        briefing=f"Offers come with an average salary hike of **{r1(mean(v))}%** (typical: **{r1(median(v))}%**). **{pct(ok, len(wb), 0):.0f}%** of offers stay within the approved budget.",
        kpis=[kpi('Average hike', r1(mean(v)), 'pct'), kpi('Typical hike', r1(median(v)), 'pct', 'median'), kpi('Within budget', pct(ok, len(wb)), 'pct', tone='up'), kpi('Over budget', len(wb) - ok, tone='down' if len(wb) - ok else None)],
        chart=dict(type='bar', categories=labs, series=[dict(name='Offers', data=bk)], fmt='int', gradient=True),
        insights=["Hike is measured against the candidate's current pay; freshers with no current pay are excluded."])

@q(98, 'CalendarCheck', None, ['Offers', 'Job_Requisitions'])
def _():
    R = REQ(); O = D['Offers']; g = defaultdict(list)
    for o in O: g[R[o['Req_ID']]['Experience_Level']].append(o)
    dd = [r1(mean([o['Days_To_Decision'] for o in g[l] if o['Days_To_Decision'] is not None])) for l in LEVELS]; jj = [r1(mean([o['Offer_To_Join_Days'] for o in g[l] if o['Offer_To_Join_Days'] is not None])) for l in LEVELS]
    ad = [o['Days_To_Decision'] for o in O if o['Days_To_Decision'] is not None]; aj = [o['Offer_To_Join_Days'] for o in O if o['Offer_To_Join_Days'] is not None]
    return dict(
        briefing=f"Candidates take **{r1(mean(ad))} days** to answer an offer and **{r1(mean(aj))} days** from offer to joining. **{LEVELS[jj.index(max(jj))]}** hires take the longest to join (**{max(jj)} days**) because of notice periods.",
        kpis=[kpi('Days to decide', r1(mean(ad)), 'days'), kpi('Days to join', r1(mean(aj)), 'days'), kpi('Longest to join', max(jj), 'days', LEVELS[jj.index(max(jj))], 'down')],
        chart=dict(type='bar', categories=LEVELS, series=[dict(name='Days to decide', data=dd), dict(name='Days from offer to joining', data=jj)], fmt='dec1'),
        insights=["Interns and freshers join fastest; experienced hires must serve notice periods first."])
