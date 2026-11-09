"""Step 6: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24092361, https://doi.org/10.5281/zenodo.24092361 and https://blog.tristanhotham.com/2026/10/31/local-mp-bonus/ stay as placeholders for the publisher. Also asserts every statement made in words."""
from common import *

R = jload(f"{DATA}/results.json"); M = R["M"]; T = R["T"]
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
# ---- facts stated in words (page, blog, paper), checked against the results ----
assert M["h1_main"]["lo"] > 0 and 1 <= M["h1_main"]["b"] < 2
assert all(M[f"h1_nat_{n}"]["lo"] > 0 for n in ("Eng", "Sco", "Wal"))
assert M["h1_fam_LAB"]["lo"] > 0 and M["h1_fam_LIB"]["lo"] > 0 and M["h1_fam_CON"]["lo"] < 0 < M["h1_fam_CON"]["b"] < M["h1_fam_LAB"]["b"]
assert all(M[k]["lo"] > 0 for k in ("h1_local10", "h1_local50", "h1_county", "h1_p19", "h1_ownpoint", "h1_noabroad", "h1_unknown",
                                     "h1_noseatfe", "h1_seatparty", "h1_tenure", "h1_cl_person", "h1_cl_twoway", "h1_drop2024", "h1_dropire"))
assert all(M[f"h1_dropnat_{n}"]["lo"] > 0 for n in ("Eng", "Sco", "Wal", "Ire")) and all(M[f"h1_dropera_{e}"]["lo"] > 0 for e in ("e1", "e2", "e3", "e4"))
assert M["h2_main"]["lo"] < 0 < M["h2_main"]["hi"] and M["h2_logit"]["lo"] < 0 < M["h2_logit"]["hi"]
assert abs(T["defeat_local_pc"] - T["defeat_nonlocal_pc"]) < 1.5 and T["terms_local"] <= T["terms_nonlocal"] + 0.2
assert M["h3_main"]["lo"] > 0 and M["h5_main"]["lo"] > 0 and M["h6_main"]["hi"] < 0
assert M["placebo_lead"]["lo"] < 0 < M["placebo_lead"]["hi"]
assert M["h1_era_e4"]["lo"] < 0 < M["h1_era_e4"]["b"] < min(M["h1_era_e1"]["b"], M["h1_era_e2"]["b"])
assert M["placebo_perm"]["p_two"] == 0 and abs(M["placebo_perm"]["mean"]) < 0.2
assert M["placebo_fakeseat_cond"]["lo"] < 0 < M["placebo_fakeseat_cond"]["hi"]
assert T["local_pc_2024"] > 40 and T["local_pc_2005"] < 30
bon = {"all": dict(b=M["h1_main"]["b"], lo=M["h1_main"]["lo"], hi=M["h1_main"]["hi"], local=R["local_share"]["all"]["pc"])}
for k, *_ in ERAS:
    m = M[f"h1_era_{k}"]; bon[k] = dict(b=round(m["b"], 3), lo=round(m["lo"], 3), hi=round(m["hi"], 3), local=round(R["local_share"][k]["pc"], 2))
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261109")
t = t.replace("{{BONUSJSON}}", json.dumps(bon))
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
