import requests
import json

# --- Configuration ---
TARGET_CITY = "New Delhi"
# A list of sector IDs to fetch courses from. (e.g., 2=IT, 4=Healthcare, 7=Electronics)
# You can find these IDs by inspecting the network traffic on the website.
SECTOR_IDS = [2, 4, 7, 13, 22] 

print("-- SQL Data Generation for Vocational Udaan --")
print("-- WARNING: This script targets a highly unstable API and may fail without notice. --")

def scrape_skill_india_courses():
    """Fetches course data directly from the Skill India Digital API."""
    print("\n-- Fetching courses from Skill India Digital API...")
    
    # CRITICAL: This is the newest known API URL. It is the part that is most likely to break.
    API_URL = "https://api.skillindiadigital.gov.in/api/v3/user/courses/search"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Referer': 'https://www.skillindiadigital.gov.in/',
    }
    
    for sector_id in SECTOR_IDS:
        print(f"---> Fetching courses for Sector ID: {sector_id}")
        payload = {"request": {"filters": {"sector_id": [sector_id], "course_mode": ["Offline", "Online", "Hybrid"]}}}
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            courses = response.json().get('result', {}).get('response', [])
            
            for course in courses:
                name = course.get('course_name', 'N/A').replace("'", "''")
                sector = course.get('sector_name', 'N/A').replace("'", "''")
                description = course.get('course_description', '').replace("'", "''")
                
                print(
                    f"INSERT INTO careers (name, sector, description, source_url) VALUES "
                    f"('{name}', '{sector}', '{description}', 'skillindia_api');"
                )
        except requests.exceptions.RequestException as e:
            print(f"---> ERROR: Could not fetch courses for Sector ID {sector_id}. Reason: {e}")

def scrape_skill_india_centres():
    """Fetches training centre data for a specific city from the API."""
    print(f"\n-- Fetching Training Centres in {TARGET_CITY} from Skill India Digital API...")
    
    # CRITICAL: This is the newest known API URL. It is the part that is most likely to break.
    API_URL = "https://api.skillindiadigital.gov.in/api/v3/user/tcs/search"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Referer': 'https://www.skillindiadigital.gov.in/'
    }
    payload = {"request": {"filters": {"city": [TARGET_CITY]}}}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        centres = response.json().get('result', {}).get('response', [])
        
        for centre in centres:
            name = centre.get('tc_name', 'N/A').replace("'", "''")
            address = centre.get('address', {}).get('address_line_1', '').replace("'", "''")
            pincode = centre.get('address', {}).get('pincode', '')
            city = centre.get('address', {}).get('city', '').replace("'", "''")
            state = centre.get('address', {}).get('state', '').replace("'", "''")
            sector_list = centre.get('sector', [])
            sector = sector_list[0].get('name', 'General').replace("'", "''") if sector_list and isinstance(sector_list[0], dict) else 'General'
            
            print(
                f"INSERT INTO centres (name, address, pincode, city, state, sector, source_url) VALUES "
                f"('{name}', '{address}', '{pincode}', '{city}', '{state}', '{sector}', 'skillindia_api');"
            )
    except requests.exceptions.RequestException as e:
        print(f"-- ERROR: Could not fetch training centres. Reason: {e}")

if __name__ == "__main__":
    scrape_skill_india_courses()
    scrape_skill_india_centres()
    print("\n-- Data generation complete. Check the data.sql file. --")