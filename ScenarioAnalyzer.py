import re

POSITIVE_SCENARIOS_REGEX = re.compile('Normal Flow(.*?)', re.DOTALL | re.IGNORECASE)
NEGATIVE_SCENARIOS_REGEX = re.compile('Abnormal Flow(.*?)', re.DOTALL | re.IGNORECASE)
SINGLE_SCENARIO_REGEX = re.compile(r'^\d+\.(.*?)((\n(?=^\d|\n))|\Z)', re.MULTILINE | re.DOTALL)


class ScenarioAnalyzer(object):

    def __init__(self, scenario_description):
        self.positive = []
        self.negative = []
        self.__parse_scenario_description(scenario_description)

    def __parse_scenario_description(self, scenario_description):
        positive_starting_position = POSITIVE_SCENARIOS_REGEX.search(scenario_description)
        negative_starting_position = NEGATIVE_SCENARIOS_REGEX.search(scenario_description)
        if positive_starting_position is None and negative_starting_position is None:
            raise ValueError(f'Unexpected reply from LLM:\n{scenario_description}')

        if positive_starting_position is not None:
            self.positive = SINGLE_SCENARIO_REGEX.findall(scenario_description,
                                                          pos=positive_starting_position.start(),
                                                          endpos=negative_starting_position.start())
        if negative_starting_position is not None:
            self.negative = SINGLE_SCENARIO_REGEX.findall(scenario_description, pos=negative_starting_position.start())
