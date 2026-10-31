const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {JSDOM} = require("jsdom");
const {createHash} = require("node:crypto");

const root = path.resolve(__dirname, "../..");
const output = process.env.SHOWCASE_OUTPUT || path.join(root, "reports/showcase");

function open() {
  const dom = new JSDOM(fs.readFileSync(path.join(output, "index.html"), "utf8"), {
    url: "http://127.0.0.1:8765/Dataset-Train-Test-Overlap-Detector/", runScripts: "outside-only", pretendToBeVisual: true,
  });
  const window = dom.window;
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement.prototype.close = function () { this.open = false; };
  window.eval(fs.readFileSync(path.join(output, "evidence.js"), "utf8"));
  window.eval(fs.readFileSync(path.join(output, "app.js"), "utf8"));
  return dom;
}

test("real similarity scores retain original benchmark bytes, filenames and reviewed-candidate status", () => {
  const dom = open();
  const {document, SHOWCASE_EVIDENCE: data} = dom.window;
  assert.equal(data.similarity_examples.length, 4);
  for (const example of data.similarity_examples) {
    assert.equal(example.status, "NOT VERIFIED");
    assert.equal(example.similarity.method, "ssim_grayscale_128_uniform7");
    assert.notEqual(example.members[0].hash, example.members[1].hash);
    for (const member of example.members) {
      assert.match(member.path, /^(ubc|leuven)\/img\d\.png$/);
      assert.match(member.source_url, /^https:\/\/raw\.githubusercontent\.com\/opencv\/opencv_extra\/[a-f0-9]{40}\//);
      const content = fs.readFileSync(path.join(output, member.image));
      assert.equal(createHash("sha256").update(content).digest("hex"), member.hash);
    }
    assert.ok(fs.existsSync(path.join(output, example.report)));
    const report = JSON.parse(fs.readFileSync(path.join(output, example.json), "utf8"));
    assert.equal(report.summary.confirmed_exact_groups, 0);
    assert.equal(report.checks.source_video, "NOT VERIFIED");
    assert.ok(report.findings.some((finding) => finding.similarity.ssim === example.similarity.ssim));
  }
  assert.equal(document.getElementById("similarity-score").textContent, "92.61%");
  assert.match(document.getElementById("similarity-check").textContent, /not official benchmark splits/i);
  assert.match(document.getElementById("similarity-check").textContent, /Not a leakage percentage/);
  dom.window.close();
});

test("similarity controls update both originals, numeric evidence, source links and reports", () => {
  const dom = open();
  const {document} = dom.window;
  const buttons = document.querySelectorAll("[data-similarity-example]");
  assert.equal(buttons.length, 4);
  buttons[3].click();
  assert.equal(document.getElementById("similarity-score").textContent, "72.01%");
  assert.equal(document.getElementById("similarity-hash-score").textContent, "100.00%");
  assert.equal(document.getElementById("similarity-right-path").textContent, "leuven/img2.png");
  assert.match(document.getElementById("similarity-full-report").href, /similarity-leuven.html$/);
  assert.match(document.getElementById("similarity-right-source").href, /leuven\/img2.png$/);
  assert.equal(document.querySelectorAll('[data-similarity-example][aria-pressed="true"]').length, 1);
  document.getElementById("similarity-right-zoom").click();
  assert.match(document.getElementById("modal-title").textContent, /COMPARISON.*img2.png/);
  assert.equal(document.getElementById("image-modal").open, true);
  dom.window.close();
});

test("evidence is produced from 128 authentic original COCO128 paths", () => {
  const dom = open();
  const {datasets} = dom.window.SHOWCASE_EVIDENCE;
  assert.equal(datasets.coco128.items.length, 128);
  assert.equal(datasets.coco128.summary.confirmed_exact_groups, 128);
  assert.equal(datasets.coco128.status, "FAIL");
  for (const item of datasets.coco128.items) {
    assert.match(item.filename, /^\d{12}\.jpg$/);
    assert.equal(item.path, `images/train2017/${item.filename}`);
    assert.match(item.hash, /^[a-f0-9]{64}$/);
    assert.equal(item.image, `assets/coco128/${item.filename}`);
    assert.ok(fs.existsSync(path.join(output, item.image)));
    assert.deepEqual(Array.from(item.splits), ["train", "val"]);
  }
  const document = dom.window.document;
  assert.equal(document.querySelectorAll(".image-option").length, 128);
  assert.equal(document.querySelectorAll(".finding-evidence img").length, 1);
  assert.deepEqual(Array.from(document.querySelectorAll("#selected-memberships span"), (node) => node.textContent), ["TRAIN", "VALIDATION"]);
  assert.match(document.querySelector(".finding-action").textContent, /reuse is expected/);
  assert.equal(document.getElementById("selected-filename").textContent, "000000000025.jpg");
  assert.equal(document.getElementById("detail-credit-link").href, "https://cocodataset.org/#explore?id=25");
  assert.match(document.body.textContent, /intentional/i);
  dom.window.close();
});

test("four experiment entries select the matching evidence and show measured findings", () => {
  const dom = open();
  const {document} = dom.window;
  assert.equal(document.querySelectorAll(".experiment-entry").length, 4);
  assert.equal(document.getElementById("index-coco128").textContent, "128");
  assert.equal(document.getElementById("index-coco8").textContent, "0");
  assert.equal(document.getElementById("index-ubc").textContent, "92.61%");
  assert.equal(document.getElementById("index-leuven").textContent, "72.01%");
  document.querySelector('[data-select-similarity="leuven"]').click();
  assert.equal(document.getElementById("similarity-right-path").textContent, "leuven/img2.png");
  document.querySelector('[data-select-similarity="ubc"]').click();
  assert.equal(document.getElementById("similarity-right-path").textContent, "ubc/img5.png");
  dom.window.close();
});

test("portable experiment records preserve inputs, configurations and measured audit results", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(output, "experiments.json"), "utf8"));
  assert.equal(manifest.experiments.length, 4);
  assert.match(manifest.build.engine_sha256, /^[a-f0-9]{64}$/);
  assert.equal(manifest.publication.rights_verified, false);
  for (const experiment of manifest.experiments) {
    assert.ok(fs.existsSync(path.join(output, experiment.configuration)));
    const report = JSON.parse(fs.readFileSync(path.join(output, experiment.report), "utf8"));
    if (experiment.summary) assert.deepEqual(experiment.summary, report.summary);
    else {
      assert.equal(experiment.settings.dhash_max_distance, report.optional_checks.near_duplicates.threshold);
      for (const comparison of experiment.comparisons) {
        assert.ok(report.findings.some((finding) => finding.similarity.ssim === comparison.measurement.ssim));
      }
    }
  }
  assert.ok(fs.statSync(path.join(output, "evidence.js")).size < 100000);
  for (const name of fs.readdirSync(path.join(output, "reports"))) {
    const content = fs.readFileSync(path.join(output, "reports", name), "utf8");
    assert.doesNotMatch(content, /file:\/\/|[a-z]:[\/\\]|dataset-showcase-/i);
  }
});

