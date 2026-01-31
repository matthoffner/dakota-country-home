/**
 * Vercel Serverless Function: Public Configuration
 *
 * Returns public configuration values needed by the frontend.
 * Only exposes values that are safe to share with the client.
 */

export default function handler(req, res) {
  // Cache for 5 minutes
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');

  return res.status(200).json({
    // URL to the ChatKit backend (same domain on Vercel)
    chatkitUrl: process.env.CHATKIT_URL || '/api/chatkit',
    stripePublishableKey: process.env.STRIPE_PUBLISHABLE_KEY || null,
  });
}
