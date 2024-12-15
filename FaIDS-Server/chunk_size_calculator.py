def get_optimal_chunk_size(file_size):
    if file_size < 1 * 1024 * 1024:  # Less than 1MB
        return 16 * 1024  # 16KB for very small files
    elif file_size < 10 * 1024 * 1024:  # Less than 10MB
        return 64 * 1024  # 64KB for small files
    elif file_size < 100 * 1024 * 1024:  # Less than 100MB
        return 128 * 1024  # 128KB for medium files
    elif file_size < 1 * 1024 * 1024 * 1024:  # Less than 1GB
        return 512 * 1024  # 512KB for larger files
    elif file_size < 10 * 1024 * 1024 * 1024:  # Less than 10GB
        return 1 * 1024 * 1024  # 1MB for very large files
    elif file_size < 50 * 1024 * 1024 * 1024:  # Less than 50GB
        return 4 * 1024 * 1024  # 4MB for extremely large files
    else:  # 50GB or larger
        return 8 * 1024 * 1024  # 8MB for massive files