def calculate_storage_usage(account):
    # Calculate storage limit based on subscription plan
    if account.storage_limit is not None:
        storage_limit = account.storage_limit * 1024 ** 3
    else:
        storage_limit = 0
    # Determine the unit for storage limit and usage (GB or MB)
    if storage_limit >= 1073741824:
        storage_limit = round(storage_limit / 1073741824, 2)
        storage_limit_unit = "GB"
    else:
        storage_limit = round(storage_limit / 1048576, 2)
        storage_limit_unit = "MB"

    if account.storage_usage >= 1073741824:
        storage_used = round(account.storage_usage / 1073741824, 2)
        storage_used_unit = "GB"
    else:
        storage_used = round(account.storage_usage / 1048576, 2)
        storage_used_unit = "MB"

    # Return the calculated values
    return storage_used, storage_limit, storage_limit_unit, storage_used_unit
