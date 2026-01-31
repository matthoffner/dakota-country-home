/**
 * Dakota Country Home - ChatKit Booking Interface
 *
 * Connects to OpenAI's managed ChatKit (Agent Builder).
 * The agent and tools are configured in OpenAI's platform.
 */

/**
 * Fetches a client secret from our backend.
 * ChatKit calls this to create/refresh sessions.
 */
async function getClientSecret(currentSecret) {
  if (currentSecret) {
    return currentSecret;
  }

  const response = await fetch('/api/create-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include'
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to create session');
  }

  return data.client_secret;
}

/**
 * Initialize ChatKit
 */
async function initChatKit() {
  const container = document.getElementById('chat-container');

  // Create the ChatKit web component
  const chatkit = document.createElement('openai-chatkit');

  // Configure for OpenAI-managed backend
  chatkit.setOptions({
    api: {
      getClientSecret: getClientSecret
    }
  });

  container.appendChild(chatkit);
}

// Wait for DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
