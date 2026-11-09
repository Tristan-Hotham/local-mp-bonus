"""Step 4: figures for the page (img/*.jpg), blog (release/blog/b_*.png, 1800 px), paper (release/paper/f_*.png, 300 dpi)
and header.png (1200 x 630). All numbers from data/results.json and data/panel.csv."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from shapely.geometry import shape
from common import *

for f in ("SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "FrauncesVar.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF, MONO = "Source Serif 4", "IBM Plex Mono"
SEMI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
def fp(size):
    f = SEMI.copy(); f.set_size(size); return f
BG, INK, MUT, RULE = "#FBF8F1", "#22201C", "#6B655B", "#E3DDD0"
LOC, NON, NEU = "#C2410C", "#3B6EA8", "#8A8478"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": BG, "figure.facecolor": BG, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.unicode_minus": False})
IMG, BLOG, PAP = f"{ROOT}/img", f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (IMG, BLOG, PAP):
    os.makedirs(d, exist_ok=True)
R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
P = pd.read_csv(f"{DATA}/panel.csv", dtype={"election": str})


def out(fig, name, page=True, blog=True, paper=True):
    fig.savefig(f"{SCR}/{name}.png", dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=86, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        im.save(f"{PAP}/f_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, s=None, y=0.975):
    fig.text(0.04, y, t, fontproperties=fp(17), color=INK, va="top")
    if s: fig.text(0.04, y - 0.055, s, fontsize=11.5, color=MUT, va="top")


def coef_rows(ax, rows, xlab, ref=0.0, main_col=LOC):
    """rows: list of (label, b, lo, hi, n, style) top to bottom"""
    y = np.arange(len(rows))[::-1]
    for yy, (lab, b, lo, hi, n, sty) in zip(y, rows):
        if sty == "head":
            ax.text(ax.get_xlim()[0] if False else 0, yy, "", fontsize=1)
            continue
        c = {"main": main_col, "plac": NEU}.get(sty, INK)
        ax.plot([lo, hi], [yy, yy], color=c, lw=2, solid_capstyle="round")
        ax.plot(b, yy, "o", ms=8 if sty == "main" else 6.5, color=c, mec=BG, mew=1.5, zorder=3)
    ax.axvline(ref, color=MUT, lw=1, ls=(0, (4, 3)), zorder=0)
    ax.set_yticks(y); ax.set_yticklabels([r[0] + (f"  (n={r[4]:,})" if r[4] else "") for r in rows], fontsize=10.5)
    for t_, r in zip(ax.get_yticklabels(), rows):
        if r[5] == "head":
            t_.set_fontproperties(SEMI); t_.set_fontsize(11); t_.set_color(INK)
        else:
            t_.set_color(INK if r[5] == "main" else MUT)
    ax.set_xlabel(xlab, fontsize=11); ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=RULE, lw=0.8); ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)


def r_(k, lab=None, sty="", scale=1.0):
    m = M[k]
    return (lab or m.get("label", k), scale * m["b"], scale * m["lo"], scale * m["hi"], m.get("n"), sty)


# ---------- 1. localness over time and the bonus by period ----------
fig = plt.figure(figsize=(11, 8.2))
title(fig, "More MPs are local than ever. Their vote bonus has not grown",
      "Top: share of MPs born within 25 km of their seat. Bottom: the extra vote share of local MPs, within the same seat, by period (95% CI; exploratory)")
ax1 = fig.add_axes([0.08, 0.55, 0.88, 0.3]); ax2 = fig.add_axes([0.08, 0.09, 0.88, 0.34])
be = [x for x in R["by_election"] if x["n"] >= 40]
ax1.plot([x["year"] for x in be], [x["local_pc"] for x in be], color=LOC, lw=2.2)
ax1.scatter([x["year"] for x in be], [x["local_pc"] for x in be], s=14, color=LOC, zorder=3, edgecolor=BG, lw=0.8)
ax1.set_ylim(0, 50); ax1.set_xlim(1828, 2028); ax1.set_ylabel("% of MPs born locally")
ax1.grid(axis="y", color=RULE); ax1.set_axisbelow(True)
for x in be:
    if x["election"] in ("1832", "2005", "2024"):
        ax1.annotate(f"{x['local_pc']:.0f}%", (x["year"], x["local_pc"]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=10, color=INK, fontfamily=MONO)
per = M["x_periods"]
xs = np.arange(len(per))
for i, p in enumerate(per):
    ax2.plot([i, i], [p["lo"], p["hi"]], color=INK, lw=2, solid_capstyle="round")
    ax2.plot(i, p["b"], "o", ms=8, color=LOC, mec=BG, mew=1.5, zorder=3)
    ax2.text(i, p["hi"] + 0.35, f"{p['b']:+.1f}", ha="center", fontsize=10, fontfamily=MONO, color=INK)
ax2.axhline(0, color=MUT, lw=1, ls=(0, (4, 3)))
ax2.axhline(M["h1_main"]["b"], color=LOC, lw=1, alpha=0.5)
ax2.text(5.5, M["h1_main"]["b"] - 0.3, f"all years {M['h1_main']['b']:+.1f}", ha="center", fontsize=9.5, color=LOC, fontfamily=MONO)
ax2.set_xticks(xs); ax2.set_xticklabels([f"{p['label']}\nn={p['n']:,}" for p in per], fontsize=9.5)
ax2.set_ylabel("Local bonus, points of vote share"); ax2.grid(axis="y", color=RULE); ax2.set_axisbelow(True)
fig.text(0.04, 0.012, "Seat fixed effects and election by party fixed effects; contested single-member seats; SE clustered by constituency. Periods are exploratory.", fontsize=9, color=MUT)
out(fig, "periods")

# ---------- 2. who gets it: era, nation, party ----------
rows = [("All MPs (main estimate)", M["h1_main"]["b"], M["h1_main"]["lo"], M["h1_main"]["hi"], M["h1_main"]["n"], "main"),
        ("Era", 0, 0, 0, None, "head")]
rows += [r_(f"h1_era_{k}", nm) for k, nm, a, b in ERAS]
rows += [("Nation", 0, 0, 0, None, "head")] + [r_(f"h1_nat_{n[:3]}", n) for n in ("England", "Scotland", "Wales", "Ireland/NI")]
rows += [("Party", 0, 0, 0, None, "head")] + [r_(f"h1_fam_{f}", FAMNAME[f]) for f in ("CON", "LAB", "LIB")]
fig = plt.figure(figsize=(11, 7.4))
title(fig, "Local MPs win a little more of the vote, almost everywhere",
      "Extra vote share (points) for an MP born within 25 km of the seat, against other MPs elected for the same seat, net of party performance")
ax = fig.add_axes([0.36, 0.14, 0.6, 0.72]); ax.set_xlim(-3, 8)
coef_rows(ax, rows, "Points of vote share (95% CI)")
fig.text(0.04, 0.015, "Each row a separate regression with seat and election by party fixed effects. Ireland before 1922 and Northern Ireland together.", fontsize=9, color=MUT)
out(fig, "groups")

# ---------- 3. designs ----------
fig = plt.figure(figsize=(11, 6.6))
title(fig, "Five ways to look for a local bonus",
      "Each design compares like with like in a different way; vote-share designs on the left, defeat on the right")
axa = fig.add_axes([0.33, 0.14, 0.38, 0.68]); axb = fig.add_axes([0.80, 0.14, 0.17, 0.68])
rowsA = [("Same seat, other MPs of the party", T["bonus"], T["bonus_lo"], T["bonus_hi"], M["h1_main"]["n"], "main"),
         ("Own change at re-election", T["swing"], T["swing_lo"], T["swing_hi"], M["h3_main"]["n"], ""),
         ("Hand-over to a local successor", T["succ"], T["succ_lo"], T["succ_hi"], M["h5_main"]["n"], ""),
         ("Party loss when a local MP retires", T["retire"], T["retire_lo"], T["retire_hi"], M["h6_main"]["n"], ""),
         ("Placebo: change before hand-over", M["placebo_lead"]["b"], M["placebo_lead"]["lo"], M["placebo_lead"]["hi"], M["placebo_lead"]["n"], "plac")]
axa.set_xlim(-2.5, 2.5); coef_rows(axa, rowsA, "Points of vote share")
y = np.arange(5)[::-1]
axb.plot([T["defeat_lo"], T["defeat_hi"]], [y[0], y[0]], color=INK, lw=2); axb.plot(T["defeat_pp"], y[0], "o", ms=7, color=INK, mec=BG)
axb.plot([100 * M["h2_logit"]["lo"], 100 * M["h2_logit"]["hi"]], [y[1], y[1]], color=INK, lw=2); axb.plot(100 * M["h2_logit"]["b"], y[1], "o", ms=7, color=INK, mec=BG)
axb.axvline(0, color=MUT, lw=1, ls=(0, (4, 3))); axb.set_ylim(axa.get_ylim()); axb.set_xlim(-4, 4)
axb.set_yticks(y[:2]); axb.set_yticklabels(["Defeated (LPM)", "Defeated (logit)"], fontsize=10.5, color=MUT); axb.tick_params(axis="y", length=0)
axb.set_xlabel("Points of probability"); axb.grid(axis="x", color=RULE); axb.set_axisbelow(True); axb.spines["left"].set_visible(False)
fig.text(0.04, 0.015, "95% CIs, SE clustered by constituency. Retirement row: the difference between local and non-local MPs in how much the party loses when they stand down.", fontsize=9, color=MUT)
out(fig, "designs")

# ---------- 4. robustness ----------
keys = [("h1_main", "Main specification", "main"), ("h1_noseatfe", "No seat fixed effects", ""), ("h1_seatparty", "Seat by party fixed effects", ""),
        ("h1_tenure", "Adding years in office", ""), ("h1_cl_person", "SE clustered by MP", ""), ("h1_cl_twoway", "SE two-way, seat and election", ""),
        ("h1_local10", "Born within 10 km", ""), ("h1_local50", "Born within 50 km", ""), ("h1_county", "Born in the seat's county", ""),
        ("h1_p19", "Wikidata birthplaces only", ""), ("h1_ownpoint", "Seats with their own coordinates", ""), ("h1_noabroad", "Without MPs born abroad", ""),
        ("h1_unknown", "All MPs, unknown birthplace kept", ""), ("h1_drop2024", "Without 2024", ""), ("h1_dropire", "Without Ireland before 1922", "")]
keys += [(f"h1_dropnat_{n}", f"Without {nm}", "") for n, nm in (("Eng", "England"), ("Sco", "Scotland"), ("Wal", "Wales"), ("Ire", "Ireland/NI"))]
rows = [r_(k, lab, s) for k, lab, s in keys]
rows.append(("Placebo: born near another seat", M["placebo_fakeseat_cond"]["mean"], M["placebo_fakeseat_cond"]["lo"], M["placebo_fakeseat_cond"]["hi"], None, "plac"))
fig = plt.figure(figsize=(11, 9.4))
title(fig, "The bonus survives every check", "Local bonus in points of vote share under alternative choices (95% CI)")
ax = fig.add_axes([0.38, 0.1, 0.58, 0.78]); ax.set_xlim(-1, 3.3)
coef_rows(ax, rows, "Points of vote share")
fig.text(0.04, 0.012, f"Placebo: localness to a randomly drawn other seat of the same nation, {M['placebo_fakeseat_cond']['draws']} draws, controlling for real localness (2.5th to 97.5th percentile).", fontsize=9, color=MUT)
out(fig, "robust")

# ---------- 5. placebo distributions (paper and page only) ----------
# draws are not stored; show summary intervals against the main estimate
fig = plt.figure(figsize=(11, 4.6))
title(fig, "Placebos sit at zero; the real estimate does not", "Coefficient on localness: the real one against placebo versions (2.5th to 97.5th percentile of draws)")
ax = fig.add_axes([0.38, 0.16, 0.58, 0.62]); ax.set_xlim(-1, 2.2)
rows = [("Real localness (main)", T["bonus"], T["bonus_lo"], T["bonus_hi"], M["h1_main"]["n"], "main"),
        ("Shuffled within election and party", M["placebo_perm"]["mean"], M["placebo_perm"]["mean"] - 1.96 * M["placebo_perm"]["sd"], M["placebo_perm"]["mean"] + 1.96 * M["placebo_perm"]["sd"], None, "plac"),
        ("Born near another seat (any)", M["placebo_fakeseat"]["mean"], M["placebo_fakeseat"]["lo"], M["placebo_fakeseat"]["hi"], None, "plac"),
        ("Born near another seat, 50 km+ away", M["placebo_fakeseat_far"]["mean"], M["placebo_fakeseat_far"]["lo"], M["placebo_fakeseat_far"]["hi"], None, "plac"),
        ("Another seat, with real localness", M["placebo_fakeseat_cond"]["mean"], M["placebo_fakeseat_cond"]["lo"], M["placebo_fakeseat_cond"]["hi"], None, "plac")]
coef_rows(ax, rows, "Points of vote share")
out(fig, "placebo", blog=False)

# ---------- 6. map: share of MPs born locally, by seat, two eras ----------
nat = jload(f"{MPL}/nations.geojson")["features"]
S = pd.read_csv(f"{MPL}/seats.csv").set_index("seat")
cm = LinearSegmentedColormap.from_list("loc", ["#F4E9DC", "#E9A66B", "#C2410C", "#6E2207"])
fig = plt.figure(figsize=(11, 8.6))
title(fig, "Where MPs are locally born", "Share of each seat's MPs born within 25 km of it (dots sized by number of MPs with a known birthplace)")
for j, (era, nm) in enumerate((("e3", "1945 to 2009"), ("e4", "2010 to 2024"))):
    ax = fig.add_axes([0.03 + 0.47 * j, 0.06, 0.46, 0.8])
    for f in nat:
        g = shape(f["geometry"])
        for poly in (g.geoms if hasattr(g, "geoms") else [g]):
            xy = np.asarray(poly.exterior.coords)
            ax.fill(xy[:, 0], xy[:, 1], fc="#EFEBE3", ec="#B9B2A5", lw=0.4)
    k = P[(P.era == era) & P.local25.notna() & (P.seat_nation != "Ireland")].groupby("seat").local25.agg(["mean", "size"])
    k = k.join(S[["lon", "lat"]]).dropna().sort_values("mean")
    ax.scatter(k.lon, k.lat, s=4 + 4 * np.sqrt(k["size"]), c=k["mean"], cmap=cm, vmin=0, vmax=1, edgecolor="white", lw=0.3, zorder=3)
    ax.set_xlim(-8.3, 2.0); ax.set_ylim(49.8, 60.9); ax.set_aspect(1 / np.cos(np.radians(55)))
    ax.axis("off")
    ax.text(-8.1, 60.5, nm, fontproperties=fp(15), color=INK)
    ax.text(-8.1, 60.05, f"{R['local_share'][era]['pc']:.0f}% of MPs born locally", fontsize=11, color=MUT, fontfamily=MONO)
cax = fig.add_axes([0.62, 0.08, 0.3, 0.018])
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 100)), cax=cax, orientation="horizontal")
cb.set_label("% of the seat's MPs born within 25 km", fontsize=10); cb.outline.set_visible(False)
out(fig, "map")

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.patch.set_facecolor(BG)
fig.text(0.05, 0.86, "DATA STUDY · 2026", fontsize=12, fontfamily=MONO, color=MUT)
fig.text(0.05, 0.70, "Does a local MP", fontproperties=fp(46), color=INK)
fig.text(0.05, 0.57, "get a local bonus?", fontproperties=fp(46), color=LOC)
fig.text(0.05, 0.43, f"{R['n']['returns']:,} MP returns, 1832 to 2024. Born within 25 km\nof the seat: about {T['bonus']:.1f} points more of the vote,\nbut no fewer defeats.", fontsize=17, color=INK, va="top", linespacing=1.4)
fig.text(0.05, 0.07, "Dr Tristan Hotham · maps.tristanhotham.com/local-mp-bonus", fontsize=11.5, fontfamily=MONO, color=MUT)
ax = fig.add_axes([0.66, 0.08, 0.31, 0.84]); ax.axis("off")
for f in nat:
    if f["properties"]["nation"] == "Ireland":
        continue
    g = shape(f["geometry"])
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        xy = np.asarray(poly.exterior.coords); ax.fill(xy[:, 0], xy[:, 1], fc="#EFEBE3", ec="#B9B2A5", lw=0.4)
k = P[(P.year >= 1945) & P.local25.notna() & (P.seat_nation != "Ireland")].groupby("seat").local25.agg(["mean", "size"]).join(S[["lon", "lat"]]).dropna().sort_values("mean")
ax.scatter(k.lon, k.lat, s=3 + 2 * np.sqrt(k["size"]), c=k["mean"], cmap=cm, vmin=0, vmax=1, edgecolor="white", lw=0.2)
ax.set_xlim(-8.3, 2.0); ax.set_ylim(49.8, 60.9); ax.set_aspect(1 / np.cos(np.radians(55)))
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=BG)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
