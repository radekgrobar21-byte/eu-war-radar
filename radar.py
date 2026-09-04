import feedparser
from collections import defaultdict
from datetime import datetime, timezone

SOURCES = {
    "Europe": "https://news.google.com/rss/search?q=Europe+security+military&hl=en-US&gl=US&ceid=US:en",
    "NATO": "https://news.google.com/rss/search?q=NATO+security+military&hl=en-US&gl=US&ceid=US:en",
    "Baltic Poland": "https://news.google.com/rss/search?q=Baltic+Poland+NATO&hl=en-US&gl=US&ceid=US:en",
    "Russia Europe": "https://news.google.com/rss/search?q=Russia+Europe+NATO&hl=en-US&gl=US&ceid=US:en",
    "Ukraine NATO": "https://news.google.com/rss/search?q=Ukraine+NATO+attack&hl=en-US&gl=US&ceid=US:en",
    "Critical infrastructure": "https://news.google.com/rss/search?q=Europe+critical+infrastructure+cyberattack&hl=en-US&gl=US&ceid=US:en",
}

HIGH_RISK = {
    "invasion": 15,
    "invaded": 15,
    "mobilization": 14,
    "mobilisation": 14,
    "missile strike": 14,
    "missile attack": 14,
    "airstrike": 12,
    "air strike": 12,
    "rocket attack": 12,
    "troops deployed": 10,
    "troop deployment": 10,
    "military escalation": 9,
    "airspace closed": 8,
    "airspace closure": 8,
    "cyberattack": 7,
    "cyber attack": 7,
}

MEDIUM_RISK = {
    "military buildup": 6,
    "military build-up": 6,
    "military alert": 6,
    "combat readiness": 6,
    "state of emergency": 5,
    "border incident": 5,
    "border clash": 5,
    "drone attack": 5,
    "drone strike": 5,
    "military exercise": 2,
    "military drill": 2,
    "nato exercise": 2,
}

LOW_RISK = {
    "military": 1,
    "war": 1,
    "attack": 2,
    "missile": 2,
    "troops": 1,
}

EU_NATO_CONTEXT = [
    "nato",
    "european union",
    "article 5",
    "poland",
    "estonia",
    "latvia",
    "lithuania",
    "finland",
    "sweden",
    "romania",
    "germany",
    "czechia",
    "czech republic",
    "slovakia",
    "france",
    "italy",
]

DIRECT_ATTACK = [
    "attack on nato",
    "attack on poland",
    "attack on estonia",
    "attack on latvia",
    "attack on lithuania",
    "attack on finland",
    "attack on sweden",
    "attack on romania",
    "attack on germany",
    "attack on czechia",
    "attack on czech republic",
    "article 5 invoked",
    "article 5 triggered",
]


def publisher_name(article):
    source = article.get("source", {})

    if hasattr(source, "get"):
        name = source.get("title", "")
        if name:
            return str(name).strip()

    title = article.get("title", "")

    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip()

    return "unknown"


def analyze_title(title):
    text = title.lower()

    score = 0
    matches = []

    for keyword, points in HIGH_RISK.items():
        if keyword in text:
            score += points
            matches.append(keyword)

    for keyword, points in MEDIUM_RISK.items():
        if keyword in text:
            score += points
            matches.append(keyword)

    for keyword, points in LOW_RISK.items():
        if keyword in text:
            score += points
            matches.append(keyword)

    context = any(term in text for term in EU_NATO_CONTEXT)
    direct = any(term in text for term in DIRECT_ATTACK)

    if context and score >= 4:
        score += 3
        matches.append("EU/NATO context")

    if direct:
        score += 12
        matches.append("DIRECT NATO/EU ATTACK SIGNAL")

    return min(score, 30), matches


