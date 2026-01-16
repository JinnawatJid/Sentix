from playwright.sync_api import sync_playwright
import os
import json

def test_audit_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cwd = os.getcwd()
        file_url = f"file://{cwd}/verification/test_audit.html"

        page.goto(file_url)

        mock_trace = {
            "timestamp": "2024-01-01T12:00:00",
            "topic": "Test Topic",
            "verification_score": 3,
            "sources_list": "['Source A', 'Source B']",
            "verification_status": "VERIFIED",
            "ai_reasoning": "Reasoning line 1.\n\n[Critic Refinement]\nOriginal Tweet:\nHello\n\nRewritten Tweet:\nHello World",
            "generated_tweet": "Hello World",
            "clusters_found": "[]"
        }

        # Correctly serialize to JSON for JS embedding
        mock_trace_json = json.dumps(mock_trace)

        page.evaluate(f"""
            const tbody = document.getElementById('audit-table-body');
            const row = document.createElement('tr');

            // Create data object
            const traceData = {mock_trace_json};

            row.innerHTML = `
                <td>Test Time</td>
                <td>Test Topic</td>
                <td>3</td>
                <td>Sources</td>
                <td>VERIFIED</td>
                <td><button id='test-btn' class="text-blue-400">View Logic</button></td>
            `;

            // Bind click event directly to avoid quoting hell
            const btn = row.querySelector('#test-btn');
            btn.onclick = () => showDetails(traceData);

            tbody.appendChild(row);
        """)

        # Click the button
        page.click("#test-btn")

        # Wait for modal to appear
        page.wait_for_selector("#details-modal:not(.hidden)", state="visible")

        # Take Screenshot
        element = page.locator("#details-modal")
        element.screenshot(path="verification/verification.png")

        browser.close()

if __name__ == "__main__":
    test_audit_page()
