import json
import random
from click import password_option
from faker import Faker
from dotenv import load_dotenv
from locust import HttpUser, TaskSet, task, between

# Firebase admin imports 
import os
import firebase_admin
import firebase_admin.auth as auth
from firebase_admin import credentials

load_dotenv()

fake = Faker()
latitude = 51.507351
longitude = -0.127758

cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PVT_KEY_ID"),
    "private_key": os.getenv("PVT_KEY").replace(r'\n', '\n'),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("CERT_URL"),
    "universe_domain": "googleapis.com"
})
firebase_admin.initialize_app(cred)

def create_firebase_user():
        email = fake.email(domain="yopmail.com")
        password = "Qwerty@123"
        print(f"\n ---  email {email}")
        user = auth.create_user(email=email, password=password)
        return email, password if user else None

# BaseUrl = "https://api.dev.seeke.us/api"
from locust import SequentialTaskSet

class EmployeeBehaviour(SequentialTaskSet):
    def __init__(self, parent: HttpUser):
        super().__init__(parent)
        self.token = None
        self.headers = {}
        self.uuid = None
        self.email = None
        self.employee_dynamic_dropdown_data = None

    def on_start(self):
        # Employee user login to get token
        email, password = create_firebase_user()
        self.email = email

        if email and password:
            response = self.client.post("/users/token", json={
                "email": email,
                "password": password
            })
            print(f"\n ---  \n onstart - {response.json()}")
            self.token = response.json().get("data")["idToken"]
            # print(f"\n ---  self.token = {self.token}")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            # print(f"\n ---  self.headers = {self.headers}")
        else:
            print("\n ---  Could not create firebase user")
            SequentialTaskSet.interrupt(self)
    
    
    @task
    def createUser(self):
        response = self.client.post("/users/create", headers=self.headers, json={
            "role": "EMPLOYEE",
            "language": "ENGLISH",
            "is_email_verified": True
        })
        print(f'create user response = {response.json()}')
    
    @task
    def employee_signup(self):
        dynamic_dropdown_data_response = self.client.get("/dynamic-dropdown?dropdown_type=employee", headers=self.headers)
        self.employee_dynamic_dropdown_data = dynamic_dropdown_data_response.json().get("data")
        print(f"\n ---  self.employee_dynamic_dropdown_data = {self.employee_dynamic_dropdown_data}")

        preferred_job_position_response = self.client.get("/dynamic-dropdown?dropdown_type=job", headers=self.headers)
        preferred_job_position = preferred_job_position_response.json().get("data")["job_titles"][0]["value"]
        print(f"\n ---  preferred_job_position = {preferred_job_position}")


        employee_signup_request_body = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "current_address":{
                "country": fake.country(),
                "state": fake.state(),
                "city": fake.city(),
                "postal_code": fake.random_number(digits=6),
                "latitude": latitude,
                "longitude": longitude,
            },
            "travel_address": {
                "country": fake.country(),
                "state": fake.state(),
                "city": fake.city(),
                "postal_code": fake.random_number(digits=6),
                "latitude": latitude,
                "longitude": longitude,
            },
            "total_experience_in_year": random.randint(3,7),
            "total_experience_in_month": random.randint(1,7),
            "education": (random.sample(self.employee_dynamic_dropdown_data["education"], 1))[0]["value"],
            "other_education": None,
            "customer_service_skills": [item["label"] for item in random.sample(self.employee_dynamic_dropdown_data["customer_service_skill"], 3)],
            "organizational_skills": [],
            "adaptability_skills": [item["label"] for item in random.sample(self.employee_dynamic_dropdown_data["adaptability_skill"], 3)],
            "physical_skills": [item["label"] for item in random.sample(self.employee_dynamic_dropdown_data["physical_skill"], 3)],
            "technical_skills": [item["label"] for item in random.sample(self.employee_dynamic_dropdown_data["technical_skill"], 3)],
            "profile_pic": f"employee/profile_image/{fake.file_name(category='image')}",
            "intro_video": f"employee/intro_video/{fake.file_name(category='video')}",
            "experience_details": [],
            "bio": fake.paragraph(nb_sentences=2),
            "other_skills": fake.words(nb=2),
            "position": preferred_job_position
        }        
        employee_signup_response = self.client.patch("/users/employees/sign-up", json=employee_signup_request_body, headers=self.headers)
        print(f"\n ---  employee_signup_response = {employee_signup_response.json()}")
        self.user.environment.runner.quit()



class EmployeeUser(HttpUser):
    tasks = [EmployeeBehaviour]
    # wait_time = between(1, 3)
    stop = True