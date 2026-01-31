/**
 * Dakota Country Home - ChatKit Booking Interface
 *
 * This initializes the OpenAI ChatKit widget for the booking experience.
 * Connects to a self-hosted Python backend running the booking agent.
 */

let CONFIG = {
  chatkitUrl: null,
  stripePublishableKey: null
};

/**
 * Fetch configuration from the server
 */
async function loadConfig() {
  try {
    const response = await fetch('/api/config');
    const data = await response.json();
    CONFIG = data;
    return data;
  } catch (error) {
    console.error('Failed to load config:', error);
    return CONFIG;
  }
}

/**
 * Handles custom widget actions from the agent.
 * This allows the agent to trigger client-side behaviors
 * like mounting Stripe Embedded Checkout.
 */
function handleAction(action) {
  console.log('Widget action:', action);

  // Handle Stripe checkout mounting
  if (action.type === 'mount_stripe_checkout' && action.clientSecret) {
    mountStripeCheckout(action.clientSecret, action.containerId);
  }
}

/**
 * Mounts Stripe Embedded Checkout into a widget container.
 */
async function mountStripeCheckout(clientSecret, containerId) {
  const container = containerId
    ? document.getElementById(containerId)
    : document.createElement('div');

  if (!container) {
    console.error('Stripe container not found:', containerId);
    return;
  }

  // Wait for Stripe.js to load
  if (typeof Stripe === 'undefined') {
    console.error('Stripe.js not loaded');
    return;
  }

  // Initialize Stripe
  const stripe = Stripe(CONFIG.stripePublishableKey);

  // Mount Embedded Checkout
  const checkout = await stripe.initEmbeddedCheckout({
    clientSecret: clientSecret,
  });

  checkout.mount(container);
}

/**
 * Initialize ChatKit when the script loads
 */
async function initChatKit() {
  const container = document.getElementById('chat-container');

  // Load configuration
  await loadConfig();

  if (!CONFIG.chatkitUrl) {
    container.innerHTML = `
      <div class="error-message">
        <h2>Configuration Required</h2>
        <p>Set CHATKIT_URL in your environment variables.</p>
      </div>
    `;
    return;
  }

  // Create the ChatKit web component
  const chatkit = document.createElement('openai-chatkit');

  // Configure for self-hosted backend
  chatkit.setOptions({
    api: {
      // Self-hosted mode: point to our Python backend
      url: CONFIG.chatkitUrl,
    },
    // Handle custom actions from widgets
    onAction: handleAction,
  });

  container.appendChild(chatkit);
}

// Wait for DOM and ChatKit script to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  // Small delay to ensure ChatKit script has registered the custom element
  setTimeout(initChatKit, 100);
}
