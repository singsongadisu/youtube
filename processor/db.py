import motor.motor_asyncio
import datetime
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, uri: str = "mongodb://localhost:27017", db_name: str = "studio_db"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.projects = self.db.projects

    async def save_project(self, project_data: Dict[str, Any]) -> str:
        """Saves a new project result to MongoDB."""
        project_data["created_at"] = datetime.datetime.utcnow()
        # Extract a clean title if possible
        video_filename = project_data.get("video_filename", "Unknown Project")
        project_data["title"] = video_filename.replace(".mp4", "").replace(".json", "").replace("studio_", "")
        
        result = await self.projects.insert_one(project_data)
        return str(result.inserted_id)

    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Retrieves all project summaries from MongoDB (newest first)."""
        cursor = self.projects.find({}, {"title": 1, "created_at": 1, "_id": 1}).sort("created_at", -1)
        projects = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc:
                doc["created_at"] = doc["created_at"].isoformat()
            projects.append(doc)
        return projects

    async def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """Retrieves a full project result by its MongoDB ID."""
        from bson import ObjectId
        doc = await self.projects.find_one({"_id": ObjectId(project_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            if "created_at" in doc:
                doc["created_at"] = doc["created_at"].isoformat()
        return doc
