import base64
import codecs
import os
import subprocess

from udemy.decryptor import mp4parse, widevine_pssh_pb2
from udemy.logger import logger


def check_for_aria():
    try:
        subprocess.Popen(["aria2c", "-v"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL).wait()
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(
            msg="> Unexpected exception while checking for Aria2c, please tell the program author about this! ",
            new_line=True
        )
        logger.error(
            msg=e,
            new_line=True
        )
        return True


def check_for_ffmpeg():
    try:
        subprocess.Popen(["ffmpeg"],
                         stderr=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL).wait()
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(
            msg="> Unexpected exception while checking for FFMPEG, please tell the program author about this! ",
            new_line=True
        )
        logger.error(
            msg=e,
            new_line=True
        )
        return True


def check_for_mp4decrypt():
    try:
        subprocess.Popen(["mp4decrypt"],
                         stderr=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL).wait()
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(
            msg="> Unexpected exception while checking for MP4Decrypt, please tell the program author about this! ",
            new_line=True
        )
        logger.error(
            msg=e,
            new_line=True
        )
        return True


def mux_process(video_title, video_filepath, audio_filepath, output_path):
    """
    @author Jayapraveen
    """
    if os.name == "nt":
        command = (
            f"ffmpeg -y -i \"{video_filepath}\" -i \"{audio_filepath}\" "
            f"-acodec copy -vcodec copy -fflags +bitexact -map_metadata -1 "
            f"-metadata title=\"{video_title}\" \"{output_path}\""
        )
    else:
        command = (
            f"nice -n 7 ffmpeg -y -i \"{video_filepath}\" -i \"{audio_filepath}\" "
            f"-acodec copy -vcodec copy -fflags +bitexact -map_metadata -1 "
            f"-metadata title=\"{video_title}\" \"{output_path}\""
        )
    os.system(command)

def decrypt(keys_decryptors, kid, in_filepath, out_filepath):
    """
    @author Jayapraveen
    """
    logger.info(msg="> Decrypting, this might take a minute...", new_line=True)
    try:
        key = keys_decryptors[kid.lower()]
        if (os.name == "nt"):
            os.system(f"mp4decrypt --key 1:%s \"%s\" \"%s\"" %
                      (key, in_filepath, out_filepath))
        else:
            os.system(f"nice -n 7 mp4decrypt --key 1:%s \"%s\" \"%s\"" %
                      (key, in_filepath, out_filepath))
        logger.info(msg="> Decryption complete", new_line=True)
    except KeyError:
        raise KeyError("Key not found")


def extract_kid(mp4_file):
    """
    Parameters
    ----------
    mp4_file : str
        MP4 file with a PSSH header


    Returns
    -------
    String

    """

    boxes = mp4parse.F4VParser.parse(filename=mp4_file)
    for box in boxes:
        if box.header.box_type == 'moov':
            pssh_box = next(x for x in box.pssh if x.system_id == "edef8ba979d64acea3c827dcd51d21ed")
            hex = codecs.decode(pssh_box.payload, "hex")

            pssh = widevine_pssh_pb2.WidevinePsshData()
            pssh.ParseFromString(hex)
            content_id = base64.b16encode(pssh.content_id)
            return content_id.decode("utf-8")

    # No Moof or PSSH header found
    return None