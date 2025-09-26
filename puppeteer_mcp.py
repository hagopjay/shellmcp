#!/usr/bin/env python3
"""
Browser Automation MCP Server - Control browsers via Playwright/Puppeteer
"""

import asyncio
import json
import base64
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from mcp.server import Server



class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: Dict[str, Page] = {}
        
    async def start_browser(self, headless: bool = True, browser_type: str = "chromium"):
        """Start browser instance"""
        self.playwright = await async_playwright().start()
        
        if browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(headless=headless)
        elif browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(headless=headless)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
            
        self.context = await self.browser.new_context()
        return f"Browser {browser_type} started (headless={headless})"
    
    async def new_page(self, page_id: str = "default") -> str:
        """Create new page"""
        if not self.context:
            raise Exception("Browser not started")
            
        page = await self.context.new_page()
        self.pages[page_id] = page
        return f"New page created with ID: {page_id}"
    
    async def navigate(self, url: str, page_id: str = "default") -> str:
        """Navigate to URL"""
        if page_id not in self.pages:
            await self.new_page(page_id)
            
        page = self.pages[page_id]
        await page.goto(url)
        title = await page.title()
        return f"Navigated to {url} - Title: {title}"
    
    async def click_element(self, selector: str, page_id: str = "default") -> str:
        """Click element by selector"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            await page.click(selector)
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Failed to click {selector}: {str(e)}"
    
    async def fill_input(self, selector: str, value: str, page_id: str = "default") -> str:
        """Fill input field"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            await page.fill(selector, value)
            return f"Filled {selector} with: {value}"
        except Exception as e:
            return f"Failed to fill {selector}: {str(e)}"
    
    async def extract_text(self, selector: str, page_id: str = "default") -> str:
        """Extract text from element"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            text = await page.text_content(selector)
            return text or "No text found"
        except Exception as e:
            return f"Failed to extract text from {selector}: {str(e)}"
    
    async def screenshot(self, page_id: str = "default") -> str:
        """Take screenshot"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            screenshot_bytes = await page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            return f"Screenshot taken (base64): {screenshot_b64[:100]}..."
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"
    
    async def execute_javascript(self, script: str, page_id: str = "default") -> str:
        """Execute JavaScript on page"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            result = await page.evaluate(script)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"JavaScript execution failed: {str(e)}"
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000, page_id: str = "default") -> str:
        """Wait for element to appear"""
        page = self.pages.get(page_id)
        if not page:
            return "Page not found"
            
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return f"Element {selector} appeared"
        except Exception as e:
            return f"Element {selector} did not appear: {str(e)}"

# Initialize browser manager
browser_manager = BrowserManager()

# MCP Server setup
server = Server("browser-automation-mcp")

@server.tool()
async def start_browser(headless: bool = True, browser_type: str = "chromium") -> str:
    """Start browser instance (chromium/firefox/webkit)"""
    result = await browser_manager.start_browser(headless, browser_type)
    return result

@server.tool()
async def navigate_to(url: str, page_id: str = "default") -> str:
    """Navigate to URL"""
    result = await browser_manager.navigate(url, page_id)
    return result

@server.tool()
async def click_element(selector: str, page_id: str = "default") -> str:
    """Click element by CSS selector"""
    result = await browser_manager.click_element(selector, page_id)
    return result

@server.tool()
async def fill_form_field(selector: str, value: str, page_id: str = "default") -> str:
    """Fill form input field"""
    result = await browser_manager.fill_input(selector, value, page_id)
    return result

@server.tool()
async def extract_text_content(selector: str, page_id: str = "default") -> str:
    """Extract text from element"""
    result = await browser_manager.extract_text(selector, page_id)
    return result

@server.tool()
async def take_screenshot(page_id: str = "default") -> str:
    """Take screenshot of current page"""
    result = await browser_manager.screenshot(page_id)
    return result

@server.tool()
async def run_javascript(script: str, page_id: str = "default") -> str:
    """Execute JavaScript code on page"""
    result = await browser_manager.execute_javascript(script, page_id)
    return result

@server.tool()
async def wait_for_element(selector: str, timeout: int = 5000, page_id: str = "default") -> str:
    """Wait for element to appear on page"""
    result = await browser_manager.wait_for_selector(selector, timeout, page_id)
    return result

# Advanced automation workflows
@server.tool()
async def automate_login(login_url: str, username_selector: str, password_selector: str, 
                        submit_selector: str, username: str, password: str, page_id: str = "default") -> str:
    """Automated login workflow"""
    results = []
    
    # Navigate to login page
    result = await browser_manager.navigate(login_url, page_id)
    results.append(f"Navigation: {result}")
    
    # Fill username
    result = await browser_manager.fill_input(username_selector, username, page_id)
    results.append(f"Username: {result}")
    
    # Fill password
    result = await browser_manager.fill_input(password_selector, password, page_id)
    results.append(f"Password: {result}")
    
    # Submit form
    result = await browser_manager.click_element(submit_selector, page_id)
    results.append(f"Submit: {result}")
    
    # Wait a moment for redirect
    await asyncio.sleep(2)
    
    return json.dumps(results, indent=2)

@server.tool()
async def scrape_table_data(table_selector: str, page_id: str = "default") -> str:
    """Scrape table data from page"""
    page = browser_manager.pages.get(page_id)
    if not page:
        return "Page not found"
    
    try:
        # JavaScript to extract table data
        script = f"""
        const table = document.querySelector('{table_selector}');
        if (!table) return 'Table not found';
        
        const rows = Array.from(table.querySelectorAll('tr'));
        const data = rows.map(row => 
            Array.from(row.querySelectorAll('th, td')).map(cell => cell.textContent.trim())
        );
        return data;
        """
        
        result = await browser_manager.execute_javascript(script, page_id)
        return result
    except Exception as e:
        return f"Failed to scrape table: {str(e)}"

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as streams:
        await server.run(*streams)


if __name__ == "__main__":
    asyncio.run(main())
