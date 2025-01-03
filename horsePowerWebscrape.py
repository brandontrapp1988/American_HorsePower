import csv
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
import time
import os


# Selenium setup for headless mode
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)  # Ensure the appropriate WebDriver is installed


# Base URL for pagination
base_url = "https://american-horsepower.de/en/american-horsepower-us-car-parts-shop-top-brands-large-choice?order=name-asc&p="

# Shared product data list
product_data = []


# Function to scrape a single page
def scrape_page(page_number, base_url):
    driver = create_driver()  # Create a new driver instance for each thread
    try:
        current_url = f"{base_url}{page_number}"
        driver.get(current_url)
        print(f"Scraping page: {current_url}")

        # Locate all product containers using the `cms-listing-col` class
        products = driver.find_elements(By.CSS_SELECTOR, "div.cms-listing-col")
        page_data = []  # Temporary storage for page-specific data

        for product in products:
            try:
                # Extract product details
                product_info = {}
                name_element = product.find_element(By.CSS_SELECTOR, "a.product-name")
                name = name_element.get_attribute("title").replace('"', '')  # Remove double quotes
                product_info["NAME"] = f"American Horsepower - {name}"

                url = name_element.get_attribute("href")
                if len(url) <= 255:  # Only include the URL if it's within 255 characters
                    product_info["URL"] = url

                try:
                    part_number = product.find_element(By.CSS_SELECTOR, ".product-ordernumber").text.strip()
                    product_info["PART_NUMBER"] = part_number
                except Exception:
                    pass  # Skip PART_NUMBER if not found

                try:
                    price = product.find_element(By.CSS_SELECTOR, "span.product-price").text.strip()
                    product_info["PRICE"] = price
                except Exception:
                    product_info["PRICE"] = "Unavailable"  # Default to "Unavailable" if not found

                try:
                    inventory_element = product.find_element(By.CSS_SELECTOR, ".badge.bg-success span")
                    inventory = inventory_element.text.strip() if inventory_element else "Unavailable"
                    product_info["INVENTORY"] = inventory
                except Exception:
                    product_info["INVENTORY"] = "Unavailable"  # Default to "Unavailable" if not found

                product_info["Competitor"] = "American Horsepower"  # Add static competitor name
                page_data.append(product_info)  # Add product info to the page-specific list
            except Exception as e:
                print(f"Error scraping product: {e}")

        return page_data
    except Exception as e:
        print(f"Error scraping page {page_number}: {e}")
        return []
    finally:
        driver.quit()  # Ensure the browser is closed after use


# Parallelize scraping using ThreadPoolExecutor
def scrape_pages_in_parallel(base_url, page_ranges):
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust `max_workers` based on your system capacity
        futures = [executor.submit(scrape_page, page, base_url) for page in page_ranges]
        results = [future.result() for future in futures]
    # Flatten the list of results
    all_data = [item for sublist in results for item in sublist]
    return all_data


# Main scraping logic
print("Starting scraping...")
all_page_numbers = list(range(1, 123))  # Main pages (1-122)
product_data.extend(scrape_pages_in_parallel(base_url, all_page_numbers))

# Additional pages
additional_pages = [
    (
    "https://american-horsepower.de/en/american-horsepower-us-car-parts-neu-im-shop-top-brands-large-choice?order=name-asc&p=",
    range(1, 3)),
    (
    "https://american-horsepower.de/en/american-horsepower-us-car-parts-sale-top-brands-large-choice?order=name-asc&p=",
    range(1, 11)),
    (
    "https://american-horsepower.de/en/american-horsepower-us-car-parts-auf-lager-top-brands-large-choice?order=name-asc&p=",
    range(1, 20)),
]
for base, page_range in additional_pages:
    product_data.extend(scrape_pages_in_parallel(base, page_range))

# Single pages
single_pages = [
    "https://american-horsepower.de/en/american-horsepower-us-car-parts-vouchers-top-brands-large-choice",
    "https://american-horsepower.de/en/american-horsepower-us-car-parts-garage-by-ahpfloor-top-brands-large-choice"
]
for single_page in single_pages:
    product_data.extend(scrape_page(1, single_page))

# Save the scraped data to a CSV file
csv_file = "american_horsepower_products.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["Competitor", "NAME", "URL", "PART_NUMBER", "PRICE", "INVENTORY"])
    writer.writeheader()
    writer.writerows(product_data)

print(f"Scraped data saved to {csv_file}")

# Push the CSV file to GitHub
try:
    repo_path = os.getcwd()  # Assume the script is run from the repo directory
    csv_path = os.path.join(repo_path, csv_file)

    # Git commands to add, commit, and push the CSV
    subprocess.run(["git", "add", csv_path], check=True)
    subprocess.run(["git", "commit", "-m", "Add updated product data CSV"], check=True)
    subprocess.run(["git", "push"], check=True)  # Simplified push command
    print(f"{csv_file} successfully pushed to GitHub.")
except subprocess.CalledProcessError as e:
    print(f"Error with Git command: {e}")
except Exception as e:
    print(f"General error pushing to GitHub: {e}")
