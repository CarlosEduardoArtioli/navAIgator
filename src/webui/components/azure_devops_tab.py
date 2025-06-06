"""
Azure DevOps integration tab component for retrieving user stories.
"""

import os
import logging
import gradio as gr
import re
from datetime import datetime
from typing import Dict, Any, Optional
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def clean_html_description(html_text: str) -> str:
    """
    Clean HTML tags from description and format properly.
    """
    if not html_text:
        return "No description"
    
    # Remove HTML tags but keep content
    clean_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Convert HTML entities
    clean_text = clean_text.replace('&quot;', '"')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&nbsp;', ' ')
    
    # Clean up extra whitespace and line breaks
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = clean_text.strip()
    
    return clean_text


def fetch_user_story(organization: str, project: str, pat: str, story_id: str) -> tuple[str, str]:
    """
    Fetch user story from Azure DevOps using the official SDK.
    Returns tuple of (formatted_result, clean_description)
    """
    if not organization or not project or not pat or not story_id:
        return "Error: All fields are required (Organization, Project, PAT, Story ID)", ""
    
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        
        # Validate story ID is a number
        work_item_id = int(story_id)
        
        # Create connection
        credentials = BasicAuthentication('', pat)
        organization_url = f'https://dev.azure.com/{organization}'
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Get work item
        work_item = wit_client.get_work_item(work_item_id, expand='relations')
        
        # Format the response
        fields = work_item.fields
        
        # Extract key information
        title = fields.get('System.Title', 'N/A')
        work_item_type = fields.get('System.WorkItemType', 'N/A')
        state = fields.get('System.State', 'N/A')
        assigned_to = fields.get('System.AssignedTo', {}).get('displayName', 'Unassigned') if fields.get('System.AssignedTo') else 'Unassigned'
        description = fields.get('System.Description', 'No description')
        acceptance_criteria = fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', 'No acceptance criteria')
        story_points = fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 'Not set')
        priority = fields.get('Microsoft.VSTS.Common.Priority', 'Not set')
        created_date = fields.get('System.CreatedDate', 'N/A')
        changed_date = fields.get('System.ChangedDate', 'N/A')
        tags = fields.get('System.Tags', 'No tags')
        
        # Clean the description
        clean_description = clean_html_description(description)
        
        # Format result
        result = f"""
=== USER STORY #{work_item_id} ===
Title: {title}
Type: {work_item_type}
State: {state}
Assigned To: {assigned_to}
Priority: {priority}
Story Points: {story_points}

Description:
{clean_description}

Acceptance Criteria:
{acceptance_criteria}

Tags: {tags}

Created: {created_date}
Last Modified: {changed_date}

Azure DevOps URL: {work_item.url}
"""
        return result.strip(), clean_description
        
    except ImportError:
        return "Error: azure-devops library not installed. Run: pip install azure-devops", ""
    except ValueError:
        return "Error: Story ID must be a number", ""
    except Exception as e:
        logger.error(f"Error fetching work item: {e}")
        return f"Error: {str(e)}", ""


def upload_attachment_to_azure_devops(organization: str, project: str, pat: str, file_path: str, file_name: str) -> str:
    """
    Upload attachment to Azure DevOps and return the attachment URL.
    """
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        import os
        
        # Validate file exists and has content
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return ""
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"File is empty: {file_path}")
            return ""
            
        logger.info(f"Uploading file: {file_path} (size: {file_size} bytes)")
        
        credentials = BasicAuthentication('', pat)
        organization_url = f'https://dev.azure.com/{organization}'
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Upload attachment with correct parameters: upload_stream, project, file_name
        with open(file_path, 'rb') as file_data:
            logger.info(f"Calling create_attachment for {file_name} in project {project}")
            attachment = wit_client.create_attachment(file_data, project, file_name)
            logger.info(f"Upload successful. URL: {attachment.url}")
            return attachment.url
            
    except Exception as e:
        logger.error(f"Error uploading attachment {file_path}: {e}", exc_info=True)
        return ""


