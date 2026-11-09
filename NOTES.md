# local-mp-bonus: working notes

Brief: /home/claude/work/new11/BRIEFS.md section 2, plus shared rules (new8, new9, new10 BRIEFS tops; newdata/BRIEF.md).
Format refs: /home/claude/studies/battle-moons, /home/claude/studies/sea-sunsets.
Scratch: /home/claude/scratch/local-mp-bonus (delete at end, by exact path).
Inputs (read in place): /home/claude/src6/mp-localness/data/{mp_elections,people,seats}.csv;
/home/claude/src6/elections-since-1832/data/{candidates,contests}.csv.

## ANALYSIS PLAN (written 2026, before any outcome model was run)

Feasibility facts checked before writing (no outcomes looked at): birthplace (point) known for 18,045 of 31,737 MP
returns; constituency Wikidata items persist across most redistributions when the name persists (e.g. 1979 to 1983:
413 of 635 seat items carry over), so "same seat" means same constituency item, boundaries may change.
Losing candidates have no birthplace unless they were an MP at some general election (then people.csv has one).

### Hypotheses
- H1 (level): an MP born within 25 km of the seat point wins a higher vote share than other MPs of the same party in
  the same seat at other elections, net of the party's national performance. Prediction: beta(local) > 0.
- H2 (re-election): incumbents born locally who stand again in the same seat are less likely to be defeated.
  Prediction: beta(local) < 0 on P(defeat).
- H3 (swing): among incumbents standing again in the same seat for the same party, local ones see a better change in
  their share relative to their party's national change. Prediction: beta > 0.
- H4 (tenure): local MPs serve more consecutive general elections (lower hazard of leaving, and of defeat).
- H5 (succession, within seat): when a seat passes between two MPs of the same party, the party's share relative to
  national swing rises when a non-local is followed by a local and falls in the reverse case.
- H6 (retirement DiD): when a local incumbent retires, the party loses more (relative to national swing) than when a
  non-local incumbent retires, compared with the same MPs' types standing again. Prediction: interaction < 0.

### Units, samples, variables
- Unit: an MP return at a general election (person x election), 1832 to 2024, linked to its contest and candidate row
  (seat item + election + surname). Main share samples: contested single-member contests, party family known.
  Multi-member seats (mostly before 1885) only in the re-election outcome and a robustness check.
- Treatment: local25 = birthplace within 25 km of the seat point (pre-specified main). Alternatives: within 10 km,
  50 km, same county, log(1 + km) continuous, and a three-way split (0 to 25, 25 to 100, over 100 km).
- Outcome H1: candidate's vote share at t (percent) minus the party family's national vote share at t. Election x
  family FE absorb national swing anyway, so the main spec uses raw share with FE.
- Outcome H2: defeated at t+1 (1 if stands again in the same seat and loses), among incumbents standing again in the
  same seat item at the next general election. Standing again found by surname + forename initial in the same contest.
- Outcome H3: share(t+1) minus share(t) for the same incumbent in the same seat item, single-member contested both times.
- Controls: H1: none beyond FE (main); +tenure (number of earlier general-election wins) in alternative. H2/H3:
  lagged share (own share at t), tenure, and FE.
- FE: H1 main = seat FE + election x family FE. H2/H3 main = election x family FE + nation FE (seat FE in an alternative;
  few repeated incumbents per seat make seat FE costly).
- SE: clustered by seat item (main); alternatives clustered by person, and two-way seat and election.
- Estimator: OLS / linear probability (linearmodels PanelOLS or statsmodels with absorbed dummies); logit for H2 as
  alternative; H4 Cox proportional hazards (lifelines or statsmodels PHReg) by person, strata = era of first election,
  covariates local25 and family; discrete-time logit for exit by defeat as alternative.
- Missing birthplace: main analysis on MPs with a placed birthplace; robustness adds unknown as a separate category.

### Robustness, placebo, heterogeneity (all pre-specified)
- Alternative specs: seat x family FE; person-level clustering; two-way clustering; logit for binary outcomes; adding
  tenure; single-member only vs including multi-member (re-election).
- Measurement: 10/50 km, same county, log distance, distance bands; drop birthplaces from Wikipedia text/infobox
  (keep Wikidata P19 only); drop seats whose point is not their own Wikidata coordinate (county seats with rough
  points); drop births abroad.
