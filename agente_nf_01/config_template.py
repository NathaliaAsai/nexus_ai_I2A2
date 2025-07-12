from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv(dotenv_path=".envapi")  
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL")