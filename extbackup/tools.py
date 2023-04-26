import hashlib
import zipfile
from .key import key
from cryptography.fernet import Fernet
from io import BytesIO
from storages.backends.ftp import FTPStorage


# def encrypt_files(files):
#     zip_file = BytesIO()
#     with zipfile.ZipFile(zip_file, mode='w') as zf:
#         for file in files:
#             if file.content_type == "application/x-zip-compressed":
#                 folder_file = BytesIO(file.read())
#                 with zipfile.ZipFile(folder_file) as folder_zip:
#                     for inner_file in folder_zip.infolist():
#                         inner_file_data = folder_zip.read(inner_file)
#                         encrypted = fernet_encrypt(inner_file_data)
#                         zf.writestr(inner_file.filename + '_encrypted',
#                                     encrypted,
#                                     compress_type=zipfile.ZIP_DEFLATED)
#             else:
#                 original = file.read()
#                 encrypted = fernet_encrypt(original)
#                 zf.writestr(file.name + '_encrypted', encrypted,
#                             compress_type=zipfile.ZIP_DEFLATED)
#     zip_file.seek(0)
#     return zip_file


def fernet_encrypt(data):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)
    return encrypted


def calculate_file_hash(file):
    # Calculate SHA-256 hash of the file
    hash = hashlib.sha256()
    while chunk := file.read(65536):
        hash.update(chunk)
    file_hash = hash.hexdigest()
    # print(f"File hash: {file_hash}")
    return file_hash


def extract_file_contents(files):
    file_tree = {}
    for file in files:
        if file.content_type == "application/x-zip-compressed":
            zip_file_hash = calculate_file_hash(file)
            file_tree[file.name.replace('_encrypted', '')] = {
                'hash': zip_file_hash,
                'content': {}
            }
            with zipfile.ZipFile(file) as zf:
                for info in zf.infolist():
                    path = info.filename
                    parts = path.split('/')
                    parent = file_tree[file.name.replace('_encrypted', '')]['content']

                    for part in parts[:-1]:
                        if part not in parent:
                            parent[part] = {}
                        parent = parent[part]

                    if parts[-1] == '':
                        continue

                    parent[parts[-1].replace("_encrypted", "")] = None
        else:
            file_hash = calculate_file_hash(file)
            path = file.name
            parts = path.split('/')
            parent = file_tree
            for part in parts[:-1]:
                if part not in parent:
                    parent[part] = {}
                parent = parent[part]
            if parts[-1] == '':
                continue
            parent[parts[-1]] = {
                'hash': file_hash,
            }
            file.seek(0)  # reset file pointer to start of file

    return file_tree


def calculate_storage_remaining(total_size, user_account, storage_limit):
    if user_account.subscription_plan is not None:
        storage_limit_gb = storage_limit * 1024 ** 3
    else:
        storage_limit_gb = 0
    size_conversion = total_size
    remaining_storage = storage_limit_gb - (
                user_account.storage_usage + size_conversion)
    return remaining_storage


# def decrypt_zip_file(file_data):
#     fernet = Fernet(key)
#     zip_file = BytesIO(file_data)
#     with zipfile.ZipFile(zip_file, mode='r') as zf:
#         new_zip_file = BytesIO()
#         with zipfile.ZipFile(new_zip_file, mode='w') as new_zf:
#             for file in zf.infolist():
#                 original = zf.read(file)
#                 decrypted = fernet.decrypt(original)
#                 new_zf.writestr(file.filename, decrypted,
#                                 compress_type=zipfile.ZIP_DEFLATED)
#     new_zip_file.seek(0)
#     return new_zip_file
