# lcd_squeeze
LCD display script for Logitech Media Server

This is a python script which displays Now Playing (artist, title and remaining time) on an LCD
It works with a Logitech Media Server install running on the same machine

**Running the script**
you can run it simply by running the script from the command line

**To run it at boot**
```
sudo cp lcd_squeeze.py /usr/local/bin/
sudo chmod +x /usr/local/bin/lcd_squeeze.py
sudo cp lcd_squeeze /etc/init.d/
sudo chmod +x /etc/init.d/lcd_squeeze
sudo cp lcd_squeeze.service /etc/systemd/system/
sudo systemctl enable lcd_squeeze
```
