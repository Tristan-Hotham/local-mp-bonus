"""Step 2: the pre-specified models (NOTES.md, analysis plan), robustness, placebo and heterogeneity checks.
Reads data/panel.csv and data/candidates_evermp.csv; writes data/models.json (every estimate with N, clusters, 95% CI).
Fixed-effects regressions use linearmodels AbsorbingLS (OLS with absorbed dummies), standard errors clustered by
constituency item unless stated. The Cox model uses statsmodels PHReg.
"""
import sys, time, warnings
import numpy as np
import pandas as pd
from linearmodels.iv.absorbing import AbsorbingLS
import statsmodels.api as sm
import statsmodels.formula.api as smf
from common import *

warnings.filterwarnings("ignore")
QUICK = "--quick" in sys.argv or "quick" in sys.argv
NPLAC = 3 if ("--noplac" in sys.argv or "noplac" in sys.argv) else (60 if QUICK else 500)
rng = np.random.default_rng(SEED)
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
people = pd.read_csv(f"{MPL}/people.csv").set_index("person")
seats = pd.read_csv(f"{MPL}/seats.csv").set_index("seat")
EV = pd.read_csv(f"{DATA}/candidates_evermp.csv", dtype={"election": str})

# ---------- common sample rules (data construction, fixed before outcomes) ----------
P = P[~P.seat_label.str.contains("University", na=False) & (P.fam != "SPK") & P.fam.notna()].copy()
P["ef"] = P.election + "_" + P.fam
P["sf"] = P.seat + "_" + P.fam
P["nation"] = P.seat_nation.replace({"Northern Ireland": "Ireland/NI", "Ireland": "Ireland/NI"})
P["fam3"] = P.fam.where(P.fam.isin(["CON", "LAB", "LIB"]), "Other")
P["logd"] = np.log1p(P.dist_km)
P["local10"] = np.where(P.dist_km.notna(), (P.dist_km <= 10).astype(float), np.nan)
P["local50"] = np.where(P.dist_km.notna(), (P.dist_km <= 50).astype(float), np.nan)
P["band"] = pd.cut(P.dist_km, [-1, 25, 100, 1e6], labels=["0 to 25", "25 to 100", "over 100"])
P["p19"] = P.bp_source.str.startswith("wikidata P19", na=False)
P["ownpoint"] = P.seat_point_source.eq("wikidata P625")
P["single"] = P.seats.eq(1)
P["contested"] = P.uncontested.eq(False) & P.share.notna()


def fe(df, y, x, absorb, cluster="seat", label=None, keep=None):
    """OLS of y on x with absorbed fixed effects; returns the estimate of x[0] (or all in keep) with clustered SE."""
    cols = [y] + list(x) + list(absorb) + ([cluster] if isinstance(cluster, str) else list(cluster))
    d = df.dropna(subset=[c for c in cols if c in df.columns]).copy()
    if len(d) < 30:
        return None
    x = [x[0]] + [v for v in x[1:] if d[v].astype(float).std() > 0]
    ab = pd.DataFrame({a: pd.Categorical(d[a]) for a in absorb}, index=d.index) if absorb else None
    X = d[list(x)].astype(float)
    if not absorb:
        X = sm.add_constant(X)
    mod = AbsorbingLS(d[y].astype(float), X, absorb=ab, drop_absorbed=True)
    if isinstance(cluster, str):
        cl = pd.DataFrame({cluster: pd.Categorical(d[cluster]).codes}, index=d.index)
    else:
        cl = pd.DataFrame({c: pd.Categorical(d[c]).codes for c in cluster}, index=d.index)
    res = mod.fit(cov_type="clustered", clusters=cl)
    out = {}
    for v in (keep or [x[0]]):
        b, s = float(res.params[v]), float(res.std_errors[v])
        ci = res.conf_int().loc[v]
        out[v] = dict(b=b, se=s, lo=float(ci.iloc[0]), hi=float(ci.iloc[1]), p=float(res.pvalues[v]))
    first = out[(keep or [x[0]])[0]]
    first.update(n=int(res.nobs), clusters=int(cl.iloc[:, 0].nunique()), ymean=float(d[y].mean()),
                 xmean=float(d[x[0]].mean()), label=label or "")
    if keep and len(keep) > 1:
        first["terms"] = {k: dict(b=v["b"], se=v["se"], lo=v["lo"], hi=v["hi"], p=v["p"]) for k, v in out.items()}
    return first


