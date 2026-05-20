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