- Boundaries: drop election pairs that span a general redistribution (1885, 1918, 1950, 1955, Feb 1974, 1983, 1997,
  2005 in Scotland, 2010, 2024).
- Placebo 1 (fake seat): localness to a randomly drawn other seat in the same nation and election (500 draws); the
  effect should be centred on zero. Placebo 2 (lead): for successions, the incoming MP's localness should not predict
  the party's change in the election BEFORE they arrived (t-1 to t). Placebo 3 (permutation): shuffle local25 within
  election x family cells (1,000 draws) for the H1 coefficient to get a randomisation p.
- Leave-one-out: drop each nation in turn; drop each era; drop 2024; drop Ireland before 1922.
- Heterogeneity: era (1832 to 1917, 1918 to 1944, 1945 to 2009, 2010 to 2024), nation (England, Scotland, Wales,
  Ireland/NI), family (CON, LAB, LIB).

### What would count against the hypotheses
- Main H1 coefficient with a 95% CI that includes zero and an upper bound below about 1 point would indicate no
  meaningful local bonus in vote share; a negative estimate would count against it. Same logic for H2 (CI includes zero,
  bound tighter than about 2 points of defeat probability) and H3.
- Any result that appears only in one era or nation, or that is matched by the fake-seat placebo, is not evidence of a
  general local bonus.
- Design caveats stated up front: birthplace is a proxy for roots; all designs condition on having won at least once
  (MPs are selected); the results are associations, causal only under the assumption that, within seat and party,
  candidate birthplace is unrelated to other drivers of vote change.

## Log
- 01_build: 31,609 of 31,737 returns linked to their candidate row (31,394 by surname, 215 single winner). Next election
  in same seat item: stood_won 18,715; stood_lost 3,386; not_standing 6,562; seat gone 2,007; moved and won 415.
  Spot-checked 25 defeated-incumbent links by eye: all right (e.g. Mark Harper, Forest of Dean 2024). Recomputed
  birthplace-to-seat distances match mp-localness to 0.05 km.
- Ever-MP candidacies: 43,910 linked (12,251 losers, 6,931 with birthplace); 4,942 ambiguous name matches dropped.
- Sample rules fixed before outcomes: university seats and the Speaker excluded; party family from the candidate row.

