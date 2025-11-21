import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
TARGET_URL = "https://pbssd.gov.in/partners/centres/0966289037ad9846c5e994be2a91bafa/6512bd43d9caa6e02c990b0a82652dca/cfcd208495d565ef66e7dff9f98764da/0"

print("-- Full Scraper for PBSSD (Centres and Courses) --")
print("-- A Chrome browser will now open. This will take a few minutes as it clicks each button. --")

# Setup Selenium WebDriver
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

def scrape_full_data():
    try:
        driver.get(TARGET_URL)
        
        # Wait for the main table to load first
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Find all rows in the main table, skipping the header
        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
        total_rows = len(rows)
        print(f"-- Found {total_rows} training centres to process. --\n")
        
        # Prepare to print SQL statements
        print("-- ========= INSERT DATA INTO 'centres' TABLE =========\n")

        # We loop through each row by its index to avoid issues
        for i in range(total_rows):
            # Re-find the rows in each iteration to avoid stale element errors
            current_row = driver.find_elements(By.XPATH, "//table/tbody/tr")[i]
            cells = current_row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 5:
                continue

            # --- Scrape Centre Data (from the main table) ---
            centre_name = cells[2].text.strip().replace("'", "''")
            contact_no = cells[3].text.strip().replace("'", "''")
            address = cells[4].text.strip().replace("'", "''")
            
            print(
                f"INSERT INTO centres (name, contact, address, city, state, source_url) VALUES "
                f"('{centre_name}', '{contact_no}', '{address}', 'NORTH 24 PARGANAS', 'WEST BENGAL', '{TARGET_URL}');"
            )

            # --- Scrape Course Data (by clicking the button) ---
            try:
                # Find and click the "View Course(s)" button in the current row
                view_button = cells[5].find_element(By.TAG_NAME, "a")
                view_button.click()
                
                # Wait for the popup (modal) to become visible
                modal = wait.until(EC.visibility_of_element_located((By.ID, "showCourse")))
                
                # Inside the modal, find the course table and its rows
                course_rows = modal.find_elements(By.XPATH, ".//table/tbody/tr")
                
                if i == 0: # Print the header only once
                    print("\n-- ========= INSERT DATA INTO 'careers' TABLE =========\n")

                for course_row in course_rows:
                    course_cells = course_row.find_elements(By.TAG_NAME, "td")
                    if len(course_cells) >= 3:
                        sector = course_cells[1].text.strip().replace("'", "''")
                        course_name = course_cells[2].text.strip().replace("'", "''")
                        
                        print(
                            f"INSERT INTO careers (name, sector, source_url) VALUES "
                            f"('{course_name}', '{sector}', '{TARGET_URL}');"
                        )
                
                # Find and click the close button of the modal
                close_button = modal.find_element(By.XPATH, ".//button[contains(text(), '×')]")
                close_button.click()
                
                # Wait for the modal to disappear
                wait.until(EC.invisibility_of_element_located((By.ID, "showCourse")))
                time.sleep(1) # A small pause to ensure the page is stable

            except Exception as e:
                print(f"-- Could not process courses for {centre_name}. Skipping. Error: {e} --")
                continue

    except Exception as e:
        print(f"\n-- An error occurred during scraping: {e} --")
    finally:
        print("\n-- Closing browser... --")
        driver.quit()

if __name__ == "__main__":
    scrape_full_data()
    print("\n-- Scraping complete. --")