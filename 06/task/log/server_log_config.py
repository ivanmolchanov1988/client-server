# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger('server_log')
formatter = logging.Formatter('%(asctime)s    %(levelname)s ---> %(message)s   ')

oTime = datetime.now().strftime('-%d-%m-%y')
fh = logging.FileHandler(f"./log/server_log{oTime}.txt", encoding='utf-8')
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
