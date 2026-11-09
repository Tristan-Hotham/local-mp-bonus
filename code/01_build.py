"""Step 1: the analysis panel.

One row per MP return at a general election (mp-localness mp_elections.csv), linked to
  - its own candidate row in elections-since-1832 (seat item + election, then surname and forename initial),
  - the same seat item at the next general election: did the MP stand there again, win or lose, with what share;
    the party family's share there; who won and whether they were local,
  - the national vote share of the party family at both elections.
Also builds the candidate-level file of ever-MP candidates (winners and losers who were an MP at some general
election, matched by name) used in the succession and candidate-level checks.
Writes data/panel.csv and data/candidates_evermp.csv; prints link statistics to SCR/stats01.json.
"""
import collections
import numpy as np
import pandas as pd
from common import *

mp = pd.read_csv(f"{MPL}/mp_elections.csv", dtype={"election": str})
people = pd.read_csv(f"{MPL}/people.csv")
seats = pd.read_csv(f"{MPL}/seats.csv")
con = pd.read_csv(f"{ELE}/contests.csv", dtype=str)
cand = pd.read_csv(f"{ELE}/candidates.csv", dtype=str)
nat = pd.read_csv(f"{ELE}/votes_by_family.csv", dtype={"election": str}).set_index("election")
assert set(mp.election) <= set(ELECTIONS), set(mp.election) - set(ELECTIONS)

con["d"] = con.wikidata.str.replace("wd:", "", regex=False)
con["seats"] = con.seats.astype(int)
con["uncontested"] = con.uncontested == "True"
cand = cand.merge(con[["election", "constituency", "d", "seats", "uncontested", "turnout"]], on=["election", "constituency"], how="left")
cand["votes"] = pd.to_numeric(cand.votes, errors="coerce")
cand["share"] = pd.to_numeric(cand.share, errors="coerce")
cand["elected"] = cand.elected == "True"
cand["cid"] = np.arange(len(cand))
sp = cand.candidate.map(cand_parts)
cand["sur"] = sp.map(lambda x: x[0])
cand["fore"] = sp.map(lambda x: x[1])
BY = {k: g for k, g in cand.groupby(["election", "d"])}

pname = dict(zip(people.person, people.name))
ptok = {p: [t for t in norm_tokens(re.sub(r"\(.*?\)", " ", str(n))) if t not in TITLES] for p, n in pname.items()}


def name_ok(person, sur, fore, need_initial=True):
    toks = ptok.get(person, [])
    if not toks or not sur:
        return False
    if not all(s in toks for s in sur):
        # double-barrelled names: accept if the last surname token is present
        if sur[-1] not in toks:
            return False
    if not need_initial or not fore:
        return True
    # forename initial: the candidate's first forename (or initial) starts like one of the person's given names
    f0 = fore[0]
    given = toks[:-1] or toks
    return any(t[0] == f0[0] for t in given)


stats = collections.Counter()
# ---------- 1. link each MP return to its candidate row ----------
own = []
for r in mp.itertuples():
    g = BY.get((r.election, r.seat))
    if g is None:
        own.append(None); stats["no_contest"] += 1; continue
    w = g[g.elected]
    hit = w[[name_ok(r.person, s, f, False) for s, f in zip(w.sur, w.fore)]]
    if len(hit) > 1:
        hit = hit[[name_ok(r.person, s, f, True) for s, f in zip(hit.sur, hit.fore)]]
    if len(hit) == 1:
        own.append(int(hit.cid.iloc[0])); stats["own_surname"] += 1
    elif len(w) == 1:
        own.append(int(w.cid.iloc[0])); stats["own_single_winner"] += 1
    else:
        own.append(None); stats["own_unmatched"] += 1
mp["cid"] = own
C = cand.set_index("cid")
for col in ("votes", "share", "family", "seats", "uncontested", "turnout", "party"):
    mp["c_" + col] = [C.at[c, col] if c is not None and c == c else None for c in mp.cid]
mp["eidx"] = mp.election.map(EIDX)

# ---------- 2. history: tenure, first election ----------
mp = mp.sort_values(["person", "eidx"]).reset_index(drop=True)
mp["tenure"] = mp.groupby("person").cumcount()           # earlier general-election wins
mp["first_eidx"] = mp.groupby("person").eidx.transform("min")
won = {(p, e): d for p, e, d in zip(mp.person, mp.eidx, mp.seat)}
local_of = {(p, e): l for p, e, l in zip(mp.person, mp.eidx, mp.local25)}


