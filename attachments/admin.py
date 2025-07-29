from django.contrib import admin

from .models import FileAttachment, AudioAttachment


admin.site.register(FileAttachment)
admin.site.register(AudioAttachment)