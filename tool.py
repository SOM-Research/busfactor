__author__ = 'atlanmod'

import subprocess
import os
import signal
import sys
import time
import psutil
from selenium import webdriver
from bus_factor_gui import BusFactor

WEB_BROWSER_PATH = 'C:\chromedriver_win32\chromedriver.exe'

pro = None
gui = None
#if this value is false, the script will prompt the content of the data folder in a HTML page
execute_bus_factor = False


def is_process_running(pid):
    found = False
    for p in psutil.process_iter():
        try:
            if p.pid == pid:
                found = True
                break
        except psutil.Error:
            pass

    return found


def start_server():
    global pro
    print "Starting server..."
    cmd = 'python -m SimpleHTTPServer'
    pro = subprocess.Popen(cmd, shell=True)


def close_browser(driver):
    driver.close()


def start_gui():
    global gui
    gui = subprocess.Popen([sys.executable, "bus_factor_gui.py"] + ["-n", "True"])


def open_browser():
    driver = webdriver.Chrome(executable_path=WEB_BROWSER_PATH)
    driver.get("http://localhost:8000/index.html")
    driver.refresh()

    return driver


def shutdown_server():
    print "Shutting down server..."
    os.kill(pro.pid, signal.SIGTERM)


def delete_notification():
    if os.path.exists(BusFactor.NOTIFICATION):
        os.remove(BusFactor.NOTIFICATION)


def browser_is_open(driver):
    open = True
    try:
        driver.current_url
    except:
        open = False

    return open


def notified():
    flag = False
    if os.path.exists(BusFactor.NOTIFICATION):
        flag = True
        delete_notification()
    return flag


def main():
    delete_notification()
    if execute_bus_factor:
        start_gui()
        while is_process_running(gui.pid):
            time.sleep(10)
            if notified():
                break

    start_server()

    driver = open_browser()
    open = True
    while open:
        time.sleep(1)
        open = browser_is_open(driver)

    shutdown_server()

if __name__ == "__main__":
    main()