## References verified (WebSearch/WebFetch, 2026; volume, pages and DOI checked on publisher, repository or RePEc pages)
- Arzheimer & Evans 2012, Political Geography 31(5):301-310, doi 10.1016/j.polgeo.2012.04.006
- Arzheimer & Evans 2014, Research & Politics 1(2), doi 10.1177/2053168014538769
- Evans, Arzheimer, Campbell & Cowley 2017, Political Geography 59:61-71, doi 10.1016/j.polgeo.2017.02.009
- Campbell & Cowley 2014, Political Studies 62(4):745-765, doi 10.1111/1467-9248.12048
- Campbell, Cowley, Vivyan & Wagner 2019, Journal of Politics 81(3):937-951, doi 10.1086/703131
- Childs & Cowley 2011, Political Studies 59(1):1-19, doi 10.1111/j.1467-9248.2010.00846.x
- Collignon & Sajuria 2018, Electoral Studies 56:170-178, doi 10.1016/j.electstud.2018.07.003
- Eggers & Spirling 2017, Journal of Politics 79(3):903-920, doi 10.1086/690617
- Eggers & Spirling 2014, Legislative Studies Quarterly 39(4):593-620, doi 10.1111/lsq.12059
- Eggers, Fowler, Hainmueller, Hall & Snyder 2015, AJPS 59(1):259-274 (RePEc)
- Tavits 2010, Party Politics 16(2):215-235, doi 10.1177/1354068809341053
- Shugart, Valdini & Suominen 2005, AJPS 49(2):437-449, doi 10.1111/j.0092-5853.2005.00133.x
- Cain, Ferejohn & Fiorina 1987, The Personal Vote, Harvard UP (doi 10.4159/harvard.9780674493285)
- Cain, Ferejohn & Fiorina 1984, APSR 78(1):110-125 (RePEc)
- Key 1949, Southern Politics in State and Nation, Knopf (APSR review record)
- Gimpel, Karnes, McTague & Pearson-Merkowitz 2008, Political Geography 27(2):231-252, doi 10.1016/j.polgeo.2007.10.005
- Górecki & Marsh 2012, EJPR 51(5):563-582, doi 10.1111/j.1475-6765.2011.02008.x
- Fiva & Halse 2016, Journal of Public Economics 143:15-26, doi 10.1016/j.jpubeco.2016.08.002
- Lewis-Beck & Rice 1983, AJPS 27(3):548-556, doi 10.2307/2110984
- Panagopoulos, Leighley & Hamel 2017, Political Behavior 39(4):865-882, doi 10.1007/s11109-016-9383-3
- Meredith 2013, APSR 107(4):742-765 (RePEc)
- Cameron & Miller 2015, Journal of Human Resources 50(2):317-372 (RePEc)
- Cox DR 1972, JRSS B 34(2):187-220
- Gelman & King 1990, AJPS 34:1142-1164
- Lee 2008, Journal of Econometrics 142(2):675-697 (RePEc)
- Vivyan & Wagner 2016, EJPR 55(1):81-99, doi 10.1111/1475-6765.12119
- Cox GW 1987, The Efficient Secret, Cambridge UP
- Norris & Lovenduski 1995, Political Recruitment, Cambridge UP
- Rush 2001, The Role of the Member of Parliament since 1868, Oxford UP
- Pattie, Hartman & Johnston 2017, BJPIR 19(4):824-841, doi 10.1177/1369148117718710
- Johnston & Pattie 2006, Putting Voters in Their Place, Oxford UP
- Johnston 1974, Annals AAG 64(3):418-429, doi 10.1111/j.1467-8306.1974.tb00990.x
- Gaines 1998, LSQ 23(2):167-195, doi 10.2307/440279
- Kellermann 2016, BJPIR 18(1):90-106, doi 10.1111/1467-856X.12075
- Middleton 2019, Politics 39(2):137-153, doi 10.1177/0263395718754717
- Harfst et al. 2024, JEPOP 34(3):387-408, doi 10.1080/17457289.2023.2189257
- Hanretty, Lauderdale & Vivyan 2017, LSQ 42(2):235-267, doi 10.1111/lsq.12148
- Willumsen 2019, West European Politics, doi 10.1080/01402382.2018.1530887 (volume/pages not verified: cite without)
- Vrandečić & Krötzsch 2014, CACM 57(10):78-85
- Hotham 2026a (mp-localness, doi 10.5281/zenodo.23763155), Hotham 2026b (elections-since-1832, doi 10.5281/zenodo.23761425): from their READMEs
Dropped (could not verify within the search budget): Wood & Norton 1992; Bowler, Donovan & Snipp 1993; Jankowski 2016; Cowley 2013; Moore 1976; Smith 2013.
- 02_models: first full run crashed at the end (period "2024" alone is absorbed by seat FE); periods changed to end
  "2010 to 2024" (exploratory figure only). Fake-seat far-seat candidates precomputed for speed; 300 fake-seat draws,
  500 permutations.
