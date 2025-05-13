from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login
from django.http import HttpResponse

def index(request):
    return HttpResponse("Это главная страница блога.")
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # или куда хочешь
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})
