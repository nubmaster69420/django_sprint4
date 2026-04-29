from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import Post, Category


def get_published_posts():
    return Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


def index(request):
    template = "blog/index.html"

    post_list = get_published_posts()[:5]
    context = {'post_list': post_list}
    return render(request, template, context)


def post_detail(request, id):
    template = "blog/detail.html"
    post = get_object_or_404(get_published_posts(), pk=id)
    context = {
        "post": post,
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = "blog/category.html"
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = get_published_posts().filter(category=category)
    context = {
        'category': category,
        'post_list': post_list,
    }
    return render(request, template, context)
