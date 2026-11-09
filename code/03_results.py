"""Step 3: data/results.json, the single source of every number quoted anywhere (page, paper, blog, collage, post, README).
Combines data/models.json (step 2) with descriptive counts from data/panel.csv and the elections data."""
import numpy as np
import pandas as pd
from common import *

M = jload(f"{DATA}/models.json")
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
cand = pd.read_csv(f"{ELE}/candidates.csv", dtype=str)
con = pd.read_csv(f"{ELE}/contests.csv", dtype=str)
R = {"M": M}
R["RV"] = jload(f"{DATA}/review_checks.json")      # checks added at external review (02b), exploratory

# ---------- descriptives ----------
Q = P[~P.seat_label.str.contains("University", na=False) & (P.fam != "SPK") & P.fam.notna()]
R["n"] = dict(returns=len(P), people=int(P.person.nunique()), elections=len(ELECTIONS), returns_used=len(Q),
              bp_known=int(P.bp_known.sum()), bp_known_pc=100 * float(P.bp_known.mean()),
              people_bp=int(P[P.bp_known == 1].person.nunique()), linked=int(P.cid.notna().sum()),
              linked_pc=100 * float(P.cid.notna().mean()), seats=int(P.seat.nunique()),
              stood_won=int((P.next_status == "stood_won").sum()), stood_lost=int((P.next_status == "stood_lost").sum()),
              not_standing=int((P.next_status == "not_standing").sum()))
st = jload(f"{SCR}/stats01.json") if os.path.exists(f"{SCR}/stats01.json") else {}
R["n"]["evermp_rows"] = st.get("evermp_rows"); R["n"]["evermp_losers_bp"] = st.get("evermp_losers_bp"); R["n"]["evermp_ambiguous"] = st.get("evermp_ambiguous")
k = Q[Q.local25.notna()]
R["local_share"] = {e: dict(name=nm, pc=100 * float(k[k.era == e].local25.mean()), n=int((k.era == e).sum())) for e, nm, a, b in ERAS}
R["local_share"]["all"] = dict(name="All", pc=100 * float(k.local25.mean()), n=len(k))
byel = k.groupby("election").local25.agg(["mean", "size"]).reindex(ELECTIONS)
R["by_election"] = [dict(election=e, year=int(re.sub(r"\D", "", e)[-4:]), local_pc=100 * float(r["mean"]), n=int(r["size"])) for e, r in byel.iterrows()]

# ---------- how big is 1.3 points? margins of defeat and of victory ----------
c = cand.merge(con[["election", "constituency", "seats", "uncontested"]], on=["election", "constituency"])
c = c[(c.seats == "1") & (c.uncontested == "False")].copy()
c["share"] = pd.to_numeric(c.share, errors="coerce")
c = c.dropna(subset=["share"])
top = c.sort_values("share", ascending=False).groupby(["election", "constituency"]).share.apply(lambda s: list(s)[:2])
top = top[top.map(len) == 2]
marg = top.map(lambda s: s[0] - s[1])
b = M["h1_main"]["b"]
R["margins"] = dict(contests=len(marg), median=float(marg.median()), under_b=100 * float((marg < b).mean()),
                    under_2b=100 * float((marg < 2 * b).mean()))
mod = marg[[int(re.sub(r"\D", "", e)[-4:]) >= 1945 for e, _ in marg.index]]
R["margins"]["post1945_under_2b"] = 100 * float((mod < 2 * b).mean()); R["margins"]["post1945_contests"] = len(mod)
# expected seats per election: contests per election * share under 2b (a seat flips only if the incumbent party's
# candidate was the non-local one AND the margin was within reach; this is an upper bound)
R["margins"]["seats_per_650"] = 650 * R["margins"]["post1945_under_2b"] / 100

