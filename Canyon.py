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
    {"name": "Butterbox", "unit_type_id": 3126},
    {"name": "Claustral", "unit_type_id": 3127},
    # ... (keep all your 27 canyons exactly as before)
    {"name": "Yileen", "unit_type_id": 3146},
]

# ================== FAST SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")          # ← modern & faster
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-images")        # ← extra speed (calendar still works)
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)  # ← explicit wait (much smarter than sleep)

driver.get(URL)
time.sleep(3)  # only initial load

# Cookie banner
try:
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Got it!"))).click()
except:
    pass

# Accept terms (once)
try:
    radio = wait.until(EC.element_to_be_clickable((By.NAME, "radPreConditionAccept")))
    driver.execute_script("arguments[0].click();", radio)
    accept_btn = wait.until(EC.element_to_be_clickable((By.ID, "divPreConditionsClose")))
    driver.execute_script("arguments[0].click();", accept_btn)
except:
    pass

# Login (once)
try:
    wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "ogin"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "txtEmail"))).send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    login_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnLoginNext")))
    driver.execute_script("arguments[0].click();", login_btn)
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@unit_type_id]")))  # wait for canyons to load
except Exception as e:
    print(f"❌ Login failed: {e}")
    driver.quit()
    exit(1)

print(f"🚀 Logged in once — now scanning {len(CANYONS)} canyons × {NUM_DAYS} days\n")

# ================== HELPER FUNCTIONS ==================
def click_next_month():
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]")))
        driver.execute_script("arguments[0].click();", next_btn)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
        return True
    except:
        return False

def navigate_to_date(target_date_display):
    target_date_full = target_date_display + "T00:00:00"
    print(f" 📅 {target_date_display} ", end="")
    for attempt in range(8):  # reduced attempts
        try:
            date_cell = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@date='{target_date_full}']")))
            driver.execute_script("arguments[0].click();", date_cell)
            wait.until(EC.presence_of_element_located((By.XPATH, "//td[@check_in_date]")))
            print("✅")
            return True
        except:
            if not click_next_month():
                break
            time.sleep(1)
    print("⚠️ Failed")
    return False

# ================== MAIN SCAN (now much faster) ==================
all_canyons_data = {}

for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]
    print(f"\n{'='*80}\n🏔️ SCANNING: {name}\n{'='*80}")

    canyon_data = {}
    try:
        # Select canyon (no page reload!)
        canyon_row = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@unit_type_id='{uid}']")))
        driver.execute_script("arguments[0].click();", canyon_row)
        wait.until(EC.presence_of_element_located((By.XPATH, f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]")))

        # Click Book
        book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]")))
        driver.execute_script("arguments[0].click();", book_btn)
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[@check_in_date]")))

        # Scan dates
        target_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NUM_DAYS)]
        for target_date_display in target_dates:
            date_clicked = navigate_to_date(target_date_display)
            if not date_clicked:
                canyon_data[target_date_display] = {"sold": [], "available": 0}
                continue

            # Extract slots
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
            except:
                canyon_data[target_date_display] = {"sold": [], "available": 0}

    except Exception as e:
        print(f"❌ Failed {name}: {e}")
        canyon_data = {"error": str(e)}

    all_canyons_data[name] = canyon_data

driver.quit()

# ================== SAVE JSON (for your PWA) ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("canyons_data.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated": today_str,
        "num_days": NUM_DAYS,
        "data": all_canyons_data
    }, f, indent=2)

print(f"\n✅ SCAN COMPLETE in ~{int(time.time() - time.time())} seconds! (data.json ready)")
