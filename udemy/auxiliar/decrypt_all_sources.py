import json
import os
import re
import sys

from udemy.decryptor.utils import extract_kid, decrypt, mux_process


def clean_title(title):
    return re.sub(r"[^\w-]", '_', title)


def walk_recursively(path, pattern_file=""):
    all_dirs_path = []
    all_files_path = []
    for _root, d_names, f_names in os.walk(path):
        all_dirs_path += [os.path.join(_root, x) for x in d_names]
        all_files_path += [os.path.join(_root, x) for x in f_names if re.search(pattern_file, x)]
    return all_dirs_path, all_files_path


def decrypt_and_merge(keys_decryptors, video_filepath_enc, audio_filepath_enc, merge_title, output_path):
    print("Desencriptando")
    print(f"    {video_filepath_enc}")
    print(f"    {audio_filepath_enc}")
    video_filepath_dec = re.sub(r"encrypted\.mp4$", "decrypted.mp4", video_filepath_enc)
    audio_filepath_dec = re.sub(r"encrypted\.m4a$", "decrypted.m4a", audio_filepath_enc)
    print(f"    {video_filepath_dec}")
    print(f"    {audio_filepath_dec}")
    try:
        if keys_decryptors:
            if os.path.isfile(video_filepath_enc):
                video_kid = extract_kid(video_filepath_enc)
                print("    KID for video file is: " + video_kid)
                decrypt(keys_decryptors, video_kid, video_filepath_enc, video_filepath_dec)
            if os.path.isfile(audio_filepath_enc):
                audio_kid = extract_kid(audio_filepath_enc)
                print("    KID for audio file is: " + audio_kid)
                decrypt(keys_decryptors, audio_kid, audio_filepath_enc, audio_filepath_dec)
            if os.path.isfile(video_filepath_dec) and os.path.isfile(audio_filepath_dec):
                mux_process(merge_title, video_filepath_dec, audio_filepath_dec, output_path)
            print("Desencriptacion completada")
            print(merge_title, output_path)
    except Exception as err:
        print(err, file=sys.stderr)

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


if __name__ == '__main__':
    keyfile_path = os.path.join(os.getcwd(), "keyfile.json")
    keyfile_data = {}
    with open(keyfile_path, 'r') as keyfile:
        keyfile = keyfile.read()
        if keyfile:
            keyfile_data = json.loads(keyfile)

    pttr_audio_enc = r"\.encrypted\.m4a$"

    dirs, files = walk_recursively("E:\\Cursos\\Udemy\\", pattern_file=pttr_audio_enc)
    files = sorted(files)

    # Ficheros con audio y video encriptado y que no tengan ya uno desencriptado y final
    audios_enc_dec = [x for x in files if not os.path.isfile(re.sub(pttr_audio_enc, ".mp4", x))]

    # Ficheros que ya esten desencriptados pero no mergeados
    audios_dec = [
        re.sub(pttr_audio_enc, ".decrypted.mp4", x)
        for x in audios_enc_dec
        if os.path.isfile(re.sub(pttr_audio_enc, ".decrypted.mp4", x)) and os.path.isfile(re.sub(pttr_audio_enc, ".decrypted.m4a", x))
    ]
    # Ficheros que ni estan desencriptados ni mergeados
    audios_enc = [
        x
        for x in audios_enc_dec
        if not os.path.isfile(re.sub(pttr_audio_enc, ".decrypted.mp4", x)) or not os.path.isfile(re.sub(pttr_audio_enc, ".decrypted.m4a", x))
    ]

    if audios_dec:
        for audio_path_dec in audios_dec:
            video_path_dec = re.sub(pttr_audio_enc, ".decrypted.m4a", audio_path_dec)
            final_name = re.sub(pttr_audio_enc, ".mp4", video_path_dec)
            mux_process(re.sub(pttr_audio_enc, "", video_path_dec), video_path_dec, audio_path_dec, final_name)

    if audios_enc:
        for audio_path_enc in audios_enc:
            final_name = os.path.basename(re.sub(pttr_audio_enc, ".mp4", audio_path_enc))
            video_path_enc = re.sub(pttr_audio_enc, ".encrypted.mp4", audio_path_enc)
            output_path = os.path.dirname(audio_path_enc)
            decrypt_and_merge(keyfile_data, video_path_enc, audio_path_enc, re.sub(r"\.mp4", "", final_name), os.path.join(output_path, final_name))

    # BORRADO
    dirs, files = walk_recursively("E:\\Cursos\\Udemy\\", pattern_file=r"\.(de|en)crypted\.m(p4|4a)")
    files = sorted(files)
    files = [x for x in files if os.path.isfile(re.sub(r"\.(de|en)crypted\.m(p4|4a)", ".mp4", x))]
    print(get_size("E:\\Cursos\\Udemy\\")/1024/1024, 'MB')
    for dec in files:
        os.remove(dec)
    print(get_size("E:\\Cursos\\Udemy\\")/1024/1024, 'MB')

    # Arreglar la cagada de cambio de nombres
    # os.path.isfile
    # dirs, files = walk_recursively("E:\\Cursos\\Udemy\\", pattern_file=r"^.+\.decrypted\.(mp4|m4a)$")
    # files = sorted(files)
    # files_paired = [(files[i], files[i+1]) for i in range(len(files)-1) if files[i][:-4] == files[i+1][:-4]]
    # files = sorted(files)
    # files_not_paired = [files[i] for i in range(len(files)-1) if files[i][:-4] != files[i+1][:-4]]
    # print(len(files_not_paired))
    # print(*files_not_paired, sep="\n")
    # print()
    # print(len(files_paired))
    # print(*files_paired, sep="\n")
    # for video_dec in files_not_paired:
    #     if re.search(r"\.decrypted\.mp4$", video_dec):
    #         audio_dec = re.sub(r"\.decrypted.mp4$", ".decrypted.m4a", video_dec)
    #         video_enc = re.sub(r"\.decrypted.mp4$", ".encrypted.mp4", video_dec)
    #         if not os.path.isfile(audio_dec):
    #             os.rename(video_enc, audio_dec)
    #
    #         mux_process(re.sub(r"\.decrypted.mp4$", "", video_dec), video_dec, audio_dec, re.sub(r"\.decrypted\.mp4$", ".mp4", video_dec))