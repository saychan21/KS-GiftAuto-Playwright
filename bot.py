import requests
import time
import random
import os
from playwright.sync_api import sync_playwright

CSV_URL = "https://docs.google.com/spreadsheets/d/1c2QmtlaBNsQ32j7JWly-ayigbkmfireBUisUEzxaJTY/export?format=csv&gid=561406276"
USED_FILE = "used_codes.txt"   # 🔥 추가

# -----------------------
# used_codes 관리
# -----------------------
def load_used_codes():
    if not os.path.exists(USED_FILE):
        return set()
    with open(USED_FILE, "r") as f:
        return set(line.strip() for line in f)


def save_used_code(code):
    with open(USED_FILE, "a") as f:
        f.write(code + "\n")


# -----------------------
# CSV 데이터 가져오기
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

            if len(cols) >= 1 and cols[0].strip():
                giftcodes.append(cols[0].strip())

            if len(cols) >= 2 and cols[1].strip():
                players.append(cols[1].strip())

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
# Redeem
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
# 실행
# -----------------------
def run():
    giftcodes, players = get_data()

    if not giftcodes or not players:
        print("❌ 데이터 없음")
        return

    # 🔥 이미 사용한 코드 제거
    used_codes = load_used_codes()
    giftcodes = [c for c in giftcodes if c not in used_codes]

    if not giftcodes:
        print("✅ 새로운 코드 없음 (이미 모두 사용됨)")
        return

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        step = 0

        for code in giftcodes:
            success = True  # 🔥 전체 player 성공 여부 체크

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
                else:
                    success = False  # 한 명이라도 실패하면 false

                human_delay(2, 5)

            # 🔥 모든 player 성공했을 때만 저장
            if success:
                print(f"💾 코드 저장: {code}")
                save_used_code(code)
            else:
                print(f"⚠️ 일부 실패 → 저장 안함: {code}")

        browser.close()


if __name__ == "__main__":
    run()
