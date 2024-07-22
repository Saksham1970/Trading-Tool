import json, os


def load_json(file_path):
    if not os.path.exists(file_path):
        f = open(file_path, "w")
        f.write(json.dumps({}))
        f.close()
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
