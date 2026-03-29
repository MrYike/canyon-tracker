from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

URL = "https://www.worldometers.info/world-population/"
CHECK_EVERY = 1  # seconds

def check_population():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(URL)
        time.sleep(5)

        body = driver.find_element(By.TAG_NAME, "body").text

        # Find the population number — it's the line after "Current World Population"
        lines = body.split("\n")
        for i, line in enumerate(lines):
            if "Current World Population" in line:
                population = lines[i + 1].strip()
                print(f"🌍 Population: {population}")
                print(f"🕐 Checked at: {datetime.now().strftime('%H:%M:%S')}")
                return

        print("⚠️ Couldn't find population")

    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        driver.quit()

print("👀 Monitoring started. Press CTRL + C to stop.\n")

while True:
    check_population()
    time.sleep(CHECK_EVERY)
