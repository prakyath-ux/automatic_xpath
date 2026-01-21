from playwright.sync_api import sync_playwright

# def main():
#     url = input("Enter URL: ")

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         page.goto(url)

#         print("Browser opened. Press Ctrl+C in terminal to close")

#         #keep browser on
#         input("Press Enter to close browser")
#         browser.close()

# if __name__== "__main__":
#     main()

from playwright.sync_api import sync_playwright

XPATH_JS = """
(function() {
function getXPath(element) {
    if (element.id) {
        return `//*[@id="${element.id}"]`;
    }

    if (element === document.body) {
        return '/html/body';
    }

    let position = 1;
    let siblings = element.parentNode ? element.parentNode.childNodes : [];

    for (let sibling of siblings) {
        if (sibling === element) {
            const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
            const tagName = element.tagName.toLowerCase();
            return `${parentPath}/${tagName}[${position}]`
        }
        if (sibling.nodeType == 1 && sibling.tagName === element.tagName) {
            position++;
        }
    }
    return '';
}

document.addEventListener('click', function(e) {
    const xpath = getXPath(e.target);
    console.log ('XPATH:', xpath);
    window.reportXPath(xpath);
    }, true);
})();
"""

def handle_xpath(xpath):
    print(f"\n>>> Captured XPath: {xpath}")

def main():
    url = input("Enter url: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        #Expose python function to JS
        page.expose_function("reportXPath", handle_xpath)

        page.goto(url)

        #inject the link listener
        page.evaluate(XPATH_JS)

        print("\nBrowser ready! Click any element to capture its XPath.")
        print("Press Enter in terminal to close.\n")

        input()
        browser.close()

if __name__ == "__main__":
    main()