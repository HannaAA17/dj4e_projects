from django.views import View
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DeleteView, ListView

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError

from ads.models import Ad, Comment, Fav
from ads.forms import CreateForm, CommentForm

from django.db.models import Q

class AdListView(ListView):
    model = Ad
    # By convention:
    # template_name = 'ads/ad_list.html'
    
    def get_queryset(self):
        search = self.request.GET.get('search', False)
        
        if not search:
            # return super().get_queryset()
            # return self.model.objects.order_by('-updated_at')[:10]
            return self.model.objects.all()[:10]
        
        else:
            search = search.strip()
            # __icontains for case-insensitive search
            qs_filter = Q(title__icontains=search) | Q(text__icontains=search) | Q(tags__name__in=[search])
            # select_related => extract the related objects ad.tags.all
            return self.model.objects.filter(qs_filter).distinct().select_related()[:10]
       
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            rows = self.request.user.favorite_ads.values('id')
            # rows = [{'id': 2}, {'id': 4} ... ]  (A list of rows)
            context['favorites'] = [ row['id'] for row in rows ]
        
        else:
            context['favorites'] = []
        
        context['search'] = self.request.GET.get('search', False)
        
        return context


class AdDetailView(View):
    template_name = 'ads/ad_detail.html'
    
    def get(self, request, pk) :
        x = get_object_or_404(Ad, id=pk)
        comments = Comment.objects.filter(ad=x).order_by('-updated_at')
        comment_form = CommentForm()
        context = { 
            'ad' : x, 'comments': comments, 'comment_form': comment_form 
        }
        return render(request, self.template_name, context)


class AdCreateView(LoginRequiredMixin, View):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk=None):
        form = CreateForm()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        # Add owner to the model before saving
        ad = form.save(commit=False)
        ad.owner = self.request.user
        ad.save()
        
        # save tags
        form.save_m2m()
        
        return redirect(self.success_url)


def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    response = HttpResponse()
    response['Content-Type'] = ad.content_type
    response['Content-Length'] = len(ad.picture)
    response.write(ad.picture)
    return response


class AdUpdateView(LoginRequiredMixin, View):
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(instance=ad)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=ad)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        ad = form.save(commit=False)
        ad.save()
        
        # save tags
        form.save_m2m()
        
        return redirect(self.success_url)


class AdDeleteView(LoginRequiredMixin, DeleteView):
    model = Ad
    
    def get_queryset(self):
        print('delete get_queryset called')
        qs = super(DeleteView, self).get_queryset()
        return qs.filter(owner=self.request.user)


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        f = get_object_or_404(Ad, id=pk)
        comment = Comment(text=request.POST['comment'], owner=request.user, ad=f)
        comment.save()
        return redirect(reverse('ads:ad_detail', args=[pk]))


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    # template_name = 'ads/comment_delete.html'
    
    def get_queryset(self):
        print('delete get_queryset called')
        qs = super(DeleteView, self).get_queryset()
        return qs.filter(owner=self.request.user)
    
    # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
    def get_success_url(self):
        ad = self.object.ad
        return reverse('ads:ad_detail', args=[ad.id])

# csrf exemption in class based views
# https://stackoverflow.com/questions/16458166/how-to-disable-djangos-csrf-validation

@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print('Add PK', pk)
        t = get_object_or_404(Ad, id=pk)
        fav = Fav(ad=t, user=request.user)
        try:
            fav.save()  # In case of duplicate key
        except IntegrityError as e:
            pass
        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print('Delete PK', pk)
        t = get_object_or_404(Ad, id=pk)
        try:
            fav = Fav.objects.get(ad=t, user=request.user).delete()
        except Fav.DoesNotExist as e:
            pass
        return HttpResponse()
