## Viking

Viking is a bot that uses [discord.py (rewrite)](https://github.com/Rapptz/discord.py/tree/rewrite).

## Getting Started

You will need:
* [Python 3.7](https://www.python.org/downloads/)
* [PostgreSQL 11](https://www.postgresql.org/download/)
* [Redis 5](https://redis.io/download)

## Requirements

You can install all of the requirements by running:
```
$ pip install -r requirements.txt
```

## Commands

### **Administration**

***kill**
* Viking will log out of Discord, and close all connections.

***restart**
* Viking will restart my Raspberry Pi, and subsequently itself.

### **Basic**

***coinflip**
* Viking will flip a coin, and choose "Heads" or "Tails".

***count \<message>**
* Viking will count the words in a message excluding punctuation.

***dice**
* Viking will roll a six-sided dye, and output the result.

***eightball \<question>**
* Viking will respond to an author's question.

***hello**
* Viking will respond with a random greeting.

***quotes**
* Viking will return a random quotation.

***repeat \<amount> \<message>**
* Viking will repeat a message a specified amount of times.

***reverse \<message>**
* Viking will reverse the words in an author's message.

***tts \<message>**
* Viking will use text-to-speech to repeat the author's message.

***uptime**
* Viking will return the duration it's been online for.

### **Discord**

***help**
* Viking will list all available commands in the text channel.

***invite**
* Viking will generate an invite link to the server.

***joined \<member>**
* Viking will return the date of when a specified member joined the server.

***members**
* Viking will return the total number of members in the server.

***owner**
* Viking will mention the owner of the server.

***ping**
* Viking will output it's latency.

### **Fortnite**

***fortnite \<platform> \<username>**
* Viking will return a member's Fortnite statistics, including
solo, duo, squad and lifetime data.

### **League of Legends**

***live \<username>**
* Viking will give you a brief overview of everyone in your current game including: everyone's name, level, champion, rank and win/loss ratio.

***summoner \<username>**
* Viking will provide you with information regarding a League of Legends' account including: name, level, rank, points, win/loss ratio,
and top five champions with the highest mastery points

### **Moderation**

***ban \<member>**
* Viking will ban a member from the server by name, mention or ID.

***clear \<amount>**
* Viking will clear a specified amount of messages from a text channel.

***kick \<member>**
* Viking will kick a member from the server by name, mention or ID.

***load \<extension>**
* Viking will load an extension.

***purge**
* Viking will purge all messages from a text channel.

***reload \<extension>**
* Viking will reload an extension.

***unban \<member>**
* Viking will unban a member from the server by name, mention or ID.

***unload \<extension>**
* Viking will unload an extension.

### **PostgreSQL**

***create_commands**
* Viking will create the commands table for the database.

***create_members**
* Viking will create the members table for the database.

***index_commands**
* Viking will create a unique index on the commands table.

***index_members**
* Viking will create a unique index on the members table.

***insert_commands**
* Viking will insert every command into the database.

***insert_members**
* Viking will insert every member into the database.

***truncate \<table>**
* Viking will truncate a table in the database.

### **Weather**

***forecast \<location>**
* Viking will return the forecast of a specified location.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
