# pillbox
raspberry pi pill box with automatic email reminders

## to connect the pillbox to the raspberry pi:
need to connect to pins: 1 (3.3v),9 (gnd),proximity switch 11 (gpio17),green led - 13 (gpio27),red led 15 (gpio22)

## to prepare the raspberry pi:
sudo nano /etc/rc.local
export PILL_PASSWORD= ***SECRET PASSWORD***
python /home/pi/git/pillbox/pillbox.py &
