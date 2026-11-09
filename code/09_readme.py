"""Step 9: README.md, LICENSE, reddit/post.md and release/paper/cover_note.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]; N = R["n"]
ci = lambda m, s=1, d=2: f"{s*m['b']:.{d}f} (95% CI {s*m['lo']:.{d}f} to {s*m['hi']:.{d}f}; N = {m['n']:,})"
readme = f"""# Does a local MP get a local bonus?

Every MP returned at a UK general election from 1832 to 2024 ({N['returns']:,} returns of {N['people']:,} people), linked to their birthplace and to constituency results, to test whether MPs born near their seat win more votes, swing better, lose less often and serve longer. Six designs, written down with their checks before any outcome model was run (see `NOTES.md`).

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24092361}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/local-mp-bonus/}}
Code and data: {REPO}

## Headline results

- **Vote share (main, pre-specified):** an MP born within 25 km of the seat won {ci(M['h1_main'])} percentage points more of the vote than other MPs elected for the same seat, net of their party's national performance (seat and election by party fixed effects; SE clustered by constituency). With seat by party fixed effects (same party, same seat): {ci(M['h1_seatparty'])}. Among first-time winners only (added at review): {ci(R['RV']['firstwin'])}.
- **Re-election:** local incumbents gained {ci(M['h3_main'])} points more at re-election. **Succession:** each step in localness from predecessor to successor of the same party raised the party's relative share by {ci(M['h5_main'])}; the lead placebo is null, {ci(M['placebo_lead'])}. **Retirement:** a local MP's retirement cost the party {abs(T['retire']):.2f} points more than a non-local MP's (interaction {ci(M['h6_main'])}).
- **Defeat:** no difference. {T['defeat_local_pc']:.1f}% of local and {T['defeat_nonlocal_pc']:.1f}% of non-local incumbents standing again were defeated; adjusted difference {ci(M['h2_main'], 100, 1)} percentage points. **Tenure:** Cox hazard ratio for leaving {M['h4']['cox_any']['hr']:.2f} (95% CI {M['h4']['cox_any']['lo']:.2f} to {M['h4']['cox_any']['hi']:.2f}).
- **Through time:** {T['local_pc_2005']:.0f}% of MPs elected in 2005 were born locally and {T['local_pc_2024']:.0f}% in 2024, but the bonus since 2010 is {ci(M['h1_era_e4'])}. An unplanned interaction test puts it {abs(R['RV']['post2010_diff']['terms']['loc_x_post']['b']):.2f} points below the 1832 to 2009 bonus (95% CI {R['RV']['post2010_diff']['terms']['loc_x_post']['lo']:.2f} to {R['RV']['post2010_diff']['terms']['loc_x_post']['hi']:.2f}): a decline is possible, not established.
- **Robustness:** {T['meas_min']:.2f} to {T['meas_max']:.2f} across alternative fixed effects, clustering and definitions of local; {T['loo_min']:.2f} to {T['loo_max']:.2f} leaving out each nation or era. Permutation placebo centred on {M['placebo_perm']['mean']:.3f} ({M['placebo_perm']['draws']} draws, none as large as the real estimate); localness to a random other seat {M['placebo_fakeseat']['mean']:.2f} alone (random seats are sometimes next door) and, in versions added after a first run, {M['placebo_fakeseat_far']['mean']:.2f} for seats at least 50 km away and {M['placebo_fakeseat_cond']['mean']:.2f} (draws {M['placebo_fakeseat_cond']['lo']:.2f} to {M['placebo_fakeseat_cond']['hi']:.2f}).

