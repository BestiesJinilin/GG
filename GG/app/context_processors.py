# GG/app/context_processors.py
# Adds role flags to every template automatically.

def role_context(request):
    if not request.user.is_authenticated:
        return {
            "user_role":         None,
            "is_admin":          False,
            "is_general_staff":  False,
            "is_financial_staff": False,
        }

    if request.user.is_superuser or request.user.username == "admin":
        return {
            "user_role":          "Admin",
            "is_admin":           True,
            "is_general_staff":   True,   # admin can do everything
            "is_financial_staff": True,
        }

    from .models import UserLog
    log  = UserLog.objects.filter(user=request.user).first()
    role = log.role if log else None

    return {
        "user_role":          role,
        "is_admin":           False,
        "is_general_staff":   role == "General Staff",
        "is_financial_staff": role == "Financial Staff",
    }