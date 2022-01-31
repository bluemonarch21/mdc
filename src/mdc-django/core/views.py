import datetime
import json
import time

from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from mysite.settings import BASE_DIR

from .forms import UploadFileForm


def index(request):
    with open(BASE_DIR / "core/static/main-assets.json", "r") as file:
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
            grade = handle_uploaded_file(request.FILES["file"])
            time.sleep(3)
            return HttpResponse(str(grade), status=200)
        else:
            print("form is invalid")
    else:
        form = UploadFileForm()
    return HttpResponse("bad input", status=400)


def handle_uploaded_file(f: UploadedFile) -> int:
    date = datetime.datetime.now()
    path = BASE_DIR / "userupload"
    if not path.exists():
        path.mkdir()
    with open(BASE_DIR / f"userupload/{hash(date) % 10 ** 8}-{f.name}", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return hash(f.name) % 9 + 1
