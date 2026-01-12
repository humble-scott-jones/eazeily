from jinja2 import Environment, FileSystemLoader


def _render_dashboard():
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    return template.render()


def test_proposal_panel_has_structured_fields():
    rendered = _render_dashboard()

    assert 'id="proposal-panel"' in rendered
    for field_id in [
        "proposal-company",
        "proposal-contact-name",
        "proposal-contact-email",
        "proposal-industry",
        "proposal-headline",
        "proposal-goals",
        "proposal-scope",
        "proposal-timeline",
        "proposal-budget-range",
        "proposal-audience",
        "proposal-cta-main",
        "proposal-keywords",
    ]:
        assert f'id="{field_id}"' in rendered


def test_proposal_flow_hides_instagram_options():
    rendered = _render_dashboard()
    # Ensure the updateDynamicInputs guard for proposals exists to avoid Instagram options bleed-through
    assert "if (taskType === 'proposal')" in rendered
    # Visual Instagram section should still exist for social tasks
    assert 'id="visual-options"' in rendered