These are observational estimates. Birthplace is a proxy for local roots, and all designs start from people who won at least once.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js`, `img/` | The interactive page: every constituency coloured by the share of its MPs born locally, by era, with popups listing each seat's MPs |
| `data/panel.csv` | One row per MP return ({N['returns']:,}): person, seat, party family, distance from birthplace to seat, local flags, own vote share, national party share, tenure, what happened at the next election in the same seat, successor |
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

- **Link.** Each MP return is linked to its own candidate row by constituency item, election and surname (forename initial where needed): {N['linked_pc']:.1f}% linked. Each MP is followed to the next general election in the same constituency item: stood and won ({N['stood_won']:,}), stood and lost ({N['stood_lost']:,}), did not stand there ({N['not_standing']:,}).
- **Local.** Born within 25 km of the seat point (alternatives 10 km, 50 km, same county, log distance, bands). Birthplace known for {N['bp_known_pc']:.1f}% of returns.
- **Models.** Linear models with absorbed fixed effects (linearmodels), SE clustered by constituency; Cox models (statsmodels PHReg) for tenure. University seats and the Speaker excluded.

## Sources and licences

- Hotham, T. (2026) Born and bred? How local are MPs, 1832 to 2024. Zenodo, https://doi.org/10.5281/zenodo.23763155 (Wikidata, CC0; English Wikipedia, CC BY-SA 4.0).
- Hotham, T. (2026) Who won here? Every UK general election since 1832. Zenodo, https://doi.org/10.5281/zenodo.23761425 (UK Parliament and House of Commons Library results, Open Parliament Licence v3.0).
- Base map: OpenFreeMap Positron, OpenStreetMap contributors (ODbL). MapLibre GL JS.

Data in `data/` are released under CC BY-SA 4.0 because some birthplaces come from Wikipedia. Text, figures and the paper: CC BY 4.0. Code: MIT (see `LICENSE`). Contains Parliamentary information licensed under the Open Parliament Licence v3.0.

## Citation

Hotham, T. (2026) Does a local MP get a local bonus? Birthplace and the electoral performance of UK Members of Parliament, 1832 to 2024. Zenodo. {{https://doi.org/10.5281/zenodo.24092361}}

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/battle-moons/LICENSE", encoding="utf-8").read().split("Text, figures")[0]
lic += ("Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/\n"
        "Data (data/): Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0), because some birthplaces are derived from English Wikipedia. "
        "Contains Parliamentary information licensed under the Open Parliament Licence v3.0.\n")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""**Title:** [OC] Do MPs born near their seat win more votes? Across {N['returns']:,} MP returns since 1832: about {T['bonus']:.1f} points more of the vote, but they lose just as often

**Body:**

Every MP returned at a UK general election from 1832 to 2024, where they were born, and how they did. The comparison is within the same seat, with each MP measured against how their party did nationally.

- MPs born within 25 km of their seat won {T['bonus']:.1f} percentage points more of the vote (95% CI {T['bonus_lo']:.1f} to {T['bonus_hi']:.1f}) than other MPs elected for the same seat (same party only: {M['h1_seatparty']['b']:.1f} points).
- But local MPs who stood again were defeated just as often: {T['defeat_local_pc']:.1f}% against {T['defeat_nonlocal_pc']:.1f}%. Most seats are won by far more than a point.
- When a local MP retired, their party lost about {abs(T['retire']):.1f} points more than when an MP from elsewhere stood down.
- {T['local_pc_2024']:.0f}% of MPs elected in 2024 were born locally, against {T['local_pc_2005']:.0f}% in 2005, but the bonus since 2010 is only {T['era4_bonus']:.1f} points and could be zero.
- Birthplace is a rough stand in for roots, and this is observational, so read it as an association.

Interactive map (every seat, every era, tap for its MPs): {PAGE}

**Source comment:**

Data: my datasets Born and bred? (Wikidata, Wikipedia birthplaces) and Who won here? (UK Parliament and House of Commons Library results). Tools: Python (pandas, linearmodels, statsmodels, matplotlib), MapLibre. Paper, data and code: {REPO}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)

import subprocess as _sp
_txt = _sp.run(["pdftotext", os.path.join(ROOT, "release", "paper", "Hotham_Local_MP_Bonus.pdf"), "-"], capture_output=True, text=True).stdout
WORDS_MAIN = int(round(len(_txt.split("\nReferences\n")[0].split()), -2))
cover = f"""# Cover note: Does a Local MP Get a Local Bonus?

## Suggested journals

Checked against the journals' author instructions in 2026 (Electoral Studies' guide could not be retrieved; confirm before submitting). None charges authors for standard (subscription) publication; open access is optional and paid.

1. **Political Studies** (Sage, Political Studies Association). Original articles "no more than 9,000 words in length including all notes but excluding references"; "no fees payable to submit or publish". It published Campbell and Cowley (2014) and Childs and Cowley (2011) on local candidates. Fits: the main text is about {WORDS_MAIN:,} words before the references (including tables); move the appendix tables to an online supplement.
2. **British Journal of Politics and International Relations** (Sage, Political Studies Association). Original research articles "between 8-10,000 words, excluding the list of references"; no fees for standard publication. Fits as it stands, with the appendix as a supplement.
3. **Electoral Studies** (Elsevier). The natural home for long-run, data-heavy studies of elections and candidate effects (Collignon and Sajuria 2018 appeared there). A hybrid subscription journal: no charge on the subscription route, an APC only for optional open access. Its word limit could not be confirmed in this session; check the current guide for authors.

Also possible: **Parliamentary Affairs** (Oxford University Press; original articles "Maximum words: 8,000", no charge listed for the standard licence). It would need cutting: lead with H1, H2 and the time trend and move H4 to H6 to a supplement.

## Summary of the contribution (for a cover letter)

Voters say they prefer local candidates, and British parties have selected far more of them since 2010, but whether local roots win real votes over the long run has not been tested. This paper links every MP returned at a UK general election from 1832 to 2024 ({N['returns']:,} returns) to their birthplace and to constituency results, and tests pre-specified hypotheses with six designs that compare MPs within the same constituency. MPs born within 25 km of their seat win about {T['bonus']:.1f} percentage points more of the vote than other MPs elected for the same seat, net of party performance; the estimate is the same among first-time winners and within the same party and seat, survives alternative definitions of local and placebo tests, and is matched in sign by re-election, succession and retirement designs. Yet local MPs are no less likely to be defeated and serve no longer, because most margins dwarf the bonus, and the bonus has not grown as localness has risen. The paper reconciles experimental evidence of a preference for local candidates with the modest weight of roots at the ballot box.
"""
open(os.path.join(ROOT, "release", "paper", "cover_note.md"), "w", encoding="utf-8").write(cover)
for fn, txt in (("README.md", readme), ("post.md", post), ("cover_note.md", cover)):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in txt.replace("```", "").replace("|---|---|", ""), (fn, bad)
print("README, LICENSE, post.md, cover_note.md written")
