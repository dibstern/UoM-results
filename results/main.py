"""
-------------------------------------------------------------------------------
Log in to my.unimelb results page using an externally-specified student
account, check for updates on the results page, and then send the student
an email if anything has changed

Script originally written by Matthew Farrugia (GITHUB HERE)
Forked & Refactored by D. Stern from 7/11/17-onwards
Updates listed in the README.
-------------------------------------------------------------------------------
Current PID: 1392
-------------------------------------------------------------------------------
"""

# Reporting Back To User
from time import localtime, strftime, sleep
import random

# Web Navigation & Parsing
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re
from contextlib import suppress

# Email Creation & Sending
import smtplib
from email.mime.text import MIMEText

QUERY = "?f=%24S1.EST.RSLTDTLS.WEB"
URL = "https://prod.ss.unimelb.edu.au/student/SM/ResultsDtls10.aspx" + QUERY
USERNAME_BOX_ID = "ctl00_Content_txtUserName_txtText"
PASSWORD_BOX_ID = "ctl00_Content_txtPassword_txtText"
LOGIN_BUTTON_ID = "ctl00_Content_cmdLogin"
LOGOUT_BUTTON_ID = "ctl00_LogoutLinkButton"
WAM_CLASS = "UMWAMText"

# Specific to D. Stern (Multiple Degrees means an intermediate page & button)
ENG_BUTTON_ID = "ctl00_Content_grdResultPlans_ctl04_ctl00"

EMAIL_FILE = "email.txt"
LOGIN_FILE = "login.txt"
WAM_FILE = "wam.txt"
STATUS_FILE = "status.txt"

EMAIL_SUBJECT = "WAM Update"
EMAIL_DOMAIN = "@gmail.com"

CHANGE_MSG = "Hey, there!\n\nI noticed that your wam has changed from "
SUCCESS_MSG = "Congratulations! "
COMMISERATIONS_MSG = ("That's okay, you tried your best, "
                      "and that's all anyone can ask for! ")
END_MSG = "\n\nHave a nice day!\n\nLove, results robot\n--\n"


def main():

    # get login details from configuration file
    username, password = get_username_password(LOGIN_FILE)

    # login to results page and retrieve the WAM and date
    new_wam, new_date = get_wam_and_date(username, password)

    # Check if WAM changed
    changed, old_wam = has_changed(new_wam, new_date)
    date_time_of_check = strftime("%a, %I:%M:%S %p, %d/%b/%Y", localtime())

    # Create & send an email if anything changed
    if changed:

        # Write the message and get the destination address
        message = write_msg(old_wam, new_wam)
        email_user, _pass = get_username_password(EMAIL_FILE)
        target = email_user + EMAIL_DOMAIN

        # Send off the message!
        send_results(target, EMAIL_SUBJECT, message)
        print("Sent an email to " + target)
        with open(STATUS_FILE, 'w') as f:
            f.write(f"Updated at {date_time_of_check}\n")

    # 20% of the time, print update messages to terminal
    elif random.random() < 0.20:
            print(f"No update at: {date_time_of_check}")


def get_wam_and_date(username, password):
    """Retrieve the WAM and the date of last update from my.unimelb.edu.au.

    Args:
        username (str): The my.unimelb.edu.au username.
        password (str): The my.unimelb.edu.au password

    Return:
        float: The WAM found at my.unimelb.edu.au.
        str  : The date of last update found at my.unimelb.edu.au.
    """

    # login to results page and get its source
    source = get_results(username, password)

    # parse results page to check for updates
    soup = BeautifulSoup(source, "html5lib")

    # Get the WAM object
    wam_div = soup.find(class_=WAM_CLASS)

    # Get the WAM and date
    wam = float(wam_div.find("b").text)
    date = (re.findall(r'\d{2}-[a-zA-Z]{3}-\d{4}', wam_div.__str__()))[0]

    return wam, date


def write_msg(old_wam, new_wam):
    """Write the message for the email.

    Args:
        old_wam (str): The old WAM from the stored file.
        new_wam (str): The new WAM from my.unimelb.edu.au

    Return:
        str: A message for the email.

    """

    # construct the message body
    message = CHANGE_MSG + f"{old_wam} to {new_wam}."
    if new_wam > old_wam:
        message += SUCCESS_MSG
    else:
        message += COMMISERATIONS_MSG

    return message + END_MSG


def has_changed(new_wam, new_date):
    """Checks if the new WAM is different to the old WAM.

    Args:
        new_wam (float): The new WAM retrieved from the site, to be compared to
                         the old WAM.

    Returns:
        bool: True if the old WAM is different to new_wam, else False
        float: The old WAM found in the file.

    """

    changed = False
    with open(WAM_FILE, 'r+') as f:

        # what was the old wam and date?
        old_wam = float(f.readline().strip())
        old_date = f.readline().strip()

        # update the file if it has changed
        if (new_wam != old_wam and new_date != old_date):
            changed = True
            f.seek(0)
            f.write(str(new_wam)+'\n')
            f.truncate()

    return changed, old_wam


def get_results(username, password):
    """Log in to the results page, retrieve the page's HTML source & logout.

    Args:
        username  (str): The username of the my.unimelb account.
        password  (str): The password of the my.unimelb account.

    Returns:
        str: The page source.

    """

    # load up the browser
    driver = webdriver.PhantomJS()
    driver.set_window_size(1120, 550)

    # go to the results page and enter the username and password
    driver.get(URL)

    usernamebox = driver.find_element_by_id(USERNAME_BOX_ID)
    passwordbox = driver.find_element_by_id(PASSWORD_BOX_ID)

    usernamebox.send_keys(username)
    passwordbox.send_keys(password)

    loginbutton = driver.find_element_by_id(LOGIN_BUTTON_ID)
    loginbutton.click()

    # Navigate into Results page for Masters Degree
    click_through_intermediate_page(driver)

    # great the source before we log out, then reurn the source
    page_source = driver.page_source

    logoutbutton = driver.find_element_by_id(LOGOUT_BUTTON_ID)
    logoutbutton.click()

    return page_source


def click_through_intermediate_page(driver):
    '''Click on the correct button, through to the intermediate page.

    Args:
        driver (webdriver.PhantomJS()): The driver object.
    '''
    retries = 20
    while retries > 0:
        with suppress(NoSuchElementException):
            sleep(2)
            view_eng_button = driver.find_element_by_id(ENG_BUTTON_ID)
            view_eng_button.click()
            return True
        retries -= 1
    return False


def send_results(target, subject, message):
    """Login to gmail as the results robot, and send an email to the target

    Args:
        target  (str): The email to which the message will be sent.
        subject (str): The subject of the email to be sent.
        message (str): The message to be sent in the email.

    """

    # what are the results robot's authentication details?
    username, password = get_username_password(EMAIL_FILE)

    sender = username + EMAIL_DOMAIN

    # make the email object
    msg = MIMEText(message)
    msg['To'] = target
    msg['Subject'] = subject
    msg['From'] = sender

    # Log into gmail's free SMTP server as the results robot & send the message
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.login(sender, password)
    s.sendmail(sender, [target], msg.as_string())
    s.quit()


def get_username_password(filename):
    """Retrieves the stored username and password.

    Args:
        filename (str): The name of the file in which the details are stored
    Returns:
        str: The username & password stored in the file.

    """
    with open(filename) as f:
        username = f.readline().strip()
        password = f.readline().strip()
    return (username, password)


if __name__ == '__main__':
    main()
