"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds booktabs tables, compiles with xelatex.
Output: release/paper/Hotham_Local_MP_Bonus.pdf and .tex beside the f_*.png figures.
The DOI stays the placeholder https://doi.org/10.5281/zenodo.24092361 unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Local_MP_Bonus"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    v = float(v) if f not in ("raw",) else v
    if f == "int": return f"{int(round(v)):,}".replace(",", "{,}")     # {,} avoids a space after the comma in maths
    if f == "f0": return f"{v:.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "s1": return f"{v:+.1f}"
    if f == "s2": return f"{v:+.2f}"
    if f == "abs1": return f"{abs(v):.1f}"
    if f == "p": return pval(v)
    return tex(str(v))


def pv(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def row(lab, m, scale=1.0, d=2):
    lab = lab if "$" in lab else tex(lab)          # labels with maths are already LaTeX (review fix: tex() stripped \\times)
    if m is None: return f"{lab} & \\multicolumn{{4}}{{c}}{{(too few cases)}}\\\\\n"
    return (f"{lab} & {scale*m['b']:.{d}f} & [{scale*m['lo']:.{d}f}, {scale*m['hi']:.{d}f}] & {pv(m['p'])} & {m['n']:,}\\\\\n")


def table(cap, label, body, head="Specification & Estimate & 95\\% CI & $p$ & $N$", cols="p{7.4cm}rcrr", note=None):
    n = f"\\par\\vspace{{2pt}}\\parbox{{\\linewidth}}{{\\footnotesize {note}}}" if note else ""
    return (f"\\begin{{table}}[tbp]\\centering\\small\\caption{{{cap}}}\\label{{{label}}}\n\\begin{{tabular}}{{{cols}}}\\toprule {head}\\\\\\midrule\n"
            + body + f"\\bottomrule\\end{{tabular}}{n}\\end{{table}}")


SE = "Standard errors clustered by constituency item unless stated."
# descriptive table
d = (f"MP returns, 1832 to 2024 & {R['n']['returns']:,}\\\\\nPeople & {R['n']['people']:,}\\\\\n"
     f"Returns with a birthplace point & {R['n']['bp_known']:,} ({R['n']['bp_known_pc']:.1f}\\%)\\\\\n"
     f"Returns linked to their own result & {R['n']['linked']:,} ({R['n']['linked_pc']:.1f}\\%)\\\\\n\\midrule\n"
     + "".join(f"Born within 25 km, {R['local_share'][k]['name']} & {R['local_share'][k]['pc']:.1f}\\% of {R['local_share'][k]['n']:,}\\\\\n" for k, *_ in ERAS)
     + "\\midrule\n"
     + f"H1 sample: contested single-member returns, birthplace known & {M['samples']['S1']:,}\\\\\n"
     + f"H2 sample: incumbents standing again, contested & {M['samples']['S2']:,}\\\\\n"
     + f"H3 sample: single-member, contested both times, same party & {M['samples']['S3']:,}\\\\\n"
     + f"H4: first unbroken spells of MPs & {M['samples']['spells']:,}\\\\\n"
     + f"H5: hand-overs between MPs of the same party & {M['samples']['S5']:,}\\\\\n"
     + f"H6: incumbents with the party standing again & {M['samples']['S6']:,}\\\\\n")
TD = table("Data and analysis samples.", "tab:desc", d, head="Item & Value", cols="p{10cm}r")

b = (row("H1 Vote share (seat FE, election $\\times$ party FE)", M["h1_main"]) +
     row("H2 Defeated at next election (LPM, percentage points)", M["h2_main"], 100, 1) +
     row("H3 Change in own share at re-election", M["h3_main"]) +
     f"H4 Leaving Parliament, Cox hazard ratio & {M['h4']['cox_any']['hr']:.2f} & [{M['h4']['cox_any']['lo']:.2f}, {M['h4']['cox_any']['hi']:.2f}] & {pv(M['h4']['cox_any']['p'])} & {M['h4']['cox_any']['n']:,}\\\\\n" +
     row("H5 Party share change per step of successor localness", M["h5_main"]) +
     row("H6 Local $\\times$ retires: party share change", M["h6_main"]) +
     row("Lead placebo for H5", M["placebo_lead"]))
TM = table("Pre-specified main estimates. Vote shares in percentage points.", "tab:main", b,
           note=SE + " H2 and H3 control for previous share and tenure with election $\\times$ party and nation FE; H4 is stratified by era of first election with party family and nation; H5 and H6 control for previous share with election $\\times$ party and nation FE.")

hb = ""
for k, nm, *_ in ERAS:
    hb += f"{nm} & {M[f'h1_era_{k}']['b']:.2f} [{M[f'h1_era_{k}']['lo']:.2f}, {M[f'h1_era_{k}']['hi']:.2f}] & {100*M[f'h2_era_{k}']['b']:.1f} [{100*M[f'h2_era_{k}']['lo']:.1f}, {100*M[f'h2_era_{k}']['hi']:.1f}] & {M[f'h3_era_{k}']['b']:.2f} [{M[f'h3_era_{k}']['lo']:.2f}, {M[f'h3_era_{k}']['hi']:.2f}]\\\\\n"
hb += "\\midrule\n"
for n in ("England", "Scotland", "Wales", "Ireland/NI"):
    a, c = M[f"h1_nat_{n[:3]}"], M[f"h2_nat_{n[:3]}"]
    hb += f"{n} & {a['b']:.2f} [{a['lo']:.2f}, {a['hi']:.2f}] & {100*c['b']:.1f} [{100*c['lo']:.1f}, {100*c['hi']:.1f}] & \\\\\n"
hb += "\\midrule\n"
for f in ("CON", "LAB", "LIB"):
    a, c, e = M[f"h1_fam_{f}"], M[f"h2_fam_{f}"], M[f"h3_fam_{f}"]
    hb += f"{tex(FAMNAME[f])} & {a['b']:.2f} [{a['lo']:.2f}, {a['hi']:.2f}] & {100*c['b']:.1f} [{100*c['lo']:.1f}, {100*c['hi']:.1f}] & {e['b']:.2f} [{e['lo']:.2f}, {e['hi']:.2f}]\\\\\n"
TH = table("Heterogeneity: separate regressions by era, nation and party family (estimate and 95\\% CI).", "tab:het", hb,
           head="Group & H1 share & H2 defeat (pp) & H3 change", cols="lccc", note=SE + " Ns in the replication files (data/models.json).")

rk = [("h1_main", "Main"), ("h1_rel_nat", "Outcome: share minus party national share"), ("h1_noseatfe", "No seat FE (nation FE)"),
      ("h1_seatparty", "Seat $\\times$ party FE"), ("h1_tenure", "Adding tenure"), ("h1_cl_person", "SE clustered by MP"),
      ("h1_cl_twoway", "SE two-way: seat and election"), ("h1_local10", "Local = within 10 km"), ("h1_local50", "Local = within 50 km"),
      ("h1_county", "Local = born in seat's county"), ("h1_logd", "log(1 + km), per unit"), ("h1_p19", "Wikidata birthplaces only"),
      ("h1_ownpoint", "Seats with own coordinates only"), ("h1_noabroad", "Excluding MPs born abroad"),
      ("h1_unknown", "Unknown birthplace kept as a category"), ("h1_drop2024", "Without 2024"), ("h1_dropire", "Without Ireland before 1922")]
rb = "".join(row(l, M[k]) for k, l in rk)
rb += "".join(row(M[f"h1_dropnat_{n}"]["label"], M[f"h1_dropnat_{n}"]) for n in ("Eng", "Sco", "Wal", "Ire"))
rb += "".join(row(M[f"h1_dropera_{e}"]["label"], M[f"h1_dropera_{e}"]) for e in ("e1", "e2", "e3", "e4"))
bt = M["h1_bands"]["terms"]
rb += f"Bands: 0 to 25 km (ref. over 100) & {bt['b0_25']['b']:.2f} & [{bt['b0_25']['lo']:.2f}, {bt['b0_25']['hi']:.2f}] & {pv(bt['b0_25']['p'])} & {M['h1_bands']['n']:,}\\\\\n"
rb += f"Bands: 25 to 100 km & {bt['b25_100']['b']:.2f} & [{bt['b25_100']['lo']:.2f}, {bt['b25_100']['hi']:.2f}] & {pv(bt['b25_100']['p'])} & \\\\\n"
rb += row("Candidacies of ever-MPs, winners and losers", M["cand_evermp"])
RV = R["RV"]
rb += "\\midrule\n\\multicolumn{5}{l}{\\emph{Added at review (exploratory)}}\\\\\n"
rb += "".join(row(l, RV[k]) for k, l in (("firstwin", "First-time winners only"), ("seatparty_tenure", "Seat $\\times$ party FE, adding tenure"),
                                          ("firstwin_lag", "First-time winners, lagged party seat strength"), ("main_lag", "All returns, lagged party seat strength and tenure")))
pt = RV["post2010_diff"]["terms"]["loc_x_post"]
rb += f"Local $\\times$ 2010 to 2024 (difference from 1832 to 2009) & {pt['b']:.2f} & [{pt['lo']:.2f}, {pt['hi']:.2f}] & {pv(pt['p'])} & {RV['post2010_diff']['n']:,}\\\\\n"
TR = table("Robustness of the level bonus (H1). Percentage points of vote share.", "tab:rob", rb, note=SE)

h2 = "".join(row(M[k]["label"], M[k], 100, 1) for k in ("h2_main", "h2_single", "h2_seatfe", "h2_cl_person", "h2_county", "h2_local10", "h2_local50", "h2_noredist", "h2_p19", "x_h2_nolag"))
h2 += f"Logit, average marginal effect & {100*M['h2_logit']['b']:.1f} & [{100*M['h2_logit']['lo']:.1f}, {100*M['h2_logit']['hi']:.1f}] & {pv(M['h2_logit']['p'])} & {M['h2_logit']['n']:,}\\\\\n"
h2 += row("log(1 + km), per unit", M["h2_logd"], 100, 2)
T2 = table("Defeat of incumbents standing again (H2): alternative specifications, percentage points of probability.", "tab:h2", h2, note=SE + " The last-but-one row omits the previous share (exploratory).")
h3 = "".join(row("H3: " + M[k]["label"], M[k]) for k in ("h3_main", "h3_seatfe", "h3_noredist", "h3_county", "h3_logd", "h3_first"))
h3 += "\\midrule\n" + "".join(row("H5: " + M[k]["label"], M[k]) for k in ("h5_main", "h5_evermp"))
tc = M["h5_cells"]["terms"]
h3 += f"H5: non-local to local (ref. no change) & {tc['to_local']['b']:.2f} & [{tc['to_local']['lo']:.2f}, {tc['to_local']['hi']:.2f}] & {pv(tc['to_local']['p'])} & {M['h5_cells']['n']:,}\\\\\n"
h3 += f"H5: local to non-local & {tc['to_nonlocal']['b']:.2f} & [{tc['to_nonlocal']['lo']:.2f}, {tc['to_nonlocal']['hi']:.2f}] & {pv(tc['to_nonlocal']['p'])} & \\\\\n"
h3 += row("H5 lead placebo", M["placebo_lead"]) + "\\midrule\n"
h3 += "".join(row("H6: " + M[k]["label"], M[k]) for k in ("h6_main", "h6_noredist", "h6_seatfe"))
h3 += "".join(row(f"H6: {M[f'h6_era_{k}']['label']}", M[f"h6_era_{k}"]) for k, *_ in ERAS)
T36 = table("Within-seat designs (H3, H5, H6): alternative specifications. Percentage points of vote share.", "tab:h36", h3, note=SE + f" H5 hand-overs by type (predecessor to successor, 1 = local): " + ", ".join(f"{k.replace('to', ' to ')}: {v}" for k, v in M["h5_counts"].items()) + ".")
H4 = M["h4"]
sv = "".join(f"Cox, leaving: {tex(H4[f'cox_era_{k}']['label'])} & {H4[f'cox_era_{k}']['hr']:.2f} & [{H4[f'cox_era_{k}']['lo']:.2f}, {H4[f'cox_era_{k}']['hi']:.2f}] & {pv(H4[f'cox_era_{k}']['p'])} & {H4[f'cox_era_{k}']['n']:,}\\\\\n" for k, *_ in ERAS)
sv = (f"Cox, leaving for any reason & {H4['cox_any']['hr']:.2f} & [{H4['cox_any']['lo']:.2f}, {H4['cox_any']['hi']:.2f}] & {pv(H4['cox_any']['p'])} & {H4['cox_any']['n']:,}\\\\\n"
      f"Cox, leaving by defeat & {H4['cox_defeat']['hr']:.2f} & [{H4['cox_defeat']['lo']:.2f}, {H4['cox_defeat']['hi']:.2f}] & {pv(H4['cox_defeat']['p'])} & {H4['cox_defeat']['n']:,}\\\\\n" + sv
      + row("LPM: not returned at next election (pp; SE by MP)", H4["dt_exit"], 100, 1) + row("LPM: did not stand again in the seat (pp; SE by MP)", H4["dt_retire"], 100, 1))
TS = table("Tenure (H4): hazard ratios for local MPs (Cox) and discrete-time linear probability models.", "tab:surv", sv,
           note="Cox models on first unbroken spells of consecutive general-election wins, stratified by era of first election, with party family and nation; ties by Efron's method.")
AD = (f"MP returns come from \\citet{{hotham2026mpl}} ({R['n']['returns']:,} rows). Each was linked to its own candidate row in \\citet{{hotham2026ele}} by Wikidata constituency item and election, then by surname (all surname tokens contained in the MP's name, ignoring titles), then by forename initial; where the contest had a single winner that winner was used. "
      f"{R['n']['linked']:,} returns linked. For the next general election in the same constituency item, the MP counts as standing and winning if returned there, as standing and losing if a losing candidate matches surname and forename initial, as moving if returned elsewhere, and otherwise as not standing. "
      f"Ever-MP candidacies: a candidacy is linked to a person when the surname and forename initial match exactly one person who was an MP at a general election within 30 years; {R['n']['evermp_ambiguous']:,} ambiguous candidacies were dropped. Recomputed birthplace-to-seat distances match the source to within 0.05 km. "
      "Party family is taken from the candidate row. The national share of each party family at each election is from the same source. University seats and the Speaker are excluded from all models. "
      "Redistribution elections (election pairs whose second election used new boundaries): 1868, 1885, 1918, 1950, 1955, February 1974, 1983, 1997, 2005, 2010 and 2024.")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_DESC", TD), ("TABLE_MAIN", TM), ("TABLE_HET", TH), ("TABLE_ROB", TR), ("TABLE_H2", T2), ("TABLE_H36", T36), ("TABLE_SURV", TS), ("APPENDIX_DATA", AD)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24092361", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, [l for l in t.splitlines() if "{{" in l or "--" in l][:5]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("References")[0]
print("paper", r.returncode, len(txt.split()), "words in all;", len(body.split()), "before references;", [l for l in pages.splitlines() if l.startswith("Pages")])
