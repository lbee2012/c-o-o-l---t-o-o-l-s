#!/usr/bin/env node
/**
 * Spotify Creator – Phase 4 → 4.5 (profile → ads signup) – JavaScript port
 * -----------------------------------------------------------------------
 * Converted from the original Python implementation. Automates the Spotify
 * signup flow, including Capsolver-assisted CAPTCHA solving, using
 * selenium-webdriver for Node.js.
 */

const fs = require('fs/promises');
const path = require('path');

function requireOrExit(moduleName, hint) {
  try {
    return require(moduleName);
  } catch (err) {
    console.error(`Missing dependency: ${moduleName}`);
    if (hint) {
      console.error(`→ Install with: ${hint}`);
    }
    process.exit(1);
  }
}
// npm install selenium-webdriver @faker-js/faker
const selenium = requireOrExit('selenium-webdriver', 'npm install selenium-webdriver');
const chrome = requireOrExit('selenium-webdriver/chrome');
const { faker } = requireOrExit('@faker-js/faker', 'npm install @faker-js/faker');

const { By, Key, until } = selenium;
const { Select } = requireOrExit('selenium-webdriver/lib/select');

// ------------ Config ------------
const ACCOUNTS_FILE = path.resolve(__dirname, 'input_accounts.txt');
const PROXIES_FILE = path.resolve(__dirname, 'proxies.txt');
const OUTPUT_FILE = path.resolve(__dirname, 'output_accounts.txt');
const SIGNUP_URL = 'https://www.spotify.com/my-en/signup';
const DOWNLOAD_SUCCESS_URL = 'https://www.spotify.com/my-en/download/windows/';

const USE_CAPSOLVER = true; // set true if you still want to load the Capsolver extension
const CHROME_LANGUAGE = 'ms-MY'; // Malay locale so Spotify serves the MY experience
const MAX_PARALLEL_DRIVERS = 7; // number of simultaneous Chrome sessions

const CHROME_BINARY_PATH = path.resolve(__dirname, '..', 'chrome-win64', 'chrome.exe');
const CHROMEDRIVER_PATH = path.resolve(__dirname, '..', 'chromedriver-win64', 'chromedriver.exe');
const CAPSOLVER_EXTENSION_PATH = path.resolve(__dirname, '..', 'capsolver-sources');
const CAPSOLVER_EXTENSION_PATH_SANITIZED = CAPSOLVER_EXTENSION_PATH.replace(/\\/g, '/');

const SELECTORS = {
  emailInput: By.id('username'),
  passwordInput: By.css("input[type='password']"),
  nextButton: By.xpath("//button[@data-testid='submit']"),
};

// ----------- Helpers -----------
async function readLines(filePath, separator) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    const lines = content
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);

    if (!separator) {
      return lines;
    }

    return lines.map((line) => {
      const idx = line.indexOf(separator);
      if (idx === -1) {
        return [line];
      }
      const left = line.slice(0, idx).trim();
      const right = line.slice(idx + separator.length).trim();
      return [left, right];
    });
  } catch (err) {
    throw new Error(`Failed to read ${filePath}: ${err.message}`);
  }
}

function parseProxy(line) {
  if (!line) {
    return null;
  }
  const parts = line.split(':');
  if (parts.length === 4) {
    const [username, password, host, port] = parts;
    return { host, port, username, password };
  }
  if (parts.length >= 2) {
    const [host, port, username, password] = parts;
    return { host, port, username, password };
  }
  throw new Error(`Proxy entry must look like ip:port or login:pass:ip:port, got: ${line}`);
}

async function recordSuccessfulAccount(email, password) {
  const entry = `${email}\n`;
  try {
    await fs.appendFile(OUTPUT_FILE, entry, 'utf8');
    console.log(`Saved account to output: ${email}`);
  } catch (err) {
    console.warn(`Warning: unable to write to ${OUTPUT_FILE}: ${err.message}`);
  }
}

function pickRandomProxy(proxies) {
  if (!proxies || proxies.length === 0) {
    return null;
  }
  const index = Math.floor(Math.random() * proxies.length);
  return proxies[index];
}

