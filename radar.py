from datetime import datetime, timezone

def check_radar():
    now = datetime.now(timezone.utc)

    print("=" * 50)
    print("EU WAR RADAR V1")
    print("=" * 50)
    print(f"Čas kontroly: {now:%Y-%m-%d %H:%M:%S} UTC")
    print()
    print("🟢 Radar je aktivní.")
    print("📡 Sběr zdrojů bude přidán v další verzi.")
    print("🤖 AI vyhodnocení bude přidáno později.")
    print()

if __name__ == "__main__":
    check_radar()