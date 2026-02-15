from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        
        # Collections
        self.users = self.db["users"]
        self.subtitles = self.db["subtitles"]
        self.requests = self.db["requests"]
        self.stats = self.db["stats"]
        self.settings = self.db["settings"]
        
        # Create indexes
        self.users.create_index("user_id", unique=True)
        self.subtitles.create_index([("title", ASCENDING), ("year", ASCENDING)], unique=True)
        self.subtitles.create_index("file_id")
        self.subtitles.create_index("message_id")
        self.requests.create_index([("user_id", ASCENDING), ("requested_title", ASCENDING)])
        self.stats.create_index("key", unique=True)
        self.settings.create_index("key", unique=True)
        
        # Initialize default settings if not present
        if not self.settings.find_one({"key": "start_image"}):
            self.settings.insert_one({"key": "start_image", "value": config.START_IMAGE})
    
    # ---------- User Management ----------
    def add_user(self, user_id, first_name, username=None, language="en"):
        try:
            self.users.insert_one({
                "user_id": user_id,
                "first_name": first_name,
                "username": username,
                "language": language,
                "joined_date": datetime.utcnow(),
                "download_count": 0,
                "request_count": 0,
                "is_active": True,
                "blocked_bot": False
            })
            logger.info(f"New user added: {user_id}")
        except DuplicateKeyError:
            self.update_user_activity(user_id)
    
    def update_user_activity(self, user_id):
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.utcnow(), "is_active": True}}
        )
    
    def get_user(self, user_id):
        return self.users.find_one({"user_id": user_id})
    
    def get_all_users(self, active_only=True):
        query = {"is_active": True} if active_only else {}
        return self.users.find(query)
    
    def count_users(self, active_only=True):
        query = {"is_active": True, "blocked_bot": False} if active_only else {}
        return self.users.count_documents(query)
    
    def set_blocked(self, user_id):
        self.users.update_one({"user_id": user_id}, {"$set": {"blocked_bot": True}})
    
    # ---------- Subtitle Management ----------
    def add_subtitle(self, file_id, file_name, file_size, caption, message_id, channel_id, title, year=None, language="si", media_type="movie"):
        """
        Add or update subtitle. If same title+year exists, update the file details.
        """
        # Clean file name: remove channel usernames, links, etc.
        clean_title = self.clean_title(title)
        
        # Check if already exists
        existing = self.subtitles.find_one({"title": clean_title, "year": year})
        if existing:
            # Update existing entry
            self.subtitles.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "caption": caption,
                    "message_id": message_id,
                    "channel_id": channel_id,
                    "updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"Updated subtitle: {clean_title} ({year})")
            return existing["_id"]
        else:
            # Insert new
            result = self.subtitles.insert_one({
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size,
                "caption": caption,
                "message_id": message_id,
                "channel_id": channel_id,
                "title": clean_title,
                "year": year,
                "language": language,
                "media_type": media_type,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            logger.info(f"Added new subtitle: {clean_title} ({year})")
            return result.inserted_id
    
    def clean_title(self, title):
        """
        Remove unwanted patterns like channel links, usernames from title.
        """
        import re
        # Remove common channel patterns: @username, t.me/xxx, https://t.me/xxx
        title = re.sub(r'@\w+', '', title)
        title = re.sub(r't\.me/\w+', '', title)
        title = re.sub(r'https?://t\.me/\w+', '', title)
        # Remove extra spaces
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def search_subtitles(self, query, limit=50):
        """
        Search by title using regex (case-insensitive). Later we can add fuzzy.
        """
        import re
        regex = re.compile(re.escape(query), re.IGNORECASE)
        cursor = self.subtitles.find({"title": regex}).sort("year", DESCENDING).limit(limit)
        return list(cursor)
    
    def get_subtitle_by_file_id(self, file_id):
        return self.subtitles.find_one({"file_id": file_id})
    
    def count_subtitles(self):
        return self.subtitles.count_documents({})
    
    # ---------- Request Management ----------
    def add_request(self, user_id, requested_title, tmdb_data=None):
        req = {
            "user_id": user_id,
            "requested_title": requested_title,
            "tmdb_data": tmdb_data,
            "status": "pending",  # pending, approved, rejected, fulfilled
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = self.requests.insert_one(req)
        # Increment user request count
        self.users.update_one({"user_id": user_id}, {"$inc": {"request_count": 1}})
        return result.inserted_id
    
    def update_request_status(self, request_id, status, fulfilled_file_id=None):
        update = {"status": status, "updated_at": datetime.utcnow()}
        if fulfilled_file_id:
            update["fulfilled_file_id"] = fulfilled_file_id
        self.requests.update_one({"_id": request_id}, {"$set": update})
    
    def get_pending_requests(self):
        return self.requests.find({"status": "pending"}).sort("created_at", ASCENDING)
    
    # ---------- Statistics ----------
    def increment_stat(self, key, inc=1):
        self.stats.update_one(
            {"key": key},
            {"$inc": {"value": inc}},
            upsert=True
        )
    
    def get_stat(self, key):
        doc = self.stats.find_one({"key": key})
        return doc["value"] if doc else 0
    
    # ---------- Settings ----------
    def get_setting(self, key):
        doc = self.settings.find_one({"key": key})
        return doc["value"] if doc else None
    
    def set_setting(self, key, value):
        self.settings.update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True
        )

db = Database()
