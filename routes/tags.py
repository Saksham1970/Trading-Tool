from app_config import app
from flask import request, jsonify
from utils import database


@app.route("/create_tag", methods=["POST"])
def create_tag():
    req = request.json
    try:
        tag_name = req["tag_name"]
        tag_color = req["tag_color"]

        database.insert_data("Tags", TagName=tag_name, TagColor=tag_color)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/delete_tag", methods=["POST"])
def delete_tag():
    req = request.json
    try:
        tag_id = req["tag_id"]
        database.delete_data("Tags", TagID=tag_id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/get_tags", methods=["GET"])
def get_tags():
    try:
        tags = database.get_data("Tags", __dictionary=True)
        return jsonify({"status": "success", "tags": tags})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/add_alert_tag", methods=["POST"])
def add_alert_tag():
    req = request.json
    try:
        alert_id = req["alert_id"]
        tag_id = req["tag_id"]
        alert = database.get_data(
            "AlertsWatchlist", AlertID=alert_id, __dictionary=True
        )
        tags = alert[0]["tags"]
        if not tags:
            tags = []
        if tag_id not in tags:
            tags.append(tag_id)
            database.cursor.execute(
                "UPDATE AlertsWatchlist SET Tags = %s WHERE AlertID = %s",
                (tags, alert_id),
            )
            database.conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/remove_alert_tag", methods=["POST"])
def remove_alert_tag():
    req = request.json
    try:
        alert_id = req["alert_id"]
        tag_id = req["tag_id"]
        alert = database.get_data(
            "AlertsWatchlist", AlertID=alert_id, __dictionary=True
        )
        tags = alert[0]["tags"]
        if tag_id in tags:
            tags.remove(tag_id)
            database.cursor.execute(
                "UPDATE AlertsWatchlist SET Tags = %s WHERE AlertID = %s",
                (tags, alert_id),
            )
            database.conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
