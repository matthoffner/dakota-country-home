/**
 * Public config endpoint (not needed for managed ChatKit, but kept for Stripe)
 */

export default function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=300');

  return res.status(200).json({
    stripePublishableKey: process.env.STRIPE_PUBLISHABLE_KEY || null,
  });
}
