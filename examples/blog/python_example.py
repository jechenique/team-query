"""
Example of using the generated Python code to interact with the blog database.
"""
import sys
import logging
import psycopg
from datetime import datetime

# Import from the generated modules
from generated.python.authors import GetAuthorById, ListAuthors, CreateAuthor, UpdateAuthor, DeleteAuthor
from generated.python.posts import GetPostById, ListPosts, CreatePost, PublishPost, UpdatePost, DeletePost
from generated.python.comments import ListCommentsByPost, CreateComment, ApproveComment, DeleteComment
# Import utility functions for telemetry and logging
from generated.python.utils import set_log_level, configure_monitoring, set_logger, Logger

def main():
    """Main function to demonstrate the usage of generated code."""
    print("Blog Database Example (Python)")
    print("-" * 50)
    
    # Create a custom logger with a different format
    custom_logger = logging.getLogger('custom_blog_logger')
    custom_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)
    custom_logger.addHandler(handler)
    
    # Set our custom logger
    set_logger(custom_logger)
    print("Custom logger configured")
    
    # Configure basic telemetry to measure query performance
    configure_monitoring("basic")
    print("Telemetry enabled: Basic monitoring mode")
    
    # Database connection string - replace with your actual connection details
    conn_string = "postgresql://postgres:1234@localhost:5433/blog"
    
    try:
        # Connect to the database
        with psycopg.connect(conn_string) as conn:
            # Example 1: List all authors
            print("\n1. Listing all authors:")
            authors, _ = ListAuthors(conn)
            for author in authors:
                print(f"  - {author['name']} ({author['email']})")
            
            # Example 2: Create a new author
            print("\n2. Creating a new author:")
            author_result, exec_time = CreateAuthor(conn, 
                name="Sam Wilson",
                email="sam@example.com",
                bio="Technology enthusiast and blogger."
            )
            author_id = author_result[0]['id']  # Store author ID for later use
            print(f"  Created author: {author_result[0]['name']} (ID: {author_id}) in {exec_time:.3f}s")
            
            # Example 3: Get author by ID
            print("\n3. Getting author by ID:")
            result, exec_time = GetAuthorById(conn, id=author_id)
            print(f"  Found author: {result[0]['name']} - {result[0]['bio']} in {exec_time:.3f}s")
            
            # Example 4: Create a new post
            print("\n4. Creating a new post:")
            post_result, exec_time = CreatePost(conn, 
                author_id=author_id,
                title="My First Blog Post",
                content="This is the content of my first blog post using team-query.",
                published=False
            )
            post_id = post_result[0]['id']  # Store post ID for later use
            print(f"  Created post: {post_result[0]['title']} (ID: {post_id}) in {exec_time:.3f}s")
            
            # Example 5: Publish the post
            print("\n5. Publishing the post:")
            result, exec_time = PublishPost(conn, id=post_id)
            published_date = result[0]['published_at'].strftime("%Y-%m-%d %H:%M:%S")
            print(f"  Post published at: {published_date} in {exec_time:.3f}s")
            
            # Example 6: List all posts
            print("\n6. Listing all posts:")
            posts, _ = ListPosts(conn, limit=10, offset=0)
            for post in posts:
                published_status = "Published" if post['published'] else "Draft"
                print(f"  - {post['title']} by {post['author_name']} ({published_status})")
            
            # Example 7: Create a comment
            print("\n7. Creating a comment:")
            comment_result, comment_exec_time = CreateComment(conn,
                post_id=post_id,
                author_name="Reader One",
                author_email="reader@example.com",
                content="Great first post! Looking forward to more content.",
                auto_approve=False
            )
            print(f"  Comment created (ID: {comment_result[0]['id']}) in {comment_exec_time:.3f}s")
            
            # Example 8: Approve the comment
            print("\n8. Approving the comment:")
            approve_result, approve_exec_time = ApproveComment(conn, id=comment_result[0]['id'])
            print(f"  Comment approved: {approve_result[0]['approved']} in {approve_exec_time:.3f}s")
            
            # Example 9: List comments for a post
            print("\n9. Listing comments for the post:")
            comments, list_exec_time = ListCommentsByPost(conn, post_id=post_id)
            print(f"  Query completed in {list_exec_time:.3f}s")
            for comment in comments:
                approved_status = "Approved" if comment['approved'] else "Pending"
                print(f"  - {comment['author_name']}: {comment['content']} ({approved_status})")
            
            # Example 10: Update the author
            print("\n10. Updating the author:")
            author_result, author_exec_time = UpdateAuthor(conn,
                id=author_id,
                name="Samuel Wilson",
                email="samuel@example.com",
                bio="Technology enthusiast, blogger, and software developer."
            )
            print(f"  Updated author: {author_result[0]['name']} - {author_result[0]['bio']} in {author_exec_time:.3f}s")
            
            # Example 11: Update the post
            print("\n11. Updating the post:")
            post_result, post_exec_time = UpdatePost(conn,
                id=post_id,
                title="My First Blog Post - Updated",
                content="This is the updated content of my first blog post using team-query."
            )
            print(f"  Updated post: {post_result[0]['title']} in {post_exec_time:.3f}s")
            
            # Example 12: Delete operations
            print("\n12. Delete operations:")
            print("  Deleting comment...")
            del_result, del_exec_time = DeleteComment(conn, id=comment_result[0]['id'])
            print(f"    - Deleted comment ID: {comment_result[0]['id']} in {del_exec_time:.3f}s")
            
            print("  Deleting post...")
            del_result, del_exec_time = DeletePost(conn, id=post_id)
            print(f"    - Deleted post ID: {post_id} in {del_exec_time:.3f}s")
            
            print("  Deleting author...")
            del_result, del_exec_time = DeleteAuthor(conn, id=author_id)
            print(f"    - Deleted author ID: {author_id} in {del_exec_time:.3f}s")
            
            print("\nAll examples completed successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
