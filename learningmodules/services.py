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
      \"order_index\": 1
    },
    {
      \"title\": \"[Siguiente título lógico]\",
      \"description\": \"[Continuación del aprendizaje práctico]\",
      \"level\": \"[Nivel adaptado progresivo]\",
      \"order_index\": 2
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
Eres un educador financiero directo y práctico, especializado en el contexto peruano. A partir del TÍTULO y la DESCRIPCIÓN de un módulo, debes generar el **contenido completo** de dicho módulo en **Markdown**.  
Requisitos estrictos de salida:  
1. Devuelve **solo** el contenido en Markdown, SIN encabezados tipo “¡Listo!” ni introducciones/despedidas.  
2. Empieza directamente con un encabezado H1 (`#`) que sea el mismo TÍTULO.  
3. Organiza la explicación con subtítulos H2/H3, viñetas y párrafos claros.  
4. Ejemplifica con casos del sistema financiero peruano (SBS, TCEA, bancos, etc.).  
5. Adapta profundidad y vocabulario al nivel del usuario: {user_level}.  
6. No incluyas código, JSON, ni comentarios fuera del contenido.  

Datos del módulo:
Título: {module.title}  
Descripción: {module.description}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=generate_content_prompt,
        )
        content=response.text.strip()

        module.content = content
        module.save()
        return {
            "module_id": module.id,
            "content": content
        }
    except ObjectDoesNotExist as e:
        return {"error": f"No se encontró: {str(e)}"}
    except Exception as e:
        return {"error": f"Error al generar contenido: {str(e)}"}