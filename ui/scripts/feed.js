console.log("feed.js loaded");

// ✅ Check if BLENDS exists
if (typeof BLENDS === "undefined") {
  console.error("BLENDS is not defined");
}

// ✅ STATE
let currentView = "blends";

// ✅ SEARCH TEXT (blends view)
let feedQuery = "";

// ✅ ON LOAD
document.addEventListener("DOMContentLoaded", () => {
  console.log("feed.js ready");

  initSearch();

  waitForBlends();
});

// blends.js fills BLENDS in the background, so wait for it
function waitForBlends(attempt = 0) {

  const container = document.getElementById("feed");
  const ready = typeof BLENDS !== "undefined" &&
                Array.isArray(BLENDS) && BLENDS.length > 0;

  if (ready) {
    renderCurrentView();
    return;
  }

  if (attempt === 0 && container) {
    container.innerHTML = '<div class="state-msg">Loading blends…</div>';
  }

  if (attempt < 40) {
    setTimeout(() => waitForBlends(attempt + 1), 300);
    return;
  }

  if (container) {
    container.innerHTML =
      '<div class="state-msg">Couldn\'t load blends.<br>' +
      '<button onclick="location.reload()">Try again</button></div>';
  }
}

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


// ✅ SAFE TEXT / SAFE onclick VALUES
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => (
    { "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]
  ));
}

