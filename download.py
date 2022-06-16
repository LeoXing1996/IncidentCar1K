import json
import os
import os.path as osp
from argparse import ArgumentParser
from io_utils import download_from_url
from multiprocessing import Manager, Process

TRAIN_JSON = './eccv_train.json'
VAL_JSON = './eccv_val.json'

TRAIN_PATH = './train'
VAL_PATH = './val'


def f(x):
    return x


def download(urls, num_worker, rank, root, error_list, lock):
    keys = list(urls.keys())
    length = len(keys)
    num_samples = length // num_worker
    if length % num_worker != 0:
        num_samples += 1
    n_start = rank * num_samples
    n_end = min((rank + 1) * num_samples, length)

    for idx in range(n_start, n_end):
        tar_path = keys[idx]
        tar_url = urls[tar_path]['url']

        folder = osp.join(root, tar_path.split('/')[0])
        os.makedirs(folder, exist_ok=True)

        try:
            download_from_url(tar_url, dest_dir=folder)
            print(f'RANK: {rank} -- [{idx-n_start+1} / {n_end-n_start}] '
                  '--  File \'{tar_path}\' Succ.')
        except Exception:
            print(f'RANK: {rank} -- [{idx-n_start+1} / {n_end-n_start}] '
                  '--  File \'{tar_path}\' Error.')
            lock.acquire()
            error_list.append(f'{tar_path}: {str(urls[tar_path])}')
            lock.release()


def get_kind(kind):
    if kind == 'car':
        return ['car', 'van', 'bus', 'track']
    return None


if __name__ == '__main__':
    parser = ArgumentParser('Incident downloader')
    parser.add_argument('--subset', choices=['train', 'val'])
    parser.add_argument('--objects', help='which object want to donwload')
    parser.add_argument('--kind',
                        help='which kind of objects want to download')
    parser.add_argument('--num-worker', type=int, default=4)
    args = parser.parse_args()
    # main(args.subset, args.num_worker, kinds=get_kind(args.kind))

    n_worker = args.num_worker
    subset = args.subset
    kinds = get_kind(args.kind)

    if subset == 'train':
        json_file = TRAIN_JSON
        tar_path = TRAIN_PATH
    else:
        json_file = VAL_JSON
        tar_path = VAL_PATH

    with open(json_file, 'r') as file:
        urls = json.load(file)

    if kinds is not None:
        if not isinstance(kinds, list):
            kinds = [kinds]
        urls_new = dict()
        for name, cont in urls.items():
            if any([k in name for k in kinds]):
                urls_new[name] = cont
        urls = urls_new

    # TOOD: just for debug --> clip the urls
    # urls_new = dict()
    # for idx, url in enumerate(urls):
    #     if idx >= 10:
    #         break
    #     urls_new[url] = urls[url]

    jobs = []
    job_running = 0
    error_list = Manager().list()
    lock = Manager().Lock()

    for rank in range(n_worker):
        p = Process(target=download,
                    args=(urls, n_worker, rank, tar_path, error_list, lock))
        jobs.append(p)
        p.start()
        job_running += 1

    for p in jobs:
        p.join()
    print(error_list)

    with open('error_list.txt', 'w') as file:
        for line in error_list:
            file.write(line + '\n')
