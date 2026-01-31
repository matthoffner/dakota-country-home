/**
 * Vercel Serverless Function: Stripe Webhook Handler
 *
 * Handles Stripe events, primarily checkout.session.completed
 * to confirm bookings after successful payment.
 */

import Stripe from 'stripe';

// Disable body parsing - Stripe needs raw body for signature verification
export const config = {
  api: {
    bodyParser: false,
  },
};

/**
 * Read raw body from request
 */
async function buffer(readable) {
  const chunks = [];
  for await (const chunk of readable) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!stripeSecretKey || !webhookSecret) {
    console.error('Stripe configuration missing');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  const stripe = new Stripe(stripeSecretKey);

  // Get raw body and signature
  const buf = await buffer(req);
  const signature = req.headers['stripe-signature'];

  let event;

  try {
    event = stripe.webhooks.constructEvent(buf, signature, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).json({ error: `Webhook Error: ${err.message}` });
  }

  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object;

      console.log('Checkout completed:', {
        sessionId: session.id,
        customerEmail: session.customer_email,
        amount: session.amount_total,
        metadata: session.metadata,
      });

      // Extract booking details from metadata
      const { start_date, end_date, guests } = session.metadata || {};

      if (start_date && end_date) {
        // Here you would:
        // 1. Store the confirmed booking
        // 2. Block the dates
        // 3. Send confirmation email

        console.log('Booking confirmed:', {
          startDate: start_date,
          endDate: end_date,
          guests,
          email: session.customer_email,
          paymentIntent: session.payment_intent,
        });

        // TODO: Integrate with your booking storage
        // await saveBooking({
        //   startDate: start_date,
        //   endDate: end_date,
        //   guests: parseInt(guests, 10),
        //   email: session.customer_email,
        //   stripeSessionId: session.id,
        //   paymentIntent: session.payment_intent,
        //   status: 'confirmed',
        // });

        // TODO: Send confirmation email
        // await sendConfirmationEmail(session.customer_email, {
        //   startDate: start_date,
        //   endDate: end_date,
        // });
      }

      break;
    }

    case 'checkout.session.expired': {
      const session = event.data.object;
      console.log('Checkout expired:', session.id);

      // Release any held dates
      // await releaseHold(session.metadata?.hold_id);
      break;
    }

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  // Return 200 to acknowledge receipt
  return res.status(200).json({ received: true });
}
