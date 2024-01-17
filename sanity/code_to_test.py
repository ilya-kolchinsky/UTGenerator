def load_list_of_tasks(ds, play, block=None, role=None, task_include=None, use_handlers=False,
                       variable_manager=None, loader=None):
    '''
    Given a list of task datastructures (parsed from YAML),
    return a list of Task() or TaskInclude() objects.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block
    from ansible.playbook.handler import Handler
    from ansible.playbook.task import Task
    from ansible.playbook.task_include import TaskInclude
    from ansible.playbook.role_include import IncludeRole
    from ansible.playbook.handler_task_include import HandlerTaskInclude
    from ansible.template import Templar
    from ansible.utils.plugin_docs import get_versioned_doclink

    if not isinstance(ds, list):
        raise AnsibleAssertionError('The ds (%s) should be a list but was a %s' % (ds, type(ds)))

    task_list = []
    for task_ds in ds:
        if not isinstance(task_ds, dict):
            raise AnsibleAssertionError('The ds (%s) should be a dict but was a %s' % (ds, type(ds)))

        if 'block' in task_ds:
            if use_handlers:
                raise AnsibleParserError("Using a block as a handler is not supported.", obj=task_ds)
            t = Block.load(
                task_ds,
                play=play,
                parent_block=block,
                role=role,
                task_include=task_include,
                use_handlers=use_handlers,
                variable_manager=variable_manager,
                loader=loader,
            )
            task_list.append(t)
        else:
            args_parser = ModuleArgsParser(task_ds)
            try:
                (action, args, delegate_to) = args_parser.parse(skip_action_validation=True)
            except AnsibleParserError as e:
                # if the raises exception was created with obj=ds args, then it includes the detail
                # so we dont need to add it so we can just re raise.
                if e.obj:
                    raise
                # But if it wasn't, we can add the yaml object now to get more detail
                raise AnsibleParserError(to_native(e), obj=task_ds, orig_exc=e)

            if action in C._ACTION_ALL_INCLUDE_IMPORT_TASKS:

                if use_handlers:
                    include_class = HandlerTaskInclude
                else:
                    include_class = TaskInclude

                t = include_class.load(
                    task_ds,
                    block=block,
                    role=role,
                    task_include=None,
                    variable_manager=variable_manager,
                    loader=loader
                )

                all_vars = variable_manager.get_vars(play=play, task=t)
                templar = Templar(loader=loader, variables=all_vars)

                # check to see if this include is dynamic or static:
                if action in C._ACTION_IMPORT_TASKS:
                    if t.loop is not None:
                        raise AnsibleParserError(
                            "You cannot use loops on 'import_tasks' statements. You should use 'include_tasks' instead.",
                            obj=task_ds)

                    # we set a flag to indicate this include was static
                    t.statically_loaded = True

                    # handle relative includes by walking up the list of parent include
                    # tasks and checking the relative result to see if it exists
                    parent_include = block
                    cumulative_path = None

                    found = False
                    subdir = 'tasks'
                    if use_handlers:
                        subdir = 'handlers'
                    while parent_include is not None:
                        if not isinstance(parent_include, TaskInclude):
                            parent_include = parent_include._parent
                            continue
                        try:
                            parent_include_dir = os.path.dirname(
                                templar.template(parent_include.args.get('_raw_params')))
                        except AnsibleUndefinedVariable as e:
                            if not parent_include.statically_loaded:
                                raise AnsibleParserError(
                                    "Error when evaluating variable in dynamic parent include path: %s. "
                                    "When using static imports, the parent dynamic include cannot utilize host facts "
                                    "or variables from inventory" % parent_include.args.get('_raw_params'),
                                    obj=task_ds,
                                    suppress_extended_error=True,
                                    orig_exc=e
                                )
                            raise
                        if cumulative_path is None:
                            cumulative_path = parent_include_dir
                        elif not os.path.isabs(cumulative_path):
                            cumulative_path = os.path.join(parent_include_dir, cumulative_path)
                        include_target = templar.template(t.args['_raw_params'])
                        if t._role:
                            new_basedir = os.path.join(t._role._role_path, subdir, cumulative_path)
                            include_file = loader.path_dwim_relative(new_basedir, subdir, include_target)
                        else:
                            include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path,
                                                                     include_target)

                        if os.path.exists(include_file):
                            found = True
                            break
                        else:
                            parent_include = parent_include._parent

                    if not found:
                        try:
                            include_target = templar.template(t.args['_raw_params'])
                        except AnsibleUndefinedVariable as e:
                            raise AnsibleParserError(
                                "Error when evaluating variable in import path: %s.\n\n"
                                "When using static imports, ensure that any variables used in their names are defined in vars/vars_files\n"
                                "or extra-vars passed in from the command line. Static imports cannot use variables from facts or inventory\n"
                                "sources like group or host vars." % t.args['_raw_params'],
                                obj=task_ds,
                                suppress_extended_error=True,
                                orig_exc=e)
                        if t._role:
                            include_file = loader.path_dwim_relative(t._role._role_path, subdir, include_target)
                        else:
                            include_file = loader.path_dwim(include_target)

                    data = loader.load_from_file(include_file)
                    if not data:
                        display.warning('file %s is empty and had no tasks to include' % include_file)
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError("included task files must contain a list of tasks", obj=data)

                    # since we can't send callbacks here, we display a message directly in
                    # the same fashion used by the on_include callback. We also do it here,
                    # because the recursive nature of helper methods means we may be loading
                    # nested includes, and we want the include order printed correctly
                    display.vv("statically imported: %s" % include_file)

                    ti_copy = t.copy(exclude_parent=True)
                    ti_copy._parent = block
                    included_blocks = load_list_of_blocks(
                        data,
                        play=play,
                        parent_block=None,
                        task_include=ti_copy,
                        role=role,
                        use_handlers=use_handlers,
                        loader=loader,
                        variable_manager=variable_manager,
                    )

                    tags = ti_copy.tags[:]

                    # now we extend the tags on each of the included blocks
                    for b in included_blocks:
                        b.tags = list(set(b.tags).union(tags))
                    # END FIXME

                    # FIXME: handlers shouldn't need this special handling, but do
                    #        right now because they don't iterate blocks correctly
                    if use_handlers:
                        for b in included_blocks:
                            task_list.extend(b.block)
                    else:
                        task_list.extend(included_blocks)
                else:
                    t.is_static = False
                    task_list.append(t)

            elif action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_ROLES:
                if use_handlers:
                    raise AnsibleParserError(f"Using '{action}' as a handler is not supported.", obj=task_ds)

                ir = IncludeRole.load(
                    task_ds,
                    block=block,
                    role=role,
                    task_include=None,
                    variable_manager=variable_manager,
                    loader=loader,
                )

                if action in C._ACTION_IMPORT_ROLE:
                    if ir.loop is not None:
                        raise AnsibleParserError(
                            "You cannot use loops on 'import_role' statements. You should use 'include_role' instead.",
                            obj=task_ds)

                    # we set a flag to indicate this include was static
                    ir.statically_loaded = True

                    # template the role name now, if needed
                    all_vars = variable_manager.get_vars(play=play, task=ir)
                    templar = Templar(loader=loader, variables=all_vars)
                    ir.post_validate(templar=templar)
                    ir._role_name = templar.template(ir._role_name)

                    # uses compiled list from object
                    blocks, dummy = ir.get_block_list(variable_manager=variable_manager, loader=loader)
                    task_list.extend(blocks)
                else:
                    # passes task object itself for latter generation of list
                    task_list.append(ir)
            else:
                if use_handlers:
                    t = Handler.load(task_ds, block=block, role=role, task_include=task_include,
                                     variable_manager=variable_manager, loader=loader)
                else:
                    t = Task.load(task_ds, block=block, role=role, task_include=task_include,
                                  variable_manager=variable_manager, loader=loader)

                task_list.append(t)

    return task_list
