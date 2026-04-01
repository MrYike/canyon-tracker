import os
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time

URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = os.environ.get("CANYON_EMAIL", "James@myadventuregroup.com.au")
PASSWORD = os.environ.get("CANYON_PASSWORD", "")

# ================== CONFIG ==================
NUM_DAYS = 14
NEXT_MONTH_XPATH = "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]"
# ===========================================

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(8)

# Step 1 - Cookie banner
try:
    driver.find_element(By.LINK_TEXT, "Got it!").click()
    print("✅ Clicked cookie banner")
    time.sleep(2)
except:
    print("⚠️ No cookie banner found")

# Step 2 - Accept terms
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

# Step 3 - Click Login link
try:
    driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
    print("✅ Clicked login link")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Login link error: {e}")

# Step 4 - Enter credentials
try:
    driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    print("✅ Entered credentials")
    time.sleep(2)
except Exception as e:
    print(f"⚠️ Credentials error: {e}")

# Step 5 - Click Login button
try:
    login_btn = driver.find_element(By.ID, "btnLoginNext")
    driver.execute_script("arguments[0].click();", login_btn)
    print("✅ Clicked Login!")
    time.sleep(8)
except Exception as e:
    print(f"⚠️ Login button error: {e}")

# Confirm logged in
try:
    body_text = driver.find_element(By.TAG_NAME, "body").text
    print(f"\n--- PAGE AFTER LOGIN ---\n{body_text[:400]}\n")
    if "Logged In" not in body_text:
        print("❌ LOGIN FAILED — exiting!")
        driver.quit()
        exit(1)
    print("✅ Confirmed logged in!")
except Exception as e:
    print(f"⚠️ Could not confirm login: {e}")
    driver.quit()
    exit(1)

# Step 6 - Click Empress
try:
    empress = driver.find_element(By.XPATH, "//div[contains(text(), 'Empress')]")
    driver.execute_script("arguments[0].click();", empress)
    print("✅ Clicked Empress!")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Empress error: {e}")

# Step 7 - Click Book button
try:
    book_btn = driver.find_element(By.XPATH, "//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {iUnitTypeId:3131});\"]")
    driver.execute_script("arguments[0].click();", book_btn)
    print("✅ Clicked Book!")
    time.sleep(8)
except Exception as e:
    print(f"⚠️ Book button error: {e}")

# ================== MULTI-DAY LOOP ==================
print(f"\n🔍 STARTING SCAN — Next {NUM_DAYS} days\n")

all_days_html = ""

for day_offset in range(NUM_DAYS):
    target_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%dT00:00:00")
    target_date_display = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")

    print(f"\n{'='*70}")
    print(f"📅 PROCESSING: {target_date_display}  (Day {day_offset+1}/{NUM_DAYS})")
    print(f"{'='*70}")

    date_clicked = False
    for attempt in range(6):
        try:
            date_cell = driver.find_element(By.XPATH, f"//td[@date='{target_date}']")
            driver.execute_script("arguments[0].click();", date_cell)
            print(f"✅ Clicked date cell: {target_date_display}")
            time.sleep(8)
            date_clicked = True
            break
        except:
            if attempt < 5:
                try:
                    next_btn = driver.find_element(By.XPATH, NEXT_MONTH_XPATH)
                    driver.execute_script("arguments[0].click();", next_btn)
                    print(f"   → Clicked Next Month arrow (attempt {attempt+1})")
                    time.sleep(5)
                except:
                    print(f"   → Next Month button not found (attempt {attempt+1})")
            else:
                print(f"⚠️ Could not reach {target_date_display}")

    if not date_clicked:
        all_days_html += f"<div class='day-section'><h2>📅 {target_date_display}</h2><p class='warning'>⚠️ Could not load this date</p></div>"
        continue

    try:
        sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class, 'Sold')]")

        day_html = f"<div class='day-section'><h2>📅 {target_date_display}</h2>"

        if not sold_slots:
            day_html += "<p class='no-book'>✅ No bookings on this day!</p>"
        else:
            rows = ""
            for slot in sold_slots:
                check_in = slot.get_attribute("check_in_date")
                who = slot.get_attribute("parent_client_label")
                time_obj = datetime.strptime(check_in, "%Y-%m-%dT%H:%M:%S")
                time_str = time_obj.strftime("%I:%M %p")
                print(f"   🔴 {time_str} — {who}")
                rows += f"<tr><td>{time_str}</td><td>{who}</td></tr>"

            day_html += f"""
            <table>
                <tr><th>Time</th><th>Booked By</th></tr>
                {rows}
            </table>"""

        day_html += "</div>"
        all_days_html += day_html

    except Exception as e:
        print(f"⚠️ Error reading slots for {target_date_display}: {e}")
        all_days_html += f"<div class='day-section'><h2>📅 {target_date_display}</h2><p class='warning'>Error loading slots</p></div>"

    print(f"✅ Day {target_date_display} complete\n")

# ================== BUILD HTML ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Empress Canyon Bookings</title>
    <meta http-equiv="refresh" content="3600">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.5; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .updated {{ color: #7f8c8d; font-size: 14px; text-align: center; }}
        .no-book {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #e67e22; }}
        .day-section {{ margin-bottom: 40px; }}
    </style>
</head>
<body>
    <h1>🏔️ Empress Canyon Bookings</h1>
    <p class="updated">Last updated: {today_str} • Next {NUM_DAYS} days</p>
    {all_days_html}
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Saved multi-day results to index.html")
driver.quit()
