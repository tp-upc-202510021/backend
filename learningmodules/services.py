import json
import re
from google import genai
from diagnostics.models import Diagnostic, LearningSection
from diagnostics.services import get_user_level
from decouple import config
from learningmodules.models import LearningModule
from django.core.exceptions import ObjectDoesNotExist

from users.models import User

client = genai.Client(api_key=config("GEMINI_API_KEY"))

def create_learning_modules(user_id: int, learning_path_id: int) -> list:
    """
    Crea y asigna módulos de aprendizaje a una ruta (LearningPath) basándose 
    en el último diagnóstico de un usuario y las secciones predefinidas.

    Esta función NO usa Gemini. En su lugar, selecciona LearningSection
    existentes cuyos learning_index coinciden con los guardados en el
    campo 'modules' del diagnóstico del usuario.

    Args:
        user_id: El ID del usuario para quien se crea la ruta.
        learning_path_id: El ID de la ruta de aprendizaje a la que se asociarán los módulos.

    Returns:
        Una lista de diccionarios, cada uno representando un LearningModule creado.
    
    Raises:
        ValueError: Si la ruta de aprendizaje ya tiene módulos, o si el usuario
                    no tiene un diagnóstico o perfil válido.
    """
    if LearningModule.objects.filter(learning_path=learning_path_id).exists():
        raise ValueError("Los módulos para esta ruta de aprendizaje ya han sido creados.")

    try:
        user = User.objects.get(id=user_id)
        

        if not hasattr(user, 'preference') or not user.preference:
             raise ValueError("El usuario no tiene una preferencia ('loans' o 'investments') definida.")
        
        user_preference = user.preference

        latest_diagnostic = Diagnostic.objects.filter(user=user).order_by('-date_taken').first()
        if not latest_diagnostic:
            raise ValueError("El usuario no tiene un diagnóstico registrado para generar la ruta.")

 
        recommended_indexes = latest_diagnostic.modules
        if(user.preference == 'loans'):
            recommended_indexes.extend([21, 22, 23, 24, 25, 26])
        elif(user.preference == 'investments'):
            recommended_indexes.extend([21])
        if not recommended_indexes:
            raise ValueError("El diagnóstico del usuario no contiene módulos recomendados.")
            
       
        sections_to_assign = LearningSection.objects.filter(
            preference=user_preference,
            learning_index__in=recommended_indexes
        ).order_by('learning_index') 

        if not sections_to_assign:
            raise ValueError("No se encontraron secciones de aprendizaje para los módulos recomendados.")

        
        created_modules = []
        for index, section in enumerate(sections_to_assign):
            is_module_blocked = (index > 0)
            module_obj = LearningModule.objects.create(
                learning_path_id=learning_path_id,
                title=section.title,
                description=section.description,
                level='-', 
                order_index=section.learning_index,  
                content=None,  
                is_blocked=is_module_blocked
            )
            created_modules.append(module_obj)


        response_data = [{
            "id": module.id,
            "learning_path_id": module.learning_path.id,
            "title": module.title,
            "description": module.description,
            "level": module.level,
            "order_index": module.order_index,
            "is_blocked": module.is_blocked
        } for module in created_modules]

        return response_data

    except User.DoesNotExist:
        raise ValueError("El usuario especificado no existe.")
    except Exception as e:
        raise ValueError(f"Ocurrió un error inesperado: {str(e)}")

