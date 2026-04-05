# ================== CANYON TRACKER - CLEAN VERSION ==================
# For canyon-tracker repo only
# Saves canyons_data.json (GitHub Actions copies it to data.json for the app)

import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time

# ================== CONFIG ==================
URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = os.environ.get("CANYON_EMAIL", "James@myadventuregroup.com.au")
PASSWORD = os.environ.get("CANYON_PASSWORD", "")
NUM_DAYS = 14

CANYONS = [
    {"name": "Butterbox", "unit_type_id": 3126},
    {"name": "Claustral", "unit_type_id": 3127},
    {"name": "Danae Brook", "unit_type_id": 3128},
    {"name": "Deep Pass", "unit_type_id": 3129},
    {"name": "Dione Dell", "unit_type_id": 3130},
    {"name": "Empress", "unit_type_id": 3131},
    {"name": "Fortress", "unit_type_id": 3132},
    {"name": "Grand Canyon", "unit_type_id": 3133},
    {"name": "Hole in the Wall", "unit_type_id": 3134},
    {"name": "Juggler", "unit_type_id": 3137},
    {"name": "Kalang", "unit_type_id": 3136},
    {"name": "Kanangra Main", "unit_type_id": 3138},
    {"name": "Malaita Point", "unit_type_id": 3149},
    {"name": "Malaita Wall", "unit_type_id": 3148},
    {"name": "Mount Portal", "unit_type_id": 3150},
    {"name": "Narrow Neck", "unit_type_id": 3151},
    {"name": "North Bowen", "unit_type_id": 3139},
    {"name": "Other", "unit_type_id": 3186},
    {"name": "River Caves", "unit_type_id": 3140},
    {"name": "Rocky Creek / Twister", "unit_type_id": 3141},
    {"name": "Serendipity", "unit_type_id": 3142},
    {"name": "Starlight", "unit_type_id": 3143},
    {"name": "Sweet Dreams", "unit_type_id": 3152},
    {"name": "Tiger Snake", "unit_type_id": 3144},
    {"name": "Whungee Wheengee", "unit_type_id": 3145},
    {"name": "Wollangambe", "unit_type_id": 3153},
    {"name": "Yileen", "unit_type_id": 3146},
]

# ================== SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")      # ← more stable in 2026 Chrome
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(8)

# Cookie banner
try:
    driver.find_element(By.LINK_TEXT, "Got it!").click()
    print("✅ Clicked cookie banner")
    time.sleep(2)
except:
    pass

# Accept terms
try:
    radio = driver.find_element(By.NAME, "radPreConditionAccept")
    driver.execute_script("arguments[0].click();", radio)
    time.sleep(2)
    accept_btn = driver.find_element(By.ID, "divPreConditionsClose")
    driver.execute_script("arguments[0].click();", accept_btn)
    print("✅ Accepted terms!")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Terms error: {e}")

# Login
try:
    driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
    time.sleep(5)
    driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    login_btn = driver.find_element(By.ID, "btnLoginNext")
    driver.execute_script("arguments[0].click();", login_btn)
    print("✅ Logged in!")
    time.sleep(8)
except Exception as e:
    print(f"❌ Login failed: {e}")
    driver.quit()
    exit(1)

# ================== HELPER FUNCTIONS ==================
def click_next_month():
    try:
        next_btn = driver.find_element(By.XPATH, "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]")
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(4)
        return True
    except:
        return False

def navigate_to_date(target_date_display):
    target_date_full = target_date_display + "T00:00:00"
    print(f" 📅 {target_date_display} ", end="")
    for attempt in range(15):
        try:
            date_cell = driver.find_element(By.XPATH, f"//td[@date='{target_date_full}']")
            driver.execute_script("arguments[0].click();", date_cell)
            time.sleep(6)
            print("✅")
            return True
        except:
            if not click_next_month():
                break
            time.sleep(2)
    print("⚠️ Failed")
    return False

# ================== MAIN SCAN ==================
print(f"\n🚀 STARTING FULL SCAN — {len(CANYONS)} canyons × next {NUM_DAYS} days\n")

all_canyons_data = {}

for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]
    print(f"\n{'='*90}")
    print(f"🏔️ SCANNING: {name}")
    print(f"{'='*90}")

    canyon_data = {}
    try:
        driver.get(URL)
        time.sleep(7)

        # Re-accept terms if needed
        try:
            radio = driver.find_element(By.NAME, "radPreConditionAccept")
            driver.execute_script("arguments[0].click();", radio)
            time.sleep(2)
            accept_btn = driver.find_element(By.ID, "divPreConditionsClose")
            driver.execute_script("arguments[0].click();", accept_btn)
            time.sleep(4)
        except:
            pass

        # Select canyon
        canyon_row = driver.find_element(By.XPATH, f"//div[@unit_type_id='{uid}']")
        driver.execute_script("arguments[0].click();", canyon_row)
        print(f"✅ Selected {name}")
        time.sleep(5)

        # Click Book
        book_xpath = f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]"
        book_btn = driver.find_element(By.XPATH, book_xpath)
        driver.execute_script("arguments[0].click();", book_btn)
        print(f"✅ Clicked Book")
        time.sleep(7)

        # Scan dates
        target_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NUM_DAYS)]
        for target_date_display in target_dates:
            date_clicked = navigate_to_date(target_date_display)
            if not date_clicked:
                canyon_data[target_date_display] = {"sold": [], "available": 0}
                continue

            # Extract detailed booking info
            try:
                all_slots = driver.find_elements(By.XPATH, "//td[@check_in_date]")
                sold_list = []
                for slot in all_slots:
                    check_in = slot.get_attribute("check_in_date")
                    slot_class = slot.get_attribute("class") or ""
                    if "Sold" in slot_class and check_in:
                        who = slot.get_attribute("parent_client_label") or "Unknown"
                        sold_list.append({"time": check_in, "company": who})

                canyon_data[target_date_display] = {
                    "sold": sold_list,
                    "available": len(all_slots) - len(sold_list)
                }
                if not sold_list:
                    print(" ✅ Fully Available!")
                else:
                    print(f" 🔴 {len(sold_list)} booked")
            except Exception as e:
                print(f" ⚠️ Error reading slots: {e}")
                canyon_data[target_date_display] = {"sold": [], "available": 0}

    except Exception as e:
        print(f"❌ Failed processing {name}: {e}")
        canyon_data = {"error": str(e)}

    all_canyons_data[name] = canyon_data

driver.quit()

# ================== SAVE JSON ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("canyons_data.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated": today_str,
        "num_days": NUM_DAYS,
        "data": all_canyons_data
    }, f, indent=2)

print(f"\n✅ Saved canyons_data.json")
print(f"\n🎉 SCAN COMPLETE!")
