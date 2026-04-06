import re
from django.core.exceptions import ValidationError

class NumberAndLengthValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                "Hasło musi mieć co najmniej 8 znaków.",
                code='password_too_short',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                "Hasło musi zawierać co najmniej jedną cyfrę.",
                code='password_no_number',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Hasło musi zawierać co najmniej jedną małą literę.",
                code='password_no_lowercase',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Hasło musi zawierać co najmniej jedną wielką literę.",
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return "Hasło musi mieć co najmniej 8 znaków, zawierać co najmniej jedną cyfrę, jedną małą i jedną wielką literę."