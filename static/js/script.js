document.addEventListener("DOMContentLoaded", function () {
  const messageContainer = document.getElementById("chat-messages");
  const queryForm = document.getElementById("query-form");
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const clearButton = document.getElementById("clear-button");
  const langchainToggle = document.getElementById("langchain-toggle");
  const langchainStatus = document.getElementById("langchain-status");
  
  // Store the initial system message
  const initialSystemMessage = messageContainer.innerHTML;

  // Form submission handling
  queryForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const userQuery = userInput.value.trim();
    if (!userQuery) return;

    // Clear input field
    userInput.value = "";

    // Add user message to chat interface
    addMessage("user", userQuery);

    // Show loading indicator
    const loadingElement = addLoadingIndicator();

    try {
      // Get LangChain status
      const useLangChain = langchainToggle.checked;
      
      // Send request to /api/query endpoint
      const queryResponse = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: userQuery,
          force_langchain: useLangChain
        }),
      });

      const queryData = await queryResponse.json();

      // Remove loading indicator
      messageContainer.removeChild(loadingElement);

      // Display results
      if (queryData.error) {
        // Query failed
        addMessage("system", `Sorry, query failed: ${queryData.error}`);
      } else if (queryData.results && queryData.results.length > 0) {
        // Standard RAG results
        const formattedResults = formatReviewResults(queryData);
        addMessage("system", formattedResults);
      } else if (queryData.response) {
        // LangChain response
        const formattedResponse = formatLangChainResponse(queryData);
        addMessage("system", formattedResponse);
      } else {
        // No results
        addMessage("system", "Sorry, I couldn't find any relevant food review information.");
      }
    } catch (error) {
      console.error("Error:", error);
      messageContainer.removeChild(loadingElement);
      addMessage("system", "Sorry, a network error occurred. Please try again later.");
    }
  });

  // Add message to chat interface
  function addMessage(type, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = type === "user" ? "user-message" : "system-message";

    if (type === "user") {
      messageDiv.innerHTML = `<p>${escapeHTML(content)}</p>`;
    } else {
      // System messages may contain formatted content
      messageDiv.innerHTML = content;
    }

    messageContainer.appendChild(messageDiv);

    // Scroll to bottom
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  // Add loading indicator
  function addLoadingIndicator() {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "loading";
    loadingDiv.innerHTML = "<span></span><span></span><span></span>";
    messageContainer.appendChild(loadingDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
    return loadingDiv;
  }

  // Format LangChain response
  function formatLangChainResponse(data) {
    let html = `<div class="langchain-response">`;
    
    // Main response
    html += `<div class="response-content">${data.response}</div>`;
    
    // Show query method badge
    const queryMethod = data.query_metadata?.query_method || "langchain";
    html += `<div class="query-method-badge ${queryMethod}">${queryMethod.toUpperCase()}</div>`;
    
    // Show intermediate steps if available (collapsible)
    if (data.intermediate_steps && data.intermediate_steps.length > 0) {
      html += `<details class="intermediate-steps">
        <summary>Show reasoning steps (${data.intermediate_steps.length})</summary>
        <ol>`;
      
      data.intermediate_steps.forEach(step => {
        html += `<li>
          <strong>Tool:</strong> ${escapeHTML(step.tool)}<br>
          <strong>Input:</strong> <code>${escapeHTML(step.input)}</code><br>
          <strong>Result:</strong> <pre>${escapeHTML(step.result)}</pre>
        </li>`;
      });
      
      html += `</ol></details>`;
    }
    
    html += `</div>`;
    return html;
  }

  // Format review results
  function formatReviewResults(data) {
    let html = `<p>Results for query "${escapeHTML(data.query)}":</p>`;

    // Show query method badge
    const queryMethod = data.query_metadata?.query_method || "standard_rag";
    html += `<div class="query-method-badge ${queryMethod}">${queryMethod.toUpperCase()}</div>`;

    // If there are interpreted query parameters, display them
    if (data.interpreted_as) {
      html += "<p><small>I understand you're looking for: ";
      const params = [];
      if (data.interpreted_as.keyword)
        params.push(`Reviews with keyword "${data.interpreted_as.keyword}"`);
      if (data.interpreted_as.min_score)
        params.push(`Reviews with at least ${data.interpreted_as.min_score} stars`);
      if (data.interpreted_as.max_score)
        params.push(`Reviews with at most ${data.interpreted_as.max_score} stars`);
      if (data.interpreted_as.product)
        params.push(`Reviews for product "${data.interpreted_as.product}"`);
      if (data.interpreted_as.user)
        params.push(`Reviews by user "${data.interpreted_as.user}"`);
      if (data.interpreted_as.sentiment)
        params.push(`Reviews with sentiment "${data.interpreted_as.sentiment}"`);
      html += params.join(", ") || "All reviews";
      html += "</small></p>";
    }

    html += `<p>Found ${data.results_count} relevant reviews:</p><ol>`;

    data.results.forEach((review) => {
      html += "<li>";

      // Title and star rating
      if (review.Summary) {
        html += `<strong>${escapeHTML(review.Summary)}</strong>`;
      }
      
      // Rating
      if (review.Score) {
        const stars = '★'.repeat(review.Score) + '☆'.repeat(5 - review.Score);
        html += ` - Rating: ${stars} (${review.Score}/5)`;
      }

      // Product ID
      if (review.ProductId) {
        html += `<br>Product ID: ${escapeHTML(review.ProductId)}`;
      }

      // User name
      if (review.ProfileName) {
        html += `<br>User: ${escapeHTML(review.ProfileName)}`;
      }

      // Time
      if (review.Time) {
        const date = new Date(review.Time * 1000);
        html += `<br>Review date: ${date.toLocaleDateString()}`;
      }

      // Helpfulness
      if (review.HelpfulnessNumerator !== undefined && review.HelpfulnessDenominator !== undefined) {
        html += `<br>Helpfulness: ${review.HelpfulnessNumerator}/${review.HelpfulnessDenominator}`;
      }

      // Review text
      if (review.Text) {
        // Only show the first 150 characters of the review
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

  // Escape HTML to prevent XSS attacks
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
  
  // LangChain toggle event handler
  langchainToggle.addEventListener("change", async function() {
    const isEnabled = langchainToggle.checked;
    langchainStatus.textContent = `LangChain: ${isEnabled ? 'ON' : 'OFF'}`;
    
    try {
      // Call API to toggle LangChain mode
      const response = await fetch("/api/toggle_langchain", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enable_langchain: isEnabled }),
      });
      
      const data = await response.json();
      console.log("LangChain toggle response:", data);
      
      // Add system message about the change
      const message = isEnabled 
        ? "LangChain Agent enabled. Try asking more complex questions!"
        : "LangChain Agent disabled. Using standard RAG approach.";
      
      addMessage("system", `<p>${message}</p>`);
    } catch (error) {
      console.error("Error toggling LangChain:", error);
      addMessage("system", "Sorry, there was an error toggling LangChain mode.");
      // Revert toggle state on error
      langchainToggle.checked = !isEnabled;
      langchainStatus.textContent = `LangChain: ${!isEnabled ? 'ON' : 'OFF'}`;
    }
  });

  // Clear button event listener
  clearButton.addEventListener("click", function() {
    // Clear the message container, but keep the initial system message
    messageContainer.innerHTML = initialSystemMessage;
  });
});
