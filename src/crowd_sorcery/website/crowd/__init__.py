from veil.frontend.template import import_widget
import veil_component
import crowd_sorcery.template_filters  # import to registering template filters

with veil_component.init_component(__name__):
    __all__ = []

    def init():
        from veil.frontend.web import register_website_context_manager
        from veil.frontend.visitor import enable_user_tracking
        from .gear.crowd_website_gear import crowd_user_info_widget

        import_widget(crowd_user_info_widget)

        register_website_context_manager('crowd', enable_user_tracking('crowd', login_url='/signin'))
