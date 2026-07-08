document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const clearChatBtn = document.getElementById('clear-chat');
    const historyList = document.getElementById('history-list');

    let sessionQueries = [];

    // Add user message to the chat view
    function addUserMessage(messageText) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-msg';
        msgDiv.innerHTML = `
            <div class="avatar">
                <i class="fa-solid fa-user"></i>
            </div>
            <div class="text-wrapper">
                <p>${escapeHtml(messageText)}</p>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // Add agent message to the chat view
    function addAgentMessage(messageHtml) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent-msg';
        msgDiv.innerHTML = `
            <div class="avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="text-wrapper">
                ${messageHtml}
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // Add a temporary typing bubble to show agent is thinking
    function showTypingBubble() {
        const bubble = document.createElement('div');
        bubble.className = 'message agent-msg typing-temp';
        bubble.innerHTML = `
            <div class="avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="text-wrapper">
                <div class="typing-bubble">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(bubble);
        scrollToBottom();
        return bubble;
    }

    // Auto-scroll chat window to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Simple HTML escaping helper
    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // Simple markdown table parser to convert raw dataframe markdown into HTML tables
    function formatAgentResponse(text) {
        // First convert code blocks
        let html = text.replace(/```(markdown|json|text|sql)?([\s\S]*?)```/g, (_, lang, code) => {
            return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
        });

        // Parse markdown tables
        const lines = html.split('\n');
        let inTable = false;
        let tableHtml = '';
        let processedLines = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.startsWith('|') && line.endsWith('|')) {
                const cols = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
                
                // Skip separator rows like |---|---|
                if (line.includes('---') || line.includes('-:-')) {
                    continue;
                }
                
                if (!inTable) {
                    inTable = true;
                    tableHtml = '<table><thead><tr>';
                    cols.forEach(col => {
                        tableHtml += `<th>${col}</th>`;
                    });
                    tableHtml += '</tr></thead><tbody>';
                } else {
                    tableHtml += '<tr>';
                    cols.forEach(col => {
                        tableHtml += `<td>${col}</td>`;
                    });
                    tableHtml += '</tr>';
                }
            } else {
                if (inTable) {
                    inTable = false;
                    tableHtml += '</tbody></table>';
                    processedLines.push(tableHtml);
                }
                processedLines.push(line);
            }
        }
        
        if (inTable) {
            tableHtml += '</tbody></table>';
            processedLines.push(tableHtml);
        }

        // Simple formatting for bold, italic, line breaks
        let result = processedLines.join('\n')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        return result;
    }

    // Update query history sidebar list
    function updateHistoryUI(queryText) {
        // Check if query is already present in sessionQueries
        const index = sessionQueries.indexOf(queryText);
        if (index > -1) {
            sessionQueries.splice(index, 1); // Remove it to move it to top
        }
        sessionQueries.unshift(queryText); // Prepend to top
        
        if (sessionQueries.length > 8) {
            sessionQueries.pop(); // Keep only last 8 queries
        }
        
        renderHistory();
    }

    // Render session query history to sidebar
    function renderHistory() {
        if (!historyList) return;
        if (sessionQueries.length === 0) {
            historyList.innerHTML = `<div class="no-history">No queries run in this session</div>`;
            return;
        }

        historyList.innerHTML = '';
        sessionQueries.forEach(query => {
            const card = document.createElement('button');
            card.className = 'history-card';
            card.innerHTML = `
                <i class="fa-solid fa-clock-rotate-left history-icon"></i>
                <span class="history-text" title="${escapeHtml(query)}">${escapeHtml(query)}</span>
            `;
            card.addEventListener('click', () => {
                sendQuery(query);
            });
            historyList.appendChild(card);
        });
    }

    // Send query request to backend
    async function sendQuery(queryText) {
        addUserMessage(queryText);
        const typingBubble = showTypingBubble();
        updateHistoryUI(queryText);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: queryText })
            });

            if (!response.ok) {
                throw new Error('API request failed');
            }

            const data = await response.json();
            typingBubble.remove();
            
            // Format response and display
            const formattedResponse = formatAgentResponse(data.response);
            addAgentMessage(formattedResponse);

        } catch (error) {
            typingBubble.remove();
            addAgentMessage(`<p style="color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> I cannot retrieve this information because the data is not sufficient.</p>`);
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = chatInput.value.trim();
        if (query) {
            sendQuery(query);
            chatInput.value = '';
        }
    });

    // Clear chat display
    clearChatBtn.addEventListener('click', () => {
        sessionQueries = [];
        renderHistory();
        // Reset to system greeting
        chatMessages.innerHTML = `
            <div class="message system-msg">
                <div class="avatar">
                    <i class="fa-solid fa-robot"></i>
                </div>
                <div class="text-wrapper">
                    <h4>Agent Connected</h4>
                    <p>Hello! I am your AI Query Agent. I can query your SAP HANA database dynamically through the Cube semantic layer using natural language. Type a custom question below to get started.</p>
                </div>
            </div>
        `;
    });
});
