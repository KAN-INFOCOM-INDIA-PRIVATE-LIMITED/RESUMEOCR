import io
import PyPDF2
from langchain.llms import OpenAIChat
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain import LLMChain, PromptTemplate

def extract_text_from_binary(file):
    pdf_data = io.BytesIO(file)
    reader = PyPDF2.PdfReader(pdf_data)
    num_pages = len(reader.pages)
    text = ""

    for page in range(num_pages):
        current_page = reader.pages[page]
        text += current_page.extract_text()
    return text

def format_resume(resume):
    template = """Format the provided resume to this YAML template:
        ---
    name: ''
    phoneNumbers:
    - ''
    websites:
    - ''
    emails:
    - ''
    dateOfBirth: ''
    addresses:
    - street: ''
      city: ''
      state: ''
      zip: ''
      country: ''
    summary: ''
    education:
    - school: ''
      degree: ''
      fieldOfStudy: ''
      startDate: ''
      endDate: ''
    workExperience:
    - company: ''
      position: ''
      startDate: ''
      endDate: ''
    skills:
    - name: ''
    certifications:
    - name: ''

    {chat_history}
    {human_input}"""

    prompt = PromptTemplate(
            input_variables=["chat_history", "human_input"],
            template=template
        )

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(
            llm=OpenAIChat(model="gpt-3.5-turbo"),
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

    res = llm_chain.predict(human_input=resume)
    return res

# Example usage
def main():
    # Read PDF file
    with open('uploads/BHUSHAN_WARAKE_RESUME_1.pdf', 'rb') as file:
        pdf_text = extract_text_from_binary(file.read())

    # Format resume
    formatted_resume = format_resume(pdf_text)

    # Print formatted resume
    print(formatted_resume)

if __name__ == "__main__":
    main()
