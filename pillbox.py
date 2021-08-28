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
            fl.write(cmsg + '\n')


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
        debug(3, "Something went wrong: %s" % ex)


def main_loop():
    global debug_level
    global logfilename

    debug_level = 3
    logfilename = 'pillbox-log.txt'
    pill_start_hour = 7
    pill_remind_hour = 10
    last_pill_time = datetime.now()
    pill_taken = True
    reminder_sent = False
    reminder_time = datetime.now()
    # time between pill reminders, in seconds
    reminder_interval = 60 * 60
    sleep_interval = 1000

    # initialize the gpio inputs
    GPIO.setmode(GPIO.BCM)
    channel = 17
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    current_state = GPIO.input(channel)

    debug(7, 'pillbox started')

    while (True):
        # wait for state change
        GPIO.wait_for_edge(channel, GPIO.BOTH, timeout=sleep_interval)

        sleep_interval = 60000
        cnow = datetime.now()

        # get the current state
        cstate = GPIO.input(channel)
        if cstate == current_state:
            # nothing changed - it was a timeout
            if last_pill_time.day != cnow.day:
                # if a new day, we need to take a new pill
                pill_taken = False
                reminder_sent = False
                debug(3, 'new day, pill_taken reset')
            if not pill_taken:
                if cnow.hour > pill_remind_hour:
                    if (cnow - reminder_time).seconds > reminder_interval:
                        reminder_sent = False
                        if not reminder_sent:
                            debug(7, 'oh no, still didnt take a pill, sending a reminder')
                            send_mail(to=['amnonim@gmail.com', 'strudelit@gmail.com'], subj='Did you forget your medicine?', body='You need to take your medicine!!!!\nAmnon loves you moremoremoremoremore\n')
                            reminder_sent = True
                            reminder_time = cnow
                        else:
                            debug(3, 'still need to take pill but reminder already sent')
            continue

        if cstate:
            # box is opened - we are taking a pill
            debug(6, 'box opened (high)')
            pill_taken = True
            last_pill_time = cnow
            reminder_sent = False
        else:
            # low
            debug(6, 'box closed')
        # we need to wait a few ms to prevent edge events
        time.sleep(0.3)
        sleep_interval = 1000

        current_state = cstate


def main(argv):
        main_loop()


if __name__ == "__main__":
        main(sys.argv[1:])
