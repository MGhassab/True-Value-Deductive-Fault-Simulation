import copy
import re


def process_input_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    # Assuming the file has exactly two lines
    keys = lines[0].strip().split()
    values = lines[1].strip().split()
    result_dict = {key: value for key, value in zip(keys, values)}
    return result_dict


def process_circuit_file(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # First pass: Identify fanouts
    fanout_counts = {}
    for line in lines:
        if "=" in line:
            inputs = line.split("=")[1].split("(")[1].split(")")[0].split(", ")
            for inp in inputs:
                if inp.isdigit():  # Checking if the input is a digit to avoid operation names
                    fanout_counts[inp] = fanout_counts.get(inp, 0) + 1

    # Create fanout lists for inputs used multiple times
    fanouts = {inp: [f"{inp}_{i + 1}" for i in range(count)] for inp, count in fanout_counts.items() if count > 1}
    fanouts_copy = copy.deepcopy(fanouts)

    # Second pass: Create circuit components
    circuit = []
    inputs = []
    outputs = []

    for line in lines:
        line = line.strip()
        if line.startswith("INPUT"):
            input_num = line.split("(")[1].split(")")[0]
            inputs.append(input_num)
        elif line.startswith("OUTPUT"):
            output_num = line.split("(")[1].split(")")[0]
            outputs.append(output_num)
        elif "=" in line:
            parts = line.split(" = ")
            output_num = parts[0]
            operation, inputs_str = parts[1].split("(")
            inputs_nums = inputs_str[:-1].split(", ")

            # Replace inputs with fanout identifiers if needed
            converted_inputs = [fanouts[inp].pop(0) if inp in fanouts else inp for inp in inputs_nums]
            circuit.append([operation, output_num] + converted_inputs)

    # Add fanout, input, and output information
    for key, values in fanouts_copy.items():
        circuit.append(["FANOUT", key] + values)

    circuit.append(["INPUT"] + inputs)
    circuit.append(["OUTPUT"] + outputs)

    return circuit


def split_circuit(circuit_data):
    input_list = []
    gate_list = []
    fanout_list = []
    output_list = []
    for e in circuit_data:
        if e[0] == "INPUT":
            input_list.extend(e[1:])
        elif e[0] == "FANOUT":
            fanout_list.append(e)
        elif e[0] == "OUTPUT":
            output_list.extend(e[1:])
        else:
            gate_list.append(e)
    return input_list, gate_list, fanout_list, output_list


def create_wires(circuit_data):
    wires = []
    for e in circuit_data:
        for j in range(1, len(e)):
            wires.append(e[j])
    wires = list(set(wires))
    return wires


def create_simulation_list(wires):
    simulation_wires = []
    simulation_value = []
    for wire in wires:
        simulation_wires.append("w" + wire)
        simulation_value.append("U")
    simulation_dict = {key: value for key, value in zip(simulation_wires, simulation_value)}
    return simulation_dict


def create_input_wires(input_list):
    input_wires = []
    for input_wire in input_list:
        input_wires.append("w" + input_wire)
    return input_wires


def create_gates_output_wires(gate_list):
    gates_output_wires = []
    for gate in gate_list:
        gates_output_wires.append(gate[1])
    gates_output_wires.sort(key=int)
    return gates_output_wires


def find_gate(gate_out_wire, gate_list):
    for gate in gate_list:
        if (gate[1]) == gate_out_wire:
            return gate[0]


def find_gate_inputs(gate_out_wire, gate_list):
    gate_inputs = []
    for gate in gate_list:
        if (gate[1]) == gate_out_wire:
            gate_inputs.extend(gate[2:])
    return gate_inputs


def is_fanin(wire_name, fanout_list):
    for fanout in fanout_list:
        if fanout[1] == wire_name:
            return True
    return False


def find_fanout_lines(fanin_wire, fanout_list):
    for fanout in fanout_list:
        if fanout[1] == fanin_wire:
            return fanout[2:]
    return None


def give_input_vector(simulation_dict, input_wires, input_vector):
    simulation_dict_copy = copy.deepcopy(simulation_dict)
    if len(input_wires) == len(input_vector):
        for (key, value) in input_vector.items():
            simulation_dict_copy["w" + key] = value
    else:
        ValueError("The lengths of input_wires and input_vector must be equal")
    return simulation_dict_copy


def make_fanout_equivalence(simulation_dict, fanout_list):
    simulation_dict_copy = copy.deepcopy(simulation_dict)
    for fanout in fanout_list:
        f_in = fanout[1]
        f_outs = fanout[2:]
        for f_out in f_outs:
            for wire_name in simulation_dict.keys():
                tem = wire_name.split("w")[1]
                if tem == f_out:
                    f_in_value = simulation_dict_copy["w" + str(f_in)]
                    simulation_dict_copy[wire_name] = f_in_value
    return simulation_dict_copy


def gate_simulator(gate_type, gate_inputs):
    if gate_type == "AND":
        if '0' in gate_inputs:
            return '0'
        if 'U' in gate_inputs or 'Z' in gate_inputs:
            return 'U'
        return '1'

    elif gate_type == "OR":
        if '1' in gate_inputs:
            return '1'
        if 'U' in gate_inputs or 'Z' in gate_inputs:
            return 'U'
        return '0'

    elif gate_type == "NAND":
        if '0' in gate_inputs:
            return '1'
        if 'U' in gate_inputs or 'Z' in gate_inputs:
            return 'U'
        return '0'

    elif gate_type == "NOR":
        if '1' in gate_inputs:
            return '0'
        if 'U' in gate_inputs or 'Z' in gate_inputs:
            return 'U'
        return '1'

    elif gate_type == "NOT":
        if len(gate_inputs) != 1:
            raise ValueError("NOT gate must have exactly one input")
        if gate_inputs[0] == '1':
            return '0'
        if gate_inputs[0] == '0':
            return '1'
        return 'U'

    elif gate_type == "BUFF":
        if len(gate_inputs) != 1:
            raise ValueError("BUFF gate must have exactly one input")
        if gate_inputs[0] == '1':
            return '1'
        if gate_inputs[0] == '0':
            return '0'
        return 'U'

    converted_inputs = []
    for inp in gate_inputs:
        if inp in ['0', '1']:
            converted_inputs.append(int(inp))
        else:
            converted_inputs.append(inp)

    if 'U' in gate_inputs or 'Z' in gate_inputs:
        return 'U'

    elif gate_type == "XOR":
        return '1' if sum(converted_inputs) % 2 == 1 else '0'

    elif gate_type == "XNOR":
        return '1' if sum(converted_inputs) % 2 == 0 else '0'

    else:
        raise ValueError("Invalid gate type.")


def true_value_simulation(input_vector, simulation_dict, fanout_list, gate_list, input_wires, gates_output_wires):
    simulation_dict_copy = copy.deepcopy(simulation_dict)
    simulation_dict_copy = give_input_vector(simulation_dict_copy, input_wires, input_vector)
    simulation_dict_copy = make_fanout_equivalence(simulation_dict_copy, fanout_list)
    for gate_out_wire in gates_output_wires:
        gate_type = find_gate(gate_out_wire, gate_list)
        gate_inputs = find_gate_inputs(gate_out_wire, gate_list)
        value_gate_inputs = []
        for gate_input in gate_inputs:
            value_gate_inputs.append(simulation_dict_copy['w' + gate_input])
        gate_out_value = gate_simulator(gate_type, value_gate_inputs)
        simulation_dict_copy["w" + gate_out_wire] = gate_out_value
        simulation_dict_copy = make_fanout_equivalence(simulation_dict_copy, fanout_list)
    return simulation_dict_copy


def custom_sort_tvs(key):
    match = re.match(r"([a-z]+)([0-9]+)_?([0-9]*)", key, re.I)
    if match:
        items = match.groups()
        return [items[0], int(items[1])] + [int(items[2])] if items[2] else [items[0], int(items[1]), 0]


def custom_sort_wrapper(my_dict, sorter):
    sorted_keys = sorted(my_dict.keys(), key=sorter)
    sorted_dict = {key: my_dict[key] for key in sorted_keys}
    return sorted_dict


def write_to_file(src_dict, out_path):
    with open(out_path, 'w') as f:
        for key, value in src_dict.items():
            f.write('%s: %s\n' % (key, value))
