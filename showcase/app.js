/* Authentic dataset evidence is produced by scripts/build_showcase.py. */
(() => {
  "use strict";
  const data = window.SHOWCASE_EVIDENCE;
  if (!data) return;
  const $ = (id) => document.getElementById(id);
  const coco128 = data.datasets.coco128;
  const coco8 = data.datasets.coco8;
  let currentDataset = "coco128";
  let selected = coco128.items.find((item) => item.filename === "000000000025.jpg") || coco128.items[0];
  const modal = $("image-modal");

  document.querySelectorAll("[data-version]").forEach((node) => { node.textContent = data.version; });
  if (data.github_url) {
    $("github-link").href = data.github_url;
    $("github-link").hidden = false;
    $("repository-note").textContent = "Install from source; no PyPI release. The repository quickstart documents input formats and CLI options.";
  }
  $("index-coco128").textContent = coco128.summary.confirmed_exact_groups;
  $("index-coco8").textContent = coco8.summary.confirmed_exact_groups;
  for (const sequence of ["ubc", "leuven"]) {
    const example = data.similarity_examples.find((item) => item.sequence === sequence &&
      (sequence !== "ubc" || item.members[1].filename === "img5.png"));
    $(`index-${sequence}`).textContent = `${example.similarity.structural_similarity_percent.toFixed(2)}%`;
  }
  $("hero-image").src = selected.image;
  $("hero-filename").textContent = selected.filename;
  $("hero-position").textContent = `${String(coco128.items.indexOf(selected) + 1).padStart(2, "0")} / ${coco128.items.length}`;

  function showImage(item, label) {
    if (data.source_links_only) {
      const controlled = data.filename_check.members.some((member) => member.path === item.path);
      const source = item.source_url || (controlled
        ? `https://cocodataset.org/#explore?id=${parseInt(data.filename_check.source_filename, 10)}`
        : /^\d{12}\.jpg$/.test(item.filename) ? `https://cocodataset.org/#explore?id=${parseInt(item.filename, 10)}` : "credits.html");
      window.open(source, "_blank", "noopener,noreferrer");
      return;
    }

    $("modal-title").textContent = `${label} · ${item.filename}`;
    $("modal-image").src = item.image;
    $("modal-image").alt = `${label}: ${item.filename}, original dataset image`;
    $("modal-reference").textContent = item.path;
    $("modal-image-note").textContent = item.path.endsWith(".png")
      ? "Original benchmark PNG bytes. Illustrative split assignments; source history remains unverified."
      : "Resized display preview. Original filename preserved; source-record image terms apply.";
    $("modal-credit-link").href = item.source_url || (/^\d{12}\.jpg$/.test(item.filename)
      ? `https://cocodataset.org/#explore?id=${parseInt(item.filename, 10)}` : "credits.html");
    modal.showModal();
  }
  document.querySelector(".modal-close").addEventListener("click", () => modal.close());
  modal.addEventListener("click", (event) => { if (event.target === modal) modal.close(); });
  document.querySelectorAll("[data-open-image]").forEach((button) => {
    button.addEventListener("click", () => showImage(selected, "SHARED IMAGE"));
  });
  const filenameCheck = data.filename_check;
  if (filenameCheck) {
    for (const split of ["train", "val"]) {
      const member = filenameCheck.members.find((item) => item.split === split);
      $(`filename-${split}-image`).src = filenameCheck.image;
      $(`filename-${split}-path`).textContent = member.path;
      $(`filename-${split}-hash`).textContent = filenameCheck.hash;
      document.querySelector(`[data-filename-image="${split}"]`).addEventListener("click", () => {
        showImage({image: filenameCheck.image, filename: member.path.split("/").pop(), path: member.path}, split.toUpperCase());
      });
    }
    $("filename-original").textContent = filenameCheck.source_filename;
  }

  const caseNames = ["renamed", "compression", "lighting", "separate"];
  let currentCase = "renamed";
  function selectCase(name, focus = false) {
    currentCase = name;
    const similarity = data.similarity_examples.find((example) =>
      example.sequence === (name === "lighting" ? "leuven" : "ubc") &&
      (name === "lighting" || example.members[1].filename === "img5.png"));
    let members, report, json, title, setup, result, meaning, boundary, measurements;
    const cocoSource = (filename) => `https://cocodataset.org/#explore?id=${parseInt(filename, 10)}`;
    if (name === "renamed") {
      members = ["train", "val"].map((split) => {
        const member = filenameCheck.members.find((item) => item.split === split);
        return {...member, filename: member.path.split("/").pop(), image: filenameCheck.image,
          hash: filenameCheck.hash, source_url: cocoSource(filenameCheck.source_filename)};
      });
      title = "One photo, saved under two filenames.";
      setup = "Only the name changed. The image file was copied intact into a separate test dataset.";
      result = "Exact overlap detected";
      meaning = "The auditor found identical file bytes across Train and Validation. Changing a filename does not hide this match.";
      boundary = "Controlled demonstration: two copies of one original COCO photo. This is separate from the official COCO split results.";
      measurements = `${filenameCheck.groups} confirmed byte-overlap group. Both SHA-256 digests are identical. Similarity scoring is unnecessary for this exact match.`;
      report = "reports/filename-check.html"; json = "reports/filename-check.json";
    } else if (name === "separate") {
      members = ["train", "val"].map((split) => {
        const item = coco8.items.find((item) => item.splits.includes(split));
        return {...item, source_url: cocoSource(item.filename)};
      });
      title = "Different images in separate splits.";
      setup = "One Train image and one Validation image from COCO8 are shown below. The auditor checked all eight files.";
      result = "No exact overlap found";
      meaning = "Across all 4 Train and 4 Validation images, the auditor found zero exact cross-split groups. These two photos are examples from those splits.";
      boundary = "Official COCO8 split assignments. A zero exact-match result does not establish freedom from other forms of leakage; recording histories remain unverified.";
      measurements = `${coco8.summary.unique_files} unique files; ${coco8.summary.confirmed_exact_groups} exact cross-split groups. This baseline is an exact check; it does not establish visual or source independence.`;
      report = "reports/coco8.html"; json = "reports/coco8.json";
    } else {
      members = similarity.members;
      title = name === "lighting" ? "The scene is related. The lighting changed." : "Compression changed the file, while scene content remains related.";
      setup = "Genuine benchmark images, assigned to Train and Validation here to demonstrate the local auditor.";
      result = "Visual similarity candidate — review needed";
      meaning = "The file bytes differ, so this is not an exact match. The optional visual check flagged the pair for inspection; it does not confirm evaluation leakage.";
      boundary = "Illustrative split assignments, not official benchmark splits. These original benchmark variations were not created by this project.";
      const metric = similarity.similarity;
      measurements = `Measured SSIM: ${metric.structural_similarity_percent.toFixed(2)}%. dHash distance: ${metric.dhash_distance}/64 (candidate threshold ≤ 6). SSIM compares grayscale 128 × 128 images using 7 × 7 windows. These are appearance measurements, not leakage probabilities.`;
      report = similarity.report; json = similarity.json;
    }
    $("case-title").textContent = title;
    $("case-setup").textContent = setup;
    $("case-result").textContent = result;
    $("case-meaning").textContent = meaning;
    $("case-boundary").textContent = boundary;
    $("case-measurements").textContent = measurements;
    $("case-report").href = report; $("case-json").href = json;
    $("comparison-panel").dataset.kind = name === "renamed" ? "exact" : name === "separate" ? "baseline" : "candidate";
    $("comparison-panel").setAttribute("aria-labelledby", `case-${name}`);
    document.querySelectorAll("[data-case]").forEach((button) => {
      const active = button.dataset.case === name;
      button.setAttribute("aria-selected", String(active)); button.tabIndex = active ? 0 : -1;
      if (active && focus) button.focus();
    });
    document.querySelector(".case-technical").open = false;
    for (const [index, side] of ["left", "right"].entries()) {
      const member = members[index];
      $(`case-${side}-image`).src = member.image;
      $(`case-${side}-image`).alt = `${index ? "Validation" : "Train"}: ${member.filename}, ${title}`;
      $(`case-${side}-path`).textContent = member.path;
      $(`case-${side}-hash`).textContent = member.hash;
      $(`case-${side}-source`).href = member.source_url;
      $(`case-${side}-context`).textContent = name === "renamed" ? "Controlled copy" : name === "separate" ? "Official split" : "Illustrative assignment";
      $(`case-${side}-zoom`).onclick = () => showImage(member, index ? "VALIDATION" : "TRAIN");
    }
  }
  document.querySelectorAll("[data-case]").forEach((button) => {
    button.addEventListener("click", () => selectCase(button.dataset.case));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const index = event.key === "Home" ? 0 : event.key === "End" ? 3 :
        (caseNames.indexOf(currentCase) + (event.key === "ArrowRight" ? 1 : 3)) % 4;
      selectCase(caseNames[index], true);
    });
  });
  selectCase("renamed");

  function selectSimilarity(example) {
    const metric = example.similarity;
    $("similarity-score").textContent = `${metric.structural_similarity_percent.toFixed(2)}%`;
    $("similarity-hash-score").textContent = `${metric.hash_agreement_percent.toFixed(2)}%`;
    $("similarity-distance").textContent = `${metric.dhash_distance} of 64 bits differ`;
    $("similarity-meter").value = metric.structural_similarity_percent;
    $("similarity-score-note").textContent = example.sequence === "ubc"
      ? "Compression changes image detail. These files have different SHA-256 hashes, but retain much of the same visual structure."
      : "Lighting changes the score, even when the scene is similar. Hash agreement and structural similarity measure different things.";
    for (const [index, side] of ["left", "right"].entries()) {
      const member = example.members[index];
      $(`similarity-${side}-image`).src = member.image;
      $(`similarity-${side}-image`).alt = `Original ${member.path} from the ${example.sequence.toUpperCase()} benchmark`;
      $(`similarity-${side}-path`).textContent = member.path;
      $(`similarity-${side}-hash`).textContent = member.hash;
      $(`similarity-${side}-source`).href = member.source_url;
      $(`similarity-${side}-zoom`).onclick = () => showImage(member, index === 0 ? "REFERENCE" : "COMPARISON");
    }
    $("similarity-full-report").href = example.report;
    $("similarity-json-report").href = example.json;
    document.querySelectorAll("[data-similarity-example]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.similarityExample === example.id));
    });
  }
  for (const example of data.similarity_examples || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "similarity-example";
    button.dataset.similarityExample = example.id;
    button.setAttribute("aria-pressed", "false");
    const label = document.createElement("span");
    label.textContent = example.sequence === "ubc" ? `Compression · ${example.members[1].filename}` : "Lighting · img2.png";
    const score = document.createElement("strong");
    score.textContent = `${example.similarity.structural_similarity_percent.toFixed(2)}%`;
    button.append(label, score);
    button.addEventListener("click", () => selectSimilarity(example));
    $("similarity-options").append(button);
  }
  if (data.similarity_examples?.length) selectSimilarity(data.similarity_examples[1] || data.similarity_examples[0]);
  document.querySelectorAll("[data-select-similarity]").forEach((link) => {
    link.addEventListener("click", () => {
      const sequence = link.dataset.selectSimilarity;
      const example = data.similarity_examples.find((item) => item.sequence === sequence &&
        (sequence !== "ubc" || item.members[1].filename === "img5.png"));
      selectSimilarity(example);
      selectCase(sequence === "ubc" ? "compression" : "lighting");
    });
  });
  function revealControlledCheck() {
    if (window.location.hash === "#filename-check") $("filename-check").open = true;
  }
  function revealEvidenceTarget() {
    const target = document.getElementById(window.location.hash.slice(1));
    if (!target) return;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === "DETAILS") node.open = true;
    }
  }
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", () => {
      const target = document.getElementById(link.hash.slice(1));
      for (let node = target; node; node = node.parentElement) {
        if (node.tagName === "DETAILS") node.open = true;
      }
    });
  });
  window.addEventListener("hashchange", revealEvidenceTarget);
  revealEvidenceTarget();
  window.addEventListener("hashchange", revealControlledCheck);
  revealControlledCheck();

  function choose(item, updateList = true) {
    selected = item;
    $("selected-filename").textContent = item.filename;
    $("selected-position").textContent = `${String(coco128.items.indexOf(item) + 1).padStart(2, "0")} / ${coco128.items.length}`;
    $("detail-image").src = item.image;
    $("detail-image").alt = `Shared image: ${item.filename}`;
    $("detail-path").textContent = item.path;
    $("detail-credit-link").href = `https://cocodataset.org/#explore?id=${parseInt(item.filename, 10)}`;
    const memberships = item.splits.map((split) => {
      const tag = document.createElement("span");
      tag.className = `split-tag ${split}`;
      tag.textContent = split === "val" ? "VALIDATION" : split.toUpperCase();
      const reference = document.createElement("div");
      reference.className = "split-reference";
      const path = document.createElement("code");
      path.textContent = item.path;
      reference.append(tag, path);
      return reference;
    });
    $("selected-memberships").replaceChildren(...memberships);
    $("selected-hash").textContent = item.hash;
    if (updateList) {
      document.querySelectorAll(".image-option").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.filename === item.filename));
      });
    }
  }

  function renderList() {
    const query = $("image-search").value.trim().toLowerCase();
    const matches = coco128.items.filter((item) => item.filename.toLowerCase().includes(query));
    $("group-count").textContent = query ? `${matches.length} / ${coco128.items.length}` : String(coco128.items.length);
    const fragment = document.createDocumentFragment();
    for (const item of matches) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "image-option";
      button.dataset.filename = item.filename;
      button.setAttribute("aria-pressed", String(item === selected));
      button.setAttribute("aria-label", `Inspect ${item.filename}`);
      const image = document.createElement("img");
      image.src = item.image;
      image.alt = "";
      image.loading = "lazy";
      image.width = 42;
      image.height = 37;
      const text = document.createElement("span");
      text.textContent = item.filename;
      const small = document.createElement("small");
      small.textContent = "Train ↔ Validation";
      text.append(small);
      button.append(image, text);
      button.addEventListener("click", () => choose(item));
      fragment.append(button);
    }
    if (!matches.length) {
      const message = document.createElement("p");
      message.className = "no-results";
      message.textContent = "No image matches that ID. Try 000000000025 or clear the search.";
      fragment.append(message);
    }
    $("image-list").replaceChildren(fragment);
  }
  $("image-search").addEventListener("input", renderList);

  function renderBaseline() {
    for (const split of ["train", "val"]) {
      const fragment = document.createDocumentFragment();
      for (const item of coco8.items.filter((item) => item.splits[0] === split)) {
        const figure = document.createElement("figure");
        figure.className = "baseline-card";
        const button = document.createElement("button");
        button.type = "button";
        button.setAttribute("aria-label", `Enlarge ${split}: ${item.filename}`);
        const image = document.createElement("img");
        image.src = item.image;
        image.alt = `Official COCO8 ${split} image ${item.filename}`;
        image.width = 320;
        image.height = 180;
        image.loading = "lazy";
        const caption = document.createElement("figcaption");
        const code = document.createElement("code");
        code.textContent = item.filename;
        caption.append(code);
        button.append(image);
        button.addEventListener("click", () => showImage(item, split.toUpperCase()));
        figure.append(button, caption);
        fragment.append(figure);
      }
      $(`baseline-${split}`).replaceChildren(fragment);
    }
  }

  function selectDataset(name, focus = false) {
    currentDataset = name;
    const dataset = data.datasets[name];
    document.querySelectorAll("[data-dataset]").forEach((button) => {
      const active = button.dataset.dataset === name;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      if (active && focus) button.focus();
    });
    $("evidence-panel").setAttribute("aria-labelledby", `tab-${name}`);
    $("overlap-inspector").hidden = name !== "coco128";
    $("shared-split-summary").hidden = name !== "coco128";
    $("explorer-title").innerHTML = name === "coco128"
      ? "The same images.<br>Used in both splits."
      : "Eight images.<br>Two separate splits.";
    $("explorer-description").textContent = name === "coco128"
      ? "COCO128 points Train and Validation at one shared folder. Explore how the auditor identifies the reused files."
      : "COCO8 uses four training images and four different validation images. Inspect the files behind its zero exact-overlap result.";
    $("shared-file-count").textContent = coco128.summary.unique_files;
    $("shared-train-count").textContent = `${coco128.summary.split_memberships.train} images`;
    $("shared-val-count").textContent = `${coco128.summary.split_memberships.val} images`;

    $("baseline-panel").hidden = name !== "coco8";
    const summary = dataset.summary;
    $("evidence-count").textContent = `${summary.confirmed_exact_groups} exact groups · ${summary.affected_memberships} affected memberships · ${summary.unique_files} unique files`;
    $("full-report").href = `reports/${name}.html`;
    $("json-report").href = `reports/${name}.json`;
  }
  document.querySelectorAll("[data-dataset]").forEach((button) => {
    button.addEventListener("click", () => selectDataset(button.dataset.dataset));
    button.addEventListener("keydown", (event) => {
      if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        const name = event.key === "Home" ? "coco128" : event.key === "End" ? "coco8" : currentDataset === "coco128" ? "coco8" : "coco128";
        selectDataset(name, true);
      }
    });
  });
  document.querySelectorAll("[data-select-dataset]").forEach((link) => {
    link.addEventListener("click", () => {
      selectDataset(link.dataset.selectDataset);
      if (link.dataset.selectDataset === "coco8") selectCase("separate");
      else $("full-evidence").open = true;
    });
  });

  const commands = {
    windows: {
      install: 'git clone https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector.git\ncd Dataset-Train-Test-Overlap-Detector\npython -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install ".[similarity]"',
      audit: '.\\.venv\\Scripts\\videosplitguard.exe audit "path\\to\\data.yaml" --near-duplicates --output "reports\\first-audit"',
    },
    linux: {
      install: 'git clone https://github.com/asadozzaman/Dataset-Train-Test-Overlap-Detector.git\ncd Dataset-Train-Test-Overlap-Detector\npython3 -m venv .venv\n.venv/bin/python -m pip install ".[similarity]"',
      audit: '.venv/bin/videosplitguard audit "path/to/data.yaml" --near-duplicates --output "reports/first-audit"',
    },
  };
  document.querySelectorAll("[data-os]").forEach((button) => {
    button.addEventListener("click", () => {
      const platform = button.dataset.os;
      document.querySelectorAll("[data-os]").forEach((node) => node.setAttribute("aria-pressed", String(node === button)));
      $("install-command").textContent = commands[platform].install;
      $("audit-command").textContent = commands[platform].audit;
      $("copy-status").textContent = "";
    });
  });
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const text = $(button.dataset.copy).textContent;
      try {
        if (!navigator.clipboard) throw new Error("Clipboard unavailable");
        await navigator.clipboard.writeText(text);
        $("copy-status").textContent = "Command copied. Run it from the project folder.";
      } catch {
        const range = document.createRange();
        range.selectNodeContents($(button.dataset.copy));
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        $("copy-status").textContent = "Command selected. Press Ctrl+C (or Command+C) to copy.";
      }
    });
  });

  const navLinks = [...document.querySelectorAll(".site-header nav a")];
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          navLinks.forEach((link) => link.classList.toggle("active", link.hash === `#${entry.target.id}`));
        }
      }
    }, {rootMargin: "-15% 0px -60% 0px"});
    navLinks.forEach((link) => observer.observe(document.querySelector(link.hash)));
  }
  renderList();
  renderBaseline();
  choose(selected);
  selectDataset("coco128");
  if (data.source_links_only) {
    document.body.classList.add("source-links-view");
    const notice = document.createElement("p");
    notice.className = "source-publication-note section-shell";
    notice.textContent = "This public edition contains verified audit results and links to original images. Dataset photos are not hosted here. Open an image source to inspect it.";
    document.getElementById("main").prepend(notice);
    document.querySelectorAll(".image-open > span").forEach((node) => { node.textContent = "Open original source ↗"; });
    document.querySelectorAll(".image-open").forEach((node) => { node.setAttribute("aria-label", "Open original image source in a new tab"); });
    document.querySelectorAll('img[src="source-preview.svg"]').forEach((node) => { node.setAttribute("aria-hidden", "true"); });
    document.querySelector(".rights-note").textContent = "This edition hosts results and original-source links. The complete image-preview build remains local while image redistribution permission and individual attribution are unresolved.";
  }
})();
