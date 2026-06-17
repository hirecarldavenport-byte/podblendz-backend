console.log("feed.js loaded");

// ✅ Check if BLENDS exists
if (typeof BLENDS === "undefined") {
  console.error("BLENDS is not defined");
}

// ✅ STATE
let currentView = "blends";

// ✅ ON LOAD
document.addEventListener("DOMContentLoaded", () => {
  renderCurrentView();
});


// ✅ SWITCH VIEWS (TAB CLICK)
function setView(view) {
  currentView = view;

  // ✅ Update active tab
  document.querySelectorAll(".tab").forEach(btn =>
    btn.classList.remove("active")
  );

  // ✅ Highlight clicked tab
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

  if (!container) {
    console.warn("Feed container not found");
    return;
  }

  const counts = {};

  // ✅ Count appearances
  BLENDS.forEach(b => {
    (b.sources || []).forEach(source => {
      counts[source] = (counts[source] || 0) + 1;
    });
  });

  // ✅ Sort descending
  const sorted = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);

  // ✅ Render
  container.innerHTML = sorted.map(([name, count]) => `
    <div class="card" onclick="goToSource('${name}', event)">
      <div class="card-title">${name}</div>
      <div class="card-meta">
        ${count} blend${count > 1 ? "s" : ""}
      </div>
    </div>
  `).join("");
}


// ✅ ✅ FEED (BLENDS VIEW)
function renderFeed() {
  const container = document.getElementById("feed");

  if (!container) {
    console.error("Feed container not found");
    return;
  }

  // ✅ Validate BLENDS
  if (!Array.isArray(BLENDS) || BLENDS.length === 0) {
    console.warn("BLENDS is empty or not an array");
    container.innerHTML = "<p>No blends available</p>";
    return;
  }

  container.innerHTML = BLENDS.map((b) => `
    <div class="card" onclick="openBlend('${b.id}')">
      
      <div class="card-content">
        <div>
          <div class="card-title">${b.title}</div>
          <div class="card-description">${b.subtitle}</div>
        </div>
      </div>

      <!-- ✅ TAGS -->
      <div class="tags">
        ${(b.tags || []).map(tag => `
          <span class="tag">${tag}</span>
        `).join("")}
      </div>

      <!-- ✅ CLICKABLE SOURCES -->
      <div class="tags">
        ${(b.sources || []).slice(0, 3).map(source => `
          <span class="tag"
                onclick="goToSource('${source}', event)">
            ${source}
          </span>
        `).join("")}
      </div>

      <!-- ✅ ACTIONS -->
      <div class="actions">
        <div class="actions-left">
          <span>🎧 ${b.clips || 0} clips</span>
        </div>
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