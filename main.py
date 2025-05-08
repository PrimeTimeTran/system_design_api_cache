from flask import Flask, request, jsonify
import redis
import hashlib
from datetime import datetime

app = Flask(__name__)
cache = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

CACHE_TIMEOUT = 5


def cache_key():
    key = request.full_path
    return hashlib.sha256(key.encode()).hexdigest()


@app.route("/data", methods=["GET"])
def get_data():
    key = cache_key()
    cached_response = cache.hgetall(key)

    if cached_response:
        cache_timestamp = cached_response["timestamp"]
        expiration_time = (
            CACHE_TIMEOUT
            - (datetime.now() - datetime.fromisoformat(cache_timestamp)).seconds
        )

        return jsonify(
            {
                "source": "cache",
                "data": cached_response["message"],
                "cached_at": cache_timestamp,
                "expires_in_seconds": max(expiration_time, 0),
            }
        )

    data = {"message": f"Hello, this is fresh data at {datetime.now().isoformat()}"}
    timestamp = datetime.now().isoformat()
    cache.hmset(key, {"message": data["message"], "timestamp": timestamp})
    cache.expire(key, CACHE_TIMEOUT)
    return jsonify(
        {
            "source": "database",
            "data": data["message"],
            "cached_at": timestamp,
            "expires_in_seconds": CACHE_TIMEOUT,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
