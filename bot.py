import requests
import time
import random
from playwright.sync_api import sync_playwright

GAS_URL = "https://script.google.com/macros/s/AKfycby58waGTukYvm-CM2-CuGWW0uS0apyP2L4ILzrtmneyh4jZSDo_2XYVQKSIgFS4puqR/exec"

# -----------------------
# GAS 데이터 가져오기 (🔥 수정됨)
# -----------------------
def get_data():
    try:
        res = requests.get(GAS_URL, timeout=10)

        print("STATUS:", res.status_code)
        print("RESPONSE:", res.text[:300])  # 🔥 핵심 디버깅

        if res.status_code != 200:
            print("❌ GAS 요청 실패")
            return [], []

        try:
            data = res.json()
        except Exception as e:
            print("❌ JSON 파싱 실패:", e)
            return [], []

        giftcodes = data.get("giftcodes", [])
        players = data.get("players", [])

        print("Giftcodes:", giftcodes)
        print("Players:", players)

        return giftcodes, players

    except Exception as e:
        print("❌ GAS 연결 자체 실패:", e)
        return [], []


# -----------------------
# 딜레이
# -----------------------
def human_delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


# -----------------------
# JS 강제 클릭
# -----------------------
def js_click_by_text(page, text):
    page.evaluate(f"""
        [...document.querySelectorAll('button')]
        .find(btn => btn.innerText.includes('{text}'))?.click();
    """)


# -----------------------
# 안전 클릭
# -----------------------
def safe_click(page, text):
    try:
        page.click(f"text={text}", timeout=5000)
    except:
        js_click_by_text(page, text)


# -----------------------
# Redeem
# -----------------------
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


# -----------------------
# 실행
# -----------------------
def run():
    giftcodes, players = get_data()

    if not giftcodes or not players:
        print("❌ 데이터 없음 (GAS 문제 가능성 높음)")
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
