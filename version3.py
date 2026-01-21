# Version 3 - Feature-Rich XPath Recorder
# New features:
# - Highlight element on hover
# - Clean exit (no error spam)
# - Multiple output formats (.py, .json, .csv)
# - More attribute strategies (class, aria-label, role, type, href)
# - Duplicate prevention
# - Match count display

from playwright.sync_api import sync_playwright
import json
import csv
from datetime import datetime
import signal
import sys

captured_xpaths = {} # Dict with "xpath|action" as key

XPATH_JS = """
(function () {
    // Highlight styles
    const HIGHLIGHT_STYLE = '2px solid red';
    const HIGHLIGHT_BG = 'rgba(255, 0, 0, 0.1)';
    let lastHighlighted = null;
    let originalStyles = {};

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

        // 1. Try ID (highest priority)
        if (element.id) {
            xpath = '//*[@id="' + element.id + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'id' };
        }

        // 2. Try name attribute
        if (element.name) {
            xpath = '//' + tag + '[@name="' + element.name + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'name' };
        }

        // 3. Try data-testid
        if (element.dataset && element.dataset.testid) {
            xpath = '//*[@data-testid="' + element.dataset.testid + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'data-testid' };

            // Try data-testid + text
            if (text) {
                xpath = '//*[@data-testid="' + element.dataset.testid + '" and contains(., "' + text + '")]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'data-testid+text' };
            }
        }

        // 4. Try aria-label (accessibility attribute)
        const ariaLabel = element.getAttribute('aria-label');
        if (ariaLabel) {
            xpath = '//*[@aria-label="' + ariaLabel + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'aria-label' };
        }

        // 5. Try role attribute
        const role = element.getAttribute('role');
        if (role) {
            xpath = '//*[@role="' + role + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'role' };

            // Try role + text
            if (text) {
                xpath = '//*[@role="' + role + '" and contains(., "' + text + '")]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'role+text' };
            }
        }

        // 6. Try placeholder
        if (element.placeholder) {
            xpath = '//input[@placeholder="' + element.placeholder + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'placeholder' };
        }

        // 7. Try type attribute (for inputs/buttons)
        if (element.type && (tag === 'input' || tag === 'button')) {
            xpath = '//' + tag + '[@type="' + element.type + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'type' };

            // Try type + name or placeholder
            if (element.name) {
                xpath = '//' + tag + '[@type="' + element.type + '" and @name="' + element.name + '"]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'type+name' };
            }
        }

        // 8. Try href for links
        if (tag === 'a' && element.href) {
            const href = element.getAttribute('href');
            if (href && !href.startsWith('javascript:')) {
                xpath = '//a[@href="' + href + '"]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'href' };
            }
        }

        // 9. Try class (less reliable but sometimes useful)
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\\s+/);
            // Try first meaningful class (skip common utility classes)
            for (const cls of classes) {
                if (cls.length > 3 && !cls.match(/^(mt-|mb-|px-|py-|flex|grid|text-|bg-)/)) {
                    xpath = '//' + tag + '[contains(@class, "' + cls + '")]';
                    if (countMatches(xpath) === 1) return { xpath, strategy: 'class' };
                }
            }
        }

        // 10. Try text alone
        if (text && text.length < 50) {
            xpath = '//' + tag + '[contains(., "' + text + '")]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'text' };
        }

        // 11. No unique relative path found - use absolute
        return { xpath: getAbsoluteXPath(element), strategy: 'absolute' };
    }

    function highlightElement(el) {
        if (lastHighlighted && lastHighlighted !== el) {
            // Restore previous element
            lastHighlighted.style.outline = originalStyles.outline || '';
            lastHighlighted.style.backgroundColor = originalStyles.bg || '';
        }

        if (el) {
            // Save original styles
            originalStyles = {
                outline: el.style.outline,
                bg: el.style.backgroundColor
            };
            // Apply highlight
            el.style.outline = HIGHLIGHT_STYLE;
            el.style.backgroundColor = HIGHLIGHT_BG;
            lastHighlighted = el;
        }
    }

    // Hover highlight
    document.addEventListener('mouseover', function(e) {
        highlightElement(e.target);
    }, true);

    // Click capture
    document.addEventListener('click', function(e) {
        const el = e.target;
        const result = getXPath(el);
        const label = el.id || el.name || el.placeholder || el.textContent.trim().slice(0, 30) || el.tagName.toLowerCase();
        const matches = countMatches(result.xpath);

        window.reportXPath(label, result.xpath, result.strategy, matches, 'click', '');
    }, true);

    // Input capture
   document.addEventListener('change', function(e) {
    const el = e.target;
    const result = getXPath(el);
    const label = el.id || el.name || el.placeholder || el.tagName.toLowerCase();
    const matches = countMatches(result.xpath);
    const value = el.type === 'checkbox' ? el.checked : el.value;
    window.reportXPath(label, result.xpath, result.strategy, matches, 'change', value);
    }, true);

})();
"""


