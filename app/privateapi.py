import logging
from flask import Blueprint, request, abort, jsonify

import config
import db

privateapi = Blueprint("privateapi", __name__)
logger = logging.getLogger()

def is_authorised(request):
    return request.headers.get("Authorization") == "Bearer " + config.private_api_secret

@privateapi.route("/privateapi/uploadqueue")
def transcoder_jobs():
    if not is_authorised(request):
        return abort(403)

    try:
        db.lock.acquire(True)

        variants = []

        for row in db.cursor.execute("SELECT variant_id, video, transcoder_status FROM video_variants WHERE transcoder_status = 0 LIMIT 10").fetchall():
            variants.append({
                "variant_id": row[0],
                "video_id": row[1],
                "transcoder_status": row[2]
            })

        return jsonify({
            "variants": variants
        })
    except Exception as e:
        logger.error("Cannot get upload queue: %s", e)

        return abort(500)
    finally:
        db.lock.release()

@privateapi.route("/privateapi/uploadqueue/<variant_id>", methods=["PUT"])
def transcoder_variant(variant_id):
    if not is_authorised(request):
        return abort(403)

    try:
        db.lock.acquire(True)
    
        data = request.get_json()

        if isinstance(data.get("transcoder_status"), int):
            db.cursor.execute("UPDATE video_variants SET transcoder_status = ? WHERE variant_id = ?", [data.get("transcoder_status"), variant_id])

            if data.get("transcoder_status") == 2:
                row = db.cursor.execute("SELECT video FROM video_variants WHERE variant_id = ?", [variant_id]).fetchone()

                if row is not None:
                    db.cursor.execute("UPDATE videos SET processing_done = TRUE WHERE video_id = ?", [row[0]])

        db.connection.commit()

        return jsonify({}), 200
    except Exception as e:
        logger.error("Cannot update upload in queue: %s", e)

        return abort(500)
    finally:
        db.lock.release()