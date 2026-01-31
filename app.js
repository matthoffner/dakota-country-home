/**
 * Dakota Country Home - ChatKit Booking
 * All on Vercel - frontend + Python agent with Stripe embedded checkout
 */

let stripeInstance = null;
let stripePublishableKey = null;

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

async function handleStripeCheckout(data) {
  const { client_secret } = data;

  // Create checkout container
  const checkoutContainer = document.createElement('div');
  checkoutContainer.id = 'stripe-checkout-container';
  checkoutContainer.innerHTML = `
    <div style="padding: 24px; background: #FFFDF9; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; margin: 16px 0;">
      <div id="checkout-element"></div>
    </div>
  `;

  // Find the chat messages area and append
  const chatArea = document.querySelector('#chat-container');
  if (chatArea) {
    chatArea.appendChild(checkoutContainer);
  }

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

  chatkit.setOptions({
    api: {
      url: '/api/chatkit',
      domainKey: 'domain_pk_697e463b99c88193ab7306989319aad80d6a6d26fd06e5e1'
    },
    theme: 'light'
  });

  // Listen for client effects via DOM event
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