def handle_xpath(label, xpath, strategy, matches, action, values):
    """Handle captured XPath from browser"""
    # Duplicate prevention
    key = f"{xpath}|{action}"

    is_update = key in captured_xpaths
    
    #Always set/update
    captured_xpaths[key] = {
        "label": label,
        "xpath": xpath,
        "strategy": strategy,
        "matches": matches,
        "action": action,
        "values": values
    }

    if is_update:
        print(f"[UPDATE] {label}: {values}")
    else:
        status = "UNIQUE" if matches == 1 else f"{matches} matches"
        print(f"[{len(captured_xpaths)}] {label}")
        print(f"    XPath: {xpath}")
        print(f"    Action: {action} | Value: {values}")
        print(f"    Strategy: {strategy} | {status}")
        print()



def save_python(filename, url):
    """Save as Python file with XPATHS dict"""
    with open(filename, 'w') as f:
        f.write(f'# XPaths captured from: {url}\n')
        f.write(f'# Captured at: {datetime.now().isoformat()}\n')
        f.write(f'# Total elements: {len(captured_xpaths)}\n\n')
        f.write('XPATHS = {\n')
        for item in captured_xpaths.values():
            # Escape single quotes in xpath
            xpath_escaped = item["xpath"].replace("'", "\\'")
            f.write(f'    "{item["label"]}": \'{xpath_escaped}\',  # {item["strategy"]} | {item["action"]}: {item["values"]}\n')
        f.write('}\n')
    print(f"Saved to {filename}")


def save_json(filename, url):
    """Save as JSON file with full metadata"""
    data = {
        "url": url,
        "captured_at": datetime.now().isoformat(),
        "total_elements": len(captured_xpaths),
        "xpaths": list(captured_xpaths.values())
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {filename}")


def save_csv(filename, url):
    """Save as CSV file"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Label', 'XPath', 'Strategy', 'Matches', 'Action', 'Value'])
        for item in captured_xpaths.values():
            writer.writerow([item["label"], item["xpath"], item["strategy"], item["matches"], item["action"], item["values"]])
    print(f"Saved to {filename}")


def main():
    url = input("Enter URL: ")

    print("\nOutput format options:")
    print("  1. Python (.py) - XPATHS dictionary")
    print("  2. JSON (.json) - Full metadata")
    print("  3. CSV (.csv) - Spreadsheet format")
    print("  4. All formats")

    format_choice = input("Choose format (1-4) [default: 1]: ").strip() or "1"

    print("\n" + "="*50)
    print("INSTRUCTIONS:")
    print("- Hover over elements to highlight them")
    print("- Click to capture XPath")
    print("- Duplicates are automatically skipped")
    print("- Press Enter in terminal when done")
    print("="*50 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.expose_function("reportXPath", handle_xpath)
        page.goto(url)
        page.evaluate(XPATH_JS)

        print("Recording... Click elements to capture XPath.\n")

        try:
            input()
        except EOFError:
            pass

        # Clean exit
        try:
            browser.close()
        except Exception:
            pass

    # Save results
    if captured_xpaths:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format_choice in ["1", "4"]:
            save_python(f"xpaths_{timestamp}.py", url)
        if format_choice in ["2", "4"]:
            save_json(f"xpaths_{timestamp}.json", url)
        if format_choice in ["3", "4"]:
            save_csv(f"xpaths_{timestamp}.csv", url)

        print(f"\nTotal captured: {len(captured_xpaths)} unique XPaths")
    else:
        print("\nNo elements were captured.")


if __name__ == "__main__":
    main()
