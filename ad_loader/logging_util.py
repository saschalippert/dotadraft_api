import logging
import logging.config

import yaml


def load_logging_config():
    with open('logging.yml', 'r') as f:
        log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
