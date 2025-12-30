def register_blueprints(app):
    """Register available blueprints. Keep imports local so missing modules don't
    crash early during scaffold phases.
    """
    try:
        from .auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except Exception:
        pass

    try:
        from .dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/')
    except Exception:
        pass

    try:
        from .wizard import wizard_bp
        app.register_blueprint(wizard_bp, url_prefix='')
    except Exception:
        pass
