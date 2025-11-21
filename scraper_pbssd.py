import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# The target URL you found
TARGET_URL = "https://pbssd.gov.in/partners/centres/0966289037ad9846c5e994be2a91bafa/6512bd43d9caa6e02c990b0a82652dca/cfcd208495d565ef66e7dff9f98764da/0"

print("-- Scraping Training Centres from PBSSD using Selenium --")
print("-- A Chrome browser will now open. Please wait. --")

# Setup Selenium WebDriver to run a visible browser
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=service, options=options)

def scrape_with_selenium():
    try:
        # 1. Open the URL in the Chrome browser
        driver.get(TARGET_URL)
        
        # 2. Wait for the table element to be loaded on the page
        wait = WebDriverWait(driver, 20) # Wait up to 20 seconds
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # 3. Get the HTML of the page *after* it has fully loaded
        page_html = driver.page_source
        
        # 4. Use BeautifulSoup to parse the loaded HTML (it's easier than using Selenium for parsing)
        soup = BeautifulSoup(page_html, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("-- ERROR: Could not find the data table on the page. --")
            return
            
        rows = table.find_all('tr')[1:] # Skip the header row

        print(f"-- Found {len(rows)} training centres. Generating SQL... --\n")
        print("-- ========= INSERT DATA INTO 'centres' TABLE =========\n")

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                centre_name = cells[2].text.strip().replace("'", "''")
                contact_no = cells[3].text.strip().replace("'", "''")
                address = cells[4].text.strip().replace("'", "''")
                
                print(
                    f"INSERT INTO centres (name, contact, address, city, state, source_url) VALUES "
                    f"('{centre_name}', '{contact_no}', '{address}', 'NORTH 24 PARGANAS', 'WEST BENGAL', '{TARGET_URL}');"
                )

    except Exception as e:
        print(f"\n-- An error occurred during scraping: {e} --")
    finally:
        # 5. Important: Close the browser
        print("\n-- Closing browser... --")
        driver.quit()

if __name__ == "__main__":
    scrape_with_selenium()
    print("\n-- Scraping complete. --")