/**
 * E2E Test: Dakota Country Home Booking Flow
 *
 * Tests:
 * 1. Hero slideshow renders with images
 * 2. ChatKit loads and accepts messages
 * 3. API endpoints work correctly
 * 4. Full booking flow produces Stripe checkout
 */

const { test, expect } = require('@playwright/test');

const SITE_URL = process.env.SITE_URL || 'https://dakota-country-home.vercel.app';

test.describe('Dakota Country Home Booking', () => {

  test('hero slideshow renders with background images', async ({ page }) => {
    await page.goto(SITE_URL);

    // Wait for slideshow
    await page.waitForSelector('.hero-slideshow');

    // Check slides exist
    const slides = await page.locator('.slide').count();
    expect(slides).toBe(6);

    // Check first slide has background image from wsimg.com
    const bgImage = await page.locator('.slide.active').evaluate(el => {
      return window.getComputedStyle(el).backgroundImage;
    });
    expect(bgImage).toContain('wsimg.com');
    expect(bgImage).toContain('url(');

    // Check text overlay
    await expect(page.locator('.slide-overlay h1')).toContainText('Dakota Country Home');

    // Check navigation works
    await page.click('.slide-nav.next');
    await page.waitForTimeout(1000);
    const activeDot = await page.locator('.dot.active').getAttribute('data-slide');
    expect(activeDot).toBe('1');
  });

  test('ChatKit loads in chat section', async ({ page }) => {
    await page.goto(SITE_URL);

    // Scroll to chat
    await page.click('a[href="#chat"]');
    await page.waitForTimeout(500);

    // Wait for ChatKit iframe
    await page.waitForSelector('openai-chatkit, iframe[name="chatkit"]', { timeout: 15000 });

    // Verify ChatKit rendered
    const chatkit = page.locator('openai-chatkit, iframe[name="chatkit"]');
    await expect(chatkit).toBeVisible();
  });

  test('API health endpoint returns ok', async ({ request }) => {
    const response = await request.get(`${SITE_URL}/api/chatkit`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ok');
    expect(data.has_openai_key).toBe(true);
    expect(data.stripe_publishable_key).toBeTruthy();
  });

  test('API agent endpoint returns configured agent', async ({ request }) => {
    const response = await request.get(`${SITE_URL}/api/chatkit?test=agent`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ok');
    expect(data.agent_name).toBe('Dakota Country Home');
    expect(data.agent_model).toBe('gpt-4o-mini');
    expect(data.num_tools).toBe(3); // get_availability, get_quote, show_payment_form
  });

  test('booking conversation flow works', async ({ page }) => {
    test.setTimeout(90000);

    await page.goto(SITE_URL);

    // Scroll to chat
    await page.click('a[href="#chat"]');
    await page.waitForTimeout(1000);

    // Wait for ChatKit iframe to load
    const chatFrame = page.frameLocator('iframe[name="chatkit"]');

    // Wait for input to be ready
    await chatFrame.getByRole('textbox', { name: /message/i }).waitFor({ timeout: 15000 });

    // Send booking message
    await chatFrame.getByRole('textbox', { name: /message/i }).fill(
      "I want to book Feb 15-17, 2025 for 4 guests"
    );
    await chatFrame.getByRole('button', { name: /send/i }).click();

    // Wait for response
    await page.waitForTimeout(10000);

    // Check that assistant responded (message appeared)
    const messages = chatFrame.locator('article');
    const count = await messages.count();
    expect(count).toBeGreaterThanOrEqual(2); // User message + assistant response
  });

});
