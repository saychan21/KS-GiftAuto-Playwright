import requests
import time
import random
from playwright.sync_api import sync_playwright

GAS_URL = "https://script.google.com/macros/s/AKfycby58waGTukYvm-CM2-CuGWW0uS0apyP2L4ILzrtmneyh4jZSDo_2XYVQKSIgFS4puqR/exec"

def get_data():
    res = requests.get(GAS_URL, timeout=10)
    data = res.json()
    return data.get("giftcodes", []), data.get("players", [])

def human_delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))

def js_click_by_text(page, text):
    page.evaluate(f"""
        [...document.querySelectorAll('button')]
        .find(btn => btn.innerText.includes('{text}'))?.click();
    """)

def safe_click(page, text):
    try:
        page.click(f"text={text}", timeout=5000)
    except:
        js_click_by_text(page, text)

def redeem(page, player_id, giftcode):
    page.goto("https://ks-giftcode.centurygame.com/", timeout=30000)

    page.wait_for_selector("input", timeout=10000)
    page.fill("input", player_id)

    human_delay()

    safe_click(page, "Login")

    human_delay(2, 4)

    page.wait_for_selector("input[placeholder='Enter Gift Code']", timeout=10000)
    page.fill("input[placeholder='Enter Gift Code']", giftcode)

    human_delay()

    safe_click(page, "Confirm")

    human_delay(2, 4)

def run():
    giftcodes, players = get_data()

    if not giftcodes or not players:
        print("No data")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        page = context.new_page()

        for code in giftcodes:
            for player in players:
                for retry in range(3):
                    try:
                        print(f"[TRY] {code} -> {player}")
                        redeem(page, player, code)
                        print(f"[SUCCESS] {code} -> {player}")
                        break
                    except Exception as e:
                        print(f"[ERROR] {e}")
                        time.sleep(3)

                human_delay(2, 5)

        browser.close()

if __name__ == "__main__":
    run()
