-- name: GetAuthorById :one
-- param: id int The ID of the author to retrieve
SELECT * FROM authors WHERE id = :id;

-- name: ListAuthors :many
-- Returns a list of all authors
SELECT * FROM authors ORDER BY name;

-- name: CreateAuthor :one
-- param: name string The author's full name
-- param: email string The author's email address
-- param: bio string The author's biography
INSERT INTO authors (name, email, bio)
VALUES (:name, :email, :bio)
RETURNING *;

-- name: UpdateAuthor :one
-- param: id int The ID of the author to update
-- param: name string The author's full name
-- param: email string The author's email address
-- param: bio string The author's biography
UPDATE authors
SET name = :name,
    email = :email,
    bio = :bio
WHERE id = :id
RETURNING *;

-- name: DeleteAuthor :exec
-- param: id int The ID of the author to delete
DELETE FROM authors WHERE id = :id;

-- name: GetAuthorWithPostCount :one
-- param: id int The ID of the author
SELECT a.*,
       COUNT(p.id) AS post_count,
       COUNT(p.id) FILTER (WHERE p.published = TRUE) AS published_post_count
FROM authors a
LEFT JOIN posts p ON a.id = p.author_id
WHERE a.id = :id
GROUP BY a.id;

-- name: SearchAuthors :many
-- param: query string The search query
SELECT * FROM authors
WHERE name ILIKE '%' || :query || '%'
   OR email ILIKE '%' || :query || '%'
   OR bio ILIKE '%' || :query || '%'
ORDER BY name;
