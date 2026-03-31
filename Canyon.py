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
NUM_DAYS = 14  # ← Change this anytime
NEXT_MONTH_XPATH = "//div[contains(@style, 'border-left: 20px solid rgb(255, 255, 255)')]"
# ===========================================

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(5)

# [All the login, Empress, Book steps are exactly the same as before...]

# ================== MULTI-DAY LOOP ==================
print(f"\n🔍 STARTING FULLY AUTOMATIC SCAN — Next {NUM_DAYS} days\n")

all_days_html = ""

for day_offset in range(NUM_DAYS):
    target_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%dT00:00:00")
    target_date_display = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
    
    print(f"\n{'='*70}")
    print(f"📅 PROCESSING: {target_date_display}  (Day {day_offset+1}/{NUM_DAYS})")
    print(f"{'='*70}")

    # Click date cell + auto next month
    date_clicked = False
    for attempt in range(6):
        try:
            date_cell = driver.find_element(By.XPATH, f"//td[@date='{target_date}']")
            driver.execute_script("arguments[0].click();", date_cell)
            print(f"✅ Clicked date cell: {target_date_display}")
            time.sleep(6)
            date_clicked = True
            break
        except:
            if attempt < 5:
                try:
                    next_btn = driver.find_element(By.XPATH, NEXT_MONTH_XPATH)
                    driver.execute_script("arguments[0].click();", next_btn)
                    print(f"   → Clicked Next Month arrow (attempt {attempt+1})")
                    time.sleep(3)
                except:
                    pass
            else:
                print(f"⚠️ Could not reach {target_date_display}")

    if not date_clicked:
        all_days_html += f"<h2>📅 {target_date_display}</h2><p style='color:orange;'>⚠️ Could not load this date</p>"
        continue

    # Scrape sold slots
    try:
        sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class, 'Sold')]")
        
        day_html = f"<h2 style='margin-top:40px; color:#2c3e50;'>📅 {target_date_display}</h2>"

        if not sold_slots:
            day_html += "<p style='color:#27ae60; font-weight:bold;'>✅ No bookings on this day!</p>"
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
            <table style="width:100%; border-collapse:collapse; margin-bottom:30px;">
                <tr><th style="background:#2c3e50; color:white; padding:12px; text-align:left;">Time</th>
                    <th style="background:#2c3e50; color:white; padding:12px; text-align:left;">Booked By</th></tr>
                {rows}
            </table>"""
        
        all_days_html += day_html

    except Exception as e:
        print(f"⚠️ Error reading slots for {target_date_display}: {e}")
        all_days_html += f"<h2>📅 {target_date_display}</h2><p style='color:red;'>Error loading slots</p>"

    print(f"✅ Day {target_date_display} complete\n")

# ================== BUILD HTML ==================
today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Empress Canyon Bookings</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.5; }}
        h1 {{ color: #2c3e50; text-align: center; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f8f9fa; }}
        .updated {{ color: #7f8c8d; font-size: 14px; text-align: center; }}
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

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# NO GIT PUSH HERE ANYMORE — GitHub Action handles it