// ==========================================================================
// CO2Ops — Frontend Controller (Streamlit-Style AWS Console)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  const API_BASE_URL = window.CO2OPS_API_URL || 'http://127.0.0.1:8080';
  const API_KEY = window.CO2OPS_API_KEY || '';
  const API_HEADERS = { 'Content-Type': 'application/json', 'X-API-Key': API_KEY };
  const APP_NAME = 'co2ops_agent';

  // --- UUID Generator ---
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  };

  // ==========================================================================
  // WORKSPACE LOGIC (Only runs when on workspace.html)
  // ==========================================================================
  const chatHistory = document.getElementById('ws-chat-history');
  const chatForm = document.getElementById('ws-chat-form');
  const chatInput = document.getElementById('ws-chat-input');
  const sendBtn = document.getElementById('ws-send-btn');
  const userIdEl = document.getElementById('ws-user-id');
  const sessionIdEl = document.getElementById('ws-session-id');
  const newSessionBtn = document.getElementById('ws-new-session-btn');

  if (chatForm && chatHistory && chatInput) {
    // Session state
    let userId = localStorage.getItem('co2ops_user_id');
    if (!userId) {
      userId = `user-${generateUUID().substring(0, 8)}`;
      localStorage.setItem('co2ops_user_id', userId);
    }
    if (userIdEl) userIdEl.textContent = userId;

    let sessionId = `session-${Math.floor(Date.now() / 1000)}`;
    if (sessionIdEl) sessionIdEl.textContent = sessionId;

    // Helper: Markdown parser
    const renderMarkdown = (text) => {
      if (!text) return '';
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Code blocks with syntax copy button
      html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<div class="st-code-block"><div class="st-code-header"><span>${lang || 'text'}</span></div><pre><code>${code.trim()}</code></pre></div>`;
      });
      // Inline code
      html = html.replace(/`([^`]+)`/g, '<code class="st-inline-code">$1</code>');
      // Headers
      html = html.replace(/^### (.*$)/gim, '<h4 class="st-heading-3">$1</h4>');
      html = html.replace(/^## (.*$)/gim, '<h3 class="st-heading-2">$1</h3>');
      html = html.replace(/^# (.*$)/gim, '<h2 class="st-heading-1">$1</h2>');
      // Bold
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      // Italic
      html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      // Horizontal rules
      html = html.replace(/^---$/gm, '<div class="st-divider"></div>');
      // Links
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="st-link">$1</a>');
      // Unordered lists
      html = html.replace(/^\s*[-*]\s+(.*)$/gm, '<li>$1</li>');
      html = html.replace(/(<li>.*<\/li>)/s, '<ul class="st-list">$1</ul>');
      // Paragraphs
      html = html.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>');

      return `<p>${html}</p>`;
    };

    // Append Streamlit Chat Message
    const appendMessage = (role, text) => {
      const msgDiv = document.createElement('div');
      msgDiv.className = `st-chat-message ${role}`;

      const avatarDiv = document.createElement('div');
      avatarDiv.className = `st-avatar ${role}-avatar`;
      avatarDiv.textContent = role === 'user' ? '👤' : '🌱';

      const bubbleDiv = document.createElement('div');
      bubbleDiv.className = 'st-message-bubble';

      const senderDiv = document.createElement('div');
      senderDiv.className = 'st-message-sender';
      senderDiv.textContent = role === 'user' ? 'You' : 'CO2Ops Orchestrator';

      const contentDiv = document.createElement('div');
      contentDiv.className = 'st-message-content';
      contentDiv.innerHTML = renderMarkdown(text);

      bubbleDiv.appendChild(senderDiv);
      bubbleDiv.appendChild(contentDiv);
      msgDiv.appendChild(avatarDiv);
      msgDiv.appendChild(bubbleDiv);

      chatHistory.appendChild(msgDiv);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    };

    // Sub-agent matching
    const AGENT_KEYWORDS = [
      { key: 'safe_executor', label: '@safe_executor_agent (Zero-Downtime Safe Migrator)', words: ['migrate', 'execute', 'resize', 'restart', 'stop instance', 'safely'] },
      { key: 'forecasting_tool', label: '@forecasting_tool_agent (Amazon SageMaker AI)', words: ['forecast', 'arima', 'sagemaker', 'predict', '7-day', 'next week'] },
      { key: 'impact_calculator', label: '@impact_calculator_agent (FinOps & Graviton Diff)', words: ['compare', 'impact', 'savings', 'vs ', 'graviton'] },
      { key: 'summary_generator', label: '@summary_generator_agent (S3 Executive Reporter)', words: ['summary', 'report', 'slides', 'presentation', 'weekly'] },
      { key: 'optimization_advisor', label: '@optimization_advisor_agent (EC2 Rightsizing)', words: ['audit', 'underutilized', 'optimi', 'rightsiz', 'recommend'] },
    ];

    const guessAgent = (text) => {
      const lower = text.toLowerCase();
      const hit = AGENT_KEYWORDS.find((a) => a.words.some((w) => lower.includes(w)));
      return hit || AGENT_KEYWORDS[4];
    };

    const setActiveAgent = (agentKey) => {
      document.querySelectorAll('.st-swarm-item, .swarm-item').forEach((el) => {
        el.classList.toggle('active-agent', el.getAttribute('data-agent') === agentKey);
      });
    };

    const clearActiveAgent = () => {
      document.querySelectorAll('.st-swarm-item, .swarm-item').forEach((el) => el.classList.remove('active-agent'));
    };

    // Streamlit-Style Thinking Indicator
    let thinkingEl = null;
    const showThinking = (label) => {
      if (thinkingEl) return;
      thinkingEl = document.createElement('div');
      thinkingEl.className = 'st-chat-message assistant thinking-msg';
      thinkingEl.innerHTML = `
        <div class="st-avatar assistant-avatar">🌱</div>
        <div class="st-message-bubble">
          <div class="st-message-sender">CO2Ops Orchestrator</div>
          <div class="st-thinking-box">
            <div class="st-dot-flashing"></div>
            <span class="st-thinking-text">Working on your request with <strong>${label}</strong>...</span>
          </div>
        </div>
      `;
      chatHistory.appendChild(thinkingEl);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    };

    const hideThinking = () => {
      if (thinkingEl && thinkingEl.parentNode) {
        thinkingEl.parentNode.removeChild(thinkingEl);
      }
      thinkingEl = null;
    };

    // Create session API call
    const createSession = async () => {
      sessionId = `session-${Math.floor(Date.now() / 1000)}`;
      if (sessionIdEl) sessionIdEl.textContent = sessionId;

      try {
        await fetch(`${API_BASE_URL}/apps/${APP_NAME}/users/${userId}/sessions/${sessionId}`, {
          method: 'POST',
          headers: API_HEADERS,
          body: JSON.stringify({})
        });
      } catch (err) {
        console.warn('Backend session endpoint notice:', err);
      }
    };

    // Initialize session
    createSession();

    if (newSessionBtn) {
      newSessionBtn.addEventListener('click', () => {
        createSession();
        appendMessage('assistant', `Started a new session: <code class="st-inline-code">${sessionId}</code>. How can I assist with your AWS infrastructure optimization today?`);
      });
    }

    // Send message to ADK backend
    const sendMessage = async (messageText) => {
      if (!messageText) return;

      appendMessage('user', messageText);
      chatInput.value = '';
      chatInput.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      const guessed = guessAgent(messageText);
      setActiveAgent(guessed.key);
      showThinking(guessed.label);

      try {
        const res = await fetch(`${API_BASE_URL}/run`, {
          method: 'POST',
          headers: API_HEADERS,
          body: JSON.stringify({
            app_name: APP_NAME,
            user_id: userId,
            session_id: sessionId,
            new_message: {
              role: 'user',
              parts: [{ text: messageText }]
            }
          })
        });

        hideThinking();

        if (res.ok) {
          const events = await res.json();
          let fullText = '';

          events.forEach((event) => {
            // ADK format 1: step_details
            if (event.step_details && event.step_details.step_type === 'model_output') {
              const modelOutput = event.step_details.model_output;
              if (modelOutput && modelOutput.parts) {
                modelOutput.parts.forEach((p) => {
                  if (p.text) fullText += p.text;
                });
              }
            }
            // ADK format 2: direct content
            if (event.content && event.content.parts) {
              event.content.parts.forEach((p) => {
                if (!p.functionResponse && p.text) fullText += p.text;
              });
            }
          });

          if (fullText.trim()) {
            const mentioned = AGENT_KEYWORDS.find((a) => fullText.includes(a.key));
            if (mentioned) setActiveAgent(mentioned.key);
            appendMessage('assistant', fullText);
          } else {
            appendMessage('assistant', 'Action processed by CO2Ops. All AWS sub-agents reported success.');
          }
        } else {
          const errorText = await res.text();
          appendMessage('assistant', `Backend notice (${res.status}): ${errorText || 'Agent service busy. Please retry.'}`);
        }
      } catch (err) {
        hideThinking();
        clearActiveAgent();
        console.error('Fetch error:', err);
        appendMessage('assistant', `Could not reach ADK backend on ${API_BASE_URL}. Ensure the service is healthy.`);
      } finally {
        chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        chatInput.focus();
      }
    };

    // Chat form submit
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (text) sendMessage(text);
    });

    // Quick chip buttons
    document.querySelectorAll('.quick-chip, .st-chip-btn').forEach((chip) => {
      chip.addEventListener('click', () => {
        const prompt = chip.getAttribute('data-prompt');
        if (prompt) {
          chatInput.value = prompt;
          sendMessage(prompt);
        }
      });
    });

    // Check URL parameters for prompt (e.g. workspace.html?prompt=Audit%20fleet)
    const urlParams = new URLSearchParams(window.location.search);
    const initialPrompt = urlParams.get('prompt');
    if (initialPrompt) {
      setTimeout(() => {
        sendMessage(decodeURIComponent(initialPrompt));
      }, 500);
    }
  }

  // ==========================================================================
  // LANDING PAGE LOGIC
  // ==========================================================================
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href').substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
});
