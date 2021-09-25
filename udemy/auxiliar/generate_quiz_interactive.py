import json
import os
import shutil
import sys
import bs4
from typing import Dict, List, Tuple, Union, Any

from bs4 import Tag

from udemy.auxiliar.decrypt_all_sources import walk_recursively


def set_validated_quiz(quiz: Dict, validated: bool, wrong_reasons=None) -> Dict:
    if wrong_reasons is None:
        wrong_reasons = []

    quiz["validated"] = validated
    quiz["wrong_reasons"] = wrong_reasons

    return quiz


def are_same_objects(obj1_checker, obj2):
    if not isinstance(obj1_checker, type(obj2)):
        return False
    if isinstance(obj1_checker, dict):
        for k, v in obj1_checker.items():
            # Validate keys
            if k not in obj2:
                return False

            # Validate values
            if not are_same_objects(obj1_checker[k], obj2[k]):
                return False
    if isinstance(obj1_checker, (list, tuple)):
        for item in obj1_checker:
            # Validate recursively every struct for each element
            if not are_same_objects(obj1_checker[0], item):
                return False

    return True


def check_struct_json(validator_json: Union[List, Dict, Tuple, type], json_invalidate: Union[List, Dict], key="") -> Tuple[Union[List, Tuple, Dict], List]:
    list_errors = []
    if type(validator_json) == type or isinstance(validator_json, tuple):
        # multiple choices
        correct_field = validator_json == type(json_invalidate)
        if isinstance(validator_json, tuple) and validator_json:
            if type(validator_json[0]) == type:
                correct_field = any([x == type(json_invalidate) for x in validator_json])

        if not correct_field:
            # No correct type
            list_errors.append("<h3>NO CORRECT TYPE</h3>")
            list_errors.append(f"<p>HAS {type(json_invalidate)}</p>")
            list_errors.append(f"<p>NEED {type(validator_json)}</p>")
            print(f"NO CORRECT TYPE: {key}", file=sys.stderr)
            print(f"    HAS {type(json_invalidate)}", file=sys.stderr)
            print(f"    NEED {type(validator_json)}", file=sys.stderr)
            return validator_json, list_errors
        else:
            validator_json = True

    if isinstance(validator_json, dict):
        for k,v in validator_json.items():
            # Validate keys
            if k not in json_invalidate:
                # No key found
                validator_json[k] = False
                list_errors.append(f"NO KEY '{k}' FOUND")
                list_errors.append(f"<p>HAS {type(json_invalidate.keys())}</p>")
                list_errors.append(f"<p>NEED {type(validator_json.keys())}")
                print(f"NO KEY '{k}' FOUND", file=sys.stderr)
                print(f"    HAS {type(json_invalidate.keys())}", file=sys.stderr)
                print(f"    NEED {type(validator_json.keys())}", file=sys.stderr)
                return validator_json, list_errors

            # Validate values
            validator_json[k], _list_errors = check_struct_json(validator_json[k], json_invalidate[k], key=f"{key}.{k}")
            list_errors += _list_errors
    if isinstance(validator_json, (list, tuple)):
        arr_validator = []
        for i in range(len(json_invalidate)):
            item = json_invalidate[i]
            # Validate recursively every struct for each element
            _validator_json, _list_errors = check_struct_json(validator_json[0], item, key=f"{key}.{i}")
            arr_validator.append(_validator_json)
            list_errors += _list_errors
        validator_json = arr_validator

    if type(validator_json) == type:
        # No correct type
        list_errors.append("<h3>NO CORRECT TYPE</h3>")
        list_errors.append(f"<p>HAS {type(json_invalidate)}</p>")
        list_errors.append(f"<p>NEED {validator_json}</p>")
        print(f"NO CORRECT TYPE: {key}", file=sys.stderr)
        print(f"    HAS {type(json_invalidate)}", file=sys.stderr)
        print(f"    NEED {validator_json}", file=sys.stderr)
        validator_json = False

    return validator_json, list_errors