def update_work_item_with_attachment(organization: str, project: str, pat: str, work_item_id: int, attachment_url: str, comment: str = "Additional attachment") -> bool:
    """
    Add an attachment to an existing work item.
    """
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        
        credentials = BasicAuthentication('', pat)
        organization_url = f'https://dev.azure.com/{organization}'
        connection = Connection(base_url=organization_url, creds=credentials)
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Create JSON patch document to add attachment
        patch_document = [
            {
                'op': 'add',
                'path': '/relations/-',
                'value': {
                    'rel': 'AttachedFile',
                    'url': attachment_url,
                    'attributes': {
                        'comment': comment
                    }
                }
            }
        ]
        
        # Update work item with attachment
        updated_work_item = wit_client.update_work_item(patch_document, work_item_id, project)
        logger.info(f"Successfully added attachment to work item {work_item_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding attachment to work item {work_item_id}: {e}", exc_info=True)
        return False


def create_work_item_with_attachments(organization: str, project: str, pat: str, 
                                    input_text: str, output_text: str, 
                                    gif_path: Optional[str] = None, history_path: Optional[str] = None,
                                    parent_work_item_id: Optional[str] = None) -> str:
    """
    Create a work item in Azure DevOps with test execution results.
    """
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        import tempfile
        import os
        from datetime import datetime
        
        credentials = BasicAuthentication('', pat)
        organization_url = f'https://dev.azure.com/{organization}'
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Determine execution status from output text
        execution_failed = ("Failed/Cancelled" in output_text or 
                           "Execution failed" in output_text or 
                           "was cancelled" in output_text or
                           "Error:" in output_text)
        
        status_text = "failed" if execution_failed else "completed successfully"
        status_emoji = "❌" if execution_failed else "✅"
        
        # Create brief description (without full output to avoid size limit)
        brief_description = f'''
<h3>Input Task:</h3>
<p>{input_text}</p>

<h3>Execution Summary:</h3>
<p>{status_emoji} Agent execution {status_text}. Detailed output and results are available in the attached files.</p>

<h3>Attached Files:</h3>
<ul>
<li><strong>agent_output.txt</strong> - Complete execution output and summary</li>
<li><strong>agent_history.json</strong> - Full chat history and execution data</li>
<li><strong>execution_recording.gif</strong> - Screen recording (if available)</li>
</ul>

<h3>Execution Details:</h3>
<p>Executed by navAIgator Test Navigator</p>
<p>Status: {status_text.title()}</p>
<p>Timestamp: {str(datetime.now())}</p>
'''
        
        # Prepare work item document with required fields
        work_item = [
            {
                'op': 'add',
                'path': '/fields/System.Title',
                'value': f'Test Execution Results - {input_text[:50]}...'
            },
            {
                'op': 'add',
                'path': '/fields/System.WorkItemType',
                'value': 'Task'
            },
            {
                'op': 'add',
                'path': '/fields/System.Description',
                'value': brief_description
            },
            {
                'op': 'add',
                'path': '/fields/Microsoft.VSTS.Common.Priority',
                'value': 2  # Medium priority (1=High, 2=Medium, 3=Low, 4=Very Low)
            },
            {
                'op': 'add',
                'path': '/fields/System.State',
                'value': 'New'  # Initial state
            },
            {
                'op': 'add',
                'path': '/fields/Microsoft.VSTS.Common.Activity',
                'value': 'Development'  # Default activity for Task
            }
        ]
        
        # Create work item with error handling for different project templates
        try:
            created_item = wit_client.create_work_item(
                document=work_item, 
                project=project, 
                type='Task'
            )
        except Exception as create_error:
            # If creation fails, try with minimal required fields
            logger.warning(f"Failed to create work item with full fields: {create_error}")
            logger.info("Attempting to create with minimal fields...")
            
            minimal_work_item = [
                {
                    'op': 'add',
                    'path': '/fields/System.Title',
                    'value': f'Test Execution Results - {input_text[:50]}...'
                },
                {
                    'op': 'add',
                    'path': '/fields/System.Description',
                    'value': brief_description
                }
            ]
            
            # Try different priority values if the first attempt fails
            for priority_value in [2, 1, 3]:
                try:
                    test_work_item = minimal_work_item + [
                        {
                            'op': 'add',
                            'path': '/fields/Microsoft.VSTS.Common.Priority',
                            'value': priority_value
                        }
                    ]
                    created_item = wit_client.create_work_item(
                        document=test_work_item,
                        project=project,
                        type='Task'
                    )
                    break  # Success, exit the loop
                except:
                    continue  # Try next priority value
            else:
                                 # If all priority values fail, try without priority
                 try:
                     created_item = wit_client.create_work_item(
                         document=minimal_work_item,
                         project=project,
                         type='Task'
                     )
                 except:
                     # Try with different work item types
                     for work_item_type in ['User Story', 'Bug', 'Issue']:
                         try:
                             created_item = wit_client.create_work_item(
                                 document=minimal_work_item,
                                 project=project,
                                 type=work_item_type
                             )
                             logger.info(f"Successfully created {work_item_type} work item")
                             break
                         except:
                             continue
                     else:
                         # If all else fails, re-raise the original error
                         raise create_error
        
        work_item_id = created_item.id
        logger.info(f"Created work item #{work_item_id} successfully")
        
        attachments_added = []
        
        # Create and upload output file
        try:
            # Create temporary file for output
            temp_dir = tempfile.gettempdir()
            output_filename = f"agent_output_{work_item_id}.txt"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Write output to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Agent Execution Output\n")
                f.write(f"=====================\n\n")
                f.write(f"Input Task: {input_text}\n\n")
                f.write(f"Output:\n")
                f.write(f"-------\n")
                f.write(output_text)
                f.write(f"\n\nTimestamp: {str(datetime.now())}")
            
            logger.info(f"Created output file: {output_path}")
            
            # Upload output file
            output_url = upload_attachment_to_azure_devops(organization, project, pat, output_path,
                                                         f"agent_output_{work_item_id}.txt")
            logger.info(f"Upload result for output file: {output_url}")
            
            if output_url:
                # Add Output attachment to work item
                attachment_doc = [
                    {
                        'op': 'add',
                        'path': '/relations/-',
                        'value': {
                            'rel': 'AttachedFile',
                            'url': output_url,
                            'attributes': {
                                'comment': 'Agent execution output and summary'
                            }
                        }
                    }
                ]
                wit_client.update_work_item(document=attachment_doc, id=work_item_id)
                attachments_added.append("Output TXT")
                logger.info(f"Output file attachment added to work item {work_item_id}")
            else:
                logger.error("Failed to upload output file - no URL returned")
            
            # Clean up temp file
            try:
                os.remove(output_path)
                logger.info(f"Cleaned up temp file: {output_path}")
            except Exception as cleanup_error:
                logger.warning(f"Could not cleanup temp file: {cleanup_error}")
                
        except Exception as e:
            logger.error(f"Error creating/uploading output file: {e}", exc_info=True)
        
        # Upload GIF if provided
        if gif_path and os.path.exists(gif_path):
            try:
                logger.info(f"Uploading GIF: {gif_path}")
                gif_url = upload_attachment_to_azure_devops(organization, project, pat, gif_path,
                                                       f"execution_recording_{work_item_id}.gif")
                logger.info(f"Upload result for GIF: {gif_url}")
                if gif_url:
                    # Add GIF attachment to work item
                    attachment_doc = [
                        {
                            'op': 'add',
                            'path': '/relations/-',
                            'value': {
                                'rel': 'AttachedFile',
                                'url': gif_url,
                                'attributes': {
                                    'comment': 'Test execution recording (GIF)'
                                }
                            }
                        }
                    ]
                    wit_client.update_work_item(document=attachment_doc, id=work_item_id)
                    attachments_added.append("GIF")
                    logger.info(f"GIF attachment added to work item {work_item_id}")
                else:
                    logger.error("Failed to upload GIF - no URL returned")
            except Exception as e:
                logger.error(f"Error uploading GIF: {e}", exc_info=True)
        else:
            logger.info(f"No GIF to upload. Path: {gif_path}, Exists: {os.path.exists(gif_path) if gif_path else False}")
        
        # Upload History JSON if provided
        if history_path and os.path.exists(history_path):
            try:
                logger.info(f"Uploading History JSON: {history_path}")
                history_url = upload_attachment_to_azure_devops(organization, project, pat, history_path,
                                                           f"agent_history_{work_item_id}.json")
                logger.info(f"Upload result for History JSON: {history_url}")
                if history_url:
                    # Add History attachment to work item
                    attachment_doc = [
                        {
                            'op': 'add',
                            'path': '/relations/-',
                            'value': {
                                'rel': 'AttachedFile',
                                'url': history_url,
                                'attributes': {
                                    'comment': 'Agent execution history (JSON)'
                                }
                            }
                        }
                    ]
                    wit_client.update_work_item(document=attachment_doc, id=work_item_id)
                    attachments_added.append("History JSON")
                    logger.info(f"History JSON attachment added to work item {work_item_id}")
                else:
                    logger.error("Failed to upload History JSON - no URL returned")
            except Exception as e:
                logger.error(f"Error uploading history: {e}", exc_info=True)
        else:
            logger.info(f"No History JSON to upload. Path: {history_path}, Exists: {os.path.exists(history_path) if history_path else False}")
        
        # Link to parent work item if provided
        if parent_work_item_id:
            try:
                logger.info(f"Linking work item {work_item_id} to parent {parent_work_item_id}")
                
                # Create parent-child relationship
                relation_doc = [
                    {
                        'op': 'add',
                        'path': '/relations/-',
                        'value': {
                            'rel': 'System.LinkTypes.Hierarchy-Reverse',  # Child relationship
                            'url': f'{organization_url}/_apis/wit/workItems/{parent_work_item_id}',
                            'attributes': {
                                'comment': f'Child task created by navAIgator for test execution'
                            }
                        }
                    }
                ]
                
                wit_client.update_work_item(document=relation_doc, id=work_item_id)
                logger.info(f"Successfully linked work item {work_item_id} to parent {parent_work_item_id}")
                parent_info = f" and linked to parent #{parent_work_item_id}"
                
            except Exception as e:
                logger.error(f"Error linking to parent work item: {e}", exc_info=True)
                parent_info = f" (failed to link to parent #{parent_work_item_id})"
        else:
            parent_info = ""
        
        attachment_info = f" with {', '.join(attachments_added)} attachments" if attachments_added else ""
        return f"✅ Work item #{work_item_id} created successfully in Azure DevOps{attachment_info}{parent_info}!"
        
    except ImportError:
        return "❌ Error: azure-devops library not installed"
    except Exception as e:
        logger.error(f"Error creating work item: {e}")
        return f"❌ Error creating work item: {str(e)}"


