/**
 * Example of using the generated JavaScript code to interact with the blog database.
 */
const { createClient, createTransaction } = require('./generated/javascript');
const { GetAuthorById, ListAuthors, CreateAuthor, UpdateAuthor, DeleteAuthor } = require('./generated/javascript/authors');
const { CreatePost, PublishPost, ListPosts, UpdatePost, DeletePost } = require('./generated/javascript/posts');
const { CreateComment, ApproveComment, ListCommentsByPost, DeleteComment } = require('./generated/javascript/comments');
// Import utility functions for telemetry and logging
const { logger, configureMonitoring } = require('./generated/javascript/utils');

async function main() {
  console.log('Blog Database Example (JavaScript)');
  console.log('-'.repeat(50));
  
  // Configure logging
  logger.setLevel('debug');
  logger.setLogger({
    error: (...args) => console.error(new Date().toISOString(), '[ERROR]', ...args),
    warn: (...args) => console.warn(new Date().toISOString(), '[WARN]', ...args),
    info: (...args) => console.info(new Date().toISOString(), '[INFO]', ...args),
    debug: (...args) => console.debug(new Date().toISOString(), '[DEBUG]', ...args)
  });
  

  console.log('Custom logger configured');
  
  // Configure basic telemetry to measure query performance
  configureMonitoring('basic');
  console.log('Telemetry enabled: Basic monitoring mode');
  
  // Database connection configuration - replace with your actual connection details
  const connectionString = 'postgresql://postgres:1234@localhost:5433/blog';
  const client = await createClient(connectionString);

  try {
    // Example 1: List all authors
    console.log('\n1. Listing all authors:');
    const [authors, listExecTime] = await ListAuthors(client);
    console.log(`  Query completed in ${listExecTime.toFixed(3)}s`);
    authors.forEach(author => {
      console.log(`  - ${author.name} (${author.email})`);
    });
    
    // Example 2: Create a new author
    console.log('\n2. Creating a new author:');
    const timestamp = new Date().getTime();
    const [result, createExecTime] = await CreateAuthor(client, {
      name: 'Chris Taylor',
      email: `chris.taylor.${timestamp}@example.com`,
      bio: 'Web developer and technical writer.'
    });
    console.log(`  Created author: ${result[0].name} (ID: ${result[0].id}) in ${createExecTime.toFixed(3)}s`);
    
    // Example 3: Get author by ID
    console.log('\n3. Getting author by ID:');
    const [author, execTime2] = await GetAuthorById(client, { id: result[0].id });
    console.log(`  Found author: ${author[0].name} - ${author[0].bio} in ${execTime2.toFixed(3)}s`);
    
    // Example 4: Create a new post
    console.log('\n4. Creating a new post:');
    const [post, execTime3] = await CreatePost(client, {
      author_id: result[0].id,
      title: 'Getting Started with Team Query',
      content: 'This is a sample blog post created using team-query.',
      published: false
    });
    console.log(`  Created post: ${post[0].title} (ID: ${post[0].id}) in ${execTime3.toFixed(3)}s`);
    
    // Example 5: Publish the post
    console.log('\n5. Publishing the post:');
    const [published, execTime4] = await PublishPost(client, { id: post[0].id });
    const publishedDate = new Date(published[0].published_at).toLocaleString();
    console.log(`  Post published at: ${publishedDate} in ${execTime4.toFixed(3)}s`);
    
    // Example 6: List recent posts
    console.log('\n6. Listing recent posts:');
    const [posts, execTime5] = await ListPosts(client, { limit: 10, offset: 0 });
    console.log(`  Query completed in ${execTime5.toFixed(3)}s`);
    posts.forEach(post => {
      console.log(`  - ${post.title} by ${post.author_name} (${post.published_at})`);
    });
    
    // Example 7: Demonstrate transaction support
    console.log('\n7. Using transactions to add comments:');
    const txn = await createTransaction(client);
    
    try {
      await txn.begin();
      
      // Add a comment within the transaction
      const [comment1Result] = await txn.execute(client => 
        CreateComment(client, {
          post_id: post[0].id,
          author_name: 'Transaction User 1',
          author_email: 'user1@example.com',
          content: 'This comment was added in a transaction.',
          auto_approve: true
        })
      );
      console.log(`  Added comment 1: ${comment1Result[0].id}`);
      
      // Add another comment within the same transaction
      const [comment2Result] = await txn.execute(client => 
        CreateComment(client, {
          post_id: post[0].id,
          author_name: 'Transaction User 2',
          author_email: 'user2@example.com',
          content: 'This is another comment in the same transaction.',
          auto_approve: false
        })
      );
      console.log(`  Added comment 2: ${comment2Result[0].id}`);
      
      // Approve the second comment
      const [approvedResult] = await txn.execute(client => 
        ApproveComment(client, { id: comment2Result[0].id })
      );
      console.log(`  Approved comment 2: ${approvedResult[0].id}`);
      
      // Commit the transaction
      await txn.commit();
      console.log('  Transaction committed successfully');
      
      // List comments for the post
      const [postComments] = await ListCommentsByPost(client, { post_id: post[0].id });
      console.log(`\n8. Comments for post "${post[0].title}":`);
      postComments.forEach(comment => {
        console.log(`  - ${comment.author_name}: ${comment.content}`);
      });
      
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
