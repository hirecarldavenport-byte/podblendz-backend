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
  renderCurrentView();
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


// ✅ CONFIDENCE BADGE (accepts old "Verified" rows too)
function confBadge(blend) {

  const raw = blend && blend.confidence_label;
  if (!raw) return "";

  const label = String(raw).replace(/^Verified$/i, "Corroborated");
  let key = label.toLowerCase().replace(/[^a-z]/g, "");

  if (!["corroborated","supported","emerging","contested","unverified"].includes(key)) {
    key = "unverified";
  }

  const colors = {
    corroborated:["#3ddc97","rgba(61,220,151,.12)","rgba(61,220,151,.4)"],
    supported:["#5aa8ff","rgba(90,168,255,.12)","rgba(90,168,255,.4)"],
    emerging:["#ffb84d","rgba(255,184,77,.12)","rgba(255,184,77,.4)"],
    contested:["#ff6b6b","rgba(255,107,107,.12)","rgba(255,107,107,.4)"],
    unverified:["#999","rgba(255,255,255,.05)","rgba(255,255,255,.15)"]
  }[key];

  return `<span style="display:inline-block;font-size:.72rem;font-weight:700;
    letter-spacing:.04em;padding:3px 10px;border-radius:999px;
    color:${colors[0]};background:${colors[1]};border:1px solid ${colors[2]};">
    ${label}</span>`;
}

// ✅ SWITCH VIEWS
function setView(view) {

  currentView = view;

  if (
    view === "blends" &&
    window.location.search.includes("board=")
  ) {

    window.history.replaceState(
      {},
      "",
      "/feed.html"
    );

  }

  document
    .querySelectorAll(".tab")
    .forEach(btn =>
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
  } else if (currentView === "following") {

    renderBoards();

    } else {
      renderFeed();

    }
  }

function openCreator(creatorName) {

  const creatorBlends = BLENDS.filter(blend =>
    (blend.sources || []).includes(creatorName)
    );

    const topicCounts = {};

creatorBlends.forEach(blend => {

  const board =
    blend.board || "General";

  topicCounts[board] =
    (topicCounts[board] || 0) + 1;

});

const topTopics =
  Object.entries(topicCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);


    const container = document.getElementById("feed");

    container.innerHTML = `
      <div class="card"

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

<div
  style="
    margin-top:12px;
    color:#888;
    font-size:.75rem;
    text-transform:uppercase;
    letter-spacing:.08em;
  "
>
  Top Topics
</div>

<div class="tags">

  ${topTopics.map(([topic]) => `
    <span class="tag">
      ${topic}
    </span>
  `).join("")}

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
      class="card"
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

console.log("BOARDS VERSION");

function renderBoards() {

  const container =
    document.getElementById("feed");

  const boards = {};

  BLENDS.forEach(blend => {

    const board =
      blend.board || "Uncategorized";

      boards[board] =
        (boards[board] || 0) + 1;


    });

  const sorted =
    Object.entries(boards)
      .sort((a, b) => b[1] - a[1]);

  container.innerHTML =
    sorted.map(([name, count]) => `

      <div
        class="card"
        onclick="openBoard('${name}')"
        style="cursor:pointer;"
      >

        <div class="card-title">
          ${name}
        </div>

        <div class="card-description">
          ${count} Blendz
        </div>

      </div>

    `).join("");

}

  function openBoard(boardName) {

  window.location.href =
    `./feed.html?board=${encodeURIComponent(boardName)}`;

}

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

    }

    const params =
  new URLSearchParams(
    window.location.search
  );

const selectedBoard =
  params.get("board");
  

  let combined = [...BLENDS];

if (selectedBoard) {

  combined = combined.filter(
    blend =>
      (blend.board || "") ===
      selectedBoard
  );

}

let html = "";

if (selectedBoard) {

  html += `
    <div class="card">
      <div class="card-title">
        📚 ${selectedBoard}
      </div>

      <div class="card-description">
        Community Board
      </div>
    </div>
  `;

}



  

  html += combined.map((b) => `

    <div
      class="card"
      onclick="openBlend('${b.id}')"
    >

      <div class="card-content">

        <div>

          <div class="category-label">
            ${(b.board || "General").toUpperCase()}
          </div>

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

  <span
    class="tag"
    onclick="
      openCreator('${source}');
      event.stopPropagation();
    "
    style="cursor:pointer;"
  >
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
        ${confBadge(b) ? `<span style="margin-left:10px;">${confBadge(b)}</span>` : ""}

      </div>

    </div>

  `).join("");

  container.innerHTML = html;




// ✅ OPEN BLEND
function openBlend(id) {

  localStorage.setItem(
    "dnaSeedBlendId",
    id);

  console.log(
    "Opening blend:",
    id
  );

  window.location.href =
     "./community-feed.html";

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

}}
