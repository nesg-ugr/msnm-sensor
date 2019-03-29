from django import forms
import datetime

from base.validators import FileValidator
from image.models import Image


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['file']

    file = forms.FileField(validators=[FileValidator(
        content_types=[
            'image/png',
            'image/jpeg',
        ]
    )])