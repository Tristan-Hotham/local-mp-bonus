"""Step 2b: checks added at external review (not in the pre-specified plan; labelled exploratory everywhere).

1. Incumbency: the level bonus among first-time winners only (no accumulated incumbency), and with seat x party FE
   plus tenure.
2. Selection on party strength: among first-time winners, does the party's own share in the seat at the previous
   general election (relative to its national share) predict whether the new MP is local (a balance test)? And does
   the H1 bonus survive controlling for that lagged party strength?
3. The post-2010 decline: a direct test of whether the bonus in 2010 to 2024 differs from 1832 to 2009
   (local x post-2010 interaction, same fixed effects).
Writes data/review_checks.json. Uses the fe() helper and sample rules of 02_models.py (copied, not imported, so that
02_models.py is not re-run).
"""
import warnings
import numpy as np
import pandas as pd
from linearmodels.iv.absorbing import AbsorbingLS
import statsmodels.api as sm
from common import *

warnings.filterwarnings("ignore")
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
P = P[~P.seat_label.str.contains("University", na=False) & (P.fam != "SPK") & P.fam.notna()].copy()
P["ef"] = P.election + "_" + P.fam
P["sf"] = P.seat + "_" + P.fam
P["single"] = P.seats.eq(1)
P["contested"] = P.uncontested.eq(False) & P.share.notna()


def fe(df, y, x, absorb, cluster="seat", label=None, keep=None):
    cols = [y] + list(x) + list(absorb) + [cluster]
    d = df.dropna(subset=cols).copy()
    ab = pd.DataFrame({a: pd.Categorical(d[a]) for a in absorb}, index=d.index)
    res = AbsorbingLS(d[y].astype(float), d[list(x)].astype(float), absorb=ab, drop_absorbed=True).fit(
        cov_type="clustered", clusters=pd.DataFrame({cluster: pd.Categorical(d[cluster]).codes}, index=d.index))
    out = {}
    for v in (keep or [x[0]]):
        ci = res.conf_int().loc[v]
        out[v] = dict(b=float(res.params[v]), se=float(res.std_errors[v]), lo=float(ci.iloc[0]), hi=float(ci.iloc[1]),
                      p=float(res.pvalues[v]))
    first = dict(out[(keep or [x[0]])[0]])
    first.update(n=int(res.nobs), clusters=int(d[cluster].nunique()), label=label or "")
    if keep and len(keep) > 1:
        first["terms"] = out
    return first


# party family's best share in each contest (contested, any number of seats), to measure lagged party strength
con = pd.read_csv(f"{ELE}/contests.csv", dtype=str)
cand = pd.read_csv(f"{ELE}/candidates.csv", dtype=str)
con["d"] = con.wikidata.str.replace("wd:", "", regex=False)
c = cand.merge(con[["election", "constituency", "d", "uncontested"]], on=["election", "constituency"])
c = c[c.uncontested == "False"].copy()
c["share"] = pd.to_numeric(c.share, errors="coerce")
fs = c.dropna(subset=["share", "family"]).groupby(["election", "d", "family"]).share.max()
contested_seats = set(zip(c.election, c.d))
nat = pd.read_csv(f"{ELE}/votes_by_family.csv", dtype={"election": str}).set_index("election")


def lagged(e, d, f):
    i = EIDX[e]
    if i == 0:
        return np.nan
    e0 = ELECTIONS[i - 1]
    if (e0, d) not in contested_seats:
        return np.nan
    s = fs.get((e0, d, f), 0.0)          # party did not stand: 0
    try:
        return float(s) - float(nat.at[e0, f])
    except (KeyError, TypeError, ValueError):
        return np.nan


S1 = P[P.single & P.contested & P.local25.notna()].copy()
S1["share"] = S1.share.astype(float)
S1["lagrel"] = [lagged(e, d, f) for e, d, f in zip(S1.election, S1.seat, S1.fam)]
S1["post2010"] = (S1.year >= 2010).astype(float)
S1["loc_x_post"] = S1.local25 * S1.post2010
F = S1[S1.tenure == 0].copy()
R = {}
R["firstwin"] = fe(F, "share", ["local25"], ["seat", "ef"], label="First-time winners only (no accumulated incumbency)")
R["seatparty_tenure"] = fe(S1, "share", ["local25", "tenure"], ["sf", "ef"], label="Seat x party FE, adding tenure")
R["balance_firstwin"] = fe(F, "local25", ["lagrel"], ["seat", "ef"],
                           label="Balance: new MP local (0/1) on party's lagged seat share minus national (per point)")
R["balance_firstwin"]["per10"] = 10 * R["balance_firstwin"]["b"]
R["firstwin_lag"] = fe(F, "share", ["local25", "lagrel"], ["seat", "ef"], label="First-time winners, controlling for party's lagged seat strength")
R["main_lag"] = fe(S1, "share", ["local25", "lagrel", "tenure"], ["seat", "ef"], label="All returns, controlling for party's lagged seat strength and tenure")
R["post2010_diff"] = fe(S1, "share", ["local25", "loc_x_post"], ["seat", "ef"], keep=["local25", "loc_x_post"],
                        label="Local x 2010 to 2024 interaction (difference from 1832 to 2009)")
R["n_firstwin"] = len(F)
jsave(R, f"{DATA}/review_checks.json", indent=1)
for k, v in R.items():
    print(k, v if not isinstance(v, dict) else {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "terms"})
print(R["post2010_diff"]["terms"]["loc_x_post"])
