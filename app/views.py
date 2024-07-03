from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from .forms import RegistrationForm
from .tokens import account_activation_token
from .models import OTP

User = get_user_model()


def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get("email")
            activation_method = request.POST.get("activation_method")

            if User.objects.filter(email=email).exists():
                form.add_error("email", "Email already exists. Try another one.")
            else:
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                if activation_method == "link":
                    send_activation_email(request, user)
                    return redirect("activation_sent")
                else:
                    send_otp_email(user)
                    return render(request, "registration/otp_verification.html")
    else:
        form = RegistrationForm()

    return render(request, "registration/registration.html", {"form": form})


def send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"

    mail_subject = "Activate your account"
    message = render_to_string(
        "registration/activation_email.html",
        {
            "user": user,
            "activation_link": activation_link,
        },
    )

    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])


def send_otp_email(user):
    otp_instance, created = OTP.objects.get_or_create(user=user)
    otp_instance.generate_otp()

    mail_subject = "Your OTP code"
    message = f"Your OTP code is {otp_instance.otp}. It is valid for 15 minutes."

    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [user.email])


def resend_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                send_otp_email(user)
                return redirect("verify_otp")
            else:
                return redirect("dashboard")
        except User.DoesNotExist:
            return render(request, "registration/otp_invalid.html")

    return render(request, "registration/resend_otp.html")


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


def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")

        try:
            user = User.objects.get(email=email)
            otp_instance = OTP.objects.get(user=user)

            if otp_instance.is_valid() and otp_instance.otp == otp:
                user.is_active = True
                user.save(otp=0)
                otp_instance.delete()  # delete OTP after successful verification
                login(request, user)
                return redirect("dashboard")
            else:
                return render(request, "registration/otp_invalid.html")
        except (User.DoesNotExist, OTP.DoesNotExist):
            return render(request, "registration/otp_invalid.html")
    else:
        pass

    return render(request, "registration/otp_verification.html")


def dashboard(request):
    return render(request, "dashboard.html")