def famshare(g, fam):
    if g is None or fam is None or fam != fam:
        return np.nan
    x = g[g.family == fam]
    if len(x) == 0:
        return 0.0 if not g.uncontested.iloc[0] else np.nan
    if g.uncontested.iloc[0] or x.share.isna().all():
        return np.nan
    return float(x.share.max())          # best candidate of the family (single-member: the candidate)


# ---------- 3. the next general election in the same seat item ----------
nxt = []
for r in mp.itertuples():
    i = r.eidx
    out = dict(next_status="last_election" if i == len(ELECTIONS) - 1 else None)
    if i < len(ELECTIONS) - 1:
        e2 = ELECTIONS[i + 1]
        g2 = BY.get((e2, r.seat))
        fam = r.c_family if isinstance(r.c_family, str) else r.family
        if g2 is None:
            out["next_status"] = "seat_gone"
            if (r.person, i + 1) in won:
                out["next_status"] = "seat_gone_won_elsewhere"
        else:
            out["next_seats"] = int(g2.seats.iloc[0]); out["next_uncontested"] = bool(g2.uncontested.iloc[0])
            out["fam_share_next"] = famshare(g2, fam)
            out["fam_stood_next"] = bool((g2.family == fam).any())
            wf = g2[g2.elected & (g2.family == fam)]
            out["fam_held_next"] = len(wf) > 0
            if won.get((r.person, i + 1)) == r.seat:
                out["next_status"] = "stood_won"
                me = g2[g2.elected]
                me = me[[name_ok(r.person, s, f, False) for s, f in zip(me.sur, me.fore)]]
                if len(me) > 1:
                    me = me[[name_ok(r.person, s, f, True) for s, f in zip(me.sur, me.fore)]]
                if len(me) == 0 and g2.elected.sum() == 1:
                    me = g2[g2.elected]
                if len(me) == 1:
                    out.update(next_share=me.share.iloc[0], next_family=me.family.iloc[0], next_cid=int(me.cid.iloc[0]))
            else:
                lo = g2[~g2.elected]
                lo = lo[[name_ok(r.person, s, f, True) for s, f in zip(lo.sur, lo.fore)]]
                if len(lo) == 1:
                    out.update(next_status="stood_lost", next_share=lo.share.iloc[0], next_family=lo.family.iloc[0],
                               next_cid=int(lo.cid.iloc[0]))
                elif len(lo) > 1:
                    out["next_status"] = "ambiguous"
                elif (r.person, i + 1) in won:
                    out["next_status"] = "moved_won"
                else:
                    out["next_status"] = "not_standing"
    nxt.append(out)
N = pd.DataFrame(nxt)
mp = pd.concat([mp, N], axis=1)
mp["fam"] = [a if isinstance(a, str) else b for a, b in zip(mp.c_family, mp.family)]

# successor of the same family in the same seat at the next election (for H5/H6)
WIN2 = collections.defaultdict(list)
for r in mp.itertuples():
    WIN2[(r.eidx, r.seat, r.fam)].append((r.person, r.local25, r.dist_km, r.same_county))
succ_local, succ_person, succ_n = [], [], []
for r in mp.itertuples():
    s = [x for x in WIN2.get((r.eidx + 1, r.seat, r.fam), []) if x[0] != r.person]
    succ_n.append(len(s))
    succ_local.append(s[0][1] if len(s) == 1 else np.nan)
    succ_person.append(s[0][0] if len(s) == 1 else None)
mp["succ_person"] = succ_person; mp["succ_local25"] = succ_local; mp["succ_n"] = succ_n

# national shares
def natshare(e, f):
    try:
        return float(nat.at[e, f])
    except (KeyError, TypeError):
        return np.nan
mp["nat_share"] = [natshare(e, f) for e, f in zip(mp.election, mp.fam)]
mp["nat_share_next"] = [natshare(ELECTIONS[i + 1], f) if i < len(ELECTIONS) - 1 else np.nan for i, f in zip(mp.eidx, mp.fam)]

