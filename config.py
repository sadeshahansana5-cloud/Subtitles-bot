import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "subtitle_bot")
    
    # Channels
    INDEX_CHANNEL_ID = int(os.getenv("INDEX_CHANNEL_ID", 0))  # Channel with subtitles
    UPDATE_CHANNEL_ID = int(os.getenv("UPDATE_CHANNEL_ID", 0))  # Channel for notifications
    
    # Admins (comma-separated IDs)
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    
    # TMDB API
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    
    # Start image (can be file_id or URL)
    START_IMAGE = os.getenv("START_IMAGE", "")  # Default start image
    
    # Bot settings
    RESULTS_COUNT = int(os.getenv("RESULTS_COUNT", 50))  # Max inline results
    FUZZY_THRESHOLD = int(os.getenv("FUZZY_THRESHOLD", 80))  # For fuzzy matching
    
config = Config()
