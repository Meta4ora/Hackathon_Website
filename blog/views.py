from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login

from django.shortcuts import render

def index(request):
    return render(request, 'index.html')
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # или куда хочешь
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})
