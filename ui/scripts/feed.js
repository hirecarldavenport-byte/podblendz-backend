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

// ✅ HUMANIZE CREATOR NAMES
function formatCreator(name) {

  const creators = {

    "huberman_lab": "Huberman Lab",
    "lex_fridman_podcast": "Lex Fridman Podcast",
    "science_vs": "Science Vs",
    "short_wave": "NPR Short Wave",
    "diary_of_a_ceo": "The Diary of a CEO",
    "dna_today": "DNA Today"

  };

  return creators[name] ||
    name
      .replace(/_/g, " ")
      .replace(/\b\w/g, c => c.toUpperCase());
}


// ✅ SWITCH VIEWS
function setView(view) {

  currentView = view;

  document.querySelectorAll(".tab").forEach(btn =>
    btn.classList.remove("active")
  );

  if (window.event?.target) {
    window.event.target.classList.add("active");
  }

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
function openCreator(creatorName) {

  const creatorBlends = BLENDS.filter(blend =>
    (blend.sources || []).includes(creatorName)
    );

    const container = document.getElementById("feed");

    container.innerHTML = `
      <div class="card">

      <button
        class="blend-btn"
        onclick="renderTopCreators()"
        style="margin-bottom:15px;"
        >
          ← Back
        </button>

        <div class="card-title">
          ${formatCreator(creatorName)}
        </div>

        <div class="card-description">
          Appears in ${creatorBlends.length} Blendz
        </div>

      </div>
      `;

    container.innerHTML += creatorBlends.map(blend => `

      <div
        class="card"
        onclick="openBlend('${blend.id}')"
        >
          <div class="card-title">
            ${blend.title}
          </div>

          <div class="card-description">
            ${blend.subtitle || ""}

          </div>

          <div class="actions">
            🎧 ${blend.clips || 0} clips

          </div>
        </div>

        `).join("");
      
      }

// ✅ TOP CREATORS
function renderTopCreators() {

  const container = document.getElementById("feed");

  const counts = {};

  BLENDS.forEach(b => {

    (b.sources || []).forEach(source => {

      counts[source] =
        (counts[source] || 0) + 1;

    });

  });

  const sorted = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);

  container.innerHTML = sorted.map(([name, count]) => `

    <div 
      class="card">
      onclick="openCreator('${name}')"
      style="cursor:pointer;"
    >

      <div class="card-title">
        ${formatCreator(name)}
      </div>

      <div class="card-meta">
        ${count} blend${count > 1 ? "s" : ""}
      </div>

    </div>

  `).join("");

}



// ✅ FEED
function renderFeed() {

  const container =
    document.getElementById("feed");

  if (!container) {

    console.error(
      "Feed container not found"
    );

    return;
  }

  if (
    !Array.isArray(BLENDS) ||
    BLENDS.length === 0
  ) {

    container.innerHTML =
      "<p>No blends available</p>";

    return;
  

  const combined = [...BLENDS];

  }

  container.innerHTML = sorted.map(([name, count]) => `

    <div
      class="card"
      onclick="openBlend('${b.id}')"
    >

      <div class="card-content">

        <div>

          <div class="card-title">
            ${b.title}
          </div>

          <div class="card-description">
            ${b.subtitle}
          </div>

          <div
            style="
              margin-top:10px;
              font-size:0.85rem;
              color:#777;
            "
          >
            Generated from ${(b.sources || []).length} creators • ${b.clips || 0} clips
            </div>

        </div>

      </div>

      <!-- TAGS -->

      <div class="tags">

        ${(b.tags || []).map(tag => `

          <span class="tag">
            ${tag}
          </span>

        `).join("")}

      </div>

      <!-- Featuring Insights From -->

      ${(b.sources || []).length ? `

        <div
          style="
            font-size:0.75rem;
            font-weight:600;
            color:#888;
            margin-top:10px;
            margin-bottom:6px;
            text-transform:uppercase;
            letter-spacing:.05em;
          "
        >
          Featuring Insights From
        </div>

        <div class="tags">

          ${(b.sources || []).map(source => `

            <span class="tag">
              🎙 ${formatCreator(source)}
            </span>

          `).join("")}

        </div>

      ` : ""}

      <!-- META -->

      <div class="actions">

        <span>
          🎧 ${b.clips || 0} clips
        </span>

      </div>

    </div>

  `).join("");

}


// ✅ OPEN BLEND
function openBlend(id) {

  console.log(
    "Opening blend:",
    id
  );

  window.location.href =
    `./blend.html?id=${id}`;

}


// ✅ CREATOR CLICK DISABLED FOR NOW
function goToSource(name, event) {

  if (event) {
    event.stopPropagation();
  }

  console.log(
    "Creator clicked:",
    name
  );

  // Future:
  // window.location.href =
  // `/source.html?name=${encodeURIComponent(name)}`;

}
