import pytest
import logging
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_logs.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlaywrightTestSuite:
    """Scalable Playwright test suite for regression testing"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.screenshots_dir = "screenshots"
        self.logs_dir = "logs"
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories for screenshots and logs"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def setup_browser(self, headless=True):
        """Setup browser instance"""
        try:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = self.context.new_page()
            logger.info("Browser setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            raise
    
    def teardown_browser(self):
        """Cleanup browser instance"""
        try:
            if self.browser:
                self.browser.close()
            logger.info("Browser teardown completed")
        except Exception as e:
            logger.error(f"Error during browser teardown: {str(e)}")
    
    def take_screenshot(self, name):
        """Take screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{self.screenshots_dir}/{name}_{timestamp}.png"
        try:
            self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return None
    
    def test_page_load(self, domain, expected_title=None, expected_element=None):
        """Test basic page load functionality"""
        try:
            logger.info(f"Testing page load for: {domain}")
            self.page.goto(domain, wait_until='networkidle')
            
            # Take screenshot of loaded page
            self.take_screenshot("page_load")
            
            # Verify title if provided
            if expected_title:
                actual_title = self.page.title()
                assert expected_title.lower() in actual_title.lower(), f"Expected title '{expected_title}' not found in '{actual_title}'"
                logger.info(f"Title verification passed: {actual_title}")
            
            # Verify expected element if provided
            if expected_element:
                element = self.page.wait_for_selector(expected_element, timeout=10000)
                assert element is not None, f"Expected element '{expected_element}' not found"
                logger.info(f"Element verification passed: {expected_element}")
            
            logger.info("Page load test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Page load test failed: {str(e)}")
            self.take_screenshot("page_load_error")
            raise
    
    def test_search_functionality(self, selector, value, result_selector):
        """Test search functionality"""
        try:
            logger.info(f"Testing search functionality with value: {value}")
            
            # Fill search input
            self.page.fill(selector, value)
            logger.info(f"Filled search input: {selector}")
            
            # Take screenshot before search
            self.take_screenshot("before_search")
            
            # Submit search
            self.page.press(selector, "Enter")
            
            # Wait for results
            self.page.wait_for_selector(result_selector, timeout=15000)
            
            # Take screenshot of results
            self.take_screenshot("search_results")
            
            # Verify results are present
            results = self.page.query_selector_all(result_selector)
            assert len(results) > 0, f"No search results found with selector: {result_selector}"
            
            logger.info(f"Search test completed successfully. Found {len(results)} results")
            return True
            
        except Exception as e:
            logger.error(f"Search functionality test failed: {str(e)}")
            self.take_screenshot("search_error")
            raise
    
    def test_click_functionality(self, selector, result_selector):
        """Test click/navigation functionality"""
        try:
            logger.info(f"Testing click functionality on: {selector}")
            
            # Take screenshot before click
            self.take_screenshot("before_click")
            
            # Click element
            self.page.click(selector)
            logger.info(f"Clicked element: {selector}")
            
            # Wait for result
            self.page.wait_for_selector(result_selector, timeout=15000)
            
            # Take screenshot after click
            self.take_screenshot("after_click")
            
            # Verify result element is present
            result_element = self.page.query_selector(result_selector)
            assert result_element is not None, f"Expected result element '{result_selector}' not found after click"
            
            logger.info("Click functionality test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Click functionality test failed: {str(e)}")
            self.take_screenshot("click_error")
            raise

# Test configuration based on user input
TEST_CONFIG = {
    "domain": "https://www.google.com",
    "functionalities": [
        {
            "name": "Page Load Verification",
            "type": "page_load",
            "expected_title": "Google",
            "expected_element": "input[name='q']"
        },
        {
            "name": "Search Functionality",
            "type": "search",
            "selector": "input[name='q']",
            "value": "Playwright Python",
            "result_selector": "h3"
        },
        {
            "name": "Navigation to Images",
            "type": "click",
            "selector": "a[href*='tbm=isch']",
            "result_selector": "img"
        }
    ]
}

@pytest.fixture(scope="session")
def test_suite():
    """Pytest fixture for test suite setup and teardown"""
    suite = PlaywrightTestSuite()
    suite.setup_browser(headless=True)
    yield suite
    suite.teardown_browser()

def test_page_load_verification(test_suite):
    """Test page load functionality"""
    config = TEST_CONFIG
    page_load_config = next((f for f in config["functionalities"] if f["type"] == "page_load"), None)
    
    if page_load_config:
        test_suite.test_page_load(
            domain=config["domain"],
            expected_title=page_load_config.get("expected_title"),
            expected_element=page_load_config.get("expected_element")
        )

def test_search_functionality(test_suite):
    """Test search functionality"""
    config = TEST_CONFIG
    search_config = next((f for f in config["functionalities"] if f["type"] == "search"), None)
    
    if search_config:
        test_suite.test_search_functionality(
            selector=search_config["selector"],
            value=search_config["value"],
            result_selector=search_config["result_selector"]
        )

def test_click_navigation(test_suite):
    """Test click/navigation functionality"""
    config = TEST_CONFIG
    click_config = next((f for f in config["functionalities"] if f["type"] == "click"), None)
    
    if click_config:
        test_suite.test_click_functionality(
            selector=click_config["selector"],
            result_selector=click_config["result_selector"]
        )

if __name__ == "__main__":
    """Run tests directly without pytest"""
    suite = PlaywrightTestSuite()
    try:
        suite.setup_browser(headless=True)
        
        # Run all configured tests
        config = TEST_CONFIG
        
        for functionality in config["functionalities"]:
            if functionality["type"] == "page_load":
                suite.test_page_load(
                    domain=config["domain"],
                    expected_title=functionality.get("expected_title"),
                    expected_element=functionality.get("expected_element")
                )
            elif functionality["type"] == "search":
                suite.test_search_functionality(
                    selector=functionality["selector"],
                    value=functionality["value"],
                    result_selector=functionality["result_selector"]
                )
            elif functionality["type"] == "click":
                suite.test_click_functionality(
                    selector=functionality["selector"],
                    result_selector=functionality["result_selector"]
                )
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise
    finally:
        suite.teardown_browser()