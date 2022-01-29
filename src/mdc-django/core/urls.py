from django.urls import re_path

from . import views

app_name = "core"
urlpatterns = [
    re_path(r"^(?!admin).*", views.index2, name="index"),
]
