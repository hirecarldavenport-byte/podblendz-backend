console.log("feed.js loaded");

// Make sure BLENDS exists
if (typeof BLENDS === "undefined") {
  console.error("BLENDS is not defined");
}

function renderFeed() {
  const container = document.getElementById("feed");

  if (!container) {
    console.error("Feed container not found");
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

      <div class="tags">
        ${b.tags.map(tag => `<span class="tag">${tag}</span>`).join("")}
      </div>

      <div class="actions">
        <div class="actions-left">
          <span>🎧 ${b.clips} clips</span>
        </div>
      </div>

    </div>
  `).join("");
}

function openBlend(id) {
  window.location.href = `/ui/blend.html?id=${id}`;
}

// Run it
renderFeed();