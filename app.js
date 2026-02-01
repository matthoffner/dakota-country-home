/**
 * Dakota Country Home - ChatKit Booking
 * All on Vercel - frontend + Python agent with Stripe embedded checkout
 *
 * Booking form is rendered inline via ChatKit widgets.
 * Stripe checkout uses client effects since it's a third-party embed.
 */

let stripeInstance = null;
let stripePublishableKey = null;
let chatkitElement = null;

async function getStripe() {
  if (!stripeInstance) {
    if (!stripePublishableKey) {
      const res = await fetch('/api/chatkit');
      const config = await res.json();
      stripePublishableKey = config.stripe_publishable_key;
    }
    stripeInstance = Stripe(stripePublishableKey);
  }
  return stripeInstance;
}

// Inject Stripe checkout below the ChatKit element
// (Stripe is a third-party embed that can't be rendered as a ChatKit widget)
function injectStripeWidget(content) {
  // Remove existing checkout if any
  const existing = document.getElementById('stripe-checkout-container');
  if (existing) existing.remove();

  // Find the chat container
  const chatContainer = document.getElementById('chat-container');
  if (!chatContainer) {
    console.warn('Could not find chat container');
    return null;
  }

  const wrapper = document.createElement('div');
  wrapper.id = 'stripe-checkout-container';
  wrapper.className = 'chatkit-inline-widget';
  wrapper.innerHTML = content;

  // Insert after the chatkit element
  if (chatkitElement && chatkitElement.nextSibling) {
    chatContainer.insertBefore(wrapper, chatkitElement.nextSibling);
  } else {
    chatContainer.appendChild(wrapper);
  }

  // Scroll to the widget
  wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });

  return wrapper;
}

async function handleStripeCheckout(data) {
  const { client_secret } = data;

  const checkoutHTML = `
    <div class="stripe-checkout-wrapper">
      <div id="checkout-element"></div>
    </div>
  `;

  const widget = injectStripeWidget(checkoutHTML);
  if (!widget) return;

  // Initialize Stripe embedded checkout
  const stripe = await getStripe();
  const checkout = await stripe.initEmbeddedCheckout({ clientSecret: client_secret });
  checkout.mount('#checkout-element');
}

async function initChatKit() {
  // Wait for ChatKit custom element to be defined
  await customElements.whenDefined('openai-chatkit');

  const container = document.getElementById('chat-container');
  const chatkit = document.createElement('openai-chatkit');
  chatkitElement = chatkit;

  chatkit.setOptions({
    api: {
      url: '/api/chatkit',
      domainKey: 'domain_pk_697e463b99c88193ab7306989319aad80d6a6d26fd06e5e1'
    },
    theme: 'light'
  });

  // Listen for client effects (Stripe checkout)
  chatkit.addEventListener('chatkit.effect', async (event) => {
    const { name, data } = event.detail;
    console.log('Received effect:', name, data);
    if (name === 'stripe_checkout') {
      await handleStripeCheckout(data);
    }
  });

  container.appendChild(chatkit);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
