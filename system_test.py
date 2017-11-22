# This will work if the system is operational.

# Testing Libraries
from selenium import webdriver
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import smtplib

# Testing PhantomJS availability in PATH
driver = webdriver.PhantomJS()

# Set up Test Email
sender = target = "dibstern@gmail.com"
password = "INSERTPASSWORDHERE"
subject = "WAM Update"
message = "Test Message!"

# Create Test Email
msg = MIMEText(message)
msg['Subject'] = subject
msg['From'] = sender


# Send Test Email
s = smtplib.SMTP('smtp.gmail.com', 587); s.ehlo(); s.starttls()
s.login(sender, password)
s.sendmail(sender, [target], msg.as_string())
