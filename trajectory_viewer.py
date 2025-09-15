#!/usr/bin/env python3
"""
Enhanced Streamlit app for visualizing SWE-bench agent trajectories.

Features:
- Interactive task navigation with Previous/Next controls
- Sidebar table of contents for quick step navigation
- Focused single-step analysis mode
- Color-coded role indicators and success/error markers
- Action distribution analytics

Usage: streamlit run trajectory_viewer.py
"""

import streamlit as st
import json
import os
from pathlib import Path
import pandas as pd

# Configuration
BASE_DIR = Path('evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)')
TRAJS_DIR = BASE_DIR / 'trajs'
RESULTS_PATH = BASE_DIR / 'results' / 'results.json'
ERROR_KEYWORDS = {'error', 'exception', 'failed', 'traceback'}
KEYS_TO_RENDER = {"old_str", "new_str", "file_text"}

@st.cache_data
def load_results():
    """Load results data"""
    if not RESULTS_PATH.exists():
        st.error(f"Results file not found: {RESULTS_PATH}")
        return None

    with open(RESULTS_PATH, 'r') as f:
        return json.load(f)

@st.cache_data
def load_trajectory(task_id):
    """Load trajectory for a given task ID"""
    task_dir = TRAJS_DIR / task_id
    if not task_dir.exists():
        return None

    json_files = list(task_dir.glob('*.json'))
    if not json_files:
        return None

    with open(json_files[0], 'r') as f:
        return json.load(f)

