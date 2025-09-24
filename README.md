# Databricks Workflows Launcher 🚀

A comprehensive Streamlit-based Databricks app for triggering and monitoring Databricks workflow jobs with custom parameters and provenance tracking.

## How to get started
- Install databricks cli and configure your workspace authentication see here: https://docs.databricks.com/en/dev-tools/cli/install.html
- Create your app: databricks apps create trigger_job_app
- Sync the files with the workspace: databricks sync --watch . /Workspace/Users/<username>/App/trigger_job_app (you can keep this command in a side window if you want to sync continously)
- Deploy: databricks apps deploy slack-bot --source-code-path=/Workspace/Users/<username>/App/slack-bot 
- Access the Apps URL and play with it.


https://github.com/user-attachments/assets/b84f62e5-afd0-4f3b-bdd9-e6ba3e1e0b1f


## Features

- **Job Discovery**: List and browse all available Databricks jobs in your workspace
- **Parameter Management**: Add, remove, and customize job parameters with support for multiple parameter types
- **Provenance Tracking**: Mandatory email tracking for job triggers with validation
- **Multi-Task Support**: Handle complex workflows with task-specific parameters
- **Run Monitoring**: Track job execution status and history
- **User-Friendly UI**: Intuitive interface with navigation between trigger and status pages

## Screenshots

### Job Trigger Page
- Select from available jobs with ID and name display
- Dynamic parameter editors based on job task types
- Support for job_parameters, notebook_params, python_params, sql_params, and more
- Mandatory triggered_by email validation

### Run Status Page
- Monitor job execution history
- Track run statuses and durations
- View detailed run information

## Prerequisites

### Databricks Workspace Requirements
- Databricks workspace with Jobs API access
- Databricks SDK for Python configured with proper authentication

### Permissions Requirements ⚠️

**CRITICAL**: This app requires specific permissions to function properly:

#### Option 1: Admin Access (Recommended for Development)
Grant **Admin** privileges to the App Service Principal for full workspace access.

#### Option 2: Job-Specific Permissions (Production)
For each job you want to trigger, grant the App Service Principal:
- **CAN MANAGE RUN** permission on the specific job

**How to set job permissions:**
1. Navigate to your Databricks job in the UI
2. Click on "Permissions" tab
3. Add your App Service Principal with "CAN MANAGE RUN" permission
4. Repeat for each job you want the app to access

See [Control access to a job](https://docs.databricks.com/en/jobs/privileges.html#control-access-to-a-job) for detailed information.


## Project Structure

```
trigger_job_app/
├── app.py                 # Main application with navigation
├── app.yaml              # Databricks app configuration
├── components/           
│   ├── __init__.py
│   ├── trigger_job.py    # Job triggering functionality
│   └── run_status.py     # Run status monitoring
├── utils.py              # Shared utility functions
├── requirements.txt      # Python dependencies
└── README.md
```

## Usage

### Triggering a Job

1. **Select Job**: Choose from the dropdown list of available jobs
2. **Configure Parameters**: 
   - Select parameter style based on your job type
   - Add/edit parameters using the dynamic editor
   - **Required**: Fill in `triggered_by` with a valid email address
3. **Optional Task Selection**: Choose specific tasks to run (for multi-task jobs)
4. **Trigger**: Click "Trigger job" to execute

### Parameter Types Supported

| Parameter Type | Description | Format |
|----------------|-------------|--------|
| `job_parameters` | Job-level parameters (Jobs 2.1) | Key-value map |
| `notebook_params` | Notebook task parameters | Key-value map |
| `python_params` | Python script parameters | List of strings |
| `python_named_params` | Named Python parameters | Key-value map |
| `sql_params` | SQL task parameters | Key-value map |
| `jar_params` | Spark JAR parameters | List of strings |
| `spark_submit_params` | Spark Submit parameters | List of strings |
| `dbt_commands` | DBT task commands | List of strings |

### Monitoring Runs

Navigate to the "RUN STATUS" page to:
- View recent job runs
- Monitor execution status
- Check run durations and results

## API Reference

This app uses the [Databricks Jobs API](https://docs.databricks.com/api/workspace/jobs) with the following key endpoints:

- `jobs.list()` - List available jobs
- `jobs.get(job_id)` - Get job details and configuration
- `jobs.run_now(job_id, **parameters)` - Trigger job execution
- `jobs.get_run(run_id)` - Get run status and details

## Configuration

### App Configuration (app.yaml)

```yaml
command: [
  "streamlit", 
  "run",
  "app.py"
]
```

## Development

### Running Locally
```bash
streamlit run app.py
```

### Adding New Features
1. Create components in the `components/` directory
2. Update navigation in `app.py`
3. Add shared utilities to `utils.py`

### Error Handling
The app includes comprehensive error handling for:
- Missing permissions
- Invalid parameters
- API failures
- Email validation

## Security Considerations

- **Email Validation**: All job triggers require valid email for provenance
- **Permission Validation**: App validates job access before attempting triggers
- **Parameter Sanitization**: Input validation for all parameter types
- **Audit Trail**: All triggers include metadata for tracking

## Troubleshooting

### Common Issues

#### Permission Denied
```
Error: User does not have permission to run job
```
**Solution**: Ensure the App Service Principal has `CAN MANAGE RUN` permission on the target job.


#### No Jobs Visible
**Solution**: Check that:
1. Jobs exist in your workspace
2. App Service Principal has appropriate permissions
3. Authentication is working correctly


## Dependencies

- **[Databricks SDK for Python](https://pypi.org/project/databricks-sdk/)** - `databricks-sdk`
- **[Streamlit](https://pypi.org/project/streamlit/)** - `streamlit` 
- **[Pandas](https://pypi.org/project/pandas/)** - `pandas`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review [Databricks Jobs API documentation](https://docs.databricks.com/api/workspace/jobs)
3. Open an issue in this repository

---

**⚠️ Important**: Always ensure proper permissions are set up before deploying to production. Lack of proper job permissions will result in runtime errors when attempting to trigger workflows.
