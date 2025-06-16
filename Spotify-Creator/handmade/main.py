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
fake = Faker()

# ——————————————————————————————————————————————
# Chrome-for-Testing v138 + Capsolver extension paths
CHROME_BINARY_PATH       = r"C:/Users/Administrator/Documents/The Spotify Creator Project/chrome-win64/chrome.exe"
CHROMEDRIVER_PATH        = r"C:/Users/Administrator/Documents/The Spotify Creator Project/chromedriver-win64/chromedriver.exe"
CAPSOLVER_EXTENSION_PATH = r"C:/Users/Administrator/Documents/The Spotify Creator Project/capsolver sources"
# ——————————————————————————————————————————————

EMAIL_SEL = (By.ID, "username")
PASS_SEL  = (By.CSS_SELECTOR, "input[type='password']")
NEXT_BTN  = (By.XPATH, "//button[@data-testid='submit']")

# ----------- Helpers -----------

def read(path: Path, sep=None):
    raw = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    return [tuple(r.split(sep,1)) if sep else r for r in raw]


def driver(proxy: str):
    """
    Launch Chrome-for-Testing v138 with matching driver and load the Capsolver unpacked extension.
    Suppress verbose logging.
    """
    opts = Options()
    # point to Chrome-for-Testing binary
    opts.binary_location = CHROME_BINARY_PATH
    # proxy if needed
    opts.add_argument(f"--proxy-server=http://{proxy}")
    # disable sandbox (optional)
    opts.add_argument("--no-sandbox")
    # load your local Capsolver unpacked extension
    opts.add_argument(f"--load-extension={CAPSOLVER_EXTENSION_PATH}")
    # suppress Chrome’s logging
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    # use NUL to discard chromedriver logs on Windows
    svc = Service(CHROMEDRIVER_PATH, log_path=os.devnull)
    return webdriver.Chrome(service=svc, options=opts)

# -------- Utilities ----------

def accept_cookies(drv):
    """Đóng banner cookie OneTrust nếu xuất hiện để tránh intercept."""
    try:
        WebDriverWait(drv, 3).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("→ Đã đóng banner cookies")
    except Exception:
        pass


def js_click(drv, elem):
    drv.execute_script("arguments[0].click()", elem)

def wait_for_recaptcha_solution(drv, timeout=30):
    """
    Wait until the 'g-recaptcha-response' textarea is populated by Capsolver.
    """
    WebDriverWait(drv, timeout).until(
        lambda d: d.execute_script(
            "const el = document.getElementsByName('g-recaptcha-response')[0];"
            "return el && el.value.trim().length > 0;"
        )
    )

def proceed_captcha(drv):
    """
    Wait until Capsolver has solved the reCAPTCHA (g-recaptcha-response populated).
    """
    wait = WebDriverWait(drv, 60)
    wait.until(lambda d: d.execute_script(
        "const el = document.getElementsByName('g-recaptcha-response')[0];"
        "return el && el.value.trim().length > 0;"
    ))
    print("Captcha has been solved. Proceeding to continue step.")

# -------- Phase 3 ----------

def to_password(drv, email: str):
    wait = WebDriverWait(drv, 8)
    box = wait.until(EC.element_to_be_clickable(EMAIL_SEL))
    box.send_keys(Keys.TAB)
    drv.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
    if _has_pass(drv):
        return
    drv.find_element(*NEXT_BTN).click()
    WebDriverWait(drv, 5).until(EC.presence_of_element_located(PASS_SEL))


def _has_pass(drv):
    try:
        WebDriverWait(drv, 4).until(EC.presence_of_element_located(PASS_SEL))
        return True
    except Exception:
        return False

# -------- Phase 4 ----------

def to_profile(drv, password: str):
    WebDriverWait(drv, 8).until(EC.element_to_be_clickable(PASS_SEL)).send_keys(password, Keys.ENTER)
    if _has_profile(drv):
        return
    drv.find_element(By.XPATH, "//span[normalize-space()='Next']/ancestor::button").click()
    WebDriverWait(drv, 5).until(lambda d: _has_profile(d))


def _has_profile(drv):
    try:
        WebDriverWait(drv, 4).until(EC.presence_of_element_located((By.ID, "month")))
        return True
    except Exception:
        return False


def fill_profile(drv):
    """Fill display name, date of birth, and gender, then proceed to the ads step."""
    wait = WebDriverWait(drv, 8)
    wait.until(EC.element_to_be_clickable((By.ID, "displayName"))).send_keys(fake.user_name()[:30])

    # DOB
    Select(wait.until(EC.element_to_be_clickable((By.ID, "month")))).select_by_value(str(random.randint(1, 12)))
    drv.find_element(By.NAME, "day").send_keys(str(random.randint(1, 28)))
    drv.find_element(By.NAME, "year").send_keys(str(random.randint(1990, 2004)))

    # Gender radio label (Man/Woman)
    gender = random.choice(["Man", "Woman"])
    drv.find_element(By.XPATH, f"//label[normalize-space()='{gender}']").click()

    print(f"Profile completed. Selected gender: {gender}")

    # Bấm Next để sang bước ads (phase 4.5)
    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Next']/ancestor::button")))
    try:
        next_btn.click()
    except:
        js_click(drv, next_btn)

