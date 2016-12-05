import veil_component

with veil_component.init_component(__name__):

    from .review import list_waiting_for_operator_reviews

    __all__ = [
        list_waiting_for_operator_reviews.__name__,
    ]
