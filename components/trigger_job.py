"""
Trigger Job page functionality
"""
import streamlit as st
from databricks.sdk import WorkspaceClient
from utils import job_label

def show_trigger_job_page(w: WorkspaceClient):
    """
    Display the trigger job page
    """
    st.subheader("Run a job")
    st.write(
        "Trigger a Databricks Workflows job with custom parameters and provenance metadata. "
        "Requires appropriate job permissions (for example, CAN MANAGE RUN)."
    )

    # --- Fetch jobs ---
    @st.cache_data(ttl=60)
    def list_jobs():
        # SDK list supports expand_tasks, pagination helpers.
        return list(w.jobs.list(expand_tasks=True))

    all_jobs = list_jobs()
    jobs_for_display = all_jobs

    # --- Job selector ---
    st.markdown("### Select a job")
    if not jobs_for_display:
        st.info("No jobs found.")
        st.stop()

    selected = st.selectbox(
        "Job",
        options=jobs_for_display,
        format_func=job_label,
    )

    # --- Load base parameters for the job (if any) and detect task types ---
    @st.cache_data(ttl=60)
    def get_job_details(job_id: int):
        return w.jobs.get(job_id=job_id)

    job_details = get_job_details(selected.job_id)

    # Collect job-level parameters (Jobs 2.1 'job_parameters') and per-task parameter style hints
    base_job_params = dict(getattr(job_details.settings, "job_parameters", {}) or {})

    # Determine allowed param flavors based on tasks in job
    task_param_modes = set()
    for t in job_details.settings.tasks or []:
        if hasattr(t, 'notebook_task') and getattr(t, 'notebook_task') is not None:
            task_param_modes.add("notebook_params")
        if hasattr(t, 'python_task') and getattr(t, 'python_task') is not None:
            # python_task supports python_params (list) or python_named_params (map) at run-now time
            task_param_modes.add("python_params")
            task_param_modes.add("python_named_params")
        if hasattr(t, 'spark_jar_task') and getattr(t, 'spark_jar_task') is not None:
            task_param_modes.add("jar_params")
        if hasattr(t, 'spark_submit_task') and getattr(t, 'spark_submit_task') is not None:
            task_param_modes.add("spark_submit_params")
        if hasattr(t, 'sql_task') and getattr(t, 'sql_task') is not None:
            task_param_modes.add("sql_params")
        if hasattr(t, 'python_wheel_task') and getattr(t, 'python_wheel_task') is not None:
            task_param_modes.add("python_named_params")
        if hasattr(t, 'dbt_task') and getattr(t, 'dbt_task') is not None:
            task_param_modes.add("dbt_commands")

    st.markdown("### Parameters")
    st.caption(
        "Provide job-level parameters or task-type-specific parameters (notebook_params, python_params, sql_params, etc.). "
        "The 'triggered_by' parameter is required and must contain a valid email address. "
        "Some parameter types are mutually exclusive at run time; use only the ones required by this job."
    )

    # Choose parameter style
    param_style = st.selectbox(
        "Parameter style",
        options=["job_parameters"] + sorted(task_param_modes),
        help="Pick which parameter field to send in run-now. For notebooks use notebook_params (map). For Python files use python_params (list) or python_named_params (map)."
    )

    # Editor based on style
    def draw_map_editor(title: str, initial: dict[str, str]):
        st.write(title)
        # Represent as simple key-value pairs
        kv = {}
        rows = st.session_state.get(f"{title}_rows", list(initial.items()) or [("", "")])
        # Render rows
        new_rows = []
        for idx, (k, v) in enumerate(rows):
            c1, c2, c3 = st.columns([4, 6, 1])
            with c1:
                nk = st.text_input(f"Key {idx+1}", value=k, key=f"{title}_key_{idx}")
            with c2:
                placeholder = "user@example.com" if nk == "triggered_by" else ""
                nv = st.text_input(f"Value {idx+1}", value=v, key=f"{title}_val_{idx}", placeholder=placeholder)
            with c3:
                if st.button("🗑️", key=f"{title}_del_{idx}"):
                    continue
            new_rows.append((nk, nv))
        st.session_state[f"{title}_rows"] = new_rows
        if st.button("➕ Add row", key=f"{title}_add"):
            st.session_state[f"{title}_rows"].append(("", ""))
        # Build dict
        for k, v in st.session_state[f"{title}_rows"]:
            if k:
                kv[k] = v
        return kv

    def draw_list_editor(title: str, initial: list[str]):
        st.write(title)
        items = st.session_state.get(f"{title}_items", initial or [""])
        new_items = []
        for idx, it in enumerate(items):
            c1, c2 = st.columns([10, 1])
            with c1:
                placeholder = "--triggered_by=user@example.com" if it.startswith("--triggered_by=") and it.endswith("=") else ""
                new_val = st.text_input(f"Item {idx+1}", value=it, key=f"{title}_item_{idx}", placeholder=placeholder)
            with c2:
                if st.button("🗑️", key=f"{title}_del_{idx}"):
                    continue
            new_items.append(new_val)
        st.session_state[f"{title}_items"] = new_items
        if st.button("➕ Add item", key=f"{title}_add"):
            st.session_state[f"{title}_items"].append("")
        return [x for x in st.session_state[f"{title}_items"] if x]

    payload = {}
    if param_style == "job_parameters":
        # Preload with base job parameters and add empty triggered_by parameter
        initial = dict(base_job_params)
        initial.setdefault("triggered_by", "")
        edited = draw_map_editor("Job parameters (map)", initial)
        payload["job_parameters"] = edited

    elif param_style in ("notebook_params", "python_named_params", "sql_params"):
        initial = {}
        initial["triggered_by"] = ""
        edited = draw_map_editor(f"{param_style} (map)", initial)
        payload[param_style] = edited

    elif param_style in ("python_params", "jar_params", "spark_submit_params", "dbt_commands"):
        # Add empty triggered_by parameter as string
        initial = ["--triggered_by="]
        edited = draw_list_editor(f"{param_style} (list)", initial)
        payload[param_style] = edited

    # Optional: restrict to specific tasks inside a multi-task job
    task_keys = [t.task_key for t in (job_details.settings.tasks or []) if t.task_key]
    subset = st.multiselect("Run only selected task keys (optional)", task_keys)
    if subset:
        payload["tasks"] = subset  # Jobs 2.1 supports 'tasks' to run subset by keys

    # --- Trigger button ---
    st.markdown("### Trigger")
    col_t1, col_t2 = st.columns([1, 3])
    with col_t1:
        run_now = st.button("Trigger job", type="primary")
    with col_t2:
        st.caption("Runs immediately via Jobs run-now API.")

    if run_now:
        # Validate required triggered_by parameter
        triggered_by_value = None
        
        # Extract triggered_by value based on parameter style
        if param_style == "job_parameters" and "job_parameters" in payload:
            triggered_by_value = payload["job_parameters"].get("triggered_by", "")
        elif param_style in ("notebook_params", "python_named_params", "sql_params") and param_style in payload:
            triggered_by_value = payload[param_style].get("triggered_by", "")
        elif param_style in ("python_params", "jar_params", "spark_submit_params", "dbt_commands") and param_style in payload:
            # Look for --triggered_by=email in list parameters
            for param in payload[param_style]:
                if param.startswith("--triggered_by="):
                    triggered_by_value = param.split("=", 1)[1] if "=" in param else ""
                    break
        
        # Validate email is provided
        if not triggered_by_value or not triggered_by_value.strip():
            st.error("❌ Please fill in the 'triggered_by' parameter with a valid email address")
            st.stop()
        
        # Basic email validation
        if "@" not in triggered_by_value or "." not in triggered_by_value.split("@")[-1]:
            st.error("❌ Please provide a valid email address in the 'triggered_by' parameter")
            st.stop()
        
        try:
            # Validate ASCII for specific param types per API notes (e.g., python_params & spark_submit_params)
            # Rely on API to enforce; keep example simple.

            resp = w.jobs.run_now(
                job_id=selected.job_id,
                **payload
            )
            st.success("Workflow triggered successfully ✅")
            st.json({"run_id": resp.run_id})
        except Exception as e:
            st.error(f"Error triggering workflow: {e}")
