import logging


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080

logging.basicConfig()
logger = logging.getLogger('GlobalLogger')
logger.setLevel(logging.INFO)
