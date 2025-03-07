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
      // 發送請求到 /query 端點
      const queryResponse = await fetch("/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userQuery }),
      });

      const queryData = await queryResponse.json();

      if (queryData.status === "success") {
        // 查詢成功，獲取結果
        const resultsResponse = await fetch("/results");
        const resultsData = await resultsResponse.json();

        // 移除加載指示器
        messageContainer.removeChild(loadingElement);

        // 顯示結果
        if (resultsData.results && resultsData.results.length > 0) {
          const formattedResults = formatResults(resultsData.results);
          addMessage("system", formattedResults);
        } else {
          addMessage("system", "抱歉，我找不到相關信息。");
        }
      } else {
        // 查詢失敗
        messageContainer.removeChild(loadingElement);
        addMessage(
          "system",
          `抱歉，查詢失敗：${queryData.error || "未知錯誤"}`
        );
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

  // 格式化結果
  function formatResults(results) {
    // 檢查結果是字符串數組還是對象數組
    if (typeof results[0] === "string") {
      // 字符串數組，直接顯示為列表
      return `<ol>${results
        .map((result) => `<li>${escapeHTML(result)}</li>`)
        .join("")}</ol>`;
    } else {
      // 對象數組，創建一個更詳細的列表
      return `<ol>${results
        .map(
          (place) => `
                <li>
                    <strong>${escapeHTML(place.name)}</strong> - 評分: ${
            place.rating || "N/A"
          }<br>
                    地址: ${escapeHTML(place.address || "N/A")}<br>
                    ${
                      place.website
                        ? `網站: <a href="${escapeHTML(
                            place.website
                          )}" target="_blank">${escapeHTML(
                            place.website
                          )}</a><br>`
                        : ""
                    }
                    ${
                      place.opening_hours
                        ? `營業時間: ${escapeHTML(place.opening_hours)}`
                        : ""
                    }
                </li>
            `
        )
        .join("")}</ol>`;
    }
  }

  // 轉義 HTML 以防止 XSS 攻擊
  function escapeHTML(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
