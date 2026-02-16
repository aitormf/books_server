-- Create the two databases for the microservices
CREATE DATABASE authors_db;
CREATE DATABASE books_db;

-- Connect to authors_db and create extensions
\c authors_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Connect to books_db and create extensions
\c books_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