async function waitForDownloadSuccess(driver, timeoutMs = 40000, pollMs = 5000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const currentUrl = await driver.getCurrentUrl();
      if (currentUrl && currentUrl.startsWith(DOWNLOAD_SUCCESS_URL)) {
        return true;
      }
    } catch (err) {
      console.warn(`Warning: unable to read current URL while polling for success: ${err.message}`);
      break;
    }
    await driver.sleep(pollMs);
  }
  return false;
}

async function buildDriver(proxySettings) {
  const options = new chrome.Options();
  options.setChromeBinaryPath(CHROME_BINARY_PATH);
  if (proxySettings?.host && proxySettings?.port) {
    options.addArguments(`--proxy-server=http://${proxySettings.host}:${proxySettings.port}`);
  }
  options.addArguments('--disable-setuid-sandbox');
  options.addArguments('--no-sandbox');
  options.addArguments('--disable-dev-shm-usage');
  options.addArguments('--disable-gpu');
  options.addArguments('--remote-debugging-port=0');
  if (CHROME_LANGUAGE) {
    options.addArguments(`--lang=${CHROME_LANGUAGE}`);
  }
  if (USE_CAPSOLVER) {
    options.addArguments(`--load-extension=${CAPSOLVER_EXTENSION_PATH_SANITIZED}`);
  }
  options.excludeSwitches(['enable-logging']);

  const builder = new selenium.Builder().forBrowser('chrome');
  builder.setChromeOptions(options);
  builder.setChromeService(new chrome.ServiceBuilder(CHROMEDRIVER_PATH));
  const driver = await builder.build();

  if (proxySettings?.username && proxySettings?.password) {
    const encoded = Buffer.from(`${proxySettings.username}:${proxySettings.password}`).toString('base64');
    const sendDevTools = driver.sendDevToolsCommand
      ? driver.sendDevToolsCommand.bind(driver)
      : driver.executeCdpCommand
      ? driver.executeCdpCommand.bind(driver)
      : null;
    if (sendDevTools) {
      try {
        await sendDevTools('Network.enable', {});
        await sendDevTools('Network.setExtraHTTPHeaders', {
          headers: {
            'Proxy-Authorization': `Basic ${encoded}`,
          },
        });
      } catch (err) {
        console.warn('Warning: unable to preload proxy credentials via DevTools.', err.message);
      }
    } else {
      console.warn('Warning: this Selenium build cannot inject proxy credentials automatically; the browser may prompt you.');
    }
  }

  return driver;
}

async function jsClick(driver, element) {
  await driver.executeScript('arguments[0].click()', element);
}

async function waitForRecaptchaSolution(driver, timeout = 15000) {
  if (!USE_CAPSOLVER) {
    return;
  }
  await driver.wait(async () => {
    const solved = await driver.executeScript(
      "const el = document.getElementsByName('g-recaptcha-response')[0];" +
        "return el && el.value.trim().length > 0;",
    );
    return Boolean(solved);
  }, timeout);
}

async function hasPassword(driver) {
  try {
    await driver.wait(until.elementLocated(SELECTORS.passwordInput), 2000);
    return true;
  } catch (err) {
    return false;
  }
}

async function hasProfile(driver) {
  try {
    await driver.wait(until.elementLocated(By.id('month')), 2000);
    return true;
  } catch (err) {
    return false;
  }
}

async function toPassword(driver, email) {
  const wait = driver.wait(until.elementLocated(SELECTORS.emailInput), 4000);
  const emailBox = await wait;
  await emailBox.clear();
  await emailBox.sendKeys(email);
  await emailBox.sendKeys(Key.TAB);
  const body = await driver.findElement(By.tagName('body'));
  await body.sendKeys(Key.ENTER);
  await driver.sleep(1500);

  if (await hasPassword(driver)) {
    return;
  }

  const next = await driver.findElement(SELECTORS.nextButton);
  await next.click();
  await driver.wait(until.elementLocated(SELECTORS.passwordInput), 2500);
}

async function toProfile(driver, password) {
  const passEl = await driver.wait(
    until.elementLocated(SELECTORS.passwordInput),
    4000,
  );
  await passEl.sendKeys(password, Key.ENTER);

  if (await hasProfile(driver)) {
    return;
  }

  const nextBtn = await driver.findElement(
    By.xpath("//span[normalize-space()='Next']/ancestor::button"),
  );
  await nextBtn.click();
  await driver.wait(() => hasProfile(driver), 2500);
}

