from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from learningmodules.services import generate_module_content

class GenerateModuleContentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        module_id = request.data.get("module_id")
        
        if not module_id:
            return Response({"error": "Se requiere 'module_id' en el body."}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_module_content(user_id=request.user.id, module_id=module_id)

        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)
