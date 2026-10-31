"""Measure one cold load of the app on Chrome's "Fast 4G" network setting."""
import time

# DevTools' Fast 4G: 9 Mbit/s down, 1.5 Mbit/s up, 165 ms delay.
FAST_4G = {"offline": False, "latency": 165, "downloadThroughput": 9_000_000 / 8, "uploadThroughput": 1_500_000 / 8}


def measure_page(page, url, wait_until_ready):
    """Return (bytes over the network, seconds until the first pair shows, bytes per file)."""
    session = page.context.new_cdp_session(page)
    urls, sizes = {}, {}
    session.on("Network.responseReceived", lambda event: urls.__setitem__(event["requestId"], event["response"]["url"]))
    session.on("Network.loadingFinished", lambda event: sizes.__setitem__(event["requestId"], event["encodedDataLength"]))
    session.send("Network.enable")
    session.send("Network.setCacheDisabled", {"cacheDisabled": True})
    session.send("Network.emulateNetworkConditions", FAST_4G)
    start = time.perf_counter()
    page.goto(url)
    wait_until_ready(page)
    seconds = time.perf_counter() - start
    page.wait_for_load_state("networkidle")
    by_file = {urls.get(key, key): value for key, value in sizes.items()}
    return sum(sizes.values()), seconds, by_file
