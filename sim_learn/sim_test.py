
import glob
import os

from learn_automata import SimulatorLearner
from dfa_runner import DFARunner

class LearningSimulationTest:
    """
    Class to test the learner and simulator
    """
    def __init__(self, training_dir=None):
        self.learner = SimulatorLearner()
        # Default to one_host_setup training traces
        if training_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            training_dir = os.path.join(script_dir, "../evaluation/one_host_setup/training_traces")
        self.output_files = sorted(glob.glob(os.path.join(training_dir, "output_*.txt")))        

    def batch_test(self):
        # Process cumulative batches: first 100, then 200, then 300, etc.
        batch_size = 100
        total_files = len(self.output_files)
        
        for i in range(batch_size, total_files + batch_size, batch_size):
            cumulative_batch = self.output_files[:min(i, total_files)]
            print(f"Processing cumulative batch: first {len(cumulative_batch)} files")
            self.learner.learn_logs(cumulative_batch)


    """
    First learns an automaton from the log files in the logs directory
    Then it tests it against a special log file "test.txt"
    """
    def simple_test(self):


        # Pass them to the learner
        self.learner.learn_logs(self.output_files)

        dfa_sim = self.learner.get_dfa_sim()

        # dfa_vis = self.learner.get_dfa_vis()

        self.learner.visualize(dfa_sim)        
        
        # self.learner.visualize(dfa_vis)

        # Try running DFA
        # self.runner = DFARunner(dfa_sim)

        # result = self.runner.process_log("sim-learn/logs/test.txt")

        # print(result)


    def main(self):
        self.simple_test()
        # self.batch_test()
        
    
if __name__ == "__main__":
    learner = LearningSimulationTest()
    learner.main()