M = {}
t0 = time.time()
# ===================== H1: vote-share level, within seat =====================
S1 = P[P.single & P.contested & P.local25.notna()].copy()
S1["share"] = S1.share.astype(float)
M["h1_main"] = fe(S1, "share", ["local25"], ["seat", "ef"], label="Main: seat FE + election x party FE")
# descriptive: how many seats contribute within-seat variation
v = S1.groupby("seat").local25.agg(["min", "max", "size"])
M["h1_main"]["seats_with_variation"] = int(((v["min"] == 0) & (v["max"] == 1)).sum())
M["h1_main"]["rows_in_varying_seats"] = int(S1.seat.isin(v[(v["min"] == 0) & (v["max"] == 1)].index).sum())
M["h1_raw_diff"] = dict(local=float(S1[S1.local25 == 1].share.mean()), nonlocal_=float(S1[S1.local25 == 0].share.mean()),
                        n_local=int((S1.local25 == 1).sum()), n_nonlocal=int((S1.local25 == 0).sum()))
M["h1_rel_nat"] = fe(S1.assign(rel=S1.share - S1.nat_share), "rel", ["local25"], ["seat", "ef"], label="Outcome: share minus party national share")
M["h1_noseatfe"] = fe(S1, "share", ["local25"], ["ef", "nation"], label="No seat FE (election x party + nation FE)")
M["h1_seatparty"] = fe(S1, "share", ["local25"], ["sf", "ef"], label="Seat x party FE + election x party FE")
M["h1_tenure"] = fe(S1, "share", ["local25", "tenure"], ["seat", "ef"], label="Adding tenure (earlier wins)")
M["h1_cl_person"] = fe(S1, "share", ["local25"], ["seat", "ef"], cluster="person", label="SE clustered by MP")
M["h1_cl_twoway"] = fe(S1, "share", ["local25"], ["seat", "ef"], cluster=["seat", "election"], label="SE two-way: seat and election")
# measurement
M["h1_local10"] = fe(S1, "share", ["local10"], ["seat", "ef"], label="Born within 10 km")
M["h1_local50"] = fe(S1, "share", ["local50"], ["seat", "ef"], label="Born within 50 km")
M["h1_county"] = fe(S1.dropna(subset=["same_county"]), "share", ["same_county"], ["seat", "ef"], label="Born in the seat's county")
M["h1_logd"] = fe(S1, "share", ["logd"], ["seat", "ef"], label="log(1 + km), per unit")
b = S1.assign(b25_100=(S1.band == "25 to 100").astype(float), b0_25=(S1.band == "0 to 25").astype(float))
M["h1_bands"] = fe(b, "share", ["b0_25", "b25_100"], ["seat", "ef"], keep=["b0_25", "b25_100"], label="Distance bands (ref: over 100 km)")
M["h1_p19"] = fe(S1[S1.p19], "share", ["local25"], ["seat", "ef"], label="Wikidata birthplaces only")
M["h1_ownpoint"] = fe(S1[S1.ownpoint], "share", ["local25"], ["seat", "ef"], label="Seats with their own coordinates only")
M["h1_noabroad"] = fe(S1[S1.born_abroad != 1], "share", ["local25"], ["seat", "ef"], label="Excluding MPs born abroad")
U = P[P.single & P.contested].copy()
U["unknown"] = U.local25.isna().astype(float); U["loc_or0"] = U.local25.fillna(0)
M["h1_unknown"] = fe(U, "share", ["loc_or0", "unknown"], ["seat", "ef"], keep=["loc_or0", "unknown"], label="All MPs, unknown birthplace as its own category")
# leave one out / heterogeneity
for k, name, a, bb in ERAS:
    M[f"h1_era_{k}"] = fe(S1[S1.era == k], "share", ["local25"], ["seat", "ef"], label=name)
    M[f"h1_dropera_{k}"] = fe(S1[S1.era != k], "share", ["local25"], ["seat", "ef"], label=f"Without {name}")
