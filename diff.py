def normalize(filename: str) -> str:
    name = filename.lower().strip()
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name


def find_new_files(delivery_filenames, postprocessed_files):
    delivery_set = {normalize(name) for name in delivery_filenames}

    return [
        (filename, data)
        for filename, data in postprocessed_files.items()
        if normalize(filename) not in delivery_set
    ]
