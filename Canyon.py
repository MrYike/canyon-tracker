from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains  # ✅ ADDED
from datetime import datetime, timedelta
import time

# ================== CONFIG ==================
URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = "James@myadventuregroup.com.au"
PASSWORD = "yfUR^8a^XAqhpt^T"

NUM_DAYS = 14

CANYONS = [
    {"name": "Butterbox",           "unit_type_id": 3126},
    {"name": "Claustral",           "unit_type_id": 3127},
    {"name": "Danae Brook",         "unit_type_id": 3128},
    {"name": "Deep Pass",           "unit_type_id": 3129},
    {"name": "Dione Dell",          "unit_type_id": 3130},
    {"name": "Empress",             "unit_type_id": 3131},
    {"name": "Fortress",            "unit_type_id": 3132},
    {"name": "Grand Canyon",        "unit_type_id": 3133},
    {"name": "Hole in the Wall",    "unit_type_id": 3134},
    {"name": "Juggler",             "unit_type_id": 3137},
    {"name": "Kalang",              "unit_type_id": 3136},
    {"name": "Kanangra Main",       "unit_type_id": 3138},
    {"name": "Malaita Point",       "unit_type_id": 3149},
    {"name": "Malaita Wall",        "unit_type_id": 3148},
    {"name": "Mount Portal",        "unit_type_id": 3150},
    {"name": "Narrow Neck",         "unit_type_id": 3151},
    {"name": "North Bowen",         "unit_type_id": 3139},
    {"name": "Other",               "unit_type_id": 3186},
    {"name": "River Caves",         "unit_type_id": 3140},
    {"name": "Rocky Creek / Twister","unit_type_id": 3141},
    {"name": "Serendipity",         "unit_type_id": 3142},
    {"name": "Starlight",           "unit_type_id": 3143},
    {"name": "Sweet Dreams",        "unit_type_id": 3152},
    {"name": "Tiger Snake",         "unit_type_id": 3144},
    {"name": "Whungee Wheengee",    "unit_type_id": 3145},
    {"name": "Wollangambe",         "unit_type_id": 3153},
    {"name": "Yileen",              "unit_type_id": 3146},
]

NEXT_MONTH_XPATH = "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]"

# ================== SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(6)

# Cookie + Terms
try:
    driver.find_element(By.LINK_TEXT, "Got it!").click()
except: pass
time.sleep(2)

try:
    driver.find_element(By.NAME, "radPreConditionAccept").click()
    time.sleep(1)
    driver.find_element(By.ID, "divPreConditionsClose").click()
except: pass
time.sleep(3)

# Login
driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
time.sleep(3)
driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
driver.find_element(By.ID, "btnLoginNext").click()
print("✅ Logged in successfully!")
time.sleep(6)

print(f"\n🚀 STARTING SCAN — {len(CANYONS)} canyons × {NUM_DAYS} days\n")

actions = ActionChains(driver)  # ✅ ADDED

for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]

    print(f"\n{'='*95}")
    print(f"🏔️  {name} (ID: {uid})")
    print(f"{'='*95}")

    try:
        driver.get(URL)
        time.sleep(6)

        try:
            driver.find_element(By.NAME, "radPreConditionAccept").click()
            time.sleep(1)
            driver.find_element(By.ID, "divPreConditionsClose").click()
            time.sleep(3)
        except:
            pass

        canyon_row = driver.find_element(By.XPATH, f"//div[@unit_type_id='{uid}']")
        driver.execute_script("arguments[0].click();", canyon_row)
        print(f"✅ Selected {name}")
        time.sleep(5)

        book_xpath = f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]"
        book_btn = driver.find_element(By.XPATH, book_xpath)
        driver.execute_script("arguments[0].click();", book_btn)
        print(f"✅ Clicked Book for {name}")
        time.sleep(6)

        for day_offset in range(NUM_DAYS):
            target_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%dT00:00:00")
            target_date_display = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")

            print(f"   📅 {target_date_display} ", end="")

            date_clicked = False
            for attempt in range(6):
                try:
                    date_cell = driver.find_element(By.XPATH, f"//td[@date='{target_date}']")
                    driver.execute_script("arguments[0].click();", date_cell)
                    time.sleep(5)
                    date_clicked = True
                    print("✅")
                    break
                except:
                    if attempt < 5:
                        try:
                            next_btn = driver.find_element(By.XPATH, NEXT_MONTH_XPATH)
                            driver.execute_script("arguments[0].click();", next_btn)
                            print("→", end=" ")
                            time.sleep(4)
                        except:
                            time.sleep(1)

            if not date_clicked:
                print("⚠️ Could not reach date")
                continue

            try:
                sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class, 'Sold')]")
                if not sold_slots:
                    print("      ✅ No bookings — Fully available!")
                else:
                    print(f"      🔴 {len(sold_slots)} booked slot(s)")

                    for slot in sold_slots[:8]:
                        check_in = slot.get_attribute("check_in_date")

                        # ✅ HOVER (so name loads)
                        try:
                            actions.move_to_element(slot).perform()
                            time.sleep(0.4)
                        except:
                            pass

                        # ✅ GET NAME (multiple fallbacks)
                        who = (
                            slot.get_attribute("parent_client_label")
                            or slot.get_attribute("title")
                            or slot.get_attribute("data-original-title")
                            or slot.text
                            or "Unknown"
                        )

                        # ✅ CLEAN NAME
                        if who:
                            who = who.replace("Booked by:", "").strip()

                        try:
                            t = datetime.strptime(check_in, "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
                            print(f"         {t} — {who}")
                        except:
                            print(f"         {check_in} — {who}")

            except Exception as e:
                print(f"      ⚠️ Error reading slots: {str(e)[:80]}")

    except Exception as e:
        print(f"❌ Error with {name}: {str(e)[:120]}")

    print(f"   ↩️ Finished {name}\n")

print("\n🎉 FULL SCAN COMPLETED!")
input("\nPress Enter to close the browser...")
driver.quit()
