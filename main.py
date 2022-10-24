import base64
import json

import requests
import streamlit as st

import analysis

parser_url = 'http://127.0.0.1:8889'
# parser_url = 'http://192.168.10.36:8889'
etalon_file_name = 'Идеальное Техническое задание 1.docx'


def get_json_from_parser(doc, filename):
    result = ""
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json; text/plain'
    }
    try:
        # file = open(doc, 'rb')
        encoded_string = base64.b64encode(doc)
        encoded_string = str(encoded_string)[2:-1]
    except Exception as e:
        print(f"\nОшибка в файле {doc}")
        print(f"при конвертации в base64, исключение = {e}")
        print("="*200)
        return

    response = requests.post(
        parser_url + "/document-parser",
        data=json.dumps({
            "base64Content": encoded_string,
            "documentFileType": filename.split(".")[-1].upper()
        }),
        headers=headers
    )

    try:
        result = response.json()['documents']
    except Exception as e:
        print(f"\nОшибка в файле {doc}")
        print(f"Ответ от парсера {response.json()}")
        print(f"Исключение = {e}")
        print("="*200)
        return
    return result


st.set_page_config(layout="wide")

st.markdown('''
    <style>
        header[data-testid="stHeader"] {left:98%;}
    </style>
''', unsafe_allow_html=True)

st.markdown('''
    <style>
        div[data-testid="stMarkdownContainer"] > p {margin-bottom: 5px;}
    </style>
''', unsafe_allow_html=True)

st.markdown('''
    <style>
        .tooltip {
            position:relative;
        }
        .tooltip:before {
            content: attr(data-text); /* here's the magic */
            position:absolute;
          
            bottom:100%;
            margin-left:15px;
            
            width:200px;
            padding:10px;
            border-radius:10px;
            background:#fff;
            color: #32333e;
            text-align:center;
            
            display:none;
        }
        .tooltip:hover:before {
            display:block;
        }
    </style>
''', unsafe_allow_html=True)

uploader = st.sidebar.file_uploader("Выберите файл", ["doc", "docx"])

if uploader and st.sidebar.button('Получить результат'):
    with st.spinner(text="Обработка документа"):
        from_parser = get_json_from_parser(uploader.getvalue(), uploader.name)[0]["paragraphs"]
        # st.write(from_parser)
        analysis.analysis(from_parser)
