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
    time.sleep(2)
except: pass

# Accept terms
try:
    radio = driver.find_element(By.NAME, "radPreConditionAccept")
    driver.execute_script("arguments[0].click();", radio)
    time.sleep(2)
    accept_btn = driver.find_element(By.ID, "divPreConditionsClose")
    driver.execute_script("arguments[0].click();", accept_btn)
    print("✅ Accepted terms!")
    time.sleep(4)
except Exception as e:
    print(f"⚠️ Terms error: {e}")

# Login
try:
    driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
    time.sleep(4)
    driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    login_btn = driver.find_element(By.ID, "btnLoginNext")
    driver.execute_script("arguments[0].click();", login_btn)
    print("✅ Logged in!")
    time.sleep(6)
except Exception as e:
    print(f"❌ Login failed: {e}")
    driver.quit()
    exit(1)

# ================== HELPER FUNCTIONS ==================
def click_next_month():
    xpaths = [
        "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]",
        "//a[contains(@class,'next')]",
        "//span[contains(@class,'next')]",
        "//div[contains(text(),'›')]"
    ]
    for xp in xpaths:
        try:
            btn = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
            return True
        except:
            continue
    return False

def navigate_to_date(target_date_display):
    print(f"   📅 {target_date_display} ", end="")
    formats = [target_date_display, target_date_display + "T00:00:00"]

    for date_str in formats:
        for attempt in range(10):
            try:
                date_cell = driver.find_element(By.XPATH, f"//td[@date='{date_str}']")
                driver.execute_script("arguments[0].click();", date_cell)
                time.sleep(4)
                print("✅")
                return True
            except:
                if not click_next_month():
                    break
                time.sleep(2)
    print("⚠️ Could not reach")
    return False

# ================== MAIN SCAN (Only 3 Canyons) ==================
print(f"\n🚀 STARTING SCAN — 3 canyons × next {NUM_DAYS} days\n")

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
        time.sleep(5)

        # Select canyon
        canyon_row = driver.find_element(By.XPATH, f"//div[@unit_type_id='{uid}']")
        driver.execute_script("arguments[0].click();", canyon_row)
        print(f"✅ Selected {name}")
        time.sleep(4)

        # Click Book
        book_xpath = f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]"
        book_btn = driver.find_element(By.XPATH, book_xpath)
        driver.execute_script("arguments[0].click();", book_btn)
        print(f"✅ Clicked Book")
        time.sleep(5)

        target_dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NUM_DAYS)]

        for target_date_display in target_dates:
            date_clicked = navigate_to_date(target_date_display)

            if not date_clicked:
                canyon_data[target_date_display] = {"sold": []}
                continue

            # Extract detailed bookings (who booked + time)
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
                    print(f"      🔴 {len(sold_list)} booked slot(s)")
                    for slot in sold_list:
                        check_in = slot["time"]
                        who = slot["company"]
                        try:
                            t = datetime.strptime(check_in, "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
                            print(f"         {t} — {who}")
                        except:
                            print(f"         {check_in} — {who}")

            except Exception as e:
                print(f"      ⚠️ Error reading slots: {e}")
                canyon_data[target_date_display] = {"sold": []}

    except Exception as e:
        print(f"❌ Failed {name}: {e}")

    all_canyons_data[name] = canyon_data

driver.quit()

# ================== SAVE JSON + HTML ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open("canyons_data.json", "w", encoding="utf-8") as f:
    json.dump({"updated": today_str, "num_days": NUM_DAYS, "data": all_canyons_data}, f, indent=2)

# HTML Report with detailed bookings
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NSW Canyons Booking Status</title>
    <meta http-equiv="refresh" content="1800">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #ddd; }}
        .no-book {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🏔️ Narrow Neck | Grand Canyon | Empress</h1>
    <p>Last updated: {today_str}</p>
"""

for name, dates in all_canyons_data.items():
    html += f'<div><h2>🏔️ {name}</h2>'
    for d, info in dates.items():
        sold = info.get("sold", [])
        html += f'<h3>📅 {d}</h3>'
        if not sold:
            html += '<p class="no-book">✅ Fully Available!</p>'
        else:
            html += f'<p style="color:red">🔴 {len(sold)} bookings</p>'
            html += '<table><tr><th>Time</th><th>Booked By</th></tr>'
            for s in sold:
                try:
                    t = datetime.strptime(s["time"], "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
                    html += f'<tr><td>{t}</td><td>{s["company"]}</td></tr>'
                except:
                    html += f'<tr><td>?</td><td>{s.get("company","Unknown")}</td></tr>'
            html += '</table>'
    html += '</div>'

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("\n✅ Saved canyons_data.json and index.html")
print(f"Finished at {datetime.now().strftime('%H:%M')}")
