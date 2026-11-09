"""Step 5: compact page data (data/seats.json) and the reusable derived CSVs.
data/seats.json: {elections, fams, seats: [[label, lon, lat, nation, wikidata]], mps: [[seat index, election index, name,
family index, km or null, share or null, person id]]}."""
import numpy as np
import pandas as pd
from common import *

P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
S = pd.read_csv(f"{MPL}/seats.csv").set_index("seat")
P = P[P.seat.isin(S.index)]
seats = sorted(P.seat.unique(), key=lambda s: S.at[s, "label"])
si = {s: i for i, s in enumerate(seats)}
fams = sorted(P.fam.dropna().unique(), key=lambda f: list(FAMNAME).index(f) if f in FAMNAME else 99)
fi = {f: i for i, f in enumerate(fams)}
rows = []
for r in P.sort_values(["seat", "eidx"]).itertuples():
    rows.append([si[r.seat], int(r.eidx), r.name, fi.get(r.fam, -1),
                 None if r.dist_km != r.dist_km else round(float(r.dist_km), 1),
                 None if r.share != r.share else round(float(r.share), 1), r.person])
out = dict(elections=ELECTIONS, fams=[[f, FAMNAME.get(f, f)] for f in fams],
           seats=[[S.at[s, "label"], round(float(S.at[s, "lon"]), 4), round(float(S.at[s, "lat"]), 4), S.at[s, "nation"], s] for s in seats],
           mps=rows)
jsave(out, f"{DATA}/seats.json", keepdash=True)
print("seats.json", os.path.getsize(f"{DATA}/seats.json") // 1024, "KB", len(seats), "seats", len(rows), "rows")
