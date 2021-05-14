# -*- coding: utf-8 -*-

import logging
from datetime import datetime

logger = logging.getLogger('client_log')
formatter = logging.Formatter('%(asctime)s    %(levelname)s ---> %(message)s   ')

oTime = datetime.now().strftime('-%d-%m-%y')
fh = logging.FileHandler(f"./log/client_log{oTime}.txt", encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger.addHandler(fh)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

### GO ###
#logger.info('Тестовый запуск логирования')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
logger.addHandler(console)
