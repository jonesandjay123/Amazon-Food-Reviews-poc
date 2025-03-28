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
        const formattedResults = formatReviewResults(queryData);
        addMessage("system", formattedResults);
      } else {
        // 沒有結果
        addMessage("system", "抱歉，我找不到相關食品評論信息。");
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

  // 格式化評論結果
  function formatReviewResults(data) {
    let html = `<p>查詢「${escapeHTML(data.query)}」的結果：</p>`;

    // 如果有解釋的查詢參數，顯示它
    if (data.interpreted_as) {
      html += "<p><small>我理解您在查詢：";
      const params = [];
      if (data.interpreted_as.keyword)
        params.push(`關鍵詞「${data.interpreted_as.keyword}」的評論`);
      if (data.interpreted_as.min_score)
        params.push(`評分至少 ${data.interpreted_as.min_score} 星的評論`);
      if (data.interpreted_as.max_score)
        params.push(`評分至多 ${data.interpreted_as.max_score} 星的評論`);
      if (data.interpreted_as.product)
        params.push(`產品「${data.interpreted_as.product}」的評論`);
      if (data.interpreted_as.user)
        params.push(`用戶「${data.interpreted_as.user}」的評論`);
      if (data.interpreted_as.sentiment)
        params.push(`情感傾向為「${data.interpreted_as.sentiment}」的評論`);
      html += params.join("，") || "所有評論";
      html += "</small></p>";
    }

    html += `<p>找到 ${data.results_count} 條相關評論：</p><ol>`;

    data.results.forEach((review) => {
      html += "<li>";

      // 標題和星級
      if (review.Summary) {
        html += `<strong>${escapeHTML(review.Summary)}</strong>`;
      }
      
      // 評分
      if (review.Score) {
        const stars = '★'.repeat(review.Score) + '☆'.repeat(5 - review.Score);
        html += ` - 評分: ${stars} (${review.Score}/5)`;
      }

      // 產品ID
      if (review.ProductId) {
        html += `<br>產品ID: ${escapeHTML(review.ProductId)}`;
      }

      // 用戶名
      if (review.ProfileName) {
        html += `<br>用戶: ${escapeHTML(review.ProfileName)}`;
      }

      // 時間
      if (review.Time) {
        const date = new Date(review.Time * 1000);
        html += `<br>評論時間: ${date.toLocaleDateString()}`;
      }

      // 有用度
      if (review.HelpfulnessNumerator !== undefined && review.HelpfulnessDenominator !== undefined) {
        html += `<br>有用度: ${review.HelpfulnessNumerator}/${review.HelpfulnessDenominator}`;
      }

      // 評論文本
      if (review.Text) {
        // 只顯示評論的前150個字符
        const shortText =
          review.Text.length > 150
            ? review.Text.substring(0, 150) + "..."
            : review.Text;
        html += `<br><small>${escapeHTML(shortText)}</small>`;
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
