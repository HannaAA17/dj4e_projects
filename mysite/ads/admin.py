from django.contrib import admin
from ads.models import Ad, Comment
# Register your models here.

# Define the PicAdmin class
class AdAdmin(admin.ModelAdmin):
    exclude = ('picture', 'content_type')

admin.site.register(Ad, AdAdmin)
admin.site.register(Comment)
