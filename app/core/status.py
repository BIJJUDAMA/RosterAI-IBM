import os
import redis
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration for Status Tracking
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

#Scalable, atomic status tracking using Redis
class RedisStatusTracker:
    
    def get_status(self):
        status = r.hgetall("system_status")
        if not status:
            return {"is_ingesting": "False", "is_matching": "False", "progress": "0", "current_task": "Ready", "is_llm_ready": "False"}
        return status

    def set_status(self, is_ingesting: bool = None, is_matching: bool = None, progress: float = None, current_task: str = None, is_llm_ready: bool = None):
        mapping = {}
        if is_ingesting is not None: mapping["is_ingesting"] = "True" if is_ingesting else "False"
        if is_matching is not None: mapping["is_matching"] = "True" if is_matching else "False"
        if progress is not None: mapping["progress"] = str(progress)
        if current_task is not None: mapping["current_task"] = current_task
        if is_llm_ready is not None: mapping["is_llm_ready"] = "True" if is_llm_ready else "False"
        if mapping:
            r.hset("system_status", mapping=mapping)
        return self.get_status()

    def reset(self):
        r.delete("system_status")
        self.set_status(is_ingesting=False, is_matching=False, progress=0, current_task="Ready", is_llm_ready=False)

status_tracker = RedisStatusTracker()
