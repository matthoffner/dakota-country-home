/**
 * Dakota Country Home - ChatKit Booking
 * All on Vercel - frontend + Python agent
 */

async function initChatKit() {
  // Wait for ChatKit custom element to be defined
  await customElements.whenDefined('openai-chatkit');

  const container = document.getElementById('chat-container');
  const chatkit = document.createElement('openai-chatkit');

  chatkit.setOptions({
    api: {
      url: '/api/chatkit',
      domainKey: 'dakota-country-home.vercel.app'
    }
  });

  container.appendChild(chatkit);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
