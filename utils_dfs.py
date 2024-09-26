from utils_tvs import *
from collections import Counter


def init_fault_list(wires, tvs):
    La = []
    La_val = []
    for wire in wires:
        wire_true_value = tvs['w' + wire]
        if wire_true_value == "1":
            wire_fault_value = "_s0"
        elif wire_true_value == "0":
            wire_fault_value = "_s1"
        else:
            raise ValueError("Only binary values")

        La.append('L_w' + wire)
        La_val.append({'w' + wire + wire_fault_value})
    La_dict = {key: value for key, value in zip(La, La_val)}
    return La_dict


def update_fault_list_for_fanout(La_dict, wire, fanout_list):
    La_copy = copy.deepcopy(La_dict)
    if is_fanin(wire, fanout_list):
        fanout_lines = find_fanout_lines(wire, fanout_list)
        for fanout_line in fanout_lines:
            La_copy['L_w' + fanout_line] = La_copy['L_w' + fanout_line].union(La_copy['L_w' + wire])
    return La_copy


def gate_dfs(gate, inputs):
    # if 0: return La
    # if 1: return complement of La
    # Last element 1: Union
    # Last element 0: Intersection
    if not all(inp in ['0', '1'] for inp in inputs):
        raise ValueError("Invalid input values. All inputs must be 0 or 1")

    if gate in ['AND', 'NAND']:
        if '0' in inputs:
            return [str(int(inp == '1')) for inp in inputs] + ['0']
        return ['0'] * len(inputs) + ['1']

    elif gate in ['OR', 'NOR']:
        if '1' in inputs:
            return [str(int(inp != '1')) for inp in inputs] + ['0']
        return ['0'] * len(inputs) + ['1']

    elif gate in ['BUFF', 'NOT']:
        if len(inputs) != 1:
            raise ValueError(f"{gate} gate must have exactly one input")
        return ['0']  # Just on set, intersection/union does not matter => ['0', 'X']

    else:
        raise ValueError("Invalid gate type")


def create_union_set(wires):
    U = []
    for wire in wires:
        U.append('w' + wire + '_s0')
        U.append('w' + wire + '_s1')
    return set(U)


def deductive_fault_simulation(La_dict, input_list, fanout_list, gates_output_wires, gate_list, tvs, U_set):
    La_dict_copy = copy.deepcopy(La_dict)

    for input_wire in input_list:
        La_dict_copy = update_fault_list_for_fanout(La_dict_copy, input_wire, fanout_list)

    for gate_out_wire in gates_output_wires:
        gate_type = find_gate(gate_out_wire, gate_list)
        gate_inputs = find_gate_inputs(gate_out_wire, gate_list)

        if gate_type in ['XOR', 'XNOR']:
            result_set = set()
            fault_counter = Counter()
            for gate_input in gate_inputs:
                input_fault_set = La_dict_copy['L_w' + gate_input]
                fault_counter.update(input_fault_set)
            for key, value in fault_counter.items():
                if value % 2 == 1:
                    result_set.add(key)

        else:
            value_gate_inputs = []
            for gate_input in gate_inputs:
                value_gate_inputs.append(tvs['w' + gate_input])

            rules_list = gate_dfs(gate_type, value_gate_inputs)

            input_sets = []
            for idx, gate_input in enumerate(gate_inputs):
                if rules_list[idx] == '0':
                    input_set = La_dict_copy['L_w' + gate_input]  # Fault List of Input Wire
                else:
                    input_set = U_set - La_dict_copy['L_w' + gate_input]  # Complement of Fault List of Input Wire
                input_sets.append(input_set)

            # Perform intersection or union based on the last element in rules_list
            if rules_list[-1] == '1':
                result_set = set.union(*input_sets)
            else:
                result_set = set.intersection(*input_sets)

        # Constructing the key for La_dict_copy
        gate_out_wire_key = 'L_w' + gate_out_wire

        La_dict_copy[gate_out_wire_key] = La_dict_copy[gate_out_wire_key].union(result_set)

        La_dict_copy = update_fault_list_for_fanout(La_dict_copy, gate_out_wire, fanout_list)

    return La_dict_copy


def dfs_report(dfs, output_list):
    all_faults = set()
    for output_wire in output_list:
        faults = dfs['L_w' + output_wire]
        all_faults = all_faults.union(faults)

    n_total_faults = len(dfs) * 2
    dfs_coverage = len(all_faults) / n_total_faults

    print(f"Number of detected faults: {len(all_faults)}")
    print(f"Total number of faults: {n_total_faults}")
    print(f"Fault Coverage: {dfs_coverage}")


def custom_sort_dfs(key):
    match = re.match(r"([a-zA-Z_]+)(\d+)", key)
    if match:
        text = match.group(1)
        number = int(match.group(2))
        return text, number
    return key,


def tvs_dfs_wrapper(bench_filepath, test_filepath, mode):
    input_vector = process_input_file(test_filepath)
    circuit_data = process_circuit_file(bench_filepath)
    input_list, gate_list, fanout_list, output_list = split_circuit(circuit_data)
    wires = create_wires(circuit_data)
    simulation_dict = create_simulation_list(wires)
    input_wires = create_input_wires(input_list)
    gates_output_wires = create_gates_output_wires(gate_list)

    tvs = true_value_simulation(
        input_vector,
        simulation_dict,
        fanout_list,
        gate_list,
        input_wires,
        gates_output_wires
    )

    if mode == "dfs":
        La_dict = init_fault_list(wires, tvs)
        U_set = create_union_set(wires)
        dfs = deductive_fault_simulation(
            La_dict,
            input_list,
            fanout_list,
            gates_output_wires,
            gate_list,
            tvs,
            U_set
        )
        dfs_report(dfs, output_list)
        return custom_sort_wrapper(dfs, custom_sort_dfs)
    return custom_sort_wrapper(tvs, custom_sort_tvs)
