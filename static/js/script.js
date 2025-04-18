document.addEventListener("DOMContentLoaded", function () {
  const messageContainer = document.getElementById("chat-messages");
  const queryForm = document.getElementById("query-form");
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const clearButton = document.getElementById("clear-button");
  
  // 儲存初始系統訊息
  const initialSystemMessage = messageContainer.innerHTML;

  // 表單提交處理
  queryForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const userQuery = userInput.value.trim();
    if (!userQuery) return;

    // 清除輸入欄位
    userInput.value = "";

    // 在聊天介面中新增使用者訊息
    addMessage("user", userQuery);

    // 顯示載入指示器
    const loadingElement = addLoadingIndicator();

    try {
      // 傳送請求到 /api/query 端點
      const queryResponse = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: userQuery
        }),
      });

      const queryData = await queryResponse.json();

      // 移除載入指示器
      messageContainer.removeChild(loadingElement);

      // 顯示結果
      if (queryData.error) {
        // 查詢失敗
        addMessage("system", `抱歉，查詢失敗：${queryData.error}`);
      } else if (queryData.results && queryData.results.length > 0) {
        // 格式化結果
        const formattedResults = formatNewsResults(queryData);
        addMessage("system", formattedResults);
      } else {
        // 沒有結果
        addMessage("system", "抱歉，我找不到任何相關的新聞文章。");
      }
    } catch (error) {
      console.error("錯誤：", error);
      messageContainer.removeChild(loadingElement);
      addMessage("system", "抱歉，發生網路錯誤。請稍後再試。");
    }
  });

  // 在聊天介面中新增訊息
  function addMessage(type, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = type === "user" ? "user-message" : "system-message";

    if (type === "user") {
      messageDiv.innerHTML = `<p>${escapeHTML(content)}</p>`;
    } else {
      // 系統訊息可能包含格式化內容
      messageDiv.innerHTML = content;
    }

    messageContainer.appendChild(messageDiv);

    // 捲動到底部
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  // 新增載入指示器
  function addLoadingIndicator() {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "loading";
    loadingDiv.innerHTML = "<span></span><span></span><span></span>";
    messageContainer.appendChild(loadingDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
    return loadingDiv;
  }

  // 格式化新聞結果
  function formatNewsResults(data) {
    let html = `<p>查詢「${escapeHTML(data.query)}」的結果：</p>`;

    // 如果有解析的查詢參數，顯示它們
    if (data.parsed) {
      html += "<p><small>我理解您正在查詢：";
      const params = [];
      if (data.parsed.category)
        params.push(`類別為「${data.parsed.category}」的新聞`);
      if (data.parsed.keyword)
        params.push(`包含關鍵字「${data.parsed.keyword}」的文章`);
      html += params.join("，") || "所有新聞";
      html += "</small></p>";
    }

    html += `<p>找到 ${data.results.length} 則相關新聞：</p><ol>`;

    data.results.forEach((news) => {
      html += "<li>";

      // 標題
      if (news.title) {
        html += `<strong>${escapeHTML(news.title)}</strong>`;
      }
      
      // 類別
      if (news.category) {
        html += `<br>類別：<span class="category-badge ${news.category.toLowerCase()}">${news.category}</span>`;
      }

      // ID
      if (news.id) {
        html += `<br>文章 ID：${news.id}`;
      }

      // 文章內容
      if (news.text) {
        // 只顯示前 150 個字元的內容
        const shortText =
          news.text.length > 150
            ? news.text.substring(0, 150) + "..."
            : news.text;
        html += `<br><small>${escapeHTML(shortText)}</small>`;
      }

      html += "</li>";
    });

    html += "</ol>";
    return html;
  }

  // 跳脫 HTML 以防止 XSS 攻擊
  function escapeHTML(str) {
    if (!str) return "";
    return str
      .toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  // 清除按鈕事件處理
  clearButton.addEventListener("click", function () {
    // 保留初始系統訊息，清除其他所有訊息
    messageContainer.innerHTML = initialSystemMessage;
  });
});
