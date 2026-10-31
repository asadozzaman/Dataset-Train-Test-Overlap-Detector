const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {JSDOM} = require("jsdom");
const output = path.resolve(process.env.SHOWCASE_PUBLIC_OUTPUT || "../reports/showcase-public");

test("publication contains no dataset images, archives or embedded previews", () => {
  for (const entry of fs.readdirSync(output, {recursive:true, withFileTypes:true})) {
    if (!entry.isFile()) continue;
    assert.doesNotMatch(entry.name, /\.(png|jpe?g|webp|gif|ppm|zip)$/i);
    assert.doesNotMatch(fs.readFileSync(path.join(entry.parentPath, entry.name), "utf8"), /data:image\//);
  }
  const record = JSON.parse(fs.readFileSync(path.join(output, "experiments.json"), "utf8"));
  assert.equal(record.publication.mode, "source_links_only");
  assert.equal(record.publication.redistributes_dataset_images, false);
  assert.equal(record.publication.rights_verified, false);
  assert.equal(record.experiments.length, 4);
});

test("public comparison actions open original sources and retain verified outcomes", () => {
  const dom = new JSDOM(fs.readFileSync(path.join(output, "index.html"), "utf8"), {
    url:"https://asadozzaman.github.io/Dataset-Train-Test-Overlap-Detector/", runScripts:"outside-only"
  });
  const opened = [];
  dom.window.open = (url) => opened.push(url);
  dom.window.eval(fs.readFileSync(path.join(output, "evidence.js"), "utf8"));
  dom.window.eval(fs.readFileSync(path.join(output, "app.js"), "utf8"));
  const d = dom.window.document;
  assert.ok(d.querySelector(".source-publication-note"));
  for (const name of ["renamed", "compression", "lighting", "separate"]) {
    d.getElementById(`case-${name}`).click();
    assert.equal(d.getElementById("case-left-image").getAttribute("src"), "source-preview.svg");
    d.getElementById("case-left-zoom").click();
    assert.match(opened.at(-1), /^https:\/\/(cocodataset\.org\/|raw\.githubusercontent\.com\/opencv\/)/);
  }
  dom.window.close();
});
