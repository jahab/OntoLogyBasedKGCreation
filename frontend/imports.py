from enum import Enum

class Environment(Enum):
    DEBUG = 1
    DEPLOY = 2

env_type = Environment.DEBUG

if env_type == Environment.DEBUG:
    MONGO_URL = "mongodb://localhost:27017"
    BACKEND = "http://localhost:5000"
    UPLOAD_DIR = "data/"
    FETCH_GRAPH_URL = "http://localhost:4044/fetch_graph"
    CREATE_GRAPH_URL = "http://localhost:4044/create_graph"
else:
    MONGO_URL = "mongodb://mongodb:27017"
    BACKEND = "http://login-service:5000"
    UPLOAD_DIR = "/data/"
    FETCH_GRAPH_URL = "http://kg_app:4044/fetch_graph"
    CREATE_GRAPH_URL = "http://kg_app:4044/create_graph"
    