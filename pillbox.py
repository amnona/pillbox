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


def send_email(subject, body, recipient=['amnonim@gmail.com', 'strudelit@gmail.com'], user='pillbox@gmail.com', pwd=None, smtp_server='smtp-relay.sendinblue.com', smtp_port=587, smtp_user='sugaroops@yahoo.com'):
    '''this is for the sendinblue smtp email server
        for gmail use:
        smtp_server='smtp.gmail.com'
    '''
    if pwd is None:
        if 'PILL_PASSWORD' not in os.environ:
            raise ValueError('PILL_PASSWORD not found in environment variables. please set or provide pwd')
        pwd = os.environ['PILL_PASSWORD']

    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
    print(smtp_user)
    print(pwd)
    print(message)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        debug(2, 'sent email: subject %s to %s' % (SUBJECT, TO))
        return True
    except Exception as err:
        debug(8, 'failed to send email: subject %s to %s. error %s' % (SUBJECT, TO, err))
        return False


def main_loop():
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
    green_led = 27
    red_led = 22
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(green_led, GPIO.OUT)
    GPIO.setup(red_led, GPIO.OUT)
    GPIO.output(green_led, GPIO.HIGH)
    GPIO.output(red_led, GPIO.LOW)

    current_state = GPIO.input(channel)

    debug(7, 'pillbox started')
    debug(7, 'input channel %s, red_led=%s, green_led=%s' % (channel, red_led, green_led))

    while (True):
        # wait for state change
        reschannel = GPIO.wait_for_edge(channel, GPIO.BOTH, timeout=sleep_interval)
        if reschannel is None:
            debug(6, 'timeout')
        else:
            debug(6, 'state changed for channel %s' % reschannel)

        # wait for one minute if nothing happens
        sleep_interval = 60000
        cnow = datetime.now()

        if pill_taken:
            GPIO.output(green_led, GPIO.HIGH)
            GPIO.output(red_led, GPIO.LOW)
        else:
            GPIO.output(green_led, GPIO.LOW)
            GPIO.output(red_led, GPIO.HIGH)

        # get the current state
        cstate = GPIO.input(channel)
        # 1 is closed, 0 is open
        debug(6, 'current state: %s' % cstate)
        if cstate == current_state:
            debug(3, 'nothing changed')
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
                            send_email(to=['amnonim@gmail.com', 'strudelit@gmail.com'], subj='Did you forget your medicine?', body='You need to take your medicine!!!!\nAmnon loves you moremoremoremoremore\n')
                            reminder_sent = True
                            reminder_time = cnow
                        else:
                            debug(3, 'still need to take pill but reminder already sent')
            debug(6, 'continue. interval = %s' % sleep_interval)
            continue

        debug('state changed!')
        if cstate == 0:
            # box is opened - we are taking a pill
            debug(6, 'box opened (high)')
            pill_taken = True
            last_pill_time = cnow
            reminder_sent = False
        else:
            # box is closed
            debug(6, 'box closed')
  
        # we need to wait a few ms to prevent edge events
        time.sleep(100)
        sleep_interval = 1000

        cstate = GPIO.input(channel)
        current_state = cstate
        debug('new current_state: %s. Continuing' % current_state)


def main(argv):
    global debug_level
    global logfilename

    debug_level = 3
    logfilename = '/home/pi/pillbox-log.txt'

    debug(8, 'pillbox started')
    send_email('pillbox started', 'pillbox is now running')
    main_loop()


if __name__ == "__main__":
    main(sys.argv[1:])
