-- Создание пользователя для репликации
CREATE USER repl_user REPLICATION LOGIN PASSWORD 'Qq12345';

-- Создание базы данных
CREATE DATABASE db_bot;

-- Переключение на созданную базу данных
\connect db_bot;
CREATE TABLE IF NOT EXISTS email_addresses (
        id SERIAL PRIMARY KEY,
        email VARCHAR(120) UNIQUE
);
CREATE TABLE IF NOT EXISTS phone_numbers (
        id SERIAL PRIMARY KEY,
        phone_number VARCHAR(20) UNIQUE
);
INSERT INTO email_addresses (email) VALUES ('test@example.com');
INSERT INTO email_addresses (email) VALUES ('sergei@ya.ru');
INSERT INTO phone_numbers (phone_number) VALUES ('89775217911');
INSERT INTO phone_numbers (phone_number) VALUES ('89075220961');