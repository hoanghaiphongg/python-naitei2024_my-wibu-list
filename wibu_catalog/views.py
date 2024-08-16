from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth.forms import UserCreationForm
from .models import Product


def homepage(request):
    return render(request, 'html/homepage.html')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('homepage')
    else:
        form = RegistrationForm()
    return render(request, 'html/registerform.html', {'form': form})

def product(request):
    products = Product.objects.all()
    return render(request, 'html/warehouse.html',{'products': products})

def search_products(request):
    query = request.GET.get('q', '').lower()
    products = None

    if query in ['one piece', 'one pieace']:
        products = Product.objects.filter(cid_id=12)
    elif query in ['naruto']:
        products = Product.objects.filter(cid_id=11)
    elif query in ['gundam']:
        products = Product.objects.filter(cid_id=61)
    
    return render(request, 'html/search_results.html', {'products': products})
