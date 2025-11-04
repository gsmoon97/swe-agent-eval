# SWE-bench Trajectory Analysis Tools

A research toolkit for analyzing LLM agent failures on software engineering tasks using interactive trajectory visualization and statistical analysis.

## Overview

The repository contains:
- **Agent trajectory data**: Located in `evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)/`
- **Analysis tools**: Scripts and notebooks for exploring and analyzing trajectories
- **Visualization tools**: Streamlit app for interactive trajectory viewing

## Files

### Analysis Tools
- `trajectory_analysis.ipynb` - Jupyter notebook for exploratory data analysis
- `trajectory_viewer.py` - Enhanced Streamlit app for interactive trajectory visualization

### Data Structure
```
evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)/
├── results/
│   └── results.json          # Success/failure results for all 500 tasks
├── trajs/                    # Individual trajectory directories
│   ├── astropy__astropy-12907/
│   │   └── Claude-3.5-Sonnet*.json
│   └── ...                   # 500 task directories
└── all_preds.jsonl          # Predictions file
```

## Usage

### 1. Setup Environment
```bash
pip install -r requirements.txt
```

### 2. Interactive Trajectory Viewing
```bash
streamlit run trajectory_viewer.py
```

**Public Access**: A live version is available at https://swe-agent-eval.streamlit.app/

This launches a web interface where you can:
- Browse all tasks (resolved/unresolved) with automatic navigation
- Filter by project and navigate with Previous/Next buttons
- View step-by-step agent actions and observations
- Use sidebar table of contents for quick navigation to specific steps
- Jump to individual steps or view focused single-step analysis
- See action distribution charts and trajectory statistics
- Download raw trajectory data

### 3. Detailed Analysis (Jupyter)
```bash
jupyter notebook trajectory_analysis.ipynb
```

This notebook provides:
- Statistical analysis of trajectory patterns
- Visualization of action distributions
- Tools for task/issue selection with analytical potential
- Sample trajectory examination

## Challenge Question Workflow

### Phase 1: Candidate Selection
1. Use `trajectory_viewer.py` to explore trajectory data:
   - Filter by project and task type (resolved/unresolved)
   - Use Previous/Next navigation to browse through filtered tasks
   - Use sidebar table of contents to jump to specific trajectory steps
   - Focus on individual steps for detailed analysis
   - Look for error indicators (❌) and success markers (✅) in tool results
2. Check GitHub PRs to understand the original issues

### Phase 2: Detailed Analysis
1. Select one task with interesting failure patterns
2. Study the original GitHub issue and correct solution
3. Trace through agent trajectory step-by-step
4. Identify specific failure points and missing context

### Phase 3: Documentation
1. Document what the bug was
2. Explain how the agent tried to fix it
3. Identify where the agent went wrong
4. Suggest what additional context could have helped

## Task Information

Each task ID follows the pattern: `{org}__{repo}-{issue_number}`

For example: `astropy__astropy-12907`
- Organization: astropy
- Repository: astropy
- Issue/PR number: 12907
- GitHub URL: https://github.com/astropy/astropy/pull/12907

## Data Summary

- **Total instances**: 500
- **Resolved**: ~195 (39% success rate)
- **Unresolved**: ~252 (available for analysis)
- **Agent**: OpenHands CodeActAgent with Claude-3.5-Sonnet
- **Date**: March 29, 2025 evaluation run
- **Source**: Agent trajectories from https://github.com/multi-swe-bench/experiments

## Key Analysis Questions

When analyzing a failed trajectory, consider:

1. **Issue Understanding**: How well did the agent understand the reported problem?
2. **Context Retrieval**: What files/code did the agent examine? What did it miss?
3. **Solution Approach**: Was the agent's approach fundamentally correct?
4. **Execution Errors**: Did the agent make implementation mistakes?
5. **Testing**: Did the agent validate its changes appropriately?
6. **Missing Context**: What additional repository context could have helped?

## Example Analysis Flow

1. `streamlit run trajectory_viewer.py` → Explore trajectory data
   - Use Previous/Next navigation to browse through filtered tasks
   - Use sidebar table of contents to jump to specific trajectory steps
   - Focus on individual steps for detailed analysis
   - Look for error indicators (❌) and success markers (✅) in tool results
2. Research GitHub issue and correct solution
3. Trace agent steps and identify failure points
4. Document analysis with recommendations for better context retrieval

## Trajectory Viewer Features

The enhanced Streamlit interface provides:

### Navigation Controls
- **Task Navigation**: Previous/Next buttons to browse through filtered task lists
- **Automatic Selection**: Shows first task in filtered results by default
- **Manual Selection**: Jump to specific tasks via dropdown

### Table of Contents
- **Sidebar TOC**: Complete step-by-step overview with role-based icons
- **Quick Navigation**: Click any step to jump directly to detailed view
- **Visual Indicators**: Success (✅) and error (❌) markers for tool results
- **Step Statistics**: Breakdown of steps by role (System, User, Assistant, Tool)

### Step Analysis
- **Focused View**: Display individual steps in isolation for detailed analysis
- **Step Navigation**: Previous/Next step buttons when viewing single steps
- **Enhanced Display**: Color-coded step headers with role identification
- **Tool Call Details**: Structured display of function calls and arguments