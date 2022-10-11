import re

import streamlit as st
import json
import difflib

from nltk import WhitespaceTokenizer


def analysis(paragraphs) -> None:
    ideal_json = open('./ideal.json', encoding='utf-8')
    ideal_json = json.load(ideal_json)

    confidentiality_header = ideal_json['confidentiality']['header']
    confidentiality_text = ideal_json['confidentiality']['text']

    is_there_confidentiality: bool = False
    is_there_main_header: bool = False
    is_there_main_header2: bool = False
    is_main_header: bool = False
    list_of_sub_paragraphs = []
    list_of_links = []

    for paragraph in paragraphs:
        paragraph_text: str = paragraph['paragraphBody']['text']
        paragraph_header = paragraph['paragraphHeader']['text']

        if not is_there_confidentiality:
            is_there_confidentiality = confidentiality(
                confidentiality_header,
                confidentiality_text,
                paragraph['paragraphHeader']['text'],
                paragraph_text,
                list_of_links
            )
            if is_there_confidentiality:
                continue

        if paragraph_header.find(ideal_json['security']['MainHeader']) != -1:
            is_there_main_header = True
            is_there_main_header2 = True
            is_main_header = True

        if is_there_main_header:
            ideal_paragraphs = ideal_json['security']['paragraphs']
            flag = False
            for ideal_paragraph in ideal_paragraphs:
                flag = confidentiality(ideal_paragraph['header'],
                                       ideal_paragraph['text'],
                                       paragraph_header,
                                       paragraph_text,
                                       list_of_links)
                if flag:
                    list_of_sub_paragraphs.append(ideal_paragraph['id'])
                    break

            if not flag and not is_main_header:
                # is_there_main_header = False
                print('123')
            elif not flag and is_main_header:
                list_of_links.append({
                    "text": paragraph_header,
                    "link": re.sub(r'\s', '', paragraph_header[:15])
                })
                st.header(paragraph_header, anchor=re.sub(r'\s', '', paragraph_header[:15]))
                st.write(paragraph_text)
                is_main_header = False
                continue
            else:
                is_main_header = False
                continue
        list_of_links.append({
            "text": paragraph_header,
            "link": re.sub(r'\s', '', paragraph_header[:15])
        })
        st.header(paragraph_header, anchor=re.sub(r'\s', '', paragraph_header[:15]))
        st.write(paragraph_text)

    if not is_there_confidentiality:
        st.sidebar.error(f'Заголовок "{confidentiality_header}" не найден')

    if not is_there_main_header2:
        st.sidebar.error(f'Заголовок "Требования к безопасности" не был найден')
    else:
        ideal_paragraphs = ideal_json['security']['paragraphs']
        for ideal_paragraph in ideal_paragraphs:
            index = ideal_paragraph['id']
            if ideal_paragraph['id'] not in list_of_sub_paragraphs:
                st.sidebar.error(f"Не найден заголовок {ideal_paragraph['header']}")
                continue
            if index_exists(list_of_sub_paragraphs, index):
                if list_of_sub_paragraphs[index] != index:
                    st.sidebar.error(f'{ideal_paragraph["header"]} не на своем месте')

    for link in list_of_links:
        # print(f'[{link["text"]}](#{link["link"]})')
        link_text = link['text'].replace('\n', '').replace('\r', '')
        st.sidebar.markdown(f'[{link_text}](#{link["link"]})')


def confidentiality(correct_header: str, correct_text: str, header: str, text: str, list_of_link: []) -> bool:
    if header.find(correct_header) != -1:
        spans_ideal = WhitespaceTokenizer().tokenize(text)
        spans = WhitespaceTokenizer().tokenize(correct_text)
        i = -1
        list_of_bad_lines: [str] = []
        list_of_good_lines: [str] = []
        diff = difflib.unified_diff(spans, spans_ideal)
        are_there_errors = False

        for ind, line in enumerate(diff):
            if line.startswith('---') or line.startswith('+++'):
                continue
            if line.startswith('@@') and line.endswith('@@\n'):
                i += 1
                continue
            if not index_exists(list_of_good_lines, i):
                list_of_good_lines.append('')
            if not index_exists(list_of_bad_lines, i):
                list_of_bad_lines.append('')

            if line.startswith('-'):
                are_there_errors = True
                list_of_good_lines[
                    i] += f'<span style="background-color:lawngreen;display: inline;"> {line[1:]} </span>'
                continue

            if line.startswith('+'):
                are_there_errors = True
                list_of_bad_lines[i] += ' ' + line[1:]
                list_of_good_lines[i] += f'<span style="background-color:red;display: inline;"> {line[1:]} </span>'
                continue

            list_of_good_lines[i] += line
            list_of_bad_lines[i] += line

        for index, line in enumerate(list_of_good_lines):
            line2 = list_of_bad_lines[index].strip().replace('.', '\\.')
            line2 = re.sub(r'\s+', '\\\s+', line2)
            re_compile = re.compile(line2)
            text = re_compile.sub(line, text)

        if are_there_errors:
            st.sidebar.error(f"Есть ошибки в {header}")

        list_of_link.append({
            "text": header,
            "link": re.sub(r'\s', '', header[:15])
        })
        st.header(header, re.sub(r'\s', '', header[:15]))
        st.markdown(text, unsafe_allow_html=True)

        return True
    else:
        return False


def index_exists(list_of, index):
    try:
        list_of[index]
        return True
    except IndexError:
        return False
