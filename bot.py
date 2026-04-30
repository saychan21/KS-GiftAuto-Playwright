import requests
import time
import random
import os
from playwright.sync_api import sync_playwright

CSV_URL = "https://docs.google.com/spreadsheets/d/1c2QmtlaBNsQ32j7JWly-ayigbkmfireBUisUEzxaJTY/export?format=csv&gid=561406276"

# -----------------------
# CSV 데이터 가져오기
# -----------------------
def get_data():
    try:
        res = requests.get(CSV_URL, timeout=10)

        print("STATUS:", res.status_code)
        print("RAW:", res.text[:200])

        if res.status_code != 200:
            print("❌ CSV 요청 실패")
            return []

        lines = res.text.splitlines()

        if len(lines) < 2:
            print("❌ 데이터 없음")
            return []

        pairs = []

        for row in lines[1:]:
            cols = row.split(",")

            if len(cols) < 2:
                continue

            giftcode = cols[0].strip()
            player = cols[1].strip()

            if giftcode and player:
                pairs.append((giftcode, player))

        print("Pairs:", pairs)

        return pairs

    except Exception as e:
        print("❌ CSV 처리 실패:", e)
        return []


# -----------------------
# 딜레이
# -----------------------
def human_delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


# -----------------------
# JS 클릭
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
# Redeem (🔥 스크린샷 포함)
# -----------------------
def redeem(page, player_id, giftcode, step_id):
    base = f"screenshots/{step_id}"

    page.goto("https://ks-giftcode.centurygame.com/", timeout=30000)
    page.screenshot(path=f"{base}_1_home.png")

    # Player 입력
    page.wait_for_selector("input", timeout=10000)
    page.fill("input", player_id)
    page.screenshot(path=f"{base}_2_player_input.png")

    human_delay()

    # Login 클릭
    safe_click(page, "Login")
    human_delay(2, 4)
    page.screenshot(path=f"{base}_3_after_login.png")

    # Gift Code 입력
    page.wait_for_selector("input[placeholder='Enter Gift Code']", timeout=10000)
    page.fill("input[placeholder='Enter Gift Code']", giftcode)
    page.screenshot(path=f"{base}_4_code_input.png")

    human_delay()

    # Confirm 클릭
    safe_click(page, "Confirm")
    human_delay(2, 4)
    page.screenshot(path=f"{base}_5_after_confirm.png")


# -----------------------
# 실행
# -----------------------
def run():
    pairs = get_data()

    if not pairs:
        print("❌ 데이터 없음 (CSV 확인)")
        return

    # 🔥 스크린샷 폴더 생성
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        page = context.new_page()

        step = 0

        for giftcode, player in pairs:
            step += 1

            for retry in range(3):
                try:
                    print(f"[TRY] {giftcode} -> {player}")

                    redeem(page, player, giftcode, step)

                    print(f"[SUCCESS] {giftcode} -> {player}")
                    break

                except Exception as e:
                    print(f"[ERROR] {e}")
                    time.sleep(3)

            human_delay(2, 5)

        browser.close()


if __name__ == "__main__":
    run()
