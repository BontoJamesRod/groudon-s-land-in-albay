"""TC-050: measure the first view on Fast 4G, with real map tiles, at both screen sizes.

Run from the project folder:
    python pipeline/reports/measure_first_view.py

It serves site/ locally, so the time doesn't include a real host's distance, and files
aren't compressed the way a real host compresses them. Takes the median of 3 cold loads.
"""
import functools
import http.server
import json
import statistics
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPORTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPORTS.parent / "tests" / "e2e"))

from pipeline_first_view import measure_page

SITE = REPORTS.parents[1] / "site"
SIZES = {"1280 px": (1280, 800), "360 px": (360, 740)}
RUNS = 3


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def ready(page):
    page.wait_for_function("document.getElementById('pair-label').textContent !== ''")
    page.wait_for_function("document.getElementById('loading').hidden")


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(SITE)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    results = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, (width, height) in SIZES.items():
            runs = []
            for _ in range(RUNS):
                page = browser.new_context(viewport={"width": width, "height": height}).new_page()
                size, seconds, files = measure_page(page, url, ready)
                runs.append((size, seconds, files))
                page.context.close()
            own = sum(value for key, value in runs[-1][2].items() if key.startswith(url))
            largest = sorted(((value, key.replace(url, "")[:60]) for key, value in runs[-1][2].items()), reverse=True)[:5]
            results[name] = {"median_mb": round(statistics.median(run[0] for run in runs) / 1e6, 2),
                             "median_seconds": round(statistics.median(run[1] for run in runs), 2),
                             "own_files_mb": round(own / 1e6, 2), "tiles_mb": round((runs[-1][0] - own) / 1e6, 2),
                             "largest": largest}
        browser.close()
    server.shutdown()
    (REPORTS / "first-view-performance.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
