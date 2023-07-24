def calculate_storage_usage(account):
    storage_limit_in_bytes = account.storage_limit * 1024 ** 3 \
        if account.storage_limit else 0
    storage_used_in_bytes = account.storage_usage

    used_percentage = (storage_used_in_bytes / storage_limit_in_bytes) * 100 \
        if storage_limit_in_bytes != 0 else 0
    available_percentage = 100 - used_percentage

    return storage_used_in_bytes, storage_limit_in_bytes, \
           round(used_percentage, 2), round(available_percentage, 2)