def test_connection(organization: str, project: str, pat: str) -> str:
    """
    Test connection to Azure DevOps.
    """
    if not organization or not project or not pat:
        return "Error: Organization, Project, and PAT are required"
    
    try:
        from azure.devops.connection import Connection
        from msrest.authentication import BasicAuthentication
        
        # Create connection
        credentials = BasicAuthentication('', pat)
        organization_url = f'https://dev.azure.com/{organization}'
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Try to get projects to test connection
        core_client = connection.clients.get_core_client()
        projects = core_client.get_projects()
        
        return "✅ Connection successful!"
        
    except ImportError:
        return "Error: azure-devops library not installed. Run: pip install azure-devops"
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return f"❌ Connection failed: {str(e)}"


def create_azure_devops_tab(webui_manager: WebuiManager):
    """
    Create the Azure DevOps integration tab.
    """
    tab_components = {}
    
    with gr.Column():
        # Header
        gr.Markdown(
            """
            ### Azure DevOps Integration
            
            Connect to Azure DevOps to retrieve user story information using your Personal Access Token (PAT).
            
            **Setup Instructions:**
            1. Go to Azure DevOps → User Settings → Personal Access Tokens
            2. Create a new token with "Work Items (Read)" permission
            3. Enter your organization name, project name, and PAT below
            """,
            elem_classes=["tab-header-text"],
        )
        
        # Configuration section
        with gr.Group():
            gr.Markdown("#### Connection Settings")
            with gr.Row():
                organization = gr.Textbox(
                    label="Organization",
                    placeholder="your-organization-name",
                    info="Azure DevOps organization name (from URL: dev.azure.com/your-organization-name)"
                )
                project = gr.Textbox(
                    label="Project",
                    placeholder="your-project-name",
                    info="Project name within your organization"
                )
            
            pat = gr.Textbox(
                label="Personal Access Token",
                type="password",
                placeholder="Enter your PAT here",
                info="PAT with 'Work Items (Read)' permission"
            )
            
            with gr.Row():
                test_button = gr.Button(
                    "🔍 Test Connection",
                    variant="secondary",
                    size="sm"
                )
        
        # User Story section
        with gr.Group():
            gr.Markdown("#### Fetch User Story")
            with gr.Row():
                story_id = gr.Textbox(
                    label="User Story ID",
                    placeholder="Enter user story number (e.g., 1234)",
                    info="The ID number of the user story to retrieve"
                )
                fetch_button = gr.Button(
                    "📥 Fetch User Story",
                    variant="primary"
                )
        
        # Auto-send Results Configuration  
        with gr.Group():
            gr.Markdown("#### Auto-send Agent Results")
            auto_send_enabled = gr.Checkbox(
                label="📤 Auto-send Agent Results to Azure DevOps",
                value=False,
                info="Automatically create a work item when agent execution finishes"
            )
            
        # Status and Results section
        with gr.Group():
            status = gr.Textbox(
                label="Status",
                placeholder="Status messages will appear here",
                interactive=False,
                lines=1
            )
            
            with gr.Row():
                clear_button = gr.Button(
                    "🗑️ Clear Results",
                    variant="secondary",
                    size="sm"
                )
                
            result = gr.Textbox(
                label="User Story Details",
                placeholder="User story information will appear here after fetching",
                interactive=False,
                lines=20,
                max_lines=30
            )
    
    # Register components
    tab_components.update({
        "organization": organization,
        "project": project,
        "pat": pat,
        "story_id": story_id,
        "status": status,
        "result": result,
        "fetch_button": fetch_button,
        "test_button": test_button,
        "clear_button": clear_button,
        "auto_send_enabled": auto_send_enabled,
    })
    
    webui_manager.add_components("azure_devops", tab_components)
    
    # Event handlers
    def handle_test_connection(org, proj, token):
        """Handle test connection button click."""
        status_msg = test_connection(org, proj, token)
        return status_msg
    
    def handle_fetch_story(org, proj, token, story):
        """Handle fetch user story button click."""
        if not org or not proj or not token or not story:
            return "Error: All fields are required", ""
        
        result_text, clean_description = fetch_user_story(org, proj, token, story)
        if result_text.startswith("Error:"):
            return result_text, ""
        else:
            # Store the parent work item ID for later linking
            webui_manager.azure_devops_parent_work_item_id = story
            logger.info(f"Stored parent work item ID: {story}")
            return f"Successfully retrieved user story #{story}", result_text
    
    def handle_clear():
        """Handle clear button click."""
        return "", ""
    
    def handle_auto_send_change(enabled):
        """Handle auto-send checkbox change."""
        # Store the setting in webui_manager for later access
        webui_manager.azure_devops_auto_send = enabled
        logger.info(f"Azure DevOps auto-send set to: {enabled}")
        return enabled
    
    # Set up event handlers
    test_button.click(
        fn=handle_test_connection,
        inputs=[organization, project, pat],
        outputs=[status]
    )
    
    fetch_button.click(
        fn=handle_fetch_story,
        inputs=[organization, project, pat, story_id],
        outputs=[status, result]
    )
    
    clear_button.click(
        fn=handle_clear,
        inputs=[],
        outputs=[status, result]
    )
    
    auto_send_enabled.change(
        fn=handle_auto_send_change,
        inputs=[auto_send_enabled],
        outputs=[]
    ) 