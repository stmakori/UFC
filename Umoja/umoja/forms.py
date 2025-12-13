from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Contribution, Repayment, Withdrawal  # Make sure these models exist

class PaymentForm(forms.Form):
    """Base form for payment operations"""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2547XXXXXXXX',
            'required': True
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'required': True
        })
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Payment description'
        })
    )

class ContributionForm(forms.ModelForm):
    """Form for creating contributions"""
    class Meta:
        model = Contribution
        fields = ['amount', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RepaymentForm(forms.ModelForm):
    """Form for loan repayments"""
    class Meta:
        model = Repayment
        fields = ['amount', 'loan', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'loan': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class WithdrawalForm(forms.ModelForm):
    """Form for withdrawal requests"""
    class Meta:
        model = Withdrawal
        fields = ['amount', 'description', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

class UserRegistrationForm(UserCreationForm):
    """User registration form with email"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class UserLoginForm(AuthenticationForm):
    """User login form with Bootstrap classes"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

class PhonePaymentForm(forms.Form):
    """Form for collecting phone number for payment"""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2547XXXXXXXX',
            'required': True
        })
    )
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone_number = self.cleaned_data.get('phone_number')
        # Add phone number validation logic here
        return phone_number

class WebhookVerificationForm(forms.Form):
    """Form for verifying webhook signatures"""
    payload = forms.JSONField()
    signature = forms.CharField()
    
    def clean(self):
        cleaned_data = super().clean()
        # Add webhook signature verification logic here
        return cleaned_data
