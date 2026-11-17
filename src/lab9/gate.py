"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems: list[str] = []
    graded = [m["id"] for m in spec.get("metrics", []) if m["id"] in GRADERS]
    for name, rep in (("PR", pr), ("baseline", base)):
        problems += [f"{name}: {p}" for p in _report_problems(rep, graded, spec)]
    problems += _same_population(pr, base)
    if base_spec is not None:
        problems += ratchet_problems(spec, base_spec)
    return problems


def _bad_number(v) -> bool:
    return isinstance(v, float) and not math.isfinite(v)


def _report_problems(rep: dict, graded: list[str], spec: dict) -> list[str]:
    """One report checked against itself: row shape, grader health, and that the summary numbers
    are the ones its rows produce (a hand-edited metrics block is not evidence)."""
    out: list[str] = []
    rows, man, metrics = rep.get("rows"), rep.get("manifest") or {}, rep.get("metrics")
    if not isinstance(rows, list) or not rows:
        return ["no rows"]
    if not isinstance(metrics, dict):
        return ["no metrics block"]
    out += [f"metric {k} is {v!r} (NaN/inf)" for k, v in metrics.items() if _bad_number(v)]
    seeds = list(man.get("seeds") or [])
    want = (man.get("items") or 0) * len(seeds)
    if len(rows) != want:
        out.append(f"{len(rows)} rows, manifest says {man.get('items')} items x {len(seeds)} seeds = {want}")
    keys = [(r.get("item_id"), r.get("seed")) for r in rows]
    dup = sorted({k for k in keys if keys.count(k) > 1}, key=str)
    if dup:
        out.append(f"{len(dup)} duplicated (item, seed) row(s), first {dup[0]}")
    stray = sorted({r.get("seed") for r in rows} - set(seeds), key=str)
    if stray:
        out.append(f"rows use seeds {stray} that are not in the manifest")
    n_items = len({r.get("item_id") for r in rows})
    if n_items != man.get("items"):
        out.append(f"{n_items} distinct items in rows, manifest says {man.get('items')}")
    if rep.get("evaluator_failures"):
        out.append(f"{len(rep['evaluator_failures'])} evaluator failure(s): a crashed grader is not a pass")
    for m in graded:
        bad = sum(1 for r in rows if not isinstance(r.get(m), bool))
        if bad:
            out.append(f"{bad} row(s) without a boolean value for graded metric {m}")
        if m not in metrics:
            out.append(f"graded metric {m} is absent from the metrics block")
    if not out:
        out += _recomputed_mismatch(rows, metrics, [m for m in graded if m in rows[0]], spec)
    return out


def _recomputed_mismatch(rows: list[dict], metrics: dict, graded: list[str], spec: dict) -> list[str]:
    has_cost = all("cost" in r for r in rows)
    try:
        again = aggregate([{"cost": 0.0, **r} for r in rows], graded, k_values=spec.get("pass_k", []))
    except Exception as exc:  # noqa: BLE001 - rows we cannot re-aggregate are untrusted
        return [f"cannot recompute metrics from rows ({type(exc).__name__})"]
    out = []
    for k, v in again.items():
        if k not in metrics or (k == "cost_per_success" and not has_cost):
            continue
        got = metrics[k]
        if v is None or got is None:
            if (v is None) != (got is None):
                out.append(f"metric {k} = {got!r} but its rows give {v}")
        elif isinstance(got, bool) or not isinstance(got, (int, float)) or abs(float(got) - float(v)) > 1e-3:
            out.append(f"metric {k} = {got!r} but its rows give {v}")
    return out


def _same_population(pr: dict, base: dict) -> list[str]:
    """The PR must be graded on exactly the baseline's (item, seed) cells, with the same slice tags."""
    out: list[str] = []
    pm, bm = pr.get("manifest") or {}, base.get("manifest") or {}
    if list(pm.get("seeds") or []) != list(bm.get("seeds") or []):
        out.append(f"seeds {pm.get('seeds')} differ from the baseline's {bm.get('seeds')}")
    if pm.get("items") != bm.get("items"):
        out.append(f"{pm.get('items')} items, the baseline has {bm.get('items')}")

    def cells(rep):
        return {(r.get("item_id"), r.get("seed")) for r in rep.get("rows") or []}

    a, b = cells(pr), cells(base)
    if a != b:
        out.append(f"(item, seed) set differs from the baseline: {len(b - a)} missing, {len(a - b)} extra")

    def tags(rep):
        seen: dict[str, set] = {}
        for r in rep.get("rows") or []:
            seen.setdefault(r.get("item_id"), set()).add(tuple(sorted(r.get("slices") or [])))
        return seen

    ta, tb = tags(pr), tags(base)
    if any(len(v) > 1 for v in ta.values()):
        out.append("an item carries different slice tags on different seeds")
    moved = sorted(i for i in set(ta) & set(tb) if ta[i] != tb[i])
    if moved:
        out.append(f"slice tags differ from the baseline on {len(moved)} item(s), first {moved[0]}")
    return out


def ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    """Same eval set => thresholds may only get stricter. Returns every loosening found."""
    same_set = (spec.get("eval_set_version") == base_spec.get("eval_set_version")
                or spec.get("eval_set") == base_spec.get("eval_set"))
    if not same_set:
        return []
    out: list[str] = []
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        out.append(f"RATCHET eval_set_version renamed {base_spec.get('eval_set_version')!r} -> "
                   f"{spec.get('eval_set_version')!r} on the same eval set")
    if spec.get("eval_set") != base_spec.get("eval_set") or spec.get("labels") != base_spec.get("labels"):
        out.append("RATCHET eval_set or labels path changed within one eval-set version")
    if list(spec.get("seeds") or []) != list(base_spec.get("seeds") or []):
        out.append(f"RATCHET seeds changed {base_spec.get('seeds')} -> {spec.get('seeds')}")
    dropped_k = sorted(set(base_spec.get("pass_k") or []) - set(spec.get("pass_k") or []))
    if dropped_k:
        out.append(f"RATCHET pass_k dropped {dropped_k}")
    bb, sb = base_spec.get("bootstrap") or {}, spec.get("bootstrap") or {}
    if float(sb.get("confidence", 0.95)) > float(bb.get("confidence", 0.95)):
        out.append(f"RATCHET bootstrap confidence raised {bb.get('confidence')} -> {sb.get('confidence')} (wider CI)")
    if sb.get("method", "percentile") != bb.get("method", "percentile"):
        out.append("RATCHET bootstrap method changed")
    cur = {m["id"]: m for m in spec.get("metrics") or []}
    for old in base_spec.get("metrics") or []:
        new = cur.get(old["id"])
        out += [f"RATCHET metric {old['id']}: {p}"
                for p in _looser(old, new, old.get("threshold") or {}, (new or {}).get("threshold") or {})]
    cur_sl = {(sl.get("name"), sl.get("metric")): sl for sl in spec.get("slices") or []}
    for old in base_spec.get("slices") or []:
        new = cur_sl.get((old.get("name"), old.get("metric")))
        out += [f"RATCHET slice {old.get('name')}/{old.get('metric')}: {p}" for p in _looser(old, new, old, new or {})]
    return out


def _looser(old: dict, new: dict | None, th_old: dict, th_new: dict) -> list[str]:
    if new is None:
        return ["removed"]
    out = []
    if old.get("blocking") and not new.get("blocking"):
        out.append("blocking -> non-blocking")
    if "max" in th_old and ("max" not in th_new or th_new["max"] > th_old["max"]):
        out.append(f"max {th_old['max']} -> {th_new.get('max')}")
    if "min" in th_old and ("min" not in th_new or th_new["min"] < th_old["min"]):
        out.append(f"min {th_old['min']} -> {th_new.get('min')}")
    if "max_increase" in th_old and ("max_increase" not in th_new or th_new["max_increase"] > th_old["max_increase"]):
        out.append(f"max_increase {th_old['max_increase']} -> {th_new.get('max_increase')}")
    if th_old.get("no_significant_drop") and not th_new.get("no_significant_drop"):
        out.append("no_significant_drop dropped")
    return out


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for sl in spec.get("slices") or []:
        name, metric = sl["name"], sl.get("metric", "pass_rate")
        sid = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, slice_name=name), per_item(base, metric, slice_name=name)
        verdict, note, val = "ok", "", None
        if not a:
            verdict = "missing"                    # an empty slice proves nothing; never a silent pass
        else:
            val = round(sum(a.values()) / len(a), 4)
            if ("min" in sl and val < sl["min"]) or ("max" in sl and val > sl["max"]):
                verdict = "fail"
            if sl.get("no_significant_drop"):
                keys = sorted(set(a) & set(b))
                if not keys:
                    verdict, note = "missing", "no items shared with the baseline"
                else:
                    d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                       n_resamples=bs.get("n_resamples", 1000),
                                                       rng=bs.get("rng", 2027),
                                                       confidence=bs.get("confidence", 0.95))
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    if hi < 0:
                        verdict = "fail"
        if verdict != "ok" and sl.get("blocking"):
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if sl.get("blocking") else "warn")
        th = {k: sl[k] for k in ("min", "max", "no_significant_drop") if k in sl}
        lines.append(f"  {sid:<34} {val!s:<8} n={len(a):<3} {json.dumps(th):<36} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
