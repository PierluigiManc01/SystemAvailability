from itertools import product
import streamlit as st
import pandas as pd

def calculate_combination_probability(machines_per_station, availabilities, combination):
    probability = 1.0
    for station_idx, machines in enumerate(machines_per_station):
        for machine_idx in range(machines):
            if combination[station_idx][machine_idx]:
                probability *= availabilities[station_idx]
            else:
                probability *= (1 - availabilities[station_idx])
    return probability

def generate_combinations(machines_per_station, availabilities, cycle_times, station_index, current_combination, case_counts, total_valid_cases):
    if station_index == len(machines_per_station):
        # Verifica se la combinazione è valida (ogni stazione ha almeno una macchina funzionante)
        failed_stations = []
        cycles = []
        is_valid = True
        for station_idx, machines in enumerate(current_combination):
            failures = machines.count(False)
            cycle_time = cycle_times[station_idx]
            cycle_time = cycle_time / (len(machines) - failures) if failures < len(machines) else 0
            if all(not status for status in machines):
                is_valid = False
                break
            failed_stations.append(failures)
            cycles.append(cycle_time)
        if is_valid:
            denom = max(cycles) if cycles else 1
            total_valid_cases[0] += 1
            case_description = " | ".join(
                f"Station {i+1} failures: {failed_stations[i]}" for i in range(len(failed_stations))
            ) + " | "
            probability = calculate_combination_probability(machines_per_station, availabilities, current_combination)
            if case_description not in case_counts:
                case_counts[case_description] = [0, 0.0, 0]
            case_counts[case_description][0] += 1
            case_counts[case_description][1] = probability
            case_counts[case_description][2] = f"1/{denom}" 
        return

    num_machines = machines_per_station[station_index]
    # Genera tutte le combinazioni di True/False per le macchine della stazione corrente
    for mask in product([False, True], repeat=num_machines):
        current_combination[station_index] = list(mask)
        generate_combinations(machines_per_station, availabilities, cycle_times, station_index + 1, current_combination, case_counts, total_valid_cases)

def main():
    num_stations = int(input("Enter the total number of stations: "))

    machines_per_station = []
    availabilities = []
    cycle_times = []
    for i in range(num_stations):
        machines = int(input(f"\nEnter the number of machines for station {i+1}: "))
        availability = float(input(f"Enter the availability for station {i+1} (0 to 1): "))
        cycle_time = float(input(f"Enter the cycle time for station {i+1} (in seconds): "))
        machines_per_station.append(machines)
        availabilities.append(availability)
        cycle_times.append(cycle_time)

    current_combination = [[] for _ in range(num_stations)]
    case_counts = {}
    total_valid_cases = [0]  # uso lista per mutabilità in ricorsione

    generate_combinations(machines_per_station, availabilities,cycle_times, 0, current_combination, case_counts, total_valid_cases)

    print("\nResults:")
    print(f"Total valid cases: {total_valid_cases[0]}")
    print(f"Total unique valid cases: {len(case_counts)}")

    total_probability = 0.0
    for description, (occurrences, prob_sum, prod_capacity) in case_counts.items():
        print(f"{description} - Number of States: {occurrences} - Probability: {prob_sum * 100:.6f}% - Production Capacity: {prod_capacity}")
        total_probability += prob_sum*occurrences

    print(f"\nTotal probability of all valid cases: {total_probability * 100:.6f}%")


def streamlit_app():
    st.title("Machine System Reliability Calculator")
    st.write("Calculate the reliability of a multi-station system with multiple machines per station.")
    
    # Get number of stations
    num_stations = st.number_input("Enter the total number of stations:", min_value=1, value=4, step=1)
    
    # Create inputs for machines and availabilities
    machines_per_station = []
    availabilities = []
    cycle_times = []
    for i in range(int(num_stations)):
        st.markdown(f"### Station {i+1}")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            machines = st.number_input(f"Number of machines:", min_value=1, value=1, step=1, key=f"machines_{i}")
        
        with col2:
            availability = st.number_input(f"Availability (0 to 1):", min_value=0.0, max_value=1.0, value=0.98, step=0.01, key=f"avail_{i}")
        with col3:
            cycle_time = st.number_input(f"Cycle time (seconds):", min_value=1.0, value=55.0, step=1.0, key=f"cycle_{i}")

        machines_per_station.append(machines)
        availabilities.append(availability)
        cycle_times.append(cycle_time)

    import numpy as np

    tpc = (1/np.max(np.array(cycle_times) / np.array(machines_per_station)))*60*60
    
    # Calculate complexity
    total_combinations = 1
    for m in machines_per_station:
        total_combinations *= 2**m
        
    # Warning for large calculations
    if total_combinations > 1000000:
        st.warning(f"This calculation involves {total_combinations:,} combinations and may take a long time.")
        proceed = st.checkbox("I understand, proceed anyway")
    else:
        proceed = True
    
    # Calculate button
    calculate_button = st.button("Calculate Probabilities", disabled=(total_combinations > 1000000 and not proceed))
    
    if calculate_button:
        # Initialize variables
        current_combination = [[] for _ in range(num_stations)]
        case_counts = {}
        total_valid_cases = [0]
        
        # Calculate
        with st.spinner(f"Calculating {total_combinations:,} combinations..."):
            generate_combinations(machines_per_station, availabilities, cycle_times, 0, current_combination, case_counts, total_valid_cases)
        
        # Display results
        st.success("Calculation complete!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total valid cases", total_valid_cases[0])
        with col2:
            st.metric("Unique valid cases", len(case_counts))
        
        # Create results dataframe
        results = []
        total_probability = 0.0
        
        for description, (occurrences, prob_sum, prod_cap) in case_counts.items():
            results.append({
                "Case Description": description,
                "Number of States": occurrences,
                "Probability (%)": round(prob_sum * 100, 6),
                "Raw Probability": prob_sum * 100,
                "Production Capacity": prod_cap,
                "Probability": prob_sum,
                "Prod_C": float(prod_cap.split("/")[0])/ float(prod_cap.split("/")[1])
            })
            total_probability += prob_sum*occurrences
        
        st.metric("Total probability", f"{total_probability * 100:.6f}%")
        
        
        # Display table
        if results:
            st.write("### Case Details")
            df = pd.DataFrame(results)
            df_sorted = df.sort_values("Raw Probability", ascending=False)

            expected_pc = df["Prod_C"]*df["Probability"]*df["Number of States"]
            expected_pc = expected_pc.sum() *60*60
            st.dataframe(df_sorted.drop(columns=["Raw Probability", "Probability", "Prod_C"]), use_container_width=True)

            st.metric("Expected Production Capacity", expected_pc, "pc/h")
            st.metric("Theoretical Production Capacity", tpc, "pc/h")
            st.metric("Availability Line", expected_pc/tpc, "%")
        


            
if __name__ == "__main__":
    streamlit_app()