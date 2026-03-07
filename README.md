Imager

Setup: `pip install -r requirements.txt`. No `playwright install` needed (script connects to your existing browser).

**Default (--open):** URLs open in your default browser. You click the first result and use Download Helper.

**Optional (--open --connect):** Automates opening the first result in your existing Chromium or Chrome (your profile; avoids Artgrid block). Start the browser with remote debugging before running: `--remote-debugging-port=9222`. Example macOS: `/Applications/Chromium.app/Contents/MacOS/Chromium --remote-debugging-port=9222` or Google Chrome: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --remote-debugging-port=9222`. Then run e.g. `python -m imager.main input/audio.mp3 --open --connect` or `python -m imager.main urls --file --open --connect`. The script connects to that browser and opens each search URL then the first result.
