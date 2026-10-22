"""
Generate SIMULATED demo files for the electricity client report workflow.

All companies and figures are fictional (consistent, but invented) and every file says so.
Use them to test the workflow end to end; use real APR data for the thesis demo.

    cd backend/orchestrator-lambda
    uv run --extra local-rag python ../../demo-data/simulated/generate.py

Writes next to this script:
- primer-energija-finansijski-izvestaj-2025.pdf   ("Coala" file: client financial statements)
- primer-energija-peers-2025.xlsx                 ("Checkpoint" file: peer comparison)
"""
from pathlib import Path

import openpyxl
import pymupdf
from openpyxl.styles import Font

OUT = Path(__file__).resolve().parent
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

CLIENT = "Primer Energija d.o.o."
NOTE = "SIMULIRANI PODACI - izmišljeno preduzeće, samo za testiranje (simulated data)"

# (name, AOP or "", 2025, 2024) in thousands of RSD; None = heading
BALANCE_SHEET = [
    ("AKTIVA", None, None, None),
    ("Stalna imovina", "", 1_120_000, 1_060_000),
    ("Obrtna imovina", "", 2_730_000, 2_460_000),
    ("  Zalihe", "", 380_000, 355_000),
    ("  Potraživanja po osnovu prodaje", "", 1_940_000, 1_710_000),
    ("  Gotovina i gotovinski ekvivalenti", "", 410_000, 395_000),
    ("UKUPNA AKTIVA", "0059", 3_850_000, 3_520_000),
    ("PASIVA", None, None, None),
    ("Kapital", "", 1_310_000, 1_081_350),
    ("Dugoročna rezervisanja i obaveze", "", 540_000, 610_000),
    ("Kratkoročne obaveze", "", 2_000_000, 1_828_650),
    ("UKUPNA PASIVA", "", 3_850_000, 3_520_000),
]

INCOME_STATEMENT = [
    ("POSLOVNI PRIHODI", "1001", 9_420_000, 8_620_000),
    ("  Prihodi od prodaje robe", "1002", 9_180_000, 8_410_000),
    ("  Prihodi od prodaje proizvoda i usluga", "1005", 240_000, 210_000),
    ("POSLOVNI RASHODI", "", 9_105_000, 8_365_000),
    ("  Nabavna vrednost prodate robe", "", 8_760_000, 8_050_000),
    ("  Troškovi zarada i naknada", "", 142_000, 131_000),
    ("  Troškovi amortizacije", "", 61_000, 57_000),
    ("  Ostali poslovni rashodi", "", 142_000, 127_000),
    ("POSLOVNI DOBITAK", "", 315_000, 255_000),
    ("Finansijski prihodi", "", 62_000, 48_000),
    ("Finansijski rashodi", "", 118_000, 104_000),
    ("Ostali prihodi", "", 23_000, 19_000),
    ("Ostali rashodi", "", 13_000, 11_000),
    ("UKUPNI PRIHODI", "1043", 9_505_000, 8_687_000),
    ("UKUPNI RASHODI", "1044", 9_236_000, 8_480_000),
    ("DOBITAK PRE OPOREZIVANJA", "", 269_000, 207_000),
    ("Porez na dobitak", "", 40_350, 31_050),
    ("NETO DOBITAK", "", 228_650, 175_950),
]

# Peer Excel: the six key AOPs per company; last column is the industry aggregate
KEY_ROWS = [
    ("UKUPNA AKTIVA", "0059"),
    ("POSLOVNI PRIHODI", "1001"),
    ("PRIHODI OD PRODAJE ROBE", "1002"),
    ("PRIHODI OD PRODAJE PROIZVODA I USLUGA", "1005"),
    ("UKUPNI PRIHODI", "1043"),
    ("UKUPNI RASHODI", "1044"),
]
PEERS = {
    CLIENT:                  [3_850_000, 9_420_000, 9_180_000, 240_000, 9_505_000, 9_236_000],
    "Voltis Trade d.o.o.":   [12_400_000, 28_750_000, 28_300_000, 450_000, 29_010_000, 28_420_000],
    "Elektra Mreža d.o.o.":  [6_120_000, 14_980_000, 14_600_000, 380_000, 15_140_000, 14_905_000],
    "Sunce Energija d.o.o.": [2_240_000, 4_310_000, 3_950_000, 360_000, 4_355_000, 4_190_000],
    "Dunav Power d.o.o.":    [1_180_000, 3_060_000, 2_990_000, 70_000, 3_092_000, 3_051_000],
}
INDUSTRY_TOTAL = [98_500_000, 241_300_000, 236_800_000, 4_500_000, 244_900_000, 238_700_000]


def _number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def write_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_font(fontname="ar", fontfile=FONT)
    page.insert_font(fontname="arb", fontfile=FONT_BOLD)

    y = 50

    def line(text, x=50, size=9, bold=False, color=(0, 0, 0)):
        page.insert_text((x, y), text, fontname="arb" if bold else "ar", fontsize=size, color=color)

    line(NOTE, size=8, bold=True, color=(0.75, 0, 0)); y += 22
    line("FINANSIJSKI IZVEŠTAJ ZA 2025. GODINU", size=14, bold=True); y += 18
    line(f"{CLIENT} · Šifra delatnosti: 3514 - Trgovina električnom energijom · Beograd"); y += 13
    line("Matični broj: 00000000 (izmišljen) · Iznosi u hiljadama dinara (RSD)"); y += 24

    for title, rows in (("BILANS STANJA na dan 31.12.2025.", BALANCE_SHEET),
                        ("BILANS USPEHA za period 01.01. - 31.12.2025.", INCOME_STATEMENT)):
        line(title, size=11, bold=True); y += 16
        line("Pozicija", bold=True); line("AOP", x=330, bold=True)
        line("2025", x=400, bold=True); line("2024", x=480, bold=True); y += 4
        page.draw_line((50, y), (545, y), width=0.5); y += 12
        for name, aop, current, previous in rows:
            if aop is None:
                line(name, bold=True); y += 13
                continue
            bold = name.isupper()
            line(name, bold=bold)
            line(aop, x=330)
            line(_number(current), x=400, bold=bold)
            line(_number(previous), x=480, bold=bold)
            y += 13
        y += 14

    doc.set_metadata({"title": f"{CLIENT} - finansijski izveštaj 2025 (simulirano)",
                      "subject": NOTE})
    doc.save(path)


def write_excel(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Peers 2025"
    sheet.append(["Pozicija", "AOP", *PEERS, "Delatnost ukupno"])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for i, (name, aop) in enumerate(KEY_ROWS):
        sheet.append([name, aop, *(values[i] for values in PEERS.values()), INDUSTRY_TOTAL[i]])
    for row in sheet.iter_rows(min_row=2, min_col=2, max_col=2):
        row[0].number_format = "@"
    sheet.append([])
    sheet.append([NOTE])
    sheet.append(["Iznosi u hiljadama RSD, 2025. Delatnost ukupno: simulirani zbir delatnosti 35.14."])
    sheet.column_dimensions["A"].width = 42
    workbook.save(path)


if __name__ == "__main__":
    pdf = OUT / "primer-energija-finansijski-izvestaj-2025.pdf"
    xlsx = OUT / "primer-energija-peers-2025.xlsx"
    write_pdf(pdf)
    write_excel(xlsx)
    print(f"Wrote {pdf}\nWrote {xlsx}")
