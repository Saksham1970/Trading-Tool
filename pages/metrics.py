from app_config import app
from utils.config import SETTINGS, SETTINGS_FILE
from utils.file_handling import save_json
from flask import request, jsonify


@app.route("/add_rvol", methods=["GET"])
def add_rvol():
    req = request.json
    if "RVols" not in SETTINGS:
        SETTINGS["RVols"] = []
    SETTINGS["RVols"].append(req["rvol"])

    save_json(SETTINGS_FILE, SETTINGS)
    return jsonify({"status": "success"})


@app.route("/delete_rvol", methods=["GET"])
def delete_rvol():
    req = request.json
    if "RVols" in SETTINGS:
        SETTINGS["RVols"].remove(req["rvol"])

    save_json(SETTINGS_FILE, SETTINGS)
    return jsonify({"status": "success"})


@app.route("/get_rvols", methods=["GET"])
def get_rvols():
    return jsonify(SETTINGS["RVols"])
