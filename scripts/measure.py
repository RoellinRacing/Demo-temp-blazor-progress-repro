"""Measure the native Blazor progress and German satellite requests in Chromium."""
import json
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

parser = ArgumentParser(description=__doc__)
parser.add_argument("url")
parser.add_argument("output", type=Path)
parser.add_argument("--chromium", help="Optional Chromium executable")
args = parser.parse_args()

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=args.chromium)
    result = {"browser": browser.version, "url": args.url, "runs": []}
    for cache_disabled, count in [(False, 3), (True, 2)]:
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": cache_disabled})
        requests, console_errors, failures = [], [], []
        cdp.on("Network.requestWillBeSent", lambda event: requests.append(event))
        cdp.on("Network.loadingFailed", lambda event: failures.append(event["errorText"]))
        page.on("pageerror", lambda error: console_errors.append(str(error)))
        for index in range(count):
            requests.clear()
            console_errors.clear()
            failures.clear()
            if index == 0:
                page.goto(args.url, wait_until="domcontentloaded")
            else:
                page.evaluate("sessionStorage.removeItem('blazor-progress-repro')")
                page.reload(wait_until="domcontentloaded")
            page.get_by_role("heading", name="Blazor startup completed").wait_for(timeout=30000)
            greetings = page.get_by_role("listitem").all_text_contents()
            assert greetings == ["Hallo!"] * 7, greetings
            trace, origin = page.evaluate("""() => [
                JSON.parse(sessionStorage.getItem('blazor-progress-repro')), performance.timeOrigin
            ]""")
            satellites = []
            for request in requests:
                path = urlsplit(request["request"]["url"]).path
                if path.startswith("/_framework/de/") and ".resources." in path:
                    satellites.append({"path": path, "timeMs": round(request["wallTime"] * 1000 - origin)})
            result["runs"].append({
                "cacheDisabled": cache_disabled,
                "iteration": index + 1,
                "trace": trace,
                "satelliteRequests": satellites,
                "pageErrors": list(console_errors),
                "networkFailures": list(failures),
            })
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(cache_disabled, index + 1, len(satellites),
                  [(entry["previous"], entry["current"]) for entry in trace if entry["decreased"]],
                  flush=True)
        context.close()
