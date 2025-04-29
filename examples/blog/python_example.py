"""
Example of using the generated Python code to interact with the blog database.
"""
import sys
import psycopg
from datetime import datetime

# Import from the generated modules
from generated.python.authors import GetAuthorById, ListAuthors, CreateAuthor, UpdateAuthor, DeleteAuthor
from generated.python.posts import GetPostById, ListPosts, CreatePost, PublishPost, UpdatePost, DeletePost
from generated.python.comments import ListCommentsByPost, CreateComment, ApproveComment, DeleteComment
# Import utility functions for telemetry
from generated.python.utils import set_log_level, configure_monitoring

def main():
    """Main function to demonstrate the usage of generated code."""
    print("Blog Database Example (Python)")
    print("-" * 50)
    
    # Enable debug logging to see query information
    set_log_level("DEBUG")
    
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
            authors = ListAuthors(conn)
            for author in authors:
                print(f"  - {author['name']} ({author['email']})")
            
            # Example 2: Create a new author
            print("\n2. Creating a new author:")
            new_author = CreateAuthor(conn, 
                name="Sam Wilson",
                email="sam@example.com",
                bio="Technology enthusiast and blogger."
            )
            print(f"  Created author: {new_author[0]['name']} (ID: {new_author[0]['id']})")
            
            # Example 3: Get author by ID
            print("\n3. Getting author by ID:")
            author = GetAuthorById(conn, id=new_author[0]['id'])
            print(f"  Found author: {author[0]['name']} - {author[0]['bio']}")
            
            # Example 4: Create a new post
            print("\n4. Creating a new post:")
            new_post = CreatePost(conn, 
                author_id=new_author[0]['id'],
                title="My First Blog Post",
                content="This is the content of my first blog post using team-query.",
                published=False
            )
            print(f"  Created post: {new_post[0]['title']} (ID: {new_post[0]['id']})")
            
            # Example 5: Publish the post
            print("\n5. Publishing the post:")
            published_post = PublishPost(conn, id=new_post[0]['id'])
            published_date = published_post[0]['published_at'].strftime("%Y-%m-%d %H:%M:%S")
            print(f"  Post published at: {published_date}")
            
            # Example 6: List all posts
            print("\n6. Listing all posts:")
            posts = ListPosts(conn, limit=10, offset=0)
            for post in posts:
                published_status = "Published" if post['published'] else "Draft"
                print(f"  - {post['title']} by {post['author_name']} ({published_status})")
            
            # Example 7: Create a comment
            print("\n7. Creating a comment:")
            new_comment = CreateComment(conn,
                post_id=new_post[0]['id'],
                author_name="Reader One",
                author_email="reader@example.com",
                content="Great first post! Looking forward to more content.",
                auto_approve=False
            )
            print(f"  Comment created (ID: {new_comment[0]['id']})")
            
            # Example 8: Approve the comment
            print("\n8. Approving the comment:")
            approved_comment = ApproveComment(conn, id=new_comment[0]['id'])
            print(f"  Comment approved: {approved_comment[0]['approved']}")
            
            # Example 9: List comments for a post
            print("\n9. Listing comments for the post:")
            comments = ListCommentsByPost(conn, post_id=new_post[0]['id'])
            for comment in comments:
                approved_status = "Approved" if comment['approved'] else "Pending"
                print(f"  - {comment['author_name']}: {comment['content']} ({approved_status})")
            
            # Example 10: Update the author
            print("\n10. Updating the author:")
            updated_author = UpdateAuthor(conn,
                id=new_author[0]['id'],
                name="Samuel Wilson",
                email="samuel@example.com",
                bio="Technology enthusiast, blogger, and software developer."
            )
            print(f"  Updated author: {updated_author[0]['name']} - {updated_author[0]['bio']}")
            
            # Example 11: Update the post
            print("\n11. Updating the post:")
            updated_post = UpdatePost(conn,
                id=new_post[0]['id'],
                title="My First Blog Post - Updated",
                content="This is the updated content of my first blog post using team-query."
            )
            print(f"  Updated post: {updated_post[0]['title']}")
            
            # Example 12: Delete operations
            print("\n12. Delete operations:")
            print("  Deleting comment...")
            DeleteComment(conn, id=new_comment[0]['id'])
            print(f"    - Deleted comment ID: {new_comment[0]['id']}")
            
            print("  Deleting post...")
            DeletePost(conn, id=new_post[0]['id'])
            print(f"    - Deleted post ID: {new_post[0]['id']}")
            
            print("  Deleting author...")
            DeleteAuthor(conn, id=new_author[0]['id'])
            print(f"    - Deleted author ID: {new_author[0]['id']}")
            
            print("\nAll examples completed successfully!")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
