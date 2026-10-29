from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen

from .protocol import decode_graph, encode_graph


def submit(url: str, envelope: dict) -> dict:
    payload = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    request = Request(
        url.rstrip("/") + "/v1/submit",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        body = json.loads(response.read())
    if type(body) is not dict or set(body) != {"graph"}:
        raise ValueError("service returned a non-fragment output envelope")
    graph = decode_graph(body["graph"])
    return {"graph": encode_graph(graph)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--request-file", required=True)
    args = parser.parse_args()
    envelope = json.loads(open(args.request_file, encoding="utf-8").read())
    print(json.dumps(submit(args.url, envelope), sort_keys=True))


if __name__ == "__main__":
    main()

