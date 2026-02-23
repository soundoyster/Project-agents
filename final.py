# <TODO: Step 3 - Imports>
# Complete the imports for all the necessary components from the semantic_kernel library.
import logging
import os
import sys
import io
import traceback
import pandas as pd
import asyncio
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatMessageContent

# -----------------
# Logging Setup
# -----------------
# The logging setup below captures all agent interactions and saves them to 'logs/agent_chat.log'.
# 1. Create a dedicated logger for agent interactions.
agent_logger = logging.getLogger("semantic_kernel.agents")
agent_logger.setLevel(logging.DEBUG)

# 2. Prevent agent logs from propagating to other handlers (like console).
agent_logger.propagate = False

# 3. Create a file handler to write to 'agent_chat.log' in write mode.
agent_chat_handler = logging.FileHandler("logs/agent_chat.log", mode='w')
agent_chat_handler.setLevel(logging.DEBUG)

# 4. Create a minimal formatter to log only the message content.
chat_formatter = logging.Formatter('%(asctime)s - %(name)s:%(message)s')
agent_chat_handler.setFormatter(chat_formatter)

# 5. Add the dedicated file handler to the agent logger.
agent_logger.addHandler(agent_chat_handler)

# 6. Function to log agent messages
def log_agent_message(content):
    try:
        agent_logger.info(f"Agent: {content.role} - {content.name or '*'}: {content.content}")
    except Exception:
        agent_logger.exception("Failed to write agent message to log")

# -----------------
# Environment Setup
# -----------------
# <TODO: Step 2 - Environment Setup>
# Load the API key and endpoint URL from the .env file.

load_dotenv()
api_key = os.getenv("AZURE_OPENAI_KEY")
url = os.getenv("URL")
api_version = "2024-12-01-preview"


# -----------------
# Kernel and Chat Service
# -----------------
# <TODO: Step 3 - Kernel Initialization>
# Initialize the Kernel, define the AzureChatCompletion service, and add it to the kernel.
kernel = Kernel()
chat_service = AzureChatCompletion(
    deployment_name="gpt-4.1-mini", 
    api_key=api_key,
    base_url=url,
    api_version=api_version,
)
kernel.add_service(chat_service)


# -----------------
# Helper Functions
# -----------------
# <TODO: Step 4 - Implement Supporting Logic>
# Implement the logic for each of the helper functions below.

