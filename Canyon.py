import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time

# ================== CONFIG ==================
URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = os.environ.get("CANYON_EMAIL", "James@myadventuregroup.com.au")
PASSWORD = os.environ.get("CANYON_PASSWORD", "")

NUM_DAYS = 14

CANYONS = [
    {"name": "Narrow Neck",  "unit_type_id": 3151},
    {"name": "Grand Canyon", "unit_type_id": 3133},
    {"name": "Empress",      "unit_type_id": 3131},
]

# ================== SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

driver.get(URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(3)

# Cookie banner
try:
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Got it!"))).click()
    print("✅ Clicked cookie banner")
    time.sleep(1)
except:
    pass

# Accept terms
try:
    radio = wait.until(EC.presence_of_element_located((By.NAME, "radPreConditionAccept")))
    driver.execute_script("arguments[0].click();", radio)
    time.sleep(1)
    accept_btn = driver.find_element(By.ID, "divPreConditionsClose")
    driver.execute_script("arguments[0].click();", accept_btn)
    print("✅ Accepted terms")
    time.sleep(4)
except Exception as e:
    print(f"Terms skipped: {e}")

# Login
try:
    wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "ogin"))).click()
    time.sleep(3)
    driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    login_btn = driver.find_element(By.ID, "btnLoginNext")
    driver.execute_script("arguments[0].click();", login_btn)
    print("✅ Logged in")
    time.sleep(8)
except Exception as e:
    print(f"❌ Login failed: {e}")
    driver.quit()
    exit(1)

# ================== ROBUST NEXT MONTH HELPER ==================
def click_next_month():
    """Multiple fallback selectors for the 'next month' arrow"""
    selectors = [
        "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]",  # old one
        "//button[contains(@aria-label, 'Next') or contains(@title, 'Next')]",
        "//div[contains(@class, 'calendar')]//button[contains(text(), '›') or contains(@aria-label, 'next')]",
        "//img[contains(@src, 'next') or contains(@alt, 'next')]/parent::div",
        "//div[@role='button' and contains(@style, 'arrow')]",
    ]
    for xpath in selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
            print("   → Clicked next month")
            return True
        except:
            continue
    print("   ⚠️  Could not find next-month button")
    return False

def navigate_to_date(target_date_display):
    target_date_full = target_date_display + "T00:00:00"
    print(f"   {target_date_display} ", end="")

    for attempt in range(20):  # increased attempts
        try:
            date_cell = wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//td[@date='{target_date_full}']"))
            )
            driver.execute_script("arguments[0].click();", date_cell)
            time.sleep(5)
            print("✅")
            return True
        except:
            if not click_next_month():
                break
            time.sleep(1)
    print("❌ Failed to reach date")
    return False

# ================== MAIN SCAN ==================
print(f"\n🚀 STARTING SCAN — {len(CANYONS)} canyons × next {NUM_DAYS} days\n")

all_canyons_data = {}

for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]

    print(f"\n{'='*70}")
    print(f"SCANNING: {name}")
    print(f"{'='*70}")

    canyon_data = {}

    try:
        driver.get(URL)
        time.sleep(6)

        # Select canyon
        canyon_row = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@unit_type_id='{uid}']"))
        )
        driver.execute_script("arguments[0].click();", canyon_row)
        print(f"✅ Selected {name}")
        time.sleep(5)

        # Click Book
        book_xpath = f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]"
        book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, book_xpath)))
        driver.execute_script("arguments[0].click();", book_btn)
        print("✅ Clicked Book")
        time.sleep(7)

        # Scan dates
        target_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NUM_DAYS)]

        for target_date_display in target_dates:
            date_clicked = navigate_to_date(target_date_display)

            if not date_clicked:
                canyon_data[target_date_display] = {"sold": [], "available": [], "all_slots": []}
                continue

            try:
                all_slots = driver.find_elements(By.XPATH, "//td[@check_in_date]")
                sold_list = []
                available_list = []
                all_slot_times = []

                for slot in all_slots:
                    check_in = slot.get_attribute("check_in_date")
                    slot_class = slot.get_attribute("class") or ""
                    if not check_in:
                        continue
                    all_slot_times.append(check_in)
                    if "Sold" in slot_class:
                        who = slot.get_attribute("parent_client_label") or "Unknown"
                        sold_list.append({"time": check_in, "company": who})
                    elif "Available" in slot_class:
                        available_list.append(check_in)

                canyon_data[target_date_display] = {
                    "sold": sold_list,
                    "available": available_list,
                    "all_slots": all_slot_times
                }

            except Exception as e:
                print(f"      Error parsing slots: {e}")
                canyon_data[target_date_display] = {"sold": [], "available": [], "all_slots": []}

    except Exception as e:
        print(f"❌ Failed processing {name}: {e}")

    all_canyons_data[name] = canyon_data

driver.quit()

# ================== SAVE DATA.JSON ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated": today_str,
        "num_days": NUM_DAYS,
        "data": all_canyons_data
    }, f, indent=2)

print(f"\n✅ Saved data.json — {len(all_canyons_data)} canyons")

# (Your existing index.html generation code can stay at the bottom if you still use the GitHub Pages view)

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Canyon Bookings</title>
    <meta http-equiv="refresh" content="3600">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.5; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #c45e2a; border-bottom: 3px solid #c45e2a; padding-bottom: 8px; margin-top: 40px; }}
        h3 {{ color: #34495e; margin-top: 16px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .updated {{ color: #7f8c8d; font-size: 14px; text-align: center; }}
        .no-book {{ color: #27ae60; font-weight: bold; }}
        .booked-count {{ color: #e74c3c; font-weight: bold; }}
        .day-section {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>🏔️ Canyon Bookings</h1>
    <p class="updated">Last updated: {today_str} • Next {NUM_DAYS} days</p>
    {all_days_html}
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Saved index.html")
print("\n🎉 SCAN COMPLETE!")
