/**
 * Social Copy-First Renderer - renders post-ready social cards with copy buttons
 * 
 * Renders SocialPostCard format with:
 * - CAPTION block + Copy button
 * - HASHTAGS block + Copy button  
 * - Copy Caption + Hashtags button
 * - Notes in collapsed <details> "Strategy notes (optional)"
 */

/**
 * Platform display names and icons
 */
const PLATFORM_META = {
  instagram: { label: 'Instagram', icon: '📸', color: '#E4405F' },
  facebook: { label: 'Facebook', icon: '👥', color: '#1877F2' },
  linkedin: { label: 'LinkedIn', icon: '💼', color: '#0A66C2' },
  x: { label: 'X', icon: '🐦', color: '#000000' },
  twitter: { label: 'X', icon: '🐦', color: '#000000' },
  tiktok: { label: 'TikTok', icon: '🎵', color: '#000000' },
};

/**
 * Copy text to clipboard and show feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element to show feedback on
 */
async function copyToClipboard(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    
    // Show success feedback
    const originalText = button.textContent;
    button.textContent = '✓ Copied!';
    button.classList.add('copied');
    
    setTimeout(() => {
      button.textContent = originalText;
      button.classList.remove('copied');
    }, 2000);
    
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    button.textContent = '✗ Failed';
    setTimeout(() => {
      button.textContent = 'Copy';
    }, 2000);
    return false;
  }
}

/**
 * Render a single social post card with copy-first UI
 * @param {Object} card - SocialPostCard object
 * @param {number} index - Card index for unique IDs
 * @returns {HTMLElement} Card element
 */
function renderSocialPostCard(card, index) {
  const platform = card.platform || 'instagram';
  const platformMeta = PLATFORM_META[platform] || PLATFORM_META.instagram;
  
  const cardEl = document.createElement('div');
  cardEl.className = 'social-post-card';
  cardEl.dataset.platform = platform;
  
  // Platform header
  const header = document.createElement('div');
  header.className = 'post-card-header';
  header.innerHTML = `
    <span class="platform-badge" style="border-color: ${platformMeta.color}">
      <span class="platform-icon">${platformMeta.icon}</span>
      <span class="platform-name">${platformMeta.label}</span>
    </span>
  `;
  cardEl.appendChild(header);
  
  // Caption block
  const captionBlock = document.createElement('div');
  captionBlock.className = 'caption-block';
  
  const captionLabel = document.createElement('div');
  captionLabel.className = 'block-label';
  captionLabel.textContent = 'Caption';
  
  const captionText = document.createElement('div');
  captionText.className = 'caption-text';
  captionText.textContent = card.caption || '';
  
  const captionCopyBtn = document.createElement('button');
  captionCopyBtn.className = 'copy-btn copy-btn-small';
  captionCopyBtn.textContent = 'Copy Caption';
  captionCopyBtn.onclick = () => copyToClipboard(card.caption || '', captionCopyBtn);
  
  captionBlock.appendChild(captionLabel);
  captionBlock.appendChild(captionText);
  captionBlock.appendChild(captionCopyBtn);
  cardEl.appendChild(captionBlock);
  
  // Hashtags block (if present)
  if (card.hashtags && card.hashtags.length > 0) {
    const hashtagsBlock = document.createElement('div');
    hashtagsBlock.className = 'hashtags-block';
    
    const hashtagsLabel = document.createElement('div');
    hashtagsLabel.className = 'block-label';
    hashtagsLabel.textContent = 'Hashtags';
    
    const hashtagsText = document.createElement('div');
    hashtagsText.className = 'hashtags-text';
    hashtagsText.textContent = card.hashtags.join(' ');
    
    const hashtagsCopyBtn = document.createElement('button');
    hashtagsCopyBtn.className = 'copy-btn copy-btn-small';
    hashtagsCopyBtn.textContent = 'Copy Hashtags';
    hashtagsCopyBtn.onclick = () => copyToClipboard(card.hashtags.join(' '), hashtagsCopyBtn);
    
    hashtagsBlock.appendChild(hashtagsLabel);
    hashtagsBlock.appendChild(hashtagsText);
    hashtagsBlock.appendChild(hashtagsCopyBtn);
    cardEl.appendChild(hashtagsBlock);
  }
  
  // Copy both button
  const copyBothBtn = document.createElement('button');
  copyBothBtn.className = 'copy-btn copy-btn-primary';
  const combinedText = card.caption + (card.hashtags && card.hashtags.length > 0 ? '\n\n' + card.hashtags.join(' ') : '');
  copyBothBtn.textContent = '📋 Copy Caption + Hashtags';
  copyBothBtn.onclick = () => copyToClipboard(combinedText, copyBothBtn);
  cardEl.appendChild(copyBothBtn);
  
  // CTA (if present)
  if (card.cta) {
    const ctaBlock = document.createElement('div');
    ctaBlock.className = 'cta-block';
    ctaBlock.innerHTML = `<strong>CTA:</strong> ${card.cta}`;
    cardEl.appendChild(ctaBlock);
  }
  
  // Image prompt (if present)
  if (card.image_prompt) {
    const imageBlock = document.createElement('div');
    imageBlock.className = 'image-prompt-block';
    imageBlock.innerHTML = `<strong>Image idea:</strong> ${card.image_prompt}`;
    cardEl.appendChild(imageBlock);
  }
  
  // Notes (if present) - collapsed by default
  if (card.notes && card.notes.length > 0) {
    const notesDetails = document.createElement('details');
    notesDetails.className = 'notes-details';
    
    const notesSummary = document.createElement('summary');
    notesSummary.textContent = 'Strategy notes (optional)';
    notesDetails.appendChild(notesSummary);
    
    const notesList = document.createElement('ul');
    notesList.className = 'notes-list';
    card.notes.forEach(note => {
      const li = document.createElement('li');
      li.textContent = note;
      notesList.appendChild(li);
    });
    notesDetails.appendChild(notesList);
    
    cardEl.appendChild(notesDetails);
  }
  
  return cardEl;
}

