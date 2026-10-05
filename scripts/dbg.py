import pickle, sys, json, importlib
sys.path.insert(0, 'scripts')
import qlib
T = pickle.load(open("/tmp/claude-0/-home-user-BI-Bot/a186cc89-d325-580c-a800-259d2074a3b0/scratchpad/wb.pkl", "rb"))
for k, (h, b) in T.items(): qlib.D[k] = [dict(zip(h, r)) for r in b]
for m in sys.argv[1].split(','): importlib.import_module(m)
lo, hi = int(sys.argv[2]), int(sys.argv[3])
for k in sorted(qlib.REG):
    if lo <= k <= hi:
        try:
            r = qlib.REG[k]['fn']()
            print(f"--- Q{k}: {r['briefing']}")
            if '-v' in sys.argv: print(json.dumps(r['chart'], default=str)[:400])
        except Exception as e:
            import traceback; print(f"--- Q{k} ERROR", e); traceback.print_exc(limit=3)
