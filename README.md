# Dakota Country Home - Chat Booking

A chat-only booking website powered by OpenAI ChatKit and the Agents SDK. The entire booking flow happens inside a conversational interface - no traditional forms or pages.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Static Frontend (Vercel)                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ChatKit Web Component                   │    │
│  │         (Full viewport chat interface)               │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│  ┌──────────────────┐  ┌─────────────────────────────┐     │
│  │  /api/config     │  │  /api/stripe/webhook        │     │
│  │  (public config) │  │  (payment confirmation)     │     │
│  └──────────────────┘  └─────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Self-Hosted ChatKit Backend (Python)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              FastAPI + ChatKit SDK                   │    │
│  │                    /chatkit                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Booking Agent (Agents SDK)              │    │
│  │  • Parses natural language booking requests          │    │
│  │  • Checks availability via Airbnb iCal               │    │
│  │  • Calculates pricing quotes                         │    │
│  │  • Creates Stripe checkout sessions                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Agent Tools                       │    │
│  │  • get_availability (Airbnb iCal)                    │    │
│  │  • get_quote (pricing logic)                         │    │
│  │  • create_stripe_checkout (Stripe API)               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/matthoffner/dakota-country-home.git
cd dakota-country-home

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for Vercel functions)
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `CHATKIT_URL` - URL to your ChatKit backend (e.g., `http://localhost:8000/chatkit`)
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret

Optional:
- `AIRBNB_ICAL_URL` - Airbnb calendar URL for availability
- `NIGHTLY_RATE`, `CLEANING_FEE` - Pricing config

### 3. Run the Backend

```bash
# Start the Python backend
python -m uvicorn agent.main:app --reload --port 8000
```

### 4. Run the Frontend

In a separate terminal:

```bash
# Start the Vercel dev server
npx vercel dev --listen 3000
```

Visit `http://localhost:3000`

## Project Structure

```
├── index.html              # Entry point - loads ChatKit
├── style.css               # Minimal styling (chat fills viewport)
├── app.js                  # ChatKit initialization (vanilla JS)
├── favicon.svg             # Site icon
├── api/                    # Vercel serverless functions
│   ├── config.js           # Public config endpoint
│   └── stripe/
│       └── webhook.js      # Stripe webhook handler
├── agent/                  # Python booking agent
│   ├── main.py             # FastAPI server
│   ├── server.py           # ChatKit server implementation
│   ├── store.py            # Conversation storage
│   └── tools/              # Agent tools
│       ├── availability.py # Airbnb iCal integration
│       ├── pricing.py      # Quote calculator
│       └── stripe_checkout.py  # Stripe integration
├── requirements.txt        # Python dependencies
├── package.json            # Node dependencies
├── vercel.json             # Vercel configuration
└── .env.example            # Environment template
```

## Agent Tools

The booking agent has three tools:

### get_availability(start_date, end_date)
Checks if dates are available by parsing the Airbnb iCal feed.

```python
# Returns:
{
  "available": True,
  "blocked_reason": None,
  "checked_dates": {"start": "2025-03-15", "end": "2025-03-17"}
}
```

### get_quote(start_date, end_date, guests)
Calculates pricing for the stay.

```python
# Returns:
{
  "nights": 2,
  "nightly_rate": 250,
  "accommodation_total": 500,
  "cleaning_fee": 150,
  "total": 650,
  "total_cents": 65000,
  "breakdown": "$250 x 2 nights = $500\nCleaning fee = $150\nTotal = $650"
}
```

### create_stripe_checkout(amount_cents, customer_email, start_date, end_date, guests)
Creates a Stripe Embedded Checkout session.

```python
# Returns:
{
  "session_id": "cs_...",
  "client_secret": "cs_..._secret_...",
  "status": "created"
}
```

## Deployment

### Backend (e.g., Railway, Render, Fly.io)

```bash
# Build and deploy
docker build -t booking-agent .
# or use platform-specific deploy
```

Set environment variables in your platform.

### Frontend (Vercel)

```bash
vercel --prod
```

Set environment variables in Vercel dashboard:
- `CHATKIT_URL` - Your deployed backend URL
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY` (for webhook)
- `STRIPE_WEBHOOK_SECRET`

## Booking Flow

1. User lands on site, sees full-screen chat
2. User: "I'd like to book 2 nights in March for 6 people"
3. Agent asks for specific dates
4. Agent calls `get_availability` → shows availability
5. Agent calls `get_quote` → shows pricing breakdown
6. Agent asks for email
7. Agent calls `create_stripe_checkout`
8. Stripe Embedded Checkout appears in chat
9. User completes payment
10. Webhook confirms booking

## Customization

### Agent Personality
Edit `agent/server.py` → `BOOKING_INSTRUCTIONS`

### Pricing
Edit `agent/tools/pricing.py` or set env vars:
- `NIGHTLY_RATE`
- `CLEANING_FEE`
- `MAX_GUESTS`

### Styling
Edit `style.css` for custom colors/layout

### ChatKit Theming
See [ChatKit Themes](https://platform.openai.com/docs/guides/chatkit-themes)

## Resources

- [OpenAI ChatKit Docs](https://platform.openai.com/docs/guides/chatkit)
- [ChatKit Python SDK](https://openai.github.io/chatkit-python/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [Stripe Embedded Checkout](https://stripe.com/docs/checkout/embedded/quickstart)

## License

MIT
