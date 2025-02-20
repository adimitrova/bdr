from src.app import run, test_run
from src.settings import config

if __name__ == '__main__':
    if config.ENV == 'test':
        test_run()
    else:
        run()
