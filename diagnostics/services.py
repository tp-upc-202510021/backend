from diagnostics.models import Diagnostic

def create_diagnostic(user, validated_data):

    diagnostic = Diagnostic.objects.create(
        user=user,
        type=validated_data['type'],
        score=validated_data['score'],
        level=validated_data['level'],
    )
    return diagnostic
