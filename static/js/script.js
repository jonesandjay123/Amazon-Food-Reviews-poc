document.addEventListener("DOMContentLoaded", function () {
  const messageContainer = document.getElementById("chat-messages");
  const queryForm = document.getElementById("query-form");
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");

  // 提交表單處理
  queryForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const userQuery = userInput.value.trim();
    if (!userQuery) return;

    // 清空輸入框
    userInput.value = "";

    // 添加用戶消息到聊天界面
    addMessage("user", userQuery);

    // 顯示加載指示器
    const loadingElement = addLoadingIndicator();

    try {
      // 發送請求到 /api/query 端點
      const queryResponse = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userQuery }),
      });

      const queryData = await queryResponse.json();

      // 移除加載指示器
      messageContainer.removeChild(loadingElement);

      // 顯示結果
      if (queryData.error) {
        // 查詢失敗
        addMessage("system", `抱歉，查詢失敗：${queryData.error}`);
      } else if (queryData.results && queryData.results.length > 0) {
        // 顯示查詢結果
        const formattedResults = formatMovieResults(queryData);
        addMessage("system", formattedResults);
      } else {
        // 沒有結果
        addMessage("system", "抱歉，我找不到相關電影信息。");
      }
    } catch (error) {
      console.error("Error:", error);
      messageContainer.removeChild(loadingElement);
      addMessage("system", "抱歉，出現了網絡錯誤，請稍後再試。");
    }
  });

  // 添加消息到聊天界面
  function addMessage(type, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = type === "user" ? "user-message" : "system-message";

    if (type === "user") {
      messageDiv.innerHTML = `<p>${escapeHTML(content)}</p>`;
    } else {
      // 系統消息可能包含格式化的內容
      messageDiv.innerHTML = content;
    }

    messageContainer.appendChild(messageDiv);

    // 滾動到底部
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  // 添加加載指示器
  function addLoadingIndicator() {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "loading";
    loadingDiv.innerHTML = "<span></span><span></span><span></span>";
    messageContainer.appendChild(loadingDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
    return loadingDiv;
  }

  // 格式化電影結果
  function formatMovieResults(data) {
    let html = `<p>查詢「${escapeHTML(data.query)}」的結果：</p>`;

    // 如果有解釋的查詢參數，顯示它
    if (data.interpreted_as) {
      html += "<p><small>我理解您在查詢：";
      const params = [];
      if (data.interpreted_as.director)
        params.push(`導演「${data.interpreted_as.director}」的電影`);
      if (data.interpreted_as.actor)
        params.push(`演員「${data.interpreted_as.actor}」的電影`);
      if (data.interpreted_as.year)
        params.push(`${data.interpreted_as.year} 年的電影`);
      if (data.interpreted_as.genre)
        params.push(`類型為「${data.interpreted_as.genre}」的電影`);
      if (data.interpreted_as.keyword)
        params.push(`包含「${data.interpreted_as.keyword}」的電影`);
      html += params.join("，") || "所有電影";
      html += "</small></p>";
    }

    html += `<p>找到 ${data.results_count} 部相關電影：</p><ol>`;

    data.results.forEach((movie) => {
      html += "<li>";

      // 標題和年份
      if (movie.title) {
        html += `<strong>${escapeHTML(movie.title)}</strong>`;
        if (movie.release_date) {
          const year = movie.release_date.split("-")[0];
          html += ` (${year})`;
        }
      }

      // 評分
      if (movie.vote_average) {
        html += ` - 評分: ${movie.vote_average}`;
      }

      // 類型
      if (movie.genres && movie.genres.length > 0) {
        html += `<br>類型: ${escapeHTML(movie.genres.join(", "))}`;
      }

      // 演員角色
      if (movie.character) {
        html += `<br>飾演: ${escapeHTML(movie.character)}`;
      }

      // 概述
      if (movie.overview) {
        // 只顯示概述的前100個字符
        const shortOverview =
          movie.overview.length > 100
            ? movie.overview.substring(0, 100) + "..."
            : movie.overview;
        html += `<br><small>${escapeHTML(shortOverview)}</small>`;
      }

      html += "</li>";
    });

    html += "</ol>";
    return html;
  }

  // 轉義 HTML 以防止 XSS 攻擊
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
});
