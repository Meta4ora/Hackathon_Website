from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login
from .models import PublicEvent

def index(request):
    events = PublicEvent.objects.all().order_by('-start_date')[:6]  # Последние 6 мероприятий
    return render(request, 'index.html', {'events': events})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})