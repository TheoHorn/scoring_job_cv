import os

def generate_readme(app_name, description, features, installation_steps, usage, routes):
    # Format features into a bullet-point list
    formatted_features = "\n".join(f"- {feature}" for feature in features)

    # Format installation steps into numbered steps
    formatted_installation = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(installation_steps))

    # Format routes into a table
    formatted_routes = "\n".join(f"| `{route['method']}` | `{route['endpoint']}` | {route['description']} |"
                                  for route in routes)

    readme_content = f"""
# {app_name}

## Description
{description}

## Features
{formatted_features}

## Installation
To set up the application locally, follow these steps:

{formatted_installation}

## Usage
{usage}

## API Routes
| Method | Endpoint         | Description          |
|--------|------------------|----------------------|
{formatted_routes}
"""

    # Write the content to README.md
    with open("README.md", "w") as f:
        f.write(readme_content)

    print("README.md has been generated successfully!")

# Example usage
if __name__ == "__main__":
    app_name = "Job Offer Analysis Application"
    description = "This application allows users to upload job offers and resumes to analyze compatibility using AI."
    features = [
        "Drag-and-drop functionality for uploading files.",
        "Automatic analysis of job offers and resumes.",
        "Visualization of matching results.",
        "User-friendly dashboard for managing uploads."
    ]
    installation_steps = [
        "Clone the repository: `git clone https://gibson.telecomnancy.univ-lorraine.fr/florian.goncalves/hackaton-job-offer.git`",
        "Navigate to the project directory: `cd hackaton-job-offer`",
        "Install dependencies: `pip install -r requirements.txt`",
        "Run the application: `python3 run.py`"
    ]
    usage = "Once the application is running, open your browser and navigate to `http://localhost:5000`."
    routes = [
        {"method": "GET", "endpoint": "/", "description": "Home page."},
        {"method": "POST", "endpoint": "/add_resume", "description": "Upload a resume for analysis."},
        {"method": "POST", "endpoint": "/add_offer", "description": "Upload a job offer for analysis."},
        {"method": "GET", "endpoint": "/offers", "description": "View uploaded job offers."},
        {"method": "GET", "endpoint": "/resumes", "description": "View uploaded resumes."},
    ]

    generate_readme(app_name, description, features, installation_steps, usage, routes)
