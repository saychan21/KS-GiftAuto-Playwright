import requests
import time
import random
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

CSV_URL = "https://docs.google.com/spreadsheets/d/1c2QmtlaBNsQ32j7JWly-ayigbkmfireBUisUEzxaJTY/export?format=csv&gid=561406276"
USED_FILE = "used_pairs.txt"
MAX_WORKERS = 3  # 🔥 병렬 개수 (안전 권장: 2~3)

# -----------------------
# used_pairs 관리
# -----------------------
def load_used_pairs():
    if not os.path.exists(USED_FILE):
        return set()
    with open(USED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)


def save_used_pair(code, player):
    with open(USED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{code}|{player}\n")


# -----------------------
# CSV 데이터 가져오기
# -----------------------
def get_data():
    try:
        res = requests.get(CSV_URL, timeout=10)

        if res.status_code != 200:
            print("❌ CSV 요청 실패")
            return [], []

        content = res.content.decode("utf-8", errors="ignore")
        reader = csv.reader(content.splitlines())

        giftcodes = set()
        players = set()

        for i, row in enumerate(reader):
            if i == 0:
                continue

            if len(row) < 2:
                continue

            code = row[0].strip()
            player = row[1].strip()

            if code:
                code = code.upper()
                if code.isalnum() and len(code) >= 4:
                    giftcodes.add(code)

            if player and player.isdigit():
                players.add(player)

        giftcodes = list(giftcodes)
        players = list(players)

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
    base = f"screenshots/{step_id}_{player_id}_{giftcode}"

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
# 단일 작업 (병렬용)
# -----------------------
def process_task(p, code, player, step):
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    try:
        for retry in range(3):
            try:
                print(f"[TRY] {code} -> {player}")

                redeem(page, player, code, step)

                print(f"[SUCCESS] {code} -> {player}")

                save_used_pair(code, player)
                return True

            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(3)
        print(f"[FAIL] {code} -> {player}")
        return False
    finally:
        browser.close()


# -----------------------
# 실행
# -----------------------
def run():
    giftcodes, players = get_data()

    if not giftcodes or not players:
        print("❌ 데이터 없음")
        return

    used_pairs = load_used_pairs()
    os.makedirs("screenshots", exist_ok=True)

    tasks = []
    step = 0

    for code in giftcodes:
        for player in players:
            pair_key = f"{code}|{player}"

            if pair_key in used_pairs:
                print(f"[SKIP] {pair_key}")
                continue

            step += 1
            tasks.append((code, player, step))

    # 🔥 병렬 실행
    with sync_playwright() as p:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_task, p, code, player, step)
                for code, player, step in tasks
            ]

            for future in as_completed(futures):
                future.result()

    print("✅ 모든 작업 완료")


if __name__ == "__main__":
    run()
