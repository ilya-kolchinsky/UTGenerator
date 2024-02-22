import re

from Similarity import Similarity

POSITIVE_SCENARIOS_REGEX = re.compile('Normal Flow(.*?)', re.DOTALL | re.IGNORECASE)
NEGATIVE_SCENARIOS_REGEX = re.compile('Abnormal Flow(.*?)', re.DOTALL | re.IGNORECASE)
SINGLE_SCENARIO_REGEX = re.compile(r'^((\d+\.)|( ?- ))(.*?)((\n(?=^\d|\n))|\Z)', re.MULTILINE | re.DOTALL)


class ScenarioAnalyzer(object):

    MAX_IMPROVEMENT_ITERATIONS = 1

    DISTANCE_THRESHOLD = 0.3

    MIN_NEW_SCENARIOS = 3

    def __init__(self, scenario_description=None):
        self.positive = []
        self.negative = []

        self.__iterations = 0
        self.__average_distance = 0.0
        self.__new_scenarios_at_last_round = 0

        if scenario_description is not None:
            self.add_scenarios(scenario_description)

    def add_scenarios(self, scenario_description):
        self.__iterations += 1

        new_positive, new_negative = self.__parse_scenario_description(scenario_description)

        if len(new_positive) == 0 and len(new_negative) == 0:
            raise ValueError(f'Unexpected reply from LLM, no scenarios found:\n{scenario_description}')

        # filter out scenarios that are too similar to the already existing ones
        new_positive, new_negative = self.__filter_scenarios(new_positive, new_negative)
        self.__new_scenarios_at_last_round = len(new_positive) + len(new_negative)
        if self.__new_scenarios_at_last_round == 0:
            # all new scenarios were filtered - our LLM cannot think of more use cases
            print("Cannot create more testing flows, proceeding to test generation.")
            return

        self.positive.extend(new_positive)
        self.negative.extend(new_negative)

        if len(new_positive) > 0 and len(new_negative) > 0:
            # we have both new positives and new negative scenarios
            print(f'Generated {len(new_positive)} normal and {len(new_negative)} abnormal flows to be tested.')
        else:  # only one of the new lists is non-empty
            print(f'Generated {len(new_positive) + len(new_negative)} flows to be tested.')

    @staticmethod
    def __parse_scenario_description(scenario_description):
        positive_starting_position = POSITIVE_SCENARIOS_REGEX.search(scenario_description)
        negative_starting_position = NEGATIVE_SCENARIOS_REGEX.search(scenario_description)
        if positive_starting_position is None and negative_starting_position is None:
            raise ValueError(f'Unexpected reply from LLM, no normal/abnormal lists:\n{scenario_description}')

        new_positive = []
        new_negative = []
        if positive_starting_position is not None:
            endpos = negative_starting_position.start() \
                if negative_starting_position is not None else len(scenario_description)
            new_positive = ScenarioAnalyzer.__find_all_scenarios(scenario_description,
                                                                 positive_starting_position.start(), endpos)
        if negative_starting_position is not None:
            new_negative = ScenarioAnalyzer.__find_all_scenarios(scenario_description,
                                                                 negative_starting_position.start())

        return new_positive, new_negative

    @staticmethod
    def __find_all_scenarios(scenario_description, start_position, end_position=None):
        # we need this helper method since Pattern.findall returns a list of tuples
        if end_position is None:
            matches_as_tuples = SINGLE_SCENARIO_REGEX.findall(scenario_description, pos=start_position)
        else:
            matches_as_tuples = SINGLE_SCENARIO_REGEX.findall(scenario_description,
                                                              pos=start_position, endpos=end_position)
        return ["".join(x) for x in matches_as_tuples]

    def can_improve_unit_test(self):
        # this method implements a strategy for incrementally extending the test suite following the initial attempt
        if self.__iterations >= ScenarioAnalyzer.MAX_IMPROVEMENT_ITERATIONS:
            # if max number of iterations was reached, stop anyway
            return False
        # only proceed if the last iteration of the test suite improvement added at least a predefined number
        # of new scenarios
        return self.__new_scenarios_at_last_round >= ScenarioAnalyzer.MIN_NEW_SCENARIOS

    def __calculate_average_distance(self):
        # calculates and stores the up-to-date average distance between all pairs of scenarios
        all_scenarios = self.positive + self.negative
        sum_of_pairs = 0.0
        for first_index, first_scenario in enumerate(all_scenarios):
            for second_index, second_scenario in enumerate(all_scenarios):
                if first_index >= second_index:
                    continue
                sum_of_pairs += Similarity.compute_similarity(first_scenario, second_scenario)
        number_of_pairs = len(all_scenarios) * (len(all_scenarios) - 1) / 2
        self.__average_distance = sum_of_pairs / number_of_pairs

    def __should_add_scenario(self, scenario):
        all_scenarios = self.positive + self.negative
        if len(all_scenarios) == 0:
            # should add the new scenario anyway
            return True
        min_distance = min([Similarity.compute_similarity(scenario, s) for s in all_scenarios])
        return min_distance > self.__average_distance * ScenarioAnalyzer.DISTANCE_THRESHOLD

    def __filter_scenarios(self, new_positive, new_negative):
        # For each new scenario, we calculate the minimal distance to an existing scenario, and only those
        # distinct enough pass the filter.
        # "Distinct enough" means that the minimal distance is lower than a predefined threshold normalized by
        # the average distance between scenarios.

        if len(self.positive) == 0 and len(self.negative) == 0:
            # we are at the very beginning - skip this step
            return new_positive, new_negative
        self.__calculate_average_distance()
        return [s for s in new_positive if self.__should_add_scenario(s)],\
               [s for s in new_negative if self.__should_add_scenario(s)]
