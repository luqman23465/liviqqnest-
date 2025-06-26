DROP TABLE IF EXISTS properties;

CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('sale', 'rent')), -- Ensures status is one of these
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optional: Add some initial data for testing if the table is empty
-- This is commented out as initial data is handled in app.py for now, or can be added manually.
/*
INSERT INTO properties (name, description, price, status, image_url) VALUES
    ('Ocean View Mansion', 'Luxurious mansion with panoramic ocean views.', 2500000.00, 'sale', 'static/images/mansion.jpg'),
    ('Downtown Loft', 'Chic loft in the heart of the city.', 3000.00, 'rent', 'static/images/loft.jpg'),
    ('Suburban Family Home', 'Spacious home perfect for families, large backyard.', 650000.00, 'sale', 'static/images/familyhome.jpg');
*/
