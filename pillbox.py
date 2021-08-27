#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import smtplib
import os
import sys
from datetime import datetime


def debug(level, msg, save_to_file=True):
    global logfilename
    global debug_level

    if level < debug_level:
        return
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cmsg = '[%s] [%s]: %s' % (level, date_str, msg)
    print(cmsg)
    if save_to_file:
        with open(logfilename, 'a') as fl:
            fl.write(cmsg)


def send_mail(to, subj, body):
    if 'PILL_PASSWORD' not in os.environ:
        raise ValueError('PILL_PASSWORD not found in environment variables')

    gmail_user = 'hasafsal.books@gmail.com'
    gmail_password = os.environ['PILL_PASSWORD']

    sent_from = gmail_user
    to = ['amnonim@gmail.com']
    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subj, body)

    try:
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_password)
        smtp_server.sendmail(sent_from, to, email_text)
        smtp_server.close()
        debug(3, "Email sent successfully!")
    except Exception as ex:
        debug(3, "Something went wrong….", ex)


def main_loop():
    global debug_level
    global logfilename

    debug_level = 3
    logfilename = 'pillbox-log.txt'

    # initialize the gpio inputs
    GPIO.setmode(GPIO.BCM)
    channel = 17
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    while (True):
        if GPIO.input(channel):
            debug(3, 'HIGH')
        else:
            debug(3, 'Input was LOW')
        time.sleep(0.1)


def main(argv):
        main_loop()


if __name__ == "__main__":
        main(sys.argv[1:])