def is_a_well_quiz(quiz: Dict) -> Tuple[bool, List]:
    # Comprobar diferentes cabeceras del quiz
    #   id
    #   title
    #   questions [
    #       feedbacks {
    #           a,b,c,d
    #       answers {
    #            a,b,c,d
    #       correct_response [
    #            a,d
    #       related_lectures [
    validator = {
        "id": (str, int),
        "title": str,
        "questions": [
            {
                "feedbacks": dict,
                "answers": dict,
                "correct_response": list,
                "related_lectures": list
            }
        ],
    }
    correct_quiz = {
        "id": True,
        "title": True,
        "questions": [
            {
                "feedbacks": True,
                "answers": True,
                "correct_response": True,
                "related_lectures": True
            }
        ],
    }
    no_related_lectures = {
        "id": True,
        "title": True,
        "questions": [
            {
                "feedbacks": True,
                "answers": True,
                "correct_response": True,
                "related_lectures": False
            }
        ],
    }

    validator_processed, errors = check_struct_json(validator, quiz)

    if are_same_objects(correct_quiz, validator_processed):
        return True, errors
    elif are_same_objects(no_related_lectures, validator_processed):
        return True, errors

    return False, errors


def get_quiz_formated(quiz: Dict) -> Dict:
    validated, wrong_reasons = is_a_well_quiz(quiz)
    formatted_quiz = set_validated_quiz(quiz, validated, wrong_reasons=wrong_reasons)

    return formatted_quiz


def get_json_quizzes(path):
    # Copia del template en la carpeta destino
    dirs_path, files_path = walk_recursively(path, pattern_file=r"\.json$")
    quizzes_json = []
    for quiz_path in files_path:
        quiz_json = {}
        with open(quiz_path, "r", encoding="utf8") as quiz_json_reader:
            quiz_json_str = quiz_json_reader.read()
            if quiz_json_str:
                quiz_json = json.loads(quiz_json_str)
                quizzes_json.append(quiz_json)

    return quizzes_json


def copy_interactive_quizzes(template_path, dest_path) -> str:
    int_quiz_path = os.path.join(dest_path, "interactive_quizzes")
    server_path = os.path.join(dest_path, "server.py")
    if os.path.isdir(int_quiz_path):
        shutil.rmtree(int_quiz_path)
    if os.path.isfile(server_path):
        os.remove(server_path)
    shutil.copytree(template_path, int_quiz_path)
    quiz_index_path = os.path.join(int_quiz_path, "index.html")
    shutil.rmtree(os.path.join(int_quiz_path, "json_example"))

    shutil.move(os.path.join(int_quiz_path, "server.py"), dest_path)

    if not os.path.isfile(quiz_index_path):
        raise Exception(f"Doesnt exist index.html file required in {int_quiz_path}")

    return quiz_index_path


def add_quiz_to_index(course_name, index_quiz_path, quizzes_path):
    # load the file
    with open(index_quiz_path, "r", encoding="utf8") as reader:
        html_text = reader.read()
        index_soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html_text, features="lxml")
        # add title
        index_soup.head.title.string = course_name
        # remove default quiz
        json_quiz_def: Tag = index_soup.body.find("json-quiz")
        json_quiz_def.extract()
        # add quizzes
        main_tag: Tag = index_soup.body.find("main")
        for quiz_path in quizzes_path:
            rel_quiz_path = os.path.relpath(quiz_path, os.path.dirname(index_quiz_path))
            new_json_quiz = index_soup.new_tag("json-quiz", **{"json-file": rel_quiz_path})
            main_tag.append(new_json_quiz)

    with open(index_quiz_path, "w", encoding="utf8") as writer:
        writer.write(str(index_soup))


def process_json_quizzes(course_name, template_quiz_path, path: str):
    # quizzes = get_json_quizzes(path)
    index_quiz_path = copy_interactive_quizzes(template_quiz_path, path)
    # Copia del template en la carpeta destino
    dirs_path, files_path = walk_recursively(path, pattern_file=r"\.json$")
    for quiz_path in files_path:
        print(quiz_path)
        quiz_formated = {}
        with open(quiz_path, "r", encoding="utf8") as quiz_json_reader:
            quiz_json_str = quiz_json_reader.read()
            if quiz_json_str:
                quiz_json = json.loads(quiz_json_str)
                quiz_formated = get_quiz_formated(quiz_json)

        with open(quiz_path, "w", encoding="utf8") as quiz_json_writer:
            quiz_json_writer.write(json.dumps(quiz_formated))

    add_quiz_to_index(course_name, index_quiz_path, files_path)
    print("To access simply run:")
    print("> python", os.path.join(path, "server.py"))


if __name__ == '__main__':
    process_json_quizzes(
        "[NEW] Ultimate AWS Certified Cloud Practitioner - 2021",
        r"..\..\quiz_template",
        r"E:\Cursos\Udemy\aws-certified-cloud-practitioner-new"
    )


