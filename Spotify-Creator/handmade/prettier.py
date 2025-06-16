"""
Spotify Creator – Phase 4 → 4.5 (profile Next → ads Sign up) – fixed syntax
==========================================================================

* Sửa lỗi cú pháp `next_btn.click():` (bỏ dấu `:`).  
* Loại bỏ đoạn mã lặp dư dưới `fill_profile`.
* Loại bỏ đoạn mã lặp dư dưới `press_continue`.
* Luồng: Profile → **Next** → Ads page → **Sign up** → Captcha.
"""

#systemd
from faker import Faker
from pathlib import Path
import random
import os # For constructing absolute paths
import time # For basic delays if needed, though explicit waits are preferred
import sys
import itertools

# selenium & chrome-for-testing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

#selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# ------------ Config ------------
ACCOUNTS_FILE = Path("input_accounts.txt")
PROXIES_FILE  = Path("proxies.txt") #put proxies and inputs in the same folder w this script
SIGNUP_URL    = "https://www.spotify.com/signup"
CHROME_BINARY = (
    r"C:/Users/Administrator/Documents/The Spotify Creator Project/"
    "chrome-win64/chrome.exe"
)
CHROMEDRIVER_PATH = (
    r"C:/Users/Administrator/Documents/The Spotify Creator Project/"
    "chromedriver-win64/chromedriver.exe"
)
CAPSOLVER_PATH = (
    r"C:/Users/Administrator/Documents/The Spotify Creator Project/"
    "capsolver sources"
)

fake = Faker()

# ——————————————————————————————————————————————
# Chrome-for-Testing v138 + Capsolver extension paths
# ——————————————————————————————————————————————

EMAIL_SEL = (By.ID, "username")
PASS_SEL  = (By.CSS_SELECTOR, "input[type='password']")
NEXT_BTN  = (By.XPATH, "//button[@data-testid='submit']")

# ----------- Helpers -----------

def read_accounts(path: Path, sep: str = ":") -> list[tuple[str, str]]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    return [tuple(line.split(sep, 1)) for line in lines]


def make_driver(proxy: str | None = None) -> webdriver.Chrome:
    options = Options()
    options.binary_location = CHROME_BINARY
    if proxy:
        options.add_argument(f"--proxy-server=http://{proxy}")
    options.add_argument("--no-sandbox")
    options.add_argument(f"--load-extension={CAPSOLVER_PATH}")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    service = Service(CHROMEDRIVER_PATH, log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)


def fill_email_step(driver: webdriver.Chrome, email: str) -> None:
    driver.get(SIGNUP_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(email)
    driver.find_element(By.ID, "confirm").send_keys(email)
    next_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@data-testid,'next-button')]")
        )
    )
    next_btn.click()
    print(f"[{email}] Email step completed.")


def fill_password_step(driver: webdriver.Chrome, password: str) -> None:
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(
        password
    )
    next_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@data-testid,'next-button')]")
        )
    )
    next_btn.click()
    print("Password step completed.")


def fill_profile_step(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 10)
    Select(driver.find_element(By.ID, "month")).select_by_value(
        str(random.randint(1, 12))
    )
    driver.find_element(By.NAME, "day").send_keys(str(random.randint(1, 28)))
    driver.find_element(By.NAME, "year").send_keys(str(random.randint(1990, 2004)))
    gender = random.choice(["male", "female"])
    driver.find_element(By.XPATH, f"//input[@value='{gender}']/..").click()
    next_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@data-testid,'next-button')]")
        )
    )
    next_btn.click()
    print("Profile step completed.")


def skip_ads_and_solve_captcha(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 15)
    btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[normalize-space()='Sign up']/ancestor::button")
        )
    )
    time.sleep(2)
    btn.click()
    print("Sign up button clicked.")
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//iframe[contains(@src,'api2/anchor')]")
            )
        )
        print("CAPTCHA iframe detected.")
    except TimeoutException:
        print("Warning: CAPTCHA iframe did not appear in time.")
    time.sleep(12)  # allow Capsolver to finish


def press_continue(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 60)
    start_url = driver.current_url
    btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[normalize-space()='Continue']/ancestor::button")
        )
    )
    btn.click()
    print("Clicked Continue, waiting for navigation…")
    try:
        WebDriverWait(driver, 30).until(lambda d: d.current_url != start_url)
        print("Navigation detected.")
    except TimeoutException:
        print("Warning: no navigation after Continue.")
    print("Waiting 30 seconds for account setup…")
    time.sleep(30)
    print("Account setup should now be complete.")


def signup_one(
    driver: webdriver.Chrome, email: str, password: str
) -> None:
    fill_email_step(driver, email)
    fill_password_step(driver, password)
    fill_profile_step(driver)
    skip_ads_and_solve_captcha(driver)
    press_continue(driver)
    print(f"[{email}] Signup flow completed.\n")


def main() -> None:
    if not os.path.exists(CHROME_BINARY) or not os.path.exists(CHROMEDRIVER_PATH):
        print("Error: Chrome binary or Chromedriver not found.")
        sys.exit(1)

    accounts = read_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("Error: No accounts in input_accounts.txt.")
        sys.exit(1)

    proxies = [p[0] for p in read_accounts(PROXIES_FILE)] if PROXIES_FILE.exists() else []
    proxy_cycle = itertools.cycle(proxies) if proxies else None

    driver = make_driver(next(proxy_cycle) if proxy_cycle else None)
    print("Browser launched. Starting signup loop.")

    try:
        for idx in itertools.count():
            email, pwd = accounts[idx % len(accounts)]
            proxy = next(proxy_cycle) if proxy_cycle else None
            print(f"Signing up {email} (proxy={proxy}).")
            try:
                signup_one(driver, email, pwd)
                driver.delete_all_cookies()
            except WebDriverException:
                print("WebDriver error or browser closed. Exiting.")
                break
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        driver.quit()
        print("Browser session ended.")


if __name__ == "__main__":
    main()