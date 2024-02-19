from typing import Callable

from django.db.models import Manager, QuerySet


class ORM:
    @staticmethod
    def only(fn: Callable[..., QuerySet]):
        def only_wrapper(objects: Manager, only=None, *args, **kwargs):
            if only is not None:
                return fn(objects, *args, **kwargs).only(*only)
            return fn(objects, *args, **kwargs)

        return only_wrapper

    @staticmethod
    def prefetch_related(fn: Callable[..., QuerySet]):
        def prefetch_related_wrapper(objects: Manager, prefetch_related=None, *args, **kwargs):
            if filter is not None:
                return fn(objects, *args, **kwargs).prefetch_related(*prefetch_related)
            return fn(objects, *args, **kwargs)

        return prefetch_related_wrapper

    @staticmethod
    def select_related(fn: Callable[..., QuerySet]):
        def select_related_wrapper(objects: Manager, select_related=None, *args, **kwargs):
            if filter is not None:
                return fn(objects, *args, **kwargs).select_related(*select_related)
            return fn(objects, *args, **kwargs)

        return select_related_wrapper

    @staticmethod
    def filter_(fn: Callable[..., QuerySet]):
        def filter_wrapper(objects: Manager, filter=None, *args, **kwargs):
            if filter is not None:
                return fn(objects, *args, **kwargs).filter(*filter)
            return fn(objects, *args, **kwargs)

        return filter_wrapper

    @staticmethod
    def exclude(fn: Callable[..., QuerySet]):
        def exclude_wrapper(objects: Manager, exclude=None, *args, **kwargs):
            if exclude is not None:
                return fn(objects, *args, **kwargs).exclude(*exclude)
            return fn(objects, *args, **kwargs)

        return exclude_wrapper

    @staticmethod
    def annotate(fn: Callable[..., QuerySet]):
        def annotate_wrapper(objects: Manager, annotations=None, *args, **kwargs):
            if annotations is not None:
                return fn(objects, *args, **kwargs).annotate(*annotations)
            return fn(objects, *args, **kwargs)

        return annotate_wrapper

    @staticmethod
    def order_by(fn: Callable[..., QuerySet]):
        def order_by_wrapper(objects: Manager, order_by=None, *args, **kwargs):
            if order_by is not None:
                return fn(objects, *args, **kwargs).order_by(*order_by)
            return fn(objects, *args, **kwargs)

        return order_by_wrapper

    @staticmethod
    def limit(fn: Callable[..., QuerySet]):
        def limit_wrapper(objects: Manager, limit=None, *args, **kwargs):
            if limit is not None:
                return fn(objects, *args, **kwargs)[:limit]
            return fn(objects, *args, **kwargs)

        return limit_wrapper

    @staticmethod
    def first(fn: Callable[..., QuerySet]):
        def first_wrapper(objects: Manager, first=None, *args, **kwargs):
            if first is not None:
                return fn(objects, *args, **kwargs).first()
            return fn(objects, *args, **kwargs)

        return first_wrapper

    @staticmethod
    @only
    @prefetch_related
    @select_related
    @exclude
    @annotate
    @order_by
    @limit
    @first
    def all(objects: Manager) -> QuerySet:
        return objects.all()
