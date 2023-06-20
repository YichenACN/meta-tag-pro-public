import openai
import pandas as pd
import os
import io
import streamlit as st
from streamlit_chat import message

os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']

@st.cache_data
def generate_response(system_prompt, user_prompt, model):
        
    response = openai.ChatCompletion.create(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        model=model,
        max_tokens=2048,
        temperature=0,
    )


    return response['choices'][0]['message']['content'].strip()

def read_dataset(folder_path):
    dataset_as_string = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            non_null_rows = df.dropna().iloc[:5]
            dataset_as_string[filename] = non_null_rows.to_csv(index=False, sep=',')
        elif filename.endswith('.xlsx'):
            excel_data = pd.read_excel
            for sheet_name, sheet_data in excel_data.items():
                sheet_data = sheet_data.dropna().iloc[:5]
                dataset_as_string[sheet_name] = sheet_data.to_csv(index=False, sep=',')

    data_string = ""
    for table_name, table_string in dataset_as_string.items():
        data_string += f"Table: {table_name}" + table_string + "\n"
                
    return data_string

def get_text():
    input_text = st.text_input("You: ","", key="input")
    return input_text

def main():
    metatag_system_prompt = """Your name is MetaTag Pro. You are a data specialist, you need to perform the following tasks:
- From a given dataset, you need to examine, understand, analyze the data
- If there is an ETL code relating to the given dataset, you need to review and understand the code
- You then need to create a summary description of their data product which can be published on the data product marketplace to help consumers understand the data product. 
- You should suggest potential use cases of the input dataset
- Finally you need to reorgnise the output as README.md format with the first section as Summary, second section as potetial use cases, third section as data description. In the third section,  for each attribute, it should be associated with data type and a detailed description structured as a table"""

    menu = ["Home", "Business User", "Technical User"]
    choice = st.sidebar.selectbox("Select your role", menu)
    st.sidebar.markdown("----")
    model = st.sidebar.radio('Pick a model version', ('gpt-3.5-turbo', 'gpt-4', 'PaLM2 (available soon)'))
    st.sidebar.markdown("----")
    uploaded_files = st.sidebar.file_uploader("Select data product", accept_multiple_files=True)

    dataset_as_string = {}
    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        df = pd.read_csv(uploaded_file)
        non_null_rows = df.iloc[:5]
        dataset_as_string[filename] = non_null_rows.to_csv(index=False, sep=',')

    data_string = ""
    for table_name, table_string in dataset_as_string.items():
        data_string += f"Table: {table_name}" + table_string + "\n"

    print(data_string)
    init_usr_prompt = f'Here is the given dataset with {len(dataset_as_string)} tables, each table has 1 header row plus 5 rows of data sample. Please do the tasks as instructed: \n {data_string}'
    init_prompt = generate_response(metatag_system_prompt, init_usr_prompt, model)

    if choice == "Home":
        home()
    elif choice == "Business User":
        business(dataset_as_string, model, metatag_system_prompt, init_prompt)
    elif choice == "Technical User":
        tech(model, metatag_system_prompt, init_prompt)

def home():
    st.title("MetaTagPro")
    st.markdown("""MetaTagPro is a powerful tool that drives data management efficiency and increases marketplace value with cutting-edge LLMs. \n
• Easily understand existing datasets with structured, human-readable descriptions and automated metadata management. \n
• Advanced capabilities include generating data product descriptions, creating data dictionaries and suggesting potential use cases, accelerating technical documentation creation. \n
• MetaTagPro can also summarise ETL code in plain English and derive data lineage without SME input. \n
• Identify PII and sensitive information, providing an extra layer of governance to your data management processes""")
    st.markdown("----")
    if st.button("Clear Cache"):
        st.cache_data.clear()

def business(dataset_as_string, model, metatag_system_prompt, init_prompt):
    st.title("For Business User")

    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "content_generated" not in st.session_state:
        st.session_state.content_generated = False

    conversation_history = []
    conversation_history.append({"role": "assistant", "content": init_prompt})

    st.sidebar.markdown("----")
    if st.sidebar.button("Preview Dataset") or st.session_state.data_loaded:
        for table_name, table_string in dataset_as_string.items():
            df = pd.read_csv(io.StringIO(table_string), sep=",")
            st.markdown(f"### Dataset sample: `{table_name}`")
            st.write(df)
        #for filename in os.listdir(folder):
        #    if filename.endswith('.csv'):
        #        file_path = os.path.join(folder, filename)
        #        df = pd.read_csv(file_path)
        #        non_null_rows = df.iloc[:5]
        #        st.markdown(f"### Dataset sample: `{filename}`")
        #        st.write(non_null_rows)
        st.session_state.data_loaded = True

    st.sidebar.markdown("----")

    questions = {'Summary':'Give me only the first summary section',
                 'Use_Case':'Give me only the suggested use cases section',
                 'Data_Description':'Give me only the data description section',
                 'PII':'I want to know which attributes contain PII data?',
                 'Sensitive_Info':'Which attributes contain personal sensitive information?'}
    
    if st.sidebar.button("Generate Contents") or st.session_state.content_generated:
        for q in questions:
            # conversation_history.append({"role": "user", "content": questions[q]})
            prompt = init_prompt + '\n' + questions[q]
            print(prompt)
            output = generate_response(metatag_system_prompt, prompt, model)
            # conversation_history.append({"role": "assistant", "content": output})
            with st.expander(questions[q]):
                st.write(output)
                st.markdown("----")
                st.button("Export " + q + " to Data Marketplace")

        #st.session_state.content_generated = True

def tech(model, metatag_system_prompt, init_prompt):
    if "content_generated" not in st.session_state:
        st.session_state.content_generated = False

    conversation_history = []
    #conversation_history.append({"role": "assistant", "content": init_prompt})
    st.title("For Technical User")
    st.sidebar.markdown("----")
    uploaded_files = st.sidebar.file_uploader("Select the source code to interpret", accept_multiple_files=True)

    for uploaded_file in uploaded_files:
        code_txt = uploaded_file.getvalue()
        content = str(uploaded_file.name) + " " + str(code_txt)
        conversation_history.append({"role": "user", "content": content})
        st.write("filename:", uploaded_file.name)
        st.code(code_txt.decode("utf-8"), language='python')

    st.sidebar.markdown("----")

    questions = {'Summary':'Provide a summary of what the given code is doing and the transformations performed in detail (for process_data.py)',
                 'Lineage':'What is the source of the raw data and can you derive basic data lineage with arrows?',
                 'Relationship':'Can you please briefly explain how the new calculated fields are derived?',
                 'Code':'Write me a code that splits the raw dataset into two new datasets, one with non-sensitive data and the other with all the information?',
                 'README': 'Generate a README.md for the given code and dataset'}
    
    if st.sidebar.button("Generate Contents") or st.session_state.content_generated:
        for q in questions:
            prompt = "\n".join([message["content"] for message in conversation_history])
            prompt += '\n' + questions[q]
            print(prompt)
            output = generate_response(metatag_system_prompt, prompt, model)
            with st.expander(questions[q]):
                st.write(output)
                if q in ['README', 'Code']:
                    st.button("Download " + q)

if __name__ == "__main__":
    main()
