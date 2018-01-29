from urllib2 import urlopen


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080
PUBLIC_IP = urlopen('http://ip.42.pl/raw').read()
