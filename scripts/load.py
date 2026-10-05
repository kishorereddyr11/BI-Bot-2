import openpyxl, pickle, sys, datetime as dt, os
sys.path.insert(0, os.path.dirname(__file__))
from compute import enrich
SRC = os.environ.get("XLSX", "data/HR_Recruitment_and_Helpdesk_Tracker.xlsx")
SKIP = ("README", "Data_Dictionary", "Settings", "Lists")

def load():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    out = {}
    for ws in wb:
        if ws.title in SKIP: continue
        rows = list(ws.iter_rows(values_only=True))
        hdr = [h for h in rows[0] if h is not None]; n = len(hdr)
        body = []
        for r in rows[1:]:
            r = [(c.date() if isinstance(c, dt.datetime) else c) for c in r[:n]]
            if any(c is not None for c in r): body.append(r)
        out[ws.title] = (hdr, body)
    return enrich(out)

if __name__ == "__main__":
    T = load()
    pickle.dump(T, open(sys.argv[1], "wb"))
    for k, (h, b) in T.items():
        empty = [c for i, c in enumerate(h) if all(r[i] is None for r in b[:500])]
        print(k, len(b), "still-empty cols:", empty)
