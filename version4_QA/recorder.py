# recorder.py - Subprocess version for Streamlit
# Takes URL and format as command line arguments
# Runs until terminated by parent process

import sys
import json
import csv
import time
import signal
from datetime import datetime
from playwright.sync_api import sync_playwright

captured_xpaths = {}

XPATH_JS = """
(function () {
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

        if (element.id) {
            xpath = '//*[@id="' + element.id + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'id' };
        }

        if (element.name) {
            xpath = '//' + tag + '[@name="' + element.name + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'name' };
        }

        if (element.dataset && element.dataset.testid) {
            xpath = '//*[@data-testid="' + element.dataset.testid + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'data-testid' };

            if (text) {
                xpath = '//*[@data-testid="' + element.dataset.testid + '" and contains(., "' + text + '")]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'data-testid+text' };
            }
        }

        const ariaLabel = element.getAttribute('aria-label');
        if (ariaLabel) {
            xpath = '//*[@aria-label="' + ariaLabel + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'aria-label' };
        }

        const role = element.getAttribute('role');
        if (role) {
            xpath = '//*[@role="' + role + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'role' };

            if (text) {
                xpath = '//*[@role="' + role + '" and contains(., "' + text + '")]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'role+text' };
            }
        }

        if (element.placeholder) {
            xpath = '//input[@placeholder="' + element.placeholder + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'placeholder' };
        }

        if (element.type && (tag === 'input' || tag === 'button')) {
            xpath = '//' + tag + '[@type="' + element.type + '"]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'type' };

            if (element.name) {
                xpath = '//' + tag + '[@type="' + element.type + '" and @name="' + element.name + '"]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'type+name' };
            }
        }

        if (tag === 'a' && element.href) {
            const href = element.getAttribute('href');
            if (href && !href.startsWith('javascript:')) {
                xpath = '//a[@href="' + href + '"]';
                if (countMatches(xpath) === 1) return { xpath, strategy: 'href' };
            }
        }

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\\s+/);
            for (const cls of classes) {
                if (cls.length > 3 && !cls.match(/^(mt-|mb-|px-|py-|flex|grid|text-|bg-)/)) {
                    xpath = '//' + tag + '[contains(@class, "' + cls + '")]';
                    if (countMatches(xpath) === 1) return { xpath, strategy: 'class' };
                }
            }
        }

        if (text && text.length < 50) {
            xpath = '//' + tag + '[contains(., "' + text + '")]';
            if (countMatches(xpath) === 1) return { xpath, strategy: 'text' };
        }

        return { xpath: getAbsoluteXPath(element), strategy: 'absolute' };
    }

    function highlightElement(el) {
        if (lastHighlighted && lastHighlighted !== el) {
            lastHighlighted.style.outline = originalStyles.outline || '';
            lastHighlighted.style.backgroundColor = originalStyles.bg || '';
        }

        if (el) {
            originalStyles = {
                outline: el.style.outline,
                bg: el.style.backgroundColor
            };
            el.style.outline = HIGHLIGHT_STYLE;
            el.style.backgroundColor = HIGHLIGHT_BG;
            lastHighlighted = el;
        }
    }

    document.addEventListener('mouseover', function(e) {
        highlightElement(e.target);
    }, true);

    document.addEventListener('click', function(e) {
        const el = e.target;
        const result = getXPath(el);
        const label = el.id || el.name || el.placeholder || el.textContent.trim().slice(0, 30) || el.tagName.toLowerCase();
        const matches = countMatches(result.xpath);
        window.reportXPath(label, result.xpath, result.strategy, matches, 'click', '');
    }, true);

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
    key = f"{xpath}|{action}"
    is_update = key in captured_xpaths
    
    captured_xpaths[key] = {
        "label": label,
        "xpath": xpath,
        "strategy": strategy,
        "matches": matches,
        "action": action,
        "values": values
    }

    if is_update:
        print(f"[UPDATE] {label}: {values}", flush=True)
    else:
        status = "UNIQUE" if matches == 1 else f"{matches} matches"
        print(f"[{len(captured_xpaths)}] {label} | {action} | {status}", flush=True)


def save_python(filename, url):
    with open(filename, 'w') as f:
        f.write(f'# XPaths captured from: {url}\n')
        f.write(f'# Captured at: {datetime.now().isoformat()}\n')
        f.write(f'# Total elements: {len(captured_xpaths)}\n\n')
        f.write('XPATHS = {\n')
        for item in captured_xpaths.values():
            xpath_escaped = item["xpath"].replace("'", "\\'")
            f.write(f'    "{item["label"]}_{item["action"]}": \'{xpath_escaped}\',  # {item["strategy"]} | {item["values"]}\n')
        f.write('}\n')


def save_json(filename, url):
    data = {
        "url": url,
        "captured_at": datetime.now().isoformat(),
        "total_elements": len(captured_xpaths),
        "xpaths": list(captured_xpaths.values())
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def save_csv(filename, url):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Label', 'XPath', 'Strategy', 'Matches', 'Action', 'Value'])
        for item in captured_xpaths.values():
            writer.writerow([item["label"], item["xpath"], item["strategy"], item["matches"], item["action"], item["values"]])


def save_files(url, formats, output_dir="."):
    if not captured_xpaths:
        print("No elements captured.", flush=True)
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_files = []
    
    if 'py' in formats:
        filename = f"{output_dir}/xpaths_{timestamp}.py"
        save_python(filename, url)
        saved_files.append(filename)
    
    if 'json' in formats:
        filename = f"{output_dir}/xpaths_{timestamp}.json"
        save_json(filename, url)
        saved_files.append(filename)
    
    if 'csv' in formats:
        filename = f"{output_dir}/xpaths_{timestamp}.csv"
        save_csv(filename, url)
        saved_files.append(filename)
    
    print(f"SAVED:{','.join(saved_files)}", flush=True)
    return saved_files


# Global variables for cleanup access
url = ""
formats = []
output_dir = "."

def cleanup(signum=None, frame=None):
    global url, formats, output_dir
    print("STOPPING...", flush=True)
    
    if captured_xpaths:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if 'json' in formats:
            filename = f"{output_dir}/xpaths_{timestamp}.json"
            save_json(filename, url)
            print(f"Saved: {filename}", flush=True)
        
        if 'csv' in formats:
            filename = f"{output_dir}/xpaths_{timestamp}.csv"
            save_csv(filename, url)
            print(f"Saved: {filename}", flush=True)
        
        if 'py' in formats:
            filename = f"{output_dir}/xpaths_{timestamp}.py"
            save_python(filename, url)
            print(f"Saved: {filename}", flush=True)
        
        print(f"Total: {len(captured_xpaths)} elements", flush=True)
    else:
        print("No elements captured.", flush=True)
    
    print("DONE", flush=True)
    sys.exit(0)


def main():
    global url, formats, output_dir
    
    if len(sys.argv) < 3:
        print("Usage: python recorder.py <url> <formats> [output_dir]", flush=True)
        print("Formats: py,json,csv (comma-separated)", flush=True)
        sys.exit(1)
    
    url = sys.argv[1]
    formats = sys.argv[2].split(',')
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    
    print(f"STARTING: {url}", flush=True)
    
    # Handle termination signals
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.expose_function("reportXPath", handle_xpath)
            page.goto(url)
            page.evaluate(XPATH_JS)
            
            print("RECORDING", flush=True)
            
            # Keep running until terminated - use page.wait_for_timeout to allow event processing
            while True:
                page.wait_for_timeout(500)  # This allows Playwright to process events

                
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        cleanup()


if __name__ == "__main__":
    main()
