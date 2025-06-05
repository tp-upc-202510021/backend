from django.db import models

from django.db import models
from users.models import User
from learningmodules.models import LearningModule

class Quiz(models.Model):
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name="quizzes")
    total_questions = models.IntegerField()

    def __str__(self):
        return f"Quiz for Module {self.module.id}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return f"Question {self.id} for Quiz {self.quiz.id}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer {self.id} for Question {self.question.id}"

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result: {self.user.email} - Quiz {self.quiz.id} - Score {self.score}"

