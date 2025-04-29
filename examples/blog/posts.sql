-- name: GetPostById :one
-- param: id int The ID of the post to retrieve
SELECT p.*,
       a.name AS author_name,
       a.email AS author_email
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.id = :id;

-- name: ListPosts :many
-- param: limit int The maximum number of posts to return
-- param: offset int The number of posts to skip
SELECT p.*,
       a.name AS author_name,
       a.email AS author_email
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.published = TRUE
ORDER BY p.published_at DESC
LIMIT :limit
OFFSET :offset;

-- name: ListPostsByAuthor :many
-- param: author_id int The ID of the author
-- param: include_unpublished boolean Whether to include unpublished posts
SELECT p.*,
       a.name AS author_name,
       a.email AS author_email
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.author_id = :author_id
  -- { include_unpublished }
  AND (p.published = TRUE OR :include_unpublished)
  -- }
ORDER BY p.created_at DESC;

-- name: CreatePost :one
-- param: author_id int The ID of the post author
-- param: title string The title of the post
-- param: content string The content of the post
-- param: published boolean Whether the post should be published immediately
INSERT INTO posts (
    author_id,
    title,
    content,
    published,
    published_at
)
VALUES (
    :author_id,
    :title,
    :content,
    :published,
    CASE WHEN :published THEN CURRENT_TIMESTAMP ELSE NULL END
)
RETURNING *;

-- name: UpdatePost :one
-- param: id int The ID of the post to update
-- param: title string The title of the post
-- param: content string The content of the post
UPDATE posts
SET title = :title,
    content = :content,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id
RETURNING *;

-- name: PublishPost :one
-- param: id int The ID of the post to publish
UPDATE posts
SET published = TRUE,
    published_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id
RETURNING *;

-- name: UnpublishPost :one
-- param: id int The ID of the post to unpublish
UPDATE posts
SET published = FALSE,
    published_at = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id
RETURNING *;

-- name: DeletePost :exec
-- param: id int The ID of the post to delete
DELETE FROM posts WHERE id = :id;

-- name: SearchPosts :many
-- param: query string The search query
-- param: published_only boolean Whether to only include published posts
SELECT p.*,
       a.name AS author_name,
       a.email AS author_email
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE (p.title ILIKE '%' || :query || '%' OR p.content ILIKE '%' || :query || '%')
  -- { published_only }
  AND p.published = TRUE
  -- }
ORDER BY
  CASE
    WHEN p.title ILIKE :query THEN 0
    WHEN p.title ILIKE :query || '%' THEN 1
    WHEN p.title ILIKE '%' || :query || '%' THEN 2
    ELSE 3
  END,
  p.published_at DESC NULLS LAST;
