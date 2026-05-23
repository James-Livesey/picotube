CREATE TABLE IF NOT EXISTS users (
    uid varchar(16) PRIMARY KEY,
    username varchar(20) NOT NULL,
    display_username varchar(20) NOT NULL,
    email varchar(255) NOT NULL,
    password varchar(60) NOT NULL,
    created_time integer NOT NULL,
    email_verified boolean DEFAULT FALSE,
    last_email_verification_sent_time integer,
    admin boolean DEFAULT FALSE,
    banned boolean DEFAULT FALSE,
    ban_reason varchar(500),
    network_id varchar(64),
    favourite_colour integer
);

CREATE TABLE IF NOT EXISTS videos (
    video_id varchar(16) PRIMARY KEY,
    author varchar(16) REFERENCES users(uid) NOT NULL,
    title varchar(100),
    description varchar(2000),
    created_time integer NOT NULL,
    published boolean DEFAULT FALSE,
    removed boolean DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS video_variants (
    variant_id varchar(16) PRIMARY KEY,
    video varchar(16) REFERENCES videos(video_id) NOT NULL,
    type varchar(16) DEFAULT 'original',
    display_name varchar(50),
    transcoder_status integer DEFAULT 0
);

CREATE TABLE IF NOT EXISTS video_subtitles (
    subtitles_id varchar(16) PRIMARY KEY,
    video varchar(16) REFERENCES videos(video_id) NOT NULL,
    type varchar(16) DEFAULT 'original',
    display_name varchar(50)
);