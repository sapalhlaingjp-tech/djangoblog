from django.shortcuts import render

def home(request):
    return render(request,"blog/home.html",{"title":"This is the Djangoblog Homepage."})

def about(request):
    return render(request, "blog/about.html", {"content":"This is the Djangoblog team."})

def contact(request):
    return render(request, "blog/contact.html", {"title":"Song"})

def base(request):
    return render(request, "blog/base.html",{"title":"me"})
