import veil_component
import crowd_sorcery.template_filters  # import to registering template filters

with veil_component.init_component(__name__):
    __all__ = [

    ]

    def init():
        from veil.frontend.web import register_website_context_manager
        from veil.frontend.visitor import enable_user_tracking
        register_website_context_manager('operator', enable_user_tracking('operator', login_url='/login',
            session_cookie_on_parent_domain=True))