test("search and selection update the image, split memberships, original path and hash", () => {
  const dom = open();
  const {document, Event} = dom.window;
  const search = document.getElementById("image-search");
  search.value = "000000000030";
  search.dispatchEvent(new Event("input", {bubbles: true}));
  assert.equal(document.querySelectorAll(".image-option").length, 1);
  document.querySelector(".image-option").click();
  assert.equal(document.getElementById("selected-filename").textContent, "000000000030.jpg");
  assert.equal(document.getElementById("detail-path").textContent, "images/train2017/000000000030.jpg");
  const references = [...document.querySelectorAll("#selected-memberships code")];
  assert.equal(references.length, 2);
  assert.ok(references.every((node) => node.textContent === "images/train2017/000000000030.jpg"));
  assert.equal(document.getElementById("shared-split-summary").hidden, false);
  const record = dom.window.SHOWCASE_EVIDENCE.datasets.coco128.items.find((item) => item.filename === "000000000030.jpg");
  assert.equal(document.getElementById("selected-hash").textContent, record.hash);
  search.value = "does-not-exist";
  search.dispatchEvent(new Event("input", {bubbles: true}));
  assert.match(document.querySelector(".no-results").textContent, /No image matches/);
  search.value = "";
  search.dispatchEvent(new Event("input", {bubbles: true}));
  assert.equal(document.querySelectorAll(".image-option").length, 128);
  dom.window.close();
});

