/* Optional real-browser QA. npm test remains fast and browser-independent. */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const {chromium} = require("playwright-core");

const output = path.resolve(process.env.SHOWCASE_OUTPUT || path.join(__dirname, "../../reports/showcase"));
const captures = path.resolve(output, "../browser");
const prefix = "/Dataset-Train-Test-Overlap-Detector/";
const types = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json", ".yaml": "text/plain"};

test("public showcase works in a real browser under the GitHub Pages project path", async (t) => {
  fs.mkdirSync(captures, {recursive: true});
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, "http://localhost");
    if (!url.pathname.startsWith(prefix)) { res.writeHead(404).end(); return; }
    const relative = decodeURIComponent(url.pathname.slice(prefix.length)) || "index.html";
    const file = path.resolve(output, relative);
    if (!file.startsWith(output + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404).end(); return;
    }
    res.setHeader("Content-Type", types[path.extname(file)] || "application/octet-stream");
    fs.createReadStream(file).pipe(res);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise((resolve) => { server.closeAllConnections(); server.close(resolve); }));
  const browser = await chromium.launch(process.env.SHOWCASE_BROWSER
    ? {executablePath: process.env.SHOWCASE_BROWSER, headless: true}
    : {channel: "chrome", headless: true});
  t.after(() => browser.close());
  const page = await browser.newPage({reducedMotion: "reduce"});
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  await page.goto(`http://127.0.0.1:${server.address().port}${prefix}`);
  await page.locator("#case-left-image").waitFor();
  await page.addScriptTag({path: require.resolve("axe-core/axe.min.js")});

  async function audit(label) {
    const result = await page.evaluate(() => axe.run(document, {runOnly: {type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"]}}));
    fs.writeFileSync(path.join(captures, `${label}-accessibility.json`), JSON.stringify(result, null, 2));
    assert.deepEqual(result.violations.map((v) => ({id: v.id, nodes: v.nodes.map((n) => n.target)})), [], label);
  }
  async function loadVisibleImages() {
    await page.evaluate(async () => {
      await Promise.all([...document.images].filter((image) => image.getAttribute("src") && image.getBoundingClientRect().width > 0).map(async (image) => {
        image.loading = "eager";
        await image.decode();
      }));
    });
  }

  for (const width of [1440, 1024, 768, 390, 320]) {
    await t.test(`layout and accessibility at ${width}px`, async () => {
      await page.setViewportSize({width, height: 1000});
      await loadVisibleImages();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await audit(`width-${width}`);
      await page.screenshot({path: path.join(captures, `width-${width}.png`), fullPage: true});
    });
  }
  await t.test("four visual cases, real images, disclosure and keyboard selection", async () => {
    for (const name of ["renamed", "compression", "lighting", "separate"]) {
      await page.locator(`#case-${name}`).click();
      await loadVisibleImages();
      await page.locator(".case-technical > summary").click();
      await audit(`case-${name}`);
      await page.locator("#comparison-panel").screenshot({path: path.join(captures, `case-${name}.png`)});
    }
    await page.locator("#case-separate").focus();
    await page.keyboard.press("Home");
    assert.equal(await page.locator("#case-renamed").getAttribute("aria-selected"), "true");
    await page.locator("#case-right-zoom").click();
    assert.equal(await page.locator("#image-modal").isVisible(), true);
    await page.keyboard.press("Escape");
  });
  await t.test("tabs, search, dialog keyboard behavior, and experiment links", async () => {
    await page.locator("#full-evidence > summary").click();
    await page.locator("#tab-coco128").focus();
    await page.keyboard.press("ArrowRight");
    assert.equal(await page.locator("#tab-coco8").evaluate((node) => node === document.activeElement), true);
    assert.equal(await page.locator("#baseline-panel").isVisible(), true);
    await loadVisibleImages();
    await audit("coco8-mobile");
    await page.screenshot({path: path.join(captures, "coco8-mobile.png"), fullPage: true});
    await page.locator('.experiment-entry[data-select-dataset="coco128"]').click();
    await page.locator("#image-search").fill("000000000030");
    await page.locator(".image-option").click();
    assert.equal(await page.locator("#selected-filename").textContent(), "000000000030.jpg");
    await page.locator('[data-open-image="shared"]').click();
    assert.equal(await page.locator("#image-modal").isVisible(), true);
    await audit("image-dialog");
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#image-modal").isVisible(), false);
    assert.equal(await page.locator('[data-open-image="shared"]').evaluate((node) => node === document.activeElement), true);
    await page.locator('[data-select-similarity="leuven"]').click();
    assert.equal(await page.locator("#similarity-score").textContent(), "72.01%");
    await loadVisibleImages();
    await audit("leuven-mobile");
    await page.locator("#similarity-check").screenshot({path: path.join(captures, "leuven-mobile.png")});
    await page.locator('[href="#filename-check"]').click();
    assert.equal(await page.locator("#filename-check").evaluate((node) => node.open), true);
    await page.locator('[data-os="linux"]').click();
    assert.match(await page.locator("#audit-command").textContent(), /--near-duplicates/);
  });
  await t.test("local links, source images, configurations and reports return HTTP 200", async () => {
    const urls = await page.evaluate(() => [...new Set([...document.querySelectorAll("a[href],img[src],script[src],link[href]")].map((node) => node.href || node.src).filter((url) => url.startsWith(location.origin) && !url.includes("#")))]);
    for (const url of urls) assert.equal((await page.request.get(url)).status(), 200, url);
    assert.deepEqual(errors, []);
  });
});
