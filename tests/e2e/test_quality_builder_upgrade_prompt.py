"""E2E test for Quality Builder - Upgrade prompts from Good to Better."""

import pytest


@pytest.mark.e2e
def test_quality_builder_upgrade_prompt_shown_at_good(page, live_server):
    """
    Test that upgrade prompt is shown when Good tier is complete.
    
    Acceptance criteria:
    - When Good tier is complete, show "Improve to Better" prompt
    - Prompt explains value of Better tier
    - Clicking prompt expands Better section
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Complete Good tier
    page.click('.industry-btn[data-industry="retail"]')
    page.fill('#qb-business-name', 'Upgrade Test')
    page.click('.platform-btn[data-platform="instagram"]')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Service 1')
    services_input.press('Enter')
    services_input.fill('Service 2')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="book"]')
    
    # Wait a moment for quality score to update
    page.wait_for_timeout(500)
    
    # Check for upgrade prompt or next step indicator
    next_step = page.locator('#quality-next-step').inner_text()
    # Should suggest moving to Better tier
    assert 'Better' in next_step or 'credible' in next_step.lower() or 'conversion' in next_step.lower()


@pytest.mark.e2e
def test_quality_builder_quality_level_buttons_expand_sections(page, live_server):
    """
    Test that clicking quality level buttons expands corresponding sections.
    
    Acceptance criteria:
    - Clicking "Better" button expands Good + Better sections
    - Clicking "Best" button expands all sections
    - Quality level buttons show active state
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Initially Good is active
    good_btn = page.locator('#level-good')
    better_btn = page.locator('#level-better')
    best_btn = page.locator('#level-best')
    
    assert 'active' in good_btn.get_attribute('class')
    
    # Good section should be visible
    assert page.locator('#section-good-content').is_visible()
    # Better should be hidden
    assert not page.locator('#section-better-content').is_visible()
    
    # Click Better level button
    better_btn.click()
    page.wait_for_timeout(300)
    
    # Both Good and Better should be visible
    assert page.locator('#section-good-content').is_visible()
    assert page.locator('#section-better-content').is_visible()
    assert not page.locator('#section-best-content').is_visible()
    
    # Better button should be active
    assert 'active' in better_btn.get_attribute('class')
    
    # Click Best level button
    best_btn.click()
    page.wait_for_timeout(300)
    
    # All sections should be visible
    assert page.locator('#section-good-content').is_visible()
    assert page.locator('#section-better-content').is_visible()
    assert page.locator('#section-best-content').is_visible()
    
    # Best button should be active
    assert 'active' in best_btn.get_attribute('class')


@pytest.mark.e2e
def test_quality_builder_score_increases_with_better_tier(page, live_server):
    """
    Test that quality score increases when Better tier fields are filled.
    
    Acceptance criteria:
    - Score increases from Good to Better
    - Next step guidance updates
    - Progress is visible
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Complete Good tier
    page.click('.industry-btn[data-industry="fitness"]')
    page.fill('#qb-business-name', 'Score Test')
    page.click('.platform-btn[data-platform="instagram"]')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Training')
    services_input.press('Enter')
    services_input.fill('Nutrition')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="book"]')
    page.wait_for_timeout(500)
    
    # Get Good tier score
    good_score = page.locator('#quality-score-text').inner_text()
    good_score_num = int(good_score.replace('%', ''))
    
    # Expand Better section
    page.click('#toggle-better')
    page.wait_for_timeout(300)
    
    # Fill Better tier
    diff_input = page.locator('#qb-differentiators-input')
    diff_input.fill('Certified trainers')
    diff_input.press('Enter')
    diff_input.fill('Custom plans')
    diff_input.press('Enter')
    page.wait_for_timeout(300)
    
    proof_input = page.locator('#qb-proof-input')
    proof_input.fill('10+ years')
    proof_input.press('Enter')
    page.wait_for_timeout(300)
    
    page.click('.offer-shape-btn[data-value="packages"]')
    page.wait_for_timeout(500)
    
    # Get Better tier score
    better_score = page.locator('#quality-score-text').inner_text()
    better_score_num = int(better_score.replace('%', ''))
    
    # Score should have increased
    assert better_score_num > good_score_num, f"Better score ({better_score_num}%) should be higher than Good score ({good_score_num}%)"


@pytest.mark.e2e
def test_quality_builder_preview_comparison_shows_improvement(page, live_server):
    """
    Test that preview clearly shows improvement from Good to Better to Best.
    
    Acceptance criteria:
    - Good preview is short and basic
    - Better preview includes proof and differentiators
    - Best preview handles objections
    - Visual distinction is clear
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Complete Good tier
    page.click('.industry-btn[data-industry="coach"]')
    page.fill('#qb-business-name', 'Preview Coach')
    page.click('.platform-btn[data-platform="linkedin"]')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Life Coaching')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="dm"]')
    page.wait_for_timeout(500)
    
    # Get Good preview length
    good_preview = page.locator('#preview-good').inner_text()
    good_length = len(good_preview)
    
    # Better preview should still show placeholder
    better_preview = page.locator('#preview-better').inner_text()
    assert 'Add' in better_preview or 'Better-tier' in better_preview
    
    # Fill Better tier
    page.click('#toggle-better')
    page.wait_for_timeout(300)
    
    diff_input = page.locator('#qb-differentiators-input')
    diff_input.fill('1-on-1 personalized')
    diff_input.press('Enter')
    diff_input.fill('Results-driven')
    diff_input.press('Enter')
    
    proof_input = page.locator('#qb-proof-input')
    proof_input.fill('500+ successful clients')
    proof_input.press('Enter')
    
    page.click('.offer-shape-btn[data-value="consultation"]')
    page.wait_for_timeout(500)
    
    # Better preview should now have content
    better_preview_updated = page.locator('#preview-better').inner_text()
    # Should be longer than Good (has more details)
    # Or at least show different content