test("COCO8 tab shows 4/4 real images, NOT VERIFIED context and correct report links", () => {
  const dom = open();
  const {document} = dom.window;
  document.getElementById("tab-coco8").click();
  assert.equal(document.getElementById("tab-coco8").getAttribute("aria-selected"), "true");
  assert.equal(document.getElementById("overlap-inspector").hidden, true);
  assert.equal(document.getElementById("baseline-panel").hidden, false);
  assert.equal(document.getElementById("shared-split-summary").hidden, true);
  assert.match(document.getElementById("explorer-title").textContent, /Eight images/);
  assert.equal(document.querySelectorAll("#baseline-train .baseline-card").length, 4);
  assert.equal(document.querySelectorAll("#baseline-val .baseline-card").length, 4);
  assert.match(document.getElementById("baseline-panel").textContent, /Overall: Not verified/);
  assert.equal(document.getElementById("full-report").getAttribute("href"), "reports/coco8.html");
  assert.match(document.getElementById("evidence-count").textContent, /^0 exact groups/);
  const data = dom.window.SHOWCASE_EVIDENCE.datasets.coco8;
  assert.equal(data.status, "NOT VERIFIED");
  assert.equal(data.checks.source_video, "NOT VERIFIED");
  assert.equal(new Set(data.items.map((item) => item.hash)).size, 8);
  dom.window.close();
});

test("dataset tabs work with arrow keys and validation links select the right dataset", () => {
  const dom = open();
  const {document, KeyboardEvent} = dom.window;
  document.getElementById("tab-coco128").dispatchEvent(new KeyboardEvent("keydown", {key: "ArrowRight", bubbles: true}));
  assert.equal(document.activeElement.id, "tab-coco8");
  assert.equal(document.getElementById("tab-coco8").tabIndex, 0);
  document.querySelector('[data-select-dataset="coco128"]').click();
  assert.equal(document.getElementById("overlap-inspector").hidden, false);
  assert.equal(document.getElementById("full-report").getAttribute("href"), "reports/coco128.html");
  dom.window.close();
});

test("image dialog shows selected image and original reference and closes", () => {
  const dom = open();
  const {document} = dom.window;
  document.querySelector('[data-open-image="shared"]').click();
  const dialog = document.getElementById("image-modal");
  assert.equal(dialog.open, true);
  assert.match(document.getElementById("modal-title").textContent, /^SHARED IMAGE/);
  assert.equal(document.getElementById("modal-reference").textContent, "images/train2017/000000000025.jpg");
  assert.equal(document.getElementById("modal-image").src, document.getElementById("detail-image").src);
  document.querySelector(".modal-close").click();
  assert.equal(dialog.open, false);
  dom.window.close();
});

test("platform commands and clipboard fallback are usable without extra permissions", async () => {
  const dom = open();
  const {document} = dom.window;
  document.querySelector('[data-os="linux"]').click();
  assert.match(document.getElementById("install-command").textContent, /python3 -m venv/);
  assert.match(document.getElementById("audit-command").textContent, /\.venv\/bin\/videosplitguard/);
  document.querySelector('[data-copy="audit-command"]').click();
  await Promise.resolve();
  assert.match(document.getElementById("copy-status").textContent, /Command selected/);
  assert.equal(dom.window.getSelection().toString(), document.getElementById("audit-command").textContent);
  document.querySelector('[data-os="windows"]').click();
  assert.match(document.getElementById("install-command").textContent, /Scripts\\python.exe/);
  dom.window.close();
});

test("navigation and local downloads resolve and public outputs contain no machine paths", () => {
  const dom = open();
  const {document} = dom.window;
  for (const anchor of document.querySelectorAll("a[href]")) {
    const href = anchor.getAttribute("href");
    if (href.startsWith("#")) assert.ok(document.getElementById(href.slice(1)), href);
    else if (!href.startsWith("https://")) assert.ok(fs.existsSync(path.join(output, href)), href);
  }
  assert.equal(document.getElementById("github-link").hidden, !dom.window.SHOWCASE_EVIDENCE.github_url);
  const credits = fs.readFileSync(path.join(output, "credits.html"), "utf8");
  assert.match(credits, /COCO source record/);
  assert.match(credits, /Original filenames and PNG bytes are retained/);
  for (const name of ["coco128", "coco8"]) {
    for (const extension of ["html", "json"]) {
      const content = fs.readFileSync(path.join(output, "reports", `${name}.${extension}`), "utf8");
      assert.doesNotMatch(content, /(?:file):\/\/|[a-z]:[\/\\]|copied-from-train|SYNTHETIC-video/i);
    }
    const report = JSON.parse(fs.readFileSync(path.join(output, "reports", `${name}.json`), "utf8"));
    assert.equal(report.dataset.yaml, `${name}.yaml`);
    assert.equal(report.dataset.root, name);
    assert.equal(report.checks.source_video, "NOT VERIFIED");
  }
  dom.window.close();
});