/**
 * Render all social post cards
 * @param {Array} posts - Array of SocialPostCard objects
 * @param {HTMLElement} container - Container element to render into
 */
function renderSocialPostCards(posts, container) {
  if (!posts || !Array.isArray(posts) || posts.length === 0) {
    container.innerHTML = '<p class="no-posts">No posts to display</p>';
    return;
  }
  
  // Clear container
  container.innerHTML = '';
  
  // Add header
  const header = document.createElement('div');
  header.className = 'posts-header';
  header.innerHTML = `
    <h2>Your Copy-Ready Posts</h2>
    <p class="posts-subtitle">Click any copy button to grab the content</p>
  `;
  container.appendChild(header);
  
  // Render cards
  const cardsContainer = document.createElement('div');
  cardsContainer.className = 'social-post-cards-grid';
  
  posts.forEach((card, index) => {
    const cardEl = renderSocialPostCard(card, index);
    cardsContainer.appendChild(cardEl);
  });
  
  container.appendChild(cardsContainer);
}

/**
 * Check if response contains SocialPostCard format
 * @param {Object} response - API response
 * @returns {boolean} True if response contains post-ready format
 */
function isPostReadyFormat(response) {
  if (!response || !response.data) {
    return false;
  }
  
  const posts = response.data.posts;
  if (!posts || !Array.isArray(posts) || posts.length === 0) {
    return false;
  }
  
  // Check if first post has SocialPostCard shape (platform + caption at root level)
  const firstPost = posts[0];
  return firstPost && 
         typeof firstPost.platform === 'string' && 
         typeof firstPost.caption === 'string';
}

// Export for use in dashboard
if (typeof window !== 'undefined') {
  window.SocialCopyFirstRenderer = {
    renderSocialPostCards,
    renderSocialPostCard,
    isPostReadyFormat,
    copyToClipboard,
  };
}
