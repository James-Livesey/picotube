import logging
from pipelines import common

logger = logging.getLogger(name="transcoder")

def transcode(upload):
    print(upload["variant_id"])

    common.fetch_private_api(
        "/privateapi/uploadqueue/" + upload["variant_id"],
        method="PUT",
        body={
            "transcoder_status": 1
        })

    pass

def run():
    data = common.fetch_private_api("/privateapi/uploadqueue")

    logger.info(data)

    for upload in data["variants"]:
        if upload.get("transcoder_status") == 0:
            transcode(upload)

            break