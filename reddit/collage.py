"""Reddit collage (r/dataisbeautiful style, light background), 2700 x 1800 px, every number from data/results.json.
Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import shape
from common import *

for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SEMI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
def fp(size):
    f = SEMI.copy(); f.set_size(size); return f
BG, INK, MUT, RULE, LOC, NON = "#FBF8F1", "#22201C", "#6B655B", "#E3DDD0", "#C2410C", "#3B6EA8"
plt.rcParams.update({"font.family": "Source Serif 4", "axes.facecolor": BG, "figure.facecolor": BG, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT})
R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})
S = pd.read_csv(f"{MPL}/seats.csv").set_index("seat")
nat = jload(f"{MPL}/nations.geojson")["features"]
cm = LinearSegmentedColormap.from_list("loc", ["#F4E9DC", "#E9A66B", "#C2410C", "#6E2207"])

fig = plt.figure(figsize=(27, 18), dpi=100)
fig.text(0.03, 0.955, "Does a local MP get a local bonus?", fontproperties=fp(58), color=INK, va="top")
fig.text(0.03, 0.885, f"Every MP returned at a UK general election, 1832 to 2024 ({R['n']['returns']:,} returns). MPs born within 25 km of their seat win "
         f"about {T['bonus']:.1f} points more of the vote\nthan other MPs elected for the same seat (net of their party's national result), but they are defeated just as often, and the bonus has not grown as local MPs became common.",
         fontsize=22, color=MUT, va="top", linespacing=1.45)

# A: map 2010 to 2024
ax = fig.add_axes([0.02, 0.07, 0.33, 0.74]); ax.axis("off")
for f in nat:
    if f["properties"]["nation"] == "Ireland":
        continue
    g = shape(f["geometry"])
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        xy = np.asarray(poly.exterior.coords); ax.fill(xy[:, 0], xy[:, 1], fc="#EFEBE3", ec="#B9B2A5", lw=0.6)
k = P[(P.era == "e4") & P.local25.notna() & (P.seat_nation != "Ireland")].groupby("seat").local25.agg(["mean", "size"]).join(S[["lon", "lat"]]).dropna().sort_values("mean")
ax.scatter(k.lon, k.lat, s=14 + 10 * np.sqrt(k["size"]), c=k["mean"], cmap=cm, vmin=0, vmax=1, edgecolor="white", lw=0.4, zorder=3)
ax.set_xlim(-8.6, 2.2); ax.set_ylim(49.8, 61.0); ax.set_aspect(1 / np.cos(np.radians(55)))
ax.text(-8.5, 60.6, "Where MPs were born locally,\n2010 to 2024", fontproperties=fp(24), color=INK, va="top")
ax.text(-8.5, 59.55, f"{R['local_share']['e4']['pc']:.0f}% of MPs born within 25 km\n(1945 to 2009: {R['local_share']['e3']['pc']:.0f}%)", fontsize=17, color=MUT, va="top", fontfamily="IBM Plex Mono")
cax = fig.add_axes([0.03, 0.235, 0.085, 0.012])
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 100)), cax=cax, orientation="horizontal")
cb.outline.set_visible(False); cb.ax.tick_params(labelsize=13)
fig.text(0.03, 0.255, "Share of the seat's MPs\nborn within 25 km (%)", fontsize=14, color=INK)
fig.text(0.03, 0.19, "Dot size: number of MPs\nwith a known birthplace", fontsize=13, color=MUT, va="top")

# B: localness over time
ax = fig.add_axes([0.42, 0.53, 0.55, 0.26])
be = [x for x in R["by_election"] if x["n"] >= 40]
ax.plot([x["year"] for x in be], [x["local_pc"] for x in be], color=LOC, lw=4)
ax.set_ylim(0, 50); ax.set_xlim(1828, 2030); ax.grid(axis="y", color=RULE); ax.tick_params(labelsize=15)
ax.set_title("MPs born within 25 km of their seat (%)", loc="left", fontproperties=fp(22), color=INK, pad=12)
for x in be:
    if x["election"] in ("1832", "1950", "2005", "2024"):
        ax.annotate(f"{x['local_pc']:.0f}%  {x['election']}", (x["year"], x["local_pc"]), xytext=(0, 14), textcoords="offset points",
                    ha={"1832": "left", "2024": "right"}.get(x["election"], "center"), fontsize=15, fontfamily="IBM Plex Mono", color=INK)

# C: bonus by era
ax = fig.add_axes([0.42, 0.11, 0.30, 0.31])
rows = [("All years", M["h1_main"])] + [(nm, M[f"h1_era_{k}"]) for k, nm, *_ in ERAS]
for i, (lab, m) in enumerate(rows[::-1]):
    c = LOC if lab == "All years" else INK
    ax.plot([m["lo"], m["hi"]], [i, i], color=c, lw=4, solid_capstyle="round")
    ax.plot(m["b"], i, "o", ms=15, color=LOC, mec=BG, mew=2)
    ax.text(m["hi"] + 0.15, i, f"{m['b']:+.1f}", va="center", fontsize=16, fontfamily="IBM Plex Mono", color=INK)
ax.axvline(0, color=MUT, ls=(0, (4, 3)))
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=17); ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False); ax.tick_params(axis="x", labelsize=14); ax.set_xlim(-1.5, 4.5)
ax.set_xlabel("Extra points of vote share, within the same seat (95% CI)", fontsize=15)
ax.set_title("The local bonus", loc="left", fontproperties=fp(22), color=INK, pad=12)

# D: defeat rates
ax = fig.add_axes([0.79, 0.11, 0.18, 0.31])
v = [T["defeat_local_pc"], T["defeat_nonlocal_pc"]]
ax.bar([0, 1], v, color=[LOC, NON], width=0.62)
for i, x in enumerate(v):
    ax.text(i, x + 0.4, f"{x:.1f}%", ha="center", fontsize=19, fontfamily="IBM Plex Mono", color=INK)
ax.set_xticks([0, 1]); ax.set_xticklabels(["Born\nlocally", "Born\nelsewhere"], fontsize=16); ax.set_ylim(0, 20); ax.tick_params(axis="y", labelsize=14)
ax.set_title("Defeated when standing again", loc="left", fontproperties=fp(22), color=INK, pad=12)
ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)

fig.text(0.03, 0.025, "Data: Born and bred? (Wikidata, Wikipedia) and Who won here? (UK Parliament, House of Commons Library results). Seat and election by party fixed effects; contested single-member seats.",
         fontsize=14, color=MUT)
fig.text(0.97, 0.025, "maps.tristanhotham.com/local-mp-bonus", fontsize=16, color=INK, ha="right", fontfamily="IBM Plex Mono")
out = os.path.join(ROOT, "reddit", "local_mp_bonus_collage.png")
fig.savefig(out, dpi=100, facecolor=BG); plt.close(fig)
print(out)
