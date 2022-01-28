import json

from django.http import HttpResponse
from django.shortcuts import render
from mysite.settings import BASE_DIR


def index(request):
    with open(BASE_DIR / "core/static/js/assets/main-assets.json", "r") as file:
        main_assets = json.load(file)
    context = {
        "css": main_assets["css"],
        "js": main_assets["js"],
    }
    return render(request, "core/index.html", context)


def index2(request):
    with open(BASE_DIR / "../mdc-ui/dist/index.html", "rb") as file:
        return HttpResponse(file.read(), None, None)
