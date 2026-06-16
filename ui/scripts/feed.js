console.log("feed.js loaded");

// ✅ Check if BLENDS exists
if (typeof BLENDS === "undefined") {
  console.error("BLENDS is not defined");
}

// ✅ Run AFTER DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  renderFeed();
});

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

      <!-- ✅ ✅ FIXED SOURCES (CLICKABLE) -->
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

// ✅ Open blend page
function openBlend(id) {
  console.log("Opening blend:", id);
  window.location.href = `/ui/blend.html?id=${id}`;
}