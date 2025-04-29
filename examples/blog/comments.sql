-- name: GetCommentById :one
-- param: id int The ID of the comment to retrieve
SELECT * FROM comments WHERE id = :id;

-- name: ListCommentsByPost :many
-- param: post_id int The ID of the post
-- param: approved_only boolean Whether to only include approved comments
SELECT * FROM comments
WHERE post_id = :post_id
  -- { approved_only }
  AND approved = TRUE
  -- }
ORDER BY created_at;

-- name: CreateComment :one
-- param: post_id int The ID of the post being commented on
-- param: author_name string The name of the comment author
-- param: author_email string The email of the comment author
-- param: content string The content of the comment
-- param: auto_approve boolean Whether to automatically approve the comment
INSERT INTO comments (
    post_id,
    author_name,
    author_email,
    content,
    approved
)
VALUES (
    :post_id,
    :author_name,
    :author_email,
    :content,
    :auto_approve
)
RETURNING *;

-- name: ApproveComment :one
-- param: id int The ID of the comment to approve
UPDATE comments
SET approved = TRUE
WHERE id = :id
RETURNING *;

-- name: DeleteComment :exec
-- param: id int The ID of the comment to delete
DELETE FROM comments WHERE id = :id;

-- name: GetCommentCountByPost :one
-- param: post_id int The ID of the post
SELECT COUNT(*) AS total_comments,
       COUNT(*) FILTER (WHERE approved = TRUE) AS approved_comments
FROM comments
WHERE post_id = :post_id;
