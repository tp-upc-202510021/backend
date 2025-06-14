import json
import re
from google import genai
from diagnostics.models import Diagnostic
from diagnostics.services import get_user_level
from decouple import config
from learningmodules.models import LearningModule
from django.core.exceptions import ObjectDoesNotExist
client = genai.Client(api_key=config("GEMINI_API_KEY"))
base_prompt = """Actúa como un educador financiero práctico y conciso, especializado en el mercado peruano. Tu misión es diseñar una ruta de aprendizaje altamente enfocada para un usuario en Perú.

El objetivo general de la aplicación es que el usuario adquiera ÚNICAMENTE los conocimientos ESENCIALES y directamente aplicables. Según el objetivo principal de aprendizaje que el usuario especificará (ya sea 'Préstamos' o 'Inversiones'), los módulos deben ayudar a:
* Para un objetivo de **PRÉSTAMOS**: Seleccionar y comparar productos financieros como préstamos (personales, hipotecarios, vehiculares, etc.) de manera informada en Perú, entendiendo sus costos (TEA, TCEA, comisiones), requisitos, y cómo gestionar la deuda responsablemente.
* Para un objetivo de **INVERSIONES**: Adquirir la base fundamental y necesaria para comenzar a invertir de forma segura y con entendimiento de las opciones disponibles en el mercado local peruano (por ejemplo: Bolsa de Valores de Lima, fondos mutuos, depósitos a plazo, factoring, etc.), comprendiendo los riesgos y rendimientos asociados.

Inmediatamente después de este texto de prompt principal, se te proporcionará la siguiente información del usuario:
1.  Su **Objetivo Principal de Aprendizaje** (indicando si se enfoca en 'Préstamos' o en 'Inversiones').
2.  Su **Perfil y Objetivos Específicos Detallados, Y sus conociniemtos actuales sobre los temas** (provenientes de su diagnóstico, campo 'level' de la tabla 'diagnostics' u otros datos relevantes).

Deberás utilizar esta información combinada (Objetivo Principal y Perfil Detallado) que sigue a este prompt para:
1.  Adaptar el punto de partida de los módulos.
2.  Seleccionar los temas más relevantes y el tipo de módulos (orientados a préstamos o a inversiones) según el Objetivo Principal y el Perfil Detallado del usuario.
3.  Ajustar la profundidad y el lenguaje de las explicaciones.

Basado en el **Objetivo Principal de Aprendizaje y el Perfil y Objetivos Específicos Detallados del usuario** (que se proporcionarán a continuación), y manteniendo un enfoque estricto en lo necesario y aplicable en Perú, genera una lista de módulos de aprendizaje. La respuesta debe ser únicamente un objeto JSON. Este JSON debe contener una clave principal llamada \"learning_modules\", cuyo valor será una lista de objetos. Cada objeto en la lista representa un módulo de aprendizaje y debe tener la siguiente estructura y tipos de datos:

* `title` (string): Un título conciso, práctico y altamente relevante para el perfil del usuario y su objetivo temático (máximo 100 caracteres), contextualizado para Perú.
* `description` (string): Una descripción detallada del contenido y propósito del módulo. Debe centrarse en los conocimientos prácticos y esenciales que el usuario necesita según su perfil y objetivo principal, mencionando aspectos clave para Perú.
* `level` (string): El nivel de dificultad del módulo, adaptado al punto de partida del usuario (ejemplos: 'Introductorio', 'Esencial', 'Intermedio Básico') (máximo 20 caracteres).
* `order_index` (integer): El orden secuencial del módulo, comenzando desde 1. Este campo es crucial para determinar el orden en que se deben presentar los módulos.
* `is_blocked` (boolean): Si el módulo está bloqueado o no. El primer módulo (`order_index` igual a 1) debe tener `is_blocked: false`, y todos los demás módulos deben tener `is_blocked: true`.

Importante: NO incluyas el campo `content` dentro de los objetos de los módulos por ahora.

Asegúrate de que el JSON esté bien formado y sea la única salida. Los módulos deben ser coherentes y progresivos, llevando al usuario desde su conocimiento actual hasta sus objetivos específicos dentro de su tema de interés, evitando información superflua.

Ejemplo de la estructura JSON esperada (el contenido real lo generarás tú, adaptado al objetivo y al perfil del usuario que se te proporcionará):

\`\`\`json
{
  \"learning_modules\": [
    {
      \"title\": \"[Título específico para el enfoque y perfil del usuario]\",
      \"description\": \"[Descripción detallada, práctica y enfocada en lo esencial para el usuario en Perú, según su diagnóstico y el tema principal]\",
      \"level\": \"[Nivel adaptado]\",
      \"order_index\": 1,
      \"is_blocked\": false
    },
    {
      \"title\": \"[Siguiente título lógico]\",
      \"description\": \"[Continuación del aprendizaje práctico]\",
      \"level\": \"[Nivel adaptado progresivo]\",
      \"order_index\": 2,
      \"is_blocked\": true
    }
    // ... más módulos si son necesarios para cubrir lo esencial del perfil
  ]
}
\`\`\`

¡¡IMPORTANTE!!
Responde **exclusivamente** con el objeto JSON, no agregues comentarios ni nada extra, SOLO EN FORMATO JSON.
No uses markdown, comillas triples ni texto adicional.
"""

