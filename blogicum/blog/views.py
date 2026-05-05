from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.db.models import Count

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm

User = get_user_model()


def get_published_posts():
    return Post.objects.select_related(
        'category',
        'location',
        'author'
    ).annotate(
        comment_count=Count('comments')
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')


def paginate(request, queryset):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = "blog/index.html"
    page_obj = paginate(request, get_published_posts())
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    template = "blog/detail.html"
    post = get_object_or_404(
        Post.objects.select_related(
            'category',
            'location',
            'author'
        ).annotate(comment_count=Count('comments')),
        pk=post_id
    )
    if post.author != request.user:
        if (not post.is_published or 
            not post.category or 
            not post.category.is_published or 
            post.pub_date > timezone.now()):
            raise Http404
    
    comments = post.comments.select_related('author')
    form = CommentForm()
    
    context = {
        "post": post,
        "form": form,
        "comments": comments,
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
    page_obj = paginate(request, post_list)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template, context)


class ProfileListView(ListView):
    model = Post
    template_name = "blog/profile.html"
    paginate_by = 10
    context_object_name = "page_obj"

    def get_queryset(self):
        self.profile = get_object_or_404(User, username=self.kwargs["username"])
        queryset = Post.objects.filter(author=self.profile).annotate(
            comment_count=Count("comments")
        ).order_by("-pub_date")
        if self.request.user == self.profile:
            return queryset
        return get_published_posts().filter(author=self.profile).order_by("-pub_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "blog/user.html"
    fields = ["username", "first_name", "last_name", "email"]

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs["post_id"])
        if instance.author != request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.kwargs["post_id"]})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs["post_id"])
        if instance.author != request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.kwargs["post_id"]})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs["comment_id"])
        if instance.author != request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.kwargs["post_id"]})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs["comment_id"])
        if instance.author != request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.kwargs["post_id"]})
