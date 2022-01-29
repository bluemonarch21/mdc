import datetime
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from mysite.settings import BASE_DIR

from .forms import UploadFileForm


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


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES["file"])
            print("uploaded")
            return HttpResponseRedirect("/success/url/")
        else:
            print("form is invalid")
    else:
        form = UploadFileForm()
    return HttpResponseRedirect("/unsuccess/url/")


def handle_uploaded_file(f):
    date = datetime.datetime.now()
    with open(BASE_DIR / f"./userupload/{hash(date)}", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