// a JS string that is safe inside onclick="..."
function jsArg(v) {
  return JSON.stringify(String(v ?? "")).replace(/"/g, "&quot;");
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

  document.querySelectorAll(".tab").forEach(btn =>
    btn.classList.toggle("active", btn.dataset.view === view)
  );

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
      <div class="card">

      <button
        class="blend-btn"
        onclick="renderTopCreators()"
        style="margin-bottom:15px;"
        >
          ← Back
        </button>

        <div class="card-title">
          ${esc(formatCreator(creatorName))}
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
      ${esc(topic)}
    </span>
  `).join("")}

</div>

      

      </div>
      `;

    container.innerHTML += creatorBlends.map(blend => `

      <div
        class="card"
        onclick="openBlend(${jsArg(blend.id)})"
        >
          <div class="card-title">
            ${esc(blend.title)}
          </div>

          <div class="card-description">
            ${esc(blend.subtitle)}

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
      onclick="openCreator(${jsArg(name)})"
      style="cursor:pointer;"
    >

      <div class="card-title">
        ${esc(formatCreator(name))}
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
        onclick="openBoard(${jsArg(name)})"
        style="cursor:pointer;"
      >

        <div class="card-title">
          ${esc(name)}
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

if (feedQuery) {
  combined = combined.filter(blend => {
    const hay = [
      blend.title, blend.subtitle, blend.board,
      ...(blend.sources || []).map(formatCreator)
    ].join(" ").toLowerCase();
    return hay.includes(feedQuery);
  });
}

let html = "";

if (selectedBoard) {

  html += `
    <div class="card">
      <div class="card-title">
        📚 ${esc(selectedBoard)}
      </div>

      <div class="card-description">
        Community Board
      </div>
    </div>
  `;

}



  

  if (feedQuery && combined.length === 0) {
    html += `<div class="state-msg">No blends match “${esc(feedQuery)}”.</div>`;
  }

  html += combined.map((b) => `

    <div
      class="card"
      onclick="openBlend(${jsArg(b.id)})"
    >

      <div class="card-content">

        <div>

          <div class="category-label">
            ${esc((b.board || "General").toUpperCase())}
          </div>

          <div class="card-title">
          ${esc(b.title)}
          </div>


          <div class="card-description">
            ${esc(b.subtitle)}
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
      openCreator(${jsArg(source)});
      event.stopPropagation();
    "
    style="cursor:pointer;"
  >
    🎙 ${esc(formatCreator(source))}
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

}


// ✅ OPEN BLEND
function openBlend(id) {

  // saving is a nicety; if the browser blocks storage the click must still work
  try { localStorage.setItem("dnaSeedBlendId", id); } catch (e) {}

  window.location.href =
     "/community-feed.html?blend=" + encodeURIComponent(id);

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


/* =====================================================
   SEARCH (type-ahead, same behaviour as the community page)
   Looks across ALL blends, creators and boards, not just
   what is on screen.
===================================================== */
let searchItems = [];     // flat list of what is shown, in order
let searchActive = -1;
let searchShowAll = false;

function highlight(text, q) {
  const i = q ? text.toLowerCase().indexOf(q) : -1;
  if (i < 0) return esc(text);
  return esc(text.slice(0, i)) +
    "<mark>" + esc(text.slice(i, i + q.length)) + "</mark>" +
    esc(text.slice(i + q.length));
}

function closeSearch() {
  const box = document.getElementById("searchResults");
  if (box) box.style.display = "none";
  searchActive = -1;
}

function setSearchActive(i) {
  const els = document.querySelectorAll("#searchResults .sr-item");
  els.forEach(el => el.classList.remove("active"));
  searchActive = i;
  if (els[i]) {
    els[i].classList.add("active");
    els[i].scrollIntoView({ block: "nearest" });
  }
}

function searchBlendsList() {
  return (typeof BLENDS !== "undefined" && Array.isArray(BLENDS)) ? BLENDS : [];
}

function renderSearch(raw) {

  const q = raw.trim().toLowerCase();
  const box = document.getElementById("searchResults");
  const list = searchBlendsList();

  box.style.display = "block";
  searchActive = -1;
  searchItems = [];

  if (!list.length) {
    box.innerHTML = '<div class="sr-empty">Blends are still loading...</div>';
    return;
  }

  // empty box: suggest the newest blends (the API lists newest first)
  if (!q) {
    searchItems = list.slice(0, 6).map(b => ({ kind: "blend", b }));
    box.innerHTML = '<div class="sr-head">Newest blends</div>' +
      searchItems.map((it, i) => blendRow(it.b, i, "")).join("");
    return;
  }

  const words = q.split(/\s+/);
  const matchesAll = hay => words.every(w => hay.includes(w));

  // blends
  const blends = [];
  list.forEach(b => {
    const title = String(b.title || "").toLowerCase();
    const hay = (title + " " + String(b.board || "") + " " +
      (b.sources || []).map(formatCreator).join(" ")).toLowerCase();
    if (!matchesAll(hay)) return;
    let score = 0;
    if (title.startsWith(q)) score += 3;
    if (title.includes(q)) score += 2;
    words.forEach(w => { if (title.includes(w)) score += 1; });
    blends.push({ b, score });
  });
  blends.sort((a, b) => b.score - a.score);

  // creators
  const creatorCount = {};
  list.forEach(b => (b.sources || []).forEach(s => {
    creatorCount[s] = (creatorCount[s] || 0) + 1;
  }));
  const creators = Object.keys(creatorCount)
    .filter(s => matchesAll((formatCreator(s) + " " + s).toLowerCase()))
    .sort((a, b) => creatorCount[b] - creatorCount[a])
    .slice(0, 3);

  // boards
  const boardCount = {};
  list.forEach(b => {
    const name = b.board;
    if (name && name !== "Uncategorized") boardCount[name] = (boardCount[name] || 0) + 1;
  });
  const boards = Object.keys(boardCount)
    .filter(n => matchesAll(n.toLowerCase()))
    .slice(0, 2);

  if (!blends.length && !creators.length && !boards.length) {
    box.innerHTML = '<div class="sr-empty">Nothing found for \u201c' + esc(raw.trim()) + '\u201d.</div>';
    return;
  }

  const limit = searchShowAll ? 40 : 6;
  const shown = blends.slice(0, limit);

  let html = "";
  let i = 0;

  if (shown.length) {
    html += '<div class="sr-head">' + blends.length + ' blend' +
            (blends.length === 1 ? "" : "s") + '</div>';
    shown.forEach(x => {
      searchItems.push({ kind: "blend", b: x.b });
      html += blendRow(x.b, i++, q);
    });
    if (!searchShowAll && blends.length > limit) {
      html += '<div class="sr-more">Show all ' + blends.length + ' matches</div>';
    }
  }

  if (creators.length) {
    html += '<div class="sr-head">Creators</div>';
    creators.forEach(name => {
      searchItems.push({ kind: "creator", name });
      html += '<div class="sr-item" role="option" data-i="' + (i++) + '">' +
        '<div class="sr-title">\uD83C\uDF99 ' + highlight(formatCreator(name), q) + '</div>' +
        '<div class="sr-meta">' + creatorCount[name] + ' blend' +
        (creatorCount[name] === 1 ? "" : "s") + '</div></div>';
    });
  }

  if (boards.length) {
    html += '<div class="sr-head">Boards</div>';
    boards.forEach(name => {
      searchItems.push({ kind: "board", name });
      html += '<div class="sr-item" role="option" data-i="' + (i++) + '">' +
        '<div class="sr-title">\uD83D\uDCDA ' + highlight(name, q) + '</div>' +
        '<div class="sr-meta">' + boardCount[name] + ' blend' +
        (boardCount[name] === 1 ? "" : "s") + '</div></div>';
    });
  }

  box.innerHTML = html;
}

function blendRow(b, i, q) {
  const first = (b.sources || [])[0];
  return '<div class="sr-item" role="option" data-i="' + i + '">' +
    '<div class="sr-title">' + highlight(String(b.title || ""), q) + '</div>' +
    '<div class="sr-meta">' + esc(b.board || "General") + ' \u2022 ' + (b.clips || 0) + ' clips' +
    (first ? ' \u2022 ' + esc(formatCreator(first)) : "") + '</div></div>';
}

function pickSearchResult(i) {
  const it = searchItems[i];
  if (!it) return;
  closeSearch();
  const input = document.getElementById("feedSearch");
  input.blur();

  if (it.kind === "blend") {
    openBlend(it.b.id);
  } else if (it.kind === "creator") {
    input.value = "";
    setView("creators");          // highlight the tab, then show that creator
    openCreator(it.name);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else if (it.kind === "board") {
    openBoard(it.name);
  }
}

function initSearch() {

  const input = document.getElementById("feedSearch");
  const box = document.getElementById("searchResults");
  const wrap = document.getElementById("searchWrap");
  if (!input || !box) return;

  input.addEventListener("input", () => { searchShowAll = false; renderSearch(input.value); });
  input.addEventListener("focus", () => { searchShowAll = false; renderSearch(input.value); });
  input.addEventListener("click", () => {
    if (box.style.display !== "block") renderSearch(input.value);
  });

  input.addEventListener("keydown", e => {
    const n = searchItems.length;
    if (e.key === "Escape") { closeSearch(); return; }
    if (box.style.display !== "block" || !n) return;

    if (e.key === "ArrowDown") { e.preventDefault(); setSearchActive((searchActive + 1) % n); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSearchActive((searchActive - 1 + n) % n); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (!input.value.trim() && searchActive < 0) return;
      pickSearchResult(searchActive >= 0 ? searchActive : 0);
    }
  });

  // mousedown (not click) so the input doesn't lose focus first
  box.addEventListener("mousedown", e => {
    if (e.target.closest(".sr-more")) {
      e.preventDefault();
      searchShowAll = true;
      renderSearch(input.value);
      return;
    }
    const item = e.target.closest(".sr-item");
    if (!item) return;
    e.preventDefault();
    pickSearchResult(Number(item.dataset.i));
  });

  document.addEventListener("click", e => {
    if (wrap && !wrap.contains(e.target)) closeSearch();
  });
}
