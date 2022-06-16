import glob
import json
import os
import os.path as osp
from argparse import ArgumentParser
from pathlib import Path
from tkinter import image_names

import numpy as np
import streamlit as st
from PIL import Image

_VALID_SUFFIX = ['png', 'jpg', 'jepg']


def init_image_list(image_info_path, subset):
    if not osp.exists(image_info_path):
        img_name, img_label = load_image_list(subset)
        with open(image_info_path, 'w') as file:
            file_list_info = dict()
            for idx, (full_path, label) in enumerate(zip(img_name, img_label)):
                file_list_info[idx] = dict(
                    path=full_path, label=label)
            json.dump(file_list_info, file)
    with open(image_info_path, 'r') as file:
        file_list_info = json.load(file)
        img_list, img_label = [], []
        for info_dict in file_list_info.values():
            img_list.append(info_dict['path'])
            img_label.append(info_dict['label'])
    return img_list, img_label


def load_image_list(subset):
    img_list = glob.glob(f'{subset}/**/**')

    img_name_valid = []
    img_label_valid = []
    # img_name_valid = []
    for img in img_list:
        img_split = img.split('.')
        if len(img_split) == 1:
            continue
        suffix = img_split[1].upper()
        if any([suffix == tar_suffix.upper() for tar_suffix in _VALID_SUFFIX]):
            try:
                Image.open(img)
                img_name_valid.append(img)
                img_label_valid.append(img.split('/')[1])
                # img_name_valid.append(img_split[1])
            except Exception:
                print(f'{img} is invalid.')

    return img_name_valid, img_label_valid


def get_image(operation, img_list, img_label, pbar):
    import ipdb
    ipdb.set_trace()
    if 'curr_idx' not in st.session_state:
        st.session_state['curr_idx'] = curr_idx = 0
    else:
        curr_idx = st.session_state['curr_idx']
    if operation == 'next':
        curr_idx = min(curr_idx + 1, len(img_list))
    else:
        curr_idx = max(curr_idx - 1, 0)

    if curr_idx == 0:
        st.info('Reach the first image.')
    elif curr_idx == len(img_list):
        st.info('Reach the last image.')

    # update session state
    print(operation, curr_idx)
    st.session_state['curr_idx'] = curr_idx
    img = np.array(Image.open(img_list[curr_idx]))
    label = img_label[curr_idx]
    st.image(img)
    st.text(label)

    pbar.progress(curr_idx / len(img_list))


def init_valid_img_list(valid_file_path, img_list, img_label, canvas, board):
    # print('init valid img list')
    if osp.exists(valid_file_path):
        # check empty file
        if os.stat(valid_file_path).st_size == 0:
            # print('st_size is 0')
            idx = 0
        else:
            with open(valid_file_path, 'r') as file:
                valid_file_info = json.load(file)

            valid_ids = list(valid_file_info.keys())
            for idx in range(len(img_list)):
                if str(idx) not in valid_ids:
                    # print(f'find {idx}')
                    board.info(f'Start at idx: \'{idx}\'')
                    break
    else:
        Path(valid_file_path).touch()
        board.info(f'Create Valid file list at \'{valid_file_path}\'.')
        idx = 0
    st.session_state['curr_idx'] = idx
    show_image(img_list, img_label, canvas, board)


def update_valid_img_list(operation, valid_file_path, img_list, img_label,
                          pbar, canvas, board):
    curr_idx = st.session_state['curr_idx']
    if not osp.exists(valid_file_path):
        st.warning(f'{valid_file_path} not exist!')
        exit()

    info = dict(path=img_list[curr_idx], label=img_label[curr_idx])

    if os.stat(valid_file_path).st_size == 0:
        valid_file_info = dict()
    else:
        with open(valid_file_path, 'r') as file:
            valid_file_info = json.load(file)

    if operation == 'valid':
        info['valid'] = True
        valid_file_info[curr_idx] = info
        curr_idx += 1
        st.session_state['curr_idx'] = min(curr_idx, len(img_list))
    elif operation == 'invalid':
        info['valid'] = False
        valid_file_info[curr_idx] = info
        curr_idx += 1
        st.session_state['curr_idx'] = min(curr_idx, len(img_list))

    else:  # undo
        undo_info = valid_file_info.pop(str(curr_idx-1))
        undo_path, undo_label = undo_info['path'], undo_info['label']
        undo_stat = undo_info['valid']
        st.info(f'Undo: \n'
                f'path: {undo_path}\n'
                f'label: {undo_label}\n'
                f'IsValid: {undo_stat}\n')
        st.session_state['curr_idx'] = max(0, curr_idx-1)

    with open(valid_file_path, 'w') as file:
        json.dump(valid_file_info, file)

    show_image(img_list, img_label, canvas, board)
    pbar.progress(curr_idx / len(img_list))


def show_image(img_list, img_label, canvas, board):
    curr_idx = st.session_state['curr_idx']
    try:
        img = np.array(Image.open(img_list[curr_idx]))

        name = img_list[curr_idx]
        label = img_label[curr_idx]

        board.text(f'Name: {name}\nLabel: {label}')
        # board.text(f'Label: {label}')
        canvas.image(img)
    except Exception as exp_info:
        error_img = np.array(Image.open('error.webp'))
        canvas.image(error_img)
        board.info(exp_info)


def static_valid(file_name):
    with open(file_name, 'r') as file:
        anno_dict = json.load(file)

    img_ids = list(anno_dict.keys())
    total_imgs = len(img_ids)
    valid_imgs = 0
    for info in anno_dict.values():
        if info['valid']:
            valid_imgs += 1
    return f'Valid / Total: {valid_imgs:4d} / {total_imgs:4d}'


def main():
    st.title('Image Fliter!')
    subset = st.sidebar.selectbox('Subset', options=['train', 'val'])

    file_list = st.sidebar.text_input('File list Template',
                                      value='{}_all.json')
    if '{}' in file_list:
        image_info_path = file_list.format(subset)
    else:
        image_info_path = file_list
    img_list, img_label = init_image_list(image_info_path, subset)

    valid_file_path = st.sidebar.text_input(
        'Valid list Template', value='{}_valid.json')
    if not valid_file_path.endswith('json'):
        st.error('Valid list path must ends with \'json\'.')
    if '{}' in valid_file_path:
        valid_file_path = valid_file_path.format(subset)
    else:
        valid_file_path = valid_file_path

    canvas = st.empty()
    board = st.empty()
    init_valid_img_list(valid_file_path, img_list, img_label, canvas, board)

    pbar = st.progress(st.session_state['curr_idx'] / len(img_list))

    # if st.sidebar.button('Last'):
    #     get_image('last', img_list, img_label, pbar)

    # elif st.sidebar.button('Next'):
    #     get_image('next', img_list, img_label, pbar)

    if st.sidebar.button('Valid'):
        update_valid_img_list('valid', valid_file_path,
                              img_list, img_label, pbar, canvas, board)

    if st.sidebar.button('InValid'):
        update_valid_img_list('invalid', valid_file_path,
                              img_list, img_label, pbar, canvas, board)

    if st.sidebar.button('Undo'):
        update_valid_img_list('undo', valid_file_path,
                              img_list, img_label, pbar, canvas, board)
    st.sidebar.write(static_valid(valid_file_path))


if __name__ == '__main__':
    main()
