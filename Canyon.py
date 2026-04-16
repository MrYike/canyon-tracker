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
    {"name": "Empress",      "unit_type_id": 3131},
    {"name": "Grand Canyon", "unit_type_id": 3133},
    {"name": "Narrow Neck",  "unit_type_id": 3151},
]

# ================== SETUP ==================
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")         # new headless mode — better JS rendering
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

start_time = time.time()

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

driver.get(URL)
time.sleep(8)

# ================== COOKIE / TERMS ==================
try:
    driver.find_element(By.LINK_TEXT, "Got it!").click()
    time.sleep(2)
except:
    pass

try:
    driver.find_element(By.NAME, "radPreConditionAccept").click()
    time.sleep(1)
    driver.find_element(By.ID, "divPreConditionsClose").click()
    time.sleep(3)
    print("✅ Accepted terms!")
except:
    pass

# ================== LOGIN ==================
driver.find_element(By.PARTIAL_LINK_TEXT, "ogin").click()
time.sleep(3)
driver.find_element(By.ID, "txtEmail").send_keys(EMAIL)
driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
driver.find_element(By.ID, "btnLoginNext").click()
time.sleep(6)
print("✅ Logged in!")

print(f"\n🚀 STARTING SCAN — {len(CANYONS)} canyons × next {NUM_DAYS} days")

all_data = {}


def wait_for_calendar(driver, timeout=15):
    """Wait until at least one td[@date] cell is present in the DOM."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//td[@date]"))
        )
        time.sleep(2)  # extra settle time for full grid render
        return True
    except:
        return False


def get_visible_dates(driver):
    """Return the set of date strings currently shown on the calendar."""
    tds = driver.find_elements(By.XPATH, "//td[@date]")
    dates = set()
    for td in tds:
        d = td.get_attribute("date")
        if d:
            dates.add(d)
    return dates


def click_date(driver, date_str):
    """
    Click a calendar cell for date_str (YYYY-MM-DD).
    Uses explicit wait + scroll into view for headless reliability.
    Returns True if successful.
    """
    fmt = date_str + "T00:00:00"
    try:
        cell = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//td[@date='{fmt}']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", cell)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", cell)
        time.sleep(5)
        return True
    except:
        return False


def try_next_month(driver):
    """
    Navigate to the next month on the booking calendar.
    The site uses a small div arrow styled with border-left: 20px solid white.
    We filter out the aMenuBar nav elements which are a false positive.
    """
    try:
        # Get all border-left divs, skip nav menu items
        candidates = driver.find_elements(
            By.XPATH,
            "//div[contains(@style,'border-left') and contains(@style,'solid')]"
        )
        for el in candidates:
            cls = el.get_attribute("class") or ""
            style = el.get_attribute("style") or ""
            text = el.text.strip()
            # Skip the top nav menu bar items (they have text like "Home", "Trip Returns")
            if "aMenuBar" in cls or text in ("Home", "Trip Returns", "Logout", ""):
                continue
            # The real next-month arrow has no meaningful text and border-left ~20px
            if "20px" in style or "15px" in style:
                driver.execute_script("arguments[0].scrollIntoView(true);", el)
                driver.execute_script("arguments[0].click();", el)
                print("      ➡️  Next month")
                time.sleep(4)
                return True
    except:
        pass
    return False


# ================== MAIN SCRAPE LOOP ==================
for canyon in CANYONS:
    name = canyon["name"]
    uid = canyon["unit_type_id"]
    all_data[name] = {}

    print(f"\n{'='*90}")
    print(f"🏔️  SCANNING: {name}")
    print(f"{'='*90}")

    try:
        # Fresh page load for each canyon
        driver.get(URL)
        time.sleep(6)

        # Re-accept terms if it reappears
        try:
            driver.find_element(By.NAME, "radPreConditionAccept").click()
            time.sleep(1)
            driver.find_element(By.ID, "divPreConditionsClose").click()
            time.sleep(3)
        except:
            pass

        # Select canyon
        canyon_row = wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//div[@unit_type_id='{uid}']")
        ))
        driver.execute_script("arguments[0].click();", canyon_row)
        print(f"✅ Selected {name}")
        time.sleep(5)

        # Click Book
        book_xpath = f"//div[@onclick=\"selectUnitType('nsw_cto_select_canyoning_location', {{iUnitTypeId:{uid}}});\"]"
        book_btn = wait.until(EC.presence_of_element_located((By.XPATH, book_xpath)))
        driver.execute_script("arguments[0].click();", book_btn)
        print(f"✅ Clicked Book")
        time.sleep(6)

        # Wait for calendar to render
        if not wait_for_calendar(driver):
            print(f"❌ Calendar never loaded for {name}")
            continue

        # Show what dates are currently visible
        visible = get_visible_dates(driver)
        print(f"   📆 Calendar loaded — {len(visible)} date cells visible")

        navigated_to_next = False

        for day_offset in range(NUM_DAYS):
            target_dt = datetime.now() + timedelta(days=day_offset)
            date_str = target_dt.strftime("%Y-%m-%d")
            fmt = date_str + "T00:00:00"

            print(f"   📅 {date_str} ", end="", flush=True)

            # Check if date is visible before attempting click
            if fmt not in visible:
                # Try navigating to next month (only once per canyon)
                if not navigated_to_next:
                    ok = try_next_month(driver)
                    if ok:
                        navigated_to_next = True
                        time.sleep(2)
                        visible = get_visible_dates(driver)
                        print(f"[now {len(visible)} cells] ", end="", flush=True)

                if fmt not in visible:
                    print("⚠️  Not on calendar — skipping")
                    all_data[name][date_str] = {"sold": []}
                    continue

            # Click the date
            if not click_date(driver, date_str):
                print("⚠️  Could not reach")
                all_data[name][date_str] = {"sold": []}
                continue

            print("✅")

            # Read booked slots
            sold = []
            try:
                sold_slots = driver.find_elements(By.XPATH, "//td[contains(@class,'Sold')]")
                for slot in sold_slots:
                    check_in = slot.get_attribute("check_in_date")
                    who = slot.get_attribute("parent_client_label") or "Unknown"
                    if check_in:
                        sold.append({"time": check_in, "company": who})
            except:
                pass

            all_data[name][date_str] = {"sold": sold}

            if not sold:
                print(f"      ✅ Fully available")
            else:
                for b in sold:
                    try:
                        t = datetime.strptime(b["time"], "%Y-%m-%dT%H:%M:%S").strftime("%I:%M %p")
                    except:
                        t = b["time"]
                    print(f"      🔴 {t} — {b['company']}")

    except Exception as e:
        print(f"❌ Error with {name}: {e}")

    print(f"   ↩️  Done {name}")

driver.quit()

# ================== SAVE ==================
updated = datetime.now().strftime("%Y-%m-%d %H:%M")
output = {"updated": updated, "data": all_data}

with open("data.json", "w") as f:
    json.dump(output, f, indent=2)

elapsed = int(time.time() - start_time)
print(f"\n✅ Saved data.json")
print(f"⏱️  Finished at {updated} ({elapsed // 60}m {elapsed % 60}s)")
