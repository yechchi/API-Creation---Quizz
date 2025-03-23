from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import pandas as pd
import random

app = FastAPI()
security = HTTPBasic()

# Dictionnaire des utilisateurs
users = {
    "alice": "wonderland",
    "bob": "builder",
    "clementine": "mandarine"
}

# Admin credentials
admin_credentials = {"admin": "4dm1N"}

data = pd.read_csv('questions.csv')

def verify_credentials(credentials: HTTPBasicCredentials):
    if credentials.username in users and users[credentials.username] == credentials.password:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

@app.get("/verify", name = "vérification de l'API")
def verify_api():
    return {"message": "L'API est fonctionnelle."}

class QuizRequest(BaseModel):
    test_type: str
    categories: list
    number_of_questions: int

@app.post("/generate_quiz", name = "génération de quiz")
def generate_quiz(quiz_request: QuizRequest, credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)

    # Filtrer les questions selon les critères
    filtered_data = data[
        (data['use'] == quiz_request.test_type) &
        (data['subject'].isin(quiz_request.categories))
    ]

    # Remplacer les NaNs par du vide ( car sinon ça pose problème lors de la conversion en JSON )
    filtered_data.fillna("", inplace=True)     

    # Sélectionner un nombre aléatoire de questions
    if len(filtered_data) < quiz_request.number_of_questions:
        raise HTTPException(status_code=404, detail="Not enough questions available")

    selected_questions = filtered_data.sample(n=quiz_request.number_of_questions)

    return selected_questions.to_dict(orient="records")

class QuestionCreate(BaseModel):
    admin_username: str
    admin_password: str
    question: str
    subject: str
    correct: list
    use: str
    responseA: str
    responseB: str
    responseC: str
    responseD: str

@app.post("/create_question", name="Rajout de question")
def create_question(question_create: QuestionCreate):
    if (question_create.admin_username in admin_credentials and
        admin_credentials[question_create.admin_username] == question_create.admin_password):
        new_question = pd.DataFrame([{
            "question": question_create.question,
            "subject": question_create.subject,
            "correct": question_create.correct,
            "use": question_create.use,
            "responseA": question_create.responseA,
            "responseB": question_create.responseB,
            "responseC": question_create.responseC,
            "responseD": question_create.responseD
        }])
        global data
        data = pd.concat([data, new_question], ignore_index=True)

        return {"message": "Question créée avec succès."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password",
        )
