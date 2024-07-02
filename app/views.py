from .forms import RegistrationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect


def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(request, "registration/registration.html", {"form": form})


def dashboard(request):
    return render(request, "dashboard.html")
