import asyncio
import random
from pathlib import Path
from contextlib import AsyncExitStack
from playwright.async_api import async_playwright
from playwright_stealth import Stealth 
from dotenv import load_dotenv
import logging
from config import settings

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

class BrowserManager:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.exit_stack = AsyncExitStack()
        self.auth_path = Path("auth/gemini_state.json")
        self.auth_path.parent.mkdir(exist_ok=True)
        self.current_ua = None

    def _get_user_agent(self):
        if settings.USER_AGENT and settings.USER_AGENT.strip():
            logger.info("Using custom User-Agent from config")
            return settings.USER_AGENT.strip()
        
        ua = random.choice(UA_POOL)
        logger.info(f"Using random User-Agent: {ua[:30]}...")
        return ua

    async def init_browser(self, force_login=False):
        if self.page and not self.page.is_closed():
            return

        if self.browser:
            await self.close()

        self.current_ua = self._get_user_agent()

        stealth_ctx = Stealth().use_async(async_playwright())
        self.playwright = await self.exit_stack.enter_async_context(stealth_ctx)
        
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            f"--user-agent={self.current_ua}"
        ]
        
        if settings.HEADLESS:
             launch_args.append("--headless=new")

        self.browser = await self.playwright.chromium.launch(
            headless=settings.HEADLESS,
            args=launch_args
        )

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "user_agent": self.current_ua,
            "timezone_id": "America/New_York",
            "permissions": ["geolocation"]
        }

        if self.auth_path.exists() and not force_login:
            self.context = await self.browser.new_context(
                storage_state=str(self.auth_path),
                **context_options
            )
        else:
            self.context = await self.browser.new_context(
                **context_options
            )

        self.page = await self.context.new_page()
        
        try:
            is_webdriver = await self.page.evaluate("navigator.webdriver")
            logger.info(f"Stealth Status - navigator.webdriver: {is_webdriver}")
        except Exception:
            pass

        if not self.auth_path.exists() or force_login:
            await self._login_flow()
        else:
            await self._navigate_and_setup()
            
        logger.info("Gemini proxy ready")

    async def _navigate_and_setup(self):
        try:
            await self.page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
            await asyncio.sleep(4)

            selectors = [
                'button[data-test-id="temp-chat-button"]',
                'button[aria-label="Temporary chat"]',
                'button[mattooltip="Temporary chat"]',
                'div[mattooltip="Temporary chat"]' 
            ]

            found_btn = None
            for s in selectors:
                if await self.page.locator(s).count() > 0:
                    found_btn = self.page.locator(s).first
                    break
            
            if not found_btn:
                menu_btn = self.page.locator('button[aria-label="Expand menu"], button[aria-label="Main menu"]')
                if await menu_btn.count() > 0 and await menu_btn.is_visible():
                    await menu_btn.click()
                    await asyncio.sleep(1)

                for s in selectors:
                    if await self.page.locator(s).count() > 0:
                        found_btn = self.page.locator(s).first
                        break

            if found_btn:
                await found_btn.click(force=True)
                await asyncio.sleep(2)
                
        except Exception:
            pass

    async def _login_flow(self):
        await self.page.goto("https://accounts.google.com/signin")
        print(f"Current User-Agent: {self.current_ua}")
        print("Please login to your Google account and press Enter to continue...")
        await asyncio.to_thread(input)
        try:
            await self.page.goto("https://gemini.google.com/app")
        except Exception as e:
            if "interrupted by another navigation" in str(e):
                pass
            else:
                raise e
        await asyncio.sleep(5)
        await self.context.storage_state(path=str(self.auth_path))

    async def send_message(self, prompt: str):
        try:
            textbox = self.page.get_by_role("textbox")
            await textbox.click()
            await textbox.fill("") 
            for char in prompt:
                await self.page.keyboard.type(char)
                delay = random.uniform(0.01, 0.05)
                await asyncio.sleep(delay)

        except Exception:
            logger.warning("Error typing message, restarting browser...")
            await self.init_browser()
            textbox = self.page.get_by_role("textbox")
            await textbox.click()
            await textbox.fill("")
            for char in prompt:
                await self.page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.01, 0.05))

        hesitation_time = random.uniform(0.5, 1.5)
        await asyncio.sleep(hesitation_time)

        await self.page.get_by_role("button", name="Send").click()
        await asyncio.sleep(1.0)

        async for chunk in self._wait_for_response():
            yield chunk

        try:
            await self.context.storage_state(path=str(self.auth_path))
        except:
            pass

    async def _wait_for_response(self):
        last_text = ""
        no_change_count = 0
        
        while True:
            await asyncio.sleep(0.5)
            try:
                locator = self.page.locator('message-content, .message-content, .model-response-text, div[role="listitem"]').last
                
                if await locator.count() > 0:
                    text = await locator.text_content()
                    if text and len(text) > len(last_text):
                        chunk = text[len(last_text):]
                        yield chunk
                        last_text = text
                        no_change_count = 0
                    else:
                        no_change_count += 1
            except Exception:
                pass
            
            if no_change_count > 20 and len(last_text) > 0:
                break

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.exit_stack:
            await self.exit_stack.aclose()