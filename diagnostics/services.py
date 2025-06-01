from diagnostics.models import Diagnostic
from django.core.exceptions import ObjectDoesNotExist
def create_diagnostic(user, validated_data):

    diagnostic = Diagnostic.objects.create(
        user=user,
        type=validated_data['type'],
        score=validated_data['score'],
        level=validated_data['level'],
    )
    return diagnostic

def get_diagnostics_for_user(user):
    diagnostics = Diagnostic.objects.filter(user=user)
    if not diagnostics.exists():
        raise ObjectDoesNotExist("No diagnostics found for this user.")
    return diagnostics
def get_user_level(user_id):
    try:
        diagnostic = Diagnostic.objects.filter(user_id=user_id).order_by('-date_taken').first()
        if diagnostic:
            return diagnostic.level
        return None
    except Diagnostic.DoesNotExist:
        return None