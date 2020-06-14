# ChatStats
Webserver for viewing analytics on discord chat logs

Requires python3

Depends on https://github.com/Tyrrrz/DiscordChatExporter to export the chat logs as json. Place exported .json files in a folder named "chats"

# Installation
```pip install -r requirements.txt```

Unzip plugins.zip under app/static. app/static should have a dist and pulgins folder in it.

# Usage

Run ```python create_db.py``` to initiaize database.

Run ```python cloud.py``` to generate word cloud images.

```python run.py``` to start server.

Go to 127.0.0.1:5000 to view.
