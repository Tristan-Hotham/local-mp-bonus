"""Shared paths, constants and helpers for the local-mp-bonus study ("Does a local MP get a local bonus?").

Inputs (read in place, never modified):
  MPL/mp_elections.csv  every MP returned at a UK general election 1832 to 2024 (Wikidata person and constituency item,
                        party family, birthplace distance to the seat point dist_km, local25, same_county ...)
  MPL/people.csv        one row per person: birthplace item, point, source and precision
  MPL/seats.csv         one row per constituency item: point and where the point came from
  ELE/contests.csv      every constituency contest 1832 to 2024 (election, constituency, Wikidata item, seats, uncontested)
  ELE/candidates.csv    every candidacy with votes, share (percent of the contest vote) and party family
  ELE/votes_by_family.csv  national vote share by party family and election
Sources: Hotham (2026) Born and Bred? (mp-localness) and Who won here? (elections-since-1832), see README.
Intermediates go to SCR, outside the repo.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MPL = os.environ.get("LMB_MPL", "/home/claude/src6/mp-localness/data")
ELE = os.environ.get("LMB_ELE", "/home/claude/src6/elections-since-1832/data")
GEO = os.environ.get("LMB_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("LMB_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("LMB_SCRATCH", "/home/claude/scratch/local-mp-bonus")
DATA = os.path.join(ROOT, "data")
for d in (DATA, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "local-mp-bonus"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
SEED = 20261109

ELECTIONS = ['1832', '1835', '1837', '1841', '1847', '1852', '1857', '1859', '1865', '1868', '1874', '1880',
             '1885', '1886', '1892', '1895', '1900', '1906', 'January 1910', 'December 1910', '1918', '1922',
             '1923', '1924', '1929', '1931', '1935', '1945', '1950', '1951', '1955', '1959', '1964', '1966',
             '1970', 'February 1974', 'October 1974', '1979', '1983', '1987', '1992', '1997', '2001', '2005',
             '2010', '2015', '2017', '2019', '2024']
EIDX = {e: i for i, e in enumerate(ELECTIONS)}
# elections at which a general redistribution of seats took effect (the pair ending at these spans new boundaries)
REDIST = {'1868', '1885', '1918', '1950', '1955', 'February 1974', '1983', '1997', '2005', '2010', '2024'}
ERAS = [("e1", "1832 to 1917", 1832, 1917), ("e2", "1918 to 1944", 1918, 1944),
        ("e3", "1945 to 2009", 1945, 2009), ("e4", "2010 to 2024", 2010, 2024)]
FAMNAME = {"CON": "Conservative", "LAB": "Labour", "LIB": "Liberal / Lib Dem", "SNP": "SNP", "PC": "Plaid Cymru",
           "LU": "Liberal Unionist", "IRN": "Irish Nationalist / SDLP", "ULS": "Ulster unionist", "SF": "Sinn Féin",
           "ALLY": "Allied (National Liberal etc.)", "PEEL": "Peelite", "REF": "Reform", "GRN": "Green", "OTH": "Other",
           "SPK": "Speaker"}


def era_of(year):
    for k, _, a, b in ERAS:
        if a <= year <= b:
            return k
    return None


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "s1": return f"{float(v):+.1f}"
    if f == "s2": return f"{float(v):+.2f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    if f == "p": return pval(v)
    if f == "f0": return f"{round(float(v))}"
    if f == "pc_frac": return f"{round(float(v) * 100)}%"
    if f == "pc_frac1": return f"{float(v) * 100:.1f}%"
    raise ValueError(f)


def pval(p):
    p = float(p)
    if p < 0.001: return "below 0.001"
    if p < 0.01: return f"{p:.3f}"
    return f"{p:.2f}"


def norm_tokens(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s).split()


TITLES = {"sir", "lord", "hon", "the", "rt", "dr", "mr", "mrs", "ms", "miss", "lady", "viscount", "earl", "marquess",
          "baron", "bt", "bart", "kc", "qc", "mp", "of", "captain", "major", "colonel", "general", "admiral", "rev",
          "reverend", "professor", "dame", "jr", "jnr", "junior", "senior", "de", "la", "le", "van", "von"}


def cand_parts(c):
    """'Surname, Forenames' -> (surname tokens, forename tokens) normalised."""
    c = re.sub(r"\(.*?\)", " ", str(c))
    if "," in c:
        a, b = c.split(",", 1)
    else:
        w = c.split(); a, b = (w[-1] if w else ""), " ".join(w[:-1])
    return [t for t in norm_tokens(a) if t not in TITLES] or norm_tokens(a), [t for t in norm_tokens(b) if t not in TITLES]
