from django import forms

from users.validators import validate_github_url

from .models import Project


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус",
        choices=[(Project.Status.OPEN, "Открыт"), (Project.Status.CLOSED, "Закрыт")],
        initial=Project.Status.OPEN,
    )

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def clean_github_url(self):
        url = (self.cleaned_data.get("github_url") or "").strip()
        validate_github_url(url)
        return url
