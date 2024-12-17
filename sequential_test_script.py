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

class EmployerBehaviour(SequentialTaskSet):
    def __init__(self, parent: HttpUser):
        super().__init__(parent)
        self.token = None
        self.headers = {}
        self.uuid = None
        self.email = None
        self.company_uuid = None
        self.dynamic_dropdown_data = None
        self.job_type_dynamic_dropdown = None
        self.company_address_uuid = None
        self.job_to_edit = None
        self.employee_stack_uuid_list = list()
        self.job_stack_uuid_list = list()
        self.posted_job_uuid_list = list()

    def on_start(self):
        # Employer user login to get token
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
            "role": "COMPANY_ADMIN",
            "language": "ENGLISH",
            "is_email_verified": True
        })
        print(f'create user response = {response.json()}')
        
    
    @task
    def employerSignup(self):
        # Get position
        dynamic_dropdown_response = self.client.get("/dynamic-dropdown?dropdown_type=employer", headers=self.headers)
        self.dynamic_dropdown_data = dynamic_dropdown_response.json().get("data")
        # print(f"\n ---  dynamic_dropdown_data  = {dynamic_dropdown_data}")
        position = self.dynamic_dropdown_data["job_titles"][2]["value"]
        print(f"\n ---  position  = {position}")

        business_category = self.dynamic_dropdown_data["business_category"][2]["value"]
        # Step 1: Create Employer


        # Step 2: Employer Signup
        employer_signup_response = self.client.patch("/users/employers/sign-up", headers=self.headers, json={
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "position": position,
            "profile_pic": f"company/admin_profile_image/{fake.file_name(category='image')}"
        })
        print(f"\n ---  employer_signup_response = {employer_signup_response.json()}")

    @task
    def createCompany(self):
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
            "business_category": (random.sample(self.dynamic_dropdown_data["business_category"], 1))[0]["value"],
            "health_wellness_highlights": [item["label"] for item in random.sample(self.dynamic_dropdown_data["health_wellness_highlights"], 3)],
            "community_highlights": [], #[item["label"] for item in random.sample(self.dynamic_dropdown_data["community_highlights"], 3)],
            "benefits_highlights": [item["label"] for item in random.sample(self.dynamic_dropdown_data["benefits_highlights"], 3)],
            "development_highlights": [item["label"] for item in random.sample(self.dynamic_dropdown_data["development_highlights"], 3)],
            "environment_highlights": [item["label"] for item in random.sample(self.dynamic_dropdown_data["environmental_highlights"], 3)],
            "bars_nightlife_highlights": [item["label"] for item in random.sample(self.dynamic_dropdown_data["bars_night_life_highlights"], 3)],
            "photo": f"company/company_image/{fake.file_name(category='image')}",
            "company_intro_video": f"company/company_intro_video/{fake.file_name(category='video')}",
            "profile_pic": f"company/company_profile_image/{fake.file_name(category='image')}"
        }

        print(f"\n ---  create_company_request_body = {create_company_request_body}")
        create_company_response = self.client.post("/companies/create", headers=self.headers, json=create_company_request_body)
        print(f"\n ---  create_company_response = {create_company_response.json()}")
    
    @task
    def getProfile(self):
        response = self.client.get("/users/profile", headers=self.headers)
        if response.status_code == 200:
            print(f"\n ---  get profile response  = {response.json()}")
            response_data = response.json().get("data")
            self.company_uuid = response_data["company"]["uuid"]
            self.company_address_uuid = response_data["company"]["address"]["uuid"]
            print(f"\n ---  company uuid  = {self.company_uuid}")
            print(f"\n ---  company address uuid  = {self.company_address_uuid}")


    @task
    def approveCompany(self):
        super_admin_login_response = self.client.post("/users/token", json={
                "email": 'superadmin@yopmail.com',
                "password": "Qwerty@123"
            })
        print(f"\n ---  \n superadmin_login_response - {super_admin_login_response.json()}")
        
        if super_admin_login_response.status_code == 200:
            headers = {"Authorization": f"Bearer {super_admin_login_response.json().get('data')['idToken']}"}
            print(f"\n ---  super admin headers = {headers}")
        
            company_approval_response = self.client.patch("/users/update-employers-status", json={
                "uuid": self.company_uuid,
                "status": "APPROVED",
                "reason": ""
            }, headers=headers)
            print(f"\n ---  company_approval response = {company_approval_response.json()}")
        else:
            print("\n ---  could not login super admin")

    @task
    def buySubscription(self):
        buy_subscription_response = self.client.post("/users/subscriptions/save", headers=self.headers, json={
            "product_id": "seeke_enterprise_yearly_dev",
            "payment_id": fake.lexify(text='????????????'),
            "platform_type": "IOS",
            "plan_type": "YEARLY",
            "category": "ENTERPRISE",
            "max_sub_admins": "20",
            "cost": 750.0
        })
        print(f"\n ---  buy_subscription_response = {buy_subscription_response.json()}")

    # @task
    # def addSubadmin(self, email, password):
    #     response = self.client.post("/users/add-subadmin", json={"email": email, "password": password}, headers=self.headers)
    #     return response

    @task
    def createJob(self):
        job_type_dynamic_dropdown_response = self.client.get("/dynamic-dropdown?dropdown_type=job", headers=self.headers)
        self.job_type_dynamic_dropdown = job_type_dynamic_dropdown_response.json().get("data")
        print(f"\n ---  self.job_type_dynamic_dropdown = {self.job_type_dynamic_dropdown}")

        create_job_request_body = {
            "company":self.company_address_uuid,
            "job_title": (random.sample(self.job_type_dynamic_dropdown["job_titles"], 1))[0]["value"],
            "status":"ACTIVE",
            "description": fake.paragraph(nb_sentences=2),
            "job_type":(random.sample(self.job_type_dynamic_dropdown["job_type"], 1))[0]["value"],
            "max_experience_in_years":random.randint(4,9),
            "min_experience_in_years":random.randint(0,3),
            "salary":(random.sample(self.job_type_dynamic_dropdown["salary_type"], 1))[0]["value"],
            "customer_service_skills":[item["label"] for item in random.sample(self.job_type_dynamic_dropdown["customer_service_skill"], 3)],
            "organizational_skills":[],
            "adaptability_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["adaptability_skill"], 3)],
            "physical_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["physical_skill"], 3)],
            "technical_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["technical_skill"], 3)],
            "other_skills": fake.words(nb=2),
            "min_salary":random.randint(100,250),
            "max_salary":random.randint(600, 1000),
            "questions":fake.sentences(nb=5),
            "is_tip_added":True,
            "job_address": self.company_address_uuid
                

        }

        create_job_response = self.client.post("/jobs/create", json=create_job_request_body, headers=self.headers)
        print(f"\n ---  create_job_response = {create_job_response.json()}")
        

    @task
    def getJobPostedList(self):
        posted_jobs_list_response = self.client.get("/jobs/list?pagination=true", headers=self.headers)

        if posted_jobs_list_response.status_code == 200:
            results = posted_jobs_list_response.json().get("data")[0]["results"]
            if len(results) > 0:
                self.job_to_edit = results[0]["uuid"]
            else:
                print("\n ---  no jobs posted")
        print(f"\n ---  posted_jobs_list_response = {posted_jobs_list_response.json()}")

    @task
    def getFilteredPostedJobsList(self):
        job_type_filter_value = (random.sample(self.job_type_dynamic_dropdown["job_type"], 1))[0]["value"]
        status_filter_value = "ACTIVE"

        filtered_posted_jobs_response = self.client.get(f"/jobs/list?job_type={job_type_filter_value}&status={status_filter_value}&pagination=true", headers=self.headers)
        print(f"\n ---  filtered_posted_jobs_response = {filtered_posted_jobs_response.json()}")

    @task
    def editJob(self):
        if self.job_to_edit:
            edit_job_request_body = {
                "job_title": (random.sample(self.job_type_dynamic_dropdown["job_titles"], 1))[0]["value"],
                "status":"ACTIVE",
                "description": fake.paragraph(nb_sentences=2),
                "job_type":(random.sample(self.job_type_dynamic_dropdown["job_type"], 1))[0]["value"],
                "max_experience_in_years":random.randint(4,9),
                "min_experience_in_years":random.randint(0,3),
                "salary":(random.sample(self.job_type_dynamic_dropdown["salary_type"], 1))[0]["value"],
                "customer_service_skills":[item["label"] for item in random.sample(self.job_type_dynamic_dropdown["customer_service_skill"], 3)],
                "organizational_skills":[],
                "adaptability_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["adaptability_skill"], 3)],
                "physical_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["physical_skill"], 3)],
                "technical_skills": [item["label"] for item in random.sample(self.job_type_dynamic_dropdown["technical_skill"], 3)],
                "other_skills": fake.words(nb=2),
                "min_salary":random.randint(100,250),
                "max_salary":random.randint(600, 1000),
                "questions":fake.sentences(nb=5),
                "is_tip_added":True,
            }

            edit_job_response = self.client.patch(f"/jobs/{self.job_to_edit}/update", json=edit_job_request_body, headers=self.headers)
            print(f"\n ---  edit_job_response = {edit_job_response.json()}")
        else:
            print("\n ---  job to edit uuid not found")
    

    # @task
    # def editProfile(self):
    #     response = self.client.patch("/users/edit-profile", json={"first_name": first_name, "last_name": last_name, "position": position, "profile_pic": profile_pic}, headers=self.headers)
    #     return response

    @task
    def getEmployeeCardStack(self):
        employee_card_stack_response = self.client.get("/users/employees/get-card-stack?pagination=true", headers=self.headers)
        if employee_card_stack_response.status_code == 200:
            results = employee_card_stack_response.json().get("data")[0]["results"]
            for emp in results:
                self.employee_stack_uuid_list.append(emp["user_uuid"])
            print(f"--- employee_stack_uuid_list {self.employee_stack_uuid_list}")


    @task
    def rightSwipeEmployee(self):
        print(f"\n ---  right swipe employee - user = {self.email} -  {self.uuid}")
        employee_uuid = self.employee_stack_uuid_list.pop() if self.employee_stack_uuid_list else None
        if employee_uuid and self.job_to_edit:
            right_swipe_response = self.client.post("/employees/swipe-right", json={"job": self.job_to_edit, "employee":employee_uuid}, headers=self.headers)
            print(f"\n ---  right_swipe_response = {right_swipe_response.json()}")
        else:
            print("\n ---  rescheduling right swipe employee for user = {self.email}")
            # self.interrupt(reschedule=True)

    @task
    def leftSwipeEmployee(self):
        print(f"\n ---  left swipe employee- user = {self.email} -  {self.uuid}")
        employee_uuid = self.employee_stack_uuid_list.pop() if self.employee_stack_uuid_list else None
        if employee_uuid:
            left_swipe_response = self.client.post("/employees/swipe-left", json={"employee":employee_uuid}, headers=self.headers)
            print(f"\n ---  left_swipe_response = {left_swipe_response.json()}")
        else:
            print("\n ---  rescheduling left swipe employee for user = {self.email}")
            # self.interrupt(reschedule=True)
        print("--- \n stopping employer script")
        # self.interrupt(reschedule=False)
        self.user.environment.runner.quit()
        # print("--- \n script stopped")




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
        # self.user.environment.runner.quit()



class EmployeeUser(HttpUser):
    tasks = [EmployeeBehaviour]
    # wait_time = between(1, 3)
    stop = True


class EmployerUser(HttpUser):
    tasks = [EmployerBehaviour]
    # wait_time = between(1, 3)
    stop = True