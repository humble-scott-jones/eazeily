/**
 * Content Type Specific Input Handlers
 * 
 * This file provides reference implementations for collecting and sending
 * content-type-specific data to the generation API.
 * 
 * To integrate into dashboard.js:
 * 1. Add UI panels for each content type (proposal, review_reply, blog_post)
 * 2. Show/hide panels based on task_type selection
 * 3. Collect fields when generating content
 * 4. Pass fields in the POST /api/generate request
 */

/**
 * Collect proposal-specific fields
 */
function collectProposalFields() {
  return {
    proposal_type: document.getElementById('proposal-type')?.value || 'partnership',
    recipient: document.getElementById('proposal-recipient')?.value || '',
    key_benefits: Array.from(document.querySelectorAll('.proposal-benefit'))
      .map(el => el.value)
      .filter(v => v.trim()),
    budget_range: document.getElementById('proposal-budget')?.value || '',
    cta: document.getElementById('proposal-cta')?.value || ''
  };
}

/**
 * Collect review reply-specific fields
 */
function collectReviewReplyFields() {
  return {
    review_source: document.getElementById('review-source')?.value || '',
    star_rating: document.getElementById('review-rating')?.value || '',
    sentiment: document.getElementById('review-sentiment')?.value || 'neutral',
    issue_type: document.getElementById('review-issue-type')?.value || '',
    desired_tone: document.getElementById('review-tone')?.value || 'professional',
    follow_up_action: document.getElementById('review-action')?.value || ''
  };
}

/**
 * Collect blog post-specific fields
 */
function collectBlogPostFields() {
  return {
    post_type: document.getElementById('blog-post-type')?.value || 'how-to',
    desired_length: document.getElementById('blog-length')?.value || 'medium',
    audience: document.getElementById('blog-audience')?.value || '',
    seo_keywords: Array.from(document.querySelectorAll('.blog-keyword'))
      .map(el => el.value)
      .filter(v => v.trim()),
    cta: document.getElementById('blog-cta')?.value || ''
  };
}

/**
 * Enhanced generation function that includes content-type-specific fields
 */
async function generateContentWithTypeFields() {
  const taskType = document.getElementById('task_type')?.value || 'post';
  const topic = document.getElementById('topic')?.value || '';
  const platform = document.getElementById('platform')?.value || '';
  
  // Base payload
  const payload = {
    task_type: taskType,
    topic: topic,
    platform: platform
  };
  
  // Add content-type-specific fields
  if (taskType === 'proposal') {
    Object.assign(payload, collectProposalFields());
  } else if (taskType === 'review_reply') {
    Object.assign(payload, collectReviewReplyFields());
  } else if (taskType === 'blog_post') {
    Object.assign(payload, collectBlogPostFields());
  }
  
  // Send to API
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    throw new Error('Generation failed');
  }
  
  const result = await response.json();
  return result;
}

/**
 * UI Panel Management - Show/hide content-type-specific panels
 */
function updateContentTypePanels() {
  const taskType = document.getElementById('task_type')?.value;
  
  // Hide all panels
  document.getElementById('proposal-panel')?.classList.add('hidden');
  document.getElementById('review-reply-panel')?.classList.add('hidden');
  document.getElementById('blog-post-panel')?.classList.add('hidden');
  
  // Show relevant panel
  if (taskType === 'proposal') {
    document.getElementById('proposal-panel')?.classList.remove('hidden');
  } else if (taskType === 'review_reply') {
    document.getElementById('review-reply-panel')?.classList.remove('hidden');
  } else if (taskType === 'blog_post') {
    document.getElementById('blog-post-panel')?.classList.remove('hidden');
  }
}

