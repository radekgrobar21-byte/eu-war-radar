import feedparser
from datetime import datetime, timezone

SOURCES = {
    "Europe Security":
        "https://news.google.com/rss/search?q=Europe+security+military+war&hl=en-US&gl=US&ceid=US:en",

    "NATO":
        "https://news.google.com/rss/search?q=NATO+military+security&hl=en-US&gl=US&ceid=US:en",

    "Russia Europe":
        "https://news.google.com/rss/search?q=Russia+Europe+military&hl=en-US&gl=US&ceid=US:en",

    "Ukraine Europe":
        "https://news.google.com/rss/search?q=Ukraine+Europe+attack&hl=en-US&gl=US&ceid=US:en",
}

# Výrazy a jejich orientační závažnost
RISK_KEYWORDS = {
    "mobilization": 15,
    "mobilisation": 15,
    "invasion": 15,
    "missile attack": 15,
    "missile strike": 15,
    "major attack": 15,
    "airstrike": 12,
    "air strike": 12,
    "rocket attack": 12,
    "military attack": 12,
    "troops deployed": 10,
    "troop deployment": 10,
    "military escalation": 10,
    "military buildup": 8,
    "military build-up": 8,
    "airspace closed": 8,
    "airspace closure": 8,
    "cyberattack": 7,
    "cyber attack": 7,
    "military exercise": 3,
    "military drill": 3,
    "nato exercise": 3,
    "military": 1,
    "war": 2,
    "attack": 4,
    "missile": 5,
}

def analyze_title(title):
    text = title.lower()

    score = 0
    matches = []

    for keyword, points in RISK_KEYWORDS.items():
        if keyword in text:
            score += points
            matches.append((keyword, points))

    # Jedna zpráva nemůže sama vytvořit extrémní poplach
    score = min(score, 20)

    return score, matches


def risk_level(score):

    if score <= 20:
        return "🟢 NORMÁLNÍ"
    elif score <= 40:
        return "🟡 ZVÝŠENÉ NAPĚTÍ"
    elif score <= 60:
        return "🟠 VÁŽNÁ SITUACE"
    elif score <= 80:
        return "🔴 VYSOKÉ RIZIKO"
    else:
        return "🚨 MIMOŘÁDNÉ RIZIKO"


def check_radar():

    now = datetime.now(timezone.utc)

    print("=" * 60)
    print("🇪🇺 EU WAR RADAR V1.1")
    print("=" * 60)
    print(f"Kontrola: {now:%Y-%m-%d %H:%M:%S} UTC")
    print()

    total_articles = 0
    relevant_articles = 0
    total_score = 0

    processed_titles = set()

    for source_name, url in SOURCES.items():

        print(f"📡 {source_name}")

        feed = feedparser.parse(url)

        for article in feed.entries[:10]:

            title = article.get("title", "").strip()

            if not title:
                continue

            # Zabráníme započítání stejné zprávy několikrát
            normalized = title.lower()

            if normalized in processed_titles:
                continue

            processed_titles.add(normalized)
            total_articles += 1

            score, matches = analyze_title(title)

            if score > 0:

                relevant_articles += 1
                total_score += score

                print()
                print(f"⚠️ {title}")
                print(f"   Skóre: +{score}")

                if matches:
                    print(
                        "   Signály: "
                        + ", ".join(keyword for keyword, points in matches)
                    )

    # Celkové skóre omezíme na 100
    final_score = min(total_score, 100)

    print()
    print("=" * 60)
    print("📊 VÝSLEDEK RADARU")
    print("=" * 60)

    print(f"Celkem článků:       {total_articles}")
    print(f"Relevantních zpráv:  {relevant_articles}")
    print()
    print(f"RIZIKO:              {final_score} / 100")
    print(f"STAV:                {risk_level(final_score)}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    check_radar()