async function loadFeed() {

  const response =
    await fetch("./data/guided_topic_cards.json");

  const cards =
    await response.json();

  const feed =
    document.querySelector(".feed");

  feed.innerHTML = "";

  cards.slice(0, 12).forEach((card, index) => {

    const keywords = card.keywords
      .slice(0, 4)
      .map(
        k => `<div class="tag">${k[0]}</div>`
      )
      .join("");

    const phrase =
      card.phrases?.[0] ||
      "Semantic podcast blend";

    const colors = [
      "#9149ff",
      "#46c7b8",
      "#ff7b54",
      "#5c7cfa",
      "#d4a017"
    ];

    const accent =
      colors[index % colors.length];

    const html = `

      <div
        class="card"
        onclick="openBlend('${encodeURIComponent(card.topic)}')"
        style="cursor:pointer;"
      >

        <div class="card-top">

          <div class="card-user">

            <img
              src="https://i.pravatar.cc/100?img=${index + 10}"
              alt=""
            />

            <div class="card-meta">

              <h4>${card.topic}</h4>

              <p>
                Guided semantic blend
              </p>

            </div>

          </div>

          <div class="card-time">
            AI
          </div>

        </div>

        <div class="card-content">

          <div>

            <div class="card-title">
              ${card.title}
            </div>

            <div class="card-description">
              ${phrase}
            </div>

          </div>

          <img
            class="card-cover"
            src="https://source.unsplash.com/300x300/?${encodeURIComponent(card.topic)}"
            alt=""
          />

        </div>

        <div class="player">

          <div
            class="play-btn"
            style="
              border-color:${accent};
              color:${accent};
            "
          >
            ▶
          </div>

          <div
            class="waveform"
            style="
              background:
              repeating-linear-gradient(
                to right,
                ${accent},
                ${accent} 2px,
                transparent 2px,
                transparent 6px
              );
            "
          ></div>

          <div class="duration">
            ${card.related_segment_count} clips
          </div>

        </div>

        <div class="tags">
          ${keywords}
        </div>

        <div class="actions">

          <div class="actions-left">

            <div>
              🧠 ${card.phrases.length}
            </div>

            <div>
              🎙 ${card.related_segment_count}
            </div>

          </div>

          <div>↗</div>

        </div>

      </div>

    `;

    feed.insertAdjacentHTML(
      "beforeend",
      html
    );

  });

}

function openBlend(topic) {

  window.location.href =
    `./blend.html?topic=${topic}`;

}

loadFeed();
