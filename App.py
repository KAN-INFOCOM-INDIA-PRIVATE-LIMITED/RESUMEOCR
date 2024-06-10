from flask import Flask, flash, jsonify, redirect, render_template, request
from werkzeug.utils import secure_filename
import os
import re
from pdfminer.high_level import extract_text
import spacy
from spacy.matcher import Matcher

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure the 'uploads' directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

# Function to extract contact number from resume text
def extract_contact_number_from_resume(text):
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, text)
    return match.group() if match else None

# Function to extract email address from resume text
def extract_email_from_resume(text):
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    return match.group() if match else None

# Function to extract skills from resume text
def extract_skills_from_resume(text):
    unique_skills = set()
    skills_list = [
        "Python", "Java", "C++", "Machine Learning", "Data Analysis", 
        "Project Management", "JavaScript", "HTML", "CSS", "SQL", "R", 
        "Statistical Analysis", "Artificial Intelligence", "Deep Learning", 
        "Natural Language Processing", "Computer Vision", "Problem Solving", 
        "Communication Skills", "Teamwork", "Time Management"
    ]
    pattern = r"\b(?:{})\b".format("|".join(re.escape(skill) for skill in skills_list))
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    for match in matches:
        unique_skills.add(match.lower())
    return list(unique_skills)

# Function to extract education details from resume text
def extract_education_from_resume(text):
    education_qualifications = [
        "Bachelor's Degree", "Master's Degree", "Doctorate", "PhD", 
        "Diploma", "Certification", "Year", "Grade", "Percentage", 
        "College", "college", "University", "university", "HSC", "SSC"
    ]
    lines = text.split("\n")
    education_data = []
    for line in lines:
        for qualification in education_qualifications:
            if qualification.lower() in line.lower():
                education_data.append(line.strip())
                break
    return education_data

# Function to extract work experience from resume text
def extract_work_experience(text):
    work_patterns = [
        {"label": "DESIGNATION", "pattern": r"(?i)[A-Z][a-z]\s(?:Analyst|Manager|Developer|Engineer|Lead|Supervisor|Specialist|Architect)"},
        {"label": "COMPANY", "pattern": r"(?i)[A-Z][a-z]\s(?:Company|Inc|Corp|Ltd|LLP|Company|Limited)"},
    ]
    doc = nlp(text)
    work_experience_data = []
    current_experience = {}
    for ent in doc.ents:
        if ent.label_ in work_patterns:
            if ent.label_ == "DESIGNATION":
                current_experience["designation"] = ent.text.strip()
            elif ent.label_ == "COMPANY":
                current_experience["company"] = ent.text.strip()
                work_experience_data.append(current_experience.copy())
                current_experience.clear()
    return work_experience_data

# Function to extract name from resume text
def extract_name(resume_text):
    nlp = spacy.load("en_core_web_sm")
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{"POS": "PROPN"}, {"POS": "PROPN"}],  # First name and Last name
        [{"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}],  # First name, Middle name, and Last name
        [{"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}]  # First name, Middle name, Middle name, and Last name
    ]
    for pattern in patterns:
        matcher.add("NAME", patterns=[pattern])
    doc = nlp(resume_text)
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text
    return None

# Function to extract address from resume text
def extract_address_from_resume(text):
    city_pattern = r"[\s,]([A-Z][a-zA-Z\s]+),"
    pincode_pattern = r"\b\d{6}\b"
    address_pattern = r"(?<!\d)[\dA-Za-z\s,-]+\s(?=city|pincode|$)"

    city_match = re.search(city_pattern, text)
    pincode_match = re.search(pincode_pattern, text)
    address_match = re.search(address_pattern, text)

    city = city_match.group(1) if city_match else None
    pincode = pincode_match.group() if pincode_match else None
    address = address_match.group().strip() if address_match else None

    return {"city": city, "pincode": pincode, "address": address}


@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_data = {}
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            text = extract_text_from_pdf(file_path)
            extracted_data['name'] = extract_name(text)
            extracted_data['contact_number'] = extract_contact_number_from_resume(text)
            extracted_data['email'] = extract_email_from_resume(text)
            extracted_data['skills'] = extract_skills_from_resume(text)
            extracted_data['education'] = extract_education_from_resume(text)
            extracted_data['work_experience'] = extract_work_experience(text)
            extracted_data['address'] = extract_address_from_resume(text)

            # Return the extracted data as JSON
            return jsonify({'extracted_data': extracted_data})

    # If address is not extracted, set it to None
    extracted_data.setdefault('address', None)

    # Render the HTML template with the extracted data
    return render_template('Template/upload_resume.html', extracted_data=extracted_data)


# Route to handle form submission for updating details
@app.route('/update', methods=['POST'])
def update_details():
    # Extract form data
    name = request.form['name']
    contact_number = request.form['contact_number']
    email = request.form['email']
    skills = request.form['skills'].split(", ")
    address = request.form['address']
    education = request.form['education'].split(", ")

    # Process the data (store in database, etc.)
    # Here, we can print the data for demonstration
    print("Updated Details:")
    print("Name:", name)
    print("Contact Number:", contact_number)
    print("Email:", email)
    print("Skills:", skills)
    print("Address:", address)
    print("Education:", education)

    # Redirect to the home page
    return redirect('/')

if __name__ == '__main__':
    nlp = spacy.load("en_core_web_sm")
    app.run(debug=True)
