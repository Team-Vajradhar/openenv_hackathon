"""
Inference Script Example
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME The name of the local image to use for the environment if you are using from_docker_image()
                     method

- Defaults are set only for API_BASE_URL and MODEL_NAME 
    (and should reflect your active inference setup):
    API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
    MODEL_NAME = os.getenv("MODEL_NAME", "<your-active-model>")
    
- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

  Rules:
    - One [START] line at episode begin.
    - One [STEP] line per step, immediately after env.step() returns.
    - One [END] line after env.close(), always emitted (even on exception).
    - reward and rewards are formatted to 2 decimal places.
    - done and success are lowercase booleans: true or false.
    - error is the raw last_action_error string, or null if none.
    - All fields on a single line with no newlines within a line.
    - Each tasks should return score in [0, 1]

  Example:
    [START] task=click-test env=miniwob model=Qwen3-VL-30B
    [STEP] step=1 action=click('123') reward=0.00 done=false error=null
    [STEP] step=2 action=fill('456','text') reward=0.00 done=false error=null
    [STEP] step=3 action=click('789') reward=1.00 done=true error=null
    [END] success=true steps=3 score=1.00 rewards=0.00,0.00,1.00
"""

import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from models import IncidentResponseAction
from server.incident_response_env_environment import IncidentResponseEnvironment
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()

IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") # If you are using docker image 
API_KEY = os.getenv("HF_TOKEN") # or os.getenv("API_KEY")

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
TASK_NAME = os.getenv("INCIDENT_TASK", "easy_api_crash")
BENCHMARK = os.getenv("BENCHMARK", "incident_response_env")
MAX_STEPS = 8
TEMPERATURE = 0.2
MAX_TOKENS = 50
SUCCESS_SCORE_THRESHOLD = 0.1  # normalized score in [0, 1]

# Max possible reward: each token contributes 0.1, across all steps
_MAX_REWARD_PER_STEP = MAX_TOKENS * 0.1
MAX_TOTAL_REWARD = MAX_STEPS * _MAX_REWARD_PER_STEP

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an SRE responding to a production incident.

    Available actions:

    inspect_logs
    inspect_metrics
    restart_service
    scale_service
    resolve_incident

    Your goal is to investigate the issue and resolve the incident efficiently.

    Respond with ONLY one action from the list above.
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def build_user_prompt(alert: str, logs: str, metrics: dict, status: str, step: int) -> str:
    return textwrap.dedent(
        f"""
        Step: {step}
        Alert: {alert}
        Logs: {logs}
        Metrics:{metrics}
        Service Status:{status}
        
        Available actions:
        - inspect_logs
        - inspect_metrics
        - restart_service
        - resolve_incident
        - scale_service
        
        Choose the best next action.
        Reply with ONLY the action name.
        """
    ).strip()

def get_model_action(client: OpenAI, prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        text = completion.choices[0].message.content
        return text.strip() if text else "inspect_logs"

    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "inspect_logs"

def parse_action(text: str) -> IncidentResponseAction:
    text = text.lower()

    if "logs" in text:
        return IncidentResponseAction(action_type="inspect_logs")

    if "metrics" in text:
        return IncidentResponseAction(action_type="inspect_metrics")

    if "restart" in text:
        return IncidentResponseAction(action_type="restart_service")

    if "resolve" in text:
        return IncidentResponseAction(action_type="resolve_incident")

    return IncidentResponseAction(action_type="inspect_logs")

# def get_model_message(client: OpenAI, step: int, last_echoed: str, last_reward: float, history: List[str]) -> str:
#     user_prompt = build_user_prompt(step, last_echoed, last_reward, history)
#     try:
#         completion = client.chat.completions.create(
#             model=MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": user_prompt},
#             ],
#             temperature=TEMPERATURE,
#             max_tokens=MAX_TOKENS,
#             stream=False,
#         )
#         text = (completion.choices[0].message.content or "").strip()
#         return text if text else "hello"
#     except Exception as exc:
#         print(f"[DEBUG] Model request failed: {exc}", flush=True)
#         return "hello"


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = IncidentResponseEnvironment()
    
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = env.reset(task_name=TASK_NAME)

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            
            obs = result
            prompt = build_user_prompt(obs.alert,obs.logs,obs.metrics,obs.status,step)
            action_text = get_model_action(client, prompt)
            action = parse_action(action_text)
            result = env.step(action)

            reward = result.reward or 0.0
            done = result.done

            rewards.append(reward)
            steps_taken = step

            log_step(step, action_text, reward, done, None)

            if done:
                break

        # score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        # score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]
        score = rewards[-1] if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            # print(f"[DEBUG] env.close() error (container cleanup): {e}", flush=True)
            pass
        log_end(success, steps_taken, score, rewards)


if __name__ == "__main__":
    asyncio.run(main())