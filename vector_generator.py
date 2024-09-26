import numpy as np


def test_generator(file_path, mode):
    with open(file_path, "r") as file:
        lines = file.readlines()
    input_names = []
    for line in lines:
        line = line.strip()
        if line.startswith("INPUT"):
            input_num = line.split("(")[1].split(")")[0]
            input_names.append(input_num)
    if mode == "tvs":
        probs = [0.45, 0.45, 0.05, 0.05]
    else:
        probs = [0.5, 0.5, 0, 0]
    test_vector = np.random.choice(['0', '1', 'U', 'Z'], size=len(input_names), p=probs)
    inp_string = ' '.join(input_names)
    out_string = ' '.join(test_vector)
    file_content = f"{inp_string}\n{out_string}"
    return file_content


bench_filepath = "bench_files/c1908.bench"
mode = "dfs"
file_content = test_generator(bench_filepath, mode)
print(file_content)
