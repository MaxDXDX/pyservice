from pyservice.django import views

from {{ app.app_name }} import manager


logger = manager.get_logger_for_pyfile(__file__, with_path=True)


class RestViewBase(views.RestViewBaseAbstract):
    log = logger
    app_manager = manager