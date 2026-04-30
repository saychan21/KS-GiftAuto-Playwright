import requests
import time
import random
import os
from playwright.sync_api import sync_playwright

CSV_URL = "https://docs.google.com/spreadsheets/d/1c2QmtlaBNsQ32j7JWly-ayigbkmfireBUisUEzxaJTY/export?format=csv&gid=561406276"

# -----------------------
# CSV 데이터 가져오기 (🔥 핵심 수정)
# -----------------------
def get_data():
    try:
        res = requests.get(CSV_URL, timeout=10)

        if res.status_code != 200:
            print("❌ CSV 요청 실패")
            return [], []

        lines = res.text.splitlines()

        giftcodes = []
        players = []

        for row in lines[1:]:
            cols = row.split(",")

            # A열 → GiftCode
            if len(cols) >= 1 and cols[0].strip():
                giftcodes.append(cols[0].strip())

            # B열 → Player
            if len(cols) >= 2 and cols[1].strip():
                players.append(cols[1].strip())

        # 중복 제거
        giftcodes = list(set(giftcodes))
        players = list(set(players))

        print("Giftcodes:", giftcodes)
        print("Players:", players)

        return giftcodes, players

    except Exception as e:
        print("❌ CSV 처리 실패:", e)
        return [], []


# -----------------------
# 딜레이
# -----------------------
def human_delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


# -----------------------
# 클릭
# -----------------------
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


# -----------------------
# Redeem (스크린샷 유지)
# -----------------------
def redeem(page, player_id, giftcode, step_id):
    base = f"screenshots/{step_id}"

    page.goto("https://ks-giftcode.centurygame.com/")
    page.screenshot(path=f"{base}_1_home.png")

    page.wait_for_selector("input")
    page.fill("input", player_id)
    page.screenshot(path=f"{base}_2_player.png")

    human_delay()

    safe_click(page, "Login")
    human_delay(2, 4)
    page.screenshot(path=f"{base}_3_login.png")

    page.wait_for_selector("input[placeholder='Enter Gift Code']")
    page.fill("input[placeholder='Enter Gift Code']", giftcode)
    page.screenshot(path=f"{base}_4_code.png")

    human_delay()

    safe_click(page, "Confirm")
    human_delay(2, 4)
    page.screenshot(path=f"{base}_5_done.png")


# -----------------------
# 실행 (🔥 핵심 변경)
# -----------------------
def run():
    giftcodes, players = get_data()

    if not giftcodes or not players:
        print("❌ 데이터 없음")
        return

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        step = 0

        # 🔥 모든 조합 실행
        for code in giftcodes:
            for player in players:
                step += 1

                for retry in range(3):
                    try:
                        print(f"[TRY] {code} -> {player}")

                        redeem(page, player, code, step)

                        print(f"[SUCCESS] {code} -> {player}")
                        break

                    except Exception as e:
                        print(f"[ERROR] {e}")
                        time.sleep(3)

                human_delay(2, 5)

        browser.close()


if __name__ == "__main__":
    run()
