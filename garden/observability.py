import logging
import time
from datetime import datetime, timezone

from django.conf import settings
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - started) * 1000)
        logger.info(
            "http_request method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response


def store_mongo_document(collection_name, document):
    mongo_uri = settings.MONGODB_URI
    if not mongo_uri:
        logger.warning("MongoDB is not configured; %s was not persisted.", collection_name)
        return False

    from pymongo import MongoClient

    client = None
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=1500,
            connectTimeoutMS=1500,
            socketTimeoutMS=1500,
        )
        client[settings.MONGODB_DATABASE][collection_name].insert_one(
            {"created_at": datetime.now(timezone.utc), **document}
        )
        return True
    except (PyMongoError, ValueError):
        logger.exception("Could not save document to MongoDB collection %s.", collection_name)
        return False
    finally:
        if client is not None:
            client.close()


def mongo_health():
    if not settings.MONGODB_URI:
        return "not_configured"

    from pymongo import MongoClient

    client = None
    try:
        client = MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=1500,
            connectTimeoutMS=1500,
        )
        client.admin.command("ping")
        return "ok"
    except (PyMongoError, ValueError):
        logger.exception("MongoDB health check failed.")
        return "unavailable"
    finally:
        if client is not None:
            client.close()
