import time

from django import forms
from django.core import signing

from .models import Message

MIN_SECONDS_TO_FILL = 3          # humans take longer than this to write a message
MAX_FORM_AGE = 60 * 60 * 24      # a form left open for a day must be reloaded


class ContactForm(forms.ModelForm):
    # Spam traps: bots fill every field and submit instantly.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "tabindex": "-1", "autocomplete": "off", "class": "trap",
    }))
    ts = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = Message
        fields = ["name", "email", "body"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 100}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "body": forms.Textarea(attrs={"rows": 6, "maxlength": 5000}),
        }
        labels = {"name": "Your name", "email": "Your email", "body": "Message"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["ts"] = signing.dumps(time.time(), salt="contact-ts")

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) < 10:
            raise forms.ValidationError("Write at least a sentence so I know what it's about.")
        return body

    def clean(self):
        data = super().clean()
        if data.get("website"):
            raise forms.ValidationError("Your message couldn't be sent. Reload the page and try again.")
        try:
            started = signing.loads(data.get("ts", ""), salt="contact-ts", max_age=MAX_FORM_AGE)
        except signing.BadSignature:
            raise forms.ValidationError("This form has expired. Reload the page and try again.")
        if time.time() - float(started) < MIN_SECONDS_TO_FILL:
            raise forms.ValidationError("That was fast. Wait a moment and send it again.")
        return data
