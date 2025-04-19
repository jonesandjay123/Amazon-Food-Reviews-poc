// static/js/main.js
document.getElementById("send").onclick = async () => {
  const qEl = document.getElementById("q");
  const log = document.getElementById("log");
  const txt = qEl.value.trim();
  if (!txt) return;
  qEl.value = "";

  log.textContent += `\n> ${txt}`;

  const r = await fetch("/query", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({query: txt})
  }).then(r => r.json()).catch(e => ({error: e}));

  if (r.error) {
    log.textContent += `\n❌ ${r.error}`;
    return;
  }

  // show parsed result
  if (r.parsed) {
    const parsedCat = r.parsed.category || "None";
    const parsedKw  = r.parsed.keyword  || "None";
    log.textContent += `\n↪️ AI understood: category=${parsedCat}, keyword=${parsedKw}`;
  }

  // show query results
  if (r.results?.length) {
    r.results.forEach(n => {
      const cat = n.category || "None";
      const preview = n.text?.substring(0, 60) || "(No content)";
      log.textContent += `\n• [${cat}] ${preview}`;
    });
  } else {
    log.textContent += `\n⚠️ No news found`;
  }

  log.scrollTop = log.scrollHeight;
};