async function fillProfile(driver) {
  const wait = driver.wait(until.elementLocated(By.id('displayName')), 4000);
  const displayName = await wait;
  const makeUsername =
    typeof faker.internet.username === 'function'
      ? faker.internet.username.bind(faker.internet)
      : faker.internet.userName.bind(faker.internet);
  await displayName.sendKeys(makeUsername().slice(0, 30));

  const monthEl = await driver.findElement(By.id('month'));
  const monthSelect = new Select(monthEl);
  await monthSelect.selectByValue(String(faker.number.int({ min: 1, max: 12 })));

  await driver.findElement(By.name('day')).sendKeys(
    String(faker.number.int({ min: 1, max: 28 })),
  );
  await driver.findElement(By.name('year')).sendKeys(
    String(faker.number.int({ min: 1990, max: 2004 })),
  );

  const gender = faker.helpers.arrayElement(['Man', 'Woman']);
  const genderLabel = await driver.findElement(
    By.xpath(`//label[normalize-space()='${gender}']`),
  );
  await genderLabel.click();

  const nextBtn = await driver.wait(
    until.elementIsEnabled(
      await driver.findElement(
        By.xpath("//span[normalize-space()='Next']/ancestor::button"),
      ),
    ),
    8000,
  );

  try {
    await nextBtn.click();
  } catch (err) {
    await jsClick(driver, nextBtn);
  }

  console.log(`Profile completed. Selected gender: ${gender}`);
}

async function skipAdsAndSolveCaptcha(driver) {
  const wait = driver.wait(
    until.elementLocated(
      By.xpath("//span[normalize-space()='Sign up']/ancestor::button"),
    ),
    7500,
  );
  const signUpBtn = await wait;
  await driver.sleep(30000);
  await signUpBtn.click();
  console.log('Sign up button clicked.');

  if (!USE_CAPSOLVER) {
    await driver.sleep(2000);
    return;
  }

  try {
    await driver.wait(
      until.elementLocated(By.xpath("//iframe[contains(@src,'api2/anchor')]")),
      7500,
    );
    console.log('CAPTCHA iframe detected.');
  } catch (err) {
    console.warn('Warning: CAPTCHA iframe did not appear within 15 seconds.');
  }

  await driver.sleep(6000);
}

async function pressContinue(driver) {
  const wait = driver.wait(
    until.elementLocated(
      By.xpath("//span[normalize-space()='Continue']/ancestor::button[not(@disabled)]"),
    ),
    30000,
  );
  const continueBtn = await wait;
  const startUrl = await driver.getCurrentUrl();

  await continueBtn.click();
  console.log("Clicked 'Continue'. Waiting for navigation…");

  try {
    await driver.wait(async () => {
      const current = await driver.getCurrentUrl();
      return current !== startUrl;
    }, 15000);
    console.log('Navigation detected.');
  } catch (err) {
    console.warn('Warning: page did not navigate within 30 seconds after Continue.');
  }

  console.log('Waiting an additional 15 seconds for account provisioning…');
  await driver.sleep(15000);
}

async function fillEmailStep(driver, email) {
  await driver.get(SIGNUP_URL);
  const emailInput = await driver.wait(until.elementLocated(By.id('email')), 5000);
  await emailInput.sendKeys(email);
  const confirmInput = await driver.findElement(By.id('confirm'));
  await confirmInput.sendKeys(email);

  const nextBtn = await driver.wait(
    until.elementLocated(
      By.xpath("//button[contains(@data-testid,'next-button')]"),
    ),
    5000,
  );
  await nextBtn.click();
  console.log(`[${email}] Email step done.`);
}

async function fillPasswordStep(driver, password) {
  const passwordInput = await driver.wait(
    until.elementLocated(By.id('password')),
    5000,
  );
  await passwordInput.sendKeys(password);

  const nextBtn = await driver.wait(
    until.elementLocated(
      By.xpath("//button[contains(@data-testid,'next-button')]"),
    ),
    5000,
  );
  await nextBtn.click();
  console.log('Password step done.');
}

