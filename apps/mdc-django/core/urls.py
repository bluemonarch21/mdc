from django.urls import path, re_path

from . import views

app_name = "core"
urlpatterns = [
    path("upload", views.upload_file, name="upload"),
    re_path(r"^(?!admin).*", views.index, name="index"),
]
