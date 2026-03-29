from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

URL = "https://nsw.rezexpert.com/nswctobookdtm?business_code=500551"
EMAIL = "James@myadventuregroup.com.au"
PASSWORD = "yfUR^8a^XAqhpt^T"  # ⚠️ update this

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
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

# Step 8 - Click today's date cell
try:
    today = datetime.now().strftime("%Y-%m-%dT00:00:00")
    today_cell = driver.find_element(By.XPATH, f"//td[@date='{today}']")
    driver.execute_script("arguments[0].click();", today_cell)
    print(f"✅ Clicked today: {today}")
    time.sleep(5)
except Exception as e:
    print(f"⚠️ Date cell error: {e}")

# Step 9 - Find all SOLD slots and print them
try:
    sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class, 'Sold')]")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🏔️  EMPRESS CANYON - BOOKED SLOTS FOR {today_str}")
    print("-" * 45)

    if not sold_slots:
        print("✅ No bookings today!")
    else:
        for slot in sold_slots:
            check_in = slot.get_attribute("check_in_date")
            who = slot.get_attribute("parent_client_label")
            # Format time nicely
            time_obj = datetime.strptime(check_in, "%Y-%m-%dT%H:%M:%S")
            time_str = time_obj.strftime("%I:%M %p")
            print(f"🔴 {time_str} — {who}")

    print("-" * 45)

except Exception as e:
    print(f"⚠️ Error reading slots: {e}")

input("\nPress Enter to close...")
driver.quit()