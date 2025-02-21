import difflib
import json
import re

import numpy as np
import streamlit as st
import tensorflow_hub as hub
import tensorflow_text as text
from nltk import WhitespaceTokenizer

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3")


def get_clean_spans(text: str) -> [str]:
    spans = WhitespaceTokenizer().tokenize(text)
    clean_spans = []
    for span in spans:
        if len(span) > 2:
            clean_spans.append(span)
    return clean_spans


def calculate_similarity(keywords: [str], text: str):
    normalized_header = re.sub(r'^[\d,.]+', '', text.lower())
    clean_spans = get_clean_spans(normalized_header)
    if len(clean_spans) > 7:  # в эталоне только короткие заголовки
        return 0
    correct_embeddings = embed(keywords)
    embeddings = embed(clean_spans)
    sim_mat = np.inner(correct_embeddings, embeddings).flatten()
    top = min(len(keywords), 2)
    indexes = np.argpartition(sim_mat, -top)[-top:]
    similarity = sum(sim_mat[indexes]) / top
    return similarity


def analysis(paragraphs) -> None:
    with open('./ideal.json', encoding='utf-8') as f:
        ideal_json = json.load(f)
    confidentiality_header = ideal_json['confidentiality']['header']
    # confidentiality_text = ideal_json['confidentiality']['text']

    is_there_confidentiality: bool = False
    is_there_main_header: bool = False
    is_there_main_header2: bool = False
    is_main_header: bool = False
    # main_headers = 0

    list_of_sub_paragraphs = []
    list_of_links = []

    for paragraph in paragraphs:
        paragraph_text: str = paragraph['paragraphBody']['text']
        paragraph_header = paragraph['paragraphHeader']['text']

        if not is_there_confidentiality:
            if calculate_similarity(ideal_json['confidentiality']['keywords'],
                                    paragraph['paragraphHeader']['text']) > 0.85:
                print_found_paragraph(
                    ideal_json['confidentiality'],
                    paragraph['paragraphHeader']['text'],
                    paragraph_text,
                    list_of_links,
                    -20
                )
                is_there_confidentiality = True
                continue

        if calculate_similarity(ideal_json['security']['keywords'],
                                paragraph_header) > 0.9 and not is_there_main_header2:
            is_there_main_header = True
            is_there_main_header2 = True
            is_main_header = True

        if is_there_main_header:
            ideal_paragraphs = ideal_json['security']['paragraphs']
            flag = False
            max_similarity = 0
            current_paragraph = None
            for ideal_paragraph in ideal_paragraphs:
                if current_paragraph is None:
                    current_paragraph = ideal_paragraph
                if ideal_paragraph['id'] in map(lambda x: x.get('id', -100), list_of_links):
                    continue
                local_similarity = calculate_similarity(ideal_paragraph['keywords'], paragraph_header)
                if local_similarity > max_similarity:
                    current_paragraph = ideal_paragraph
                    max_similarity = local_similarity

            if max_similarity > 0.85:
                flag = True
                print_found_paragraph(current_paragraph,
                                      paragraph_header,
                                      paragraph_text,
                                      list_of_links,
                                      current_paragraph['id'])
                list_of_links[-1]['similarity'] = f' ({round(max_similarity*100)}% {current_paragraph["header"]})'
            if flag:
                list_of_sub_paragraphs.append(current_paragraph['id'])
                is_main_header = False
                continue

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
                is_main_header = False
                continue

            if not flag:
                list_of_links.append({
                    "text": paragraph_header,
                    'similarity': f' ({round(max_similarity*100)}% {current_paragraph["header"]})',
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
                list_of_sub_paragraphs.insert(index, index)
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
        write(link_text, link['messages'],
              True if link['link'] is not None else False,
              link['link'],
              link.get('similarity', None))


def print_found_paragraph(etalon: dict, header: str, text: str, list_of_link: [],
                          paragraph_id=None) -> None:
    # if calculate_similarity(etalon['keywords'], header) > 0.85:
    # if header.find(correct_header) != -1:
    list_of_symbol = ['[', '$', '&',
                      '+', ':', ';',
                      '=', '?', '@',
                      '#', '|', '<',
                      '>', '.', '^',
                      '*', '(', ')',
                      '%', '!', '-', ']']
    spans_ideal = WhitespaceTokenizer().tokenize(text)
    spans = WhitespaceTokenizer().tokenize(etalon['text'])
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
                i] += f'<span style="background-color:rgb(141, 255, 135);display: inline;"> {line[1:]} </span>'
            continue

        if line.startswith('+'):
            are_there_errors = True
            list_of_bad_lines[i] += ' ' + line[1:]
            list_of_good_lines[
                i] += f'<span style="background-color:rgb(254, 204, 203);display: inline;"> {line[1:]} </span>'
            continue

        list_of_good_lines[i] += line
        list_of_bad_lines[i] += line

    for index, line in enumerate(list_of_good_lines):
        line2 = list_of_bad_lines[index].strip()
        for symbol in list_of_symbol:
            line2 = line2.replace(symbol, f'\\{symbol}')

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


def index_exists(list_of, index):
    try:
        list_of[index]
        return True
    except IndexError:
        return False


def write(text, messages, is_link=False, link=None, similarity=None):
    link_text = text.replace('\n', '').replace('\r', '')
    link_text = re.sub(r"[\d\.]{1,4}", "", link_text)
    # if similarity:
    #     link_text += similarity
    if is_link:
        # st.sidebar.markdown(f'[{link_text}](#{link})')
        if similarity:
            st.sidebar.markdown(f'''
                <p style="margin-bottom: 5px;">
                    <a
                        data-text="{similarity}" 
                        class="tooltip"
                        href="#{link}">{link_text}
                    </a>
                </p>
                ''', unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f'''
                <p>
                    <a href="#{link}">{link_text}
                    </a>
                </p>
                ''', unsafe_allow_html=True)
    else:
        st.sidebar.write(text)
    if len(messages) > 0:
        result_str = '<div style="display: flex;gap: 10px;">'
        for msg in messages:
            result_str += get_style(msg)
        result_str += '</div>'
        st.sidebar.markdown(result_str, unsafe_allow_html=True)


def get_style(text: str):
    grey_color = 'rgb(173, 173, 173)'
    orange_color = 'rgb(248, 203, 172)'
    green_color = 'rgb(141, 255, 135)'
    red_color = 'rgb(254, 204, 203)'
    yellow_color = 'rgb(255, 230, 153)'
    purple_color = 'rgb(224, 163, 255)'
    current_color = 'rgb(161, 161, 161)'

    if text == 'Найден, ошибок нет':
        current_color = green_color

    if text == 'Неправильный порядок':
        current_color = yellow_color

    if text == 'Неизвестный пункт':
        current_color = grey_color

    if text == 'Неизвестный текст':
        current_color = purple_color

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
    padding: 5px;
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
