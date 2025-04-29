-- Seed data for blog example

-- Insert authors
INSERT INTO authors (name, email, bio) VALUES
('Jane Smith', 'jane@example.com', 'Tech blogger and software engineer with 10 years of experience.'),
('John Doe', 'john@example.com', 'Fiction writer and poet. Published author of three novels.'),
('Alice Johnson', 'alice@example.com', 'Data scientist and AI researcher. PhD in Computer Science.');

-- Insert posts
INSERT INTO posts (author_id, title, content, published, published_at) VALUES
(1, 'Getting Started with Team Query', 'Team Query is a powerful tool for managing SQL queries in your codebase...', TRUE, NOW() - INTERVAL '10 days'),
(1, 'Advanced SQL Techniques', 'In this post, we will explore some advanced SQL techniques that can help you optimize your database queries...', TRUE, NOW() - INTERVAL '5 days'),
(2, 'The Art of Storytelling', 'Storytelling is an ancient art form that has been used throughout human history...', TRUE, NOW() - INTERVAL '7 days'),
(2, 'Writing Effective Dialogue', 'Dialogue is one of the most important elements of fiction writing...', FALSE, NULL),
(3, 'Introduction to Machine Learning', 'Machine learning is a subset of artificial intelligence that focuses on...', TRUE, NOW() - INTERVAL '3 days'),
(3, 'Data Visualization Best Practices', 'Effective data visualization is crucial for communicating insights...', TRUE, NOW() - INTERVAL '1 day');

-- Insert comments
INSERT INTO comments (post_id, author_name, author_email, content, approved) VALUES
(1, 'Bob Wilson', 'bob@example.com', 'Great introduction! Looking forward to trying Team Query.', TRUE),
(1, 'Sarah Lee', 'sarah@example.com', 'Does Team Query support PostgreSQL extensions?', TRUE),
(2, 'Michael Brown', 'michael@example.com', 'These techniques saved me hours of work. Thanks!', TRUE),
(3, 'Emily Davis', 'emily@example.com', 'I never thought about storytelling this way before.', TRUE),
(5, 'David Clark', 'david@example.com', 'Clear explanation of machine learning concepts.', TRUE),
(5, 'Lisa Wang', 'lisa@example.com', 'Could you elaborate more on neural networks in a future post?', TRUE),
(6, 'James Wilson', 'james@example.com', 'I applied these visualization tips to my project and got great feedback!', TRUE),
(6, 'Olivia Martinez', 'olivia@example.com', 'What tools do you recommend for data visualization?', FALSE);
