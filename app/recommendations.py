import logging

import db

logger = logging.getLogger()

def get_recommendations(filters=[], positionals=[], limit=8):
    try:
        db.lock.acquire(True)

        fields = [
            ["video_id", "videos.video_id"],
            ["author", "videos.author"],
            ["author_display_username", "users.display_username"],
            ["title", "videos.title"],
            ["created_time", "videos.created_time"],
            ["duration", "videos.duration"]
        ]

        filters.insert(0, "videos.published")
        filters.insert(0, "videos.processing_done")
        filters.insert(0, "NOT videos.removed")

        rows = db.cursor.execute(
            f"SELECT {', '.join(map(lambda field: field[1], fields))} FROM videos "
            f"LEFT JOIN users ON videos.author = users.uid "
            f"WHERE {' AND '.join(filters)} LIMIT {limit}",
            positionals
        )

        videos = []

        for row in rows:
            video = {}

            for i in range(0, len(fields)):
                video[fields[i][0]] = row[i]

            duration_secs = video["duration"] // 1000
            video["duration_time"] = f"{duration_secs // 60}:{str(duration_secs % 60).zfill(2)}"

            videos.append(video)

        return videos
    finally:
        db.lock.release()