from transformers import pipeline

# Load a generative model (FLAN-T5 for prompt-based tasks)
generator = pipeline("text2text-generation", model="google/flan-t5-large")

# Define a prompt for the generator
prompt = """
Extract and resume the skills and put them in a list with a coma as a separator: 
Human Resources Coordinator 03/1996 to 02/2000 Company Name City , State
Developed HRIS database from ground up for employee records and monitoring.
Instrumental in reducing the use of Agency Staffing needs for hospital.
Coordinated and facilitates manpower planning, recruitment and retention, career development and training, staff relations, compensation
and benefits, compliance with local, state and federal statutory regulations, public programs, and regulatory audit procedures.
Served as the HR resource source for administration, mid-level management and staff.
Coordinated hiring procedures, appraisals, pay increases, promotions, transfers, terminations, job postings, and all corrective actions;
One Person Office, responsible for all OSHA, Work Comp, Benefits, payroll, etc.
"""

# Generate a response
response = generator(prompt, max_length=150, num_return_sequences=1)

print(response)
