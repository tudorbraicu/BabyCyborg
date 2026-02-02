from aalpy.automata import Dfa, DfaState
from learn_automata import SimulatorLearner


class DFARunner:
    

    """Initialize with an AALpy DFA"""
    def __init__(self, dfa: Dfa):
        if dfa is None:
            raise ValueError("DFA cannot be None")
        if not isinstance(dfa, Dfa):
            raise ValueError(f"Expected Dfa object, got {type(dfa).__name__}")
        if not hasattr(dfa, 'initial_state') or dfa.initial_state is None:
            raise ValueError("Invalid DFA: missing initial state")
        if not hasattr(dfa, 'states') or not dfa.states:
            raise ValueError("Invalid DFA: no states defined")
        
        self.simLearner = SimulatorLearner()            
        self.dfa = dfa

    def pretty_print_dfa(self,dfa):
        print(f"Initial State: {dfa.initial_state.state_id}")
        print("States:")
        for state in dfa.states:
            print(f"{state.state_id} (accepting: {state.is_accepting})")
            for symbol, target in state.transitions.items():
                print(f"  {symbol} -> {target.state_id}")
        print()

    def process_input(self, input_sequence):
        """Simulate the DFA on an input sequence."""
        current_state = self.dfa.initial_state
        for symbol in input_sequence:
            # print(symbol)
            # print(current_state.state_id)
            if symbol in current_state.transitions:
                current_state = current_state.transitions[symbol]
            else:
                print("I do not have the symbol")
                return False
        return True if current_state.is_accepting else False
    
    def process_log(self, log_file):
        data = self.simLearner.parse_raw_log_file(log_file)
        traces = self.simLearner.convert_to_combined_traces(data)

        success = True

        for item in traces:
            path_tuple, expected_result = item
            answer = self.process_input(path_tuple)
            if answer != expected_result:
                return (False, path_tuple)  # Return failure with the failing path
        
        return (success, None)  # Return success with no failing path
            
            

        
    

