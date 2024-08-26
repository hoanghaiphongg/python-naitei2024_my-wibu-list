from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, LoginForm, CommentForm, EditCommentForm, ChangePasswordForm
from django.contrib.auth.forms import UserCreationForm
from django.views import generic, View
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.contrib.auth.hashers import check_password,make_password

from django.db.models import Q
# import data from constants.py
from wibu_catalog.constants import Role_dict, Score_dict, ITEMS_PER_PAGE_MORE
from wibu_catalog.constants import ITEMS_PER_PAGE, Content_category
from wibu_catalog.constants import Manga_status, Anime_status
from wibu_catalog.constants import Manga_rating, Anime_rating
from wibu_catalog.constants import FIELD_MAX_LENGTH_S, FIELD_MAX_LENGTH_M
from wibu_catalog.constants import FIELD_MAX_LENGTH_L, FIELD_MAX_LENGTH_XL

# import models form models.py
from wibu_catalog.models import Content, Score, Users, FavoriteList
from wibu_catalog.models import ScoreList, Comments, Notifications
from wibu_catalog.models import Product, Order, OrderItems, Feedback

from .constants import TOP_WATCHING_LIMIT, LATEST_CONTENT_LIMIT, TOP_RANKED_LIMIT
from wibu_catalog.constants import ITEMS_PER_PAGE
from django.contrib.auth.hashers import check_password

from django.contrib import messages
from functools import wraps
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist
from random import randint
from enum import Enum