- Deviation from plan, labelled in the paper: the unconditional fake-seat placebo has a small positive mean (random
  seats are sometimes near the MP's own seat), so a conditional version (with real localness) and a 50 km+ version were
  added after seeing the first quick run. Periods, defeat without lagged share, margin arithmetic: exploratory.
- Reference search budget ran out before journal word limits could be checked; cover_note says so.

## External review (journal referee and fact-check), 2026

Reproduction: re-ran 01 to 09 from the raw inputs (scratch in /home/claude/scratch/review-local-mp-bonus, deleted
afterwards). panel.csv, candidates_evermp.csv, seats.json, models.json and results.json reproduce exactly (bit for
bit for the CSVs; every float in models.json identical; results.json identical apart from the new RV block).
Every number in the paper, blog, page, README, Zenodo description, Reddit post and collage is generated from
results.json; checked the rendered outputs against it.

Errors fixed:
- Identification misdescribed. The main H1 model has seat FE + election x party FE, not seat x party FE, so it compares
  MPs elected for the same seat (possibly of different parties), each net of their party's national result. Paper,
  blog, page, README, Reddit post, collage and figure titles said "other MPs of the same party in the same seat".
  Reworded everywhere; the pre-specified seat x party variant (1.32, CI 0.70 to 1.95) is now reported next to the
  main estimate as the same-party comparison.
- "Pre-registered" (abstract, appendix heading, cover note): the plan was written in NOTES.md before estimation but
  not lodged with a registry. Now "pre-specified", with that stated.
- Distance gradient called "monotone" and "a smaller [advantage] between 25 and 100 km": the 25 to 100 km band is
  -0.18 (CI -0.70 to 0.33), i.e. no advantage. Corrected.
- Fake-seat placebo: blog said being born near a random seat "adds next to nothing"; the pre-specified unconditional
  version is +0.27 (draws -0.06 to 0.70). Blog, page and README now give that number, explain it (random seats
  sometimes adjacent) and label the 50 km and conditional versions as added after a first run.
- Defeat effect in the abstract/Zenodo was "+0.01 in probability, CI -0.00 to +0.02"; now percentage points
  (+1.0, CI -0.3 to +2.3).
- "Never saved local MPs from defeat" / "has never made local MPs less likely to lose" (blog standfirst, excerpt):
  overclaim; now "has not made local MPs any less likely to lose".
- Causal phrasing "one voter in 78 seems to be won over" (page, blog) and "a local MP gains roughly 586 votes":
  recast as an association ("one extra vote in every 78 cast", "corresponds to").
- Robustness table labels printed "$times$" (tex() stripped backslashes); fixed in 07_paper.py. N in maths mode
  printed "3, 989"; fixed.
- Citation: Hotham 2026b title is "Who won here? Every UK general election since 1832 on one map".
- Abstract trimmed to about 250 words.

Checks added at review (code/02b_review_checks.py, data/review_checks.json; labelled exploratory everywhere):
- First-time winners only (no accumulated incumbency): 1.31 (0.66 to 1.95), N 3,989.
- Seat x party FE plus tenure: 1.45 (0.83 to 2.07).
- Balance: party's lagged seat share (relative to national) does not predict whether a new MP is local
  (0.000 per point, CI -0.002 to 0.002; N 3,259).
- Controlling lagged party strength: 1.18 (0.55 to 1.81) first-time winners; 1.12 (0.69 to 1.55) all returns with tenure.
- Post-2010 interaction: -1.25 (-2.45 to -0.06), p 0.04. Reported as weak evidence of a decline: unplanned, one of many
  tests, interval close to zero. Text says "possible, not established".

References: all 39 checked by WebSearch/WebFetch (publisher, repository, RePEc or citing reference lists). Authors,
years, titles, volumes, issues, pages and DOIs as cited are correct. Willumsen (2019) WEP: title, author and DOI
verified, volume/pages not found, left without (as before). Norris and Lovenduski is sometimes catalogued 1994; CUP
edition is 1995, kept.

Journals (cover_note.md rewritten from the author instructions): Political Studies 9,000 words incl. notes excl.
references, no fees; BJPIR 8,000 to 10,000 excl. references, no fees; Parliamentary Affairs 8,000 max, no standard
charge listed; Electoral Studies hybrid, guide not retrievable, word limit unconfirmed. Paper text about 8,200 words
before references (including tables): fits PS and BJPIR with the appendix moved to a supplement.

House rules: map has full-screen button, layers panel, site-nav.js, dot radius floor 3 px, no horizontal scroll at
390 px, 0 console errors (qa/ screenshots re-taken and viewed). Byline "Dr Tristan Hotham · Independent researcher ·
2026"; no DSIT/DCMS/civil service; no dashes in the blog; AI statement exact. Paper title block says "Tristan
Hotham" (as in the reviewed siblings). Collage light, labels on paper, legend complete.

What a referee would still ask for:
- Selection on winning: H1 uses winners only; losing candidates' birthplaces are known only for ever-MPs. A
  candidate-level design with complete birthplaces for all candidates (at least since 1945) is the real fix.
- Within-seat comparisons across parties under seat FE: the seat x party version is close, but identification rests on
  only 662 seats with both local and non-local MPs; show the distribution of within-seat switches and weight.
- Time-varying local party strength beyond the lagged share (local election results, membership).
- Boundary changes: constituency items persist across redistributions; H1 has no boundary-stable version.
- Birthplace as a proxy for roots (no residence/schooling/local office); a validation on a recent subsample would help.
- Multiple testing across six hypotheses and many subgroups (e.g. a Holm or sharpened q-value table).
- Heterogeneity by margin (does the bonus matter in marginal seats where it could change outcomes?).