async function fillProfileStep(driver) {
  const monthEl = await driver.wait(until.elementLocated(By.id('month')), 5000);
  const monthSelect = new Select(monthEl);
  await monthSelect.selectByValue(String(faker.number.int({ min: 1, max: 12 })));

  await driver.findElement(By.name('day')).sendKeys(
    String(faker.number.int({ min: 1, max: 28 })),
  );
  await driver.findElement(By.name('year')).sendKeys(
    String(faker.number.int({ min: 1990, max: 2004 })),
  );

  const gender = faker.helpers.arrayElement(['male', 'female']);
  const genderRadio = await driver.findElement(
    By.xpath(`//input[@value='${gender}']/..`),
  );
  await genderRadio.click();

  const nextBtn = await driver.wait(
    until.elementLocated(
      By.xpath("//button[contains(@data-testid,'next-button')]"),
    ),
    5000,
  );
  await nextBtn.click();
  console.log('Profile step done.');
}

async function signupOne(driver, email, password) {
  await fillEmailStep(driver, email);
  await fillPasswordStep(driver, password);
  await fillProfileStep(driver);
  await skipAdsAndSolveCaptcha(driver);
  await pressContinue(driver);
  console.log(`[${email}] Signup flow completed.\n`);
}

async function runSignupForAccount(email, password, proxies) {
  const proxyLine = pickRandomProxy(proxies);
  const proxySettings = proxyLine ? parseProxy(proxyLine) : null;
  if (proxySettings) {
    console.log(`[${email}] Using proxy ${proxySettings.host}:${proxySettings.port}`);
  } else {
    console.log(`[${email}] No proxy selected.`);
  }

  const driver = await buildDriver(proxySettings);

  if (!USE_CAPSOLVER) {
    console.log(`[${email}] Capsolver disabled; continuing without automated CAPTCHA solving.`);
  }
  await driver.get(SIGNUP_URL);

  let signupCompleted = false;
  const ensureRecorded = async () => {
    if (!signupCompleted) {
      await recordSuccessfulAccount(email, password);
      signupCompleted = true;
    }
  };

  try {
    await toPassword(driver, email);
    await toProfile(driver, password);
    await fillProfile(driver);
    await skipAdsAndSolveCaptcha(driver);
    if (await waitForDownloadSuccess(driver, 30000, 5000)) {
      await ensureRecorded();
    }
    if (!signupCompleted) {
      await waitForRecaptchaSolution(driver, 30000);
      if (await waitForDownloadSuccess(driver, 40000, 5000)) {
        await ensureRecorded();
      }
    }
    if (!signupCompleted) {
      await pressContinue(driver);
      if (await waitForDownloadSuccess(driver, 30000, 5000)) {
        await ensureRecorded();
      } else {
        const finalUrl = await driver.getCurrentUrl();
        console.warn(`[${email}] Signup did not land on expected page. Current URL: ${finalUrl}`);
      }
    }
  } catch (err) {
    console.error(`[${email}] Error:`, err.message);
  } finally {
    await driver.quit();
  }

  console.log(`[${email}] Process completed. Success recorded: ${signupCompleted}`);
  return signupCompleted;
}

async function main() {
  const accounts = await readLines(ACCOUNTS_FILE);
  if (!accounts.length) {
    throw new Error('No accounts found in input_accounts.txt');
  }

  const proxies = await readLines(PROXIES_FILE);
  console.log(`Loaded ${accounts.length} accounts and ${proxies.length} proxies.`);

  const successes = [];
  const failures = [];

  for (let i = 0; i < accounts.length; i += MAX_PARALLEL_DRIVERS) {
    const batch = accounts.slice(i, i + MAX_PARALLEL_DRIVERS);
    const batchLabel = `${i + 1}-${i + batch.length}`;
    console.log(`Starting batch ${batchLabel}: ${batch.join(', ')}`);

    const tasks = batch.map((email) =>
      runSignupForAccount(email, email, proxies)
        .then((success) => ({ email, success }))
        .catch((err) => {
          console.error(`[${email}] Unexpected failure:`, err);
          return { email, success: false };
        }),
    );

    const results = await Promise.all(tasks);
    results.forEach(({ email, success }) => {
      if (success) {
        successes.push(email);
      } else {
        failures.push(email);
      }
    });
  }

  console.log(`All accounts processed. Success: ${successes.length}, Failed: ${failures.length}.`);
  if (failures.length) {
    console.log('Failed accounts:', failures.join(', '));
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
