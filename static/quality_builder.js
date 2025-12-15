// Quality Builder JavaScript
// Implements the single-page tiered quality builder

let CFG = null;
let qualityData = {
  // Basics
  industry: null,
  businessName: '',
  serviceArea: '',
  platforms: [],
  
  // Good tier
  services: [],
  audiences: [],
  pains: [],
  outcomes: [],
  ctaIntent: null,
  
  // Better tier
  differentiators: [],
  proof: [],
  offerShape: null,
  
  // Best tier
  objections: [],
  policies: [],
  emailName: '',
  emailTitle: '',
  emailContact: '',
  deposit: '',
  turnaround: '',
  validity: '',
  paymentMethods: ''
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  await loadConfig();
  initializeUI();
  setupEventListeners();
  loadExistingData();
  updateQualityScore();
});

async function loadConfig() {
  try {
    const res = await fetch('/static/content/config.json', { cache: 'no-store' });
    if (res.ok) {
      CFG = await res.json();
      window.CFG = CFG;
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

function initializeUI() {
  if (!CFG) return;
  
  // Render industries
  const industriesContainer = document.getElementById('qb-industries');
  if (industriesContainer && CFG.industries) {
    CFG.industries.forEach(ind => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'industry-btn px-4 py-3 rounded-xl border-2 border-slate-200 hover:border-purple-500 text-sm font-medium text-slate-700 hover:text-purple-700 transition flex items-center gap-2';
      btn.dataset.industry = ind.key;
      btn.innerHTML = `<span>${ind.icon || '📁'}</span><span>${ind.label}</span>`;
      btn.addEventListener('click', () => selectIndustry(ind.key));
      industriesContainer.appendChild(btn);
    });
  }
  
  // Render platforms
  const platformsContainer = document.getElementById('qb-platforms');
  if (platformsContainer && CFG.platforms) {
    CFG.platforms.forEach(plat => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'platform-btn px-4 py-2 rounded-lg border-2 border-slate-300 bg-white hover:border-purple-500 hover:bg-purple-50 transition';
      btn.dataset.platform = plat.key;
      btn.textContent = plat.label;
      btn.addEventListener('click', () => togglePlatform(plat.key));
      platformsContainer.appendChild(btn);
    });
  }
}

function setupEventListeners() {
  // Quality level buttons
  document.getElementById('level-good')?.addEventListener('click', () => setQualityLevel('good'));
  document.getElementById('level-better')?.addEventListener('click', () => setQualityLevel('better'));
  document.getElementById('level-best')?.addEventListener('click', () => setQualityLevel('best'));
  
  // Section toggles
  document.getElementById('toggle-good')?.addEventListener('click', () => toggleSection('good'));
  document.getElementById('toggle-better')?.addEventListener('click', () => toggleSection('better'));
  document.getElementById('toggle-best')?.addEventListener('click', () => toggleSection('best'));
  
  // Chip inputs
  setupChipInput('qb-services-input', 'qb-services-chips', 'services', 5);
  setupChipInput('qb-audience-input', 'qb-audience-chips', 'audiences', 3);
  setupChipInput('qb-pain-input', 'qb-pain-chips', 'pains', 3);
  setupChipInput('qb-outcome-input', 'qb-outcome-chips', 'outcomes', 2);
  setupChipInput('qb-differentiators-input', 'qb-differentiators-chips', 'differentiators', 5);
  setupChipInput('qb-proof-input', 'qb-proof-chips', 'proof', 10);
  setupChipInput('qb-objections-input', 'qb-objections-chips', 'objections', 2);
  setupChipInput('qb-policies-input', 'qb-policies-chips', 'policies', 3);
  
  // Chip suggestions
  document.querySelectorAll('.chip-suggestion').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (target) {
        target.value = btn.dataset.value;
        target.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
      }
    });
  });
  
  // CTA intent buttons
  document.querySelectorAll('.cta-intent-btn').forEach(btn => {
    btn.addEventListener('click', () => selectCtaIntent(btn.dataset.value));
  });
  
  // Offer shape buttons
  document.querySelectorAll('.offer-shape-btn').forEach(btn => {
    btn.addEventListener('click', () => selectOfferShape(btn.dataset.value));
  });
  
  // Preview tabs
  document.getElementById('preview-tab-social')?.addEventListener('click', () => showPreviewTab('social'));
  document.getElementById('preview-tab-email')?.addEventListener('click', () => showPreviewTab('email'));
  document.getElementById('preview-tab-quote')?.addEventListener('click', () => showPreviewTab('quote'));
  
  // Text inputs with live update - use mapping for clarity
  const inputFieldMap = {
    'qb-business-name': 'businessName',
    'qb-service-area': 'serviceArea'
  };
  
  Object.entries(inputFieldMap).forEach(([id, dataKey]) => {
    document.getElementById(id)?.addEventListener('input', (e) => {
      qualityData[dataKey] = e.target.value;
      updateQualityScore();
      updatePreview();
    });
  });
  
  // Save button
  document.getElementById('qb-save')?.addEventListener('click', saveQualityBuilder);
}

