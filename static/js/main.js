const log   = document.getElementById("log");
const qEl   = document.getElementById("q");
const sendB = document.getElementById("send");

// helper: insert DOM node into log
function addNode(node){
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
}

// send query
sendB.onclick = async () => {
  const txt = qEl.value.trim();
  if (!txt) return;
  qEl.value = "";

  // user input
  addNode(Object.assign(document.createElement("div"), {
    textContent: "> " + txt, className: "user"
  }));

  // call backend
  const r = await fetch("/query", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({query:txt})
  }).then(r=>r.json()).catch(e=>({error:e}));

  if (r.error){
    addNode(Object.assign(document.createElement("div"), {
      textContent: "❌ " + r.error, className: "system"
    }));
    return;
  }

  // show LLM parsing result
  const kw = r.parsed?.keyword ?? "None";
  addNode(Object.assign(document.createElement("div"), {
    textContent: `↪️ AI understood: keyword=${kw}`, className: "system"
  }));

  // result list
  if (r.results?.length){
    r.results.forEach((n, idx)=>{
      const entry     = document.createElement("div");
      entry.className = "entry";

      const head = document.createElement("div");
      head.className  = "entry-head";
      const cat = n.category || "None";
      // limit the preview to 40 characters
      const preview = n.text.substring(0, 40);
      head.textContent = `• [${cat}] ${preview} … (click to expand)`;

      const full = document.createElement("div");
      full.className  = "entry-full";
      full.textContent= n.text;

      // toggle the full text
      head.onclick = ()=> {
        full.style.display = full.style.display === "none" ? "block" : "none";
      };

      entry.appendChild(head);
      entry.appendChild(full);
      addNode(entry);
    });
  }else{
    addNode(Object.assign(document.createElement("div"), {
      textContent:"⚠️ No news found", className:"system"
    }));
  }
};
