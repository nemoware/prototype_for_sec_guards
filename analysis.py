import difflib
import json
import re

import streamlit as st
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
                list_of_links,
                -20
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
                                       list_of_links,
                                       ideal_paragraph['id'])
                if flag:
                    list_of_sub_paragraphs.append(ideal_paragraph['id'])
                    break

            if not flag and is_main_header:
                obj = {
                    "text": paragraph_header,
                    "link": re.sub(r'\s', '', paragraph_header[:15]),
                    "messages": []
                }
                st.header(paragraph_header, anchor=re.sub(r'\s', '', paragraph_header[:15]))
                if paragraph_text:
                    st.write(paragraph_text)
                    obj['messages'].append('Неизвестный текст')
                write(paragraph_header, obj['messages'], True, obj['link'])
                # list_of_links.append(obj)
                is_main_header = False
                continue

            if flag:
                is_main_header = False
                continue

            if not flag:
                list_of_links.append({
                    "text": paragraph_header,
                    "link": re.sub(r'\s', '', paragraph_header[:15]),
                    "messages": ["Неизвестный пункт"],
                    "unknown": True
                })
                st.header(paragraph_header, anchor=re.sub(r'\s', '', paragraph_header[:15]))
                st.write(paragraph_text)
                continue
        st.header(paragraph_header, anchor=re.sub(r'\s', '', paragraph_header[:15]))
        st.write(paragraph_text)

    if not is_there_confidentiality:
        write(confidentiality_header, ['Не найден пункт'])

    if not is_there_main_header2:
        main_header = ideal_json['security']['MainHeader']
        write(main_header, ['Не найден пункт'])
    else:
        ideal_paragraphs = ideal_json['security']['paragraphs']
        for ideal_paragraph in ideal_paragraphs:
            index = ideal_paragraph['id']
            if index not in list_of_sub_paragraphs:
                list_of_links.insert(index, {
                    "text": ideal_paragraph['header'],
                    "link": None,
                    "messages": ["Не найден пункт"]
                })
                continue

            obj = next(item for item in list_of_links if item.get('id', -1) == index)
            if index_exists(list_of_sub_paragraphs, index):
                if list_of_sub_paragraphs[index] != index:
                    obj['messages'].append("Неправильный порядок")
            else:
                obj['messages'].append("Неправильный порядок")

    list_of_links2 = []
    is_it_scum = True
    for link in reversed(list_of_links):
        if is_it_scum:
            if not link.get('unknown', False):
                is_it_scum = False
                list_of_links2.append(link)
        else:
            list_of_links2.append(link)
    list_of_links2.reverse()

    for link in list_of_links2:
        link_text = link['text'].replace('\n', '').replace('\r', '')
        write(link_text, link['messages'], True if link['link'] is not None else False, link['link'])


def confidentiality(correct_header: str, correct_text: str, header: str, text: str, list_of_link: [],
                    paragraph_id=None) -> bool:
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

        obj = {
            "id": paragraph_id,
            "text": header,
            "link": re.sub(r'\s', '', header[:15]),
            "messages": []
        }

        if are_there_errors:
            obj['messages'].append('Ошибки')
        else:
            obj['messages'].append("Найден, ошибок нет")
        if paragraph_id == -20:
            write(header, obj['messages'], True, re.sub(r'\s', '', header[:15]))
        else:
            list_of_link.append(obj)
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


def write(text, messages, is_link=False, link=None):
    link_text = text.replace('\n', '').replace('\r', '')
    link_text = re.sub(r"[\d\.]{1,4}", "", link_text)
    if is_link:
        st.sidebar.markdown(f'[{link_text}](#{link})')
    else:
        st.sidebar.write(text)
    result_str = '<div style="display: flex;gap: 10px;">'
    for msg in messages:
        result_str += get_style(msg)
    result_str += '</div>'
    st.sidebar.markdown(result_str, unsafe_allow_html=True)


def get_style(text: str):
    grey_color = '#808080'
    orange_color = 'rgb(248, 203, 172)'
    green_color = 'lawngreen'
    red_color = 'rgb(254, 204, 203)'
    yellow_color = 'rgb(255, 230, 153)'
    current_color = '#808080'

    if text == 'Найден, ошибок нет':
        current_color = green_color

    if text == 'Неправильный порядок':
        current_color = yellow_color

    if text == 'Неизвестный пункт':
        current_color = grey_color

    if text == 'Не найден пункт':
        current_color = red_color

    if text == 'Ошибки':
        current_color = orange_color

    return f'''
    <span style="text-size-adjust: 100%;
    -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
    -webkit-font-smoothing: auto;
    user-select: auto;
    box-sizing: border-box;
    font-size: 1rem;
    font-weight: normal;
    line-height: 1.6;
    pointer-events: auto;
    height: auto;
    padding-top: 8px;
    padding-right: 8px;
    padding-bottom: 8px;
    padding-left: 8px;
    margin-top: 0px;
    margin-bottom: 0px;
    border-top-left-radius: 0.25rem;
    border-top-right-radius: 0.25rem;
    border-bottom-right-radius: 0.25rem;
    border-bottom-left-radius: 0.25rem;
    box-shadow: none;
    transition-property: all;
    transition-duration: 200ms;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    -webkit-box-pack: justify;
    justify-content: space-between;
    border: 0px;
    opacity: 1;
    background-color: {current_color};">{text}</span>'''
