# coding: utf-8
import os
import sys
from pyPdf import PdfFileReader
import subprocess
import yaml
import requests
import getpass
from requests.exceptions import ConnectionError

url = "http://localhost:8000/"
headers = {"Accept": "application/json"}
cookies = {}

def login():
    global cookies
    print "Logging you in"
    username = raw_input("username: ")
    password = getpass.getpass("password: ")
    try:
        r = requests.post(url + "login/", 
            data = {'username':username, "password": password},
            headers=headers,
            allow_redirects=True)
    except ConnectionError:
        print "Server seems unreachable"
        sys.exit(1)
    if r.status_code == 200:
        print "Login ok"
        cookies = r.cookies
    elif r.status_code == 401:
        print "Wrong credentials"
        return login()
    else:
        print r.status_code
        print r.text
        sys.exit(1)


def generate_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in [f for f in filenames if f.endswith(".pdf")]:
            yield os.path.join(dirpath, filename)


def get_pdf_info(pdf_file_path):
    infos = {}
    with open(pdf_file_path) as f:
        pdf_reader = PdfFileReader(f)
        pdf_infos = pdf_reader.getDocumentInfo()
        if pdf_infos is not None:
            infos['title'] = pdf_infos.title
            infos['authors'] = pdf_infos.author
        else:
            infos['title'] = None
            infos['authors'] = None
    return infos

def print_help():
    print "This is the set of commands you can use any time you are prompted"
    print "/h, /help -- shows this help"
    print "/s, /show -- opens the pdf"
    print "/n, /next -- skip this file"

glob_commands = ["help", "h", "s", "show", "n", "next"]

def get_input(prompt_string=""):
    try:
        out = raw_input(">>>> " +prompt_string)
    except KeyboardInterrupt:
        clean_exit()
    if out.startswith("/"):
        command = out[1:]
        if not command in glob_commands:
            print "Command not understood."
            print_help()
            return get_input()
    else:
        command = None

    return out, command

subprocesses = []

def is_skip(command):
    return command in ["n","next"]

def exec_command(command, filename):
    if command in ["h", "help"]:
        return print_help()
    elif command in ["s", "show"]:
        if sys.platform == "linux" or sys.platform == "linux2":
            open_command = "gnome-open"
        elif sys.platform == "darwin":
            open_command = "open"
        subprocesses.append(subprocess.Popen(["gnome-open", filename]))


def handle_command(command, filename):
    if is_skip(command):
        return False
    else:
        exec_command(command, filename)
        return True

def get_info_name(filename):
    return filename.replace(".pdf", ".nfo")


def send_infos(infos, filename):
    print "sending infos..."
    r = requests.post(url + "upload/",
        headers=headers,
        files={"document": open(filename, "rb")},
        data=infos,
        cookies=cookies
        )
    if r.status_code == 200:
        print "yay one more"
        return True
    else:
        print "Something went wrong sending the document"
        print r.status_code
        print r.text
        return False


def save_infos(infos, filename):
    dirname = os.path.dirname(filename)
    name = os.path.basename(filename).replace(".pdf", ".nfo")
    with open(os.path.join(dirname, name), "w") as _:
        _.write(yaml.dump(infos, indent=4))


def wrap_out(infos, filename, file_gen):
    save_infos(infos, filename)
    send_infos(infos, filename)
    try:
        filename = file_gen.next()
    except StopIteration:
        sys.exit(0)
    return filename

def clean_exit():
    print "\n leaving...\n"
    sys.exit(0)

def do_skip(file_gen):
    try:
        filename = file_gen.next()
    except StopIteration:
        clean_exit()
    return filename

