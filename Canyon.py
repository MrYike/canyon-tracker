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

# ONLY THESE 3 CANYONS
CANYONS = [
    {"name": "Narrow Neck",   "unit_type_id": 3151},
    {"name": "Grand Canyon",  "unit_type_id": 3133},
    {"name": "Empress",       "unit_type_id": 3131},
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

    print(f"\n{'='*85}")
    print(f"🏔️  SCANNING: {name}")
    print(f"{'='*85}")

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

        # Click Book button
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
                canyon_data[target_date_display] = {"sold": []}
                continue

            # Extract bookings with proper time
            try:
                all_slots = driver.find_elements(By.XPATH, "//td[@check_in_date]")
                sold_list = []

                for slot in all_slots:
                    check_in = slot.get_attribute("check_in_date")
                    slot_class = slot.get_attribute("class") or ""
                    if "Sold" in slot_class and check_in:
                        who = slot.get_attribute("parent_client_label") or "Unknown"
                        sold_list.append({"time": check_in, "company": who})

                canyon_data[target_date_display] = {"sold": sold_list}

                if not sold_list:
                    print("      ✅ Fully Available!")
                else:
                    print(f"      🔴 {len(sold_list)} booked")

            except Exception as e:
                print(f"      ⚠️ Error reading slots: {e}")
                canyon_data[target_date_display] = {"sold": []}

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

# ================== GENERATE DETAILED HTML ==================
print("Generating HTML report...")

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NSW Canyons Booking Status</title>
    <meta http-equiv="refresh" content="1800">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .canyon {{ margin-bottom: 50px; }}
        .day-section {{ margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .updated {{ color: #7f8c8d; text-align: center; font-size: 15px; }}
        .no-book {{ color: #27ae60; font-weight: bold; font-size: 1.15em; }}
        .booked-count {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <h1>🏔️ NSW Canyons Booking Status</h1>
    <p class="updated">Last updated: {today_str} • Next {NUM_DAYS} days</p>
"""

for canyon_name, dates in all_canyons_data.items():
    html += f'<div class="canyon"><h2>🏔️ {canyon_name}</h2>'
    
    for date_str, info in dates.items():
        html += f'<div class="day-section"><h3>📅 {date_str}</h3>'
        
        sold_list = info.get("sold", [])
        if not sold_list:
            html += '<p class="no-book">✅ No bookings — Fully Available!</p>'
        else:
            html += f'<p class="booked-count">🔴 {len(sold_list)} bookings found</p>'
            html += '<table><tr><th>Time</th><th>Booked By</th></tr>'
            for slot in sold_list:
                try:
                    time_obj = datetime.strptime(slot["time"], "%Y-%m-%dT%H:%M:%S")
                    time_str = time_obj.strftime("%I:%M %p")
                    html += f'<tr><td>{time_str}</td><td>{slot["company"]}</td></tr>'
                except:
                    html += f'<tr><td>{slot.get("time", "Unknown")}</td><td>{slot.get("company", "Unknown")}</td></tr>'
            html += '</table>'
        
        html += '</div>'
    
    html += '</div>'

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Saved index.html")
print(f"\n🎉 DONE! Open index.html to see the detailed report for Narrow Neck, Grand Canyon & Empress.")
