# Does a local MP get a local bonus?

Every MP returned at a UK general election from 1832 to 2024 (31,737 returns of 10,094 people), linked to their birthplace and to constituency results, to test whether MPs born near their seat win more votes, swing better, lose less often and serve longer. Six designs, written down with their checks before any outcome model was run (see `NOTES.md`).

Interactive page: https://maps.tristanhotham.com/local-mp-bonus/
Paper: https://doi.org/10.5281/zenodo.24092361
Blog post: https://blog.tristanhotham.com/2026/10/31/local-mp-bonus/
Code and data: https://github.com/Tristan-Hotham/local-mp-bonus

## Headline results

- **Vote share (main, pre-specified):** an MP born within 25 km of the seat won 1.29 (95% CI 0.73 to 1.85; N = 14,580) percentage points more of the vote than other MPs elected for the same seat, net of their party's national performance (seat and election by party fixed effects; SE clustered by constituency). With seat by party fixed effects (same party, same seat): 1.32 (95% CI 0.70 to 1.95; N = 14,580). Among first-time winners only (added at review): 1.31 (95% CI 0.66 to 1.95; N = 3,989).
- **Re-election:** local incumbents gained 0.31 (95% CI 0.06 to 0.56; N = 10,257) points more at re-election. **Succession:** each step in localness from predecessor to successor of the same party raised the party's relative share by 0.67 (95% CI 0.10 to 1.24; N = 1,138); the lead placebo is null, 0.17 (95% CI -0.40 to 0.74; N = 896). **Retirement:** a local MP's retirement cost the party 0.86 points more than a non-local MP's (interaction -0.86 (95% CI -1.67 to -0.06; N = 12,494)).
- **Defeat:** no difference. 14.6% of local and 14.5% of non-local incumbents standing again were defeated; adjusted difference 1.0 (95% CI -0.3 to 2.3; N = 11,672) percentage points. **Tenure:** Cox hazard ratio for leaving 1.03 (95% CI 0.96 to 1.10).
- **Through time:** 26% of MPs elected in 2005 were born locally and 43% in 2024, but the bonus since 2010 is 0.29 (95% CI -0.74 to 1.33; N = 2,838). An unplanned interaction test puts it 1.25 points below the 1832 to 2009 bonus (95% CI -2.45 to -0.06): a decline is possible, not established.
- **Robustness:** 0.93 to 1.51 across alternative fixed effects, clustering and definitions of local; 1.07 to 2.05 leaving out each nation or era. Permutation placebo centred on 0.008 (500 draws, none as large as the real estimate); localness to a random other seat 0.27 alone (random seats are sometimes next door) and, in versions added after a first run, -0.11 for seats at least 50 km away and 0.20 (draws -0.14 to 0.63).

These are observational estimates. Birthplace is a proxy for local roots, and all designs start from people who won at least once.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js`, `img/` | The interactive page: every constituency coloured by the share of its MPs born locally, by era, with popups listing each seat's MPs |
| `data/panel.csv` | One row per MP return (31,737): person, seat, party family, distance from birthplace to seat, local flags, own vote share, national party share, tenure, what happened at the next election in the same seat, successor |
| `data/candidates_evermp.csv` | Every candidacy of a person who was an MP at some general election (winners and losers), with distance from birthplace to that seat |
| `data/seats.json` | Compact page data |
| `data/models.json` | Every estimate (coefficient, SE, 95% CI, p, N, clusters) |
| `data/review_checks.json` | Checks added at external review (exploratory): first-time winners, lagged party strength, post-2010 interaction |
| `data/results.json` | Every number quoted in the page, paper, blog, collage and post |
| `code/` | The pipeline (below) |
| `NOTES.md` | Working notes, the analysis plan written before estimation, and the reference checks |
| `release/paper/` | Paper (PDF and LaTeX), figures and `cover_note.md` |
| `release/blog/` | Blog post (WordPress block markup) and figures |
| `release/zenodo/` | Zenodo files and metadata |
| `reddit/` | Collage, its script and the post text |
| `header.png` | Social card (1200 by 630) |

## How to rerun

Inputs are read in place (paths in `code/common.py`): `mp_elections.csv`, `people.csv`, `seats.csv` and `nations.geojson` from Born and bred? (mp-localness), and `candidates.csv`, `contests.csv`, `votes_by_family.csv` from Who won here? (elections-since-1832). Python 3 with pandas, numpy, statsmodels, linearmodels, shapely, matplotlib and Pillow; xelatex for the paper.

```
python3 code/01_build.py      # the panel: MP returns linked to results and to the next election
python3 code/02_models.py     # all models, robustness, placebos (about 20 minutes; add the argument quick for fewer placebo draws)
python3 code/02b_review_checks.py # checks added at external review (exploratory): first-time winners, lagged party strength, post-2010 test
python3 code/03_results.py    # results.json
python3 code/04_figures.py    # figures and header.png
python3 code/05_export.py     # page data
python3 code/06_build_site.py # index.html (and checks every statement made in words)
python3 code/07_paper.py      # paper; DOI=10.5281/zenodo.N to fill the DOI
python3 reddit/collage.py
python3 code/09_readme.py     # README, LICENSE, reddit post, cover note
python3 code/08_release.py    # blog post, Zenodo files
```

## Method in brief

- **Link.** Each MP return is linked to its own candidate row by constituency item, election and surname (forename initial where needed): 99.6% linked. Each MP is followed to the next general election in the same constituency item: stood and won (18,715), stood and lost (3,386), did not stand there (6,562).
- **Local.** Born within 25 km of the seat point (alternatives 10 km, 50 km, same county, log distance, bands). Birthplace known for 56.9% of returns.
- **Models.** Linear models with absorbed fixed effects (linearmodels), SE clustered by constituency; Cox models (statsmodels PHReg) for tenure. University seats and the Speaker excluded.

## Sources and licences

- Hotham, T. (2026) Born and bred? How local are MPs, 1832 to 2024. Zenodo, https://doi.org/10.5281/zenodo.23763155 (Wikidata, CC0; English Wikipedia, CC BY-SA 4.0).
- Hotham, T. (2026) Who won here? Every UK general election since 1832. Zenodo, https://doi.org/10.5281/zenodo.23761425 (UK Parliament and House of Commons Library results, Open Parliament Licence v3.0).
- Base map: OpenFreeMap Positron, OpenStreetMap contributors (ODbL). MapLibre GL JS.

Data in `data/` are released under CC BY-SA 4.0 because some birthplaces come from Wikipedia. Text, figures and the paper: CC BY 4.0. Code: MIT (see `LICENSE`). Contains Parliamentary information licensed under the Open Parliament Licence v3.0.

## Citation

Hotham, T. (2026) Does a local MP get a local bonus? Birthplace and the electoral performance of UK Members of Parliament, 1832 to 2024. Zenodo. https://doi.org/10.5281/zenodo.24092361

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
