# ChatStats
Webserver for viewing analytics on discord chat logs

Depends on https://github.com/Tyrrrz/DiscordChatExporter to export the chat logs as json. Place exported .json files in a folder named "chats"

Unzip plugins.zip under app/static

Run ```python create_db.py``` to initiaize database.

Run ```python cloud.py``` to generate word cloud images.

```flask run``` to start server.