if __name__ == '__main__':
    login()
    dir_path = sys.argv[1]
    skip_nfo = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "--skip-nfo":
            skip_nfo = True

    file_gen = generate_files(dir_path)
    filename = file_gen.next()
    while True:
        skip = False
        sent = False
        print ">>>> {}".format(os.path.basename(filename))
        info_file = get_info_name(filename)
        if os.path.isfile(info_file):
            if not skip_nfo:
                with open(info_file, "r") as _:
                    infos = yaml.load(_)
                print yaml.dump(infos, indent=4)
                print "\n"
                while True:
                    ok, command = get_input("A corresponding .nfo file has been found. Do you want to use it? (y/n) ")
                    if command:
                        if not handle_command(command, filename):
                            skip = True
                            break
                        else:
                            continue
                    if ok in ["y", "Y"]:
                        filename = wrap_out(infos, filename, file_gen)
                        sent = True
                    break
                if sent:
                    continue
                if skip:
                    filename = do_skip(file_gen)
                    continue
            else:
                print "Skipping {}".format(os.path.basename(filename))
                filename = do_skip(file_gen)
                continue
        try:
            infos = get_pdf_info(filename)
        except Exception:
            filename = file_gen.next()
            continue
        
        print "\n=== Getting title info ===\n"
        # Getting title info
        while True:  
            print "What title do you want for the document? "
            print "1) {}\n2) {}\n3) None of that, let me choose".format(
                    os.path.basename(filename), infos["title"])
            raw_choice, command = get_input()
            if command:
                if not handle_command(command, filename):
                    skip = True
                    break
                else:
                    continue
            try:
                choice = int(raw_choice)
                if choice == 1:
                    infos["title"] = os.path.basename(filename)
                elif choice == 2:
                    pass
                elif choice == 3:
                    while True:
                        title, command = get_input("enter your choice: ")
                        if command:
                            if not handle_command(command, filename):
                                skip = True
                                break
                            else:
                                continue
                        if skip:
                            break
                        infos["title"] = title
                        print "<<<< {}".format(title)
                        break
                else:
                    print "Choice not understood"
                    continue
                if infos["title"] is None or infos["title"] == "":
                    print "Title '{}' is not valid".format(infos["title"])
                    continue
                else:
                    break
            except ValueError:
                continue
        if skip:
            filename = do_skip(file_gen)
            continue

        # Getting authors info
        print "\n==== Getting authors infos ====\n"
        while True:
            print "Is {} a correct value for authors (y/n)".format(infos["authors"])
            ok, command = get_input()
            if command:
                if not handle_command(command, filename):
                    skip = True
                    break
                else:
                    continue
            if ok in ["y", "Y"]:
                break
            else:
                while True:
                    authors, command = get_input('Enter a comma separated list of authors: ')
                    if command:
                        if not handle_command(command, filename):
                            skip = True
                            break
                        else:
                            continue
                    if skip:
                        break
                    infos["authors"] = [a.strip() for a in authors.split(",")]
                    break
                break
        if skip:
            filename = do_skip(file_gen)
            continue

        # Res type
        print "\n==== Getting resource type infos ====\n"
        while True:
            print "Choose a type of document:\n1) {}\n2) {}\n3) {}\n4) {}\n5) Other".format(
                "Paper", "Proceedings", "Tutorial", "Book")
            raw_choice, command = get_input()
            if command:
                if not handle_command(command, filename):
                    skip = True
                    break
                else:
                    continue

            try:
                choice = int(raw_choice)
                if choice == 1:
                    infos["res_type"] = "Paper"
                elif choice == 2:
                    infos["res_type"] = "Proceedings"
                elif choice == 3:
                    infos["res_type"] = "Tutorial"
                elif choice == 4:
                    infos["res_type"] = "Book"
                elif choice == 5:
                    while True:
                        res_type, command = get_input('Enter the type of document: ')
                        if command:
                            if not handle_command(command, filename):
                                skip = True
                                break
                            else:
                                continue
                        infos["res_type"] = res_type
                        break
                    if skip:
                        break
                else:
                    print "Choice not understood"
                    continue
                break
            except ValueError:
                continue

        if skip:
            filename = do_skip(file_gen)
            continue

        # tags
        print "\n==== Getting tags infos ====\n"
        while True:
            tags, command = get_input("Enter a comma separated list of tags: ")
            if command:
                if not handle_command(command, filename):
                    skip = True
                    break
                else:
                     continue
            infos["tags"] = [t.strip() for t in tags.split(",")]
            break

        if skip:
            filename = do_skip(file_gen)
            continue

        print " Title: {}\n Authors: {}\n Resource type: {}\n Tags: {}\n".format(
            infos["title"], infos["authors"], infos["res_type"], infos["tags"])

        while True:
            ok, command = get_input("Do you confirm? (y/n):")
            if command:
                if not handle_command(command, filename):
                    skip = True
                    do_skip(file_gen)
                    break
                else:
                    continue
            if ok in ["y", "Y"]:
                filename = wrap_out(infos, filename, file_gen)
            else:
                pass # reuse the same filename
            break


