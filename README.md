# School science practicals database

192 GCSE and A-Level practicals (124 physics, 35 chemistry, 33 biology) with the student procedure on one side and the technician's kit list on the other, flagged against the AQA, OCR and Edexcel required practicals. Comes with printable A6 recipe cards.

## What's in it

| File | What it is |
|---|---|
| `data/experiments.csv` | One row per practical: ID, title, level, topic, type (experiment or demo), required-practical flags for AQA / OCR / Edexcel, ★ if often examined, aim, variables, method, measurements, analysis, safety, data skills, common errors and improvements, time, technician preparation notes |
| `data/equipment.csv` | One row per item per practical: experiment ID, item, quantity per group, notes. Filter by ID to get a kit list |
| `data/physics_experiments_db.xlsx` | The same data as a colour-coded workbook (blue GCSE, yellow A-Level, green both, grey demonstrations) |
| `cards/*.pdf` | Ready-to-print cards: all, GCSE only, A-Level only |
| `make_cards.py` | Rebuilds the cards from the CSVs, with filters |
| `browser/index.html` | A searchable, filterable page for the physics practicals. Open it in any browser |

The two CSVs are flat and linked by ID, so they import straight into Notion, Airtable or Google Sheets as two related tables.

## Printing cards

```bash
pip install reportlab
python make_cards.py --board AQA --required --out aqa-required.pdf
python make_cards.py --level A-Level --out a-level.pdf
python make_cards.py --ids GCSE-01 THERM-03 --out this-week.pdf
```

Cards are A6, four to an A4 sheet. Print double-sided, flipping on the long edge, and the technician side lands behind the student side. Cut along the dashed lines.

## Contributing

Additions and corrections are very welcome, especially:

- practicals for other boards (WJEC/Eduqas, CCEA, Cambridge IGCSE and 9702, IB)
- updated required-practical flags when specifications change
- better methods, common errors, or kit you've found works

Edit the CSVs (keep the same columns and ID pattern) and open a pull request. If you don't use Git, open an issue and paste your suggestion in.

## Please note

Required-practical flags reflect the AQA, OCR and Edexcel specifications at the time of writing; check against the current published spec. Safety notes are summaries only. Always consult CLEAPSS (or SSERC in Scotland) and your own department's risk assessments before running a practical.

## Licence

Data, cards and the browser page: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Use and adapt them freely, credit Joe Rowing, and share adaptations under the same licence. `make_cards.py`: MIT. See [LICENSE](LICENSE).