# Function definition:
def _get_user_from_session(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return Users.objects.get(uid=user_id)
        except Users.DoesNotExist:
            return None
    return None

def homepage(request):
    userr = _get_user_from_session(request)
    top_watching_content = Content.objects.order_by('-watching')[:TOP_WATCHING_LIMIT]

    latest_content = Content.objects.order_by('-lastUpdate')[:LATEST_CONTENT_LIMIT]

    top_ranked_content = Content.objects.order_by('ranked')[:TOP_RANKED_LIMIT]

    content_random = randint(1,17562)
    what_to_watch = None
    while (what_to_watch is None):
        content_random = randint(1,17562)
        try:
            what_to_watch = Content.objects.get(cid=content_random)
        except ObjectDoesNotExist:
            what_to_watch = None

    return render(request, 'html/homepage.html', {
        'top_watching_content': top_watching_content,
        'latest_content': latest_content,
        'top_ranked_content': top_ranked_content,
        'userr': userr,
        'what_to_watch': what_to_watch,
    })


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


def logout(request):
    request.session.flush()
    return redirect('homepage')


# Comment section:
def post_comment(request, content_id):
    userr = _get_user_from_session(request)
    cmtedContent = get_object_or_404(Content, cid=content_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.cid = cmtedContent
            comment.uid = userr
            comment.dateOfCmt = timezone.now().date()
            comment.save()
            # debuging corner
            print("Comment saved:", comment)  # Debugging line
            print(Comments.objects.filter(uid=userr, cid=cmtedContent))
            return redirect('anime_detail', pk=content_id)
    return redirect('anime_detail', pk=content_id)


def edit_comment(request, comment_id):
    userr = _get_user_from_session(request)
    try:
        comment = Comments.objects.get(id=comment_id, uid=userr.uid)
    except Comments.DoesNotExist:
        return redirect('anime_detail', pk=comment.cid.cid)

    if request.method == 'POST':
        form = EditCommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.dateOfCmt = timezone.now().date()  # Update the date
            comment.save()
            return redirect('anime_detail', pk=comment.cid.cid)
            # somehow comment.cid = Content.__str__
    else:
        form = EditCommentForm(instance=comment)

    return redirect('anime_detail', pk=comment.cid.cid)


def delete_comment(request, comment_id):
    userr = _get_user_from_session(request)

    try:
        comment = Comments.objects.get(id=comment_id)
        comment.delete()
    except Comments.DoesNotExist:
        return redirect('anime_detail', pk=comment.cid.cid)
    return redirect('anime_detail', pk=comment.cid.cid)
# end of Comment section


def list_product(request):
    userr = _get_user_from_session(request)
    query = request.GET.get('q', '')  # Lấy từ khóa tìm kiếm từ URL, mặc định là chuỗi rỗng
    sort_by = request.GET.get('sort_by', 'id')  # Giá trị mặc định là 'id'

    # Tìm kiếm sản phẩm theo từ khóa
    if query:
        products_list = Product.objects.filter(name__icontains=query)
    else:
        products_list = Product.objects.all()

    # Sắp xếp sản phẩm theo yêu cầu
    if sort_by == 'highest_rate':
        products_list = products_list.order_by('-ravg')
    elif sort_by == 'low_to_high':
        products_list = products_list.order_by('price')
    elif sort_by == 'high_to_low':
        products_list = products_list.order_by('-price')

    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'html/warehouse.html', {'products': products, 'current_sort': sort_by, 'query': query,"userr":userr})


def search_content(request):
    query = request.GET.get('q','').lower()
    search_results = None
    if query:
        search_results = Content.objects.filter(name__icontains=query)
    else:
        search_results = Content.objects.all()  # Nếu không có từ khóa, hiển thị tất cả

    return render(request, 'html/search_content_results.html', {'search_results': search_results,})


def filter_by_genre(request, genre):
    userr = _get_user_from_session(request)

    # Lọc content theo thể loại và sắp xếp theo scoreAvg
    filtered_content = Content.objects.filter(genres__icontains=genre).order_by('-scoreAvg')[:ITEMS_PER_PAGE]

    context = {
        'filtered_content': filtered_content,
        'selected_genre': genre,
        'userr': userr
    }
    return render(request, 'html/filtered_content.html', context)


# Class definition:
class AnimeListView(generic.ListView):
    """Class based view for anime list."""
    model = Content
    context_object_name = "anime_list"
    paginate_by = ITEMS_PER_PAGE_MORE
    template_name = "html/anime_list.html"

    def get_queryset(self):
        return Content.objects.filter(category="anime")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userr = _get_user_from_session(self.request)
        context["userr"] = userr
        return context


class AnimeDetailView(generic.DetailView):
    """Class based view for anime detail."""
    model = Content
    context_object_name = "anime_detail"
    template_name = "html/anime_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content_instance = self.get_object()
        score_data_ = content_instance.score_data.all()
        userr = _get_user_from_session(self.request)
        comments_list = Comments.objects.filter(cid=content_instance.cid).order_by('-dateOfCmt')
        paginator = Paginator(comments_list, 5)
        page_number = self.request.GET.get('page')
        comments = paginator.get_page(page_number)

        favorite = None
        if userr:
            favorite = FavoriteList.objects.filter(uid=userr, cid=content_instance).first()

        # User score
        if userr != None:
            score_str = score_to_str(content_instance.cid, userr.uid)
        else:
            score_str = None
        # Sumarize context
        context["score_"] = score_data_
        context["userr"] = userr
        context["comments"] = comments
        context["score_str"] = score_str
        context["favorite"] = favorite
        return context

class MangaListView(generic.ListView):
    """Class for the view of the book list."""
    model = Content
    paginate_by = ITEMS_PER_PAGE_MORE
    context_object_name = "manga_list"
    template_name = "html/manga_list.html"

    def get_queryset(self):
        return Content.objects.filter(category='manga').all()


class MangaDetailView(generic.DetailView):
    model = Content
    context_object_name = "manga_detail"
    template_name = "html/manga_detail.html"

    # passing Score to view
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content_instance = self.get_object()
        score_data_ = content_instance.score_data.all()
        context['score_'] = score_data_
        return context


class LoginView(View):
    def _authenticate_user(self, email, password):
        try:
            user = Users.objects.get(email=email)
            if check_password(password, user.password):
                return user
            else:
                return None
        except Users.DoesNotExist:
            return None

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = self._authenticate_user(email=email, password=password)
        if user is not None:
            request.session['user_id'] = user.uid
            return redirect('homepage')
        else:
            form = LoginForm()
            return render(request, 'html/loginform.html', {'form': form})

    def get(self, request):
        form = LoginForm()
        return render(request, 'html/loginform.html', {'form': form})


class FavoriteListView(generic.ListView):
    """Class based view for favorite anime list."""
    model = Content
    context_object_name = "favorites_list"
    paginate_by = ITEMS_PER_PAGE_MORE
    template_name = "html/favorites_list.html"

    def get_queryset(self):
        userr = _get_user_from_session(self.request)
        if userr:
            # favListInstance = FavoriteList.objects.get(uid=userr.uid)
            # return FavoriteList.objects.filter(uid=userr).select_related('cid')
            # return Content.objects.filter(category='manga').all()
            favorite_content_cids = FavoriteList.objects.filter(uid=userr).values_list('cid', flat=True)
            return Content.objects.filter(cid__in=favorite_content_cids)
        return FavoriteList.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userr = _get_user_from_session(self.request)
        context["userr"] = userr
        return context

def require_login(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        userr = _get_user_from_session(request)
        if not userr:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@require_login
def user_profile(request):
    user_id = request.session.get('user_id')
    try:
        userr = Users.objects.get(uid=user_id)
    except Users.DoesNotExist:
        return redirect('homepage')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        date_of_birth = request.POST.get('dateOfBirth')

        #Update
        userr.username = username
        userr.email = email
        userr.dateOfBirth = date_of_birth
        userr.save()

        messages.success(request, _('Profile updated successfully!'))
        return redirect('user_profile')

    return render(request, 'html/user_profile.html', {'userr': userr})


@require_login
def update_favorite_status(request, content_id):
    userr = _get_user_from_session(request)
    if not userr:
        return HttpResponseForbidden(_("You must be logged in to update your status."))

    content_instance = get_object_or_404(Content, cid=content_id)

    status = request.POST.get('status')

    if status in ['1', '2', '3', '5', '6']:
        favorite, created = FavoriteList.objects.get_or_create(
            uid=userr,
            cid=content_instance,
        )
        favorite.status = status
        favorite.save()
    else:
        FavoriteList.objects.filter(uid=userr, cid=content_instance).delete()

    return redirect('anime_detail', pk=content_id)


@require_login
def update_score(request, content_id):
    """ Function to add or update content score rated by user """
    userr = _get_user_from_session(request)
    if not userr:
        return HttpResponseForbidden(_("You must be logged in to rate or update rated score."))

    content_instance = get_object_or_404(Content, cid=content_id)

    if request.method == 'POST':
        score, created = ScoreList.objects.get_or_create(
            uid=userr,
            cid=content_instance,
        )
        score.score = request.POST.get('score')
        score.save()

    return redirect('anime_detail', pk=content_id)

class ScoreEnum(Enum):
    """ In case want to display not just score"""
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"

def score_to_str(content_cid, user_uid):
    try:
        user_score = ScoreList.objects.get(cid=content_cid, uid=user_uid)
        score_int = user_score.score
        return ScoreEnum(str(score_int)).value
    except ObjectDoesNotExist:
        return None

class ChangePassword(View):
    def post(self, request):
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password_confirmation = request.POST.get('new_password_confirmation')
        userr = _get_user_from_session(request)

        if check_password(old_password, userr.password) and new_password == new_password_confirmation:
            userr.password = make_password(new_password)
            userr.save()
            return redirect('homepage')
        else:
            form = ChangePasswordForm()
            return render(request, 'html/change_password.html', {'form': form})

    def get(self, request):
        form = ChangePasswordForm()
        return render(request, 'html/change_password.html', {'form': form})

