// rag-assistant.js

// RAG Tabs logic
const tabDocs = document.getElementById('tab-docs');
const tabTut = document.getElementById('tab-tut');
const docsContainer = document.getElementById('docs-chat-container');
const tutContainer = document.getElementById('tut-chat-container');

function activateTab(tabToActivate) {
  if (tabToActivate === 'docs') {
    tabDocs.classList.add('border-pink-500', 'font-semibold');
    tabDocs.classList.remove('border-transparent');
    tabTut.classList.remove('border-pink-500', 'font-semibold');
    tabTut.classList.add('border-transparent');
    docsContainer.classList.remove('hidden');
    tutContainer.classList.add('hidden');
  } else {
    tabTut.classList.add('border-pink-500', 'font-semibold');
    tabTut.classList.remove('border-transparent');
    tabDocs.classList.remove('border-pink-500', 'font-semibold');
    tabDocs.classList.add('border-transparent');
    tutContainer.classList.remove('hidden');
    docsContainer.classList.add('hidden');
  }
}

tabDocs.addEventListener('click', () => activateTab('docs'));
tabTut.addEventListener('click', () => activateTab('tut'));

// Helper to append messages to chat windows
function appendMessage(container, sender, text) {
  const div = document.createElement('div');
  div.className = `rag-message ${sender === 'user' ? 'text-pink-400 text-right' : 'text-blue-400 text-left'}`;
  if (sender === 'ai') {
    div.innerHTML = marked.parse(text);
  } else {
    div.textContent = text;
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Query backend RAG API
async function queryRagAPI(endpoint, question, history) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ question, history })
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data.answer;
  } catch (err) {
    return `Error: ${err.message}`;
  }
}

// Docs Assistant elements
const docsForm = document.getElementById('docs-chat-form');
const docsInput = document.getElementById('docs-chat-input');
const docsChat = document.getElementById('docs-chat');

// Tutorial Assistant elements
const tutForm = document.getElementById('tut-chat-form');
const tutInput = document.getElementById('tut-chat-input');
const tutChat = document.getElementById('tut-chat');


// Docs Assistant form handling
docsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = docsInput.value.trim();
  if (!question) return;

  appendMessage(docsChat, 'user', `You: ${question}`);
  docsInput.value = '';

  appendMessage(docsChat, 'ai', 'AI is thinking...');

  const history = getChatHistory(docsChat);
  const answer = await queryRagAPI('/chat/rag_docs', question, history);

  // Replace placeholder
  const thinkingMsg = [...docsChat.querySelectorAll('.rag-message')]
    .reverse()
    .find(msg => msg.textContent.includes('AI is thinking'));

  if (thinkingMsg) {
    thinkingMsg.textContent = 'AI response:';
    const answerDiv = document.createElement('div');
    answerDiv.className = 'rag-message text-blue-400 text-left';
    answerDiv.innerHTML = marked.parse(answer);
    docsChat.appendChild(answerDiv);
  } else {
    appendMessage(docsChat, 'ai', answer);
  }

  adjustChatHeight(docsChat);
});

// Tutorial Assistant form handling
tutForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = tutInput.value.trim();
  if (!question) return;

  appendMessage(tutChat, 'user', `You: ${question}`);
  tutInput.value = '';

  appendMessage(tutChat, 'ai', 'AI is thinking...');

  // 🧠 Extract chat history from previous messages
  const history = getChatHistory(tutChat);

  // 📡 Send current question + history
  const answer = await queryRagAPI('/chat/rag_tut', question, history);

  // Replace the "AI is thinking..." message with the real response
  const thinkingMsg = [...tutChat.querySelectorAll('.rag-message')]
    .reverse()
    .find(msg => msg.textContent.includes('AI is thinking'));

  if (thinkingMsg) {
    thinkingMsg.textContent = 'AI response:';
    const answerDiv = document.createElement('div');
    answerDiv.className = 'rag-message text-blue-400 text-left';
    answerDiv.innerHTML = marked.parse(answer);
    tutChat.appendChild(answerDiv);
  } else {
    appendMessage(tutChat, 'ai', answer);
  }

  adjustChatHeight(tutChat);
});




function adjustChatHeight(chatDiv) {
  const minHeight = 240; // px (15rem)
  const maxHeight = 480; // px

  // Reset height to auto to get scrollHeight
  chatDiv.style.height = 'auto';

  const contentHeight = chatDiv.scrollHeight;

  const newHeight = Math.min(Math.max(contentHeight, minHeight), maxHeight);

  chatDiv.style.height = newHeight + 'px';

  chatDiv.style.overflowY = contentHeight > maxHeight ? 'auto' : 'hidden';
}

document.addEventListener("DOMContentLoaded", () => {
  const toggleRagBtn = document.getElementById('toggle-rag-btn');
  const ragContainer = document.getElementById('rag-container');

  if (toggleRagBtn && ragContainer) {
    toggleRagBtn.addEventListener('click', () => {
      const isHidden = ragContainer.classList.contains('hidden');
      ragContainer.classList.toggle('hidden');
      toggleRagBtn.innerHTML = isHidden
        ? 'Close Assistant'
        : 'AI-powered<br>Docs & Tutorials';

      const scrollTarget = isHidden ? document.getElementById('rag-assistants') : null;
      if (scrollTarget) {
        scrollTarget.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }
});

function getChatHistory(container) {
  const messages = [...container.querySelectorAll('.rag-message')];
  const history = [];

  for (let i = 0; i < messages.length - 1; i++) {
    const userMsg = messages[i];
    const aiMsg = messages[i + 1];

    if (userMsg.classList.contains('text-pink-400') && aiMsg.classList.contains('text-blue-400')) {
      history.push({
        question: userMsg.textContent.replace(/^You:\s*/, ''),
        answer: aiMsg.innerText
      });
      i++; // skip next since it's paired
    }
  }

  return history;
}
