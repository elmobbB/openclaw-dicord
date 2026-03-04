import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python scripts/test_openclaw.py "your prompt"')
        return 1
    prompt = " ".join(sys.argv[1:])
    base_url = os.getenv("OPENCLAW_API_URL", "http://localhost:8000").rstrip("/")
    url = f"{base_url}/openclaw"
    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        print(f"HTTP {exc.code}: {detail}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
