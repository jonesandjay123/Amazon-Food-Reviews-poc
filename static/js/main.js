const log   = document.getElementById("log");
const qEl   = document.getElementById("q");
const ragCB = document.getElementById("rag");
const sendB = document.getElementById("send");

// add node and scroll to bottom
function addNode(node){
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
}

// main flow
sendB.onclick = async () => {
  const txt = qEl.value.trim();
  if (!txt) return;
  qEl.value = "";

  addNode(Object.assign(document.createElement("div"), {
    textContent: "> " + txt, className: "user"
  }));

  const endpoint = ragCB.checked ? "/rag_query" : "/query";

  const r = await fetch(endpoint,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({query:txt})
  }).then(r=>r.json()).catch(e=>({error:e}));

  if (r.error){
    addNode(Object.assign(document.createElement("div"),{
      textContent:"❌ "+r.error,className:"system"})); return;
  }

  // ========== RAG return format ==========
  if (ragCB.checked){
    addNode(Object.assign(document.createElement("div"),{
      textContent:"📝 "+r.answer,className:"system"}));

    r.chunks.forEach(c=>{
      const head = document.createElement("div");
      head.className="entry-head";
      head.textContent=`• [${c.category}] ${c.text}`;
      addNode(head);
    });
    return; // 結束
  }

  // ========== Baseline return format ==========
  const kw = r.parsed?.keyword ?? "None";
  addNode(Object.assign(document.createElement("div"),{
    textContent:`↪️ AI understood: keyword=${kw}`,className:"system"}));

  if (r.results?.length){
    r.results.forEach(n=>{
      const entry=document.createElement("div");
      entry.className="entry";

      const head=document.createElement("div");
      head.className="entry-head";
      const cat=n.category||"None";
      // only show first 40 characters
      const preview=n.text.substring(0,40);
      head.textContent=`• [${cat}] ${preview} … (click to expand)`;

      const full=document.createElement("div");
      full.className="entry-full";
      full.textContent=n.text;

      head.onclick=()=>{full.style.display=
        full.style.display==="none"?"block":"none";};

      entry.appendChild(head);
      entry.appendChild(full);
      addNode(entry);
    });
  }else{
    addNode(Object.assign(document.createElement("div"),{
      textContent:"⚠️ No news found",className:"system"}));
  }
};