def get_trajectory_summary(traj_data):
    """Get summary statistics for a trajectory using structured fncall_messages"""
    if not traj_data:
        return {}

    # Use structured fncall_messages if available, fallback to messages
    messages = traj_data.get('fncall_messages', traj_data.get('messages', []))

    actions = []
    files_modified = set()
    error_count = 0

    for message in messages:
        role = message.get('role', '')

        # Process assistant messages with structured tool calls
        if role == 'assistant':
            tool_calls = message.get('tool_calls', [])
            for tool_call in tool_calls:
                if tool_call.get('type') == 'function':
                    func_name = tool_call.get('function', {}).get('name', '')
                    if func_name:
                        actions.append(func_name)

                        # Track file modifications
                        try:
                            import json as json_lib
                            args = json_lib.loads(tool_call.get('function', {}).get('arguments', '{}'))
                            if func_name == 'str_replace_editor' and 'path' in args:
                                files_modified.add(args['path'])
                        except json_lib.JSONDecodeError:
                            pass

        # Process tool execution results for errors
        elif role == 'tool':
            content = message.get('content', '')
            if any(keyword in content.lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                error_count += 1

    assistant_messages = [m for m in messages if m.get('role') == 'assistant']

    return {
        'total_assistant_steps': len(assistant_messages),
        'total_steps': len(messages),
        'action_types': list(set(actions)),
        'action_counts': pd.Series(actions).value_counts().to_dict() if actions else {},
        'files_modified': len(files_modified),
        'error_count': error_count
    }

def generate_table_of_contents(messages):
    """
    Generate table of contents for trajectory navigation.

    Creates a structured list of all trajectory steps with:
    - Role-based icons and titles
    - Content previews
    - Success/error indicators for tool results
    - Color coding for different message types
    """
    toc_items = []

    for i, message in enumerate(messages):
        role = message.get('role', 'UNK')
        step_num = i + 1

        if role == 'system':
            toc_items.append({
                'step': step_num,
                'role': role,
                'title': '🔧 System Prompt',
                'subtitle': 'Initial system prompt and configuration',
                'color': '#DEB887'
            })
        elif role == 'user':
            content = message.get('content', '')

            toc_items.append({
                'step': step_num,
                'role': role,
                'title': '👤 User Prompt',
                'subtitle': 'Uploaded files and issue description',
                'color': '#9370DB'
            })
        elif role == 'assistant':
            tool_calls = message.get('tool_calls', [])
            if tool_calls:
                func_name = tool_calls[0].get('function', {}).get('name', 'UNK')
                toc_items.append({
                    'step': step_num,
                    'role': role,
                    'title': f'🤖 Assistant Action',
                    'subtitle': f'{func_name}',
                    'color': '#32CD32'
                })
            else:
                content = message.get('content', '')
                preview = content.split('\n')[0][:40]
                if len(content.split('\n')[0]) > 40:
                    preview += "..."
                toc_items.append({
                    'step': step_num,
                    'role': role,
                    'title': '🤖 Assistant Response',
                    'subtitle': preview,
                    'color': '#32CD32'
                })
        elif role == 'tool':
            tool_name = message.get('name', 'UNK')
            content = message.get('content', '')
            # Check if there's an error
            has_error = any(keyword in content.lower() for keyword in ERROR_KEYWORDS)
            error_indicator = ' ❌' if has_error else ' ✅'

            toc_items.append({
                'step': step_num,
                'role': role,
                'title': f'🔧 Tool Result{error_indicator}',
                'subtitle': f'{tool_name}',
                'color': '#1E90FF'
            })

    return toc_items

def display_step(message_data, step_num):
    """
    Display a single trajectory step using fncall_messages format.

    Renders step content with:
    - Color-coded headers based on message role
    - Structured tool call display with arguments
    - Success/error indicators for tool results
    - Expandable content areas for detailed examination
    """
    role = message_data.get('role', 'UNK')
    content = message_data.get('content', '')

    # Define color scheme for different roles
    role_colors = {
        'system': '#FFE4B5',      # Moccasin (light orange)
        'user': '#E6E6FA',        # Lavender (light purple)
        'assistant': '#E0F2E7',   # Light green
        'tool': '#E3F2FD'         # Light blue
    }

    # Get color for current role
    bg_color = role_colors.get(role, '#F5F5F5')  # Default light gray

    # Add custom CSS for role-based styling
    role_border_colors = {
        'system': '#DEB887',   # Dark orange
        'user': '#9370DB',     # Medium purple
        'assistant': '#32CD32', # Lime green
        'tool': '#1E90FF'      # Dodger blue
    }
    border_color = role_border_colors.get(role, '#808080')

    # Create a colored indicator before the expander
    if role == 'system':
        st.markdown(f"""
        <div style="border-left: 6px solid {border_color}; background: {bg_color}; padding: 2px 0; margin-bottom: 5px;">
            <span style="color: {border_color}; font-weight: bold; padding-left: 10px;">🔧 SYSTEM</span>
        </div>

        """, unsafe_allow_html=True)

        with st.expander(f"Step {step_num}", expanded=True):
            st.subheader("System Prompt:")
            st.text_area("Content", content, height=200, key=f"system_{step_num}")

    elif role == 'user':
        st.markdown(f"""
        <div style="border-left: 6px solid {border_color}; background: {bg_color}; padding: 2px 0; margin-bottom: 5px;">
            <span style="color: {border_color}; font-weight: bold; padding-left: 10px;">👤 USER</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Step {step_num}", expanded=True):
            st.subheader("User Prompt:")
            st.text_area("Content", content, height=500, key=f"user_{step_num}")

    elif role == 'assistant':
        tool_calls = message_data.get('tool_calls', [])
        if tool_calls:
            if len(tool_calls) > 1:
                raise ValueError(f"There should only be one tool call per step, but the current step has {len(tool_calls)} tool calls.")
            tool_call = tool_calls[0]  # Show first and only tool call
            tool_call_id = tool_call.get('id', '')
            func_name = tool_call.get('function', {}).get('name', 'UNK')

            st.markdown(f"""
            <div style="border-left: 6px solid {border_color}; background: {bg_color}; padding: 2px 0; margin-bottom: 5px;">
                <span style="color: {border_color}; font-weight: bold; padding-left: 10px;">🤖 ASSISTANT</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Step {step_num}", expanded=True):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("Reasoning:")
                    st.text_area("Reasoning", content, height=200, key=f"reasoning_{step_num}")

                with col2:
                    st.subheader(f"Tool Call ({tool_call_id}):")
                    st.write(f"**Function:** `{func_name}`")

                    # Parse and display arguments in organized format
                    args_json = tool_call.get('function', {}).get('arguments', '{}')
                    try:
                        import json as json_lib
                        parsed_args = json_lib.loads(args_json)

                        if parsed_args:
                            st.write("**Arguments:**")
                            for key, value in parsed_args.items():
                                # Display key-value pairs with better formatting
                                if key in KEYS_TO_RENDER:
                                    with st.expander(f"📄 **{key}** (click to expand)", expanded=False):
                                        if parsed_args['path'].endswith('py'):
                                            st.code(value, height=200, language='py')
                                        else:
                                            st.text_area("", value, height=200, key=f"arg_{key}_{step_num}")
                                else:
                                    # For short values, display inline
                                    st.write(f"\t**{key}:** `{value}`")
                        else:
                            st.write("*No arguments*")

                    except json_lib.JSONDecodeError:
                        # Fallback to raw display if JSON parsing fails
                        st.write("**Raw Arguments:**")
                        st.code(args_json, language='json')
        else:
            st.markdown(f"""
            <div style="border-left: 6px solid {border_color}; background: {bg_color}; padding: 2px 0; margin-bottom: 5px;">
                <span style="color: {border_color}; font-weight: bold; padding-left: 10px;">🤖 ASSISTANT</span>
            </div>
            """, unsafe_allow_html=True)

            # Assistant message without tool calls
            with st.expander(f"Step {step_num}", expanded=True):
                st.text_area("Response", content, height=200, key=f"assistant_no_tool_{step_num}")

    elif role == 'tool':
        tool_name = message_data.get('name', 'UNK')
        tool_call_id = message_data.get('tool_call_id', '')
        has_error = any(keyword in content.lower() for keyword in ERROR_KEYWORDS)
        error_indicator = ' ❌' if has_error else ' ✅'

        st.markdown(f"""
        <div style="border-left: 6px solid {border_color}; background: {bg_color}; padding: 2px 0; margin-bottom: 5px;">
            <span style="color: {border_color}; font-weight: bold; padding-left: 10px;">🔧 TOOL</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Step {step_num}", expanded=True):
            st.subheader(f"Tool Result ({tool_call_id}): {error_indicator}")
            st.text_area("Output", content, height=300, key=f"tool_output_{step_num}")

    else:
        raise ValueError(f"The following role is not defined: {role}.")

def main():
    st.set_page_config(
        page_title="SWE-bench Trajectory Viewer",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 SWE Agent Trajectory Viewer")
    st.markdown("Analyze the [trajectories](https://github.com/multi-swe-bench/experiments/tree/main/evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)) of the OpenHands CodeActAgent with Claude-3.5-Sonnet on Python tasks")

    # Load results
    results_data = load_results()
    if not results_data:
        return

    # Sidebar: Task selection
    st.sidebar.header("Task Selection")

    # Show summary stats
    st.sidebar.metric("Total Instances", results_data.get('total_instances', 0))
    st.sidebar.metric("Resolved", results_data.get('resolved_instances', 0))
    st.sidebar.metric("Unresolved", results_data.get('unresolved_instances', 0))

    # Task selection
    task_type = st.sidebar.selectbox(
        "Select task type",
        ["Unresolved Tasks", "All Tasks"]
    )

    if task_type == "Unresolved Tasks":
        available_tasks = results_data.get('unresolved_ids', [])
    else:
        # Get all tasks from directory
        available_tasks = [d.name for d in TRAJS_DIR.iterdir() if d.is_dir()]

    # Filter by project
    projects = list(set([task.split('__')[0] for task in available_tasks]))
    selected_project = st.sidebar.selectbox(
        "Filter by project",
        ["All"] + sorted(projects)
    )

    if selected_project != "All":
        available_tasks = [task for task in available_tasks if task.startswith(selected_project)]

    # Initialize session state for task navigation
    # Tracks current position in filtered task list and detects filter changes
    if 'task_index' not in st.session_state:
        st.session_state.task_index = 0
    if 'current_filter' not in st.session_state:
        st.session_state.current_filter = (task_type, selected_project)

    # Reset index if filter changed to start from beginning of new filtered list
    if st.session_state.current_filter != (task_type, selected_project):
        st.session_state.task_index = 0
        st.session_state.current_filter = (task_type, selected_project)

    # Ensure index is within bounds of current filtered list
    if available_tasks:
        st.session_state.task_index = max(0, min(st.session_state.task_index, len(available_tasks) - 1))
        selected_task = available_tasks[st.session_state.task_index]
    else:
        selected_task = None

    # Navigation controls for browsing through filtered tasks
    if available_tasks:
        st.sidebar.markdown("---")
        st.sidebar.write(f"Task {st.session_state.task_index + 1} of {len(available_tasks)}")

        col1, col2, col3 = st.sidebar.columns([1, 1, 1])
        with col1:
            if st.button("Prev", disabled=(st.session_state.task_index == 0)):
                st.session_state.task_index -= 1
                st.rerun()
        with col2:
            st.write(f"{st.session_state.task_index + 1}/{len(available_tasks)}")
        with col3:
            if st.button("Next", disabled=(st.session_state.task_index == len(available_tasks) - 1)):
                st.session_state.task_index += 1
                st.rerun()

    # Manual task selection for jumping to specific tasks
    st.sidebar.markdown("---")
    manual_task = st.sidebar.selectbox(
        "Jump to specific task",
        [""] + available_tasks,
        index=available_tasks.index(selected_task) + 1 if selected_task and selected_task in available_tasks else 0
    )

    if manual_task and manual_task != selected_task:
        st.session_state.task_index = available_tasks.index(manual_task)
        st.rerun()

    if not selected_task:
        st.info("👈 No tasks available for the selected filters")
        return

    # Load trajectory data early for TOC generation
    traj_data = load_trajectory(selected_task)
    if not traj_data:
        st.error(f"Could not load trajectory for {selected_task}")
        return

    # Use structured fncall_messages if available, fallback to messages
    messages = traj_data.get('fncall_messages', traj_data.get('messages', []))
    if not messages:
        st.warning("No trajectory messages found")
        return

    # Generate table of contents for sidebar
    toc_items = generate_table_of_contents(messages)

    # Table of Contents in Sidebar - provides navigation overview of all trajectory steps
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Table of Contents")

    # Initialize selected step in session state for focused view mode
    if 'selected_step' not in st.session_state:
        st.session_state.selected_step = None

    # Quick stats showing trajectory composition
    st.sidebar.write(f"**Total Steps:** {len(messages)}")

    # Role breakdown - shows distribution of different message types
    role_counts = {}
    for item in toc_items:
        role = item['role']
        role_counts[role] = role_counts.get(role, 0) + 1

    for role, count in role_counts.items():
        icon = {'system': '🔧', 'user': '👤', 'assistant': '🤖', 'tool': '🔧'}.get(role, '❓')
        st.sidebar.write(f"{icon} {role.title()}: {count}")

    st.sidebar.markdown("---")

    # TOC navigation - clickable buttons for each trajectory step
    st.sidebar.write("**Navigate to Step:**")

    # Display TOC items in sidebar with compact formatting
    for item in toc_items:
        button_key = f"toc_step_{item['step']}"

        # Create compact button with step info (remove emoji for cleaner sidebar)
        button_label = f"Step {item['step']}: {item['title'].replace('🔧 ', '').replace('👤 ', '').replace('🤖 ', '')}"

        if st.sidebar.button(
            button_label,
            key=button_key,
            help=f"{item['subtitle']}",
            use_container_width=True
        ):
            st.session_state.selected_step = item['step']
            st.rerun()

        # Add small visual indicator for tool result status
        if 'Tool Result❌' in item['title']:
            st.sidebar.markdown("   <small style='color: red;'>⚠️ Contains errors</small>", unsafe_allow_html=True)
        elif 'Tool Result✅' in item['title']:
            st.sidebar.markdown("   <small style='color: green;'>✓ Success</small>", unsafe_allow_html=True)

    # Task header
    st.header(f"Task: {selected_task}")

    # Parse task info
    parts = selected_task.split('__')
    if len(parts) == 2:
        org_name = parts[0]
        repo_and_issue = parts[1]
        repo_parts = repo_and_issue.split('-')
        repo_name = '-'.join(repo_parts[:-1])
        issue_num = repo_parts[-1]

        github_url = f"https://github.com/{org_name}/{repo_name}/pull/{issue_num}"
        st.markdown(f"**GitHub PR**: [{github_url}]({github_url})")

    # Trajectory summary
    summary = get_trajectory_summary(traj_data)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Assistant Steps", summary.get('total_assistant_steps', 0))
    with col2:
        st.metric("Total Steps", summary.get('total_steps', 0))
    with col3:
        st.metric("Files Modified", summary.get('files_modified', 0))
    with col4:
        st.metric("Errors", summary.get('error_count', 0))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Unique Actions", len(summary.get('action_types', [])))
    with col2:
        action_counts = summary.get('action_counts', {})
        most_common = max(action_counts.items(), key=lambda x: x[1]) if action_counts else ("none", 0)
        st.metric("Most Common Action", f"{most_common[0]} ({most_common[1]})")

    # Action distribution
    if summary.get('action_counts'):
        st.subheader("Action Distribution")
        df_actions = pd.DataFrame(list(summary['action_counts'].items()),
                                 columns=['Action', 'Count'])
        st.bar_chart(df_actions.set_index('Action'))

    # Trajectory steps
    st.subheader("🔍 Trajectory Steps")
    st.info(f"Displaying all {len(messages)} messages in the trajectory")

    # Handle navigation to selected step
    if st.session_state.selected_step:
        # Show selected step prominently
        selected_step_num = st.session_state.selected_step
        st.info(f"🎯 Jumped to Step {selected_step_num}")

        # Add a "Show All Steps" button
        if st.button("📋 Show All Steps", help="Return to viewing all steps"):
            st.session_state.selected_step = None
            st.rerun()

        # Display only the selected step
        if 1 <= selected_step_num <= len(messages):
            selected_message = messages[selected_step_num - 1]
            st.markdown(f'<div id="step_{selected_step_num}"></div>', unsafe_allow_html=True)
            display_step(selected_message, selected_step_num)

            # Add navigation buttons around the selected step
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if selected_step_num > 1:
                    if st.button("⬅️ Prev Step"):
                        st.session_state.selected_step = selected_step_num - 1
                        st.rerun()

            with col2:
                st.write(f"Step {selected_step_num} of {len(messages)}")

            with col3:
                if selected_step_num < len(messages):
                    if st.button("Next Step ➡️"):
                        st.session_state.selected_step = selected_step_num + 1
                        st.rerun()

    else:
        # Display all steps with anchors
        for i, message in enumerate(messages):
            step_num = i + 1
            # Add HTML anchor for navigation
            st.markdown(f'<div id="step_{step_num}"></div>', unsafe_allow_html=True)
            display_step(message, step_num)

    # Raw data download
    st.subheader("Raw Data")
    if st.button("Download trajectory JSON"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(traj_data, indent=2),
            file_name=f"{selected_task}_trajectory.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()