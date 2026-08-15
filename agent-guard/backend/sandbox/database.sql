-- Database Schema Initialization File -- DO NOT DELETE --
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (email, password_hash) VALUES ('admin@example.com', 'hashed_secret_password');
