from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from learningmodules.services import generate_module_content
from learningmodules.services import get_learning_module_by_id
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

class GetLearningModuleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, module_id):
        try:
            module_data = get_learning_module_by_id(module_id)
            return Response(module_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
