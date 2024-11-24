from pickletools import long1

from locust import HttpUser, TaskSet, task, between
import json
from faker import Faker

fake = Faker()
latitude = 51.507351
longitude = -0.127758


class EmployerBehavior(TaskSet):
    def __init__(self, parent: HttpUser):
        super().__init__(parent)
        self.token = None
        self.headers = {}

    def on_start(self):
        # Employer user login to get token
        response = self.client.post("/users/token", json={
            "email": "test1@yopmail.com",
            "password": "Qwerty@123"
        })
        # print(f"\n onstart - {response.json()}")
        self.token = response.json().get("data")["idToken"]
        # print(f"self.token = {self.token}")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        # print(f"self.headers = {self.headers}")

    @task
    def employer_sequence(self):
        # Define the sequence of API calls for EmployerUser

        # Step 1 : Create Employer
        create_employer_response = self.client.post("/users/create", headers=self.headers, json={
            "role": "COMPANY_ADMIN",
            "language": "ENGLISH",
            "is_email_verified": True
        })
        print(f"create_employer_response = {create_employer_response}")

        # Get position
        dynamic_dropdown_response = self.client.get("/dynamic-dropdown?dropdown_type=employer", headers=self.headers)
        dynamic_dropdown_data = dynamic_dropdown_response.json().get("data")
        # print(f"dynamic_dropdown_data  = {dynamic_dropdown_data}")
        position = dynamic_dropdown_data["job_titles"][2]["value"]
        print(f"position  = {position}")

        business_category = dynamic_dropdown_data["business_category"][2]["value"]
        # Step 1: Create Employer


        # Step 2: Employer Signup
        employer_signup_response = self.client.patch("/users/employers/sign-up", headers=self.headers, json={
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "position": position,
            "profile_pic": f"company/admin_profile_image/{fake.file_name(category='image')}"
        })
        print(f"employer_signup_response = {employer_signup_response.json()}")


        # Step 2: Create Company
        create_company_request_body = {
            "name": fake.company(),
            "website": fake.url(),
            "description": fake.word(),
            "address": {
                "country": fake.country(),
                "state": fake.state(),
                "city": fake.city(),
                "postal_code": fake.random_number(digits=6),
                "street_address": fake.street_address(),
                "latitude": latitude,
                "longitude": longitude,
            },
            "business_category": business_category,
            "health_wellness_highlights": [item["label"] for item in dynamic_dropdown_data["health_wellness_highlights"]],
            "community_highlights": [item["label"] for item in dynamic_dropdown_data["community_highlights"]],
            "benefits_highlights": [item["label"] for item in dynamic_dropdown_data["benefits_highlights"]],
            "development_highlights": [item["label"] for item in dynamic_dropdown_data["development_highlights"]],
            "environment_highlights": [item["label"] for item in dynamic_dropdown_data["environmental_highlights"]],
            "bars_nightlife_highlights": [item["label"] for item in dynamic_dropdown_data["bars_night_life_highlights"]],
            "photo": f"company/company_image/{fake.file_name(category='image')}",
            "company_intro_video": f"company/company_intro_video/{fake.file_name(category='video')}",
            "profile_pic": f"company/company_profile_image/{fake.file_name(category='image')}"
        }

        print(f"create_company_request_body = {create_company_request_body}")
        create_company_response = self.client.post("/companies/create", headers=self.headers, json=create_company_request_body)
        print(f"create_company_response = {create_company_response.json()}")

        # Add more employer-specific API calls here...

        # Final Step: Logout
        # self.client.post("/users/logout?login_type=firebase", headers=self.headers)
        # print(f"\n onstart - {response}")


"""class EmployeeBehavior(TaskSet):

    def on_start(self):
        # Employee user login to get token
        response = self.client.post("/users/token", json={
            "username": "employee_user",
            "password": "employee_password"
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task
    def employee_sequence(self):
        # Define the sequence of API calls for EmployeeUser

        # Step 1: Employee Signup
        self.client.post("/users/employees/sign-up", headers=self.headers, json={
            "first_name": "Employee",
            "last_name": "User",
            "current_address": {
                "country": "USA",
                "state": "CA",
                "city": "Los Angeles",
                "postal_code": "90001"
            }
        })

        # Step 2: Get Employee Card Stack
        self.client.get("/users/employees/get-card-stack?pagination=true", headers=self.headers)

        # Step 3: Right Swipe Employee Card
        self.client.post("/employees/swipe-right", headers=self.headers, json={
            "employee_id": "employee123"
        })

        # Add more employee-specific API calls here...

        # Final Step: Logout
        self.client.post("/users/logout?login_type=firebase", headers=self.headers)
"""

class EmployerUser(HttpUser):
    tasks = [EmployerBehavior]
    wait_time = between(1, 3)


"""class EmployeeUser(HttpUser):
    tasks = [EmployeeBehavior]
    wait_time = between(1, 3)
"""