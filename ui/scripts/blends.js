// =====================================
// PodBlendz Live Feed
// =====================================

let BLENDS = [];

async function loadBlends() {

  try {

    console.log("Loading Blendz...");

    const response = await fetch(
      "https://api.podblendz.com/blends"
    );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    const data = await response.json();

    console.log("FIRST BLEND", data[0]);

    BLENDS = data.map(blend => ({

      id: blend.id,

      title: blend.title,

      subtitle:
        blend.summary ||
        blend.description ||
        "Discover what the world's leading experts collectively think about any topic.",

      clips:
        blend.clip_count || 0,

      tags: ["blend"],

      sources: blend.creators || [],
      episode_objects:
      blend.episode_objects || [],
    
      duration_ms:
        blend.duration_ms,

      audio_file:
        blend.audio_file,

      confidence_label:
        blend.confidence_label,

      created_at:
        blend.created_at

    }));

    console.log(
      `✅ Loaded ${BLENDS.length} Blendz`
    );

    if (
      typeof renderCurrentView === "function"
    ) {
      renderCurrentView();
    }

  } catch (error) {

    console.error(
      "❌ Failed to load blends:",
      error
    );

    BLENDS = [];

    const feed =
      document.getElementById("feed");

    if (feed) {

      feed.innerHTML = `
        <div class="card">
          <div class="card-title">
            Unable to load Blendz
          </div>

          <div class="card-description">
            Make sure the PodBlendz backend is running.
          </div>
        </div>
      `;
    }
  }
}


// =====================================
// Load on Startup
// =====================================

document.addEventListener(
  "DOMContentLoaded",
  loadBlends
);