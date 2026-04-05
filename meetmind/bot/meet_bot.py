"""
Google Meet Bot using Playwright (Python async).

Joins a Google Meet call as a virtual participant, captures audio, and
scrapes participant names. Uses playwright-stealth to avoid bot detection.

Requires:
- pip install playwright playwright-stealth
- playwright install chromium
- Google account credentials in .env
"""

import os
import random
import asyncio
import logging

logger = logging.getLogger(__name__)


class MeetBot:
    """
    Playwright-based bot that joins a Google Meet call.
    
    Workflow:
    1. Launch browser with stealth flags
    2. Log into Google account
    3. Navigate to Meet URL
    4. Join the meeting
    5. Start audio capture subprocess
    6. Periodically scrape participants
    """

    def __init__(self, meet_url: str, session_id: str, api_base_url: str = "http://localhost:8000"):
        self.meet_url = meet_url
        self.session_id = session_id
        self.api_base_url = api_base_url
        self.browser = None
        self.page = None
        self.audio_capture = None
        self._running = False

    async def start(self):
        """Launch browser, login, join meeting, start audio capture."""
        from playwright.async_api import async_playwright
        try:
            from playwright_stealth import stealth_async
        except ImportError:
            stealth_async = None
            logger.warning("playwright-stealth not installed, bot detection risk higher")

        pw = await async_playwright().start()

        self.browser = await pw.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--disable-web-security',
            ]
        )

        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            permissions=["microphone", "camera"],
        )

        self.page = await context.new_page()

        if stealth_async:
            await stealth_async(self.page)

        # Step 1: Google login
        await self._google_login()

        # Step 2: Navigate to Meet and join
        await self._join_meeting()

        # Step 3: Start audio capture
        self._running = True
        from bot.audio_capture import AudioCapture
        self.audio_capture = AudioCapture(self.session_id, self.api_base_url)
        asyncio.create_task(self.audio_capture.start())

        # Step 4: Periodically scrape participants
        asyncio.create_task(self._poll_participants())

        logger.info(f"Bot joined meeting: {self.meet_url}")

    async def _google_login(self):
        """Log into Google account using credentials from .env."""
        email = os.environ.get("GOOGLE_BOT_EMAIL")
        password = os.environ.get("GOOGLE_BOT_PASSWORD")

        if not email or not password:
            logger.warning("GOOGLE_BOT_EMAIL / GOOGLE_BOT_PASSWORD not set, skipping login")
            return

        try:
            await self.page.goto("https://accounts.google.com/signin")
            await self.page.wait_for_timeout(random.randint(1000, 2000))

            # Enter email
            await self.page.fill('input[type="email"]', email)
            await self.page.click('#identifierNext')
            await self.page.wait_for_timeout(random.randint(2000, 4000))

            # Enter password
            await self.page.fill('input[type="password"]', password)
            await self.page.click('#passwordNext')
            await self.page.wait_for_timeout(random.randint(3000, 5000))

            logger.info("Google login completed")
        except Exception as e:
            logger.error(f"Google login failed: {e}")

    async def _join_meeting(self):
        """Navigate to Meet URL and join the call."""
        await self.page.goto(self.meet_url)
        await self.page.wait_for_timeout(random.randint(2000, 4000))

        try:
            # Try to set display name
            name_input = await self.page.query_selector('input[aria-label="Your name"]')
            if name_input:
                await name_input.fill("")
                await name_input.type("MeetMind Bot", delay=50)
                await self.page.wait_for_timeout(random.randint(1000, 2000))

            # Turn off camera and microphone if buttons exist
            for label in ["Turn off camera", "Turn off microphone"]:
                btn = await self.page.query_selector(f'[aria-label="{label}"]')
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(500)

            # Click "Ask to join" or "Join now"
            join_btn = None
            for selector in [
                'button:has-text("Ask to join")',
                'button:has-text("Join now")',
                '[data-mdc-dialog-action="join"]',
            ]:
                join_btn = await self.page.query_selector(selector)
                if join_btn:
                    break

            if join_btn:
                await self.page.wait_for_timeout(random.randint(2000, 5000))
                await join_btn.click()
                logger.info("Clicked join button")
            else:
                logger.warning("Could not find join button")

            # Wait for meeting controls to appear (indicates we've joined)
            await self.page.wait_for_timeout(5000)

        except Exception as e:
            logger.error(f"Failed to join meeting: {e}")

    async def _poll_participants(self):
        """Periodically scrape participants list."""
        from bot.participant_scraper import get_participants
        import httpx

        while self._running:
            try:
                participants = await get_participants(self.page)
                if participants:
                    async with httpx.AsyncClient() as client:
                        for p in participants:
                            await client.post(
                                f"{self.api_base_url}/api/sessions/{self.session_id}/participants",
                                json=p,
                            )
            except Exception as e:
                logger.debug(f"Participant scrape cycle error: {e}")

            await asyncio.sleep(15)  # Poll every 15 seconds

    async def stop(self):
        """Gracefully stop the bot."""
        self._running = False
        if self.audio_capture:
            await self.audio_capture.stop()
        if self.browser:
            await self.browser.close()
        logger.info("Bot stopped")
