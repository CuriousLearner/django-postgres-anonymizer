from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse


@login_required
def test_user_data(request):
    """Test view to see if dynamic masking works"""
    users = User.objects.all()[:5]

    user_data = []
    for user in users:
        user_data.append(
            {
                "username": user.username,
                "email": user.email,
            }
        )

    return JsonResponse(
        {
            "current_user": request.user.username,
            "user_groups": [g.name for g in request.user.groups.all()],
            "is_masked_user": request.user.groups.filter(name="view_masked_data").exists(),
            "users": user_data,
        }
    )