function setupChipInput(inputId, chipContainerId, dataKey, maxCount) {
  const input = document.getElementById(inputId);
  const container = document.getElementById(chipContainerId);
  
  if (!input || !container) return;
  
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const value = input.value.trim();
      if (value && qualityData[dataKey].length < maxCount) {
        qualityData[dataKey].push(value);
        addChip(container, value, dataKey);
        input.value = '';
        updateQualityScore();
        updatePreview();
      } else if (qualityData[dataKey].length >= maxCount) {
        showToast(`Maximum ${maxCount} items for this field`);
      }
    }
  });
}

function addChip(container, value, dataKey) {
  const chip = document.createElement('div');
  chip.className = 'chip px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm flex items-center gap-2';
  chip.innerHTML = `
    <span>${value}</span>
    <button type="button" class="hover:text-purple-900" onclick="removeChip(this, '${dataKey}', '${value}')">×</button>
  `;
  container.appendChild(chip);
}

function removeChip(button, dataKey, value) {
  qualityData[dataKey] = qualityData[dataKey].filter(item => item !== value);
  button.closest('.chip').remove();
  updateQualityScore();
  updatePreview();
}

function selectIndustry(key) {
  qualityData.industry = key;
  
  // Update UI
  document.querySelectorAll('.industry-btn').forEach(btn => {
    if (btn.dataset.industry === key) {
      btn.classList.add('border-purple-500', 'bg-purple-50', 'text-purple-700');
      btn.classList.remove('border-slate-200');
    } else {
      btn.classList.remove('border-purple-500', 'bg-purple-50', 'text-purple-700');
      btn.classList.add('border-slate-200');
    }
  });
  
  updateQualityScore();
  updatePreview();
}