def load_quality_instructions(file_path):
    """
    Loads instructional text from a file within the 'specs' directory.

    This function constructs the full path to the file, reads its content,
    and processes it into a list of non-empty, stripped lines.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings, where each string is a line of instruction.
                   Returns an empty list if the file does not exist.
    """
    full_path = os.path.join('specs', file_path)
    if not os.path.exists(full_path): return []
    with open(full_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_reports_instructions(file_path):
    """
    Loads report generation instructions from a file within the 'specs' directory.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings for building the report. Returns an
                   empty list if the file does not exist.
    """
    full_path = os.path.join('specs', file_path)
    if not os.path.exists(full_path): return []
    with open(full_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_logs(file_path):
    """
    Loads agent interaction logs from a file within the 'logs' directory.

    Args:
        file_path (str): The name of the log file in the 'logs' directory.
4
    Returns:
        list[str]: A list of log entries. Returns an empty list if the file
                   does not exist.
    """
    full_path = os.path.join('logs', file_path)
    if not os.path.exists(full_path): return []
    with open(full_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_csv_name():
    """
    Interactively prompts the user to select a CSV file from the 'data' directory.

    It lists all available .csv files and asks for a numerical selection.

    Returns:
        str: The relative path to the selected CSV file (e.g., 'data/my_file.csv').
    """
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"Error: The directory '{data_dir}' does not exist.")
        return None
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not files:
        print("No CSV files were found in the 'data' folder.")
        return None
    print("--- Data Selection ---")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    while True:
        try:
            choice = int(input("Select the file number: "))
            if 1 <= choice <= len(files):
                return os.path.join(data_dir, files[choice - 1])
            print(f"Number out of range (1-{len(files)}).")
        except ValueError:
            print("Invalid input. Please use numbers.")

def load_csv_file(file_path):
    """
    Reads a CSV file and converts its entire content into a single string.

    The CSV data is flattened into a list and then joined by ', '.

    Args:
        file_path (str): The path to the CSV file to load.

    Returns:
        str: A single string containing all the data from the CSV file.
    """
    if not os.path.exists(file_path): return ""
    df = pd.read_csv(file_path)
    flat_data = ", ".join(map(str, df.values.flatten()))
    return flat_data


class PythonExecutor:
    """
    A safe executor for dynamically generated Python code strings.

    This class is designed to run code provided by an AI agent in a controlled
    manner. It includes a retry mechanism and captures execution errors.
    """
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts

    def run(self, code):
        """
        Executes a string of Python code using the exec() function.

        Args:
            code (str): The Python code to execute.

        Returns:
            tuple[bool, str | None]: A tuple containing:
                - A boolean indicating if the execution was successful.
                - The error traceback as a string if an exception occurred,
                  otherwise None.
        """
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        try:
            exec(code, globals())
            sys.stdout = old_stdout
            return True, redirected_output.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            return False, traceback.format_exc()

def save_final_report(report, path='artifacts/final_report.md'):
    """
    Saves the generated final report to a markdown file.

    Args:
        report (str): The content of the report to be saved.
        path (str, optional): The file path for the saved report.
                              Defaults to 'artifacts/final_report.md'.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to {path}")


# -----------------
# Agent Instructions
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 1. Complete the AGENT_CONFIG with detailed prompts for each agent.
data_quality_instructions = ''.join(load_quality_instructions("Data_Quality_Instructions.txt"))
report_instructions = ''.join(load_reports_instructions("Report_Instructions.txt"))

AGENT_CONFIG = {
    "PythonExecutorAgent": (
        "Role: Senior Data Visualization Expert."
        "Task: Generate Python code to visualize data cleaning results."
        "Instructions:"
        "1. Plot Type: Create a SINGLE LINE CHART comparing 'Original' vs 'Cleaned' data."
        "2. Colors: Use 'blue' for Original data and 'green' for Cleaned data."
        "3. Directory: You MUST ensure the 'artifacts/' directory exists using 'os.makedirs'."
        "4. File Saving: Save the plot strictly to 'artifacts/data_visualization.png'."
        "5. Constraints: Output ONLY the raw Python code. Do not include markdown blocks, explanations, or comments."
        "6. Context: Use matplotlib and pandas. Do not use plt.show()."
    ),
    "DataCleaning": (
        "Role: Data Cleaning Assistant."
        "Behavior: Analyze the raw dataset, identify outliers (zeros or extreme anomalies), and produce a clean data list."
        "Format: Present the cleaning plan first, then the cleaned data."
        f"{data_quality_instructions}"
    ),
    "DataStatistics": (
        "Role: Data Statistics Assistant."
        "Behavior: Calculate Count, Mean, Median, Std Dev, Min, and Max for the cleaned data."
        "Format: Return ONLY the statistical summary as a structured list or table."
        f"{data_quality_instructions}"
    ),
    "AnalysisChecker": (
        "Role: Data Validation Auditor."
        "Behavior: Verify that outliers were correctly removed and statistics match the cleaned data."
        "Rule: If the process is accurate and matches the instructions, end your message with 'APPROVED'."
        f"{data_quality_instructions}"
    ),
    "ReportGenerator": (
        "Role: Professional Report Generator."
        "Behavior: Synthesize all agent logs into a professional Markdown report."
        "Structure: You must include 7 sections: 1. Overview, 2. Data Cleaning (with outlier list), "
        "3. Descriptive Statistics (table), 4. Validation Summary, 5. Data Visualization (reference the image), "
        "6. Conclusions, 7. Agent Workflow Summary."
        f"{report_instructions}"
    ),
    "ReportChecker": (
        "Role: Report Quality Auditor."
        "Behavior: Audit the report. Check for all 7 sections: 1.Overview, 2.Cleaning, 3.Stats, 4.Validation, 5.Visualization, 6.Conclusions, 7.Workflow Summary"
        "Rule: If complete and professional, end your response with 'APPROVED'."
        f"{report_instructions}"
    )
}


# -----------------
# Agent Factory
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 2. Implement the agent factory function.
def create_agent(name, instructions, service, temperature):
    """Factory function to create a new ChatCompletionAgent."""
    settings = OpenAIChatPromptExecutionSettings()
    settings.temperature = temperature
    return ChatCompletionAgent(
        kernel=kernel,
        service=service,
        name=name,
        instructions=instructions,
        arguments=KernelArguments(settings)
    )


# -----------------
# Termination Strategy
# -----------------
# A custom termination strategy that stops after user approval.
class ApprovalTerminationStrategy(TerminationStrategy):
    """A custom termination strategy that stops after user approval."""
    async def should_agent_terminate(self, agent, history):
        if "approved" in history[-1].content.lower():
            return True
        return False


# -----------------
# Agent Instantiation
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 3. Instantiate each agent with the correct name, prompt, and temperature setting.
python_agent = create_agent("PythonExecutorAgent", AGENT_CONFIG["PythonExecutorAgent"], chat_service, 0.1)
cleaning_agent = create_agent("DataCleaning", AGENT_CONFIG["DataCleaning"], chat_service, 0.7)
stats_agent = create_agent("DataStatistics", AGENT_CONFIG["DataStatistics"], chat_service, 0.5)
checker_agent = create_agent("AnalysisChecker", AGENT_CONFIG["AnalysisChecker"], chat_service, 0.2)
report_agent = create_agent("ReportGenerator", AGENT_CONFIG["ReportGenerator"], chat_service, 1.0)
report_checker_agent = create_agent("ReportChecker", AGENT_CONFIG["ReportChecker"], chat_service, 0.2)


# -----------------
# Group Chats
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 4. Create the three agent group chats.
analysis_chat = AgentGroupChat(
    agents=[cleaning_agent, stats_agent, checker_agent],
    termination_strategy=ApprovalTerminationStrategy(agents=[checker_agent], maximum_iterations=10)
)
code_chat = AgentGroupChat(
    agents=[python_agent],
    termination_strategy=ApprovalTerminationStrategy(agents=[python_agent], maximum_iterations=10)
)
report_chat = AgentGroupChat(
    agents=[report_agent, report_checker_agent],
    termination_strategy=ApprovalTerminationStrategy(agents=[report_checker_agent], maximum_iterations=5)
)


# -----------------
# Main Workflow
# -----------------
# <TODO: Step 6 - Orchestrate the Main Workflow>
# Implement the main workflow logic, following the sequence described in the instructions.
async def main():
    """The main entry point for the agentic workflow."""
    # 1. Load the CSV data.
    print("=== Phase 1:  Load the CSV data ===")
    csv_path = get_csv_name()
    if not csv_path: return
    raw_data = load_csv_file(csv_path)

    # 2. Invoke the analysis chat.
    print("=== Phase 2:  Invoke the analysis chat ===")
    await analysis_chat.add_chat_message(ChatMessageContent(role="user", content=f"Process this raw data: {raw_data}"))
    
    analysis_results = ""
    async for response in analysis_chat.invoke():
        print(f"[{response.name}]: {response.content}")
        log_agent_message(response)
        analysis_results += f"\{response.content}"


    # 3. Get human approval.
    print("=== Phase 3:  Get human approval ===")
    while True:
        user_input = input("Confirm data validity for visualization? (yes/no/feedback): ").lower().strip()

        if user_input == 'yes':
            print("Approval received. Proceeding to visualization...")
            break 
        elif user_input == 'no':
            print("Workflow terminated by user.")
            return
        elif user_input == 'feedback':
            feedback = input("What should the agents fix? (e.g., 'remove more outliers', 'check the mean'): ")
            print("Re-running analysis with your feedback...")
            await analysis_chat.add_chat_message(
                ChatMessageContent(role="user", content=f"The user rejected the previous results. Feedback: {feedback}. Please re-analyze.")
            )
        
            analysis_chat.is_complete = False
            analysis_results = ""
            async for response in analysis_chat.invoke():
                print(f"[{response.name}]: {response.content}")
                log_agent_message(response)
                analysis_results += f"{response.content}"
        else:
            print("Please only type 'yes' or 'no'.")
    
    # 4. Save the cleaned data.
    print("=== Phase 4:  Save the cleaned data. ===")
    os.makedirs('artifacts', exist_ok=True)
    with open('artifacts/cleaned_data_summary.txt', 'w') as f:
        f.write(analysis_results)
    
    print("data saved in: artifacts/cleaned_data_summary.txt")

    # 5. Invoke the code chat to generate and execute visualization code.
    print("=== Phase 5:  Invoke the code chat to generate and execute visualization code ===")
    await code_chat.add_chat_message(ChatMessageContent(role="user", content=f"Generate visualization code for this data summary: {analysis_results}"))
    
    executor = PythonExecutor(max_attempts=10)
    success = False
    attempts = 0

    # 6. Execute the code in a retry loop.
    print("=== Phase 6:  Execute the code in a retry loop ===")
    while not success and attempts < executor.max_attempts:
        attempts += 1
        code_response = None
        async for response in code_chat.invoke():
            code_response = response.content
            log_agent_message(response)
        
        # Clean markdown code blocks if present
        clean_code = code_response.replace("```python", "").replace("```", "").strip()
        
        success, exec_output = executor.run(clean_code)
        if success:
            print(f"Code executed successfully on attempt {attempts}.")
            with open('artifacts/visualization_script.py', 'w') as f:
                f.write(clean_code)
        else:
            print(f"Execution failed. Retrying... (Attempt {attempts})")
            await code_chat.add_chat_message(ChatMessageContent(role="user", content=f"Execution failed with error:\n{exec_output}\nPlease fix the code."))


    # 7. Save the working visualization script.
    print("=== Phase 7:  Save the working visualization script ===")

    logs_content = "\n".join(load_logs("agent_chat.log"))
    await report_chat.add_chat_message(ChatMessageContent(role="user", content=f"Generate the final report using these logs and artifacts:\n{logs_content}"))
    # 8. Invoke the report chat to generate the final report.
    print("=== Phase 8:  Invoke the report chat to generate the final report ===")

    final_report_content = ""
    async for response in report_chat.invoke():
        print(f"[{response.name}]: {response.content}")
        log_agent_message(response)
        if response.name == "ReportGenerator":
            final_report_content = response.content


    # 9. Save the final report.
    print("=== Phase 9:  Save the final report ===")

    save_final_report(final_report_content)
    print("=== Workflow Complete ===")


# -----------------
# Main Execution
# -----------------
if __name__ == "__main__":
    asyncio.run(main())