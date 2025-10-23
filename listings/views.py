from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, permissions

from .models import Listing
from .forms import ListingForm
from .serializers import ListingSerializer

class ListingListView(ListView):
    model = Listing
    paginate_by = 12
    template_name = 'listings_list.html'
    def get_queryset(self):
        qs = super().get_queryset().order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

class ListingCreateView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listing_create.html'
    success_url = reverse_lazy('listing_list')
    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

class ListingDetailView(DetailView):
    model = Listing
    template_name = 'listing_detail.html'

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by('-created_at')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