function togglePlatform(key) {
  const index = qualityData.platforms.indexOf(key);
  if (index > -1) {
    qualityData.platforms.splice(index, 1);
  } else {
    qualityData.platforms.push(key);
  }
  
  // Update UI
  document.querySelectorAll('.platform-btn').forEach(btn => {
    if (qualityData.platforms.includes(btn.dataset.platform)) {
      btn.classList.add('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.remove('border-slate-300', 'bg-white');
    } else {
      btn.classList.remove('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.add('border-slate-300', 'bg-white');
    }
  });
  
  updateQualityScore();
}

function selectCtaIntent(value) {
  qualityData.ctaIntent = value;
  
  // Update UI
  document.querySelectorAll('.cta-intent-btn').forEach(btn => {
    if (btn.dataset.value === value) {
      btn.classList.add('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.remove('border-slate-300', 'bg-white');
    } else {
      btn.classList.remove('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.add('border-slate-300', 'bg-white');
    }
  });
  
  updateQualityScore();
  updatePreview();
}

function selectOfferShape(value) {
  qualityData.offerShape = value;
  
  // Update UI
  document.querySelectorAll('.offer-shape-btn').forEach(btn => {
    if (btn.dataset.value === value) {
      btn.classList.add('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.remove('border-slate-300', 'bg-white');
    } else {
      btn.classList.remove('border-purple-500', 'bg-purple-100', 'text-purple-700');
      btn.classList.add('border-slate-300', 'bg-white');
    }
  });
  
  updateQualityScore();
  updatePreview();
}

function setQualityLevel(level) {
  // Update active button
  document.querySelectorAll('.quality-level-btn').forEach(btn => {
    btn.classList.remove('active', 'border-green-400', 'border-blue-400', 'border-purple-400');
  });
  
  const btn = document.getElementById(`level-${level}`);
  if (btn) {
    btn.classList.add('active');
    if (level === 'good') btn.classList.add('border-green-400');
    if (level === 'better') btn.classList.add('border-blue-400');
    if (level === 'best') btn.classList.add('border-purple-400');
  }
  
  // Show/hide sections
  if (level === 'good') {
    document.getElementById('section-good-content').classList.remove('hidden');
    document.getElementById('section-better-content').classList.add('hidden');
    document.getElementById('section-best-content').classList.add('hidden');
  } else if (level === 'better') {
    document.getElementById('section-good-content').classList.remove('hidden');
    document.getElementById('section-better-content').classList.remove('hidden');
    document.getElementById('section-best-content').classList.add('hidden');
  } else if (level === 'best') {
    document.getElementById('section-good-content').classList.remove('hidden');
    document.getElementById('section-better-content').classList.remove('hidden');
    document.getElementById('section-best-content').classList.remove('hidden');
  }
}

function toggleSection(section) {
  const content = document.getElementById(`section-${section}-content`);
  const toggle = document.getElementById(`toggle-${section}`);
  
  if (content && toggle) {
    content.classList.toggle('hidden');
    toggle.textContent = content.classList.contains('hidden') ? '▶' : '▼';
  }
}

function updateQualityScore() {
  let score = 0;
  let totalFields = 10; // Total possible fields for 100%
  let filledFields = 0;
  
  // Basics (2 required fields)
  if (qualityData.industry) filledFields += 1;
  if (qualityData.platforms.length > 0) filledFields += 1;
  
  // Good tier (5 fields)
  if (qualityData.services.length >= 2) filledFields += 1;
  if (qualityData.audiences.length >= 1) filledFields += 1;
  if (qualityData.pains.length >= 1) filledFields += 1;
  if (qualityData.outcomes.length >= 1) filledFields += 1;
  if (qualityData.ctaIntent) filledFields += 1;
  
  // Better tier (3 fields)
  if (qualityData.differentiators.length >= 2) filledFields += 1;
  if (qualityData.proof.length >= 1) filledFields += 1;
  if (qualityData.offerShape) filledFields += 1;
  
  // Calculate percentage
  score = Math.round((filledFields / totalFields) * 100);
  
  // Update UI
  const scoreBar = document.getElementById('quality-score-bar');
  const scoreText = document.getElementById('quality-score-text');
  const nextStep = document.getElementById('quality-next-step');
  
  if (scoreBar) scoreBar.style.width = score + '%';
  if (scoreText) scoreText.textContent = score + '%';
  
  // Update next step guidance
  if (nextStep) {
    if (filledFields === 0) {
      nextStep.textContent = 'Fill in the basics below to get started';
    } else if (filledFields < 7) {
      nextStep.textContent = 'Complete Good tier fields to unlock copy/paste-ready posts';
    } else if (filledFields < 10) {
      nextStep.textContent = 'Add Better tier fields for more credible, conversion-focused content';
    } else {
      nextStep.textContent = '🎉 Excellent! Your content will be expert-level';
    }
  }
  
  return score;
}

function updatePreview() {
  // Generate instant preview based on current data
  const goodPreview = generateGoodPreview();
  const betterPreview = generateBetterPreview();
  const bestPreview = generateBestPreview();
  
  const goodEl = document.getElementById('preview-good');
  const betterEl = document.getElementById('preview-better');
  const bestEl = document.getElementById('preview-best');
  
  if (goodEl) goodEl.innerHTML = goodPreview;
  if (betterEl) betterEl.innerHTML = betterPreview;
  if (bestEl) bestEl.innerHTML = bestPreview;
}

function generateGoodPreview() {
  if (!qualityData.industry || qualityData.services.length === 0) {
    return '<em class="text-slate-500">Fill in the basics above to see your Good-level content here...</em>';
  }
  
  const service = qualityData.services[0] || 'our services';
  const audience = qualityData.audiences[0] || 'clients';
  const outcome = qualityData.outcomes[0] || 'great results';
  const cta = qualityData.ctaIntent ? getCtaText(qualityData.ctaIntent) : 'Contact us';
  
  return `Ready to ${outcome}? We offer ${service} for ${audience}. ${cta} to learn more!`;
}

function generateBetterPreview() {
  const goodContent = generateGoodPreview();
  if (goodContent.includes('Fill in')) {
    return '<em class="text-slate-500">Add Better-tier fields to see improved content...</em>';
  }
  
  if (qualityData.differentiators.length === 0 && qualityData.proof.length === 0) {
    return '<em class="text-slate-500">Add differentiators and proof to see Better-level content...</em>';
  }
  
  const service = qualityData.services[0] || 'our services';
  const audience = qualityData.audiences[0] || 'clients';
  const outcome = qualityData.outcomes[0] || 'great results';
  const diff = qualityData.differentiators[0] || 'personalized service';
  const proof = qualityData.proof[0] || 'years of experience';
  const cta = qualityData.ctaIntent ? getCtaText(qualityData.ctaIntent) : 'Contact us';
  
  return `Ready to ${outcome}? With ${proof}, we offer ${service} for ${audience}. Our ${diff} sets us apart. ${cta} today!`;
}

function generateBestPreview() {
  const betterContent = generateBetterPreview();
  if (betterContent.includes('Fill in') || betterContent.includes('Add')) {
    return '<em class="text-slate-500">Complete all fields to see expert-level content...</em>';
  }
  
  const service = qualityData.services[0] || 'our services';
  const audience = qualityData.audiences[0] || 'clients';
  const outcome = qualityData.outcomes[0] || 'great results';
  const diff = qualityData.differentiators[0] || 'personalized service';
  const proof = qualityData.proof[0] || 'years of experience';
  const objection = qualityData.objections[0] || 'the investment';
  const cta = qualityData.ctaIntent ? getCtaText(qualityData.ctaIntent) : 'Contact us';
  
  return `Ready to ${outcome}? With ${proof}, we offer ${service} for ${audience}. Our ${diff} ensures quality results. Concerned about ${objection}? We make it easy. ${cta} today for a consultation!`;
}

function getCtaText(intent) {
  const ctaMap = {
    book: '📅 Book now',
    call: '📞 Call us',
    dm: '💬 Send us a DM',
    quote: '📋 Request a quote',
    visit: '🌐 Visit our website'
  };
  return ctaMap[intent] || 'Contact us';
}

function showPreviewTab(tab) {
  // Update tab buttons
  document.querySelectorAll('.preview-tab').forEach(btn => {
    btn.classList.remove('bg-purple-100', 'text-purple-700', 'active');
    btn.classList.add('bg-slate-100', 'text-slate-600');
  });
  
  const activeTab = document.getElementById(`preview-tab-${tab}`);
  if (activeTab) {
    activeTab.classList.remove('bg-slate-100', 'text-slate-600');
    activeTab.classList.add('bg-purple-100', 'text-purple-700', 'active');
  }
  
  // For now, keep showing social preview (we can expand this later)
  // In a full implementation, we'd generate different previews for each tab
}

async function loadExistingData() {
  // Load existing profile data if available
  try {
    const res = await fetch('/api/profile', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      if (data && data.industry) {
        // Map profile fields to qualityData
        qualityData.industry = data.industry;
        qualityData.businessName = data.company || '';
        qualityData.platforms = data.platforms || [];
        
        // Map brand_kit fields if available
        if (data.brand_kit) {
          const bk = data.brand_kit;
          qualityData.services = bk.services || [];
          qualityData.audiences = bk.audience ? bk.audience.split(',').map(s => s.trim()).filter(Boolean) : [];
          qualityData.pains = bk.pain ? bk.pain.split(',').map(s => s.trim()).filter(Boolean) : [];
          qualityData.outcomes = bk.outcome ? bk.outcome.split(',').map(s => s.trim()).filter(Boolean) : [];
          qualityData.differentiators = bk.differentiators || [];
          qualityData.proof = bk.proof ? bk.proof.split(',').map(s => s.trim()).filter(Boolean) : [];
          qualityData.ctaIntent = bk.cta_intent || null;
          qualityData.offerShape = bk.offer_shape || null;
          qualityData.objections = bk.objections ? bk.objections.split(',').map(s => s.trim()).filter(Boolean) : [];
          qualityData.policies = bk.policies ? bk.policies.split(',').map(s => s.trim()).filter(Boolean) : [];
        }
        
        // Update UI with loaded data
        updateUIFromLoadedData();
        updateQualityScore();
        updatePreview();
      }
    }
  } catch (e) {
    console.log('No existing profile data');
  }
}

function updateUIFromLoadedData() {
  // Update industry selection
  if (qualityData.industry) {
    const btn = document.querySelector(`.industry-btn[data-industry="${qualityData.industry}"]`);
    if (btn) btn.click();
  }
  
  // Update business name
  const businessNameInput = document.getElementById('qb-business-name');
  if (businessNameInput) businessNameInput.value = qualityData.businessName;
  
  // Update platforms
  qualityData.platforms.forEach(platform => {
    const btn = document.querySelector(`.platform-btn[data-platform="${platform}"]`);
    if (btn) btn.click();
  });
  
  // Update chips
  qualityData.services.forEach(service => {
    addChip(document.getElementById('qb-services-chips'), service, 'services');
  });
  qualityData.audiences.forEach(audience => {
    addChip(document.getElementById('qb-audience-chips'), audience, 'audiences');
  });
  qualityData.pains.forEach(pain => {
    addChip(document.getElementById('qb-pain-chips'), pain, 'pains');
  });
  qualityData.outcomes.forEach(outcome => {
    addChip(document.getElementById('qb-outcome-chips'), outcome, 'outcomes');
  });
  qualityData.differentiators.forEach(diff => {
    addChip(document.getElementById('qb-differentiators-chips'), diff, 'differentiators');
  });
  qualityData.proof.forEach(proof => {
    addChip(document.getElementById('qb-proof-chips'), proof, 'proof');
  });
  
  // Update CTA intent
  if (qualityData.ctaIntent) {
    const btn = document.querySelector(`.cta-intent-btn[data-value="${qualityData.ctaIntent}"]`);
    if (btn) btn.click();
  }
  
  // Update offer shape
  if (qualityData.offerShape) {
    const btn = document.querySelector(`.offer-shape-btn[data-value="${qualityData.offerShape}"]`);
    if (btn) btn.click();
  }
}

async function saveQualityBuilder() {
  const btn = document.getElementById('qb-save');
  if (!btn) return;
  
  // Validate required fields
  if (!qualityData.industry) {
    showToast('Please select your industry');
    return;
  }
  
  if (qualityData.platforms.length === 0) {
    showToast('Please select at least one platform');
    return;
  }
  
  // Show loading state
  btn.disabled = true;
  btn.textContent = 'Saving...';
  
  try {
    // Map qualityData to profile format
    const profileData = {
      industry: qualityData.industry,
      company: qualityData.businessName,
      tone: 'friendly', // Default tone
      platforms: qualityData.platforms,
      keywords: [],
      note: '',
      // Brand Kit data
      brand_kit: {
        business_name: qualityData.businessName,
        services: qualityData.services,
        audience: qualityData.audiences.join(', '),
        pain: qualityData.pains.join(', '),
        outcome: qualityData.outcomes.join(', '),
        differentiators: qualityData.differentiators,
        proof: qualityData.proof.join(', '),
        cta_intent: qualityData.ctaIntent,
        offer_shape: qualityData.offerShape,
        objections: qualityData.objections.join(', '),
        policies: qualityData.policies.join(', ')
      }
    };
    
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(profileData)
    });
    
    if (!res.ok) {
      throw new Error('Failed to save profile');
    }
    
    showToast('Quality Builder saved!', 'success');
    
    // Redirect to dashboard after short delay
    setTimeout(() => {
      window.location.href = '/generate';
    }, 1000);
    
  } catch (e) {
    console.error('Save failed:', e);
    showToast('Failed to save. Please try again.');
    btn.disabled = false;
    btn.textContent = 'Save & Continue to Dashboard';
  }
}

function showToast(message, type = 'info') {
  // Simple toast notification
  const toast = document.createElement('div');
  toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
    type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
  }`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

// Make removeChip globally accessible
window.removeChip = removeChip;
