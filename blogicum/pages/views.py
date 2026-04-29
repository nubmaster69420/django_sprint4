from django.shortcuts import render


def about(request):
    template = "pages/about.html"
    return render(request, template)


def rules(request):
    template_name = "pages/rules.html"
    return render(request, template_name)
