Imager

Setup: `pip install -r requirements.txt`.

**Default (--open):** URLs open in your default browser. You click the first result and use Download Helper.

**Optional (--open --connect-firefox):** Automates opening the first result in Firefox. One-time setup: install geckodriver (e.g. `brew install geckodriver` on macOS). The script starts Firefox with Marionette, connects to it, opens each search URL and navigates to the first result. Firefox is closed when the script exits.