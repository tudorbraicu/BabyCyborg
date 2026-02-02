
import ast
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from aalpy.learning_algs import run_RPNI
from aalpy.automata import Dfa, DfaState
from aalpy.utils import visualize_automaton
from aalpy.utils import save_automaton_to_file
from graphviz import Source
from graphviz import Digraph
import os.path



class SimulatorLearner:

    def __init__(self):
        # Persistent simplification mappings
        self.field_maps = {
            'action': {'prefix': 'a', 'counter': 1, 'mapping': {}},
            'hostname': {'prefix': 'h', 'counter': 1, 'mapping': {}},
            'ip_address': {'prefix': 'i', 'counter': 1, 'mapping': {}},
            'subnetname': {'prefix': 's', 'counter': 1, 'mapping': {}},
            'exploit_port': {'prefix': 'p', 'counter': 1, 'mapping': {}},
            'prefix_length': {'prefix': 'l', 'counter': 1, 'mapping': {}},
            'exploit_class': {'prefix': 'e', 'counter': 1, 'mapping': {}}
        }
        
        # Processed data storage        
        self.structured_data = None
        self.simplified_data = None
        self.traces = []

        # Learned DFA
        self.learned_dfa: Dfa = None

    
    def remap_dfa_inputs(self, input_map: dict) -> Dfa:
        if self.learned_dfa is None:
            raise ValueError("DFA not initialized")

        # Create new states (retaining the same structure)
        new_states = {}
        for state in self.learned_dfa.states:
            new_states[state.state_id] = DfaState(state.state_id, state.is_accepting)

        # Remap transitions
        for state in self.learned_dfa.states:
            for old_input, transition in state.transitions.items():
                # Apply the input mapping
                new_input = input_map.get(old_input, old_input)  # Default to old_input if not in map
                new_states[state.state_id].transitions[new_input] = new_states[transition.state_id]

        # The initial state remains the same
        new_initial_state = new_states[self.learned_dfa.initial_state.state_id]
        return Dfa(new_initial_state, list(new_states.values()))

    """Returns the learned DFA instance for visualization if it exists."""
    def get_dfa_vis(self):
        if self.learned_dfa is None:
            raise ValueError("DFA not initialized")
        return self.learned_dfa
    
    """Returns the learned DFA instance for simulation if it exists."""
    def get_dfa_sim(self):
        if self.learned_dfa is None:
            raise ValueError("DFA not initialized")
        
        reverse_mapping = {}

        for field_name, field_info in self.field_maps.items():  # Now field_name is properly defined
            # Skip 'ip_address' field
            if field_name == 'ip_address':
                continue
        
            # Add mappings from other fields
            for key, value in field_info['mapping'].items():
                reverse_mapping[value] = key              # 'p1': '21', 'p2': '80'
    
        self.remap_dfa = self.remap_dfa_inputs(reverse_mapping)
       
        return self.remap_dfa

    """
    Internal method to manage simplified value mappings
    """
    def get_simplified_value(self, field, original_value):
        if original_value not in self.field_maps[field]['mapping']:
            self.field_maps[field]['mapping'][original_value] = \
                f"{self.field_maps[field]['prefix']}{self.field_maps[field]['counter']}"
            self.field_maps[field]['counter'] += 1
        return self.field_maps[field]['mapping'][original_value]

    """
    Parse a raw cyber battle log file into structured nested dictionaries.

    Reads a text file containing Python-formatted logs of Blue/Red agent actions,
    then organizes them into a hierarchical structure:
        {episode: {step: {'Blue': [actions], 'Red': [actions]}}}
    """

    def parse_raw_log_file(self,file_path):

        structured_data = defaultdict(lambda: defaultdict(lambda: {"Blue": [], "Red": []}))

        
        try:
            with open(file_path, 'r') as file:
                # Read the entire file content
                content = file.read().strip()
                
                # The file appears to contain a list of lists - ensure proper format
                if not (content.startswith('[') and content.endswith(']')):
                    raise ValueError("File content is not properly enclosed in list brackets")
                
                # Parse using ast.literal_eval
                raw_data = ast.literal_eval(content)
        
                for step_actions in raw_data:
                    if not isinstance(step_actions, list):
                        continue
                    
                    for action in step_actions:

                        try:
                            blue_action = action[0]  # First dict is Blue
                            red_action = action[1]   # Second dict is Red

                            # Validate agents
                            if blue_action['agent'] != 'Blue' or red_action['agent'] != 'Red':
                                print(f"Unexpected agent order in step: {step_actions}")
                                continue
                            
                            episode = blue_action['episode']  # Same for both
                            step = blue_action['step']        # Same for both

                            # Store Blue action
                            structured_data[episode][step]['Blue'].append(
                                {k:v for k,v in blue_action.items() 
                                if k not in ['episode','step','agent']}
                            )

                            # Store Red action
                            structured_data[episode][step]['Red'].append(
                                {k:v for k,v in red_action.items() 
                                if k not in ['episode','step','agent']}
                            )
                        except (KeyError, TypeError) as e:
                            print(f"Skipping malformed action: {action}. Error: {e}")
                            continue
                            
        except Exception as e:
            print(f"Error processing file: {e}")
            return None
        
        # Access all Blue actions in Episode 1, Step 1
        # print(structured_data[1][1]['Blue'])
        # print(structured_data[1][1]['Blue'][0]['ip_address'])

        return structured_data

    """
    Pretty printing the stuctured data
    """

    def print_structured_data(self, indent=0):
        for episode_num, episode_data in sorted(self.structured_data.items()):
            print(f"{'  ' * indent}Episode {episode_num}:")
            for step_num, step_data in sorted(episode_data.items()):
                print(f"{'  ' * (indent + 1)}Step {step_num}:")
                for agent in ['Blue', 'Red']:
                    if step_data[agent]:  # Only print if actions exist
                        print(f"{'  ' * (indent + 2)}{agent} Actions:")
                        for action in step_data[agent]:
                            print(f"{'  ' * (indent + 3)}{action}")

    """
    Transforms verbose log data into compact, normalized form by replacing:
    - Action names (e.g., 'DecoyApache' → 'a1')
    - Hostnames (e.g., 'Subnet_1_Host_2' → 'h1') 
    - IPs (e.g., '10.0.154.252' → 'i1')
    - Ports (e.g., 3306 → 'p1')
    """

    def simplify_structured_data(self):

        if self.structured_data is None:
            raise ValueError("No structured data available. Call parse_raw_log_file() first.")        

        # Initialize fresh simplified storage
        
        self.simplified_data = defaultdict(lambda: defaultdict(lambda: {'Blue': [], 'Red': []}))

        # Process all episodes, steps, and agents
        for episode_num, episode_data in self.structured_data.items():
                for step_num, step_data in episode_data.items():
                    for agent in ['Blue', 'Red']:
                        for action in step_data[agent]:
                            # Create simplified action copy
                            simplified_action = {}
                            for field in action:
                                if field == 'success':
                                    simplified_action[field] = action[field]
                                else:
                                    simplified_action[field] = self.get_simplified_value(field, action[field])
                            
                            # Store in simplified_data
                            self.simplified_data[episode_num][step_num][agent].append(simplified_action)


    """
    Makes independent automata traces from simplified_data structure
    Returns:
    list: A list of tuples where each tuple contains:
         A trace tuple with format: 
            (episode_num, step_num, team, [action_fields...])
        - A boolean indicating whether the action was successful
    """
    def convert_to_traces(self, data = None):
        
        data_to_use = data or self.simplified_data

        traces = []
        
        for episode_num, episode_data in data_to_use.items():
            for step_num, step_data in sorted(episode_data.items()):
                # Process Blue actions
                for action in step_data['Blue']:
                    # Required fields
                    trace = [f'ep{episode_num}', f'step{step_num}', 'Blue']
                    
                    # Optional fields
                    for field in ['action', 'ip_address', 'exploit_port', 'hostname', 'subnetname', 'prefix_length']:
                        if field in action:
                            trace.append(action[field])
                    
                    # Add to traces
                    traces.append((tuple(trace), action.get('success', 'FALSE') == 'TRUE'))
                
                # Process Red actions
                for action in step_data['Red']:
                    # Required fields
                    trace = [f'ep{episode_num}', f'step{step_num}', 'Red']
                    
                    # Optional fields
                    for field in ['action', 'hostname', 'ip_address', 'exploit_port', 'subnetname', 'prefix_length']:
                        if field in action:
                            trace.append(action[field])
                    
                    # Add to traces
                    traces.append((tuple(trace), action.get('success', 'FALSE') == 'TRUE'))
        
        return traces    

    """
    Generate progressively combined traces across all episodes and steps.
    
    Transforms simplified battle data into cumulative traces where each subsequent trace
    contains all previous actions. Maintains cross-episode continuity by chaining traces
    from one episode to the next.
    """
    def convert_to_combined_traces(self, data=None, include_fields=['action', 'hostname', 'exploit_class', 'exploit_port', 'subnetname']):

        episode_sequences = {}
        cumulative_trace = []
        result = []
        
        # Check if data is provided, otherwise fall back to self.simplified_data
        if data is not None:
            working_data = data
        elif self.simplified_data is not None:
            working_data = self.simplified_data
        else:
            raise ValueError("No data provided and self.simplified_data is None")

        for episode_num, episode_data in sorted(working_data.items()):
            episode_key = f'ep{episode_num}'
            episode_sequences[episode_key] = []
            
            for step_num, step_data in sorted(episode_data.items()):
                # Process Blue actions
                for action in step_data['Blue']:
                    trace = []
                    for field in include_fields:
                        if field in action:
                            trace.append(action[field])
                    success = action.get('success', 'FALSE') == 'TRUE'
                    episode_sequences[episode_key].append((tuple(trace), success))
                
                # Process Red actions
                for action in step_data['Red']:
                    trace = []
                    for field in include_fields:
                        if field in action:
                            trace.append(action[field])
                    success = action.get('success', 'FALSE') == 'TRUE'
                    episode_sequences[episode_key].append((tuple(trace), success))
            
            # Build continuous traces
            for trace, success in episode_sequences[episode_key]:
                cumulative_trace.extend(trace)
                result.append((tuple(cumulative_trace), success))

        return result
    
    """
     Visualize the DFA
     This may take a lot of time for huge models
    """ 
    def visualize(self, dfa):

        save_automaton_to_file(dfa, path='learned_dfa.dot')

        # Create a new Digraph and read the DOT file

        g = Digraph()
        with open('learned_dfa.dot') as f:
            g.body = f.readlines()[1:-1]  # Skip the first and last lines (graph declaration)

            # Set graph attributes for compact vertical layout
            g.attr(rankdir='TB',         # Top-to-bottom layout
                   nodesep='0.3',
                   ranksep='1.0',
                concentrate='true')  

            # Render and view
            g.render('automaton', format='png', view=True, engine='dot')


    def learn_logs(self,log_files):

        if not log_files:
            raise ValueError("Log file array cannot be empty")    

        # Process each file sequentially
        for log_file in log_files:
            if not os.path.isfile(log_file):
                print(f"Error: File does not exist - {log_file}")
                continue
            try:
                self.structured_data = self.parse_raw_log_file(log_file)
            except IOError as e:
                raise ValueError(f"Error reading file {log_file}: {e}")
            except Exception as e:
                raise ValueError(f"Unexpected error processing file {log_file}: {e}")

            # Skip if parsing failed
            if self.structured_data is None:
                continue

            #self.print_structured_data()
            self.simplify_structured_data()        
            #indiv_traces = self.convert_to_traces()
            #print(indiv_traces )
            combined_traces = self.convert_to_combined_traces()
            #print(combined_traces)
            self.traces += combined_traces

        #print(self.field_maps)
        #print(self.traces)
        # Run RPNI with correct argument passing
        dfa = self.learned_dfa = run_RPNI(
            self.traces,
            automaton_type='dfa',
            input_completeness='sink_state'  # forces completeness
        )


        

