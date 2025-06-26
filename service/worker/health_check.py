import os
from flask import Flask, Response

app = Flask(__name__)

@app.route('/')
def health_check():
    version = os.getenv("GIT_SHA", "0.0.0")
    environment = os.getenv("ENVIRONMENT", "development")
    return Response(f"Environment: {environment}, Version: {version}", status=200) 