/**
 * Example of using the generated JavaScript code to interact with the blog database.
 */
const { createClient, createTransaction } = require('./generated/javascript');
const { GetAuthorById, ListAuthors, CreateAuthor, UpdateAuthor, DeleteAuthor } = require('./generated/javascript/authors');
const { CreatePost, PublishPost, ListPosts, UpdatePost, DeletePost } = require('./generated/javascript/posts');
const { CreateComment, ApproveComment, ListCommentsByPost, DeleteComment } = require('./generated/javascript/comments');
// Import utility functions for telemetry
const { setLogLevel, configureMonitoring } = require('./generated/javascript/utils');

async function main() {
  console.log('Blog Database Example (JavaScript)');
  console.log('-'.repeat(50));
  
  // Enable debug logging to see query information
  setLogLevel('debug');
  
  // Configure basic telemetry to measure query performance
  configureMonitoring('basic');
  console.log('Telemetry enabled: Basic monitoring mode');
  
  // Database connection configuration - replace with your actual connection details
  const connectionString = 'postgresql://postgres:1234@localhost:5433/blog';
  const client = await createClient(connectionString);

  try {
    // Example 1: List all authors
    console.log('\n1. Listing all authors:');
    const authorsList = await ListAuthors(client);
    authorsList.forEach(author => {
      console.log(`  - ${author.name} (${author.email})`);
    });
    
    // Example 2: Create a new author
    console.log('\n2. Creating a new author:');
    const newAuthor = await CreateAuthor(client, {
      name: 'Chris Taylor',
      email: 'chris@example.com',
      bio: 'Web developer and technical writer.'
    });
    console.log(`  Created author: ${newAuthor[0].name} (ID: ${newAuthor[0].id})`);
    
    // Example 3: Get author by ID
    console.log('\n3. Getting author by ID:');
    const author = await GetAuthorById(client, { id: newAuthor[0].id });
    console.log(`  Found author: ${author[0].name} - ${author[0].bio}`);
    
    // Example 4: Create a new post
    console.log('\n4. Creating a new post:');
    const newPost = await CreatePost(client, {
      author_id: newAuthor[0].id,
      title: 'JavaScript and Team Query',
      content: 'This post demonstrates how to use team-query with JavaScript.',
      published: false
    });
    console.log(`  Created post: ${newPost[0].title} (ID: ${newPost[0].id})`);
    
    // Example 5: Publish the post
    console.log('\n5. Publishing the post:');
    const publishedPost = await PublishPost(client, { id: newPost[0].id });
    console.log(`  Published post: ${publishedPost[0].title} at ${publishedPost[0].published_at}`);
    
    // Example 6: List recent posts
    console.log('\n6. Listing recent posts:');
    const recentPosts = await ListPosts(client, { limit: 5, offset: 0 });
    recentPosts.forEach(post => {
      console.log(`  - ${post.title} by ${post.author_name} (${post.published_at})`);
    });
    
    // Example 7: Demonstrate transaction support
    console.log('\n7. Using transactions to add comments:');
    const txn = await createTransaction(client);
    
    try {
      await txn.begin();
      
      // Add a comment within the transaction
      const comment1 = await txn.execute(client => 
        CreateComment(client, {
          post_id: newPost[0].id,
          author_name: 'Transaction User 1',
          author_email: 'user1@example.com',
          content: 'This comment was added in a transaction.',
          auto_approve: true
        })
      );
      console.log(`  Added comment 1: ${comment1[0].id}`);
      
      // Add another comment within the same transaction
      const comment2 = await txn.execute(client => 
        CreateComment(client, {
          post_id: newPost[0].id,
          author_name: 'Transaction User 2',
          author_email: 'user2@example.com',
          content: 'This is another comment in the same transaction.',
          auto_approve: false
        })
      );
      console.log(`  Added comment 2: ${comment2[0].id}`);
      
      // Approve the second comment
      const approvedComment = await txn.execute(client => 
        ApproveComment(client, { id: comment2[0].id })
      );
      console.log(`  Approved comment 2: ${approvedComment[0].id}`);
      
      // Commit the transaction
      await txn.commit();
      console.log('  Transaction committed successfully');
      
      // List comments for the post
      const postComments = await ListCommentsByPost(client, { post_id: newPost[0].id });
      console.log(`\n8. Comments for post "${newPost[0].title}":`);
      postComments.forEach(comment => {
        console.log(`  - ${comment.author_name}: ${comment.content}`);
      });
      
      // Example 9: Update author information
      console.log('\n9. Updating author information:');
      const updatedAuthor = await UpdateAuthor(client, {
        id: newAuthor[0].id,
        name: 'Christopher Taylor',
        email: 'christopher@example.com',
        bio: 'Web developer, technical writer, and open source contributor.'
      });
      console.log(`  Updated author: ${updatedAuthor[0].name} (${updatedAuthor[0].email})`);
      console.log(`  New bio: ${updatedAuthor[0].bio}`);
      
      // Example 10: Update post content
      console.log('\n10. Updating post content:');
      const updatedPost = await UpdatePost(client, {
        id: newPost[0].id,
        title: 'JavaScript and Team Query - Updated',
        content: 'This updated post demonstrates how to use team-query with JavaScript. Now with more details!'
      });
      console.log(`  Updated post: ${updatedPost[0].title}`);
      console.log(`  New content: ${updatedPost[0].content.substring(0, 50)}...`);
      
      // Example 11: Cleanup - Delete all created data
      console.log('\n11. Cleaning up - Deleting created data:');
      
      // Delete comments first (due to foreign key constraints)
      console.log('  Deleting comments...');
      for (const comment of postComments) {
        if (comment.post_id === newPost[0].id) {
          await DeleteComment(client, { id: comment.id });
          console.log(`    - Deleted comment ID: ${comment.id}`);
        }
      }
      
      // Delete the comments we added in the transaction
      await DeleteComment(client, { id: comment1[0].id });
      console.log(`    - Deleted comment ID: ${comment1[0].id}`);
      
      await DeleteComment(client, { id: comment2[0].id });
      console.log(`    - Deleted comment ID: ${comment2[0].id}`);
      
      // Delete posts next
      console.log('  Deleting posts...');
      await DeletePost(client, { id: newPost[0].id });
      console.log(`    - Deleted post ID: ${newPost[0].id}`);
      
      // Finally delete authors
      console.log('  Deleting authors...');
      await DeleteAuthor(client, { id: newAuthor[0].id });
      console.log(`    - Deleted author ID: ${newAuthor[0].id}`);
      
    } catch (error) {
      // Rollback the transaction on error
      await txn.rollback();
      console.error('  Transaction failed:', error);
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    // Close the database connection
    if (client && client.end) {
      console.log('\nClosing database connection...');
      await client.end();
      console.log('Database connection closed.');
    }
  }
}

// Run the example
main();