def event_key(title, matches):
    text = title.lower()

    regions = []

    for region in [
        "poland",
        "baltic",
        "estonia",
        "latvia",
        "lithuania",
        "finland",
        "sweden",
        "romania",
        "moldova",
        "ukraine",
        "russia",
        "belarus",
        "nato",
        "europe",
        "germany",
        "czechia",
        "czech republic",
    ]:
        if region in text:
            regions.append(region)

    strong = []

    for match in matches:
        if match in HIGH_RISK or match in MEDIUM_RISK:
            strong.append(match)

    return (
        "|".join(sorted(set(regions)))
        + ":"
        + "|".join(sorted(set(strong)))
    )


def risk_level(score):

    if score <= 20:
        return "🟢 NORMÁLNÍ"

    if score <= 40:
        return "🟡 ZVÝŠENÉ NAPĚTÍ"

    if score <= 60:
        return "🟠 VÁŽNÁ SITUACE"

    if score <= 80:
        return "🔴 VYSOKÉ RIZIKO"

    return "🚨 MIMOŘÁDNÉ RIZIKO"


def check_radar():

    now = datetime.now(timezone.utc)

    print("=" * 70)
    print("🇪🇺 EU WAR RADAR V1.2")
    print("=" * 70)
    print(f"Kontrola: {now:%Y-%m-%d %H:%M:%S} UTC")
    print("Metoda: více zdrojů + závažnost + EU/NATO kontext")
    print()

    articles_seen = 0
    relevant = 0

    seen_titles = set()

    events = defaultdict(
        lambda: {
            "max_score": 0,
            "publishers": set(),
            "titles": [],
        }
    )

    for source_name, url in SOURCES.items():

        print(f"📡 {source_name}")

        feed = feedparser.parse(url)

        for article in feed.entries[:10]:

            title = article.get("title", "").strip()

            if not title:
                continue

            normalized = " ".join(title.lower().split())

            if normalized in seen_titles:
                continue

            seen_titles.add(normalized)

            articles_seen += 1

            score, matches = analyze_title(title)

            if score == 0:
                continue

            relevant += 1

            key = event_key(title, matches)

            events[key]["max_score"] = max(
                events[key]["max_score"],
                score
            )

            events[key]["publishers"].add(
                publisher_name(article)
            )

            events[key]["titles"].append(title)

    event_scores = []

    for event in events.values():

        score = event["max_score"]

        publisher_count = len(
            event["publishers"] - {"unknown"}
        )

        if publisher_count >= 2:
            score += 5

        if publisher_count >= 3:
            score += 5

        event_scores.append(
            (
                min(score, 40),
                publisher_count,
                event
            )
        )

    event_scores.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    final_score = 0

    weights = [
        1.0,
        0.55,
        0.35,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
    ]

    for index, (score, _, _) in enumerate(
        event_scores[:8]
    ):
        final_score += int(
            score * weights[index]
        )

    final_score = min(final_score, 100)

    print()
    print("=" * 70)
    print("📊 VÝSLEDEK RADARU")
    print("=" * 70)

    print(
        f"Článků zpracováno:     {articles_seen}"
    )

    print(
        f"Relevantních zpráv:    {relevant}"
    )

    print(
        f"Detekovaných událostí: {len(events)}"
    )

    print()

    print(
        f"RIZIKO:                {final_score} / 100"
    )

    print(
        f"STAV:                  {risk_level(final_score)}"
    )

    print()

    print("TOP UDÁLOSTI:")

    for index, (
        score,
        publisher_count,
        event
    ) in enumerate(
        event_scores[:5],
        1
    ):

        print(
            f"{index}. +{score} | "
            f"potvrzení: {publisher_count} zdrojů"
        )

        for title in event["titles"][:2]:

            print(
                f"   • {title}"
            )

    print()

    print(
        "Poznámka: Skóre není předpověď války."
    )

    print(
        "Je to indikátor množství a závažnosti "
        "veřejných bezpečnostních signálů."
    )

    print("=" * 70)


if __name__ == "__main__":
    check_radar()

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