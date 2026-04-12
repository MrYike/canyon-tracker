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

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 12)  # slightly tighter wait

driver.get(URL)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(3)

# Cookie banner
try:
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Got it!"))).click()
    print("✅ Cookie banner")
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
    print("✅ Terms accepted")
    time.sleep(4)
except:
    pass

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

# ================== ROBUST NEXT MONTH (now primary is aria-label) ==================
def click_next_month():
    selectors = [
        "//div[@aria-label='Next Month']",           # ← most reliable for RezExpert
        "//button[contains(@aria-label, 'Next')]",
        "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]",
        "//button[contains(@title, 'Next') or contains(text(), '›')]",
    ]
    for xpath in selectors:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2.5)
            print("   → Next month clicked")
            return True
        except:
            continue
    print("   ⚠️  Next-month button not found")
    return False

# ================== MAIN SCAN (SEQUENTIAL NAVIGATION) ==================
print(f"\n🚀 STARTING SCAN — {len(CANYONS)} canyons × next {NUM_DAYS} days\n")

all_canyons_data = {}

target_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NUM_DAYS)]

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

        last_month = None
        for target_date_display in target_dates:
            print(f"   {target_date_display} ", end="")

            target_full = target_date_display + "T00:00:00"

            # Try to click the date (up to 3 attempts with next-month if needed)
            success = False
            for attempt in range(4):
                try:
                    date_cell = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"//td[@date='{target_full}']"))
                    )
                    driver.execute_script("arguments[0].click();", date_cell)
                    time.sleep(4)
                    print("✅")
                    success = True
                    break
                except:
                    if attempt == 0 and last_month is None:
                        # First date of this canyon — just try next month once if needed
                        click_next_month()
                    elif attempt < 3:
                        click_next_month()
                    time.sleep(1)

            if not success:
                print("❌")
                canyon_data[target_date_display] = {"sold": [], "available": [], "all_slots": []}
                continue

            # Parse slots
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
                print(f"      Parse error: {e}")
                canyon_data[target_date_display] = {"sold": [], "available": [], "all_slots": []}

            last_month = target_date_display[:7]  # track month for next iteration

    except Exception as e:
        print(f"❌ Failed {name}: {e}")

    all_canyons_data[name] = canyon_data

driver.quit()

# ================== SAVE ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated": today_str,
        "num_days": NUM_DAYS,
        "data": all_canyons_data
    }, f, indent=2)

print(f"\n✅ FINISHED — data.json saved ({len(all_canyons_data)} canyons)")
