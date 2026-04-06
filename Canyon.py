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
    {"name": "Narrow Neck",  "unit_type_id": 3151},
    {"name": "Grand Canyon", "unit_type_id": 3133},
    {"name": "Empress",      "unit_type_id": 3131},
]

# ================== SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--headless")
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

# Confirm login
body_text = driver.find_element(By.TAG_NAME, "body").text
if "Logged In" not in body_text:
    print("❌ LOGIN FAILED — exiting!")
    driver.quit()
    exit(1)
print("✅ Confirmed logged in!")

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
    print(f"   📅 {target_date_display} ", end="")
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
print(f"\n🚀 STARTING SCAN — {len(CANYONS)} canyons × next {NUM_DAYS} days\n")

all_canyons_data = {}

for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]

    print(f"\n{'='*70}")
    print(f"🏔️  SCANNING: {name}")
    print(f"{'='*70}")

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
                        print(f"      🔴 {check_in} — {who}")
                    elif "Available" in slot_class:
                        available_list.append(check_in)

                canyon_data[target_date_display] = {
                    "sold": sold_list,
                    "available": available_list,
                    "all_slots": all_slot_times
                }

                if not sold_list:
                    print(f"      ✅ No bookings")

            except Exception as e:
                print(f"      ⚠️ Error: {e}")
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

print("\n✅ Saved data.json")

# ================== SAVE INDEX.HTML ==================
all_days_html = ""
for canyon_name, dates in all_canyons_data.items():
    all_days_html += f"<h2>🏔️ {canyon_name}</h2>"
    for date_str, info in dates.items():
        all_days_html += f"<div class='day-section'><h3>📅 {date_str}</h3>"
        sold = info.get("sold", [])
        if not sold:
            all_days_html += "<p class='no-book'>✅ No bookings!</p>"
        else:
            all_days_html += f"<p class='booked-count'>🔴 {len(sold)} bookings</p>"
            all_days_html += "<table><tr><th>Time</th><th>Booked By</th></tr>"
            for slot in sold:
                try:
                    t = datetime.strptime(slot["time"], "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
                except:
                    t = slot["time"]
                all_days_html += f"<tr><td>{t}</td><td>{slot['company']}</td></tr>"
            all_days_html += "</table>"
        all_days_html += "</div>"

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