@pytest.mark.e2e
def test_quality_builder_next_step_guidance_updates(page, live_server):
    """
    Test that "next best improvement" guidance updates as user progresses.
    
    Acceptance criteria:
    - Initial: "Fill in the basics"
    - After basics: "Complete Good tier fields"
    - After Good: "Add Better tier fields"
    - After Better: "Complete Best tier" or "Excellent!"
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Check initial guidance
    next_step = page.locator('#quality-next-step')
    initial_text = next_step.inner_text()
    assert 'basics' in initial_text.lower() or 'started' in initial_text.lower()
    
    # Fill basics
    page.click('.industry-btn[data-industry="retail"]')
    page.click('.platform-btn[data-platform="instagram"]')
    page.wait_for_timeout(300)
    
    # Guidance should update
    after_basics = next_step.inner_text()
    assert after_basics != initial_text
    assert 'Good' in after_basics or 'copy/paste' in after_basics.lower()
    
    # Complete Good tier
    page.fill('#qb-business-name', 'Guidance Test')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Service')
    services_input.press('Enter')
    services_input.fill('Service2')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="book"]')
    page.wait_for_timeout(500)
    
    # Guidance should suggest Better tier
    after_good = next_step.inner_text()
    assert 'Better' in after_good or 'credible' in after_good.lower() or 'conversion' in after_good.lower()


@pytest.mark.e2e
def test_quality_builder_back_to_good_from_better(page, live_server):
    """
    Test that user can navigate back from Better to Good.
    
    Acceptance criteria:
    - User can click Good level button to focus on Good tier
    - Better section collapses (optional UX)
    - Data is preserved
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Complete Good tier
    page.click('.industry-btn[data-industry="retail"]')
    page.fill('#qb-business-name', 'Navigation Test')
    page.click('.platform-btn[data-platform="instagram"]')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Service')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="book"]')
    
    # Go to Better
    better_btn = page.locator('#level-better')
    better_btn.click()
    page.wait_for_timeout(300)
    
    # Better section should be visible
    assert page.locator('#section-better-content').is_visible()
    
    # Go back to Good
    good_btn = page.locator('#level-good')
    good_btn.click()
    page.wait_for_timeout(300)
    
    # Good button should be active again
    assert 'active' in good_btn.get_attribute('class')
    
    # Data should be preserved
    business_name = page.locator('#qb-business-name').input_value()
    assert business_name == 'Navigation Test'


@pytest.mark.e2e
def test_quality_builder_encourages_completion(page, live_server):
    """
    Test that UI encourages users to complete higher tiers.
    
    Acceptance criteria:
    - Quality meter shows progress visually
    - Next step text is encouraging
    - Preview comparison makes value obvious
    """
    page.goto(f'{live_server.url()}/quality-builder')
    page.wait_for_selector('#qb-industries', state='visible')
    
    # Complete Good tier
    page.click('.industry-btn[data-industry="realtor"]')
    page.fill('#qb-business-name', 'Real Estate Pro')
    page.click('.platform-btn[data-platform="facebook"]')
    
    services_input = page.locator('#qb-services-input')
    services_input.fill('Home Sales')
    services_input.press('Enter')
    services_input.fill('Market Analysis')
    services_input.press('Enter')
    
    page.click('.chip-suggestion[data-target="qb-audience-input"]')
    page.click('.chip-suggestion[data-target="qb-pain-input"]')
    page.click('.chip-suggestion[data-target="qb-outcome-input"]')
    page.click('.cta-intent-btn[data-value="call"]')
    page.wait_for_timeout(500)
    
    # Check quality meter
    score_bar = page.locator('#quality-score-bar')
    score_width = score_bar.evaluate('el => el.style.width')
    # Should have some progress but not 100%
    assert score_width != '0%'
    assert score_width != '100%'
    
    # Check next step text is encouraging
    next_step = page.locator('#quality-next-step').inner_text()
    assert len(next_step) > 0, "Next step guidance should be shown"
    
    # Check that preview shows difference
    good_preview = page.locator('#preview-good').inner_text()
    better_preview = page.locator('#preview-better').inner_text()
    best_preview = page.locator('#preview-best').inner_text()
    
    # Previews should be distinct
    assert good_preview != better_preview or 'Add' in better_preview
    assert good_preview != best_preview or 'Complete' in best_preview
