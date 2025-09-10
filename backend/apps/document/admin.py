from django.contrib import admin
from django.db.models.functions import Substr

from .models import Document, SmartChunk

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "chunking_done",
        "preview_extracted_text",
        "owner_email",
        "created",
        "file",
    )
    search_fields = ("name", "extracted_text", "extracted_text")
    list_filter = ("chunking_status", "chunking_done", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "chunking_status", "chunking_done", "last_error", "retry_count")

    def created(self, obj):
        return obj.created_at.strftime("%Y/%m/%d %H:%M:%S")

    def file(self, obj):
        if obj.file:
            return obj.file.url
        return "No File"

    def owner_email(self, obj):
        return obj.owner.email if obj.owner else "No Owner"


    def preview_extracted_text(self, obj):
        return (obj.extracted_text[:50] + "...") if obj.extracted_text and len(obj.extracted_text) > 50 else obj.extracted_text
    preview_extracted_text.short_extracted_text = "extracted_text"


@admin.register(SmartChunk)
class SmartChunkAdmin(admin.ModelAdmin):
    # keep columns tiny
    list_display = ("id", "document", "chunk_index", "preview_content", "token_count", "created_at")
    list_select_related = ("document",)
    list_per_page = 50
    ordering = ("document", "chunk_index")
    show_full_result_count = False  # avoid expensive COUNT(*)

    # ✅ avoid LIKE on huge text; search small fields/FKs instead
    search_fields = ("id", "document__name", "chunk_index")
    # search_fields = ("content","chunk_index")

    # ✅ filter only by related docs that actually appear in the result set
    list_filter = (("document", admin.RelatedOnlyFieldListFilter),)

    # If your Document table is big, this keeps the widget snappy on forms
    autocomplete_fields = ("document",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ⚠️ Defer wide fields so the list view doesn't fetch them
        # replace/add other wide fields if you have them (e.g., 'embedding', 'metadata_json', 'tokens_json')
        qs = qs.defer("content")

        # ✅ Annotate a short preview at the DB level (won’t load full content into memory)
        qs = qs.annotate(_preview=Substr("content", 1, 120))
        return qs

    @admin.display(description="Content Preview")
    def preview_content(self, obj: SmartChunk):
        # Use DB-annotated preview; add ellipsis if original content is longer (best-effort without loading it)
        # If you want a precise ellipsis only when >120, store content length separately or annotate Length().
        preview = getattr(obj, "_preview", "") or ""
        # keep it compact in the table
        return (preview + "…") if len(preview) == 120 else preview