# ---------- plain-language derived numbers (T) ----------
H = M
T = {}
T["bonus"] = H["h1_main"]["b"]; T["bonus_lo"] = H["h1_main"]["lo"]; T["bonus_hi"] = H["h1_main"]["hi"]
T["raw_gap"] = H["h1_raw_diff"]["local"] - H["h1_raw_diff"]["nonlocal_"]
T["defeat_pp"] = 100 * H["h2_main"]["b"]; T["defeat_lo"] = 100 * H["h2_main"]["lo"]; T["defeat_hi"] = 100 * H["h2_main"]["hi"]
T["defeat_rate_pc"] = 100 * H["h2_main"]["defeat_rate"]
T["defeat_local_pc"] = 100 * H["h2_raw"]["local"]; T["defeat_nonlocal_pc"] = 100 * H["h2_raw"]["nonlocal_"]
T["swing"] = H["h3_main"]["b"]; T["swing_lo"] = H["h3_main"]["lo"]; T["swing_hi"] = H["h3_main"]["hi"]
T["succ"] = H["h5_main"]["b"]; T["succ_lo"] = H["h5_main"]["lo"]; T["succ_hi"] = H["h5_main"]["hi"]
T["retire"] = H["h6_main"]["b"]; T["retire_lo"] = H["h6_main"]["lo"]; T["retire_hi"] = H["h6_main"]["hi"]
T["cox_hr"] = H["h4"]["cox_any"]["hr"]; T["cox_lo"] = H["h4"]["cox_any"]["lo"]; T["cox_hi"] = H["h4"]["cox_any"]["hi"]
T["terms_local"] = H["h4"]["mean_terms_local"]; T["terms_nonlocal"] = H["h4"]["mean_terms_nonlocal"]
T["era4_bonus"] = H["h1_era_e4"]["b"]; T["era4_lo"] = H["h1_era_e4"]["lo"]; T["era4_hi"] = H["h1_era_e4"]["hi"]
T["era1_bonus"] = H["h1_era_e1"]["b"]; T["era2_bonus"] = H["h1_era_e2"]["b"]; T["era3_bonus"] = H["h1_era_e3"]["b"]
T["local_pc_e3"] = R["local_share"]["e3"]["pc"]; T["local_pc_e4"] = R["local_share"]["e4"]["pc"]
T["local_pc_2024"] = [x for x in R["by_election"] if x["election"] == "2024"][0]["local_pc"]
T["local_pc_2005"] = [x for x in R["by_election"] if x["election"] == "2005"][0]["local_pc"]
T["perm_p"] = H["placebo_perm"]["p_two"]
loo = [H[f"h1_dropnat_{n}"]["b"] for n in ("Eng", "Sco", "Wal", "Ire")] + [H[f"h1_dropera_{e}"]["b"] for e in ("e1", "e2", "e3", "e4")]
T["loo_min"] = min(loo); T["loo_max"] = max(loo)
meas = [H[k]["b"] for k in ("h1_local10", "h1_local50", "h1_county", "h1_p19", "h1_ownpoint", "h1_noabroad", "h1_unknown", "h1_seatparty", "h1_tenure")]
T["meas_min"] = min(meas); T["meas_max"] = max(meas)
T["one_in"] = 100 / max(T["bonus"], 1e-9)
S1 = P[(P.seats == 1) & (P.uncontested == False) & P.share.notna() & P.local25.notna() & P.fam.notna()]
T["sd_share"] = float(S1.groupby(["election", "fam"]).share.std().mean())
T["bonus_sd_ratio"] = 100 * T["bonus"] / T["sd_share"]
T["voters_per_70k"] = 70000 * 0.65 * T["bonus"] / 100
T["logd_double"] = abs(H["h1_logd"]["b"]) * math.log(2)
T["perm_bound"] = 1 / H["placebo_perm"]["draws"]
T["evermp_win_pp"] = 100 * H["cand_evermp_win"]["b"]
T["bp_missing_pc"] = 100 - R["n"]["bp_known_pc"]
R["T"] = T

# ---------- checks on statements made in words ----------
assert H["h1_main"]["lo"] > 0, "main H1 must be positive for the text as written"
assert H["h2_main"]["lo"] < 0 < H["h2_main"]["hi"], "defeat: null as written"
assert H["h4"]["cox_any"]["lo"] < 1 < H["h4"]["cox_any"]["hi"]
assert H["placebo_lead"]["lo"] < 0 < H["placebo_lead"]["hi"]
assert H["h1_era_e4"]["lo"] < 0
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps(T, indent=1)); print(R["margins"])
