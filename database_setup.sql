-- Create database
CREATE DATABASE IF NOT EXISTS book_management_uts_db;
USE book_management_uts_db;

-- Books table
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) DEFAULT 'Unknown',
    isbn VARCHAR(13),
    total_copies INT DEFAULT 1,
    available_copies INT DEFAULT 1,
    cover_url VARCHAR(255)
);

-- Insert sample books with cover_url
INSERT INTO books (title, author, isbn, total_copies, available_copies, cover_url) VALUES
('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 5, 5, 'https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg'),
('1984', 'George Orwell', '9780451524935', 3, 3, 'https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg');

-- Create database for loans
CREATE DATABASE IF NOT EXISTS loan_management_uts_db;
USE loan_management_uts_db;

-- Loans table
CREATE TABLE IF NOT EXISTS loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    loan_date DATETIME NOT NULL,
    return_date DATETIME NOT NULL
);

-- Insert sample loan
CREATE TABLE IF NOT EXISTS loans_total (
    book_id INT NOT NULL,
    date DATE NOT NULL,
    borrowed_count INT NOT NULL,
    is_peak_season INT NOT NULL,
    is_low_season INT NOT NULL
);

-- Create database for users
CREATE DATABASE IF NOT EXISTS user_management_uts_db;
USE user_management_uts_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Insert sample user
INSERT INTO users (name, email) VALUES
('John Doe', 'john.doe@example.com');