def generate_module_content(user_id, module_id):

    try:
        diagnostic = Diagnostic.objects.get(user_id=user_id)
        user_level = diagnostic.level
        module = LearningModule.objects.get(id=module_id)


        generate_content_prompt = f"""
Actúa como un educador financiero experto y un creador de contenido multimedia, especializado en el mercado peruano.

Tu tarea es generar el contenido completo para un módulo de aprendizaje basándote en su título, descripción y el nivel del usuario. El resultado final debe ser un objeto JSON único y bien formado, sin ningún texto o formato adicional.

**Datos del Módulo de Entrada:**
- **Título del Módulo:** "{module.title}"
- **Descripción del Módulo:** "{module.description}"
- **Nivel del Usuario:** "{user_level}"

**Notas muy importantes a tener en cuenta**
-**El tono de tu respuesta debe ser(Esto es a solicitud del usuario):** "{diagnostic.response_tone}"
- **Motivación del Usuario:** "{diagnostic.motivation}"

**Requisitos Estrictos de Salida:**
Debes generar un objeto JSON que contenga una única clave principal llamada `pages`. El valor de `pages` debe ser una lista (array) de 3 objetos, en un orden específico.

Cada objeto en la lista debe tener EXACTAMENTE la siguiente estructura: `{{"type": "...", "content": "..."}}`.

**Ejemplo de la Estructura JSON Final (limpio y claro para la IA):**
{{
  "pages": [
    {{
      "type": "informative",
      "content": "# Título Teórico\\n\\nExplicación teórica, clara y concisa aquí..."
    }},
    {{
      "type": "practical",
      "content": "## Ejemplo Práctico\\n\\nUn caso práctico o cálculo simplificado aquí..."
    }},
    {{
      "type": "video",
      "content": "https://www.youtube.com/watch?v=xxxxxxxxxxx"
    }}
  ]
}}

**Instrucciones para la lista `pages`:**
Debes generar la lista con 3 elementos en este orden exacto:

1.  **Primer Objeto (Informativo):**
    -   `type`: Debe ser la cadena de texto `"informative"`.
    -   `content`: Crea el contenido educativo **TEÓRICO** principal en formato **Markdown**. Debe ser claro, muy conciso, optimizado para 1 pantalla de celular y explicar los conceptos fundamentales del módulo. Ten en cuenta el tono de respuesta del usuario.

2.  **Segundo Objeto (Práctico):**
    -   `type`: Debe ser la cadena de texto `"practical"`.
    -   `content`: Proporciona un **ejemplo PRÁCTICO y CONCRETO** en formato **Markdown** relacionado con la teoría. Debe mostrar cómo se aplica el concepto en una situación real del mercado peruano. Debe estar optimizado para 1 pantalla de celular. Ten en cuenta el tono de respuesta del usuario y, SOLO SI ES POSIBLE, si se pueda aplicar su motivación

3.  **Tercer Objeto (Video):**
    -   `type`: Debe ser la cadena de texto `"video"`.
    -   `content`: Busca y proporciona **UN ÚNICO enlace URL** a un video de YouTube relevante. El video debe durar entre 3 y 7 minutos, ser de una fuente confiable, estar disponible y tener un enlace válido.

**¡¡MUY IMPORTANTE!!**
Tu respuesta debe ser **EXCLUSIVAMENTE el objeto JSON**. No incluyas texto introductorio como "Aquí está el JSON:", despedidas, explicaciones, ni ```json. La salida debe ser el JSON puro para que pueda ser procesado directamente por un programa.
"""

        # 4. Llamar a la API de Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",  # Modelo recomendado, puedes usar el que prefieras
            contents=generate_content_prompt,
        )
        
        # 5. Procesar la respuesta para convertirla en un objeto JSON
        try:
            # La API puede devolver el texto JSON envuelto en ```json ... ```, lo limpiamos por si acaso
            clean_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            content_object = json.loads(clean_response_text)
        except json.JSONDecodeError:
            # Este error ocurre si la respuesta de la IA no es un JSON válido
            raise ValueError(f"La respuesta de la API no pudo ser decodificada como JSON. Respuesta recibida: {response.text}")

        # 6. Guardar el objeto JSON en la base de datos
        module.content = content_object  # Django JSONField maneja diccionarios directamente
        module.save()

        # 7. Devolver la respuesta exitosa
        return {
            "module_id": module.id,
            "content": content_object
        }

    except ObjectDoesNotExist as e:
        return {"error": f"No se encontró el objeto en la base de datos: {str(e)}"}
    except ValueError as e: # Captura el error de contenido ya generado o JSON inválido
        return {"error": str(e)}
    except Exception as e:
        # Captura cualquier otro error inesperado
        return {"error": f"Ocurrió un error inesperado al generar contenido: {str(e)}"}
    
def get_learning_module_by_id(module_id):
    try:
        module = LearningModule.objects.get(id=module_id)
    except LearningModule.DoesNotExist:
        raise ValueError(f"No se encontró ningún módulo con el ID {module_id}")

    return {
        "id": module.id,
        "title": module.title,
        "description": module.description,
        "level": module.level,
        "order_index": module.order_index,
        "is_blocked": module.is_blocked,
        "is_approved": module.is_approved,
        "content": module.content,
    }