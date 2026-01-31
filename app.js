/**
 * Dakota Country Home - ChatKit Booking
 * All on Vercel - frontend + Python agent with Stripe embedded checkout
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

function handleBookingForm(data) {
  const { min_date } = data;

  // Remove existing form if any
  const existing = document.getElementById('booking-form-container');
  if (existing) existing.remove();

  // Create booking form container
  const formContainer = document.createElement('div');
  formContainer.id = 'booking-form-container';
  formContainer.innerHTML = `
    <div class="booking-form">
      <h3>Book Your Stay</h3>
      <div class="form-row">
        <div class="form-group">
          <label for="checkin">Check-in</label>
          <input type="date" id="checkin" name="checkin" min="${min_date}" required>
        </div>
        <div class="form-group">
          <label for="checkout">Check-out</label>
          <input type="date" id="checkout" name="checkout" min="${min_date}" required>
        </div>
      </div>
      <div class="form-group">
        <label for="guests">Number of Guests</label>
        <select id="guests" name="guests" required>
          <option value="">Select guests</option>
          <option value="1">1 guest</option>
          <option value="2">2 guests</option>
          <option value="3">3 guests</option>
          <option value="4">4 guests</option>
          <option value="5">5 guests</option>
          <option value="6">6 guests</option>
          <option value="7">7 guests</option>
          <option value="8">8 guests</option>
          <option value="9">9 guests</option>
          <option value="10">10 guests</option>
        </select>
      </div>
      <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" placeholder="your@email.com" required>
      </div>
      <button type="button" id="check-availability-btn" class="submit-btn">Check Availability</button>
    </div>
  `;

  // Find the chat area and append
  const chatArea = document.querySelector('#chat-container');
  if (chatArea) {
    chatArea.appendChild(formContainer);
  }

  // Handle form submission
  document.getElementById('check-availability-btn').addEventListener('click', () => {
    const checkin = document.getElementById('checkin').value;
    const checkout = document.getElementById('checkout').value;
    const guests = document.getElementById('guests').value;
    const email = document.getElementById('email').value;

    if (!checkin || !checkout || !guests || !email) {
      alert('Please fill in all fields');
      return;
    }

    // Send message to chat with the booking details
    const message = `I want to book from ${checkin} to ${checkout} for ${guests} guest(s). My email is ${email}`;

    // Remove the form
    formContainer.remove();

    // Send the message to ChatKit
    if (chatkitElement && chatkitElement.sendMessage) {
      chatkitElement.sendMessage(message);
    } else {
      // Fallback: find input and submit
      const iframe = document.querySelector('iframe[name="chatkit"]');
      if (iframe && iframe.contentDocument) {
        const input = iframe.contentDocument.querySelector('textarea, input[type="text"]');
        if (input) {
          input.value = message;
          const form = input.closest('form');
          if (form) form.submit();
        }
      }
    }
  });

  // Update checkout min date when checkin changes
  document.getElementById('checkin').addEventListener('change', (e) => {
    const checkoutInput = document.getElementById('checkout');
    checkoutInput.min = e.target.value;
    if (checkoutInput.value && checkoutInput.value <= e.target.value) {
      checkoutInput.value = '';
    }
  });
}

async function handleStripeCheckout(data) {
  const { client_secret } = data;

  // Remove booking form if still present
  const form = document.getElementById('booking-form-container');
  if (form) form.remove();

  // Create checkout container
  const checkoutContainer = document.createElement('div');
  checkoutContainer.id = 'stripe-checkout-container';
  checkoutContainer.innerHTML = `
    <div>
      <div id="checkout-element"></div>
    </div>
  `;

  // Find the chat area and append
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
  chatkitElement = chatkit;

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
    } else if (name === 'booking_form') {
      handleBookingForm(data);
    }
  });

  container.appendChild(chatkit);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatKit);
} else {
  setTimeout(initChatKit, 100);
}
