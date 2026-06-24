console.log("feed.js loaded");

// ✅ Check if BLENDS exists
if (typeof BLENDS === "undefined") {
  console.error("BLENDS is not defined");
}

// ✅ STATE
let currentView = "blends";

// ✅ ON LOAD
document.addEventListener("DOMContentLoaded", () => {
  console.log("feed.js ready");
});


// ✅ SWITCH VIEWS (TAB CLICK)
function setView(view) {
  currentView = view;

  document.querySelectorAll(".tab").forEach(btn =>
    btn.classList.remove("active")
  );

  event.target.classList.add("active");

  renderCurrentView();
}


// ✅ MAIN VIEW ROUTER
function renderCurrentView() {
  if (currentView === "creators") {
    renderTopCreators();
  } else {
    renderFeed();
  }
}


// ✅ ✅ TOP CREATORS (RANKING VIEW)
function renderTopCreators() {
  const container = document.getElementById("feed");

  const counts = {};

  BLENDS.forEach(b => {
    (b.sources || []).forEach(source => {
      counts[source] = (counts[source] || 0) + 1;
    });
  });

  const sorted = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);

  container.innerHTML = sorted.map(([name, count]) => `
    <div class="card" onclick="goToSource('${name}', event)">
      <div class="card-title">${name}</div>
      <div class="card-meta">
        ${count} blend${count > 1 ? "s" : ""}
      </div>
    </div>
  `).join("");
}


// ✅ ✅ AUTO-BLEND GENERATOR
function generateAutoBlends() {
  const pairCounts = {};

  // ✅ Count co-occurrences
  BLENDS.forEach(b => {
    const sources = b.sources || [];

    for (let i = 0; i < sources.length; i++) {
      for (let j = i + 1; j < sources.length; j++) {
        const key = [sources[i], sources[j]].sort().join("::");
        pairCounts[key] = (pairCounts[key] || 0) + 1;
      }
    }
  });

  // ✅ Only strong overlaps
  const pairs = Object.entries(pairCounts)
    .filter(([_, count]) => count >= 2);

  // ✅ Generate blends
  const autoBlends = pairs.map(([key, count], index) => {
    const [a, b] = key.split("::");

    return {
      id: "auto-" + index,
      title: generateTitle(a, b),
      subtitle: "Emerging patterns across conversations",
      clips: Math.floor(Math.random() * 60 + 20),
      tags: ["auto", "insight"],
      sources: [a, b],
      isAuto: true
    };
  });

  return autoBlends;
}


// ✅ AUTO TITLE GENERATOR
function generateTitle(a, b) {
  const templates = [
    `${a} & ${b}: Shared Perspectives`,
    `Conversations Between ${a} and ${b}`,
    `Where ${a} Meets ${b}`,
    `${a} x ${b}: Cross Ideas`,
    `${a} and ${b} on the Same Signal`
  ];

  return templates[Math.floor(Math.random() * templates.length)];
}


// ✅ ✅ FEED (BLENDS VIEW + AUTO GENERATION)
function renderFeed() {
  const container = document.getElementById("feed");

  if (!container) {
    console.error("Feed container not found");
    return;
  }

  if (!Array.isArray(BLENDS) || BLENDS.length === 0) {
    container.innerHTML = "<p>No blends available</p>";
    return;
  }

  // ✅ Generate + merge
  const autoBlends = generateAutoBlends();
  const combined = [...autoBlends, ...BLENDS];

  container.innerHTML = combined.map((b) => `
    <div class="card" onclick="openBlend('${b.id}')">

      ${b.isAuto ? `
        <div style="font-size:0.7rem; color:#cfa85c; margin-bottom:6px;">
          ✨ Generated Insight
        </div>
      ` : ""}

      <div class="card-content">
        <div>
          <div class="card-title">${b.title}</div>
          <div class="card-description">${b.subtitle}</div>
        </div>
      </div>

      <!-- TAGS -->
      <div class="tags">
        ${(b.tags || []).map(tag => `
          <span class="tag">${tag}</span>
        `).join("")}
      </div>

      <!-- SOURCES -->
      <div class="tags">
        ${(b.sources || []).map(source => `
          <span class="tag"
                onclick="goToSource('${source}', event)">
            ${source}
          </span>
        `).join("")}
      </div>

      <!-- META -->
      <div class="actions">
        <span>🎧 ${b.clips || 0} clips</span>
      </div>

    </div>
  `).join("");
}


// ✅ NAV TO BLEND
function openBlend(id) {
  console.log("Opening blend:", id);
  window.location.href = `/ui/blend.html?id=${id}`;
}


// ✅ NAV TO CREATOR
function goToSource(name, event) {
  event.stopPropagation();
  window.location.href =
    '/ui/source.html?name=' + encodeURIComponent(name);
}