import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_JS = ROOT / "data.js"
OUTPUT = ROOT / "data" / "bl-observations.json"
API_URL = "https://seti.berkeley.edu/opendata/api/query-files"

DEFAULT_RADIUS_DEG = 0.2
DEFAULT_LIMIT_PER_HOST = 80
DEFAULT_MAX_HOSTS = 80


def parse_existing_targets():
    if not DATA_JS.exists():
        return []
    text = DATA_JS.read_text(encoding="utf-8")
    match = re.search(r"window\.EXOPLANETS_DATA\s*=\s*(\[.*\]);\s*$", text, re.S)
    if not match:
        raise ValueError(f"Could not parse {DATA_JS}")
    rows = json.loads(match.group(1))
    hosts = {}
    for row in rows:
        host = row.get("hostname")
        ra = row.get("ra")
        dec = row.get("dec")
        distance = row.get("distance_ly")
        if not host or not isinstance(ra, (int, float)) or not isinstance(dec, (int, float)):
            continue
        key = normalize_name(host)
        current = hosts.get(key)
        priority = row.get("target_priority", 9)
        if current is None or (priority, distance or math.inf) < (current["target_priority"], current["distance_ly"]):
            hosts[key] = {
                "hostname": host,
                "ra": ra,
                "dec": dec,
                "distance_ly": distance or math.inf,
                "target_priority": priority,
            }
    return sorted(hosts.values(), key=lambda item: (item["target_priority"], item["distance_ly"], item["hostname"]))


def normalize_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def parse_utc(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def decimal_year(dt):
    if dt is None:
        return None
    start = datetime(dt.year, 1, 1, tzinfo=timezone.utc)
    end = datetime(dt.year + 1, 1, 1, tzinfo=timezone.utc)
    return dt.year + ((dt - start).total_seconds() / (end - start).total_seconds())


def query_host(host, radius_deg, limit):
    params = {
        "target": "",
        "pos-ra": f"{host['ra']:.7f}",
        "pos-dec": f"{host['dec']:.7f}",
        "pos-rad": f"{radius_deg:.4f}",
        "limit": str(limit),
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "signal-window-metadata/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("result") != "success":
        raise RuntimeError(payload.get("message") or f"API query failed for {host['hostname']}")
    return payload.get("data", [])


def observation_key(record):
    return (
        record.get("target"),
        record.get("telescope"),
        round(float(record.get("mjd") or 0), 6),
        round(float(record.get("center_freq") or 0), 6),
        record.get("file_type"),
    )


def compact_records(host, records):
    grouped = {}
    for record in records:
        key = observation_key(record)
        utc_dt = parse_utc(record.get("utc"))
        normalized = {
            "source_host": host["hostname"],
            "source_ra": host["ra"],
            "source_dec": host["dec"],
            "target_name": record.get("target"),
            "telescope": record.get("telescope"),
            "utc": utc_dt.isoformat().replace("+00:00", "Z") if utc_dt else record.get("utc"),
            "mjd": record.get("mjd"),
            "observation_year": decimal_year(utc_dt),
            "ra": record.get("ra"),
            "dec": record.get("decl"),
            "center_freq_mhz": record.get("center_freq"),
            "file_type": record.get("file_type"),
            "quality": record.get("quality"),
            "size_bytes": record.get("size"),
            "sample_file_url": record.get("url"),
            "file_count": 1,
            "api_id": record.get("id"),
        }
        if key not in grouped:
            grouped[key] = normalized
        else:
            grouped[key]["file_count"] += 1
            grouped[key]["size_bytes"] = (grouped[key].get("size_bytes") or 0) + (record.get("size") or 0)
    return list(grouped.values())


def main():
    max_hosts = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_HOSTS
    hosts = parse_existing_targets()[:max_hosts]
    observations = []
    errors = []

    for index, host in enumerate(hosts, start=1):
        try:
            records = query_host(host, DEFAULT_RADIUS_DEG, DEFAULT_LIMIT_PER_HOST)
            compacted = compact_records(host, records)
            observations.extend(compacted)
            print(f"[{index}/{len(hosts)}] {host['hostname']}: {len(compacted)} observation groups")
        except Exception as exc:
            errors.append({"hostname": host["hostname"], "error": str(exc)})
            print(f"[{index}/{len(hosts)}] {host['hostname']}: {exc}", file=sys.stderr)
        time.sleep(0.15)

    observations.sort(key=lambda item: (item["source_host"], item.get("mjd") or 0))
    payload = {
        "source": "Breakthrough Listen Open Data Archive API",
        "source_url": API_URL,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query": {
            "method": "RA/Dec cone search against hosts from data.js",
            "radius_deg": DEFAULT_RADIUS_DEG,
            "limit_per_host": DEFAULT_LIMIT_PER_HOST,
            "max_hosts": max_hosts,
        },
        "observations": observations,
        "errors": errors,
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(observations)} grouped observations to {OUTPUT}")
    if errors:
        print(f"{len(errors)} host queries had errors; see payload.errors", file=sys.stderr)


if __name__ == "__main__":
    main()
