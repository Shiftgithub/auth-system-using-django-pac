from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login
from .forms import RegistrationForm
from .tokens import account_activation_token

User = get_user_model()


def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get("email")

            if User.objects.filter(email=email).exists():
                form.add_error("email", "Email already exists. Try another one.")
            else:
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                # Send activation email
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)
                activation_link = (
                    f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"
                )

                mail_subject = "Activate your account"
                message = render_to_string(
                    "registration/activation_email.html",
                    {
                        "user": user,
                        "activation_link": activation_link,
                    },
                )

                send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])

                return redirect("activation_sent")
    else:
        form = RegistrationForm()

    return render(request, "registration/registration.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect("dashboard")
    else:
        return render(request, "registration/activation_invalid.html")


def dashboard(request):
    return render(request, "dashboard.html")