def create_modules_from_gemini(user_id, learning_path_id):
    if LearningModule.objects.filter(learning_path_id=learning_path_id).exists():
        raise ValueError("Los módulos para este learning path ya han sido creados.")
    user_level = get_user_level(user_id)
    if not user_level:
        raise ValueError("El usuario no tiene un diagnóstico registrado.")
    prompt = f"{base_prompt}\n\nNivel y Objetivos del Usuario: \"{user_level}\""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
        )
        raw_text = response.text.strip()
        match = re.search(r"```json(.*?)```", raw_text, re.DOTALL)
        json_str = match.group(1).strip() if match else raw_text

        data = json.loads(json_str)

    except Exception as e:
        print(f"Error al procesar la respuesta de Gemini: {e}")
        raise ValueError("Ocurrió un error procesando la respuesta de Gemini.")

    modules_data = data.get("learning_modules", [])
    created_modules = []

    for m in modules_data:
        obj = LearningModule.objects.create(
            learning_path_id=learning_path_id,
            title=m["title"],
            description=m["description"],
            level=m["level"],
            order_index=m["order_index"],
        )
        created_modules.append({
            "id": obj.id,
            "title": obj.title,
            "description": obj.description,
            "level": obj.level,
            "order_index": obj.order_index
        })
    return created_modules

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
    -   `content`: Crea el contenido educativo **TEÓRICO** principal en formato **Markdown**. Debe ser claro, muy conciso, optimizado para 1 pantalla de celular y explicar los conceptos fundamentales del módulo.

2.  **Segundo Objeto (Práctico):**
    -   `type`: Debe ser la cadena de texto `"practical"`.
    -   `content`: Proporciona un **ejemplo PRÁCTICO y CONCRETO** en formato **Markdown** relacionado con la teoría. Debe mostrar cómo se aplica el concepto en una situación real del mercado peruano. Debe estar optimizado para 1 pantalla de celular.

3.  **Tercer Objeto (Video):**
    -   `type`: Debe ser la cadena de texto `"video"`.
    -   `content`: Busca y proporciona **UN ÚNICO enlace URL** a un video de YouTube relevante. El video debe durar entre 3 y 7 minutos, ser de una fuente confiable, estar disponible y tener un enlace válido.

**¡¡MUY IMPORTANTE!!**
Tu respuesta debe ser **EXCLUSIVAMENTE el objeto JSON**. No incluyas texto introductorio como "Aquí está el JSON:", despedidas, explicaciones, ni ```json. La salida debe ser el JSON puro para que pueda ser procesado directamente por un programa.
"""

        # 4. Llamar a la API de Gemini
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-06-05",  # Modelo recomendado, puedes usar el que prefieras
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
        "content": module.content,
    }