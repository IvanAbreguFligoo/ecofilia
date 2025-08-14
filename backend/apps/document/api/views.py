from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.db.models import Q

from apps.document.models import SmartChunk, Document
from apps.document.api.filters import DocumentFilter
from apps.document.api.serializers import SmartChunkSerializer, DocumentSerializer,DocumentCreateSerializer


class RAGQueryView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({"error": "Missing query parameter"}, status=status.HTTP_400_BAD_REQUEST)

        
        user = request.user
        if user.is_staff:
            qs = SmartChunk.objects.all()
        else:
            qs = SmartChunk.objects.filter(
                Q(document__owner=user) | Q(document__is_public=False)
            )
        
        slugs = request.query_params.getlist("documents")
        if slugs:
            qs = qs.filter(document__slug__in=slugs)

        public_param = request.query_params.get("public")

        if public_param is not None:
            if public_param.lower() == "false":
                qs = qs.filter(document__is_public=False)
            elif public_param.lower() != "true":
                return Response({"error": "Invalid 'public' value. Use 'true' or 'false'."},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            chunks = qs.top_similar(query)
            serializer = SmartChunkSerializer(chunks, many=True)
            return Response({"query": query, "results": serializer.data})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset=Document.objects.all()
    serializer_class=DocumentCreateSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(owner=request.user)

        # Use output serializer for the response
        response_serializer = DocumentSerializer(document, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    

class DocumentListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_class = DocumentFilter
    
    def get_queryset(self):
        qs = Document.objects.all()
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(owner=user)

        return qs