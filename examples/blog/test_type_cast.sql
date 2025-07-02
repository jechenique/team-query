-- name: GetPostsWithVector :many
-- param: embedding vector The embedding to search with
-- param: limit int The number of posts to return
SELECT 
    p.id, 
    p.title, 
    p.content,
    1 - (p.embedding <=> :embedding::vector) AS similarity
FROM posts p
WHERE p.embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT :limit;
