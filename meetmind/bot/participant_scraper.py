"""
Participant Scraper — scrapes Google Meet participants panel.

Extracts display names and email guesses from the meeting participants list.
"""

import re
import logging

logger = logging.getLogger(__name__)


async def get_participants(page) -> list[dict]:
    """
    Scrapes the Google Meet participants panel to get display names.

    Returns:
    [
        {"display_name": "Aditya Kumar", "email_guess": "aditya.kumar@gmail.com"},
        {"display_name": "Priya Singh", "email_guess": None},
    ]

    Strategy:
    1. Click the "People" / participants icon in Meet
    2. Find all participant name elements
    3. If display name looks like an email address, extract it
    4. Otherwise return the name with email_guess=None
    """
    participants = []

    try:
        # Try to open participants panel
        people_btn = await page.query_selector(
            '[aria-label="Show everyone"], [aria-label="People"]'
        )
        if people_btn:
            await people_btn.click()
            await page.wait_for_timeout(1500)

        # Scrape participant names from the panel
        # Meet uses various selectors depending on version
        selectors = [
            '[data-participant-id] [data-self-name]',
            '.ZjFb7c',  # Common Meet participant name class
            '[data-participant-id]',
        ]

        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                for el in elements:
                    name = await el.inner_text()
                    name = name.strip()
                    if not name or name == "You":
                        continue

                    email_guess = None
                    # Check if the display name is an email
                    if re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', name):
                        email_guess = name

                    participants.append({
                        "display_name": name,
                        "email_guess": email_guess,
                    })
                break  # Found working selector

        # Close the panel
        if people_btn:
            close_btn = await page.query_selector('[aria-label="Close"]')
            if close_btn:
                await close_btn.click()

    except Exception as e:
        logger.debug(f"Participant scraping error: {e}")

    return participants
