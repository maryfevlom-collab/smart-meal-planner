CREATE DATABASE recipe_db
USE recipe_db;

CREATE TABLE community_recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    ingredients TEXT,
    instructions TEXT,
    budget DECIMAL(10,2),
    user_email VARCHAR(255)
);

CREATE TABLE recipe_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT,
    rating INT,
    FOREIGN KEY (recipe_id) REFERENCES community_recipes(id)
);