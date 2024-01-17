SANITY_SKELETON_QUERY_REPLY = """
To write unit tests for the given function, you can use a testing framework like unittest in Python. Here's an example of how you can structure your unit tests:
python
import unittest
from unittest.mock import Mock
from your_module import load_list_of_tasks

class TestLoadListOfTasks(unittest.TestCase):

    def setUp(self):
        # Set up any necessary objects or mocks
        pass

    def tearDown(self):
        # Clean up resources if needed
        pass

    def test_load_list_of_tasks_with_valid_data(self):
        # Create sample data for testing
        sample_data = [
            {'action': 'some_action', 'args': {'param1': 'value1'}},
            {'block': [{'action': 'nested_action', 'args': {'param2': 'value2'}}]}
        ]

        # Mock the required objects (you might need more mocks)
        play = Mock()
        block = Mock()
        role = Mock()
        task_include = Mock()
        variable_manager = Mock()
        loader = Mock()

        # Call the function with the sample data
        result = load_list_of_tasks(
            ds=sample_data,
            play=play,
            block=block,
            role=role,
            task_include=task_include,
            use_handlers=False,
            variable_manager=variable_manager,
            loader=loader
        )

        # Assert the result meets your expectations
        self.assertIsInstance(result, list)
        self.assertTrue(all(isinstance(task, (Task, TaskInclude, Block)) for task in result))

    def test_load_list_of_tasks_with_invalid_data(self):
        # Create sample data with invalid structure
        invalid_data = {'not_a_list': 'invalid_data'}

        # Mock the required objects
        play = Mock()
        block = Mock()
        role = Mock()
        task_include = Mock()
        variable_manager = Mock()
        loader = Mock()

        # Call the function with invalid data and assert an exception is raised
        with self.assertRaises(AnsibleAssertionError):
            load_list_of_tasks(
                ds=invalid_data,
                play=play,
                block=block,
                role=role,
                task_include=task_include,
                use_handlers=False,
                variable_manager=variable_manager,
                loader=loader
            )

    # Add more test cases as needed

if __name__ == '__main__':
    unittest.main()

Note: Adjust the import statements and the your_module placeholder with the actual module where load_list_of_tasks is defined. Also, you may need to mock more objects depending on the context and dependencies of your function.
"""


SANITY_SCENARIO_DESCRIPTION_QUERY_REPLY = """
This function, `load_list_of_tasks`, appears to process a list of task data structures parsed from YAML and returns a list of `Task` or `TaskInclude` objects. Below are the normal and abnormal flows that can be tested:

### Normal Flows:

1. **Loading Tasks without Blocks or Includes:**
   - **Input:** A list of task data structures without blocks or include statements.
   - **Expected Output:** A list of `Task` objects representing the tasks.

2. **Loading Tasks with Blocks:**
   - **Input:** A list of task data structures containing blocks.
   - **Expected Output:** A list of `Block` objects, each representing a block of tasks.

3. **Loading Tasks with Task Includes:**
   - **Input:** A list of task data structures containing `include_tasks` or `import_tasks` statements.
   - **Expected Output:** A list of `TaskInclude` objects representing the included tasks.

4. **Loading Tasks with Role Includes:**
   - **Input:** A list of task data structures containing `include_role` or `import_role` statements.
   - **Expected Output:** A list of `IncludeRole` objects representing the included roles.

### Abnormal Flows:

1. **Invalid Input Type:**
   - **Input:** Pass a non-list object as `ds`.
   - **Expected Output:** Raise an `AnsibleAssertionError` with an appropriate error message.

2. **Invalid Task Data Structure Type:**
   - **Input:** Pass a list containing a non-dict object as a task data structure.
   - **Expected Output:** Raise an `AnsibleAssertionError` with an appropriate error message.

3. **Using Block as a Handler:**
   - **Input:** A task data structure with a block and `use_handlers=True`.
   - **Expected Output:** Raise an `AnsibleParserError` with a message indicating that using a block as a handler is not supported.

4. **Invalid Action in Include Statements:**
   - **Input:** A task data structure with an unsupported action in `include_tasks` or `import_tasks`.
   - **Expected Output:** Raise an `AnsibleParserError` with a relevant error message.

5. **Invalid Loop in Import Statements:**
   - **Input:** A task data structure with a loop in `import_tasks` or `import_role`.
   - **Expected Output:** Raise an `AnsibleParserError` with a message indicating that using loops in import statements is not allowed.

6. **Error in Parsing Action Arguments:**
   - **Input:** A task data structure with invalid arguments for the action.
   - **Expected Output:** Raise an `AnsibleParserError` with details about the parsing error.

7. **Error in Dynamic Parent Include Path:**
   - **Input:** A task data structure with an error in evaluating the dynamic parent include path.
   - **Expected Output:** Raise an `AnsibleParserError` with details about the error.

8. **Error in Import Path:**
   - **Input:** A task data structure with an error in evaluating the import path.
   - **Expected Output:** Raise an `AnsibleParserError` with details about the error.

9. **Empty Included Task File:**
   - **Input:** An `import_tasks` statement pointing to an empty task file.
   - **Expected Output:** Display a warning and continue processing the next task.

10. **Included Task File Not Found:**
    - **Input:** An `import_tasks` statement pointing to a non-existent file.
    - **Expected Output:** Raise an `AnsibleParserError` indicating that the included task file was not found.

11. **Invalid Included Task File Format:**
    - **Input:** An `import_tasks` statement pointing to a file that does not contain a list of tasks.
    - **Expected Output:** Raise an `AnsibleParserError` indicating that the included task file must contain a list of tasks.

These test cases cover a range of scenarios to ensure the function behaves correctly under normal conditions and handles errors appropriately.
"""


SANITY_SINGLE_SCENARIO_QUERY_REPLY = """
Certainly! For the normal flow number 3 (Loading Tasks with Task Includes), you can write a unit test as follows:
python
import unittest
from unittest.mock import patch
from your_module import load_list_of_tasks  # Replace 'your_module' with the actual module containing the function

class TestLoadListOfTasks(unittest.TestCase):

    @patch('your_module.os.path.exists', return_value=True)
    @patch('your_module.loader.load_from_file', return_value=[{'name': 'IncludedTask'}])
    @patch('your_module.display.vv')
    def test_load_tasks_with_task_includes(self, mock_display_vv, mock_load_from_file, mock_path_exists):
        # Arrange
        ds = [{'import_tasks': 'included_tasks.yml'}]  # Include a task with an existing file
        play = mock_role = None  # Provide necessary mock objects or None if not relevant
        # Mock other necessary dependencies as needed

        # Act
        result = load_list_of_tasks(ds, play, role=mock_role)

        # Assert
        mock_path_exists.assert_called_once_with('included_tasks.yml')
        mock_load_from_file.assert_called_once_with('included_tasks.yml')
        mock_display_vv.assert_called_once_with("statically imported: included_tasks.yml")
        self.assertEqual(len(result), 1)  # Check that one task is loaded
        self.assertEqual(result[0]['name'], 'IncludedTask')  # Check the loaded task details

if __name__ == '__main__':
    unittest.main()

In this test case, the patch decorator is used to mock the os.path.exists, loader.load_from_file, and display.vv functions. The test checks whether the function correctly loads tasks when there is an import_tasks statement, mocks the file existence check, and simulates loading tasks from the included file. Adjust the module and dependencies as needed based on your actual implementation.
"""