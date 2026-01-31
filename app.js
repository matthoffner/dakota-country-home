/**
 * Dakota Country Home - ChatKit Booking
 * All on Vercel - frontend + Python agent
 */

async function initChatKit() {
  const container = document.getElementById('chat-container');
  const chatkit = document.createElement('openai-chatkit');

  chatkit.setAttribute('agent', '/api/chatkit');

  container.appendChild(chatkit);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
