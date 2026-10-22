# Demo data

A Client Report needs two files per client, uploaded in the "New analysis" form:

1. **Client financial statements (PDF)** — read directly by Claude for the Market Position.
2. **Peer Excel** — the client and its Peer group side by side, for the Peer Analysis.

Use public data only. Put the files you download or prepare in `demo-data/private/`
(git-ignored) and note every source in the table at the bottom.

## 1. Client financial statements

Serbian companies' annual financial statements are public in the **APR register of financial
statements** (Agencija za privredne registre → Registar finansijskih izveštaja → Pretraga
finansijskih izveštaja): search by company name or registration number (matični broj) and
download the statement for the last completed year as PDF.

Pick a client whose NACE category matches a demo industry:

| Industry | NACE categories | Form in the app |
|---|---|---|
| Electricity | D35.10 – D35.16, D35.40 (e.g. D35.14 Trade of electricity) | New analysis → Electricity |
| Cereals | A1.11 Growing of cereals (the form always files the report under A1.11, so a grain trader works too) | New analysis |

## 2. Peer Excel

Start from [`peer_template.xlsx`](./peer_template.xlsx). The layout is what the Peer Analysis
prompt expects (a "Tree List": rows are statement positions, columns are companies):

| Pozicija | AOP | Client | Peer 1 | … | **Delatnost ukupno** |
|---|---|---|---|---|---|
| UKUPNA AKTIVA | 0059 | | | | |
| POSLOVNI PRIHODI | 1001 | | | | |
| PRIHODI OD PRODAJE ROBE | 1002 | | | | |
| PRIHODI OD PRODAJE PROIZVODA I USLUGA | 1005 | | | | |
| UKUPNI PRIHODI | 1043 | | | | |
| UKUPNI RASHODI | 1044 | | | | |

Rules:
- **One column per company**, the column header is the company name. Include the client.
- **AOP codes as text** (`0059`, not `59`) — the template's AOP column is already text.
- Copy the values from each company's APR statement for the **same year** and in the **same
  unit** (APR statements are in thousands of RSD).
- More AOP rows (the full balance sheet and income statement) are welcome; the six above are
  the ones the analysis is built on.
- **The last column is the Industry aggregate** (`Delatnost ukupno`): the sector total for the
  client's NACE category, used as the denominator for market shares. Take it from official
  sector statistics — the APR annual bulletin of financial statements (aggregates by
  activity) or the RZS structural business statistics — for the positions where a total is
  published. **Leave cells empty where no official total exists**; the report then says
  "Data not available" instead of inventing a share. Do not use the sum of the peers.

Upload the sheet in the same form as the PDF. The app names it after the analysis, so the
Peer Analysis is linked to the Market Position automatically.

## Sources used

| File | Company / statistic | Source (URL) | Year | Retrieved |
|---|---|---|---|---|
| | | | | |
