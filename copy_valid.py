import os
import json
from argparse import ArgumentParser
import shutil
from tqdm import tqdm


def get_args():
    parser = ArgumentParser()
    parser.add_argument('--file_name', type=str, default='train_valid.json')
    parser.add_argument('--tar_folder', type=str, default='train_valid')
    return parser.parse_args()


def main():
    """This function copy all valid file in annotation file to a target folder.
    """
    args = get_args()
    file_name = args.file_name
    tar_folder = args.tar_folder

    os.makedirs(tar_folder, exist_ok=True)

    with open(file_name, 'r') as file:
        anno_dict = json.load(file)

    img_ids = list(anno_dict.keys())

    img_idx = 0  # the index for image to save
    for idx in tqdm(img_ids):
        path = anno_dict[idx]['path']
        label = anno_dict[idx]['label']
        is_valid = anno_dict[idx]['valid']
        if not is_valid:
            continue

        suffix = path.split('.')[-1]
        shutil.copy2(path, os.path.join(tar_folder, f'{img_idx}.{suffix}'))
        with open(os.path.join(tar_folder, 'label.txt'), 'a+') as file:
            file.write(label+'\n')

        img_idx += 1


if __name__ == '__main__':
    main()
