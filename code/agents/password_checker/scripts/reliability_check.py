#!/usr/bin/env python3
import argparse
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.request


def call_score(base_url, password, components):
    payload = {"password": password}
    if components is not None:
        payload["components"] = components
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body), resp.status
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read().decode("utf-8")), exc.code


def get_component(detail, name):
    for comp in detail.get("components", []):
        if comp.get("name") == name:
            return comp
    return None


def describe(scores):
    if not scores:
        return {"count": 0}
    return {
        "count": len(scores),
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "min": min(scores),
        "max": max(scores),
        "stdev": round(statistics.pstdev(scores), 2) if len(scores) > 1 else 0.0,
    }


def bucketize(scores):
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for score in scores:
        if score <= 20:
            buckets["0-20"] += 1
        elif score <= 40:
            buckets["21-40"] += 1
        elif score <= 60:
            buckets["41-60"] += 1
        elif score <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1
    return buckets


def rank(values):
    sorted_vals = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0] * len(values)
    i = 0
    while i < len(sorted_vals):
        j = i
        while j + 1 < len(sorted_vals) and sorted_vals[j + 1][1] == sorted_vals[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[sorted_vals[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman(xs, ys):
    if len(xs) < 2:
        return 0.0
    rx = rank(xs)
    ry = rank(ys)
    mean_rx = statistics.mean(rx)
    mean_ry = statistics.mean(ry)
    num = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    den_x = math.sqrt(sum((a - mean_rx) ** 2 for a in rx))
    den_y = math.sqrt(sum((b - mean_ry) ** 2 for b in ry))
    return 0.0 if den_x == 0 or den_y == 0 else round(num / (den_x * den_y), 3)


def generate_samples(seed):
    random.seed(seed)

    weak_common = [
        "password",
        "123456",
        "123456789",
        "qwerty",
        "abc123",
        "111111",
        "123123",
        "letmein",
        "welcome",
        "iloveyou",
        "admin",
        "login",
        "princess",
        "qwerty123",
        "football",
        "monkey",
        "dragon",
        "sunshine",
        "master",
        "hello",
    ]

    weak_patterns = [
        "abcdef",
        "abcd1234",
        "1234",
        "000000",
        "999999",
        "aaaaaa",
        "aaaaaaa1",
        "qwertyuiop",
        "1q2w3e4r",
        "1234567890",
        "password1",
        "passw0rd",
        "aaaa1111",
        "abcabc",
        "abcabc123",
        "P@ssw0rd",
        "letmein123",
        "football1",
        "iloveyou2",
        "summer",
    ]

    words = [
        "Blue",
        "Moon",
        "Rain",
        "Cedar",
        "Mango",
        "Rocket",
        "Quartz",
        "Silver",
        "Forest",
        "Shadow",
    ]

    symbols = ["!", "@", "#", "$", "%"]

    medium = []
    for _ in range(20):
        word = random.choice(words)[:4]
        year = random.choice(["23", "24", "25"])
        symbol = random.choice(symbols)
        medium.append(f"{word}{year}{symbol}")

    strong_random = []
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    for _ in range(20):
        strong_random.append("".join(random.choice(charset) for _ in range(10)))

    strong_structured = []
    for _ in range(10):
        w1 = random.choice(words)[:2]
        w2 = random.choice(words)[:2]
        digits = random.choice(["47", "82", "93", "58"])
        symbol = random.choice(symbols)
        strong_structured.append(f"{w1}{w2}{digits}{symbol}Xy")

    long_over = ["".join(random.choice(charset) for _ in range(20)) for _ in range(6)]

    return {
        "weak_common": weak_common,
        "weak_patterns": weak_patterns,
        "medium": medium,
        "strong_random": strong_random,
        "strong_structured": strong_structured,
        "overlength": long_over,
    }


def analyze_group(base_url, passwords, components):
    scores = []
    pass_gpt_scores = []
    zxcvbn_scores = []
    diffs = []
    lengths = []
    bad = 0
    for password in passwords:
        data, status = call_score(base_url, password, components)
        if status != 200:
            bad += 1
            continue
        scores.append(data["normalized_score"])
        lengths.append(len(password))
        comp_pass = get_component(data, "pass_gpt")
        comp_zx = get_component(data, "zxcvbn")
        if comp_pass:
            pass_gpt_scores.append(comp_pass["normalized_score"])
        if comp_zx:
            zxcvbn_scores.append(comp_zx["normalized_score"])
        if comp_pass and comp_zx:
            diffs.append(comp_pass["normalized_score"] - comp_zx["normalized_score"])
    return {
        "overall": describe(scores),
        "pass_gpt": describe(pass_gpt_scores),
        "zxcvbn": describe(zxcvbn_scores),
        "buckets": bucketize(scores),
        "bad": bad,
        "len_corr": spearman(lengths, scores),
        "diff_mean": round(statistics.mean(diffs), 2) if diffs else 0.0,
        "raw_scores": scores,
    }


def main():
    parser = argparse.ArgumentParser(description="Reliability evaluation for the password strength system.")
    parser.add_argument("--base-url", default="http://localhost:9000/score")
    parser.add_argument(
        "--components",
        default="pass_gpt,zxcvbn",
        help="Comma-separated component list (omit or set to 'all' for aggregator defaults).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--with-hibp", action="store_true", help="Include a small HIBP sample.")
    parser.add_argument("--json", dest="json_path", help="Write full results to a JSON file.")
    args = parser.parse_args()

    components = None
    if args.components and args.components.lower() != "all":
        components = [c.strip() for c in args.components.split(",") if c.strip()]

    samples = generate_samples(args.seed)

    print("=== Reliability evaluation ===")
    results = {}
    for name, passwords in samples.items():
        if name == "overlength":
            continue
        stats = analyze_group(args.base_url, passwords, components)
        results[name] = stats
        print(f"{name}: overall={stats['overall']} len_rho={stats['len_corr']} diff_mean={stats['diff_mean']}")
        print(f"  buckets={stats['buckets']}")

    if all(key in results for key in ("weak_common", "weak_patterns", "medium", "strong_random")):
        weak_mean = results["weak_common"]["overall"].get("mean")
        pattern_mean = results["weak_patterns"]["overall"].get("mean")
        medium_mean = results["medium"]["overall"].get("mean")
        strong_mean = results["strong_random"]["overall"].get("mean")
        if all(v is not None for v in [weak_mean, pattern_mean, medium_mean, strong_mean]):
            print("Ordering check: weak_common < weak_patterns < medium < strong_random")
            print(
                f"  weak_common={weak_mean} weak_patterns={pattern_mean} medium={medium_mean} strong_random={strong_mean}"
            )

    print("\n=== Component agreement (pass_gpt vs zxcvbn) ===")
    disagreements = []
    for name, passwords in samples.items():
        if name == "overlength":
            continue
        for password in passwords:
            data, status = call_score(args.base_url, password, components)
            if status != 200:
                continue
            comp_pass = get_component(data, "pass_gpt")
            comp_zx = get_component(data, "zxcvbn")
            if not comp_pass or not comp_zx:
                continue
            diff = comp_pass["normalized_score"] - comp_zx["normalized_score"]
            disagreements.append((abs(diff), diff, password, comp_pass["normalized_score"], comp_zx["normalized_score"]))

    disagreements.sort(reverse=True)
    print("Top 8 disagreements (abs diff):")
    for entry in disagreements[:8]:
        _, diff, password, pass_score, zx_score = entry
        print(f"  {password!r}: pass_gpt={pass_score} zxcvbn={zx_score} diff={diff}")

    print("\n=== Overlength behavior (>16 chars) ===")
    over_scores = []
    for password in samples["overlength"]:
        data, status = call_score(args.base_url, password, components)
        if status == 200:
            over_scores.append(data["normalized_score"])
    if over_scores:
        print(f"overlength count={len(over_scores)} avg={round(statistics.mean(over_scores),2)}")
    else:
        print("overlength count=0")

    if args.with_hibp:
        print("\n=== Small HIBP sample (full aggregator) ===")
        hibp_subset = samples["weak_common"][:6] + samples["strong_random"][:6]
        for password in hibp_subset:
            data, status = call_score(args.base_url, password, None)
            if status != 200:
                continue
            print(f"  {password!r}: {data['normalized_score']}")

    print("\n=== Repeatability ===")
    repeat_targets = [samples["weak_patterns"][0], samples["strong_random"][0]]
    for password in repeat_targets:
        scores = []
        for _ in range(3):
            data, status = call_score(args.base_url, password, components)
            scores.append((status, data.get("normalized_score")))
            time.sleep(0.1)
        unique = len(set(scores))
        print(f"  {password!r}: {scores} unique={unique}")

    if args.json_path:
        payload = {
            "components": components,
            "results": {k: {**v, "raw_scores": v.get("raw_scores", [])} for k, v in results.items()},
        }
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\nWrote JSON report to {args.json_path}")


if __name__ == "__main__":
    main()
