const log   = document.getElementById("log");
const qEl   = document.getElementById("q");
const ragCB = document.getElementById("rag");
const sendB = document.getElementById("send");

/* ---------- helpers ---------- */

// 1. add node and scroll to bottom
function addNode(node) {
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
}

// 2. highlight keyword
function highlightKeyword(text, keyword) {
  if (!keyword) return text;
  const pattern = new RegExp(`(${keyword})`, "gi");
  return text.replace(pattern, "<mark>$1</mark>");
}

/* ---------- main flow ---------- */

sendB.onclick = async () => {
  const txt = qEl.value.trim();
  if (!txt) return;
  qEl.value = "";

  // user input
  addNode(Object.assign(document.createElement("div"), {
    textContent: "> " + txt,
    className:   "user"
  }));

  const endpoint = ragCB.checked ? "/rag_query" : "/query";

  const r = await fetch(endpoint, {
    method : "POST",
    headers: { "Content-Type": "application/json" },
    body   : JSON.stringify({ query: txt })
  }).then(r => r.json()).catch(e => ({ error: e }));

  if (r.error) {
    addNode(Object.assign(document.createElement("div"), {
      textContent: "❌ " + r.error,
      className  : "system"
    }));
    return;
  }

  /* ======== RAG mode ======== */
  if (ragCB.checked) {
    /* Gemini summary block */
    addNode(Object.assign(document.createElement("div"), {
      innerHTML: `
        <div style="padding:.5rem;background:#eef;border-left:5px solid #88f;
                    margin:.5rem 0;">
          <b>📝 Gemini summary:</b><br>${r.answer}
        </div>`,
      className: "system"
    }));

    /* original paragraph + score */
    r.chunks.forEach(c => {
      const entry = document.createElement("div");
      entry.className = "entry";

      const head = document.createElement("div");
      head.className = "entry-head";
      const cat  = c.category || "None";
      const prev = c.text.substring(0, 80);
      const sc   = c.score !== undefined ? ` (score: ${c.score})` : "";
      head.innerHTML = `• [${cat}] ${prev}${sc} … <i>(click to expand)</i>`;

      const full = document.createElement("div");
      full.className  = "entry-full";
      full.innerHTML  = highlightKeyword(c.text, txt);

      head.onclick = () => {
        full.style.display =
          full.style.display === "none" ? "block" : "none";
      };

      entry.appendChild(head);
      entry.appendChild(full);
      addNode(entry);
    });
    return; // End RAG
  }

  /* ======== Baseline mode ======== */
  const kw = r.parsed?.keyword ?? "None";
  addNode(Object.assign(document.createElement("div"), {
    textContent: `↪️ AI understood: keyword=${kw}`,
    className  : "system"
  }));

  if (r.results?.length) {
    r.results.forEach(n => {
      const entry = document.createElement("div");
      entry.className = "entry";

      const head = document.createElement("div");
      head.className  = "entry-head";
      const cat  = n.category || "None";
      const prev = n.text.substring(0, 40);
      head.textContent = `• [${cat}] ${prev} … (click to expand)`;

      const full = document.createElement("div");
      full.className  = "entry-full";
      full.innerHTML  = highlightKeyword(n.text, kw);

      head.onclick = () => {
        full.style.display =
          full.style.display === "none" ? "block" : "none";
      };

      entry.appendChild(head);
      entry.appendChild(full);
      addNode(entry);
    });
  } else {
    addNode(Object.assign(document.createElement("div"), {
      textContent: "⚠️ No news found",
      className  : "system"
    }));
  }
};
