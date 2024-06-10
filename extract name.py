import spacy
from spacy.matcher import Matcher

def extract_names(resume_path):
    nlp = spacy.load("en_core_web_sm")
    matcher = Matcher(nlp.vocab)
    patterns = [
        [{"POS": "PROPN"}, {"POS": "PROPN"}],  # First name and Last name
        [{"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}],  # First name, Middle name, and Last name
        [{"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}, {"POS": "PROPN"}]  # First name, Middle name, Middle name, and Last name
    ]
    for pattern in patterns:
        matcher.add("NAME", patterns=[pattern])

    with open(resume_path, "r", encoding="utf-8-sig") as file:
        resume_text = file.read()

    doc = nlp(resume_text)
    matches = matcher(doc)
    names = []
    for match_id, start, end in matches:
        name = doc[start:end].text
        names.append(name)

    return names

# Example usage
resume_path = "c:\\Users\\GauravKale\\Desktop\\RESUMEOCR\\Resume\\Resume_Bhushan_Warake.pdf"
names = extract_names(resume_path)
print(names)