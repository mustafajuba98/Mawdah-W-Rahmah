from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from apps.accounts.models import User

from .forms import ConsoleUserCreateForm, ConsoleUserEditForm


def _superuser(u):
    return u.is_authenticated and u.is_superuser


@user_passes_test(_superuser)
def dashboard(request):
    qs = User.objects.all()
    by_status = dict(
        qs.values("profile_status")
        .annotate(c=Count("id"))
        .values_list("profile_status", "c")
    )
    breakdown = [
        (label, by_status.get(code, 0)) for code, label in User.ProfileStatus.choices
    ]
    ctx = {
        "total_users": qs.count(),
        "active_members": qs.filter(profile_status=User.ProfileStatus.ACTIVE).count(),
        "pending_review": qs.filter(profile_status=User.ProfileStatus.PENDING_REVIEW).count(),
        "breakdown": breakdown,
    }
    return render(request, "console/dashboard.html", ctx)


class ConsoleUserListView(ListView):
    model = User
    template_name = "console/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return user_passes_test(_superuser)(view)

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(applicant_profile__full_name__icontains=q))
        st = self.request.GET.get("status")
        if st in dict(User.ProfileStatus.choices):
            qs = qs.filter(profile_status=st)
        return qs.select_related("applicant_profile").prefetch_related("groups")


@user_passes_test(_superuser)
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ConsoleUserEditForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, "تم حفظ التعديلات.")
            return redirect("console_user_list")
    else:
        form = ConsoleUserEditForm(instance=target)
    return render(
        request,
        "console/user_form.html",
        {"form": form, "target_user": target, "is_create": False},
    )


@user_passes_test(_superuser)
def user_create(request):
    if request.method == "POST":
        form = ConsoleUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إنشاء المستخدم والملف التجريبي.")
            return redirect("console_user_list")
    else:
        form = ConsoleUserCreateForm()
    return render(
        request,
        "console/user_create.html",
        {"form": form},
    )
