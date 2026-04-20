def get_user_name(request):
    return (
        request.user.username
        if request.user.is_authenticated
        else "system"
    )