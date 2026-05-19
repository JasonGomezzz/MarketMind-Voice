from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cliente_nombre", "industria", "plataforma", "tono", "estado", "marketero", "fecha_creacion"]
    list_filter = ["estado", "plataforma", "tono"]
    search_fields = ["titulo", "cliente_nombre", "industria"]
    readonly_fields = ["fecha_creacion", "fecha_actualizacion"]
    ordering = ["-fecha_creacion"]
