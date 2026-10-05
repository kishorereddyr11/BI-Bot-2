"""Re-creates the Excel formula (grey) columns, since the workbook ships without cached values."""
import datetime as dt, math, bisect
from collections import defaultdict, Counter

ASOF = dt.date(2026, 9, 30)

def xr(x, nd=0):
    """Excel ROUND (half away from zero)."""
    m = 10 ** nd
    return math.floor(abs(x) * m + 0.5) / m * (1 if x >= 0 else -1) if nd else int(math.floor(abs(x) + 0.5) * (1 if x >= 0 else -1))

def som(d): return dt.date(d.year, d.month, 1)
def edate(d, months):
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    m += 1
    import calendar
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))
def fy(d):
    y = d.year if d.month >= 4 else d.year - 1
    return f"FY{y}-{(y + 1) % 100:02d}"

def networkdays(a, b, hol):
    if a > b: return 0
    n = (b - a).days + 1
    full, rem = divmod(n, 7)
    cnt = full * 5
    s = a.weekday()
    for i in range(rem):
        if (s + i) % 7 < 5: cnt += 1
    for h in hol:
        if a <= h <= b and h.weekday() < 5: cnt -= 1
    return cnt

def enrich(T):
    """T: {name: (header, rows)} ; rows are lists mutated in place."""
    H = {k: {c: i for i, c in enumerate(v[0])} for k, v in T.items()}
    R = {k: v[1] for k, v in T.items()}
    def g(t, r, c): return r[H[t][c]]
    def s(t, r, c, v): r[H[t][c]] = v
    hol = sorted({r[1] for r in R['Holiday_Calendar']})

    # ---- masters
    for r in R['Round_Plan']:
        rn = {x[0]: x[1] for x in R['Rounds']}
        s('Round_Plan', r, 'Round_Name', rn.get(g('Round_Plan', r, 'Round_ID'), ''))
    cnt = Counter(g('Round_Plan', r, 'Experience_Level') for r in R['Round_Plan'])
    for r in R['Experience_Levels']: s('Experience_Levels', r, 'No_of_Rounds', cnt[r[0]])
    for r in R['Holiday_Calendar']:
        d = g('Holiday_Calendar', r, 'Holiday_Date'); s('Holiday_Calendar', r, 'Year', d.year); s('Holiday_Calendar', r, 'Day_Of_Week', d.strftime('%A'))
    for r in R['Payroll_Calendar']:
        pm = r[0]; s('Payroll_Calendar', r, 'Fiscal_Year', fy(pm))
        s('Payroll_Calendar', r, 'Status', 'Processed' if r[3] <= ASOF else ('In Progress' if r[1] <= ASOF else 'Upcoming'))
    for r in R['HR_Policies']:
        due = edate(g('HR_Policies', r, 'Last_Reviewed'), 12)
        s('HR_Policies', r, 'Review_Due_Date', due); s('HR_Policies', r, 'Review_Overdue', 'Yes' if due < ASOF else 'No')
    pn = {r[0]: r[1] for r in R['HR_Policies']}
    for r in R['HR_FAQs']: s('HR_FAQs', r, 'Policy_Name', pn.get(g('HR_FAQs', r, 'Policy_ID'), ''))

    # ---- lookups
    emp = {r[0]: r for r in R['Employees']}
    dept_of = {r[0]: g('Employees', r, 'Dept_ID') for r in R['Employees']}
    ename = {r[0]: r[1] for r in R['Employees']}
    app = {r[0]: r for r in R['Applications']}
    cand = {r[0]: r for r in R['Candidates']}
    req = {r[0]: r for r in R['Job_Requisitions']}
    ltype = {r[0]: r for r in R['Leave_Types']}
    rpol = {r[0]: r for r in R['Reimbursement_Policy']}
    dtype = {r[0]: r for r in R['Document_Types']}
    plan = {r[0]: r for r in R['Benefit_Plans']}
    rounds = {r[0]: r for r in R['Rounds']}

    # ---- applications
    first_offer = {}
    for r in R['Offers']:
        first_offer.setdefault(g('Offers', r, 'Application_ID'), r)
    for r in R['Applications']:
        ap = g('Applications', r, 'Applied_Date'); st = g('Applications', r, 'Overall_Status')
        s('Applications', r, 'Applied_Month', som(ap))
        upd = g('Applications', r, 'Status_Updated_Date')
        if st in ('In Progress', 'On Hold', 'Offered', 'Offer Accepted'): dp = (ASOF - ap).days
        else: dp = (upd - ap).days if upd else None
        s('Applications', r, 'Days_In_Pipeline', dp)
        if st in ('Hired', 'Offer Accepted', 'Did Not Join'):
            o = first_offer.get(r[0]); dd = g('Offers', o, 'Decision_Date') if o else None
            s('Applications', r, 'Time_To_Accept_Days', (dd - ap).days if dd else None)

    # ---- requisitions
    tot = Counter(); filled = Counter(); pend = Counter()
    for r in R['Applications']:
        rq = g('Applications', r, 'Req_ID'); st = g('Applications', r, 'Overall_Status')
        tot[rq] += 1
        if st == 'Hired': filled[rq] += 1
        if st == 'Offer Accepted': pend[rq] += 1
    for r in R['Job_Requisitions']:
        k = r[0]; op = g('Job_Requisitions', r, 'No_of_Openings'); od = g('Job_Requisitions', r, 'Req_Open_Date')
        cl = g('Job_Requisitions', r, 'Req_Closed_Date'); tg = g('Job_Requisitions', r, 'Target_Close_Date')
        s('Job_Requisitions', r, 'Total_Applications', tot[k]); s('Job_Requisitions', r, 'Positions_Filled', filled[k])
        s('Job_Requisitions', r, 'Offers_Accepted_Pending_Join', pend[k])
        s('Job_Requisitions', r, 'Fill_Rate', (filled[k] / op) if op else None)
        s('Job_Requisitions', r, 'Days_Open', ((cl or ASOF) - od).days)
        s('Job_Requisitions', r, 'Target_Breached', 'Yes' if (cl or ASOF) > tg else 'No')
        s('Job_Requisitions', r, 'Open_Month', som(od))
    # ---- candidates
    for r in R['Candidates']:
        cur = g('Candidates', r, 'Current_CTC_LPA'); ex = g('Candidates', r, 'Expected_CTC_LPA')
        s('Candidates', r, 'Expected_Hike_Pct', (ex / cur - 1) if cur else None)
    # ---- employees
    it = Counter(g('Interview_Panel', r, 'Emp_ID') for r in R['Interview_Panel'])
    rm = Counter(); rh = Counter()
    for r in R['Applications']:
        e = g('Applications', r, 'Referrer_Emp_ID')
        if e:
            rm[e] += 1
            if g('Applications', r, 'Overall_Status') == 'Hired': rh[e] += 1
    for r in R['Employees']:
        k = r[0]; doj = g('Employees', r, 'Date_of_Joining'); ex = g('Employees', r, 'Exit_Date')
        s('Employees', r, 'Hire_Year', doj.year); s('Employees', r, 'Interviews_Taken', it[k])
        s('Employees', r, 'Referrals_Made', rm[k]); s('Employees', r, 'Referral_Hires', rh[k])
        s('Employees', r, 'Employment_Status', 'Exited' if (ex and ex <= ASOF) else 'Active')
    dc = defaultdict(lambda: [0, 0]); 
    for r in R['Employees']:
        d = g('Employees', r, 'Dept_ID')
        if g('Employees', r, 'Employment_Status') == 'Active': dc[d][0] += 1
        if g('Employees', r, 'Source_Candidate_ID'): dc[d][1] += 1
    oc = Counter(g('Job_Requisitions', r, 'Dept_ID') for r in R['Job_Requisitions'] if g('Job_Requisitions', r, 'Req_Status') == 'Open')
    for r in R['Departments']:
        s('Departments', r, 'Active_Employees', dc[r[0]][0]); s('Departments', r, 'Open_Reqs', oc[r[0]]); s('Departments', r, 'Total_Hires', dc[r[0]][1])

    # ---- interviews
    ckey = {}
    for r in R['Interviews']:
        seq = rounds[g('Interviews', r, 'Round_ID')][2]
        if g('Interviews', r, 'Interview_Status') == 'Completed':
            ckey.setdefault((g('Interviews', r, 'Application_ID'), seq), g('Interviews', r, 'Scheduled_Date'))
    for r in R['Interviews']:
        rd = rounds[g('Interviews', r, 'Round_ID')]; seq = rd[2]; a = g('Interviews', r, 'Application_ID')
        sd = g('Interviews', r, 'Scheduled_Date'); stt = g('Interviews', r, 'Start_Time'); en = g('Interviews', r, 'End_Time')
        s('Interviews', r, 'Round_Name', rd[1]); s('Interviews', r, 'Round_Seq', seq)
        s('Interviews', r, 'Planned_Duration_Min', rd[3]); s('Interviews', r, 'Target_Gap_Days', rd[4])
        if stt and en: s('Interviews', r, 'Actual_Duration_Min', xr((en.hour * 60 + en.minute) - (stt.hour * 60 + stt.minute)))
        if seq == 1:
            prev = g('Applications', app[a], 'Shortlist_Date') if a in app else None
        else:
            prev = ckey.get((a, seq - 1)) or ckey.get((a, seq - 2)) or ckey.get((a, seq - 3))
        s('Interviews', r, 'Prev_Step_Date', prev)
        dsp = (sd - prev).days if prev else None
        s('Interviews', r, 'Days_Since_Prev_Round', dsp if dsp else (None if dsp is None else None))
        if dsp: s('Interviews', r, 'Gap_SLA_Breached', 'Yes' if dsp > rd[4] else 'No')
        fb = g('Interviews', r, 'Feedback_Date')
        s('Interviews', r, 'Feedback_TAT_Days', (fb - sd).days if fb else None)
        s('Interviews', r, 'Scheduled_Month', som(sd))
        s('Interviews', r, 'Completed_Key', f"{a}|{seq}" if g('Interviews', r, 'Interview_Status') == 'Completed' else None)
    for r in R['Interview_Panel']:
        e = g('Interview_Panel', r, 'Emp_ID')
        s('Interview_Panel', r, 'Interviewer_Name', ename.get(e, '')); s('Interview_Panel', r, 'Interviewer_Dept', dept_of.get(e, ''))
    # ---- offers
    for i, r in enumerate(R['Offers']):
        a = g('Offers', r, 'Application_ID'); ar = app.get(a)
        s('Offers', r, 'App_Row', list(app).index(a) + 2 if False else None)
        if ar:
            c = g('Applications', ar, 'Candidate_ID'); q = g('Applications', ar, 'Req_ID')
            s('Offers', r, 'Candidate_ID', c); s('Offers', r, 'Req_ID', q); s('Offers', r, 'Source_ID', g('Applications', ar, 'Source_ID'))
            cur = g('Candidates', cand[c], 'Current_CTC_LPA') if c in cand else None
            s('Offers', r, 'Current_CTC_LPA', cur)
            o = g('Offers', r, 'Offered_CTC_LPA')
            s('Offers', r, 'CTC_Hike_Pct', (o / cur - 1) if cur else None)
            bm = g('Job_Requisitions', req[q], 'Budget_Max_LPA') if q in req else None
            s('Offers', r, 'Budget_Max_LPA', bm)
            if bm is not None: s('Offers', r, 'Within_Budget', 'Yes' if o <= bm else 'No')
            s('Offers', r, 'Referral_Bonus_Eligible', 'Yes' if (g('Offers', r, 'Joining_Status') == 'Joined' and g('Applications', ar, 'Source_ID') == 'S02') else 'No')
        od = g('Offers', r, 'Offer_Date'); dd = g('Offers', r, 'Decision_Date'); aj = g('Offers', r, 'Actual_Joining_Date')
        s('Offers', r, 'Days_To_Decision', (dd - od).days if dd else None)
        s('Offers', r, 'Offer_To_Join_Days', (aj - od).days if aj else None)
        if ar is not None and r[-1] is None: pass
    # App_Row = row number of application in the Applications sheet
    arow = {r[0]: i + 2 for i, r in enumerate(R['Applications'])}
    for r in R['Offers']: s('Offers', r, 'App_Row', arow.get(g('Offers', r, 'Application_ID')))

    # ---- HR profile / salary
    for r in R['Employee_HR_Profile']:
        e = r[0]; er = emp[e]; ex = g('Employees', er, 'Exit_Date'); doj = g('Employees', er, 'Date_of_Joining')
        s('Employee_HR_Profile', r, 'Emp_Name', er[1]); s('Employee_HR_Profile', r, 'Dept_ID', g('Employees', er, 'Dept_ID'))
        s('Employee_HR_Profile', r, 'Date_of_Joining', doj); s('Employee_HR_Profile', r, 'Employment_Status', g('Employees', er, 'Employment_Status'))
        end = min(ex, ASOF) if ex else ASOF
        s('Employee_HR_Profile', r, 'Tenure_Years', xr((end - doj).days / 365.25, 1))
        s('Employee_HR_Profile', r, 'Manager_Name', ename.get(g('Employee_HR_Profile', r, 'Manager_ID'), None))
    for r in R['Salary_Structure']:
        C = g('Salary_Structure', r, 'Annual_CTC_INR'); D = g('Salary_Structure', r, 'Basic_Pct'); E = g('Salary_Structure', r, 'HRA_Pct_of_Basic')
        F = g('Salary_Structure', r, 'Is_PF_Gratuity_Applicable'); G = g('Salary_Structure', r, 'Employer_Insurance_Monthly_INR')
        Hm = xr(C / 12); I = xr(C * D / 12); J = xr(I * E)
        K = xr(min(I, 15000) * 0.12) if F == 'Yes' else 0
        L = xr(round(I * 0.0481, 6)) if F == 'Yes' else 0
        M = Hm - I - J - K - L - G
        for n, v in (('Monthly_CTC_INR', Hm), ('Basic_Monthly', I), ('HRA_Monthly', J), ('Employer_PF_Monthly', K), ('Gratuity_Monthly', L), ('Special_Allowance_Monthly', M), ('Gross_Monthly', I + J + M)):
            s('Salary_Structure', r, n, v)
        s('Salary_Structure', r, 'Dept_ID', dept_of.get(r[0]))
    for r in R['Salary_Revisions']:
        o = g('Salary_Revisions', r, 'Old_CTC_INR'); n = g('Salary_Revisions', r, 'New_CTC_INR')
        s('Salary_Revisions', r, 'Increment_Pct', (n / o - 1) if o else None); s('Salary_Revisions', r, 'Increment_Amount_INR', n - o)
        s('Salary_Revisions', r, 'Dept_ID', dept_of.get(g('Salary_Revisions', r, 'Emp_ID')))

    # ---- leave
    for r in R['Leave_Requests']:
        f = g('Leave_Requests', r, 'From_Date'); t = g('Leave_Requests', r, 'To_Date'); lt = g('Leave_Requests', r, 'Leave_Type_ID')
        wk = ltype[lt][7] == 'Yes'
        days = 0.5 if g('Leave_Requests', r, 'Is_Half_Day') == 'Yes' else ((t - f).days + 1 if wk else networkdays(f, t, hol))
        s('Leave_Requests', r, 'Days', days); s('Leave_Requests', r, 'Leave_Year', f.year); s('Leave_Requests', r, 'Leave_Month', som(f))
        ap = g('Leave_Requests', r, 'Applied_Date'); dd = g('Leave_Requests', r, 'Decision_Date')
        s('Leave_Requests', r, 'Notice_Days', (f - ap).days); s('Leave_Requests', r, 'Approval_TAT_Days', (dd - ap).days if dd else None)
        s('Leave_Requests', r, 'Leave_Name', ltype[lt][1]); s('Leave_Requests', r, 'Dept_ID', dept_of.get(g('Leave_Requests', r, 'Emp_ID')))
    used = defaultdict(float); up = defaultdict(float); pe = defaultdict(float)
    for r in R['Leave_Requests']:
        k = (g('Leave_Requests', r, 'Emp_ID'), g('Leave_Requests', r, 'Leave_Type_ID'), g('Leave_Requests', r, 'Leave_Year'))
        st = g('Leave_Requests', r, 'Status'); d = g('Leave_Requests', r, 'Days'); f = g('Leave_Requests', r, 'From_Date')
        if st == 'Approved':
            if f <= ASOF: used[k] += d
            else: up[k] += d
        elif st == 'Pending': pe[k] += d
    for r in R['Leave_Balances']:
        k = (g('Leave_Balances', r, 'Emp_ID'), g('Leave_Balances', r, 'Leave_Type_ID'), g('Leave_Balances', r, 'Leave_Year'))
        o = g('Leave_Balances', r, 'Opening_Balance'); c = g('Leave_Balances', r, 'Credited_Days')
        s('Leave_Balances', r, 'Used_Days', used[k]); s('Leave_Balances', r, 'Upcoming_Approved_Days', up[k]); s('Leave_Balances', r, 'Pending_Approval_Days', pe[k])
        s('Leave_Balances', r, 'Available_Balance', o + c - used[k] - up[k] - pe[k])
        s('Leave_Balances', r, 'Utilization_Pct', (used[k] / (o + c)) if (o + c) else None)
        s('Leave_Balances', r, 'Dept_ID', dept_of.get(r[1]))

    # ---- claims & payslips
    for r in R['Reimbursement_Claims']:
        cat = g('Reimbursement_Claims', r, 'Claim_Category'); ed = g('Reimbursement_Claims', r, 'Expense_Date'); cd = g('Reimbursement_Claims', r, 'Claim_Date')
        dd = g('Reimbursement_Claims', r, 'Decision_Date'); p = rpol.get(cat)
        lag = (cd - ed).days
        s('Reimbursement_Claims', r, 'Policy_Limit_INR', p[2] if p else None); s('Reimbursement_Claims', r, 'Submission_Lag_Days', lag)
        s('Reimbursement_Claims', r, 'Within_Window', ('Yes' if lag <= p[4] else 'No') if p else None)
        s('Reimbursement_Claims', r, 'Decision_TAT_Days', (dd - cd).days if dd else None)
        s('Reimbursement_Claims', r, 'Claim_Month', som(cd)); s('Reimbursement_Claims', r, 'Dept_ID', dept_of.get(r[1]))
    rsum = defaultdict(float)
    for r in R['Reimbursement_Claims']:
        pm = g('Reimbursement_Claims', r, 'Paid_In_Payslip_Month')
        if pm: rsum[(r[1], pm)] += g('Reimbursement_Claims', r, 'Approved_Amount_INR') or 0
    for r in R['Payslips']:
        pm = g('Payslips', r, 'Pay_Month'); gr = sum(g('Payslips', r, c) or 0 for c in ('Basic', 'HRA', 'Special_Allowance', 'Bonus'))
        de = sum(g('Payslips', r, c) or 0 for c in ('PF_Employee', 'Professional_Tax', 'TDS', 'Other_Deductions'))
        rb = rsum[(r[1], pm)]
        import calendar
        s('Payslips', r, 'Days_In_Month', calendar.monthrange(pm.year, pm.month)[1]); s('Payslips', r, 'Gross_Earnings', gr)
        s('Payslips', r, 'Total_Deductions', de); s('Payslips', r, 'Reimbursement_INR', rb); s('Payslips', r, 'Net_Pay', gr - de + rb)
        s('Payslips', r, 'Fiscal_Year', fy(pm)); s('Payslips', r, 'Dept_ID', dept_of.get(r[1]))

    # ---- benefits
    for r in R['Benefit_Enrollments']:
        p = plan.get(g('Benefit_Enrollments', r, 'Plan_ID'))
        s('Benefit_Enrollments', r, 'Plan_Name', p[1] if p else ''); s('Benefit_Enrollments', r, 'Plan_Category', p[2] if p else '')
        s('Benefit_Enrollments', r, 'Employer_Contribution_Monthly_INR', p[6] if p else 0); s('Benefit_Enrollments', r, 'Dept_ID', dept_of.get(r[1]))
    for r in R['Dependents']:
        dob = g('Dependents', r, 'Date_of_Birth'); s('Dependents', r, 'Age_Years', int((ASOF - dob).days / 365.25))
        s('Dependents', r, 'Employee_Name', ename.get(r[1], ''))

    # ---- documents & tickets
    for r in R['Document_Requests']:
        d = dtype.get(g('Document_Requests', r, 'Doc_Type_ID')); rq = g('Document_Requests', r, 'Requested_Date'); iss = g('Document_Requests', r, 'Issued_Date')
        s('Document_Requests', r, 'Doc_Name', d[1] if d else ''); s('Document_Requests', r, 'SLA_Working_Days', d[2] if d else None)
        if iss:
            tat = networkdays(rq, iss, hol) - 1; s('Document_Requests', r, 'TAT_Working_Days', tat)
            s('Document_Requests', r, 'SLA_Met', 'Yes' if tat <= d[2] else 'No')
        if g('Document_Requests', r, 'Status') not in ('Issued', 'Rejected'):
            s('Document_Requests', r, 'Open_Age_Days', networkdays(rq, ASOF, hol) - 1)
        s('Document_Requests', r, 'Request_Month', som(rq)); s('Document_Requests', r, 'Dept_ID', dept_of.get(r[1]))
    for r in R['Helpdesk_Tickets']:
        c = g('Helpdesk_Tickets', r, 'Created_Date'); rs = g('Helpdesk_Tickets', r, 'Resolved_Date'); pr = g('Helpdesk_Tickets', r, 'Priority')
        sla = 1 if pr == 'High' else (2 if pr == 'Medium' else 4)
        s('Helpdesk_Tickets', r, 'SLA_Days', sla)
        if rs:
            rd = (rs - c).days; s('Helpdesk_Tickets', r, 'Resolution_Days', rd); s('Helpdesk_Tickets', r, 'SLA_Met', 'Yes' if rd <= sla else 'No')
        s('Helpdesk_Tickets', r, 'Created_Month', som(c))
        s('Helpdesk_Tickets', r, 'Is_AI_Resolved', 'Yes' if g('Helpdesk_Tickets', r, 'Resolved_By') == 'AI Copilot' else 'No')
        s('Helpdesk_Tickets', r, 'Dept_ID', dept_of.get(r[1]))
    return T