for n in ["England", "Scotland", "Wales", "Ireland/NI"]:
    M[f"h1_nat_{n[:3]}"] = fe(S1[S1.nation == n], "share", ["local25"], ["seat", "ef"], label=n)
    M[f"h1_dropnat_{n[:3]}"] = fe(S1[S1.nation != n], "share", ["local25"], ["seat", "ef"], label=f"Without {n}")
for f in ["CON", "LAB", "LIB"]:
    M[f"h1_fam_{f}"] = fe(S1[S1.fam == f], "share", ["local25"], ["seat", "ef"], label=FAMNAME[f])
M["h1_drop2024"] = fe(S1[S1.election != "2024"], "share", ["local25"], ["seat", "ef"], label="Without 2024")
M["h1_dropire"] = fe(S1[~((S1.seat_nation == "Ireland") & (S1.year < 1922))], "share", ["local25"], ["seat", "ef"], label="Without Ireland before 1922")
print("H1 done", round(time.time() - t0), "s", M["h1_main"])

# ---------- candidate-level extension: losers who were MPs at some general election ----------
EV = EV[(EV.seats == 1) & (EV.uncontested == False) & EV.share.notna() & EV.local25.notna() & EV.family.notna()].copy()
EV = EV[~EV.family.isin(["SPK"])]
EV["ef"] = EV.election + "_" + EV.family
EV["seat"] = EV.d
M["cand_evermp"] = fe(EV, "share", ["local25"], ["seat", "ef"], label="All candidacies of ever-MPs (winners and losers)")
M["cand_evermp"]["n_losers"] = int((EV.elected == False).sum())
M["cand_evermp_win"] = fe(EV, "elected", ["local25"], ["seat", "ef"], label="Won the seat (ever-MP candidacies)")
EV["elected"] = EV.elected.astype(float)
M["cand_evermp_win"] = fe(EV, "elected", ["local25"], ["seat", "ef"], label="Won the seat (ever-MP candidacies)")

# ---------- placebo 1: localness to a random other seat of the same election and nation ----------
bl = S1.person.map(people.bp_lon).values; bt = S1.person.map(people.bp_lat).values
seatpool = {}
for (e, n), g in P.groupby(["election", "seat_nation"]):
    seatpool[(e, n)] = g.seat.unique()
slon, slat = seats.lon, seats.lat


