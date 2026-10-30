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
    $("repository-note").textContent = "Source code and installation instructions are available in the repository.";
  }
  $("hero-image").src = selected.image;
  $("hero-filename").textContent = selected.filename;
  $("hero-position").textContent = `${String(coco128.items.indexOf(selected) + 1).padStart(2, "0")} / ${coco128.items.length}`;

  function showImage(item, label) {
    $("modal-title").textContent = `${label} · ${item.filename}`;
    $("modal-image").src = item.image;
    $("modal-image").alt = `${label}: ${item.filename}, original dataset image`;
    $("modal-reference").textContent = item.path;
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
      return tag;
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
    link.addEventListener("click", () => selectDataset(link.dataset.selectDataset));
  });

  const commands = {
    windows: {
      install: "python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install .",
      audit: '.\\.venv\\Scripts\\videosplitguard.exe audit "data\\data.yaml" --output "reports\\first-audit"',
    },
    linux: {
      install: "python3 -m venv .venv\n.venv/bin/python -m pip install .",
      audit: '.venv/bin/videosplitguard audit "data/data.yaml" --output "reports/first-audit"',
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
})();
