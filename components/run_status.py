"""
Run Status page functionality
"""
import streamlit as st
import pandas as pd
import datetime
from databricks.sdk import WorkspaceClient
from utils import job_label, get_string_value

def show_run_status_page(w: WorkspaceClient):
    """
    Display the run status page
    """
    st.subheader("Job Run Status")
    st.write("View and monitor job run history and status.")
    
    # Job selector for status page
    @st.cache_data(ttl=60)
    def list_all_jobs():
        return list(w.jobs.list(expand_tasks=False))
    
    all_jobs = list_all_jobs()
    
    st.markdown("### Select a job to view run history")
    if not all_jobs:
        st.info("No jobs found.")
        st.stop()
    
    selected_job = st.selectbox(
        "Job",
        options=all_jobs,
        format_func=job_label,
        key="status_job_selector"
    )
    
    # Initialize session state for pagination
    if "runs_offset" not in st.session_state:
        st.session_state.runs_offset = 0
    if "all_runs" not in st.session_state:
        st.session_state.all_runs = []
    if "selected_job_id" not in st.session_state:
        st.session_state.selected_job_id = None
    
    # Reset when job changes
    if st.session_state.selected_job_id != selected_job.job_id:
        st.session_state.runs_offset = 0
        st.session_state.all_runs = []
        st.session_state.selected_job_id = selected_job.job_id
    
    # Fetch job runs with pagination
    @st.cache_data(ttl=30)  # Shorter cache for more up-to-date status
    def get_job_runs_batch(job_id: int, limit: int = 5, offset: int = 0):
        try:
            # Get runs for the specific job with pagination
            runs = list(w.jobs.list_runs(job_id=job_id, limit=limit, offset=offset))
            return runs
        except Exception as e:
            st.error(f"Error fetching job runs: {e}")
            return []
    
    # Load initial batch or when load more is clicked
    if st.session_state.runs_offset == 0 or len(st.session_state.all_runs) == 0:
        initial_runs = get_job_runs_batch(selected_job.job_id, limit=5, offset=0)
        st.session_state.all_runs = initial_runs
        st.session_state.runs_offset = 5
    
    if not st.session_state.all_runs:
        st.info("No runs found for this job.")
    else:
        st.markdown("### Run History")
        
        # Prepare data for table
        run_data = []
        for run in st.session_state.all_runs:
            # Extract run parameters - try multiple locations
            run_params = "None"
            params = []
            
            # First try job_parameters (API structure: array of objects with name/value/default)
            if hasattr(run, 'job_parameters') and run.job_parameters:
                if isinstance(run.job_parameters, list):
                    for param in run.job_parameters:
                        if isinstance(param, dict):
                            # Handle API structure: {"name": "table", "value": "customers", "default": "users"}
                            if 'name' in param and 'value' in param:
                                params.append(f"{param['name']}: {param['value']}")
                            else:
                                # Handle other dict formats
                                for k, v in param.items():
                                    params.append(f"{k}: {v}")
                        else:
                            params.append(str(param))
                elif isinstance(run.job_parameters, dict):
                    # Handle dict format
                    for k, v in run.job_parameters.items():
                        params.append(f"{k}: {v}")
                else:
                    params.append(str(run.job_parameters))
            
            # Fallback to overriding_parameters if no job_parameters found
            elif hasattr(run, 'overriding_parameters') and run.overriding_parameters:
                if hasattr(run.overriding_parameters, 'job_parameters') and run.overriding_parameters.job_parameters:
                    for k, v in run.overriding_parameters.job_parameters.items():
                        params.append(f"{k}: {v}")
                if hasattr(run.overriding_parameters, 'notebook_params') and run.overriding_parameters.notebook_params:
                    for k, v in run.overriding_parameters.notebook_params.items():
                        params.append(f"{k}: {v}")
                if hasattr(run.overriding_parameters, 'python_named_params') and run.overriding_parameters.python_named_params:
                    for k, v in run.overriding_parameters.python_named_params.items():
                        params.append(f"{k}: {v}")
                if hasattr(run.overriding_parameters, 'python_params') and run.overriding_parameters.python_params:
                    for param in run.overriding_parameters.python_params:
                        params.append(str(param))
            
            run_params = ", ".join(params) if params else "None"
            
            # Format duration
            duration = ""
            if hasattr(run, 'execution_duration') and run.execution_duration:
                duration = f"{run.execution_duration // 1000}s"
            elif hasattr(run, 'start_time') and hasattr(run, 'end_time') and run.start_time and run.end_time:
                duration_ms = run.end_time - run.start_time
                duration = f"{duration_ms // 1000}s"
            
            # Format start time
            start_time = ""
            if hasattr(run, 'start_time') and run.start_time:
                start_time = datetime.datetime.fromtimestamp(run.start_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            
            # Get status from API response structure
            status = "Unknown"
            error_code = ""
            
            # First try run.status.state (main status field)
            if hasattr(run, 'status') and run.status:
                if hasattr(run.status, 'state') and run.status.state:
                    status = get_string_value(run.status.state)
                    
                    # For TERMINATING or TERMINATED, get termination details
                    if status in ["TERMINATING", "TERMINATED"]:
                        if hasattr(run.status, 'termination_details') and run.status.termination_details:
                            if hasattr(run.status.termination_details, 'code') and run.status.termination_details.code:
                                termination_code = get_string_value(run.status.termination_details.code)
                                # Use termination code as status for terminated runs
                                if termination_code in ["SUCCESS", "FAILED", "CANCELED", "TIMEOUT"]:
                                    status = termination_code
                                    # Only show error code if it's actually an error (not SUCCESS)
                                    if termination_code != "SUCCESS":
                                        error_code = termination_code
                                else:
                                    # Unknown termination codes go to error code
                                    error_code = termination_code
                            elif hasattr(run.status.termination_details, 'message') and run.status.termination_details.message:
                                error_code = get_string_value(run.status.termination_details.message)
            
            # Fallback to run.state.life_cycle_state if status not available  
            if status == "Unknown" and hasattr(run, 'state') and run.state:
                if hasattr(run.state, 'life_cycle_state') and run.state.life_cycle_state:
                    status = get_string_value(run.state.life_cycle_state)
                    
                    # For TERMINATED state, check result_state for more detailed status
                    if status == "TERMINATED" and hasattr(run.state, 'result_state') and run.state.result_state:
                        result_state = get_string_value(run.state.result_state)
                        # Use result_state for terminated runs (SUCCESS, FAILED, etc.)
                        if result_state in ["SUCCESS", "FAILED", "CANCELED", "TIMEOUT"]:
                            status = result_state
                            # Only show error code if it's actually an error (not SUCCESS)
                            if result_state != "SUCCESS":
                                error_code = result_state
                
                # Get state message as error code if no other error code found and run failed
                if not error_code and status not in ["SUCCESS", "RUNNING", "PENDING"] and hasattr(run.state, 'state_message') and run.state.state_message:
                    error_code = get_string_value(run.state.state_message)
            
            run_data.append({
                "Start time": start_time,
                "Run ID": getattr(run, 'run_id', 'N/A'),
                "Launched": "Manually",  # Most runs will be manual
                "Duration": duration,
                "Status": status,
                "Error code": error_code,
                "Run parameters": run_params
            })
        
        # Display as dataframe
        df = pd.DataFrame(run_data)
        st.dataframe(df, use_container_width=True)
        
        # Load More button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Load More Runs", key="load_more_runs"):
                # Load next batch
                more_runs = get_job_runs_batch(
                    selected_job.job_id, 
                    limit=5, 
                    offset=st.session_state.runs_offset
                )
                if more_runs:
                    st.session_state.all_runs.extend(more_runs)
                    st.session_state.runs_offset += 5
                    st.rerun()
                else:
                    st.info("No more runs to load.")