def hav(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


keys = list(zip(S1.election, S1.seat_nation, S1.seat))
ownlon, ownlat = slon.reindex(S1.seat).values, slat.reindex(S1.seat).values
NFAKE = max(3, NPLAC * 3 // 5)
FARC = []
for j, (e, n, s) in enumerate(keys):
    pool = seatpool[(e, n)]
    dd = hav(ownlon[j], ownlat[j], slon.reindex(pool).values, slat.reindex(pool).values)
    FARC.append(pool[dd >= 50])
fake_b, fake_joint, far_b = [], [], []
for it in range(NFAKE):
    fs, ff = [], []
    for (e, n, s) in keys:
        pool = seatpool[(e, n)]
        x = s
        while x == s and len(pool) > 1:
            x = pool[rng.integers(len(pool))]
        fs.append(x)
    fs = np.array(fs)
    d = hav(bl, bt, slon.reindex(fs).values, slat.reindex(fs).values)
    S1["fake"] = (d <= 25).astype(float)
    fake_b.append(fe(S1, "share", ["fake"], ["seat", "ef"])["b"])
    fake_joint.append(fe(S1, "share", ["local25", "fake"], ["seat", "ef"], keep=["local25", "fake"])["terms"]["fake"]["b"])
    # far version: a random seat of the same election and nation at least 50 km from the MP's own seat
    far = [(FARC[j][rng.integers(len(FARC[j]))] if len(FARC[j]) else s) for j, (e, n, s) in enumerate(keys)]
    far = np.array(far)
    d2 = hav(bl, bt, slon.reindex(far).values, slat.reindex(far).values)
    S1["fakefar"] = (d2 <= 25).astype(float)
    far_b.append(fe(S1, "share", ["fakefar"], ["seat", "ef"])["b"])
fake_b, fake_joint, far_b = map(np.array, (fake_b, fake_joint, far_b))
summ = lambda a: dict(draws=len(a), mean=float(a.mean()), sd=float(a.std()), lo=float(np.percentile(a, 2.5)), hi=float(np.percentile(a, 97.5)),
                      share_ge_main=float((a >= M["h1_main"]["b"]).mean()))
M["placebo_fakeseat"] = summ(fake_b)
M["placebo_fakeseat_cond"] = summ(fake_joint)
M["placebo_fakeseat_far"] = summ(far_b)
# one draw with both real and fake in the same model
M["placebo_fakeseat_joint"] = fe(S1, "share", ["local25", "fake"], ["seat", "ef"], keep=["local25", "fake"], label="Real and fake localness together")
print("placebo 1 done", round(time.time() - t0), "s", M["placebo_fakeseat"])

# ---------- placebo 3: permutation of local25 within election x party cells ----------
perm_b = []
grp = S1.groupby("ef").indices
for it in range(NPLAC):
    x = S1.local25.values.copy()
    for idx in grp.values():
        x[idx] = x[idx][rng.permutation(len(idx))]
    S1["perm"] = x
    perm_b.append(fe(S1, "share", ["perm"], ["seat", "ef"])["b"])
perm_b = np.array(perm_b)
M["placebo_perm"] = dict(draws=NPLAC, mean=float(perm_b.mean()), sd=float(perm_b.std()),
                         p_two=float((np.abs(perm_b) >= abs(M["h1_main"]["b"])).mean()))
print("placebo 3 done", round(time.time() - t0), "s", M["placebo_perm"])

# ===================== H2: defeat of incumbents standing again in the same seat =====================
S2 = P[P.next_status.isin(["stood_won", "stood_lost"]) & (P.next_uncontested == False) & P.local25.notna()].copy()
S2["defeat"] = (S2.next_status == "stood_lost").astype(float)
S2["lag_share"] = np.where(S2.single & S2.contested, S2.share, np.nan)
S2["lag_missing"] = S2.lag_share.isna().astype(float)
S2["lag_share0"] = S2.lag_share.fillna(0)
S2["multi"] = (~S2.single).astype(float)
S2["nseats_next_multi"] = (S2.next_seats > 1).astype(float)
M["h2_main"] = fe(S2, "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"],
                  label="Main: election x party FE + nation FE, lagged share, tenure")
M["h2_main"]["defeat_rate"] = float(S2.defeat.mean())
M["h2_raw"] = dict(local=float(S2[S2.local25 == 1].defeat.mean()), nonlocal_=float(S2[S2.local25 == 0].defeat.mean()),
                   n_local=int((S2.local25 == 1).sum()), n_nonlocal=int((S2.local25 == 0).sum()))
S2s = S2[S2.single & S2.contested & (S2.next_seats == 1)].copy()
M["h2_single"] = fe(S2s, "defeat", ["local25", "lag_share", "tenure"], ["ef", "nation"], label="Single-member, contested both times")
M["h2_seatfe"] = fe(S2s, "defeat", ["local25", "lag_share", "tenure"], ["ef", "seat"], label="Seat FE instead of nation FE")
M["h2_cl_person"] = fe(S2, "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], cluster="person", label="SE clustered by MP")
M["h2_county"] = fe(S2.dropna(subset=["same_county"]), "defeat", ["same_county", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="Born in the seat's county")
M["h2_logd"] = fe(S2, "defeat", ["logd", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="log(1 + km), per unit")
M["h2_local10"] = fe(S2, "defeat", ["local10", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="Born within 10 km")
M["h2_local50"] = fe(S2, "defeat", ["local50", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="Born within 50 km")
M["h2_noredist"] = fe(S2[~S2.redist_next], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="Excluding elections with new boundaries")
M["h2_p19"] = fe(S2[S2.p19], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label="Wikidata birthplaces only")
# logit (single-member, contested both, election FE as dummies is heavy: use family + era + nation dummies and lagged share)
try:
    lg = smf.logit("defeat ~ local25 + lag_share + tenure + C(election) + C(fam3) + C(nation)", data=S2s).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": pd.Categorical(S2s.seat).codes})
    ame = lg.get_margeff(at="overall").summary_frame().loc["local25"]
    M["h2_logit"] = dict(b=float(ame["dy/dx"]), se=float(ame["Std. Err."]), lo=float(ame["Conf. Int. Low"]),
                         hi=float(ame["Cont. Int. Hi."]), p=float(ame["Pr(>|z|)"]), n=int(lg.nobs),
                         label="Logit, average marginal effect (election, party, nation dummies)")
except Exception as ex:
    print("logit failed", ex)
for k, name, a, bb in ERAS:
    M[f"h2_era_{k}"] = fe(S2[S2.era == k], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label=name)
for n in ["England", "Scotland", "Wales", "Ireland/NI"]:
    M[f"h2_nat_{n[:3]}"] = fe(S2[S2.nation == n], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef"], label=n)
    M[f"h2_dropnat_{n[:3]}"] = fe(S2[S2.nation != n], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label=f"Without {n}")
for f in ["CON", "LAB", "LIB"]:
    M[f"h2_fam_{f}"] = fe(S2[S2.fam == f], "defeat", ["local25", "lag_share0", "lag_missing", "tenure", "multi"], ["ef", "nation"], label=FAMNAME[f])
print("H2 done", round(time.time() - t0), "s", M["h2_main"])

# ===================== H3: change in the incumbent's own share =====================
S3 = S2s[(S2s.next_family == S2s.fam)].copy()
S3["dshare"] = S3.next_share.astype(float) - S3.share.astype(float)
M["h3_main"] = fe(S3, "dshare", ["local25", "lag_share", "tenure"], ["ef", "nation"], label="Main: election x party FE + nation FE, lagged share, tenure")
M["h3_seatfe"] = fe(S3, "dshare", ["local25", "lag_share", "tenure"], ["ef", "seat"], label="Seat FE")
M["h3_noredist"] = fe(S3[~S3.redist_next], "dshare", ["local25", "lag_share", "tenure"], ["ef", "nation"], label="Excluding elections with new boundaries")
M["h3_county"] = fe(S3.dropna(subset=["same_county"]), "dshare", ["same_county", "lag_share", "tenure"], ["ef", "nation"], label="Born in the seat's county")
M["h3_logd"] = fe(S3, "dshare", ["logd", "lag_share", "tenure"], ["ef", "nation"], label="log(1 + km), per unit")
M["h3_first"] = fe(S3[S3.tenure == 0], "dshare", ["local25", "lag_share"], ["ef", "nation"], label="First re-election only (sophomore)")
for k, name, a, bb in ERAS:
    M[f"h3_era_{k}"] = fe(S3[S3.era == k], "dshare", ["local25", "lag_share", "tenure"], ["ef", "nation"], label=name)
for f in ["CON", "LAB", "LIB"]:
    M[f"h3_fam_{f}"] = fe(S3[S3.fam == f], "dshare", ["local25", "lag_share", "tenure"], ["ef", "nation"], label=FAMNAME[f])
print("H3 done", round(time.time() - t0), "s", M["h3_main"])

# ===================== H4: tenure (spells of consecutive general-election wins) =====================
Q = P.sort_values(["person", "eidx"]).copy()
Q["gap"] = Q.groupby("person").eidx.diff().fillna(99) != 1
Q["spell"] = Q.groupby("person").gap.cumsum()
sp = Q.groupby(["person", "spell"]).agg(start=("eidx", "min"), end=("eidx", "max"), n=("eidx", "size"),
                                         local25=("local25", "first"), fam=("fam", "first"), year=("year", "first"),
                                         nation=("nation", "first"), last_status=("next_status", "last")).reset_index()
sp = sp[sp.spell == 1].copy()     # first spell of each person
sp["event"] = (sp.end < len(ELECTIONS) - 1).astype(int)
sp["defeated"] = ((sp.last_status == "stood_lost") & (sp.event == 1)).astype(int)
sp["era"] = sp.year.map(era_of)
sp["fam3"] = sp.fam.where(sp.fam.isin(["CON", "LAB", "LIB"]), "Other")
spk = sp.dropna(subset=["local25"]).copy()
H4 = {}
H4["n_people"] = len(spk); H4["mean_terms_local"] = float(spk[spk.local25 == 1].n.mean()); H4["mean_terms_nonlocal"] = float(spk[spk.local25 == 0].n.mean())
X = pd.get_dummies(spk[["local25", "fam3", "nation"]], columns=["fam3", "nation"], drop_first=True).astype(float)
for nm, ev in (("any", "event"), ("defeat", "defeated")):
    m = sm.PHReg(spk.n.values.astype(float), X, status=spk[ev].values, strata=spk.era.values, ties="efron").fit()
    i = list(X.columns).index("local25")
    b, s = float(m.params[i]), float(m.bse[i])
    H4[f"cox_{nm}"] = dict(hr=float(np.exp(b)), lo=float(np.exp(b - 1.96 * s)), hi=float(np.exp(b + 1.96 * s)), p=float(m.pvalues[i]),
                           n=len(spk), events=int(spk[ev].sum()))
for k, name, a, bb in ERAS:
    g = spk[spk.era == k]
    Xg = pd.get_dummies(g[["local25", "fam3", "nation"]], columns=["fam3", "nation"], drop_first=True).astype(float)
    Xg = Xg.loc[:, Xg.std() > 0]
    m = sm.PHReg(g.n.values.astype(float), Xg, status=g.event.values, ties="efron").fit()
    i = list(Xg.columns).index("local25"); b, s = float(m.params[i]), float(m.bse[i])
    H4[f"cox_era_{k}"] = dict(hr=float(np.exp(b)), lo=float(np.exp(b - 1.96 * s)), hi=float(np.exp(b + 1.96 * s)), p=float(m.pvalues[i]), n=len(g), label=name)
# discrete-time alternative: not returned at the next general election (any reason), LPM with election x party FE
D = P[(P.eidx < len(ELECTIONS) - 1) & P.local25.notna()].copy()
D["exit"] = (~D.next_status.isin(["stood_won", "moved_won", "seat_gone_won_elsewhere"])).astype(float)
H4["dt_exit"] = fe(D, "exit", ["local25", "tenure"], ["ef", "nation"], cluster="person", label="Not returned at next election (LPM), SE by MP")
H4["dt_exit"]["rate"] = float(D.exit.mean())
D["notstand"] = (D.next_status == "not_standing").astype(float)
H4["dt_retire"] = fe(D[D.next_status.isin(["stood_won", "stood_lost", "not_standing"])], "notstand", ["local25", "tenure"], ["ef", "nation"], cluster="person", label="Did not stand again in the same seat (LPM)")
M["h4"] = H4
print("H4 done", round(time.time() - t0), "s", H4["cox_any"], H4["cox_defeat"])

# ===================== H5: succession between MPs of the same party, within seat =====================
# predecessor at t (this row) does not stand again; the party's new candidate wins at t+1 (successor known)
S5 = P[(P.next_status == "not_standing") & (P.succ_n == 1) & P.local25.notna() & P.succ_local25.notna() &
       P.single & P.contested & (P.next_seats == 1) & (P.next_uncontested == False)].copy()
S5["drel"] = (S5.fam_share_next - S5.share) - (S5.nat_share_next - S5.nat_share)
S5["dloc"] = S5.succ_local25 - S5.local25
S5["to_local"] = ((S5.local25 == 0) & (S5.succ_local25 == 1)).astype(float)
S5["to_nonlocal"] = ((S5.local25 == 1) & (S5.succ_local25 == 0)).astype(float)
M["h5_main"] = fe(S5, "drel", ["dloc", "share"], ["ef", "nation"], label="Successor minus predecessor localness")
M["h5_cells"] = fe(S5, "drel", ["to_local", "to_nonlocal", "share"], ["ef", "nation"], keep=["to_local", "to_nonlocal"], label="Transitions (ref: no change)")
M["h5_counts"] = {f"{int(a)}to{int(b)}": int(v) for (a, b), v in S5.groupby(["local25", "succ_local25"]).size().items()}
# extension: successor is the party's candidate whether they won or lost, if they were an MP at some point
EVall = pd.read_csv(f"{DATA}/candidates_evermp.csv", dtype={"election": str})
EVk = {(e, d, f): l for e, d, f, l in zip(EVall.election, EVall.d, EVall.family, EVall.local25)}
nextE = {e: ELECTIONS[i + 1] for i, e in enumerate(ELECTIONS[:-1])}
S5b = P[(P.next_status == "not_standing") & P.local25.notna() & P.single & P.contested & (P.next_seats == 1) &
        (P.next_uncontested == False) & P.fam_stood_next.eq(True)].copy()
S5b["succ_any"] = [EVk.get((nextE.get(e), s, f), np.nan) for e, s, f in zip(S5b.election, S5b.seat, S5b.fam)]
S5b = S5b.dropna(subset=["succ_any"])
S5b["drel"] = (S5b.fam_share_next - S5b.share) - (S5b.nat_share_next - S5b.nat_share)
S5b["dloc"] = S5b.succ_any - S5b.local25
M["h5_evermp"] = fe(S5b, "drel", ["dloc", "share"], ["ef", "nation"], label="Successor known if ever an MP (won or lost)")
M["h5_evermp"]["n_lost"] = int((S5b.fam_held_next == False).sum())
# placebo 2 (lead): the successor's localness against the party's change in the election BEFORE the hand-over
prev = P.set_index(["person", "eidx"])
lead = []
for r in S5.itertuples():
    k = (r.person, r.eidx - 1)
    if k in prev.index:
        q = prev.loc[k]
        if isinstance(q, pd.DataFrame):
            q = q.iloc[0]
        if q.seat == r.seat and q.single and q.contested and q.fam == r.fam:
            lead.append(dict(drel_prev=(r.share - q.share) - (r.nat_share - q.nat_share), dloc=r.dloc, share=q.share, ef=r.ef,
                             nation=r.nation, seat=r.seat))
L5 = pd.DataFrame(lead)
M["placebo_lead"] = fe(L5, "drel_prev", ["dloc", "share"], ["ef", "nation"], label="Lead placebo: change before the successor arrived")
print("H5 done", round(time.time() - t0), "s", M["h5_main"], M["placebo_lead"])

# ===================== H6: retirement difference-in-differences =====================
S6 = P[P.next_status.isin(["stood_won", "stood_lost", "not_standing"]) & P.local25.notna() & P.single & P.contested &
       (P.next_seats == 1) & (P.next_uncontested == False) & P.fam_stood_next.eq(True)].copy()
S6["retire"] = (S6.next_status == "not_standing").astype(float)
S6["dfam"] = S6.fam_share_next - S6.share
S6["loc_x_ret"] = S6.local25 * S6.retire
M["h6_main"] = fe(S6, "dfam", ["loc_x_ret", "local25", "retire", "share", "tenure"], ["ef", "nation"],
                  keep=["loc_x_ret", "local25", "retire"], label="Party share change: local x retires")
M["h6_noredist"] = fe(S6[~S6.redist_next], "dfam", ["loc_x_ret", "local25", "retire", "share", "tenure"], ["ef", "nation"],
                      keep=["loc_x_ret", "local25", "retire"], label="Excluding elections with new boundaries")
M["h6_seatfe"] = fe(S6, "dfam", ["loc_x_ret", "local25", "retire", "share", "tenure"], ["ef", "seat"],
                    keep=["loc_x_ret", "local25", "retire"], label="Seat FE")
for k, name, a, bb in ERAS:
    M[f"h6_era_{k}"] = fe(S6[S6.era == k], "dfam", ["loc_x_ret", "local25", "retire", "share", "tenure"], ["ef", "nation"],
                          keep=["loc_x_ret", "local25", "retire"], label=name)
print("H6 done", round(time.time() - t0), "s", M["h6_main"])

# ---------- era-by-era H1 for the time figure: election-group estimates ----------
# ---------- exploratory (added after the planned models; labelled exploratory everywhere) ----------
PER = [("1832 to 1880", 1832, 1884), ("1885 to 1910", 1885, 1917), ("1918 to 1935", 1918, 1944), ("1945 to 1966", 1945, 1969),
       ("1970 to 1992", 1970, 1996), ("1997 to 2005", 1997, 2009), ("2010 to 2024", 2010, 2024)]
M["x_periods"] = []
for name, a, bb in PER:
    g = S1[(S1.year >= a) & (S1.year <= bb)]
    r = fe(g, "share", ["local25"], ["seat", "ef"], label=name)
    r["local_share"] = float(g.local25.mean())
    M["x_periods"].append(r)
M["x_h2_nolag"] = fe(S2, "defeat", ["local25", "tenure", "multi"], ["ef", "nation"], label="Exploratory: defeat without the lagged-share control")
M["samples"] = dict(S1=len(S1), S2=len(S2), S2s=len(S2s), S3=len(S3), S5=len(S5), S5b=len(S5b), S6=len(S6), spells=len(spk), EV=len(EV))
jsave(M, f"{DATA}/models.json", indent=1)
print("all done", round(time.time() - t0), "s")
