import logging

__version__ = "0.0.1"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)03d %(name)-12s %(levelname)-8s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# EVA Configuration
EVA_IP_ADDRESS = "10.213.55.80"
EVA_TOKEN = '35ad1b7da935684d10afdc09a5842d5e6403b0f8'

# Server configuration
SERVER_PORT = 80