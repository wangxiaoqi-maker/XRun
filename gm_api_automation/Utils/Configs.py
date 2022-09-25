import os

from pydantic import BaseSettings

ROOT = os.path.dirname(os.path.abspath(__file__))


class BaseConfig(BaseSettings):
    LOG_DIR = os.path.join(ROOT, 'logs')
    LOG_NAME = os.path.join(LOG_DIR, 'gmjk.log')
    GMJK_INFO = "gmjk_info"
    GMJK_ERROR = "gmjk_error"

    BANNER = """
  ██████╗ ███╗   ███╗     ██╗██╗  ██╗    ██████╗ ██╗   ██╗███╗   ██╗███╗   ██╗███████╗██████╗ 
██╔════╝ ████╗ ████║     ██║██║ ██╔╝    ██╔══██╗██║   ██║████╗  ██║████╗  ██║██╔════╝██╔══██╗
██║  ███╗██╔████╔██║     ██║█████╔╝     ██████╔╝██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
██║   ██║██║╚██╔╝██║██   ██║██╔═██╗     ██╔══██╗██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
╚██████╔╝██║ ╚═╝ ██║╚█████╔╝██║  ██╗    ██║  ██║╚██████╔╝██║ ╚████║██║ ╚████║███████╗██║  ██║
 ╚═════╝ ╚═╝     ╚═╝ ╚════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
                                                                                                                                          
    """


if __name__ == '__main__':
    print(BaseConfig().LOG_DIR)
    print(BaseConfig().LOG_NAME)
