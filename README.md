# BI Bot — Infinyty HR Analytics (demo)

Conversational-style analytics demo on a dummy HR workbook: **98 fixed questions** (each = chart + key numbers + plain-English explanation), a **15-chart dashboard** and a **34-table dataset browser**. No backend — a static site.

## Run
```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # static output in dist/ (deploy to Vercel as-is)
```

## Tabs
- **Copilot** – left Question Library (search + category dropdown); click a question and the answer appears in the chat. Typing is disabled by design; the trash button clears the chat.
- **Dashboard** – 15 fixed charts + KPI strip.
- **Dataset** – every table, 200 rows per page, column sorting, in-table search, CSV download.

## Data pipeline
`data/HR_Recruitment_and_Helpdesk_Tracker.xlsx` is the single source. The workbook has no cached formula values, so `scripts/compute.py` re-creates every calculated (grey) column.

```bash
pip install openpyxl
npm run data       # rebuilds public/data/*.json, src/data/*.json from the xlsx + QUESTION_LIBRARY.md
node scripts/gen-icons.mjs   # only if question icons change
```
- Questions/categories: `QUESTION_LIBRARY.md` (text) + `scripts/q_*.py` (the calculation for each question number).
- Generated JSON is committed so Vercel only needs `npm run build`.
