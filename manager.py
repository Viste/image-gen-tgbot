from celery import Celery

from misc.tasks import send_davinci
from misc.utils import config

app = Celery('manager', broker=config.celery_url, backend=config.celery_backend)
app.autodiscover_tasks()
app.conf.update(
    result_expires=3600,
    result_backend_transport_options={
      'retry_policy': {'timeout': 5.0},
    }
)
conversations = {}


def conversation_tracking(text_message, user_id):
    # Get the last 10 conversations and responses for this user
    user_conversations = conversations.get(user_id, {'conversations': [], 'responses': []})
    user_messages = user_conversations['conversations'][-9:] + [text_message]
    user_responses = user_conversations['responses'][-9:]

    # Store the updated conversations and responses for this user
    conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}

    # Construct the full conversation history in the "human: bot: " format
    conversation_history = ""
    for i in range(min(len(user_messages), len(user_responses))):
        conversation_history += f"human: {user_messages[i]}\nНастя: {user_responses[i]}\n"

    if conversation_history == "":
        conversation_history = "human:{}\nНастя:".format(text_message)
    else:
        conversation_history += "human:{}\nНастя:".format(text_message)

    # Generate response
    task = send_davinci.apply_async(args=[conversation_history])
    task_state = task.status()
    task_id = task.id()
    print("ID: %s, State: %s", task_state, task_id)
    response = task.get()

    # Add the response to the user's responses
    user_responses.append(response)
    # Store the updated conversations and responses for this user
    conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}

    return response


if __name__ == '__main__':
    app.start()
