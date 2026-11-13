"""Post new items from RSS/Atom feeds and a few JSON APIs to Discord channels via webhooks. Run on a schedule."""
import html, json, os, re, sys, time
import feedparser, requests

MAX_PER_FEED = 3       # newest N per feed per run; the rest are marked seen so busy feeds can't flood
KEEP_SEEN = 300        # older ids remembered per feed, on top of everything currently in the feed
DRY_RUN = os.getenv("DRY_RUN") == "1"
UA = "Mozilla/5.0 (discord-news-bot)"
REPO = os.getenv("GITHUB_REPOSITORY")  # owner/name, set by GitHub Actions; used for avatar URLs
REDDIT_GAP = 65        # seconds; Reddit allows about 1 logged-out request per minute
last_reddit = 0.0

# Sources without RSS. Each turns the API's JSON into (title, link, id) items, newest first.
JSON_SOURCES = {
    "https://openrouter.ai/api/v1/models": lambda d: [
        {"id": m["id"], "title": f"New model: {m['name']}", "link": f"https://openrouter.ai/{m['id']}"}
        for m in sorted(d["data"], key=lambda m: m.get("created", 0), reverse=True)
        if ":" not in m["id"]  # skip :free / :batch variants of the same model
    ],
    "https://huggingface.co/api/daily_papers": lambda d: [
        {"id": p["paper"]["id"], "title": p["title"], "link": f"https://huggingface.co/papers/{p['paper']['id']}"}
        for p in d
    ],
}


def fetch(url):
    """Return (source name, items) or raise."""
    global last_reddit
    if "reddit.com" in url:
        time.sleep(max(0, last_reddit + REDDIT_GAP - time.time()))
        last_reddit = time.time()
    if url in JSON_SOURCES:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        r.raise_for_status()
        return url.split("/")[2], JSON_SOURCES[url](r.json())
    parsed = feedparser.parse(url, agent=UA)
    if parsed.get("status", 200) >= 400 or not parsed.entries:  # e.g. Reddit 429; an empty result must not be saved as "seen"
        raise RuntimeError(f"HTTP {parsed.get('status')}, {parsed.get('bozo_exception', 'no items')}")
    return parsed.feed.get("title", url), parsed.entries


def item_id(e):
    return e.get("id") or e.get("link") or e.get("title")


def title_of(e):
    # Bluesky/Mastodon posts have no title, only text
    text = e.get("title") or re.sub(r"<[^>]+>", "", e.get("summary", "")) or "New post"
    text = " ".join(html.unescape(text).split())
    return text if len(text) <= 250 else text[:247] + "..."


def post(webhook, entry, source, avatar):
    msg = f"**{title_of(entry)}**\n<{source}> · {entry.get('link', '')}"
    if DRY_RUN:
        print("  would post:", msg.replace("\n", " | "))
        return
    # allowed_mentions: a feed title containing @everyone must not ping the server
    body = {"content": msg[:2000], "allowed_mentions": {"parse": []}}
    if avatar:
        body["avatar_url"] = avatar
    for _ in range(3):
        r = requests.post(webhook, json=body, timeout=20)
        if r.status_code == 429:  # Discord rate limit
            time.sleep(float(r.json().get("retry_after", 2)))
            continue
        r.raise_for_status()
        time.sleep(1)
        return


def main():
    feeds = json.load(open("feeds.json", encoding="utf-8"))
    seen = json.load(open("seen.json", encoding="utf-8")) if os.path.exists("seen.json") else {}
    failed = total = 0
    for group in feeds:
        webhook = os.getenv(group["webhook_secret"])  # each secret is passed by name in news.yml
        if not webhook and not DRY_RUN:
            print(f"skip {group['channel']}: secret {group['webhook_secret']} not set")
            continue
        slug = group["channel"].lstrip("#")  # avatars/<channel>.png, served from this repo on GitHub
        avatar = (f"https://raw.githubusercontent.com/{REPO}/main/avatars/{slug}.png"
                  if REPO and os.path.exists(f"avatars/{slug}.png") else None)
        for url in group["feeds"]:
            total += 1
            try:
                source, entries = fetch(url)
            except Exception as ex:
                print(f"FAIL {url}: {ex}")
                failed += 1
                continue
            ids = [item_id(e) for e in entries]
            first_run = url not in seen
            old = set(seen.get(url, []))
            new = [e for e, i in zip(entries, ids) if i not in old]
            print(f"{group['channel']} {url}: {len(new)} new{' (first run, seeding only)' if first_run else ''}")
            if not first_run:  # first run only remembers items, so the channel isn't flooded with old news
                for e in reversed(new[:MAX_PER_FEED]):  # oldest first
                    try:
                        post(webhook, e, source, avatar)
                    except requests.RequestException as ex:
                        print(f"  post failed: {ex}")
                        failed += 1
            current = set(ids)  # keep every id still in the feed, or huge feeds (OpenAI: 1000+ items) would repost old ones
            seen[url] = ids + [i for i in seen.get(url, []) if i not in current][:KEEP_SEEN]
    if not DRY_RUN:
        json.dump(seen, open("seen.json", "w", encoding="utf-8"), indent=0)
    sys.exit(1 if total and failed >= total else 0)


if __name__ == "__main__":
    main()
