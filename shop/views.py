
from django.shortcuts import render,HttpResponse


# Create your views here.
def product_list(request):
    return render(request, "list.html")

def login(request):
    if request.method == "GET":
        return render(request,"login.html")
    else:
        #print(request.POST)
        username = request.POST.get("user")
        password = request.POST.get("password")

        if username == "user" and password == "123":
            return render(request,"list.html")
        else:
            return render(request,"login.html", {"error_msg":"Error!"})