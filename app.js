/**
 * Dakota Country Home - ChatKit Booking
 * Connects to self-hosted agent on Render
 */

const CHATKIT_URL = 'https://dakota-booking-agent.onrender.com/chatkit';

async function initChatKit() {
  const container = document.getElementById('chat-container');
  const chatkit = document.createElement('openai-chatkit');

  chatkit.setOptions({
    api: {
      url: CHATKIT_URL
    }
  });

  container.appendChild(chatkit);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