test("different-filename section displays real audited byte overlap and discloses its setup", () => {
  const dom = open();
  const {document} = dom.window;
  const check = dom.window.SHOWCASE_EVIDENCE.filename_check;
  const source = dom.window.SHOWCASE_EVIDENCE.datasets.coco128.items.find((item) => item.filename === check.source_filename);
  assert.equal(check.groups, 1);
  assert.equal(check.evidence, "confirmed_bytes");
  assert.equal(check.status, "FAIL");
  assert.equal(check.hash, source.hash);
  assert.equal(check.image, source.image);
  assert.notEqual(check.members[0].path, check.members[1].path);
  assert.equal(document.getElementById("filename-train-path").textContent, "images/train/scene_014.jpg");
  assert.equal(document.getElementById("filename-val-path").textContent, "images/val/capture_928.jpg");
  assert.equal(document.getElementById("filename-train-hash").textContent, document.getElementById("filename-val-hash").textContent);
  assert.equal(document.getElementById("filename-train-image").src, document.getElementById("filename-val-image").src);
  assert.match(document.getElementById("filename-check").textContent, /controlled capability check/);
  document.querySelector('[data-filename-image="val"]').click();
  assert.equal(document.getElementById("image-modal").open, true);
  assert.match(document.getElementById("modal-title").textContent, /capture_928.jpg/);
  const report = JSON.parse(fs.readFileSync(path.join(output, "reports/filename-check.json"), "utf8"));
  assert.equal(report.summary.confirmed_exact_groups, 1);
  assert.equal(report.summary.shared_path_groups, 0);
  assert.match(report.warnings[0], /Controlled filename-independence check/);
  assert.equal(report.findings[0].group_id, source.hash);
  dom.window.close();
});


test("visual comparison explorer preserves real evidence and explains all four outcomes", () => {
  const dom = open();
  const {document, SHOWCASE_EVIDENCE: data, KeyboardEvent} = dom.window;
  assert.match(document.getElementById("case-result").textContent, /Exact overlap detected/);
  assert.equal(document.getElementById("case-left-image").getAttribute("src"), data.filename_check.image);
  assert.equal(document.getElementById("case-left-hash").textContent, document.getElementById("case-right-hash").textContent);
  assert.notEqual(document.getElementById("case-left-path").textContent, document.getElementById("case-right-path").textContent);
  assert.match(document.getElementById("case-boundary").textContent, /Controlled demonstration/);
  for (const [name, sequence] of [["compression", "ubc"], ["lighting", "leuven"]]) {
    document.getElementById(`case-${name}`).click();
    assert.match(document.getElementById("case-result").textContent, /candidate/);
    const example = data.similarity_examples.find((e) => e.sequence === sequence && (sequence === "leuven" || e.members[1].filename === "img5.png"));
    assert.equal(document.getElementById("case-left-image").getAttribute("src"), example.members[0].image);
    assert.equal(document.getElementById("case-right-image").getAttribute("src"), example.members[1].image);
    assert.match(document.getElementById("case-measurements").textContent, new RegExp(example.similarity.structural_similarity_percent.toFixed(2)));
    assert.match(document.getElementById("case-boundary").textContent, /Illustrative split assignments/);
    assert.notEqual(document.getElementById("case-left-hash").textContent, document.getElementById("case-right-hash").textContent);
  }
  document.getElementById("case-separate").click();
  assert.match(document.getElementById("case-result").textContent, /No exact overlap/);
  assert.equal(document.getElementById("case-report").getAttribute("href"), "reports/coco8.html");
  assert.match(document.getElementById("case-meaning").textContent, /all 4 Train and 4 Validation/);
  document.getElementById("case-separate").dispatchEvent(new KeyboardEvent("keydown", {key:"Home", bubbles:true}));
  assert.equal(document.activeElement.id, "case-renamed");
  assert.equal(document.querySelectorAll('[data-case][aria-selected="true"]').length, 1);
  document.getElementById("case-right-zoom").click();
  assert.equal(document.getElementById("image-modal").open, true);
  dom.window.close();
});
