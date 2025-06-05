import json
import re
from decouple import config
from users.models import User
from learningmodules.models import LearningModule
from .models import Quiz, Question, Answer
from google import genai
from django.core.exceptions import ObjectDoesNotExist


client = genai.Client(api_key=config("GEMINI_API_KEY"))
prompt = """
Eres una IA educativa especializada en finanzas personales. A partir del siguiente contenido de un módulo educativo, genera un quiz en formato JSON con 5 preguntas de opción múltiple.

Condiciones:
- Cada pregunta debe tener exactamente 4 opciones.
- Solo una opción debe tener "is_correct": true.
- Las demás deben tener "is_correct": false.
- Usa lenguaje claro y educativo.
- NO des explicaciones, SOLO responde en el siguiente formato JSON encerrado en triple backticks:

```json
[
  {
    "text": "¿Cuál es la finalidad principal del ahorro?",
    "answers": [
      {"text": "Tener dinero disponible para emergencias", "is_correct": true},
      {"text": "Gastar más en cosas innecesarias", "is_correct": false},
      {"text": "Endeudarse menos", "is_correct": false},
      {"text": "Evitar trabajar", "is_correct": false}
    ]
  },
  ...
]
Contenido del módulo(Genera las preguntas en base al contenido del módulo):
"""
def generate_quizzes_from_gemini(module_id):
    module = LearningModule.objects.get(id=module_id)
    final_prompt = f"{prompt}\n{module.content}"   
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=final_prompt,
        )
        raw_text = response.text.strip()
        match = re.search(r"```json(.*?)```", raw_text, re.DOTALL)
        json_str = match.group(1).strip() if match else raw_text
        questions = json.loads(json_str) 
    except Exception as e:
        print(f"Error al procesar la respuesta de Gemini: {e}")
        raise ValueError("Ocurrió un error procesando la respuesta de Gemini.")
    
    quiz = Quiz.objects.create(module=module, total_questions=len(questions))

    for q in questions:
        question = Question.objects.create(quiz=quiz, text=q["text"])
        for ans in q["answers"]:
            Answer.objects.create(
                question=question,
                text=ans["text"],
                is_correct=ans["is_correct"]
            )

    return quiz
def get_latest_quiz_with_questions_and_answers(module_id):
    try:
        quiz = Quiz.objects.filter(module_id=module_id).order_by('-id').first()

        if not quiz:
            raise ObjectDoesNotExist("No se encontró un quiz para este módulo.")

        result = {
            "quiz_id": quiz.id,
            "module_id": module_id,
            "total_questions": quiz.total_questions,
            "questions": []
        }

        questions = Question.objects.filter(quiz=quiz).prefetch_related('answers')

        for q in questions:
            question_data = {
                "question_id": q.id,
                "text": q.text,
                "answers": []
            }

            for a in q.answers.all():
                question_data["answers"].append({
                    "answer_id": a.id,
                    "text": a.text,
                    "is_correct": a.is_correct
                })

            result["questions"].append(question_data)

        return result

    except Exception as e:
        print(f"Error al obtener quiz del módulo {module_id}: {e}")
        raise ValueError("No se pudo obtener el quiz del módulo.")
