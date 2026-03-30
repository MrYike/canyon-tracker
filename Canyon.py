import os
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = os.environ.get("CANYON_EMAIL", "James@myadventuregroup.com.au")
PASSWORD = os.environ.get("CANYON_PASSWORD", "")

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(5)

# Step 1 - Cookie banner
try:
    driver.find_element(By.LINK_TEXT, "Got it!").click()
    print("✅ Clicked cookie banner")
    time.sleep(1)
except:
    pass

# Step 2 - Accept terms
try:
    radio = driver.find_element(By.NAME, "radPreConditionAccept")
    driver.execute_script("arguments[0].click();", radio)
    time.sleep(1)
    accept_btn = driver.find_element(By.ID, "divPreConditionsClose")
    driver.execute_script("arguments[0].click();", accept_btn)
    print("✅ Accepted terms!")
    time.sleep(3)
except Exception as e:
    print(f"⚠️ Terms error: {e}")

# Step 3 - Click Login link
try:
    driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
    print("✅ Clicked login link")
    time.sleep(3)
except Exception as e:
    print(f"⚠️ Login link error: {e}")

# Step 4 - Enter credentials
try:
    driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
    driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
    print("✅ Entered credentials")
    time.sleep(1)
except Exception as e:
    print(f"⚠️ Credentials error: {e}")

# Step 5 - Click Login button
try:
    login_btn = driver.find_element(By.ID, "btnLoginNext")
    driver.execute_script("arguments[0].click();", login_btn)
    print("✅ Clicked Login!")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Login button error: {e}")

# Step 6 - Click Empress
try:
    empress = driver.find_element(By.XPATH, "//div[contains(text(), 'Empress')]")
    driver.execute_script("arguments[0].click();", empress)
    print("✅ Clicked Empress!")
    time.sleep(3)
except Exception as e:
    print(f"⚠️ Empress error: {e}")

# Step 7 - Click Book button
try:
    book_btn = driver.find_element(By.XPATH, "//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {iUnitTypeId:3131});\"]")
    driver.execute_script("arguments[0].click();", book_btn)
    print("✅ Clicked Book!")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Book button error: {e}")

# Step 8 - Click the first available date cell
try:
    date_cell = driver.find_element(By.XPATH, "//td[@date]")
    clicked_date = date_cell.get_attribute("date")
    driver.execute_script("arguments[0].click();", date_cell)
    print(f"✅ Clicked date: {clicked_date}")
    time.sleep(10)
except Exception as e:
    print(f"⚠️ Date cell error: {e}")

# Step 9 - Find all SOLD slots and save to HTML
try:
    all_cells = driver.find_elements(By.XPATH, "//td[@class]")
    print(f"Total cells found: {len(all_cells)}")
    for cell in all_cells[:10]:
        print(f"class='{cell.get_attribute('class')}' text='{cell.text}'")

    sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class, 'Sold')]")
    print(f"Sold slots found: {len(sold_slots)}")

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""

    if not sold_slots:
        rows = "<tr><td colspan='2'>✅ No bookings today!</td></tr>"
    else:
        for slot in sold_slots:
            check_in = slot.get_attribute("check_in_date")
            who = slot.get_attribute("parent_client_label")
            time_obj = datetime.strptime(check_in, "%Y-%m-%dT%H:%M:%S")
            time_str = time_obj.strftime("%I:%M %p")
            print(f"🔴 {time_str} — {who}")
            rows += f"<tr><td>{time_str}</td><td>{who}</td></tr>"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Empress Canyon Bookings</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .updated {{ color: grey; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>🏔️ Empress Canyon Bookings</h1>
    <p class="updated">Last updated: {today_str}</p>
    <table>
        <tr><th>Time</th><th>Booked By</th></tr>
        {rows}
    </table>
</body>
</html>"""

    with open("index.html", "w") as f:
        f.write(html)
    print("✅ Saved results to index.html")

except Exception as e:
    print(f"⚠️ Error reading slots: {e}")

driver.quit()

# Push index.html to GitHub
try:
    subprocess.run(["git", "config", "--global", "user.email", "action@github.com"])
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Action"])
    subprocess.run(["git", "add", "index.html"])
    subprocess.run(["git", "commit", "-m", "update bookings"])
    subprocess.run(["git", "push"])
    print("✅ Pushed to GitHub!")
except Exception as e:
    print(f"⚠️ Push error: {e}")