/**
 * Example HTML structure for proposal panel:
 * 
 * <div id="proposal-panel" class="hidden">
 *   <h3>Proposal Details</h3>
 *   
 *   <label for="proposal-type">Proposal Type:</label>
 *   <select id="proposal-type">
 *     <option value="partnership">Partnership</option>
 *     <option value="sponsorship">Sponsorship</option>
 *     <option value="funding">Funding</option>
 *     <option value="rfp_response">RFP Response</option>
 *     <option value="collaboration">Collaboration</option>
 *   </select>
 *   
 *   <label for="proposal-recipient">Recipient:</label>
 *   <input type="text" id="proposal-recipient" placeholder="Company/Person name">
 *   
 *   <label>Key Benefits:</label>
 *   <input type="text" class="proposal-benefit" placeholder="Benefit 1">
 *   <input type="text" class="proposal-benefit" placeholder="Benefit 2">
 *   <input type="text" class="proposal-benefit" placeholder="Benefit 3">
 *   
 *   <label for="proposal-budget">Budget Range:</label>
 *   <input type="text" id="proposal-budget" placeholder="e.g., $10k-$50k">
 *   
 *   <label for="proposal-cta">Call to Action:</label>
 *   <input type="text" id="proposal-cta" placeholder="e.g., Schedule a call">
 * </div>
 */

/**
 * Example HTML structure for review reply panel:
 * 
 * <div id="review-reply-panel" class="hidden">
 *   <h3>Review Reply Details</h3>
 *   
 *   <label for="review-source">Review Platform:</label>
 *   <input type="text" id="review-source" placeholder="e.g., Google, Yelp, Amazon">
 *   
 *   <label for="review-rating">Star Rating:</label>
 *   <select id="review-rating">
 *     <option value="1">1 Star</option>
 *     <option value="2">2 Stars</option>
 *     <option value="3">3 Stars</option>
 *     <option value="4">4 Stars</option>
 *     <option value="5">5 Stars</option>
 *   </select>
 *   
 *   <label for="review-sentiment">Sentiment:</label>
 *   <select id="review-sentiment">
 *     <option value="positive">Positive</option>
 *     <option value="neutral">Neutral</option>
 *     <option value="negative">Negative</option>
 *   </select>
 *   
 *   <label for="review-issue-type">Issue Type:</label>
 *   <select id="review-issue-type">
 *     <option value="">None</option>
 *     <option value="shipping">Shipping</option>
 *     <option value="product">Product</option>
 *     <option value="experience">Experience</option>
 *     <option value="service">Service</option>
 *   </select>
 *   
 *   <label for="review-tone">Desired Tone:</label>
 *   <select id="review-tone">
 *     <option value="professional">Professional</option>
 *     <option value="apologetic">Apologetic</option>
 *     <option value="grateful">Grateful</option>
 *     <option value="empathetic">Empathetic</option>
 *   </select>
 *   
 *   <label for="review-action">Follow-up Action:</label>
 *   <input type="text" id="review-action" placeholder="e.g., Offer refund, Send replacement">
 * </div>
 */

/**
 * Example HTML structure for blog post panel:
 * 
 * <div id="blog-post-panel" class="hidden">
 *   <h3>Blog Post Details</h3>
 *   
 *   <label for="blog-post-type">Post Type:</label>
 *   <select id="blog-post-type">
 *     <option value="how-to">How-To Guide</option>
 *     <option value="listicle">Listicle</option>
 *     <option value="announcement">Announcement</option>
 *     <option value="thought-leadership">Thought Leadership</option>
 *     <option value="case-study">Case Study</option>
 *   </select>
 *   
 *   <label for="blog-length">Desired Length:</label>
 *   <select id="blog-length">
 *     <option value="short">Short (400-600 words)</option>
 *     <option value="medium" selected>Medium (750-1000 words)</option>
 *     <option value="long">Long (1200-1500 words)</option>
 *   </select>
 *   
 *   <label for="blog-audience">Target Audience:</label>
 *   <input type="text" id="blog-audience" placeholder="e.g., Small business owners">
 *   
 *   <label>SEO Keywords:</label>
 *   <input type="text" class="blog-keyword" placeholder="Keyword 1">
 *   <input type="text" class="blog-keyword" placeholder="Keyword 2">
 *   <input type="text" class="blog-keyword" placeholder="Keyword 3">
 *   
 *   <label for="blog-cta">Call to Action:</label>
 *   <input type="text" id="blog-cta" placeholder="e.g., Subscribe to our newsletter">
 * </div>
 */

// Export functions for integration
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    collectProposalFields,
    collectReviewReplyFields,
    collectBlogPostFields,
    generateContentWithTypeFields,
    updateContentTypePanels
  };
}
