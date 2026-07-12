# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements from the database
- Signed-in teachers can create, edit, and delete announcements

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements/active`                                           | Get currently active announcements                                  |
| GET    | `/announcements?teacher_username=<username>`                      | Get all announcements (authenticated user required)                 |
| POST   | `/announcements?teacher_username=<username>`                      | Create an announcement (authenticated user required)                |
| PUT    | `/announcements/{announcement_id}?teacher_username=<username>`    | Update an announcement (authenticated user required)                |
| DELETE | `/announcements/{announcement_id}?teacher_username=<username>`    | Delete an announcement (authenticated user required)                |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB, including activities, teacher accounts, and announcements.