# -------- Phase 4.5 ----------

def skip_ads_and_signup(drv):
    """Click 'Sign up' on the ads page, wait for the CAPTCHA iframe, then pause for solver."""

    btn = WebDriverWait(drv, 8).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Sign up']/ancestor::button"))
    )
    # small delay before click so the page has time to render the CAPTCHA
    time.sleep(3)
    btn.click()
    print("Sign up button clicked.")

    # wait for the reCAPTCHA iframe to appear
    WebDriverWait(drv, 15).until(
        EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src,'api2/anchor')]"))
    )
    print("CAPTCHA iframe detected. Waiting for solution.")
    # give Capsolver a few more seconds to solve
    time.sleep(10)

def skip_ads_and_solve_captcha(drv):
    """
    Click 'Sign up', wait for the CAPTCHA iframe (warn only on timeout),
    then pause for Capsolver.
    """
    wait = WebDriverWait(drv, 15)
    sign_up_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[normalize-space()='Sign up']/ancestor::button")
    ))
    time.sleep(2)
    sign_up_btn.click()
    print("Sign up button clicked.")
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//iframe[contains(@src,'api2/anchor')]")
        ))
        print("CAPTCHA iframe detected.")
    except TimeoutException:
        print("Warning: CAPTCHA iframe did not appear within 15 seconds.")
    # give Capsolver time to solve
    time.sleep(12)

def press_continue(drv):
    """
    Click 'Continue' once enabled, then wait for navigation and an extra 30s.
    """
    wait = WebDriverWait(drv, 60)
    start_url = drv.current_url

    continue_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[normalize-space()='Continue']/ancestor::button[not(@disabled)]")
    ))
    continue_btn.click()
    print("Clicked 'Continue'. Waiting for navigation…")

    # wait for URL to change
    try:
        WebDriverWait(drv, 30).until(lambda d: d.current_url != start_url)
        print("Navigation detected.")
    except TimeoutException:
        print("Warning: page did not navigate within 30 seconds after Continue.")
    # wait 30 seconds for Spotify to finalize account creation
    print("Waiting an additional 30 seconds for account provisioning…")
    time.sleep(30)

def fill_email_step(drv, email):
    drv.get(SIGNUP_URL)
    wait = WebDriverWait(drv, 10)
    # fill email + confirm
    wait.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(email)
    drv.find_element(By.ID, "confirm").send_keys(email)
    # click Next instead of ENTER
    nxt = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@data-testid,'next-button')]")
    ))
    nxt.click()
    print(f"[{email}] Email step done.")

def fill_password_step(drv, password):
    wait = WebDriverWait(drv, 10)
    # fill password
    wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(password)
    # click Next instead of ENTER
    nxt = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@data-testid,'next-button')]")
    ))
    nxt.click()
    print("Password step done.")

def fill_profile_step(drv):
    wait = WebDriverWait(drv, 10)
    wait.until(EC.element_to_be_clickable((By.ID, "month"))).select_by_value(str(random.randint(1,12)))
    drv.find_element(By.NAME, "day").send_keys(str(random.randint(1,28)))
    drv.find_element(By.NAME, "year").send_keys(str(random.randint(1990,2004)))
    gender = random.choice(["male","female"])
    drv.find_element(By.XPATH, f"//input[@value='{gender}']/..").click()
    # click Next
    nxt = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@data-testid,'next-button')]")
    ))
    nxt.click()
    print("Profile step done.")

def signup_one(drv, email, password):
    fill_email_step(drv, email)
    fill_password_step(drv, password)
    fill_profile_step(drv)
    skip_ads_and_solve_captcha(drv)
    press_continue(drv)
    print(f"[{email}] Signup flow completed.\n")

# ------------- MAIN -------------~
if __name__ == '__main__':
    email, pw = read(ACCOUNTS_FILE, ":")[0]
    proxy = read(PROXIES_FILE)[0]

    drv = driver(proxy)
    drv.get(SIGNUP_URL)

    try:
        to_password(drv, email)
        to_profile(drv, pw)
        fill_profile(drv)
        skip_ads_and_signup(drv)
        proceed_captcha(drv)
        press_continue(drv)
    except Exception as e:
        print("⚠️  Error:", e)

    print("Process completed.")
    drv.quit()