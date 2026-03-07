import random
import socket
import subprocess
import time
import webbrowser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from imager.config import (
    ARTGRID_FIRST_RESULT_SELECTOR,
    ARTGRID_SEARCH_BASE,
    BROWSER_OPEN_DELAY_MIN,
    BROWSER_OPEN_DELAY_MAX,
    FIREFOX_BINARY,
    FIREFOX_MARIONETTE_PORT,
    PATHS,
)


def open_first_result(search_url: str) -> None:
    webbrowser.open(search_url)
    time.sleep(random.uniform(BROWSER_OPEN_DELAY_MIN, BROWSER_OPEN_DELAY_MAX))


def _wait_for_port(port: int, timeout_seconds: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                s.connect(("127.0.0.1", port))
                return
        except (OSError, socket.error):
            time.sleep(0.2)
    raise TimeoutError(f"Marionette port {port} did not become reachable within {timeout_seconds}s")


def _start_firefox_with_marionette(port: int) -> subprocess.Popen:
    profile_dir = PATHS["data_dir"] / "firefox_automation_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        FIREFOX_BINARY,
        "-profile",
        str(profile_dir),
        "-marionette",
        "-start-debugger-server",
        str(port),
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as e:
        raise ValueError(
            f"Firefox binary not found: {FIREFOX_BINARY}. Install Firefox or set correct path."
        ) from e
    _wait_for_port(port)
    return proc


def connect_firefox(marionette_port: int | None = None) -> tuple["webdriver.Firefox", subprocess.Popen]:
    port = marionette_port if marionette_port is not None else FIREFOX_MARIONETTE_PORT
    firefox_process = _start_firefox_with_marionette(port)
    service = Service(
        service_args=[
            "--marionette-port",
            str(port),
            "--connect-existing",
        ]
    )
    driver = webdriver.Firefox(service=service)
    return driver, firefox_process


def open_first_result_via_firefox(driver, search_url: str) -> None:
    driver.get(search_url)
    try:
        first = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ARTGRID_FIRST_RESULT_SELECTOR))
        )
        href = first.get_attribute("href")
        if href and not href.startswith("http"):
            base = ARTGRID_SEARCH_BASE.rstrip("/")
            href = base + ("/" + href.lstrip("/"))
        if href:
            driver.get(href)
    except Exception:
        pass
    time.sleep(random.uniform(BROWSER_OPEN_DELAY_MIN, BROWSER_OPEN_DELAY_MAX))
