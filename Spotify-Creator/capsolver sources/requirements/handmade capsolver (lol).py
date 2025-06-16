"""
Spotify Creator – Phase 4 → 4.5 (profile Next → ads Sign up) – fixed syntax
==========================================================================

* Sửa lỗi cú pháp `next_btn.click():` (bỏ dấu `:`).  
* Loại bỏ đoạn mã lặp dư dưới `fill_profile`.
* Luồng: Profile → **Next** → Ads page → **Sign up** → Captcha.
"""

from pathlib import Path
import random
from faker import Faker

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ------------ Config ------------
ACCOUNTS_FILE = Path("input_accounts.txt")
PROXIES_FILE  = Path("proxies.txt") #put proxies and inputs in the same folder w this script
SIGNUP_URL    = "https://www.spotify.com/signup"
CHROME_MAJOR  = 138
fake = Faker()

EMAIL_SEL = (By.ID, "username")
PASS_SEL  = (By.CSS_SELECTOR, "input[type='password']")
NEXT_BTN  = (By.XPATH, "//button[@data-testid='submit']")

# ----------- Helpers -----------

def read(path: Path, sep=None):
    raw = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    return [tuple(r.split(sep,1)) if sep else r for r in raw]


def driver(proxy: str):
    opt = uc.ChromeOptions()
    opt.add_argument(f"--proxy-server=http://{proxy}")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--load-extension=C:/Users/lbee/Downloads/capsolver sources") #replace directly the extension FOLDER. after '='
    opt.set_browser_version("138")
    return uc.Chrome(options=opt, headless=False, version_main=CHROME_MAJOR)

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

# -------- Phase 3 ----------

def to_password(drv, email: str):
    wait = WebDriverWait(drv, 8)
    box = wait.until(EC.element_to_be_clickable(EMAIL_SEL))
    box.send_keys(email, Keys.ENTER)
    if _has_pass(drv):
        return
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
    """Điền display name + DOB + gender, rồi bấm Next để sang trang ads."""
    wait = WebDriverWait(drv, 8)
    wait.until(EC.element_to_be_clickable((By.ID, "displayName"))).send_keys(fake.user_name()[:30])

    # DOB
    Select(wait.until(EC.element_to_be_clickable((By.ID, "month")))).select_by_value(str(random.randint(1, 12)))
    drv.find_element(By.NAME, "day").send_keys(str(random.randint(1, 28)))
    drv.find_element(By.NAME, "year").send_keys(str(random.randint(1990, 2004)))

    # Gender radio label (Man/Woman)
    gender = random.choice(["Man", "Woman"])
    drv.find_element(By.XPATH, f"//label[normalize-space()='{gender}']").click()

    print(f"✅ Profile điền xong – gender {gender}")

    # Bấm Next để sang bước ads (phase 4.5)
    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Next']/ancestor::button")))
    try:
        next_btn.click()
    except Exception:
        js_click(drv, next_btn)

# -------- Phase 4.5 ----------

def skip_ads_and_signup(drv):
    """Bỏ qua trang quảng cáo: click Sign up ngay."""
    try:
        btn = WebDriverWait(drv, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Sign up']/ancestor::button"))
        )
        btn.click()
        print("→ Đã click Sign up (skip ads page)")
    except Exception as e:
        print("⚠️  Không tìm thấy nút Sign up:", e)

# ------------- MAIN -------------
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
    except Exception as e:
        print("⚠️  Error:", e)

    input("\nDừng ở captcha → Enter để đóng…")
    drv.quit()
