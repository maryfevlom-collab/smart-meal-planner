import os

# FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")

class Config:
    # Load environment variables (good for Render or local .env file)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # MySQL database connection
    #DB_HOST = os.getenv("DB_HOST", "localhost")
    #DB_USER = os.getenv("DB_USER", "root")
    #DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    #DB_NAME = os.getenv("DB_NAME", "recipe_db")
    #DB_PORT = int(os.getenv("DB_PORT", 3306))
    
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = int(os.getenv("DB_PORT"))
