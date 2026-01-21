# Version 2 - Enhanced XPath Recorder

from playwright.sync_api import sync_playwright
import json
from datetime import datetime

captured_xpaths = []

XPATH_JS = """
(function () {
    function countMatches(xpath) {
        try {
            const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            return result.snapshotLength;
        } catch (e) {
            return 0;
        }
    }
    
    function getAbsoluteXPath(element) {
        if (element === document.body) {
            return '/html/body';
        }
        
        let position = 1;
        let siblings = element.parentNode ? element.parentNode.childNodes : [];
        
        for (let sibling of siblings) {
            if (sibling === element) {
                const parentPath = element.parentNode ? getAbsoluteXPath(element.parentNode) : '';
                const tagName = element.tagName.toLowerCase();
                return parentPath + '/' + tagName + '[' + position + ']';
            }
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                position++;
            }
        }
        return '';
    }
    
    function getXPath(element) {
        const tag = element.tagName.toLowerCase();
        const text = element.textContent ? element.textContent.trim().slice(0, 30) : '';
        let xpath = '';
        
        // Try ID
        if (element.id) {
            xpath = '//*[@id="' + element.id + '"]';
            if (countMatches(xpath) === 1) return xpath;
        }
        
        // Try name
        if (element.name) {
            xpath = '//' + tag + '[@name="' + element.name + '"]';
            if (countMatches(xpath) === 1) return xpath;
        }
        
        // Try data-testid
        if (element.dataset && element.dataset.testid) {
            xpath = '//*[@data-testid="' + element.dataset.testid + '"]';
            if (countMatches(xpath) === 1) return xpath;
            
            // Try data-testid + text
            if (text) {
                xpath = '//*[@data-testid="' + element.dataset.testid + '" and contains(., "' + text + '")]';
                if (countMatches(xpath) === 1) return xpath;
            }
        }
        
        // Try placeholder
        if (element.placeholder) {
            xpath = '//input[@placeholder="' + element.placeholder + '"]';
            if (countMatches(xpath) === 1) return xpath;
        }
        
        // Try text alone
        if (text && text.length < 50) {
            xpath = '//' + tag + '[contains(., "' + text + '")]';
            if (countMatches(xpath) === 1) return xpath;
        }
        
        // No unique relative path found - use absolute
        return getAbsoluteXPath(element);
    }

    document.addEventListener('click', function(e) {
        const el = e.target;
        const xpath = getXPath(el);
        const label = el.id || el.name || el.placeholder || el.textContent.trim().slice(0, 30) || el.tagName.toLowerCase();
        
        window.reportXPath(label, xpath);
    }, true);
})();
"""


def handle_xpath(label, xpath):
    captured_xpaths.append({
        "label": label,
        "xpath": xpath
    })
    print(f">>> {label} -> {xpath}")

def main():
    url = input("Enter URL: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.expose_function("reportXPath", handle_xpath)
        page.goto(url)
        page.evaluate(XPATH_JS)

        print("\nClick elements to capture XPath. Press Enter to close.\n")
        input()
        browser.close()

    # save to file
        # save to file
    if captured_xpaths:
        filename = f"xpaths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(filename, 'w') as f:
            f.write(f'# XPaths captured from: {url}\n')
            f.write(f'# Captured at: {datetime.now().isoformat()}\n\n')
            f.write('XPATHS = {\n')
            for item in captured_xpaths:
                f.write(f'    "{item["label"]}": \'{item["xpath"]}\',\n')
            f.write('}\n')
        print(f"\nSaved {len(captured_xpaths)} XPaths to {filename}")

if __name__ == "__main__":
    main()