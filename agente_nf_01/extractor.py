import zipfile
import os
import pandas as pd
import argparse
import logging
from datetime import datetime
from functools import wraps
import sys

def configure_log(file_prefix,log_dir="logs",timestamp=datetime.today().strftime('%y%m%d')):
    """Configures logging to file and stdout."""
    os.makedirs(log_dir, exist_ok=True)
    log_file_name = os.path.join(log_dir, f"{file_prefix}_{timestamp}.log")
    log_format = '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        filename=log_file_name,
        filemode='w',
        datefmt=date_format,
        format=log_format,
        level=logging.INFO,
        force=True
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    logging.getLogger().addHandler(stdout_handler)
    logging.info(f"Logging configured to: {log_file_name}")

def handle_errors(func):
    """Decorator to handle exceptions within class methods."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except FileNotFoundError as e:
            self.logger.error(f"Arquivo não encontrado: {e}")
            sys.exit(1)
        except PermissionError as e:
            self.logger.error(f"Erro de permissão: {e}")
            sys.exit(1)
        except ValueError as e:
            self.logger.error(f"Erro de valor: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Erro inesperado em {func.__name__}: {e}")
            sys.exit(1)
    return wrapper

class Extractor:
    def __init__(self,output_dir):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            default_loc = os.path.abspath(__file__)
            default_loc = os.path.join(os.path.dirname(default_loc), "outputs")
            self.logger.warning(f"Output directory '{self.output_dir}' does not exist. Using default: {default_loc}")
    
    @handle_errors    
    def _check_file(self,file_path: str) -> bool:
        """Check if the file exists and is .zip."""
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        if not file_path.endswith('.zip'):
            self.logger.error(f"File is not a .zip file: {file_path}")
            return False
        return True
    
    @handle_errors
    def load_file(self, file_path: str) -> bool:
        """Load the .zip file and extract its contents."""
        if not self._check_file(file_path):
            return False
        self.logger.info(f"Loading file: {file_path}")
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(self.output_dir)
 
if __name__ == "__main__":
    configure_log(file_prefix="extractor")
    logger = logging.getLogger(__name__)
    logger.info("Extractor started")
    
    parser = argparse.ArgumentParser(description="Performs data extraction from a zip file.")
    parser.add_argument("-f", "--file", help="Path to the zip file to extract data", required=True)
    parser.add_argument("-o", "--output", help="Path to the output directory", required=True)
    
    args = parser.parse_args()
    
    extractor = Extractor(output_dir=args.output)
    extractor.load_file(file_path=args.file)
    
    logger.info("Extractor finished")
    
    