/**
 * Vercel Serverless Function: Create ChatKit Session
 *
 * Exchanges a workflow ID for a ChatKit client secret.
 * This keeps the OpenAI API key secure on the server.
 */

export default async function handler(req, res) {
  // Only accept POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    console.error('OPENAI_API_KEY not configured');
    return res.status(500).json({ error: 'Server not configured' });
  }

  const workflowId = process.env.CHATKIT_WORKFLOW_ID;
  if (!workflowId) {
    console.error('CHATKIT_WORKFLOW_ID not configured');
    return res.status(500).json({ error: 'Workflow not configured' });
  }

  // Get or create user ID from cookie
  let userId = req.cookies?.chatkit_session_id;
  if (!userId) {
    userId = crypto.randomUUID();
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chatkit/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        workflow: { id: workflowId },
        user: userId,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('OpenAI API error:', data);
      return res.status(response.status).json({
        error: data.error?.message || 'Failed to create session'
      });
    }

    // Set session cookie
    res.setHeader('Set-Cookie',
      `chatkit_session_id=${userId}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${60 * 60 * 24 * 30}`
    );

    return res.status(200).json({
      client_secret: data.client_secret,
    });

  } catch (error) {
    console.error('Session creation failed:', error);
    return res.status(500).json({ error: 'Failed to create session' });
  }
}
