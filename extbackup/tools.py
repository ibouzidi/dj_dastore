import zipfile
from .key import key
from cryptography.fernet import Fernet
from io import BytesIO
from storages.backends.ftp import FTPStorage


def encrypt_files(files):
    zip_file = BytesIO()
    with zipfile.ZipFile(zip_file, mode='w') as zf:
        for file in files:
            if file.content_type == "application/x-zip-compressed":
                folder_file = BytesIO(file.read())
                with zipfile.ZipFile(folder_file) as folder_zip:
                    for inner_file in folder_zip.infolist():
                        inner_file_data = folder_zip.read(inner_file)
                        encrypted = fernet_encrypt(inner_file_data)
                        zf.writestr(inner_file.filename + '_encrypted',
                                    encrypted,
                                    compress_type=zipfile.ZIP_DEFLATED)
            else:
                original = file.read()
                encrypted = fernet_encrypt(original)
                zf.writestr(file.name + '_encrypted', encrypted,
                            compress_type=zipfile.ZIP_DEFLATED)
    zip_file.seek(0)
    return zip_file


def fernet_encrypt(data):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)
    return encrypted


def extract_zip_contents(zip_file_path):
    file_tree = {}
    with zipfile.ZipFile(zip_file_path) as zip_file:
        for inner_file in zip_file.infolist():
            path = inner_file.filename
            parts = path.split('/')
            parent = file_tree
            for part in parts[:-1]:
                if part not in parent:
                    parent[part.replace("_encrypted", "")] = {}
                parent = parent[part.replace("_encrypted", "")]
            if parts[-1] == '':
                continue
            parent[parts[-1].replace("_encrypted", "")] = None
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


def decrypt_zip_file(file_data):
    fernet = Fernet(key)
    zip_file = BytesIO(file_data)
    with zipfile.ZipFile(zip_file, mode='r') as zf:
        new_zip_file = BytesIO()
        with zipfile.ZipFile(new_zip_file, mode='w') as new_zf:
            for file in zf.infolist():
                original = zf.read(file)
                decrypted = fernet.decrypt(original)
                new_zf.writestr(file.filename, decrypted,
                                compress_type=zipfile.ZIP_DEFLATED)
    new_zip_file.seek(0)
    return new_zip_file
