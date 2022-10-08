import re

import streamlit as st
import json
import difflib

from nltk import WhitespaceTokenizer


def analysis(paragraphs):
    ideal_json = open('./ideal.json', encoding='utf-8')
    ideal_json = json.load(ideal_json)

    headers = ideal_json['confidentiality']['header']
    text = ideal_json['confidentiality']['text']
    d = difflib.Differ()

    for paragraph in paragraphs:
        full_paragraph: str = paragraph['paragraphHeader']['text'] + "\n" + paragraph['paragraphBody']['text']

        if full_paragraph.find(headers) != -1:
            st.header('Оригинал')
            st.write(text)
            st.header('Жалкая пародия')
            st.write(full_paragraph[:-10] + '123 234 dfsd')

            span_generator = WhitespaceTokenizer().tokenize(full_paragraph[:-10] + '123 234 dfsd')
            spans_ideal = [span for span in span_generator]

            span_generator = WhitespaceTokenizer().tokenize(headers + '\n' + text)
            spans = [span for span in span_generator]

            i = -1
            list_of_bad_lines: [str] = []
            list_of_good_lines: [str] = []
            diff = difflib.unified_diff(spans, spans_ideal)

            flag = False
            for ind, line in enumerate(diff):
                st.write(line)
                if line.startswith('---') or line.startswith('+++'):
                    continue
                if line.startswith('@@') and line.endswith('@@\n'):
                    i += 1
                    flag = False
                    continue
                if not index_exists(list_of_good_lines, i):
                    list_of_good_lines.append('')
                if not index_exists(list_of_bad_lines, i):
                    list_of_bad_lines.append('')

                if line.startswith('-'):
                    list_of_good_lines[
                        i] += f'<span style="background-color:moccasin;display: inline;">{line[1:]}</span>'
                    continue

                if line.startswith('+'):
                    list_of_good_lines[i] += f'<span style="background-color:red;display: inline;">{line[1:]}</span>'
                    if not flag:
                        list_of_bad_lines[i] += ' ' + line[1:]
                        flag = True
                    continue

                list_of_good_lines[i] += line
                list_of_bad_lines[i] += line

            for index, line in enumerate(list_of_good_lines):
                re_compile = re.compile(list_of_bad_lines[index])
                # full_paragraph = re_compile.sub(line, full_paragraph)
                full_paragraph = full_paragraph.replace(fr'{list_of_bad_lines[index]}', line)

            st.write(list_of_bad_lines)
            st.write(list_of_good_lines)
            st.markdown(full_paragraph, unsafe_allow_html=True)


def index_exists(list_of, index):
    try:
        list_of[index]
        return True
    except IndexError:
        return False
