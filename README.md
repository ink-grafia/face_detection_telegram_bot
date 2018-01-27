# photo_bot for Telegram
Telegram bot for cropping face from image.

Crops face from received image with spacing 3x4.

Logs is stored to logs.txt in project directory.

Two executable files: 
  - bot.py (telegram bot itself)
  - images_sender.py (gives you photo associated with conversation by the link "url:port?id=conversation_id"
  
Logs are stored in the project directory in the file "logs.txt" with the following format:
  <datestamp> <user_id> <first_name> <last_name> <username> <url> <message>
Examples:
  - 2018-01-27T17:34:03.312125 234485146 Vladimir Nitochkin vovnit - face was found, will send it to user, try 0
  - 2018-01-27T17:34:06.416273 234485146 Vladimir Nitochkin vovnit - face was found, will send it to user, try 1
  - 2018-01-27T17:34:07.611237 234485146 Vladimir Nitochkin vovnit http://85.17.15.165:443/?id=234485146_2.png accepted our cropping
  

**Master branch** deploys on [graphie_bot](https://t.me/graphie_bot)


**Develop branch** always deploys on [prepare_photo_bot](https://t.me//prepare_photo_bot)

