from django import forms
from .models import AttendanceSession
from accounts.models import Course


class SessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['course', 'date', 'section', 'start_time', 'mode']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, faculty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty:
            self.fields['course'].queryset = faculty.courses.all()
