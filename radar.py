import feedparser
from datetime import datetime, timezone

SOURCES = {
    "Google News - Europe security":
        "https://news.google.com/rss/search?q=Europe+security+military+war&hl=en-US&gl=US&ceid=US:en",

    "Google News - NATO":
        "https://news.google.com/rss/search?q=NATO+military&hl=en-US&gl=US&ceid=US:en",

    "Google News - Russia Europe":
        "https://news.google.com/rss/search?q=Russia+Europe+military&hl=en-US&gl=US&ceid=US:en",

    "Google News - Ukraine":
        "https://news.google.com/rss/search?q=Ukraine+Europe+attack&hl=en-US&gl=US&ceid=US:en",
}

KEYWORDS = [
    "attack",
    "war",
    "missile",
    "military",
    "troops",
    "mobilization",
    "invasion",
    "nato",
    "airspace",
    "cyberattack",
]

def analyze_title(title):
    title_lower = title.lower()

    matches = [
        keyword for keyword in KEYWORDS
        if keyword in title_lower
    ]

    return matches


def check_radar():

    now = datetime.now(timezone.utc)

    print("=" * 60)
    print("EU WAR RADAR V1")
    print(f"Kontrola: {now:%Y-%m-%d %H:%M:%S} UTC")
    print("=" * 60)

    total = 0

    for source_name, url in SOURCES.items():

        print(f"\n📡 {source_name}")

        feed = feedparser.parse(url)

        for article in feed.entries[:10]:

            title = article.get("title", "")
            matches = analyze_title(title)

            if matches:

                total += 1

                print(f"\n⚠️ {title}")
                print(f"Signály: {', '.join(matches)}")

    print("\n" + "=" * 60)
    print(f"Nalezeno relevantních zpráv: {total}")
    print("=" * 60)


if __name__ == "__main__":
    check_radar()