# birthplace and seat point quality
pp = people.set_index("person")
mp["bp_source"] = mp.person.map(pp.bp_source)
mp["bp_precision"] = mp.person.map(pp.bp_precision)
mp["seat_point_source"] = mp.seat.map(seats.set_index("seat").point_source)
mp["era"] = mp.year.map(era_of)
mp["redist_next"] = [ELECTIONS[i + 1] in REDIST if i < len(ELECTIONS) - 1 else False for i in mp.eidx]

# ---------- 4. ever-MP candidates: every candidacy of a person who was an MP at some general election ----------
# A candidacy is linked to a person if the surname (all tokens) and forename initial match, the person was an MP at
# some general election within 30 years either side, and exactly one such person matches.
span = mp.groupby("person").year.agg(["min", "max"])
bysur = collections.defaultdict(set)
for p, toks in ptok.items():
    if p in span.index:
        for t in toks:
            bysur[t].add(p)
cid2person = {int(c): p for c, p in zip(mp.cid, mp.person) if c == c and c is not None}
link = []
yr = {e: int(re.sub(r"\D", "", e)[-4:]) for e in ELECTIONS}
for r in cand.itertuples():
    if r.cid in cid2person:
        link.append((r.cid, cid2person[r.cid], "own MP row")); continue
    if not r.sur:
        continue
    cands = set.intersection(*[bysur.get(t, set()) for t in r.sur]) if r.sur else set()
    y = yr[r.election]
    cands = [p for p in cands if span.at[p, "min"] - 30 <= y <= span.at[p, "max"] + 30 and name_ok(p, r.sur, r.fore, True)]
    if len(cands) == 1:
        link.append((r.cid, cands[0], "name match"))
    elif len(cands) > 1:
        stats["evermp_ambiguous"] += 1
L = pd.DataFrame(link, columns=["cid", "person", "link"])
ev = cand.merge(L, on="cid")
bp = people.set_index("person")
ev["name"] = ev.person.map(pname)
# distance from the birthplace to this contest's seat point
sp_ = seats.set_index("seat")
def hav(lon1, lat1, lon2, lat2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))
ev["dist_km"] = hav(ev.person.map(bp.bp_lon), ev.person.map(bp.bp_lat), ev.d.map(sp_.lon), ev.d.map(sp_.lat))
ev["local25"] = np.where(ev.dist_km.notna(), (ev.dist_km <= 25).astype(float), np.nan)
ev["eidx"] = ev.election.map(EIDX)
ev["year"] = ev.election.map(yr)
ev = ev.drop(columns=["sur", "fore"])
ev.to_csv(f"{DATA}/candidates_evermp.csv", index=False)

# check: our recomputed distance equals the mp-localness distance on own rows
chk = ev[ev.link == "own MP row"].merge(mp[["cid", "dist_km"]], on="cid", suffixes=("", "_mpl"))
diff = (chk.dist_km - chk.dist_km_mpl).abs()
print("distance check: max abs diff", round(float(diff.max()), 3), "n", int(diff.notna().sum()))
stats["evermp_rows"] = len(ev); stats["evermp_losers"] = int((~ev.elected).sum())
stats["evermp_losers_bp"] = int(((~ev.elected) & ev.dist_km.notna()).sum())

keep = ["election", "year", "eidx", "era", "person", "name", "seat", "seat_label", "seat_nation", "seat_county",
        "seat_region", "fam", "party_label", "bp_known", "dist_km", "local25", "same_county", "born_london",
        "born_abroad", "bp_source", "bp_precision", "seat_point_source", "cid", "c_votes", "c_share", "c_seats",
        "c_uncontested", "c_turnout", "nat_share", "tenure", "first_eidx", "next_status", "next_seats",
        "next_uncontested", "next_share", "next_family", "fam_share_next", "fam_stood_next", "fam_held_next",
        "nat_share_next", "succ_person", "succ_local25", "succ_n", "redist_next"]
mp[keep].rename(columns={"c_votes": "votes", "c_share": "share", "c_seats": "seats", "c_uncontested": "uncontested",
                         "c_turnout": "turnout"}).to_csv(f"{DATA}/panel.csv", index=False)
stats.update({f"next_{k}": int(v) for k, v in mp.next_status.value_counts().items()})
stats["returns"] = len(mp); stats["linked"] = int(mp.cid.notna().sum())
jsave(dict(stats), f"{SCR}/stats01.json", indent=1)
print(dict(stats))
