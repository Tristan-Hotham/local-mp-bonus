"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24092361, https://doi.org/10.5281/zenodo.24092361 and https://blog.tristanhotham.com/2026/10/31/local-mp-bonus/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from PIL import Image
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks (and rebuilds index.html)
R = jload(f"{DATA}/results.json"); T = R["T"]
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Local_MP_Bonus"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
early = [x["local_pc"] for x in R["by_election"] if x["year"] <= 2005 and x["n"] >= 40]
assert 17 < min(early) and max(early) < 33, (min(early), max(early))      # "about a quarter" for 1832 to 2005
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Does a local MP get a local bonus?",
        "slug": "local-mp-bonus",
        "excerpt": f"Parties now pick far more local candidates. Across every MP elected since 1832, being born near the seat wins about {T['bonus']:.1f} points more of the vote, but has not made local MPs any less likely to lose.",
        "seo_description": f"Do MPs born near their seat win more votes? {R['n']['returns']:,} MP returns since 1832: about {T['bonus']:.1f} points more, but no fewer defeats.",
        "tags": ["maps", "data visualisation", "elections", "MPs", "Parliament", "UK politics", "political history", "localness"],
        "header_alt": f"Title card reading 'Does a local MP get a local bonus?' beside a map of Great Britain with a dot for every constituency coloured by the share of its MPs born locally, and the line 'about {T['bonus']:.1f} points more of the vote, but no fewer defeats'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
OWN = ["panel.csv", "candidates_evermp.csv", "models.json", "review_checks.json", "results.json"]
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in OWN:
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("{,}", ",").replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("N=", "N = ")
zmeta = {"title": "Does a Local MP Get a Local Bonus? Birthplace and the Electoral Performance of UK Members of Parliament, 1832 to 2024",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/local-mp-bonus/}}.</p><p>Sources: Hotham (2026) Born and bred? (Wikidata CC0, English Wikipedia CC BY-SA 4.0) and Who won here? (UK Parliament and House of Commons Library results, Open Parliament Licence v3.0). Data CC BY-SA 4.0; text and figures CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["friends and neighbours voting", "candidate localness", "personal vote", "incumbency", "Members of Parliament", "British elections", "electoral history"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23763155", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.5281/zenodo.23761425", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2, keepdash=True)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
